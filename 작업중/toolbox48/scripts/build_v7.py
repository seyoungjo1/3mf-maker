#!/usr/bin/env python3
"""Toolbox48 v7 — 42장 → 48장. 칸 깊이(앞 50.0 / 뒤 51.8) → 58.0 (명판 8장 × 7.0 + 여유 2.0).
본체·뚜껑을 각 칸 노치 중심에서 잘라 y 로 늘린다(앞 +8.0, 뒤 +6.2). 경첩·손잡이 귀·걸쇠 귀·탭·U자 홈 단면은 그대로.
추가 수정: 본체 바닥 곡선 ≤0.115/층 + 첫 층 EFC +0.15 선반영, 본체 립 바깥면 0.1 깎아 끼움 0.2 → 0.3(립 1.6 → 1.5), 손잡이·걸쇠 첫 층 EFC.
사용: python scripts/build_v7.py ../toolbox42/v5parts.pkl ../toolbox42/lid_v6.pkl"""
import sys, os, pickle, json, numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, '작업중', 'toolbox42', 'scripts')]
from overhang import layer_poly
from efc import pre_expand_first_layer
from generic3mf import write_generic_3mf
MODELS = os.path.join(HERE, '..', 'models'); DOCS = os.path.join(HERE, '..', 'docs')
C1, C2 = '#30949D', '#F2AF38'
# ---------------- 설계 매개변수 ----------------
PLATE_T = 7.0          # 명판 피치(본체 6.0 + 테두리 띠 1.0, 샘플 실측)
N_PER_BAY = 8; SLACK = 2.0; ROW = N_PER_BAY * PLATE_T + SLACK      # 58.0
FRONT_ROW0, REAR_ROW0 = 50.0, 51.8                                 # v5 실측
D_FRONT, D_REAR = ROW - FRONT_ROW0, ROW - REAR_ROW0                # 8.0, 6.2
CUT_FRONT, CUT_REAR = 106.75, 159.75                               # 본체 좌표: 칸막이 노치 중심(±1 mm 단면 동일 확인)
C0 = 260.81                                                        # 닫힘 상태 대응: base_y = C0 - lid_y (v5)
LIP_SHAVE = 0.1; ZC = 1.51; SLOPE = 0.115 / 0.2                    # 바닥 곡선: z<1.51 을 층당 0.115 로 제한
def polys(p): return [q for q in (p.geoms if isinstance(p, MultiPolygon) else [p]) if q.area > 1e-6]
def ext(p, h):
    ms = [extrude_polygon(q, h) for q in polys(p)]
    return ms[0] if len(ms) == 1 else trimesh.boolean.union(ms, engine='manifold')
def vol(m): return float(m.volume) if m.is_volume else 0.0
# ---------------- y 방향 늘리기 ----------------
def xz_polys(m, y):
    s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]); p2, T3 = s.to_planar(normal=[0, 1, 0])
    def xz(coords):
        c = np.asarray(coords); w = np.column_stack([c, np.zeros(len(c)), np.ones(len(c))]) @ T3.T; return [(x, -z) for x, _, z in w[:, :3]]
    return [Polygon(xz(q.exterior.coords), [xz(i.coords) for i in q.interiors]).buffer(0) for q in p2.polygons_full]
def filler(m, y, d):
    out = []
    for q in xz_polys(m, y):
        e = ext(q, d); e.apply_transform(R(-np.pi / 2, [1, 0, 0])); e.apply_translation([0, y, 0]); out.append(e)
    return out
def slab(m, y0, y1):
    bx = trimesh.creation.box(extents=[2000, y1 - y0, 2000]); bx.apply_translation([0, (y0 + y1) / 2, 0])
    return trimesh.boolean.intersection([m, bx], engine='manifold')
def stretch_y(m, cuts):
    cuts = sorted(cuts); b = m.bounds; edges = [b[0, 1] - 1] + [c for c, _ in cuts] + [b[1, 1] + 1]
    pieces = []; shift = 0.0
    for i in range(len(edges) - 1):
        p = slab(m, edges[i], edges[i + 1]); p.apply_translation([0, shift, 0]); pieces.append(p)
        if i < len(cuts):
            y, d = cuts[i]
            for f in filler(m, y, d): f.apply_translation([0, shift, 0]); pieces.append(f)
            shift += d
    return trimesh.boolean.union(pieces, engine='manifold')
# ---------------- 본체 바닥 곡선 ----------------
def fix_bottom(m):
    L = layer_poly(m, ZC); slabs = []
    for z0 in np.arange(0.0, ZC + 0.05, 0.1):
        zc = z0 + 0.05; d = max(0.0, SLOPE * (ZC - zc))
        new = L.buffer(-d, join_style='round').union(layer_poly(m, min(zc, ZC))).buffer(0)
        e = ext(new, 0.1 + 1e-3); e.apply_translation([0, 0, z0]); slabs.append(e)
    bx = trimesh.creation.box(extents=[2000, 2000, ZC]); bx.apply_translation([0, 0, ZC / 2])
    top = trimesh.boolean.difference([m, bx], engine='manifold')
    return trimesh.boolean.union([top] + slabs, engine='manifold')
# ---------------- 뚜껑 립 깎기(본체 쪽) ----------------
def shave_lip(m):
    """립(1.6 mm) **바깥면만** LIP_SHAVE 깎는다. 닫힘 실측: 뚜껑 스커트 안쪽면 ↔ 립 바깥면 0.20 이 유일한 끼움면(립 안쪽면엔 뚜껑이 없음). 0.1 → 끼움 0.3, 립 1.5."""
    ring = max(polys(layer_poly(m, 27.0)), key=lambda q: q.area)                  # 립 링(≈890 mm², 너클 ≈8 은 제외)
    outer = Polygon(ring.exterior); cutter = outer.buffer(0.6).difference(outer.buffer(-LIP_SHAVE)).buffer(0)
    e = ext(cutter, 31 - 26.45); e.apply_translation([0, 0, 26.45])
    return trimesh.boolean.difference([m, e], engine='manifold'), ring
if __name__ == '__main__':
    P = pickle.load(open(sys.argv[1], 'rb')); lid6 = pickle.load(open(sys.argv[2], 'rb'))
    base0, logo0, handle0, latch0 = P['base'], P['logo'], P['handle'], P['latch']
    # 1) 본체 늘리기
    base = stretch_y(base0, [(CUT_FRONT, D_FRONT), (CUT_REAR, D_REAR)])
    print('base stretched: is_volume', base.is_volume, 'bounds', base.bounds.round(2).tolist(), 'vol', round(base0.volume), '->', round(vol(base)))
    # 2) 립 깎기
    base, ring = shave_lip(base); print('lip shaved: is_volume', base.is_volume, 'vol', round(vol(base)), 'ring area', round(ring.area, 1))
    # 3) 바닥 곡선
    base = fix_bottom(base); base.apply_translation([0, 0, -base.bounds[0, 2]]); print('bottom fixed: is_volume', base.is_volume, 'vol', round(vol(base)), 'faces', len(base.faces))
    zz = np.arange(0.1137, 2.2, 0.2); xs = np.array([layer_poly(base, z).bounds[0] for z in zz]); ins = xs - layer_poly(base, 8.0).bounds[0]
    print('  바닥 inset(z):', ' '.join(f'{z:.2f}:{i:.2f}' for z, i in zip(zz, ins)), '| 층당 최대', round(float(np.max(-np.diff(ins))), 3))
    # 4) 첫 층 EFC 선반영 (본체·손잡이·걸쇠)
    base_e = pre_expand_first_layer(base); handle = pre_expand_first_layer(handle0.copy()); latch = pre_expand_first_layer(latch0.copy())
    print('EFC: base', base_e.is_volume, round(vol(base_e) - vol(base), 1), 'mm3 | handle', handle.is_volume, '| latch', latch.is_volume)
    # 5) 뚜껑 늘리기 + 로고 이동
    lid = stretch_y(lid6, [(C0 - CUT_FRONT, D_FRONT), (C0 - CUT_REAR, D_REAR)]); logo = logo0.copy(); logo.apply_translation([0, D_REAR, 0])
    print('lid stretched: is_volume', lid.is_volume, 'bounds', lid.bounds.round(2).tolist(), 'vol', round(lid6.volume), '->', round(vol(lid)), 'faces', len(lid.faces), 'lid∩logo', round(vol(trimesh.boolean.intersection([lid, logo], engine='manifold')), 3))
    parts = {'base': base_e, 'lid': lid, 'logo': logo, 'handle': handle, 'latch': latch}
    for n, m in parts.items():
        assert m.is_volume and len(m.faces) <= 200000, (n, m.is_volume, len(m.faces))
        print(f'  {n}: faces {len(m.faces)} bounds {m.bounds.round(2).tolist()} bodies {len(m.split(only_watertight=False))}')
    pickle.dump(parts, open(os.path.join(HERE, '..', 'v7parts.pkl'), 'wb'))
    # 6) 플레이트 3MF (베드 256, 여유 두고 배치)
    def place(m, x0, y0):
        m = m.copy(); b = m.bounds; m.apply_translation([x0 - b[0, 0], y0 - b[0, 1], -b[0, 2]]); return m
    A_base = place(base_e, 20, 18); A_handle = place(handle, 20, 178); A_latch = place(latch, 112, 182)
    b = lid.bounds; d = [40 - b[0, 0], 50 - b[0, 1], -b[0, 2]]; B_lid = lid.copy(); B_lid.apply_translation(d); B_logo = logo.copy(); B_logo.apply_translation(d)
    A = [{'name': 'base', 'parts': [(A_base, C1, 'base')]}, {'name': 'handle', 'parts': [(A_handle, C1, 'handle')]}, {'name': 'latch', 'parts': [(A_latch, C1, 'latch')]}]
    B = [{'name': 'lid+logo', 'parts': [(B_lid, C1, 'lid'), (B_logo, C2, 'logo')]}]
    write_generic_3mf(os.path.join(MODELS, 'Toolbox48_v7_A_base_handle_latch.3mf'), A, 'Toolbox48 v7 A', material_order=[C1, C2])
    write_generic_3mf(os.path.join(MODELS, 'Toolbox48_v7_B_lid_logo.3mf'), B, 'Toolbox48 v7 B', material_order=[C1, C2])
    for n, m in [('base', base_e), ('lid', lid), ('handle', handle), ('latch', latch), ('logo', logo)]:
        mm = m.copy(); mm.export(os.path.join(MODELS, f'Toolbox48_{n}_v7.stl'))
    json.dump({'row_depth': ROW, 'd_front': D_FRONT, 'd_rear': D_REAR, 'cut_front': CUT_FRONT, 'cut_rear': CUT_REAR, 'C_closed': C0 + D_FRONT + D_REAR,
               'knuckle': [0, 192.39 + D_FRONT + D_REAR, 26.5], 'lip_shave': LIP_SHAVE}, open(os.path.join(DOCS, 'v7_params.json'), 'w'), indent=1)
    print('done')
