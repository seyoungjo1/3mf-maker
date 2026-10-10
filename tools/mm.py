#!/usr/bin/env python3
"""3mf-maker 표준 프로그램 — 모든 모델링 검사·렌더·3MF·파이프라인 작업의 단일 입구.
같은 기능을 세 가지로 부른다(결과는 항상 JSON 직렬화 가능한 dict):
  1) 명령줄:  python tools/mm.py <명령> [인자…]           (python tools/mm.py help)
  2) 파이썬:  import sys; sys.path.insert(0,'tools'); import mm; mm.run('qc', files=['a.3mf'], out='qc/x')
  3) HTTP:    python tools/mm.py serve --port 8765  →  POST /run  {"cmd":"qc","args":{"files":["a.3mf"],"out":"qc/x"}}
             GET /commands (명령 목록), GET /schema (Claude API tool 정의)
  Claude API(tool use)에서 쓰려면 `python tools/mm.py schema` 의 tools 배열을 그대로 tools= 에 넣고, tool_use 의 name/input 을 mm.run(name, **input) 으로 실행한다.
메시 지정: 'a.3mf'(모든 파트) · 'a.3mf:lid'(한 파트) · 'a.stl' · 'parts.pkl:lid'(pickle dict 의 키)
"""
import os, sys, json, pickle, argparse, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
COMMANDS = {}
def command(name, desc, params):
    def deco(fn): COMMANDS[name] = {'fn': fn, 'desc': desc, 'params': params}; return fn
    return deco
def _abs(p): return p if os.path.isabs(p) else os.path.join(os.getcwd(), p)
def load_any(spec):
    """메시 지정 문자열 → {이름: trimesh}"""
    import trimesh
    path, _, key = spec.partition(':') if not os.path.exists(spec) else (spec, '', '')
    path = _abs(path)
    if path.endswith('.pkl'):
        d = pickle.load(open(path, 'rb')); d = d if isinstance(d, dict) else {'mesh': d}
        return {key: d[key]} if key else d
    if path.endswith('.3mf'):
        from load3mf import load_parts; d = load_parts(path); return {key: d[key]} if key else d
    m = trimesh.load(path, force='mesh'); return {os.path.splitext(os.path.basename(path))[0]: m}
def _meshes(specs):
    out = {}
    for s in specs:
        for n, m in load_any(s).items():
            k = n if n not in out else f"{os.path.basename(s.split(':')[0])}:{n}"      # 이름이 겹치면 파일 이름을 붙인다
            if k in out: k = s
            out[k] = m
    return out
# ---------------------------------------------------------------- 명령
@command('doctor', '환경 점검: 파이썬 의존·Chromium·렌더러·main 동기화 상태', {})
def doctor():
    r = {}
    for mod in ['trimesh', 'shapely', 'manifold3d', 'lib3mf', 'playwright', 'fast_simplification']:
        try: __import__(mod); r[mod] = 'ok'
        except Exception as e: r[mod] = f'없음: {e}'
    r['chromium'] = os.path.exists('/opt/pw-browsers/chromium')
    try: r['git'] = subprocess.run(['git', '-C', ROOT, 'log', '--oneline', '-1'], capture_output=True, text=True).stdout.strip()
    except Exception as e: r['git'] = str(e)
    return r
@command('qc', '출력 방향 파트 QC(닫힘·조각·삼각형·접지·얇은 살·벽 속 수평 틈·오버행/브리지, EFC 반영)',
         {'files': {'type': 'array', 'items': {'type': 'string'}, 'description': '메시 지정 목록'}, 'efc': {'type': 'number', 'default': 0.15}, 'max_bridge': {'type': 'number', 'default': 7.0}})
def qc(files, efc=0.15, max_bridge=7.0):
    from qc_model import qc_part
    qa = argparse.Namespace(layer=0.2, min_wall=1.2, max_tri=200000, max_bridge=max_bridge, efc=efc, single_wall=[])
    return {n: qc_part(n, m, qa) for n, m in _meshes(files).items()}
@command('slits', '벽 속 수평 틈(출력물 옆면 줄의 원인) 검사', {'files': {'type': 'array', 'items': {'type': 'string'}}})
def slits(files):
    import collections; from qc_model import internal_gaps
    out = {}
    for n, m in _meshes(files).items():
        g = [x for x in internal_gaps(m) if x[0] == 2]; cl = collections.Counter(round(x[2][2], 1) for x in g)
        out[n] = {'slit_z': sorted(z for z, c in cl.items() if c >= 10), 'rays': len(g)}
    return out
@command('section', '단면 그림(PNG) — 평면 x=/y=/z= 값으로 자른 윤곽을 여러 메시 겹쳐 그림, 실측 근거용',
         {'files': {'type': 'array', 'items': {'type': 'string'}}, 'plane': {'type': 'string', 'description': '예 "y=130"'}, 'out': {'type': 'string'},
          'xlim': {'type': 'array', 'items': {'type': 'number'}}, 'ylim': {'type': 'array', 'items': {'type': 'number'}}, 'title': {'type': 'string'}})
def section(files, plane, out, xlim=None, ylim=None, title=''):
    import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    ax_name, _, v = plane.partition('='); ai = 'xyz'.index(ax_name.strip()); v = float(v); keep = [i for i in range(3) if i != ai]
    n = np.zeros(3); n[ai] = 1; o = np.zeros(3); o[ai] = v
    fig, ax = plt.subplots(figsize=(8, 6)); cols = ['k', 'r', 'g', 'b', 'm', 'c']; segs = {}
    for k, (nm, m) in enumerate(_meshes(files).items()):
        s = m.section(plane_origin=o, plane_normal=n)
        if s is None: segs[nm] = 0; continue
        for j, e in enumerate(s.entities):
            p = s.vertices[e.points]; ax.plot(p[:, keep[0]], p[:, keep[1]], cols[k % 6] + '-', lw=1.2, label=nm if j == 0 else None)
        segs[nm] = len(s.entities)
    if xlim: ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    ax.set_aspect('equal'); ax.grid(True, alpha=.3); ax.legend(); ax.set_xlabel('xyz'[keep[0]]); ax.set_ylabel('xyz'[keep[1]]); ax.set_title(title or plane)
    os.makedirs(os.path.dirname(_abs(out)) or '.', exist_ok=True); fig.savefig(_abs(out), dpi=90, bbox_inches='tight'); plt.close(fig)
    return {'png': _abs(out), 'loops': segs}
@command('crop', '메시를 상자로 잘라 STL 저장(클로즈업 렌더·비교용). flip_x=true 면 x축 180° 뒤집기(뒤집어 출력한 뚜껑을 조립 방향으로), 결과를 offset 위치로 옮김',
         {'file': {'type': 'string'}, 'box': {'type': 'array', 'items': {'type': 'number'}, 'description': '[x0,y0,z0,x1,y1,z1]'}, 'out': {'type': 'string'},
          'flip_x': {'type': 'boolean', 'default': False}, 'offset': {'type': 'array', 'items': {'type': 'number'}, 'default': [0, 0, 0]}})
def crop(file, box, out, flip_x=False, offset=(0, 0, 0)):
    import numpy as np, trimesh
    from trimesh.transformations import rotation_matrix
    (n, m), = load_any(file).items() if len(load_any(file)) == 1 else [(k, v) for k, v in load_any(file).items()][:1]
    lo, hi = np.array(box[:3], float), np.array(box[3:], float); bx = trimesh.creation.box(extents=hi - lo); bx.apply_translation((lo + hi) / 2)
    c = trimesh.boolean.intersection([m, bx], engine='manifold')
    if flip_x: c.apply_transform(rotation_matrix(np.pi, [1, 0, 0]))
    c.apply_translation(-c.bounds[0] + np.asarray(offset, float)); os.makedirs(os.path.dirname(_abs(out)) or '.', exist_ok=True); c.export(_abs(out))
    return {'stl': _abs(out), 'faces': len(c.faces), 'bounds': c.bounds.round(2).tolist(), 'is_volume': bool(c.is_volume)}
@command('wallscan', '바깥 벽 단차 검사(출력물 가로줄): 파트 중심에서 n_dir 방향으로 바깥 벽을 z 0.02 간격으로 재서 0.02~0.3 mm 턱이 갑자기 생기는 높이·위치를 보고',
         {'files': {'type': 'array', 'items': {'type': 'string'}}, 'z_range': {'type': 'array', 'items': {'type': 'number'}, 'default': None}, 'n_dir': {'type': 'integer', 'default': 48}})
def wallscan(files, z_range=None, n_dir=48):
    from qc_model import wall_steps
    return {n: wall_steps(m, z_range=z_range, n_dir=n_dir) for n, m in _meshes(files).items()}
@command('render', 'three.js 렌더: 5뷰 PNG + 회전 GIF(상태 순환 가능)',
         {'files': {'type': 'array', 'items': {'type': 'string'}}, 'out': {'type': 'string'}, 'colors': {'type': 'object'}, 'states': {'type': 'object'}, 'frames': {'type': 'integer', 'default': 36}, 'status': {'type': 'string'}})
def render(files, out, colors=None, states=None, frames=36, status=None):
    from render_preview import render as r3
    parts = _meshes(files); pngs = r3(parts, _abs(out), colors or {}, states, frames, status=status)
    return {'pngs': pngs, 'gif': os.path.join(_abs(out), 'turntable.gif')}
@command('check3mf', 'lib3mf strict 모드 경고 수(ASCII 임시 경로에서)', {'files': {'type': 'array', 'items': {'type': 'string'}}})
def check3mf(files):
    import shutil, tempfile; from check3mf import check
    out = {}; tmp = tempfile.mkdtemp()
    for i, f in enumerate(files):
        p = os.path.join(tmp, f'p{i}.3mf'); shutil.copy(_abs(f), p); n, w, c = check(p); out[f] = {'warnings': n, 'messages': w[:5], 'objects': c}
    shutil.rmtree(tmp, ignore_errors=True); return out
@command('pipeline', '게이트 파이프라인: QC → 플레이트 3MF(충돌·베드·strict) → 조립 검증 → 렌더/GIF → REPORT.md (⚠ 있으면 ok=false)',
         {'config': {'type': 'string', 'description': '프로젝트 pipeline_*.json'}, 'render_only': {'type': 'boolean', 'default': False}})
def pipeline(config, render_only=False):
    import pipeline as PL
    rc = PL.run(_abs(config), render_only=render_only); cfg = json.load(open(_abs(config), encoding='utf-8'))
    out = os.path.join(os.path.dirname(_abs(config)), cfg['out']); rep = json.load(open(os.path.join(out, 'report.json'))) if os.path.exists(os.path.join(out, 'report.json')) else {}
    return {'ok': rc == 0, 'report': os.path.join(out, 'REPORT.md'), 'warn': rep.get('warn', []), 'info': rep.get('info', [])}
@command('assemble', '조립 검증만(파이프라인과 같은 코드): config 의 조립 정의로 상태별 교집합·간격·스윕. override 로 파트를 다른 버전으로 바꿔 끼워 호환성 확인(예: 이미 출력한 v8 하판 + 새 뚜껑)',
         {'config': {'type': 'string'}, 'override': {'type': 'object', 'default': None, 'description': '{"파트이름": "메시 지정"} 예 {"base": "v8parts_nominal.pkl:base"} (config 폴더 기준 경로)'}, 'out': {'type': 'string', 'default': None}})
def assemble(config, override=None, out=None):
    import importlib.util, pipeline as PL
    cfg = json.load(open(_abs(config), encoding='utf-8')); base = os.path.dirname(_abs(config)); P = lambda p: os.path.join(base, p)
    nominal = pickle.load(open(P(cfg.get('assembly_parts_pkl') or cfg['parts_pkl']), 'rb')); used = {}
    for n, spec in (override or {}).items():
        path, _, key = spec.partition(':'); m = load_any(P(path) + (':' + key if key else '')); nominal[n] = m[key or n] if (key or n) in m else next(iter(m.values())); used[n] = spec
    spec_ = importlib.util.spec_from_file_location('asm', P(cfg['assembly'])); mod = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(mod)
    asm = mod.define(nominal); allparts = dict(nominal); allparts.update(asm.get('extra', {}))
    L, warn = [f"# 조립 검증 — {cfg['name']}" + (f" · 바꿔 끼움 {used}" if used else ''), ''], []
    PL.check_assembly(asm, allparts, cfg.get('min_gap', 0.3), L, warn)
    if out: os.makedirs(os.path.dirname(_abs(out)) or '.', exist_ok=True); open(_abs(out), 'w', encoding='utf-8').write('\n'.join(L) + '\n\n' + ('\n'.join('- ⚠ ' + w for w in warn) or '- ✓ 경고 없음') + '\n')
    return {'ok': not warn, 'override': used, 'warn': warn, 'report': _abs(out) if out else None, 'table': [l for l in L if l.startswith('|') or '간섭 0 범위' in l]}
@command('bambu', 'Bambu Studio 프로젝트 3MF 로 변환(사용자 내보내기 3MF 를 틀로, 설정은 틀 그대로 + 허용된 키만 변경) 후 구조 검증. "형상만 불러옴" 해결용',
         {'plate': {'type': 'string', 'description': '우리 플레이트 3MF(generic)'}, 'out': {'type': 'string'}, 'template': {'type': 'string', 'default': None},
          'colors': {'type': 'array', 'items': {'type': 'string'}, 'default': None}, 'settings': {'type': 'object', 'default': None, 'description': '틀에 있는 키만, 같은 형식으로 예 {"enable_support":"1","support_on_build_plate_only":"1"}'},
          'plate_name': {'type': 'string', 'default': ''}, 'title': {'type': 'string', 'default': ''}})
def bambu(plate, out, template=None, colors=None, settings=None, plate_name='', title=''):
    import bambu_project as BP
    tpl = _abs(template) if template else BP.DEFAULT_TEMPLATE; obs = BP.read_plate(_abs(plate))
    BP.write_bambu_project(_abs(out), obs, tpl, plate_name, colors, settings, title)
    r = BP.verify_bambu_project(_abs(out), tpl, obs); r['template'] = tpl; return r
@command('make', '빌드 → 파이프라인 일괄: config 의 "build": [스크립트, 인자…] 를 config 폴더에서 실행한 뒤 pipeline',
         {'config': {'type': 'string'}})
def make(config):
    cfg = json.load(open(_abs(config), encoding='utf-8')); base = os.path.dirname(_abs(config)); t = time.time()
    if cfg.get('build'):
        p = subprocess.run([sys.executable] + cfg['build'], cwd=base, capture_output=True, text=True)
        if p.returncode: return {'ok': False, 'stage': 'build', 'stderr': p.stderr[-3000:]}
    r = pipeline(config); r['build_log_tail'] = (p.stdout[-1500:] if cfg.get('build') else ''); r['seconds'] = round(time.time() - t); return r
@command('selftest', '도구 자가검사(정상/간섭/빡빡한 끼움/EFC 그룹/실제 모서리/벽 속 틈)', {})
def selftest():
    p = subprocess.run([sys.executable, os.path.join(HERE, 'selftest.py')], capture_output=True, text=True)
    lines = [l for l in p.stdout.splitlines() if l.startswith('[') or 'SELFTEST' in l]
    return {'ok': p.returncode == 0, 'lines': lines}
# ---------------------------------------------------------------- 실행기
def run(cmd, **args):
    if cmd not in COMMANDS: return {'error': f'모르는 명령 {cmd}', 'commands': list(COMMANDS)}
    return COMMANDS[cmd]['fn'](**args)
def schema():
    tools = []
    for n, c in COMMANDS.items():
        req = [k for k, v in c['params'].items() if 'default' not in v]
        tools.append({'name': f'mm_{n}', 'description': c['desc'], 'input_schema': {'type': 'object', 'properties': c['params'], 'required': req}})
    return {'tools': tools, 'note': 'tool_use name 에서 mm_ 를 떼고 mm.run(name, **input) 으로 실행'}
def serve(port=8765):
    import http.server
    class H(http.server.BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj, ensure_ascii=False, default=str).encode(); self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
        def do_GET(self):
            if self.path == '/commands': self._send(200, {n: c['desc'] for n, c in COMMANDS.items()})
            elif self.path == '/schema': self._send(200, schema())
            else: self._send(404, {'error': 'GET /commands, GET /schema, POST /run'})
        def do_POST(self):
            if self.path != '/run': return self._send(404, {'error': 'POST /run'})
            try:
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}'); name = body.get('cmd', '').removeprefix('mm_')
                self._send(200, run(name, **body.get('args', {})))
            except Exception as e: self._send(500, {'error': f'{type(e).__name__}: {e}'})
        def log_message(self, *a): pass
    print(f'mm API: http://127.0.0.1:{port}  (POST /run, GET /commands, GET /schema)', flush=True)
    http.server.ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
def main(argv):
    if not argv or argv[0] in ('help', '-h', '--help'):
        print(__doc__); [print(f'  {n:10s} {c["desc"]}') for n, c in COMMANDS.items()]; print('  schema     Claude API tool 정의 출력\n  serve      HTTP JSON API (--port 8765)'); return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == 'schema': print(json.dumps(schema(), ensure_ascii=False, indent=1)); return 0
    if cmd == 'serve': serve(int(rest[rest.index('--port') + 1]) if '--port' in rest else 8765); return 0
    if cmd not in COMMANDS: print(f'모르는 명령 {cmd}. python tools/mm.py help'); return 2
    ap = argparse.ArgumentParser(prog=f'mm.py {cmd}')
    for k, v in COMMANDS[cmd]['params'].items():
        t = v.get('type')
        if t == 'array': ap.add_argument(k if k == 'files' else f'--{k}', nargs='+', type=(float if v.get('items', {}).get('type') == 'number' else str), default=v.get('default'))
        elif t == 'object': ap.add_argument(f'--{k}', type=json.loads, default=v.get('default'))
        elif t == 'boolean': ap.add_argument(f'--{k}', action='store_true')
        elif k == 'config': ap.add_argument(k)
        else: ap.add_argument(f'--{k}', type=(float if t == 'number' else int if t == 'integer' else str), default=v.get('default'), required='default' not in v)
    a = vars(ap.parse_args(rest)); res = run(cmd, **{k: v for k, v in a.items() if v is not None})
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    return 0 if res.get('ok', True) is not False else 1
if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
