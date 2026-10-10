#!/usr/bin/env python3
"""Toolbox48 v9 — v8 에서 고친 것:
 1) 뚜껑 벽 속 0.1 mm 수평 틈 제거(v6/v8: 곡선 로프트가 z 7.8 까지, 잘라낼 띠는 7.9 까지 → 벽이 0.1 mm 파임 → 출력물 옆면 줄). 로프트를 z 8.3 까지 만들고 띠는 7.8 에서 멈춘다.
 2) 본체 바닥 곡선: 0.1 mm 판 쌓기(계단) → 링 로프트(tools/loft.py)로 매끈하게.
 3) 로고 1.5배: 옛 포켓을 메우고 → 뚜껑을 늘린 뒤 → 1.5배 로고 모양 그대로 포켓(면 접촉 인레이). 절단면이 큰 로고를 가로지르지 않게 순서를 바꿈.
사용: python scripts/build_v9.py ../toolbox42/v5parts.pkl"""
import sys, os, pickle, json, numpy as np, trimesh
from shapely.geometry import Polygon, box as sbox, Point
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [HERE, os.path.join(ROOT, 'tools')]
import build_v7 as B7
from overhang import layer_poly
from loft import loft_rings
from efc import pre_expand_first_layer, pre_expand_first_layer_group
from meshops import drop_slivers
from shapely.affinity import scale as sscale
from generic3mf import write_generic_3mf
MODELS = os.path.join(HERE, '..', 'models'); DOCS = os.path.join(HERE, '..', 'docs'); TAG = 'v9'
LOGO_SCALE = 1.5; LAND = 0.6; ZTOP = 7.8; DZ = 0.2; Z0 = 0.1137
def polys(p): return list(p.geoms) if p.geom_type == 'MultiPolygon' else [p]
def vol(m): return float(abs(m.volume)) if m.is_volume else 0.0
# ---------- 1) 뚜껑 모서리: v5 연속 곡선 + 인레이 3층만 inset 자리 수직, 벽 속 틈 없음 ----------
def lid_edge(lid):
    full_ext = Polygon(max(polys(layer_poly(lid, ZTOP)), key=lambda q: q.area).exterior)
    first = Polygon(max(polys(layer_poly(lid, Z0)), key=lambda q: q.area).exterior)
    stack = []
    for z in np.round(np.arange(0, ZTOP + 0.5 + DZ / 2, DZ), 3):              # z 8.4 까지(잘라낼 띠 7.8 보다 높게)
        zs = z - LAND
        if zs < Z0: p = first
        elif zs >= ZTOP: p = full_ext
        else: p = Polygon(max(polys(layer_poly(lid, zs)), key=lambda q: q.area).exterior)
        stack.append((z, p))
    loft = loft_rings(stack)
    band = full_ext.buffer(0.6).difference(full_ext.buffer(-4.0)).difference(sbox(415, 183, 456, 200))   # 바깥 4 mm 띠, 걸쇠 탭 제외
    cut = extrude_polygon(band, ZTOP + 0.1); cut.apply_translation([0, 0, -0.1])  # z −0.1 ~ 7.8 (로프트 8.4 안)
    lip = trimesh.boolean.difference([cut, loft], engine='manifold')
    out = trimesh.boolean.difference([lid, lip], engine='manifold'); out.apply_translation([0, 0, -out.bounds[0, 2]])
    out, n, v = drop_slivers(out); print(f'  lid_edge: 계산 찌꺼기 {n}조각 {v:.2e} mm³ 제거'); return out
# ---------- 2) 본체 바닥: 링 로프트 ----------
def base_bottom(m, ZC=1.51, SLOPE=0.115 / 0.2):
    L = layer_poly(m, ZC); stack = []
    for z in np.round(np.arange(0.0, ZC + 1e-6, 0.1), 3):
        d = max(0.0, SLOPE * (ZC - z)); zz = min(max(z, 0.02), ZC)
        p = L.buffer(-d, join_style='round').union(layer_poly(m, zz)).buffer(0)          # v7 과 같은 단면(귀 등 원형 보존), 판 대신 로프트
        stack.append((z, Polygon(max(polys(p), key=lambda q: q.area).exterior)))
    stack.append((ZC + 0.05, Polygon(max(polys(L), key=lambda q: q.area).exterior)))
    loft = loft_rings(stack)
    bx = trimesh.creation.box(extents=[2000, 2000, ZC]); bx.apply_translation([0, 0, ZC / 2])
    top = trimesh.boolean.difference([m, bx], engine='manifold')
    return trimesh.boolean.union([top, loft], engine='manifold')
# ---------- 3) 로고 ----------
def fill_pockets(lid):
    holes = unary_union([Polygon(i) for g in polys(layer_poly(lid, 0.3)) for i in g.interiors])
    plug = extrude_polygon(holes.buffer(0.05), 0.6 + 0.05) if holes.geom_type == 'Polygon' else trimesh.boolean.union([extrude_polygon(h.buffer(0.05), 0.65) for h in polys(holes)], engine='manifold')
    return trimesh.boolean.union([lid, plug], engine='manifold'), holes.area
if __name__ == '__main__':
    P = pickle.load(open(sys.argv[1], 'rb'))
    lid5, logo5, base0, handle0, latch0 = P['lid'], P['logo'], P['base'], P['handle'], P['latch']
    # 본체: v7 과 같은 늘리기·립 0.1 → 바닥 로프트
    base = B7.stretch_y(base0, [(B7.CUT_FRONT, B7.D_FRONT), (B7.CUT_REAR, B7.D_REAR)]); base, _ = B7.shave_lip(base)
    base = base_bottom(base); base.apply_translation([0, 0, -base.bounds[0, 2]])
    zz = np.arange(Z0, 2.2, 0.2); xs = np.array([layer_poly(base, z).bounds[0] for z in zz]); ins = xs - layer_poly(base, 8.0).bounds[0]
    print('base: is_volume', base.is_volume, 'bodies', len(base.split(only_watertight=False)), '| 바닥 inset', ' '.join(f'{z:.2f}:{i:.2f}' for z, i in zip(zz, ins)), '| 층당 최대', round(float(np.max(-np.diff(ins))), 3))
    # 뚜껑: 모서리 → 옛 포켓 메움 → 늘리기 → 1.5배 로고 포켓
    lid = lid_edge(lid5); print('lid edge: is_volume', lid.is_volume, 'bodies', len(lid.split(only_watertight=False)))
    lid, ha = fill_pockets(lid); print('old pockets filled:', round(ha, 1), 'mm², is_volume', lid.is_volume)
    lid = B7.stretch_y(lid, [(B7.C0 - B7.CUT_FRONT, B7.D_FRONT), (B7.C0 - B7.CUT_REAR, B7.D_REAR)])
    # 로고는 0.6 mm 평판 압출(단면×0.6 = 부피 확인) → 단면 폴리곤을 1.5배 해서 인레이와 포켓을 같은 폴리곤으로 압출(정확히 맞물림).
    # 원본 로고 메시를 그대로 빼면 글자 속 구멍 껍질 때문에 불리언이 실패한다(글자 섬 15조각·겹침 112 mm³).
    c = (logo5.bounds[0] + logo5.bounds[1]) / 2
    lp = sscale(layer_poly(logo5, 0.3), LOGO_SCALE, LOGO_SCALE, origin=(c[0], c[1]))
    from shapely.affinity import translate as stranslate; lp = stranslate(lp, 0, B7.D_REAR)          # 로고 중심을 옛 위치(늘린 뚜껑 기준) 그대로
    logo = trimesh.util.concatenate([extrude_polygon(q, 0.6) for q in polys(lp)])
    cutter = trimesh.util.concatenate([extrude_polygon(q, 0.61) for q in polys(lp)]); cutter.apply_translation([0, 0, -0.01])
    lid = trimesh.boolean.difference([lid, cutter], engine='manifold'); lid, n, v = drop_slivers(lid)
    print(f'  logo pocket: 찌꺼기 {n}조각 {v:.2e} mm³ 제거, 로고 단면 {lp.area:.1f} mm² (원본 {layer_poly(logo5, 0.3).area:.1f} × 2.25 = {layer_poly(logo5, 0.3).area * 2.25:.1f})')
    print('logo x1.5:', (logo.bounds[1] - logo.bounds[0]).round(2).tolist(), 'center', ((logo.bounds[0] + logo.bounds[1]) / 2).round(2).tolist(), '| lid∩logo', round(vol(trimesh.boolean.intersection([lid, logo], engine='manifold')), 3), '| lid bodies', len(lid.split(only_watertight=False)))
    nominal = {'base': base, 'lid': lid.copy(), 'logo': logo.copy(), 'handle': handle0.copy(), 'latch': latch0.copy()}
    # EFC 선반영(출력용)
    base_e = pre_expand_first_layer(base); handle = pre_expand_first_layer(handle0.copy()); latch = pre_expand_first_layer(latch0.copy())
    lid_e, logo_e = pre_expand_first_layer_group([lid, logo])
    parts = {'base': base_e, 'lid': lid_e, 'logo': logo_e, 'handle': handle, 'latch': latch}
    for n, m in parts.items():
        print(f'  {n}: is_volume {m.is_volume} faces {len(m.faces)} bodies {len(m.split(only_watertight=False))} bounds {m.bounds.round(2).tolist()}')
        assert m.is_volume and len(m.faces) <= 200000
    pickle.dump(parts, open(os.path.join(HERE, '..', f'{TAG}parts.pkl'), 'wb')); pickle.dump(nominal, open(os.path.join(HERE, '..', f'{TAG}parts_nominal.pkl'), 'wb'))
    def place(m, x0, y0):
        m = m.copy(); b = m.bounds; m.apply_translation([x0 - b[0, 0], y0 - b[0, 1], -b[0, 2]]); return m
    A = [{'name': 'base', 'parts': [(place(base_e, 20, 18), B7.C1, 'base')]}, {'name': 'handle', 'parts': [(place(handle, 20, 178), B7.C1, 'handle')]}, {'name': 'latch', 'parts': [(place(latch, 112, 182), B7.C1, 'latch')]}]
    b = lid_e.bounds; d = [40 - b[0, 0], 50 - b[0, 1], -b[0, 2]]; Bl = lid_e.copy(); Bl.apply_translation(d); Bg = logo_e.copy(); Bg.apply_translation(d)
    write_generic_3mf(os.path.join(MODELS, f'Toolbox48_{TAG}_A_base_handle_latch.3mf'), A, f'Toolbox48 {TAG} A', material_order=[B7.C1, B7.C2])
    write_generic_3mf(os.path.join(MODELS, f'Toolbox48_{TAG}_B_lid_logo.3mf'), [{'name': 'lid+logo', 'parts': [(Bl, B7.C1, 'lid'), (Bg, B7.C2, 'logo')]}], f'Toolbox48 {TAG} B', material_order=[B7.C1, B7.C2])
    for n, m in parts.items(): m.export(os.path.join(MODELS, f'Toolbox48_{n}_{TAG}.stl'))
    pr = json.load(open(os.path.join(DOCS, 'v8_params.json'))); pr['logo_scale'] = LOGO_SCALE; json.dump(pr, open(os.path.join(DOCS, f'{TAG}_params.json'), 'w'), indent=1)
    print('done')
