#!/usr/bin/env python3
"""tv-pen-hanger 빌드 — 75TR3DQ 펜 자석 거치대에 Ø20×1 자석 3개로 붙는 걸이대(아래쪽에 펜 2개 + MRSVI M5 에어마우스).
`python tools/mm.py make 작업중/tv-pen-hanger/pipeline.json` 이 이 스크립트를 프로젝트 폴더에서 실행한다.
스킬 순서: 1 설계 규칙 → 2 모델링(이 파일) → 3 QC → 4 조립 검증 → 5 렌더 → 6 3MF → 7 보고 (3~7 은 파이프라인이 한다).

좌표(걸었을 때, '설치 좌표'): x = 폭(TV 가로), y = 앞(0 = 거치대에 닿는 뒷면), z = 위.
형상 = 옆 단면(y–z) 하나를 폭 W 로 압출. 출력은 옆으로 눕혀(단면이 베드, x 가 출력 높이) → 모든 벽이 수직이라 서포트 0,
갈고리(홈)가 층과 평행한 평면에서 휘어 강하다. 자석 포켓은 뒷면(출력 시 옆 벽)에 열린 Ø20.2×1.1 원 + 출력 위쪽(+x)으로
28° 눈물방울(층당 0.106 ≤ 0.115) — 자석은 순간접착제로 붙이고 앞면이 뒷면보다 0.1 들어간다.
산출: parts_nominal.pkl(공칭, 출력 방향) · parts.pkl(첫 층 +0.15 선반영) · models/tv-pen-hanger_A.3mf"""
import os, sys, math, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROJ))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import numpy as np, trimesh
from shapely.geometry import box as sbox, Point, Polygon
from shapely.ops import unary_union
from efc import pre_expand_first_layer
from generic3mf import write_generic_3mf

# 설계 치수표 (README.md 와 같게). '가정' 표시 값은 치수 조사·실측 후 바꾼다.
P = {
    'W': 110.0,          # 폭(x) — 자석 3개 + 눈물방울 + 옆 살
    'T_BACK': 4.0,       # 뒷판 두께(y) — 포켓 1.1 뒤로 2.9 남음
    'H_BACK': 60.0,      # 뒷판 높이(z)
    'MAG_D': 20.0, 'MAG_T': 1.0, 'MAG_N': 3,          # 사용자 자석 Ø20×1, 3개
    'MAG_CLR_D': 0.2, 'MAG_CLR_T': 0.1,                # 포켓 = 지름 +0.2, 깊이 +0.1 (design-method 자석 규칙)
    'MAG_PITCH': 36.0,   # 자석 중심 간격(x)
    'MAG_X0': 14.0,      # 첫 자석 중심 x — 눈물방울 끝(+21.5)이 윗면(W) 안에 남도록 아래로 치우침
    'MAG_Z': 46.0,       # 자석 중심 높이(z) — 뒷판 위쪽(거치대에 닿는 부분)
    'TEAR_DEG': 28.0,    # 포켓 눈물방울 반각(출력 수직 기준) — tan28° × 0.2 = 0.106/층
    'MOUSE_T': 18.0,     # 가정: MRSVI M5 두께
    'MOUSE_W': 42.0,     # 가정: MRSVI M5 폭(세워 꽂음 → 높이 방향)
    'MOUSE_L': 160.0,    # 가정: MRSVI M5 길이(x 방향으로 눕힘)
    'MOUSE_CLR': 2.0,    # 마우스 홈 여유(한쪽)
    'PEN_D': 12.0,       # 가정: 75TR3DQ 전용 펜 지름
    'PEN_L': 150.0,      # 가정: 펜 길이
    'PEN_CLR': 0.75,     # 펜 홈 반경 여유
    'WALL': 3.0,         # 마우스 홈 바닥·앞벽
    'PEN_WALL': 2.4,     # 펜 홈 벽(≥1.2, 휘는 부재 ≥ 3 은 앞벽·바닥 3 으로)
    'H_MWALL': 28.0,     # 마우스 홈 앞벽 높이
    'FILLET': 1.0,       # 바깥 모서리 둥글기(2D)
}
COLORS = {'hanger': '#37474f'}

def derived():
    p = dict(P); p['MS'] = p['MOUSE_T'] + 2 * p['MOUSE_CLR']            # 마우스 홈 안쪽 폭(y)
    p['RP'] = p['PEN_D'] / 2 + p['PEN_CLR']                              # 펜 홈 반경
    p['RO'] = p['RP'] + p['PEN_WALL']                                     # 펜 홈 바깥 반경
    p['Y_MW'] = p['T_BACK'] + p['MS']                                     # 마우스 앞벽 시작 y
    p['Y_P1'] = p['Y_MW'] + p['WALL'] + p['RP']                            # 펜 홈 1 중심 y (앞벽 = 펜 홈 뒷벽)
    p['Y_P2'] = p['Y_P1'] + 2 * p['RP'] + p['PEN_WALL']                    # 펜 홈 2 중심 y
    p['Z_P'] = p['PEN_WALL'] + p['RP']                                    # 펜 홈 중심 z (바닥 살 = PEN_WALL)
    p['MAG_X'] = [p['MAG_X0'] + i * p['MAG_PITCH'] for i in range(p['MAG_N'])]
    return p

def profile(p):
    """옆 단면(y, z) 폴리곤 — 뒷판 + 마우스 홈 + 펜 홈 2개."""
    solid = [sbox(0, 0, p['T_BACK'], p['H_BACK']),                                      # 뒷판
             sbox(p['T_BACK'] - 0.5, 0, p['Y_MW'] + p['WALL'], p['WALL']),               # 마우스 홈 바닥
             sbox(p['Y_MW'], 0, p['Y_MW'] + p['WALL'], p['H_MWALL'])]                    # 마우스 홈 앞벽
    for yc in (p['Y_P1'], p['Y_P2']):
        solid += [Point(yc, p['Z_P']).buffer(p['RO'], 16), sbox(yc - p['RO'], 0, yc + p['RO'], p['Z_P'])]
    out = unary_union(solid)
    cut = []
    for yc in (p['Y_P1'], p['Y_P2']):
        cut += [Point(yc, p['Z_P']).buffer(p['RP'], 16), sbox(yc - p['RP'], p['Z_P'], yc + p['RP'], 200)]
    out = out.difference(unary_union(cut))
    f = p['FILLET']
    out = out.buffer(-f, 4).buffer(f, 4)                 # 바깥(볼록) 모서리 둥글게
    out = out.buffer(f * 0.6, 4).buffer(-f * 0.6, 4)     # 안쪽(오목) 모서리 둥글게 — 응력 집중 완화
    # 뒷면(y=0)은 거치대에 붙는 평면이어야 하므로 다시 곧게 자른다
    out = out.intersection(sbox(0, 0, 500, 500))
    return out.buffer(0)

def teardrop(p):
    """자석 포켓 단면(x, z): 원 + 출력 위쪽(+x)으로 뾰족한 눈물방울."""
    r = (p['MAG_D'] + p['MAG_CLR_D']) / 2; a = math.radians(p['TEAR_DEG'])
    apex = r / math.sin(a); tx = r * math.sin(a); tz = r * math.cos(a)          # 접점: 중심에서 (r sin a, ±r cos a)
    tri = Polygon([(tx, tz), (apex, 0), (tx, -tz), (0, 0)])
    return unary_union([Point(0, 0).buffer(r, 32), tri])

def make_parts():
    """출력 방향 공칭 파트 {이름: trimesh}. 출력 좌표 (x', y', z') = (y, z, x) — 단면이 베드에, 폭이 출력 높이."""
    p = derived(); prof = profile(p)
    # 단면을 z' 방향 2 mm 마디로 스윕(옆면 삼각형이 110 mm 통짜로 길면 QC 레이 검사의 후보가 폭증해 메모리 초과 — 마디로 끊는다)
    nz = int(math.ceil(p['W'] / 2.0)) + 1; path = np.column_stack([np.zeros(nz), np.zeros(nz), np.linspace(0, p['W'], nz)])
    body = trimesh.creation.sweep_polygon(prof.simplify(0.01), path)
    body.apply_transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], float))   # 스윕 틀 (py, -px) → (px, py)
    depth = p['MAG_T'] + p['MAG_CLR_T']; pockets = []
    for xm in p['MAG_X']:
        td = teardrop(p)                                                       # (u=x 방향, v=z 방향)
        pk = trimesh.creation.extrude_polygon(td, depth + 1.0)                # 뒷면 밖 1.0 부터 depth 까지
        # 지역 (u, v, w) → 출력 (x'=y = w-1, y'=z = v + MAG_Z, z'=x = u + xm)
        M = np.array([[0, 0, 1, -1.0], [0, 1, 0, p['MAG_Z']], [1, 0, 0, xm], [0, 0, 0, 1]], float)
        pk.apply_transform(M); pockets.append(pk)
    hanger = trimesh.boolean.difference([body] + pockets, engine='manifold')
    return {'hanger': hanger}

def plate(parts, gap=10.0):
    """플레이트 배치: 베드 가운데쯤(원점 90, 90)."""
    objs, x = [], 90.0
    for n, m in parts.items():
        c = m.copy(); c.apply_translation([x - c.bounds[0][0], 90.0 - c.bounds[0][1], -c.bounds[0][2]]); x = c.bounds[1][0] + gap
        objs.append({'name': n, 'parts': [(c, COLORS.get(n, '#37474f'), n)]})
    return objs

if __name__ == '__main__':
    os.chdir(PROJ); os.makedirs('models', exist_ok=True)
    nominal = make_parts(); pickle.dump(nominal, open('parts_nominal.pkl', 'wb'))
    printed = {n: pre_expand_first_layer(m) for n, m in nominal.items()}; pickle.dump(printed, open('parts.pkl', 'wb'))
    write_generic_3mf('models/tv-pen-hanger_A.3mf', plate(printed), 'tv-pen-hanger')
    for n, m in printed.items(): m.export(f'models/tv-pen-hanger_{n}.stl')          # 파트 STL 동봉(출력 방향, 첫 층 선반영)
    d = derived()
    print('build ok', {n: [round(v, 2) for v in m.extents] for n, m in nominal.items()},
          {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items() if k in ('MS', 'RP', 'RO', 'Y_MW', 'Y_P1', 'Y_P2', 'Z_P', 'MAG_X')})
