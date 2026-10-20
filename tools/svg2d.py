#!/usr/bin/env python3
"""SVG 로고 → shapely 2D 도형(mm). 로고·문양을 판 위 부조/인레이로 압출할 때 쓴다.
  from svg2d import load_svg, thin_parts
  g = load_svg('sample/logo.svg', width_mm=40)     # 폭 40 mm 로 축척, y 위쪽(+), 왼쪽 아래가 (0,0)
  thin = thin_parts(g, 0.8)                         # 폭 0.8 mm 보다 가는 부분(노즐 두 줄 미만)
채우기 규칙: 한 <path> 안의 하위 경로는 짝홀(even-odd)로 구멍을 만들고, 경로끼리는 합친다(일반 로고 SVG 기준).
CLI: python tools/svg2d.py <svg> --width 40 --min 0.8 --out fig.png  → 크기·면적·조각·가는 부분 면적 JSON + 그림"""
import sys, json, argparse, numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import scale as sscale, translate

def _rings(path, step):
    from svgelements import Move, Close
    rings, cur = [], []
    for seg in path:
        if isinstance(seg, Move):
            if len(cur) > 2: rings.append(cur)
            cur = [(seg.end.x, seg.end.y)]; continue
        if seg.start is None or seg.end is None: continue
        L = seg.length() if hasattr(seg, 'length') else 0
        n = max(1, int(np.ceil((L or 0) / step)))
        cur += [(p.x, p.y) for p in (seg.point(t) for t in np.linspace(0, 1, n + 1)[1:])]
        if isinstance(seg, Close) and len(cur) > 2: rings.append(cur); cur = []
    if len(cur) > 2: rings.append(cur)
    return rings

def load_svg(path, width_mm=None, step=0.5):
    """SVG 의 모든 path(변환 적용) → 하나의 도형. step: 원본 단위 곡선 샘플 간격. width_mm 를 주면 그 폭으로 축척."""
    from svgelements import SVG, Path as SPath, Shape
    svg = SVG.parse(path); geoms = []
    for el in svg.elements():
        if not isinstance(el, Shape): continue
        p = SPath(el); p.reify()
        g = Polygon()
        for r in _rings(p, step):
            q = Polygon(r).buffer(0)
            if not q.is_empty: g = g.symmetric_difference(q)
        if not g.is_empty: geoms.append(g)
    g = unary_union(geoms)
    g = sscale(g, 1, -1, origin=(0, 0))                        # SVG y 아래(+) → 위(+)
    x0, y0, x1, y1 = g.bounds; g = translate(g, -x0, -y0)
    if width_mm: k = width_mm / (x1 - x0); g = sscale(g, k, k, origin=(0, 0))
    return g

def thin_parts(g, w):
    """폭 w 보다 가는 부분 = g − opening(g, w/2)."""
    return g.difference(g.buffer(-w / 2, join_style=2).buffer(w / 2, join_style=2))

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('svg'); ap.add_argument('--width', type=float, required=True)
    ap.add_argument('--min', type=float, default=0.8); ap.add_argument('--out'); a = ap.parse_args(argv)
    g = load_svg(a.svg, a.width); t = thin_parts(g, a.min); x0, y0, x1, y1 = g.bounds
    parts = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
    res = {'size_mm': [round(x1 - x0, 2), round(y1 - y0, 2)], 'area_mm2': round(g.area, 1), 'pieces': len(parts),
           'holes': sum(len(p.interiors) for p in parts), f'thinner_than_{a.min}_mm2': round(t.area, 2)}
    if a.out:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 10 * (y1 - y0) / (x1 - x0) + 1.2), dpi=120)
        for G, c in ((g, '#9aa0a6'), (t, '#e53935')):
            for p in (G.geoms if hasattr(G, 'geoms') else [G]):
                if p.geom_type != 'Polygon' or p.is_empty: continue
                ax.fill(*p.exterior.xy, color=c, lw=0)
                for h in p.interiors: ax.fill(*h.xy, color='white', lw=0)
        ax.set_aspect('equal'); ax.grid(True, alpha=.3); ax.set_title(f"{res['size_mm'][0]}×{res['size_mm'][1]} mm · 조각 {res['pieces']} · 빨강 = 폭 {a.min} mm 미만 {res[f'thinner_than_{a.min}_mm2']} mm²")
        fig.savefig(a.out, bbox_inches='tight'); res['png'] = a.out
    print(json.dumps(res, ensure_ascii=False)); return res

if __name__ == '__main__': main()
