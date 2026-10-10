"""링 로프트: 높이별 외곽 폴리곤을 매끈하게 이어 닫힌 메시를 만든다(계단 없음).
판(slab)을 쌓으면 층마다 수평 턱이 생겨 출력물·렌더에 줄이 보인다(Toolbox48 v7 본체 바닥 0.1 판 계단) — 그 대신 쓴다.
loft_rings([(z, Polygon), ...], M=1200) → trimesh. 각 폴리곤은 구멍 없는 단일 외곽(가장 큰 것만 씀).
링마다 둘레를 같은 비율로 M 점 재샘플하고, 시작점을 이전 링의 시작점과 가장 가까운 점으로 맞춰 꼬임을 막는다."""
import numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon, Point
from trimesh.creation import triangulate_polygon
def _ring(poly, M, ref=None):
    g = max(poly.geoms, key=lambda q: q.area) if isinstance(poly, MultiPolygon) else poly
    ext = g.exterior; L = ext.length
    st = ext.project(Point(ref)) if ref is not None else ext.project(Point(g.bounds[0], g.bounds[1]))
    t = (st + np.linspace(0, L, M, endpoint=False)) % L
    pts = np.array([ext.interpolate(v).coords[0] for v in t])
    return pts if ext.is_ccw else np.vstack([pts[:1], pts[1:][::-1]])
def loft_rings(stack, M=1200):
    stack = sorted(stack, key=lambda s: s[0]); rings = []; ref = None
    for z, poly in stack:
        r = _ring(poly, M, ref); ref = r[0]; rings.append((z, r))
    V = np.vstack([np.column_stack([r, np.full(M, z)]) for z, r in rings]); F = []
    i = np.arange(M); j = (i + 1) % M
    for k in range(len(rings) - 1):
        a, b = k * M, (k + 1) * M; F.append(np.column_stack([a + i, a + j, b + j])); F.append(np.column_stack([a + i, b + j, b + i]))
    F = np.vstack(F).tolist()
    for k, sign in [(0, -1), (len(rings) - 1, 1)]:
        z, r = rings[k]; vv, ff = triangulate_polygon(Polygon(r), engine='earcut'); bi = len(V)
        V = np.vstack([V, np.column_stack([vv, np.full(len(vv), z)])]); F.extend(((ff[:, ::-1] if sign < 0 else ff) + bi).tolist())
    m = trimesh.Trimesh(V, np.array(F), process=True); m.merge_vertices(); trimesh.repair.fix_normals(m)
    return m
