#!/usr/bin/env python3
"""인정전 램프 v2 빌드 → 플레이트 3MF (pipeline_v2.json 의 build).
1) assemble.py(조립 STL + objs pkl) → export_v2.py(출력 방향 STL, EFC 0.15 선반영)
2) 출력 방향 메시를 색별 플레이트에 배치(플레이트 = 한 색, AMS 없이 출력). 링 모양 파트 안에 작은 파트를 넣어 장수를 줄인다.
3) models/v2/plates/*.3mf (일반 3MF, 색 번호 공통) + models/v2/parts_print.pkl(QC용) + parts_nominal.pkl(조립 검사용, EFC 전)
"""
import os, sys, glob, pickle, subprocess, numpy as np, trimesh
from shapely.ops import unary_union
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); REPO = os.path.abspath(os.path.join(ROOT, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools')); from generic3mf import write_generic_3mf
MD = os.path.join(ROOT, 'models', 'v2'); PL = os.path.join(MD, 'plates'); os.makedirs(PL, exist_ok=True)
BED, GAP = 256.0, 4.0
for s in ('assemble.py', 'export_v2.py'):
    r = subprocess.run([sys.executable, os.path.join(HERE, s)], cwd=HERE, capture_output=True, text=True)
    if r.returncode: sys.stderr.write(r.stderr); sys.exit(1)
load = lambda d: {os.path.basename(f)[:-4]: trimesh.load(f, force='mesh') for f in sorted(glob.glob(os.path.join(MD, d, '*.stl')))}
prt, nom = load('print'), load('asm')
assert set(prt) == set(nom), set(prt) ^ set(nom)
cols = dict(s.split('=') for s in open(os.path.join(ROOT, 'qc', 'v2_colors.txt')).read().split(','))
pickle.dump(prt, open(os.path.join(MD, 'parts_print.pkl'), 'wb')); pickle.dump(nom, open(os.path.join(MD, 'parts_nominal.pkl'), 'wb'))

def rot(m, k):                                                          # z 축 90°×k
    m = m.copy()
    if k: m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2 * k, [0, 0, 1]))
    return m
def size(m): b = m.bounds; return b[1] - b[0]
def at(m, cx, cy):                                                      # 바운딩 박스 가운데를 (cx, cy), 바닥 z=0
    m = m.copy(); b = m.bounds; m.apply_translation([cx - (b[0, 0] + b[1, 0]) / 2, cy - (b[0, 1] + b[1, 1]) / 2, -b[0, 2]]); return m
def rows(spec, cx=BED / 2, cy=BED / 2):
    """spec: [[(이름, 회전), ...], ...] 위에서 아래로 줄, 줄 안은 왼쪽→오른쪽, 전체를 (cx, cy) 가운데에."""
    R = [[(n, rot(prt[n], k)) for n, k in row] for row in spec]
    H = sum(max(size(m)[1] for _, m in row) for row in R) + GAP * (len(R) - 1); y = cy + H / 2; out = {}
    for row in R:
        h = max(size(m)[1] for _, m in row); W = sum(size(m)[0] for _, m in row) + GAP * (len(row) - 1); x = cx - W / 2
        for n, m in row:
            w = size(m)[0]; out[n] = at(m, x + w / 2, y - h / 2); x += w + GAP
        y -= h + GAP
    return out
def nest(*names, cx=BED / 2, cy=BED / 2):                               # 같은 중심(조립 좌표에서 동심인 링·통)
    c = (prt[names[0]].bounds[0] + prt[names[0]].bounds[1]) / 2; out = {}
    for n in names:
        m = prt[n].copy(); m.apply_translation([cx - c[0], cy - c[1], -m.bounds[0, 2]]); out[n] = m
    return out
def foot(m):
    from trimesh.path.polygons import projected
    return projected(m, normal=[0, 0, 1])
def fits_inside(inner, outer):                                          # 안 파트 발자국이 바깥 파트 발자국과 안 겹치고 2 mm 이상 떨어짐
    return foot(inner).buffer(2.0).intersection(foot(outer)).area < 1e-3

plates = {}
plates['P01_gray_platform'] = rows([[('platform', 0)]])
plates['P02_tile_lower'] = rows([[('L_roof_tile', 0)]])
plates['P03_tile_upper'] = rows([[('U_roof_tile', 0)]])
plates['P04_brown_soffit_lower'] = rows([[('L_roof_soffit', 0)]])
plates['P05_brown_soffit_upper'] = rows([[('U_roof_soffit', 0)]])
plates['P06_brown_floor_walls'] = rows([[('L_floor', 0)], [('wall_front', 0)], [('wall_back', 0)], [('uwall_front', 0)], [('uwall_back', 0)]])
b = nest('L_ring', 'U_ring', cy=BED / 2 + 37.0); assert fits_inside(b['U_ring'], b['L_ring'])
b.update(rows([[('wall_left', 0)], [('wall_right', 0)]], cy=BED / 2 + 37.0 - 64.9 - GAP - 37.7)); plates['P07_brown_rings_sidewalls'] = b
plates['P08_brown_upperfloor_gables'] = rows([[('U_floor', 0)], [('U_roof_gableL', 0), ('U_roof_gableR', 0), ('uwall_left', 1), ('uwall_right', 1)]])
g = nest('L_band', 'U_band')
if fits_inside(g['U_band'], g['L_band']): plates['P09_green_bands'] = g
else: plates['P09_green_band_lower'] = rows([[('L_band', 0)]]); plates['P10_green_band_upper'] = rows([[('U_band', 0)]])
w = nest('L_roof_eave_white', 'L_diffuser', 'U_diffuser'); w.update(rows([[('U_roof_ridge', 1)]]))
assert fits_inside(w['L_diffuser'], w['L_roof_eave_white']) and fits_inside(w['U_diffuser'], w['L_diffuser']) and fits_inside(w['U_roof_ridge'], w['U_diffuser'])
plates['P11_white_lower_ring_diffusers_ridge'] = w
w2 = nest('U_roof_eave_white'); inner = rows([[('U_roof_desc1', 0), ('U_roof_desc2', 0), ('U_roof_desc3', 0), ('U_roof_desc4', 0)],
                                               [(f'L_roof_hip{i}', 0) for i in range(1, 5)] + [(f'U_roof_hip{i}', 0) for i in range(1, 5)]])
for n, m in inner.items(): assert fits_inside(m, w2['U_roof_eave_white']), n
w2.update(inner); plates['P12_white_upper_ring_hips_desc'] = w2

placed = set(); plate_colors = {}
for pn, pp in plates.items():
    for n, m in pp.items():
        lo, hi = m.bounds; assert lo[0] >= 2 and lo[1] >= 2 and hi[0] <= BED - 2 and hi[1] <= BED - 2, (pn, n, lo, hi)
    fs = {n: foot(m) for n, m in pp.items()}; ks = list(fs)
    for i in range(len(ks)):                                            # 발자국 겹침은 둥지(링 안 파트) 말고는 없어야 한다
        for j in range(i + 1, len(ks)):
            ov = fs[ks[i]].intersection(fs[ks[j]]).area
            assert ov < 1e-3, (pn, ks[i], ks[j], ov)
    placed |= set(pp)
    pc = sorted({cols[n] for n in pp}); assert len(pc) == 1, (pn, pc)                # 플레이트 = 한 색 → 그 색이 1번 필라멘트(AMS 없이 한 롤)
    write_generic_3mf(os.path.join(PL, pn + '.3mf'), [{'name': n, 'parts': [(m, cols[n], n)]} for n, m in pp.items()], title=f'인정전 램프 v2 {pn}', material_order=pc)
    plate_colors['models/v2/plates/' + pn + '.3mf'] = pc
    print(pn, len(pp), 'parts', ', '.join(pp))
missing = set(prt) - placed; assert not missing, missing
print('plates', len(plates), 'parts', len(placed))
import json; cp = os.path.join(ROOT, 'pipeline_v2.json'); cfg = json.load(open(cp, encoding='utf-8'))
cfg.setdefault('bambu', {})['plate_colors'] = plate_colors; json.dump(cfg, open(cp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
