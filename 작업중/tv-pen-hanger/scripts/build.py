#!/usr/bin/env python3
"""tv-pen-hanger 빌드 — 75TR3DQ 펜 자석 거치대에 Ø20×1 자석 3개로 붙는 걸이대(아래쪽에 펜 2개 + MRSVI M5 에어마우스). v2: 펜 12.5 각 R4·176, M5 155×45×9 반영.
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
from loft import loft_rings

# 설계 치수표 (README.md 와 같게). '가정' 표시 값은 치수 조사·실측 후 바꾼다.
P = {
    # ── 공통
    'W': 167.0,          # 폭(x) — 리모컨 155 + TV 쪽 자석 5개(간격 33, 눈물방울 끝 +21.5 가 윗면 안 1.5)
    'MAG_D': 20.0, 'MAG_T': 1.0,                       # 사용자 자석 Ø20×1
    'MAG_CLR_D': 0.2, 'MAG_CLR_T': 0.1,                # 포켓 = 지름 +0.2, 깊이 +0.1 (design-method 자석 규칙)
    'TEAR_DEG': 28.0,    # 열린 포켓 눈물방울 반각(출력 수직 기준) — tan28° × 0.2 = 0.106/층
    # ── 리모컨 걸이(hanger) — TV 거치대에 Ø20 5개
    'MAG_N': 5, 'MAG_PITCH': 33.0, 'MAG_X0': 12.0,     # TV 쪽 자석 수·간격·첫 중심 x
    'MAG_Z': 47.0,       # TV 쪽 자석 중심 높이(z)
    'T_BACK': 3.5,       # 뒷판 두께(y) — 열린 포켓 1.1 뒤로 2.4
    'H_BACK': 60.0,      # 뒷판 높이(z)
    'FLOOR': 3.7,        # 리모컨 홈 바닥 두께 = 펜 홀더와 붙는 받침(살 1.3 + 묻힌 자석 1.1 + 1.3)
    'PAD_D': 24.5,       # 바닥 받침 깊이(y) — 묻힌 Ø20 자석 + 앞뒤 살 2.15
    'MOUSE_T': 9.0, 'MOUSE_W': 45.0, 'MOUSE_L': 155.0, # MRSVI M5 두께·폭·길이(설명서)
    'MOUSE_CLR': 1.0,    # 리모컨 홈 여유(한쪽)
    'WALL': 2.4,         # 리모컨 홈 앞벽 두께
    'H_MWALL': 20.0,     # 리모컨 홈 앞벽 높이(바닥 위) — 45 중 20 을 잡음
    # ── 걸이 ↔ 펜 홀더 결합: 묻힌 자석(안 보임) Ø20 3개씩
    'JM_N': 3, 'JM_PITCH': 33.0,                       # 결합 자석 수·간격(가운데 기준)
    'SKIN': 1.3,         # 묻힌 자석 앞 살(결합면 쪽) — 벽 최소 1.2(3줄) + 측정 여유 0.1
    # ── 펜 홀더(penholder) — J 고리 2개를 위아래로
    'PEN_S': 13.1, 'PEN_L': 176.0,                     # 펜 최대 지름·길이 (사용자 실측)
    'PEN_CLR': 0.3,      # 펜 홈 = 펜 윤곽 + 한쪽 0.3
    'PEN_S0': 4.5,       # 홀더 x=0 에 오는 펜 위치(캡 끝에서) — 어깨(11~23)·펜촉 원뿔(148~167)이 둘 다 홈 안 → 좌우로 안 밀림
    'SPINE': 2.4,        # 펜 홀더 세로 기둥 두께(y)
    'PEN_WALL': 2.0,     # J 고리 둘레 살
    'LIP': 2.0,          # J 앞 입술 끝 = 펜 축보다 2 위 (펜이 굴러 나오지 않음)
    'OPEN': 15.0,        # J 입구 높이(입술 끝 → 위 부재) — 펜 13.1 이 수평으로 들어갈 틈
    'FILLET': 0.9, 'FILLET_IN': 0.8,                   # 바깥·안쪽 모서리 둥글기(2D) — 바깥은 가장 얇은 살 2.0 의 절반 미만(살이 깎여 사라지지 않게)
}
COLORS = {'hanger': '#37474f', 'penholder': '#546e7a'}
LAYER = 0.2

def derived():
    p = dict(P); p['MS'] = p['MOUSE_T'] + 2 * p['MOUSE_CLR']            # 리모컨 홈 안쪽 폭(y)
    p['Y_MW'] = p['T_BACK'] + p['MS']                                     # 리모컨 앞벽 시작 y
    p['MAG_X'] = [p['MAG_X0'] + i * p['MAG_PITCH'] for i in range(p['MAG_N'])]
    p['JM_X'] = [p['W'] / 2 + (i - (p['JM_N'] - 1) / 2) * p['JM_PITCH'] for i in range(p['JM_N'])]
    p['JM_Y'] = p['PAD_D'] / 2                                            # 결합 자석 중심 y
    p['GW'] = p['PEN_S'] / 2 + p['PEN_CLR']                              # 펜 홈 최대 반지름
    p['RO'] = p['GW'] + p['PEN_WALL']                                     # J 바깥 반지름
    p['YC'] = p['SPINE'] + p['GW']                                        # J 홈 축 y (기둥 앞면에 펜이 닿음)
    p['Z1'] = -p['FLOOR'] - p['OPEN'] - p['LIP']                          # 위 J 축 z (받침 아래)
    p['Z2'] = p['Z1'] - p['RO'] - p['OPEN'] - p['LIP']                    # 아래 J 축 z (위 J 바닥 아래로 입구 15)
    p['Z_BOT'] = p['Z2'] - p['RO']                                        # 펜 홀더 아래 끝
    # 묻힌 자석 일시정지 높이(출력 z' = 설치 x): 슬롯 윗면(자석 위 끝 +0.1)을 층 격자로 올림 → 그 위 층 시작 전에 멈춤
    r = (p['MAG_D'] + p['MAG_CLR_D']) / 2
    p['PAUSE_Z'] = [round(math.ceil((x + r + 0.1) / LAYER - 1e-6) * LAYER, 2) for x in p['JM_X']]   # 슬롯 윗면 ≥ 포켓 원 위 끝 + 0.1
    return p

# 펜 윤곽(캡 끝에서 s mm → 지름 w). 사용자 실측: 캡 7, 위에서 23 에 최대 13.1, 148(펜촉 끝에서 28)에 Ø10, 펜촉 3, 길이 176.
PEN_W = [(0, 4.0), (2, 7.0), (11, 7.0), (23, 13.1), (30, 13.1), (148, 10.0), (167, 3.0), (176, 3.0)]
def pen_w(s): return float(np.interp(s, *zip(*PEN_W)))
def pen_section(s, grow=0.0):
    """펜 단면(원 포락선) + grow."""
    return Point(0, 0).buffer(pen_w(s) / 2 + grow, 32)

def groove_cutter(p, yc, zc, up):
    """펜 홈(출력 좌표): z' = 설치 x 마다 펜 단면 + 0.3 을 축 (yc, zc) 에 두고 위로 up 만큼 열어 로프트."""
    kinks = [s_ - p['PEN_S0'] for s_, _ in PEN_W if 0 < s_ - p['PEN_S0'] < p['W']]                 # 윤곽 꺾이는 곳은 반드시 단면(현이 펜을 파고들지 않게)
    xs = np.unique(np.round(np.r_[-1.0, np.arange(0.0, p['W'] + 0.01, 2.0), kinks, p['W'] + 1.0], 4)); rings = []
    for x in xs:
        sec = pen_section(x + p['PEN_S0'], p['PEN_CLR']); hw = (sec.bounds[2] - sec.bounds[0]) / 2
        g = unary_union([sec, sbox(-hw, 0, hw, up)])
        rings.append((x, Polygon(np.asarray(g.exterior.coords) + [yc, zc])))
    return loft_rings(rings, M=240)

def _round(out, p):
    f, fi = p['FILLET'], p['FILLET_IN']
    out = out.buffer(-f, 8).buffer(f, 8).buffer(fi, 8).buffer(-fi, 8)
    if out.geom_type != 'Polygon': raise SystemExit(f'단면이 한 덩어리가 아님: {out.geom_type}')
    return out

def profile_hanger(p):
    """리모컨 걸이 옆 단면(y, z): 뒷판(TV 자석) + 바닥 받침(묻힌 결합 자석) + 앞벽."""
    tb, w = p['T_BACK'], p['WALL']
    out = unary_union([sbox(0, 0, tb, p['H_BACK']), sbox(0, 0, p['PAD_D'], p['FLOOR']),
                       sbox(p['Y_MW'], 0, p['Y_MW'] + w, p['FLOOR'] + p['H_MWALL'])])
    return _round(out, p).intersection(sbox(0, 0, 500, 500))      # 뒷면 y=0·밑면 z=0 평면 유지

def profile_pen(p):
    """펜 홀더 옆 단면(y, z ≤ 0): 위 받침(묻힌 결합 자석) + 세로 기둥 + J 고리 2개(위·아래)."""
    yc, ro, sp = p['YC'], p['RO'], p['SPINE']; parts = [sbox(0, -p['FLOOR'], p['PAD_D'], 0), sbox(0, p['Z_BOT'] + ro, sp, 0)]
    for zc in (p['Z1'], p['Z2']):
        cup = Point(yc, zc).buffer(ro, 64).intersection(sbox(-50, zc - 50, 100, zc + p['LIP']))   # 입술 끝 = 축 + LIP
        parts += [cup, sbox(0, zc - ro * 0.6, yc, zc + p['LIP'])]                                     # 기둥과 J 바닥을 잇는 살
    out = unary_union(parts)
    out = _round(out, p).intersection(sbox(0, -500, 500, 0))     # 뒷면 y=0·윗면 z=0 평면 유지
    return out

def _sweep(prof, W):
    nz = int(math.ceil(W / 2.0)) + 1; path = np.column_stack([np.zeros(nz), np.zeros(nz), np.linspace(0, W, nz)])
    body = trimesh.creation.sweep_polygon(prof.simplify(0.01), path)
    body.apply_transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], float))   # (py, -px) → (px, py)
    return body                                                                # 출력 좌표 (x', y', z') = (y, z, x)

def teardrop(p):
    """열린 포켓 단면(u=x, v): 원 + 출력 위쪽(+x)으로 뾰족한 눈물방울."""
    r = (p['MAG_D'] + p['MAG_CLR_D']) / 2; a = math.radians(p['TEAR_DEG'])
    apex = r / math.sin(a); tx = r * math.sin(a); tz = r * math.cos(a)
    return unary_union([Point(0, 0).buffer(r, 32), Polygon([(tx, tz), (apex, 0), (tx, -tz), (0, 0)])])

def slot(p, top):
    """묻힌 자석 슬롯 단면(u=x, v): 아래 반원 + 위로 곧은 홈(윗면 = top, 층 격자). 일시정지 때 위에서 자석을 떨어뜨려 넣고,
    다음 층부터 1.1 폭 브리지로 덮인다."""
    r = (p['MAG_D'] + p['MAG_CLR_D']) / 2
    return unary_union([Point(0, 0).buffer(r, 32), sbox(0, -r, top, r)])

INV = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float)    # 설치 → 출력 (MOUNT 의 역)
def _place(poly, h0, h1, L):
    """(u, v) 폴리곤을 h0~h1 로 압출 → 지역 (u, v, h) 를 설치 좌표로 보내는 4×4 L → 출력 좌표."""
    m = trimesh.creation.extrude_polygon(poly, h1 - h0); m.apply_translation([0, 0, h0]); m.apply_transform(INV @ L); return m

def make_parts():
    """출력 방향 공칭 파트 {이름: trimesh}."""
    p = derived(); dep = p['MAG_T'] + p['MAG_CLR_T']; sk = p['SKIN']; r = (p['MAG_D'] + p['MAG_CLR_D']) / 2
    # 리모컨 걸이: 뒷면 열린 포켓 5(TV 쪽, 접착) + 바닥 묻힌 슬롯 3
    cut = []
    for xm in p['MAG_X']:   # 설치 (x, y, z) = (u + xm, h, MAG_Z − v)  (det +1)
        cut.append(_place(teardrop(p), -1.0, dep, np.array([[1, 0, 0, xm], [0, 0, 1, 0], [0, -1, 0, p['MAG_Z']], [0, 0, 0, 1]], float)))
    for xm, pz in zip(p['JM_X'], p['PAUSE_Z']):   # 설치 (x, y, z) = (u + xm, v + JM_Y, h)
        cut.append(_place(slot(p, pz - xm), sk, sk + dep, np.array([[1, 0, 0, xm], [0, 1, 0, p['JM_Y']], [0, 0, 1, 0], [0, 0, 0, 1]], float)))
    hanger = trimesh.boolean.difference([_sweep(profile_hanger(p), p['W'])] + cut, engine='manifold')
    # 펜 홀더: 윗면 묻힌 슬롯 3 + J 홈 2(펜 윤곽 로프트, 입술 위로 열림)
    cut = []
    for xm, pz in zip(p['JM_X'], p['PAUSE_Z']):   # 설치 (x, y, z) = (u + xm, JM_Y − v, −h)  (det +1)
        cut.append(_place(slot(p, pz - xm), sk, sk + dep, np.array([[1, 0, 0, xm], [0, -1, 0, p['JM_Y']], [0, 0, -1, 0], [0, 0, 0, 1]], float)))
    cut += [groove_cutter(p, p['YC'], zc, p['LIP'] + 3.0) for zc in (p['Z1'], p['Z2'])]
    pen = trimesh.boolean.difference([_sweep(profile_pen(p), p['W'])] + cut, engine='manifold')
    return {'hanger': hanger, 'penholder': pen}

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
          {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items() if k in ('MS', 'GW', 'RO', 'YC', 'Z1', 'Z2', 'Z_BOT', 'Y_MW', 'MAG_X', 'JM_X', 'PAUSE_Z')})
