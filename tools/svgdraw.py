#!/usr/bin/env python3
"""단계적 SVG 그리기 — 선과 함수만으로. 모든 획은 매개함수 t∈[0,1] → (x, y) 를 샘플한 꺾은선이고, SVG 에는 `M…L…` 꺾은선 +
`data-fn`(원래 함수식)으로 남는다. 채우기는 닫힌 함수 곡선 안쪽만.

세 길(같은 스펙 JSON 을 주고받는다):
 A) draw  — AI 가 단계별로 그린다(SketchAgent 방식): 스펙 = 단계 목록, 단계마다 획(함수 이름 + 인자 + id). 단계마다 격자 PNG 를
            렌더해 눈으로 보고 다음 단계를 정한다(한 번에 다 그리지 않는다).
 B) trace — 점수 최적화 트레이싱(Primitive·스트링아트·LIVE 계열, 윤곽 따기 아님): 목표 그림과 지금 캔버스의 오차 지도(공간 분석)로
            후보 자리를 뽑고, 구조 텐서 방향으로 획 방향을 정하고, 색은 닫힌 식(최소제곱 최적 색 또는 팔레트 중 최선)으로 구해
            '오차 감소량'이 가장 큰 획을 언덕 오르기로 다듬어 하나씩 확정한다. 굵은 획 → 가는 획 순서가 단계가 된다.
 C) score — 그림 ↔ 목표: RMSE·SSIM·윤곽 F1 + 오차가 큰 칸(격자 이름 x3y7)·그 칸의 목표 색·방향 → A 의 다음 단계 제안.

스펙 JSON:
  {"width":400,"height":300,"background":"#ffffff","grid":20,
   "steps":[{"name":"1 큰 형태","strokes":[{"fn":"ellipse","c":[200,150],"rx":120,"ry":80,"stroke":"#333","width":4,"id":"몸통"}]}]}
  점은 [x, y](SVG 좌표, y 아래로) 또는 격자 이름 "x12y30"(SketchAgent: 1부터, y 는 아래에서 위로).
  획 공통 키: stroke(색) width(굵기) opacity fill(닫힌 곡선 채움 색) fill_opacity id(의미 이름) n(샘플 수)
             tf {"scale":s,"rotate":도,"translate":[dx,dy],"mirror":"x"|"y","about":[x,y]}  repeat {"n":k,"dx":..,"dy":..,"rotate":도,"about":[x,y]}
  함수(FUNCS): line p0 p1 · polyline pts closed · rect x y w h · poly c r sides rot · circle c r · ellipse c rx ry rot a0 a1 · arc c r a0 a1
              bezier pts(임의 차수 조절점) · through pts t(통과점 + t값, 최소제곱 3차 베지어, 같은 점 두 번 = 꺾임)
              graph f x0 x1 origin scale (y=f(x)) · param x y t0 t1 (x(t), y(t)) · polar r th0 th1 c (r(th), 도) · sine p0 p1 amp cycles · spiral c r0 r1 turns
  식은 numpy 이름(sin cos tan sqrt abs exp log pi e …)만 쓰는 안전한 식.
명령: python tools/mm.py svgdraw|svgtrace|svgscore …  (이 파일 단독: python tools/svgdraw.py draw|trace|score …)
"""
import os, sys, json, ast, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

STYLE = {'stroke', 'width', 'opacity', 'fill', 'fill_opacity', 'id', 'tf', 'repeat', 'n', 'fn'}
FONTS = ['/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf']

# ---------------------------------------------------------------- 안전한 식
_NP = {k: getattr(np, k) for k in ('sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'arctan2', 'sinh', 'cosh', 'tanh', 'sqrt', 'abs', 'exp', 'log',
                                    'log10', 'floor', 'ceil', 'sign', 'minimum', 'maximum', 'clip', 'where', 'mod', 'hypot', 'pi', 'e')}
_OK = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Constant, ast.Load, ast.Compare, ast.IfExp, ast.operator, ast.unaryop, ast.cmpop, ast.Tuple)
def expr(src, **var):
    """'0.5*sin(3*t)' 같은 식을 numpy 배열로 계산. 이름은 numpy 함수·상수와 넘긴 변수만, 속성 접근·첨자·람다 금지."""
    tree = ast.parse(str(src), mode='eval')
    for nd in ast.walk(tree):
        if not isinstance(nd, _OK): raise ValueError(f'식에 쓸 수 없는 요소: {type(nd).__name__} in {src!r}')
        if isinstance(nd, ast.Call) and not isinstance(nd.func, ast.Name): raise ValueError(f'함수 호출은 이름만: {src!r}')
        if isinstance(nd, ast.Name) and nd.id not in _NP and nd.id not in var: raise ValueError(f'모르는 이름 {nd.id!r} in {src!r}')
    v = eval(compile(tree, '<expr>', 'eval'), {'__builtins__': {}}, {**_NP, **var})
    return np.broadcast_to(np.asarray(v, float), np.shape(next(iter(var.values())))) if var else np.asarray(v, float)

# ---------------------------------------------------------------- 점·함수 라이브러리 (모두 (n,2) 꺾은선을 돌려준다)
_GRID = re.compile(r'^x(\d+(?:\.\d+)?)y(\d+(?:\.\d+)?)$')
def pt(p, ctx):
    """[x,y] 또는 'x12y30'(격자 칸 중심, SketchAgent: 1부터·y 아래→위) → (x, y) SVG 좌표."""
    if isinstance(p, str):
        m = _GRID.match(p.strip())
        if not m: raise ValueError(f'점 형식 {p!r} (예 [10,20] 또는 "x3y7")')
        g = ctx.get('grid') or 50; cw, ch = ctx['width'] / g, ctx['height'] / g
        return np.array([(float(m[1]) - 0.5) * cw, ctx['height'] - (float(m[2]) - 0.5) * ch])
    return np.asarray(p, float)[:2]
def pts(a, ctx): return np.array([pt(p, ctx) for p in a])
def _n(n, L, lo=8, hi=600): return int(n) if n else int(np.clip(L / 1.5, lo, hi))
def _bern(t, k):
    from math import comb
    return np.stack([comb(k, i) * t ** i * (1 - t) ** (k - i) for i in range(k + 1)], 1)

def f_line(ctx, p0, p1, n=None): a, b = pt(p0, ctx), pt(p1, ctx); return np.array([a, b])
def f_polyline(ctx, pts_, closed=False, n=None):
    q = pts(pts_, ctx); return np.vstack([q, q[:1]]) if closed else q
def f_rect(ctx, x, y, w, h, n=None): return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], float)
def f_poly(ctx, c, r, sides=6, rot=0, n=None):
    c = pt(c, ctx); a = np.radians(rot) + np.arange(sides + 1) * 2 * np.pi / sides; return c + r * np.c_[np.cos(a), np.sin(a)]
def f_ellipse(ctx, c, rx, ry, rot=0, a0=0, a1=360, n=None):
    c = pt(c, ctx); t = np.radians(np.linspace(a0, a1, _n(n, abs(a1 - a0) / 360 * np.pi * (rx + ry)))); r = np.radians(rot)
    x, y = rx * np.cos(t), ry * np.sin(t); return c + np.c_[x * np.cos(r) - y * np.sin(r), x * np.sin(r) + y * np.cos(r)]
def f_circle(ctx, c, r, n=None): return f_ellipse(ctx, c, r, r, n=n)
def f_arc(ctx, c, r, a0=0, a1=90, n=None): return f_ellipse(ctx, c, r, r, 0, a0, a1, n)
def f_bezier(ctx, pts_, n=None):
    P = pts(pts_, ctx); L = np.linalg.norm(np.diff(P, axis=0), axis=1).sum(); t = np.linspace(0, 1, _n(n, L)); return _bern(t, len(P) - 1) @ P
def fit_cubic(P, t):
    """통과점 P(k,2)·t값 → 최소제곱 3차 베지어 조절점(4,2). 점 2개면 직선, 3개면 2차를 3차로 올림."""
    P, t = np.asarray(P, float), np.asarray(t, float)
    if len(P) == 2: return np.array([P[0], P[0] + (P[1] - P[0]) / 3, P[0] + 2 * (P[1] - P[0]) / 3, P[1]])
    if len(P) == 3:
        Q = np.linalg.lstsq(_bern(t, 2), P, rcond=None)[0]; return np.array([Q[0], Q[0] + 2 / 3 * (Q[1] - Q[0]), Q[2] + 2 / 3 * (Q[1] - Q[2]), Q[2]])
    return np.linalg.lstsq(_bern(t, 3), P, rcond=None)[0]
def f_through(ctx, pts_, t=None, n=None):
    """SketchAgent 획: 통과점과 t 값. 같은 점이 연달아 두 번이면 꺾임(조각을 나눠 각각 맞춤). 점 1개 = 점(작은 원)."""
    P = pts(pts_, ctx); t = np.linspace(0, 1, len(P)) if t is None else np.asarray(t, float)
    if len(P) == 1: return f_circle(ctx, P[0], 0.5, n=8)
    cuts = [0] + [i for i in range(1, len(P)) if np.allclose(P[i], P[i - 1])] + [len(P)]
    out = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        Q, tq = P[a:b], t[a:b]
        if len(Q) < 2: continue
        tq = (tq - tq[0]) / max(tq[-1] - tq[0], 1e-9); C = fit_cubic(Q, np.clip(tq, 0, 1))
        L = np.linalg.norm(np.diff(Q, axis=0), axis=1).sum(); out.append(_bern(np.linspace(0, 1, _n(n, L, 2)), 3) @ C)
    return np.vstack(out) if out else P
def f_graph(ctx, f, x0, x1, origin=(0, 0), scale=(1, 1), n=None):
    """y = f(x) 그래프. 화면 점 = origin + (x·sx, −f(x)·sy) — 수학 좌표(y 위)를 SVG(y 아래)로."""
    o = pt(origin, ctx); sx, sy = (scale, scale) if np.isscalar(scale) else scale
    x = np.linspace(x0, x1, _n(n, abs(x1 - x0) * sx * 2)); return o + np.c_[x * sx, -expr(f, x=x) * sy]
def f_param(ctx, x, y, t0=0, t1=1, n=None):
    t = np.linspace(t0, t1, int(n or 300)); return np.c_[expr(x, t=t), expr(y, t=t)]
def f_polar(ctx, r, th0=0, th1=360, c=(0, 0), n=None):
    """r = f(th) (th 도 단위, 식 안에서는 라디안 변수 th)."""
    c = pt(c, ctx); th = np.radians(np.linspace(th0, th1, int(n or 360))); rr = expr(r, th=th); return c + np.c_[rr * np.cos(th), rr * np.sin(th)]
def f_sine(ctx, p0, p1, amp=5, cycles=3, phase=0, n=None):
    a, b = pt(p0, ctx), pt(p1, ctx); d = b - a; L = np.linalg.norm(d); u = d / max(L, 1e-9); v = np.array([-u[1], u[0]])
    s = np.linspace(0, 1, _n(n, L * (1 + cycles), 16)); return a + np.outer(s, d) + np.outer(amp * np.sin(2 * np.pi * cycles * s + np.radians(phase)), v)
def f_spiral(ctx, c, r0=0, r1=50, turns=3, n=None):
    c = pt(c, ctx); s = np.linspace(0, 1, int(n or 120 * turns)); th = 2 * np.pi * turns * s; r = r0 + (r1 - r0) * s; return c + np.c_[r * np.cos(th), r * np.sin(th)]
FUNCS = {'line': f_line, 'polyline': f_polyline, 'rect': f_rect, 'poly': f_poly, 'circle': f_circle, 'ellipse': f_ellipse, 'arc': f_arc,
         'bezier': f_bezier, 'through': f_through, 'graph': f_graph, 'param': f_param, 'polar': f_polar, 'sine': f_sine, 'spiral': f_spiral}
_KEYMAP = {'pts': 'pts_'}

def _tf(P, tf, k=1):
    if not tf: return P
    o = np.asarray(tf.get('about', [0, 0]), float); P = P - o
    if 'scale' in tf: s = tf['scale']; P = P * (np.asarray(s, float) ** k if not np.isscalar(s) else s ** k)
    if 'mirror' in tf and k % 2: P = P * (np.array([-1, 1]) if tf['mirror'] == 'x' else np.array([1, -1]))
    if 'rotate' in tf:
        r = np.radians(tf['rotate'] * k); P = P @ np.array([[np.cos(r), np.sin(r)], [-np.sin(r), np.cos(r)]])
    P = P + o
    if 'translate' in tf: P = P + np.asarray(tf['translate'], float) * k
    if 'dx' in tf or 'dy' in tf: P = P + np.array([tf.get('dx', 0), tf.get('dy', 0)]) * k
    return P
def sample(st, ctx):
    """획 dict → 꺾은선 목록(repeat 면 여러 개)."""
    fn = st.get('fn', 'polyline')
    if fn not in FUNCS: raise ValueError(f'모르는 함수 {fn!r}: {sorted(FUNCS)}')
    kw = {_KEYMAP.get(k, k): v for k, v in st.items() if k not in STYLE}
    P = _tf(FUNCS[fn](ctx, n=st.get('n'), **kw), st.get('tf'))
    rp = st.get('repeat')
    if not rp: return [P]
    rr = {k: v for k, v in rp.items() if k != 'n'}
    return [_tf(P, rr, k) if k else P for k in range(int(rp.get('n', 1)))]
def fn_text(st):
    return st.get('fn', 'polyline') + ' ' + ' '.join(f'{k}={json.dumps(v, ensure_ascii=False, separators=(",", ":"))}' for k, v in st.items() if k not in STYLE or k in ('tf', 'repeat'))

# ---------------------------------------------------------------- 색
def rgb(c):
    if c is None or c == 'none': return None
    if isinstance(c, (list, tuple, np.ndarray)): a = np.asarray(c, float); return a / 255 if a.max() > 1 else a
    c = c.strip().lstrip('#')
    if len(c) == 3: c = ''.join(ch * 2 for ch in c)
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], float) / 255
def hexc(a): a = np.clip(np.round(np.asarray(a, float) * 255), 0, 255).astype(int); return '#%02x%02x%02x' % tuple(a)

# ---------------------------------------------------------------- 래스터(획 덮임 = 안티에일리어스 마스크) — 그리기·채점·최적화가 같은 함수
def cover(P, width, fill, H, W, ss=4):
    """꺾은선 P(픽셀 좌표) → (y0, y1, x0, x1, 덮임 0~1). width 0 이면 채움만. 화면 밖이면 None."""
    P = np.asarray(P, float); r = width / 2 + 1.5
    x0, y0 = max(int(np.floor(P[:, 0].min() - r)), 0), max(int(np.floor(P[:, 1].min() - r)), 0)
    x1, y1 = min(int(np.ceil(P[:, 0].max() + r)) + 1, W), min(int(np.ceil(P[:, 1].max() + r)) + 1, H)
    if x1 <= x0 or y1 <= y0: return None
    im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0); d = ImageDraw.Draw(im)
    Q = (P - [x0, y0]) * ss; flat = [tuple(q) for q in Q]
    if fill and len(flat) > 2: d.polygon(flat, fill=255)
    if width > 0:
        w = max(1, int(round(width * ss)))
        if len(flat) > 1: d.line(flat, fill=255, width=w, joint='curve')
        h = w / 2
        for q in (Q[0], Q[-1]): d.ellipse([q[0] - h, q[1] - h, q[0] + h, q[1] + h], fill=255)       # 둥근 끝(SVG round cap)
    m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
    return y0, y1, x0, x1, m
def paint(canvas, P, color, width, opacity=1.0, fill=None, fill_opacity=None, ss=4, k=1.0):
    """캔버스(H,W,3 0~1)에 획을 합성(제자리). k = 좌표 배율(스펙 단위 → 픽셀)."""
    H, W = canvas.shape[:2]; P = np.asarray(P, float) * k
    if fill is not None:
        c = cover(P, 0, True, H, W, ss)
        if c: y0, y1, x0, x1, m = c; a = (fill_opacity if fill_opacity is not None else opacity) * m[..., None]; v = canvas[y0:y1, x0:x1]; v += a * (fill - v)
    if color is not None and width > 0:
        c = cover(P, width * k, False, H, W, ss)
        if c: y0, y1, x0, x1, m = c; a = opacity * m[..., None]; v = canvas[y0:y1, x0:x1]; v += a * (color - v)
    return canvas

# ---------------------------------------------------------------- 스펙 → 획·래스터·SVG·단계 그림
def load(spec):
    if isinstance(spec, dict): return spec
    if str(spec).lower().endswith('.svg'): return from_svg(spec)
    return json.load(open(spec, encoding='utf-8'))
def strokes(spec):
    """(단계 번호, 단계 이름, 획 dict, 꺾은선) 목록."""
    ctx = {'width': spec['width'], 'height': spec['height'], 'grid': spec.get('grid')}; out = []
    for i, stp in enumerate(spec['steps']):
        for st in stp.get('strokes', []):
            for P in sample(st, ctx): out.append((i, stp.get('name', f'{i + 1}단계'), st, P))
    return out
def raster(spec, scale=1.0, upto=None, ss=4):
    """스펙을 캔버스로(upto=단계 번호까지). scale 은 출력 배율."""
    H, W = int(round(spec['height'] * scale)), int(round(spec['width'] * scale))
    bg = rgb(spec.get('background', '#ffffff')); cv = np.ones((H, W, 3), np.float32) * (bg if bg is not None else np.ones(3)).astype(np.float32)   # 'none' = 흰 종이
    for i, _, st, P in strokes(spec):
        if upto is not None and i > upto: break
        paint(cv, P, rgb(st.get('stroke', '#000000')), float(st.get('width', 1)), float(st.get('opacity', 1)), rgb(st.get('fill')), st.get('fill_opacity'), ss, scale)
    return cv
def _f(v): return f'{v:.2f}'.rstrip('0').rstrip('.')
def to_svg(spec, path=None):
    from xml.sax.saxutils import quoteattr
    W, H = spec['width'], spec['height']
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(W)}" height="{_f(H)}" viewBox="0 0 {_f(W)} {_f(H)}">',
         f'<rect width="{_f(W)}" height="{_f(H)}" fill="{spec.get("background", "#ffffff")}"/>']
    cur = None; k = 0
    for i, name, st, P in strokes(spec):
        if i != cur:
            if cur is not None: o.append('</g>')
            o.append(f'<g id="step{i + 1}" data-step={quoteattr(name)}>'); cur = i
        closed = st.get('fill') not in (None, 'none')
        d = 'M' + ' L'.join(f'{_f(x)} {_f(y)}' for x, y in P) + (' Z' if closed else '')
        w = float(st.get('width', 1)); k += 1
        sty = (f'fill="{st["fill"]}" fill-opacity="{_f(st.get("fill_opacity", st.get("opacity", 1)))}"' if closed else 'fill="none"') + \
              (f' stroke="{st.get("stroke", "#000000")}" stroke-width="{_f(w)}" stroke-opacity="{_f(float(st.get("opacity", 1)))}" stroke-linecap="round" stroke-linejoin="round"' if w > 0 and st.get('stroke') != 'none' else ' stroke="none"')
        o.append(f'<path id={quoteattr(str(st.get("id", f"s{k}")))} d="{d}" {sty} data-fn={quoteattr(fn_text(st))}/>')
    if cur is not None: o.append('</g>')
    o.append('</svg>'); s = '\n'.join(o)
    if path: open(path, 'w', encoding='utf-8').write(s)
    return s
def from_svg(path):
    """아무 SVG → 스펙(모든 도형을 꺾은선 획으로, 한 단계). 손으로 그린 SVG 도 채점·렌더할 수 있게."""
    from svgelements import SVG, Path as SPath, Shape, Move, Close
    svg = SVG.parse(path); W, H = float(svg.width or 100), float(svg.height or 100); out = []
    for el in svg.elements():
        if not isinstance(el, Shape): continue
        p = SPath(el); p.reify(); cur = []; segs = []
        for sg in p:
            if isinstance(sg, Move):
                if len(cur) > 1: segs.append(cur)
                cur = [(sg.end.x, sg.end.y)]; continue
            if sg.start is None or sg.end is None: continue
            L = sg.length() if hasattr(sg, 'length') else 0; m = max(1, int(np.ceil((L or 0) / 1.0)))
            cur += [(q.x, q.y) for q in (sg.point(t) for t in np.linspace(0, 1, m + 1)[1:])]
            if isinstance(sg, Close) and len(cur) > 1: segs.append(cur); cur = []
        if len(cur) > 1: segs.append(cur)
        sw = float(getattr(el, 'implicit_stroke_width', None) or el.stroke_width or 0) if el.stroke is not None and el.stroke.value is not None else 0
        sc = el.stroke.hex[:7] if sw else None; fc = el.fill.hex[:7] if el.fill is not None and el.fill.value is not None else None
        so = (el.stroke.opacity if sw else 1) or 1; fo = (el.fill.opacity if fc else 1) or 1
        for s in segs:
            st = {'fn': 'polyline', 'pts': [[round(x, 3), round(y, 3)] for x, y in s], 'width': sw, 'opacity': so}
            if sc: st['stroke'] = sc
            else: st['stroke'] = 'none'; st['width'] = 0
            if fc: st['fill'] = fc; st['fill_opacity'] = fo
            if sc or fc: out.append(st)
    return {'width': W, 'height': H, 'background': 'none', 'steps': [{'name': os.path.basename(path), 'strokes': out}]}

def _font(sz):
    for f in FONTS:
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()
def grid_image(cv, spec, title='', scale=1.0, grid=None):
    """캔버스 + 격자(칸 이름 x?y? 를 읽을 수 있게 가장자리 번호) + 제목 → PIL 그림. AI 가 다음 단계 좌표를 읽는 화면."""
    g = grid or spec.get('grid') or 20; H, W = cv.shape[:2]; M = 34
    im = Image.new('RGB', (W + 2 * M, H + 2 * M + 22), (250, 250, 250)); im.paste(Image.fromarray((np.clip(cv, 0, 1) * 255).astype(np.uint8)), (M, M + 22))
    d = ImageDraw.Draw(im, 'RGBA'); f = _font(11); every = 1 if g <= 25 else 5
    for i in range(g + 1):
        x = M + i * W / g; y = M + 22 + i * H / g; strong = i % 5 == 0
        d.line([(x, M + 22), (x, M + 22 + H)], fill=(0, 120, 255, 70 if strong else 30)); d.line([(M, y), (M + W, y)], fill=(0, 120, 255, 70 if strong else 30))
    for i in range(1, g + 1):
        if i % every and i != 1: continue
        x = M + (i - 0.5) * W / g; y = M + 22 + H - (i - 0.5) * H / g
        d.text((x, M + 22 + H + 4), str(i), fill=(60, 60, 60), font=f, anchor='mt'); d.text((M - 4, y), str(i), fill=(60, 60, 60), font=f, anchor='rm')
    d.text((M, 6), title, fill=(20, 20, 20), font=_font(14))
    return im
def draw(spec, out, scale=None, gif=True):
    """A) 스펙 → out/drawing.svg + 단계별 격자 PNG(step_01.png …) + 한 장 모음(steps.png) + 단계 GIF. 각 단계 그림을 보고 다음 단계를 정한다."""
    spec = load(spec); os.makedirs(out, exist_ok=True)
    scale = scale or min(4.0, 640 / max(spec['width'], spec['height']))
    svg = to_svg(spec, os.path.join(out, 'drawing.svg')); frames = []; n_st = len(spec['steps'])
    allst = strokes(spec)
    for i, stp in enumerate(spec['steps']):
        cv = raster(spec, scale, upto=i); n = sum(1 for s in allst if s[0] <= i)
        im = grid_image(cv, spec, f'{i + 1}/{n_st} {stp.get("name", "")}  (획 {n})', scale); im.save(os.path.join(out, f'step_{i + 1:02d}.png')); frames.append(im)
    cols = min(3, len(frames)); rows = -(-len(frames) // cols); w, h = frames[0].size; t = 0.5
    sheet = Image.new('RGB', (int(w * t) * cols, int(h * t) * rows), 'white')
    for k, im in enumerate(frames): sheet.paste(im.resize((int(w * t), int(h * t))), ((k % cols) * int(w * t), (k // cols) * int(h * t)))
    sheet.save(os.path.join(out, 'steps.png'))
    if gif: frames[0].save(os.path.join(out, 'steps.gif'), save_all=True, append_images=frames[1:] + [frames[-1]] * 2, duration=700, loop=0)
    return {'svg': os.path.join(out, 'drawing.svg'), 'steps': [os.path.join(out, f'step_{i + 1:02d}.png') for i in range(n_st)], 'sheet': os.path.join(out, 'steps.png'),
            'gif': os.path.join(out, 'steps.gif') if gif else None, 'strokes': len(allst), 'paths_only_ML': _only_lines(svg)}
def browser_rmse(svg_path, spec):
    """SVG 파일을 Chromium 으로 렌더한 그림 ↔ 내부 래스터(채점에 쓰는 것) RMSE. 0.02 안팎이면 점수가 실제 렌더와 같다고 본다."""
    from playwright.sync_api import sync_playwright
    import tempfile
    spec = load(spec); W, H = int(round(spec['width'])), int(round(spec['height'])); f = os.path.join(tempfile.mkdtemp(prefix='svgb_'), 'b.png')
    with sync_playwright() as p:
        exe = '/opt/pw-browsers/chromium'; b = p.chromium.launch(**({'executable_path': exe} if os.path.exists(exe) else {}))
        pg = b.new_page(viewport={'width': W, 'height': H}); pg.set_content('<html><body style="margin:0">' + open(svg_path, encoding='utf-8').read() + '</body></html>')
        pg.screenshot(path=f); b.close()
    A = np.asarray(Image.open(f).convert('RGB'), np.float32)[:H, :W] / 255; B = raster(spec, 1.0)[:A.shape[0], :A.shape[1]]
    return round(float(np.sqrt(((A - B) ** 2).mean())), 4)
def _only_lines(svg): return all(set(re.sub(r'[\d\s.\-eE]', '', d)) <= set('MLZ') for d in re.findall(r' d="([^"]*)"', svg))

# ---------------------------------------------------------------- 그림 불러오기·공간 분석
def load_image(path, size=None, fit=None):
    """그림 → (H,W,3) 0~1. size: 긴 변 픽셀, fit=(W,H) 면 그 크기로. 투명은 흰 배경에."""
    im = Image.open(path).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); im = Image.alpha_composite(bg, im).convert('RGB')
    if fit: im = im.resize((int(fit[0]), int(fit[1])), Image.LANCZOS)
    elif size: s = size / max(im.size); im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255
def structure(img, sigma=2.0):
    """구조 텐서: 획 방향(윤곽에 나란한 각, 라디안)·일관성(0~1, 1 = 뚜렷한 한 방향)·윤곽 세기."""
    from scipy import ndimage as nd
    L = img @ np.array([0.299, 0.587, 0.114], np.float32)
    gx, gy = nd.sobel(L, 1), nd.sobel(L, 0)
    jxx, jyy, jxy = (nd.gaussian_filter(a, sigma) for a in (gx * gx, gy * gy, gx * gy))
    tr = jxx + jyy; det = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2)
    coh = np.where(tr > 1e-9, det / (tr + 1e-9), 0) ** 2
    theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2              # 기울기의 수직 = 윤곽 방향
    return theta, coh, np.hypot(gx, gy)
def palette_kmeans(img, k=6, iters=12, seed=0):
    """그림에서 대표색 k 개(k-평균) — 필라멘트 색 수에 맞춰 팔레트로 그리기."""
    X = img.reshape(-1, 3); rng = np.random.default_rng(seed); X = X[rng.choice(len(X), min(len(X), 20000), replace=False)]
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        lab = ((X[:, None] - C[None]) ** 2).sum(-1).argmin(1)
        C = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
    return C

# ---------------------------------------------------------------- B) 점수 최적화 트레이싱
class Tracer:
    """목표 T, 캔버스 C, 가중 지도 Wm(윤곽 강조). 후보 획의 점수 = Σ Wm·(T−C)² − Σ Wm·(T−C')² (오차 감소량, 클수록 좋음).
    색: 덮임 a=opacity·m 일 때 C' = C + a(c − C) → 최적 c = Σ Wm·a·(T − (1−a)C) / Σ Wm·a² (채널별, 0~1 로 자름) 또는 팔레트 중 최선."""
    def __init__(self, target, init=None, alpha=0.85, palette=None, edge_weight=1.0, ss=3, seed=0):
        self.T = target.astype(np.float32); self.H, self.W = target.shape[:2]
        self.C = (init.astype(np.float32).copy() if init is not None else np.ones_like(self.T) * np.median(self.T.reshape(-1, 3), 0))
        self.theta, self.coh, mag = structure(self.T); self.Wm = (1 + edge_weight * mag / (mag.max() + 1e-9)).astype(np.float32)
        self.alpha, self.ss, self.rng = alpha, ss, np.random.default_rng(seed)
        self.pal = None if palette is None else np.asarray([rgb(p) if isinstance(p, str) else p for p in palette], np.float32)
    def err_map(self): return (self.Wm * ((self.T - self.C) ** 2).sum(-1))
    def total(self): return float(self.err_map().sum())
    def rmse(self): return float(np.sqrt(((self.T - self.C) ** 2).mean()))
    def polyline(self, g):
        if g['type'] == 'line': return np.array([g['p'][0], g['p'][1]])
        P = np.array(g['p']); L = np.linalg.norm(P[2] - P[0]) + 1; t = np.linspace(0, 1, int(np.clip(L / 2, 6, 40))); return _bern(t, 2) @ P
    def score(self, g):
        c = cover(self.polyline(g), g['w'], False, self.H, self.W, self.ss)
        if c is None: return -1e18, None
        y0, y1, x0, x1, m = c; a = (self.alpha * m)[..., None]; T, C, Wm = self.T[y0:y1, x0:x1], self.C[y0:y1, x0:x1], self.Wm[y0:y1, x0:x1, None]
        D = T - C; E = D + a * C; saa = float((Wm * a * a).sum())
        if saa < 1e-6: return -1e18, None
        sae = (Wm * a * E).sum((0, 1)); base = float((Wm * D * D).sum())
        if self.pal is None:
            col = np.clip(sae / saa, 0, 1)
            err = float((Wm * (E - a * col) ** 2).sum())
        else:   # err(p) = ΣWm E² − 2 p·ΣWm a E + |p|² ΣWm a²  (채널 합)
            see = float((Wm * E * E).sum()); errs = see - 2 * self.pal @ sae + (self.pal ** 2).sum(1) * saa
            j = int(errs.argmin()); col, err = self.pal[j], float(errs[j])
        return base - err, col
    def random_geom(self, prob, lr, wr, kinds):
        H, W = self.H, self.W; i = self.rng.choice(H * W, p=prob); y, x = divmod(i, W); x += self.rng.random(); y += self.rng.random()
        th = self.theta[int(y), int(x)] if self.rng.random() < 0.25 + 0.75 * self.coh[int(y), int(x)] else self.rng.uniform(0, np.pi)
        th += self.rng.normal(0, 0.15); L = np.exp(self.rng.uniform(*np.log(lr))); w = np.exp(self.rng.uniform(*np.log(wr)))
        u = np.array([np.cos(th), np.sin(th)]); a, b = np.array([x, y]) - u * L / 2, np.array([x, y]) + u * L / 2
        kind = kinds[self.rng.integers(len(kinds))]
        if kind == 'line': return {'type': 'line', 'p': [a, b], 'w': w}
        mid = (a + b) / 2 + np.array([-u[1], u[0]]) * self.rng.normal(0, L / 4); return {'type': 'curve', 'p': [a, mid, b], 'w': w}
    def mutate(self, g, wr):
        h = {'type': g['type'], 'p': [p.copy() for p in g['p']], 'w': g['w']}; L = np.linalg.norm(h['p'][-1] - h['p'][0]) + 1; r = self.rng.integers(len(h['p']) + 2)
        if r < len(h['p']): h['p'][r] += self.rng.normal(0, max(1.0, 0.2 * L), 2)
        elif r == len(h['p']): h['w'] = float(np.clip(h['w'] * np.exp(self.rng.normal(0, 0.3)), 0.6, wr[1] * 1.5))
        else: d = self.rng.normal(0, max(1.0, 0.1 * L), 2); h['p'] = [p + d for p in h['p']]
        return h
    def step(self, prob, lr, wr, kinds, n_cand=40, n_top=2, climbs=40, patience=12):
        cands = [self.random_geom(prob, lr, wr, kinds) for _ in range(n_cand)]; sc = [self.score(g)[0] for g in cands]
        best = (-1e18, None, None)
        for j in np.argsort(sc)[::-1][:n_top]:
            g = cands[j]; s, col = self.score(g); miss = 0
            for _ in range(climbs):
                h = self.mutate(g, wr); s2, c2 = self.score(h)
                if s2 > s: g, s, col, miss = h, s2, c2, 0
                else:
                    miss += 1
                    if miss >= patience: break
            if s > best[0]: best = (s, g, col)
        return best
    def commit(self, g, col): paint(self.C, self.polyline(g), col, g['w'], self.alpha, ss=self.ss)

def trace(image, out, strokes_n=300, size=160, kinds='line,curve', alpha=0.85, palette=None, colors=0, edge_weight=1.0,
          stages=3, init=None, seed=0, tol=2e-5, frames=24, out_width=None, patience=5):
    """B) 목표 그림 → 선·함수 획만으로 된 스펙/SVG. 매 획: 오차 지도^1.5 로 자리 표본 → 구조 텐서 방향 → 후보 n개 점수 → 상위 2개 언덕 오르기 → 최선 확정.
    굵기·길이는 단계마다 줄어든다(큰 덩어리 → 세부). palette: 색 목록(필라멘트 색) 또는 colors=k 면 그림에서 k-평균. init: 먼저 그린 스펙(AI 단계 그림) 위에 이어 그림."""
    from scipy import ndimage as nd
    os.makedirs(out, exist_ok=True); T = load_image(image, size); H, W = T.shape[:2]
    full = Image.open(image).size; OW = out_width or full[0]; k = OW / W; OH = H * k
    pal = np.array([rgb(p) for p in palette], np.float32) if palette else (palette_kmeans(T, int(colors), seed=seed) if colors else None)
    C0 = None; base_steps = []
    if init:
        ispec = load(init); C0 = raster(ispec, W / ispec['width'], ss=3); base_steps = _scaled_steps(ispec, OW / ispec['width'])
    tr = Tracer(T, C0, alpha, pal, edge_weight, 3, seed); kinds = [s.strip() for s in kinds.split(',') if s.strip()]
    e0 = tr.total(); r0 = tr.rmse(); S = max(H, W); log = []; snaps = []; steps = [{'name': f'{i + 1} ' + ('큰 덩어리' if i == 0 else '세부' if i == stages - 1 else '중간'), 'strokes': []} for i in range(stages)]
    every = max(1, strokes_n // max(frames, 1)); miss = 0
    for n in range(strokes_n):
        p = n / max(strokes_n - 1, 1); st_i = min(int(p * stages), stages - 1)
        wmax = S * (0.10 * (1 - p) ** 1.5 + 0.006) + 0.8; lmax = S * (0.5 * (1 - p) + 0.06)
        wr, lr = (max(0.7, wmax / 4), wmax), (max(2.0, lmax / 5), lmax)
        E = nd.gaussian_filter(tr.err_map(), 1.0) ** 1.5; prob = (E / E.sum()).ravel() if E.sum() > 0 else None
        if prob is None: break
        s, g, col = tr.step(prob, lr, wr, kinds)
        if g is None or s < tol * H * W:                                      # 이번 표본이 나빴을 수 있다 — 연속 patience 번이면 멈춤
            miss += 1
            if miss >= patience: log.append({'n': n, 'stop': f'감소량 {s:.4g} < 기준 {tol * H * W:.4g} 이 {miss}번 연속'}); break
            continue
        miss = 0; tr.commit(g, col)
        P = (tr.polyline(g) if g['type'] == 'line' else np.array(g['p'])) * k
        st = ({'fn': 'line', 'p0': _r(P[0]), 'p1': _r(P[1])} if g['type'] == 'line' else {'fn': 'bezier', 'pts': [_r(q) for q in P]})
        st.update({'stroke': hexc(col), 'width': round(g['w'] * k, 2), 'opacity': alpha, 'id': f't{n + 1}'})
        steps[st_i]['strokes'].append(st); log.append({'n': n + 1, 'gain': round(s, 4), 'rmse': round(tr.rmse(), 5), 'w': round(g['w'], 2)})
        if n % every == 0 or n == strokes_n - 1: snaps.append(tr.C.copy())
    spec = {'width': round(OW, 2), 'height': round(OH, 2), 'background': hexc(np.median(T.reshape(-1, 3), 0)) if not init else load(init).get('background', '#ffffff'),
            'grid': 20, 'steps': base_steps + [s for s in steps if s['strokes']], 'source': os.path.basename(image)}
    json.dump(spec, open(os.path.join(out, 'trace.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    to_svg(spec, os.path.join(out, 'trace.svg'))
    if snaps:
        sc = max(1, int(320 / max(H, W)))
        fr = [Image.fromarray((np.clip(np.hstack([T, c]), 0, 1) * 255).astype(np.uint8)).resize((2 * W * sc, H * sc), Image.NEAREST) for c in snaps]
        fr[0].save(os.path.join(out, 'progress.gif'), save_all=True, append_images=fr[1:] + [fr[-1]] * 6, duration=150, loop=0)
    n_done = sum(len(s['strokes']) for s in steps)
    return {'spec': os.path.join(out, 'trace.json'), 'svg': os.path.join(out, 'trace.svg'), 'gif': os.path.join(out, 'progress.gif'), 'strokes': n_done,
            'work_px': [W, H], 'rmse_start': round(r0, 4), 'rmse_end': round(tr.rmse(), 4), 'error_drop': round(1 - tr.total() / e0, 4),
            'palette': [hexc(c) for c in pal] if pal is not None else None, 'stop': log[-1].get('stop') if log else None, 'log_tail': log[-3:]}
def _r(p): return [round(float(p[0]), 2), round(float(p[1]), 2)]
def _scaled_steps(spec, k):
    """init 스펙의 단계를 출력 좌표 배율 k 로. 배율이 1 이면 그대로(함수식 유지), 아니면 꺾은선으로 굳히고 원래 함수는 id 에 남긴다."""
    if abs(k - 1) < 1e-9: return [dict(s) for s in spec['steps']]
    ctx = {'width': spec['width'], 'height': spec['height'], 'grid': spec.get('grid')}; out = []
    for stp in spec['steps']:
        ss_ = []
        for st in stp.get('strokes', []):
            for P in sample(st, ctx):
                q = {kk: v for kk, v in st.items() if kk in ('stroke', 'opacity', 'fill', 'fill_opacity')}
                q.update({'fn': 'polyline', 'pts': [_r(p) for p in P * k], 'width': round(float(st.get('width', 1)) * k, 3), 'id': f"{st.get('id', '')}·{st.get('fn', 'polyline')}"}); ss_.append(q)
        out.append({'name': stp.get('name', ''), 'strokes': ss_})
    return out

# ---------------------------------------------------------------- C) 채점·제안
def ssim(a, b, sigma=1.5):
    from scipy import ndimage as nd
    g = lambda x: nd.gaussian_filter(x, sigma); c1, c2 = 0.01 ** 2, 0.03 ** 2
    ma, mb = g(a), g(b); va, vb, cov = g(a * a) - ma ** 2, g(b * b) - mb ** 2, g(a * b) - ma * mb
    return float((((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))).mean())
def edge_f1(a, b, tol=2.0):
    from scipy import ndimage as nd
    def edges(x): L = x @ np.array([0.299, 0.587, 0.114], np.float32); m = np.hypot(nd.sobel(L, 0), nd.sobel(L, 1)); return m > max(0.25, 0.3 * m.max())
    ea, eb = edges(a), edges(b)
    if not ea.any() or not eb.any(): return 0.0
    da, db = nd.distance_transform_edt(~ea), nd.distance_transform_edt(~eb)
    prec = float((da[eb] <= tol).mean()); rec = float((db[ea] <= tol).mean()); return 2 * prec * rec / max(prec + rec, 1e-9)
def score(drawing, target, out=None, size=256, grid=10, top=6):
    """C) 그림(스펙 JSON 또는 SVG) ↔ 목표 그림. 오차가 큰 칸 = 다음 단계에서 그릴 곳(칸 이름·목표 색·현재 색·방향)."""
    spec = load(drawing); s = size / max(spec['width'], spec['height']); D = raster(spec, s, ss=3); H, W = D.shape[:2]
    T = load_image(target, fit=(W, H)); err = ((T - D) ** 2).sum(-1)
    theta, coh, _ = structure(T); regions = []
    for gy in range(grid):
        for gx in range(grid):
            ys, xs = slice(gy * H // grid, (gy + 1) * H // grid), slice(gx * W // grid, (gx + 1) * W // grid)
            e = float(err[ys, xs].mean()); th = theta[ys, xs]; c2 = float(np.abs(np.mean(np.exp(2j * th) * coh[ys, xs])))
            regions.append({'cell': f'x{gx + 1}y{grid - gy}', 'err': round(e, 4), 'target': hexc(T[ys, xs].reshape(-1, 3).mean(0)), 'now': hexc(D[ys, xs].reshape(-1, 3).mean(0)),
                            'dir_deg': round(float(np.degrees(np.angle(np.mean(np.exp(2j * th) * coh[ys, xs])) / 2)) % 180, 0) if c2 > 0.05 else None,
                            'box': [round(gx * spec['width'] / grid, 1), round(gy * spec['height'] / grid, 1), round(spec['width'] / grid, 1), round(spec['height'] / grid, 1)]})
    regions.sort(key=lambda r: -r['err'])
    r = {'rmse': round(float(np.sqrt(((T - D) ** 2).mean())), 4), 'ssim': round(ssim(T.mean(-1), D.mean(-1)), 4), 'edge_f1': round(edge_f1(T, D), 4),
         'grid': grid, 'worst': regions[:top], 'note': '칸 이름 x?y? 는 1부터·y 아래→위. dir_deg 는 윤곽 방향(0=가로, 90=세로, SVG 좌표). box=[x,y,w,h] 스펙 좌표'}
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
        hm = np.clip(err / max(np.percentile(err, 99), 1e-6), 0, 1); heat = np.stack([hm, 0.2 * (1 - hm), 1 - hm], -1) * 0.75 + 0.25 * D
        im = Image.fromarray((np.clip(np.hstack([T, D, heat]), 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im); f = _font(12)
        for k, t in enumerate(['목표', '그림', f'오차 RMSE {r["rmse"]} SSIM {r["ssim"]}']): d.text((k * W + 4, 4), t, fill=(255, 0, 80), font=f)
        for rg in regions[:top]:
            gx, gy = int(rg['cell'][1:].split('y')[0]) - 1, grid - int(rg['cell'].split('y')[1])
            d.rectangle([2 * W + gx * W / grid, gy * H / grid, 2 * W + (gx + 1) * W / grid, (gy + 1) * H / grid], outline=(255, 255, 0))
        im.save(out); r['image'] = out
    return r

# ---------------------------------------------------------------- 3D 로: 획 → shapely 도형(mm)
def to_shapely(spec, width_mm=None):
    """획(굵기 있는 선은 버퍼, 채움은 다각형) → 합친 도형, y 위(+)·왼쪽 아래 (0,0). 판 위 부조·인레이로 압출할 때(svg2d 와 같은 좌표 규칙)."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    from shapely.affinity import scale as sscale
    spec = load(spec); gs = []
    for _, _, st, P in strokes(spec):
        P = np.c_[P[:, 0], spec['height'] - P[:, 1]]
        if st.get('fill') not in (None, 'none') and len(P) > 2: gs.append(Polygon(P).buffer(0))
        w = float(st.get('width', 1))
        if w > 0 and st.get('stroke') != 'none': gs.append(LineString(P).buffer(w / 2, cap_style=1, join_style=1) if len(P) > 1 else Polygon())
    g = unary_union(gs); k = (width_mm / spec['width']) if width_mm else 1.0
    return sscale(g, k, k, origin=(0, 0))

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest='cmd', required=True)
    a = sp.add_parser('draw'); a.add_argument('spec'); a.add_argument('--out', required=True)
    b = sp.add_parser('trace'); b.add_argument('image'); b.add_argument('--out', required=True); b.add_argument('--strokes', type=int, default=300); b.add_argument('--size', type=int, default=160)
    b.add_argument('--kinds', default='line,curve'); b.add_argument('--colors', type=int, default=0); b.add_argument('--palette', default=''); b.add_argument('--alpha', type=float, default=0.85)
    b.add_argument('--init'); b.add_argument('--seed', type=int, default=0)
    c = sp.add_parser('score'); c.add_argument('drawing'); c.add_argument('target'); c.add_argument('--out')
    x = ap.parse_args()
    if x.cmd == 'draw': r = draw(x.spec, x.out)
    elif x.cmd == 'trace': r = trace(x.image, x.out, x.strokes, x.size, x.kinds, x.alpha, [p for p in x.palette.split(',') if p] or None, x.colors, init=x.init, seed=x.seed)
    else: r = score(x.drawing, x.target, x.out)
    print(json.dumps(r, ensure_ascii=False, indent=1))
