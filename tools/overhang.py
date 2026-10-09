"""0.2 mm 층당 수평 돌출 ≤ 0.115 mm 규칙 검사 + 브리지(양쪽 지지)/오버행(한쪽 지지) 분류.
- check(mesh): 예전 방식 — 층 윤곽이 아래층 윤곽 ⊕ 0.115 를 벗어난 면적(브리지 포함) 합계.
- classify(mesh): 벗어난 영역을 0.5 mm 격자로 샘플링해, 8방향으로 아래층까지 거리를 재서 135°/180° 떨어진 두 방향이 모두 (max_bridge 안에) 닿으면 '브리지'(스팬=거리 합), 아니면 '오버행(캔틸레버)'.
  돌려주는 값: dict(overhang_mm2, bridge_mm2, bridge_max_span, overhang_top=[(z, mm2, bounds)], bridge_top=[(z, mm2, span)]).
  슬라이서는 양쪽 지지 영역을 브리지로 출력하므로 스팬 ≤ max_bridge 면 허용. 한쪽 긴 변만 받친 띠는 길이 방향 스팬(기둥 사이)으로 잡혀 폭 초과로 걸린다.
"""
import numpy as np, shapely
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import affine_transform
def layer_poly(mesh, z):
    """z 높이 단면 폴리곤. 겹치는 조각(여러 바디가 겹친 오브젝트)도 닫힌 윤곽을 각각 합쳐 복구한다."""
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None: return Polygon()
    p2, T = sec.to_2D(normal=[0, 0, 1])
    a, b, c, d, xo, yo = T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]
    try:
        polys = list(p2.polygons_full)
        if not polys: return Polygon()
        return unary_union([affine_transform(q, [a, b, c, d, xo, yo]) for q in polys]).buffer(0)
    except Exception:
        polys = [Polygon(q.exterior.coords) for q in p2.polygons_closed if q is not None and q.area > 1e-6]
        if not polys: return Polygon()
        return unary_union([affine_transform(q, [a, b, c, d, xo, yo]).buffer(0) for q in polys]).buffer(0)
def check(mesh, layer=0.2, maxstep=0.115, min_area=0.5):
    """returns (total_area, [(z, area, bounds), ...] sorted by area desc)"""
    zmax = mesh.bounds[1, 2]; prev = None; bad = []; total = 0.0; z = layer / 2 + 0.0137
    while z < zmax:
        cur = layer_poly(mesh, z)
        if prev is not None and not cur.is_empty:
            unsup = cur.difference(prev.buffer(maxstep)); a = unsup.area
            if a > min_area: bad.append((round(z, 2), round(a, 1), tuple(round(v, 1) for v in unsup.bounds))); total += a
        prev = cur; z += layer
    bad.sort(key=lambda t: -t[1]); return total, bad
def _width(poly):
    """최대 내접원 지름(이진 탐색)"""
    lo, hi = 0.0, 0.5 * max(poly.bounds[2] - poly.bounds[0], poly.bounds[3] - poly.bounds[1]) + 0.01
    for _ in range(18):
        mid = (lo + hi) / 2
        if poly.buffer(-mid).is_empty: hi = mid
        else: lo = mid
    return 2 * lo
_DIRS = [np.array([np.cos(t), np.sin(t)]) for t in np.arange(8) * np.pi / 4]     # 0,45,…,315°
def _split(unsup, prev, max_bridge, grid=0.5):
    """unsup 영역을 브리지/오버행 면적으로 나눈다.
    각 샘플 점에서 8방향으로 (max_bridge+0.3) 길이 선분을 쏘아 아래층(prev)에 닿는 거리를 잰다.
    서로 135°/180° 떨어진 두 방향이 모두 닿으면 그 점은 '브리지'(스팬 = 두 거리 합), 아니면 '오버행(한쪽 지지)'.
    반환 (bridge_area, overhang_area, max_span)."""
    if unsup.is_empty: return 0.0, 0.0, 0.0
    polys = list(unsup.geoms) if isinstance(unsup, MultiPolygon) else [unsup]
    br_a = oh_a = 0.0; span_max = 0.0; L = max_bridge + 0.3
    for c in polys:
        if c.area < 1e-6: continue
        x0, y0, x1, y1 = c.bounds
        xs = np.arange(x0 + grid / 2, x1, grid); ys = np.arange(y0 + grid / 2, y1, grid)
        pts = np.zeros((0, 2))
        if len(xs) and len(ys):
            gx, gy = np.meshgrid(xs, ys); pts = np.column_stack([gx.ravel(), gy.ravel()])
            pts = pts[shapely.contains_xy(c, pts[:, 0], pts[:, 1])]
        if len(pts) == 0: rp = c.representative_point(); pts = np.array([[rp.x, rp.y]])
        P = shapely.points(pts); dist = np.full((8, len(pts)), np.inf)
        for k, d in enumerate(_DIRS):
            seg = shapely.linestrings(np.stack([pts, pts + d * L], axis=1))
            inter = shapely.intersection(seg, prev); ok = ~shapely.is_empty(inter)
            if ok.any(): dist[k, ok] = shapely.distance(P[ok], inter[ok])
        span = np.full(len(pts), np.inf)
        for k in range(8):
            for j in (3, 4):                                            # 135°, 180° 떨어진 짝
                span = np.minimum(span, dist[k] + dist[(k + j) % 8])
        bridged = np.isfinite(span); frac = bridged.mean()
        br_a += c.area * frac; oh_a += c.area * (1 - frac)
        if bridged.any(): span_max = max(span_max, float(span[bridged].max()))
    return br_a, oh_a, span_max
def classify(mesh, layer=0.2, maxstep=0.115, max_bridge=7.0, min_area=0.5, efc=0.0):
    """efc: 슬라이서 코끼리발 보정 — 첫 층 윤곽을 efc 만큼 깎은 것을 2층의 받침으로 본다(출력물 기준 규칙)."""
    zmax = mesh.bounds[1, 2]; prev = None; z = layer / 2 + 0.0137; first = True
    oh_tot = br_tot = 0.0; span_max = 0.0; oh_top = []; br_top = []
    while z < zmax:
        cur = layer_poly(mesh, z)
        if first and efc > 0 and not cur.is_empty: cur_support = cur.buffer(-efc, join_style='mitre')
        else: cur_support = cur
        if prev is not None and not cur.is_empty:
            unsup = cur.difference(prev.buffer(maxstep))
            if unsup.area > min_area:
                br, oh, sp = _split(unsup, prev, max_bridge)
                br_tot += br; oh_tot += oh; span_max = max(span_max, sp)
                if oh > min_area: oh_top.append((round(z, 2), round(oh, 1), tuple(round(v, 1) for v in unsup.bounds)))
                if br > min_area: br_top.append((round(z, 2), round(br, 1), round(sp, 1)))
        prev = cur_support; first = False; z += layer
    oh_top.sort(key=lambda t: -t[1]); br_top.sort(key=lambda t: -t[1])
    return dict(overhang_mm2=oh_tot, bridge_mm2=br_tot, bridge_max_span=span_max, overhang_top=oh_top, bridge_top=br_top)
