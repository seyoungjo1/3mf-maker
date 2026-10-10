"""뚜껑 v8: 윗면 모서리 = v5 의 연속 곡선(층당 ≤0.115, inset 1.69 → 0) 을 LAND 만큼 올리고, z<LAND 는 **곡선 시작 inset 자리에서** 수직.
v6 은 이 띠를 전체 윤곽으로 깔아 1.58 mm 턱(접시 테두리)이 생겼다 — 그 턱을 없앤다. 로고 포켓·경첩 귀·걸쇠 탭은 건드리지 않는다.
사용: python scripts/lid_v8.py ../toolbox42/v5parts.pkl [LAND=0.6] → lid_v8.pkl"""
import pickle, sys, os, numpy as np, trimesh
from shapely.geometry import Polygon, Point, box
from trimesh.creation import triangulate_polygon, extrude_polygon
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools')); from overhang import layer_poly
LAND = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
P = pickle.load(open(sys.argv[1], 'rb')); lid = P['lid']; logo = P['logo']
ZTOP = 7.8; M = 900; dz = 0.2; Z0 = 0.1137
def polys(p): return list(p.geoms) if p.geom_type == 'MultiPolygon' else [p]
def outer_ring(poly):
    ext = max(polys(poly), key=lambda q: q.area).exterior
    L = ext.length; xc = (poly.bounds[0] + poly.bounds[2]) / 2; st = ext.project(Point(xc, poly.bounds[1]))
    t = (st + np.linspace(0, L, M, endpoint=False)) % L; pts = np.array([ext.interpolate(v).coords[0] for v in t])
    return pts if ext.is_ccw else pts[::-1]
full_ext = Polygon(outer_ring(layer_poly(lid, ZTOP)))                 # 전체 윤곽(수직 벽 구간)
first_ring = outer_ring(layer_poly(lid, Z0))                            # v5 첫 층 윤곽 = 곡선 시작(inset 1.69)
zs = np.round(np.arange(0, ZTOP + dz / 2, dz), 3); rings = []
for z in zs:
    zsrc = z - LAND
    rings.append(first_ring if zsrc < Z0 else outer_ring(layer_poly(lid, min(zsrc, ZTOP))))
V = np.vstack([np.column_stack([r, np.full(M, z)]) for z, r in zip(zs, rings)]); F = []
for k in range(len(zs) - 1):
    a = k * M; b = (k + 1) * M; i = np.arange(M); j = (i + 1) % M; F.append(np.column_stack([a + i, a + j, b + j])); F.append(np.column_stack([a + i, b + j, b + i]))
F = np.vstack(F).tolist()
for k, sign in [(0, -1), (len(zs) - 1, 1)]:
    vv, ff = triangulate_polygon(Polygon(rings[k]), engine='earcut'); bi = len(V); V = np.vstack([V, np.column_stack([vv, np.full(len(vv), zs[k])])]); F.extend(((ff[:, ::-1] if sign < 0 else ff) + bi).tolist())
loft = trimesh.Trimesh(V, np.array(F), process=True); loft.merge_vertices(); trimesh.repair.fix_normals(loft); print('loft is_volume', loft.is_volume)
band = full_ext.buffer(0.6).difference(full_ext.buffer(-4.0)).difference(box(415, 183, 456, 200))   # 바깥 4 mm 띠, 걸쇠 탭 구역 제외
cut_region = extrude_polygon(band, ZTOP + 0.2); cut_region.apply_translation([0, 0, -0.1])
lip = cut_region.difference(loft, engine='manifold')
lid8 = lid.difference(lip, engine='manifold'); lid8.apply_translation([0, 0, -lid8.bounds[0, 2]])
print('lid8 is_volume', lid8.is_volume, 'vol', round(lid.volume), '->', round(lid8.volume), 'faces', len(lid8.faces), 'lid∩logo', round(lid8.intersection(logo, engine='manifold').volume, 3), 'bounds', lid8.bounds.round(2).tolist())
def region_vol(m, b):
    bx = trimesh.creation.box(extents=[b[1][0] - b[0][0], b[1][1] - b[0][1], b[1][2] - b[0][2]]); bx.apply_translation([(b[0][i] + b[1][i]) / 2 for i in range(3)]); r = m.intersection(bx, engine='manifold'); return round(r.volume, 2) if r.is_volume else 0
for nm, bb in [('경첩 귀 구역', [[340, 60, 8], [530, 72, 19]]), ('걸쇠 탭 구역', [[415, 183, 3], [456, 200, 19]])]:
    print(f'  {nm}: v5 {region_vol(lid, bb)} / v8 {region_vol(lid8, bb)} mm³')
zz = np.arange(Z0, 8.0, 0.2)
def prof(m): xs = np.array([layer_poly(m, z).bounds[0] for z in zz]); return xs - xs[zz > 7.5].min()
p5 = prof(lid); p8 = prof(lid8); pb = prof(P['base'])
print(' z    본체    v5    v8')
for z, a, b, c in zip(zz, pb, p5, p8):
    if z < 2.2 or abs(z - round(z)) < 0.11: print(f'{z:5.2f} {a:6.2f} {b:6.2f} {c:6.2f}')
print('첫층 면적 v5 %.0f → v8 %.0f ; 층당 바깥 돌출 최대 v8 %.3f (z<%.1f 구간 %.3f)' % (layer_poly(lid, Z0).area, layer_poly(lid8, Z0).area, -np.diff(p8).min(), LAND, -np.diff(p8[zz < LAND + 0.1]).min() if (zz < LAND + 0.1).sum() > 1 else 0))
pickle.dump(lid8, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lid_v8.pkl'), 'wb')); print('saved lid_v8.pkl')
