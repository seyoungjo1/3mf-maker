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
    'W': 167.0,          # 폭(x) — 펜 176 중 어깨~펜촉 원뿔을 홈 안에 + 리모컨 155
    'MAG_D': 20.0, 'MAG_T': 1.0,                       # 사용자 자석 Ø20×1
    'MAG_CLR_D': 0.2, 'MAG_CLR_T': 0.1,                # 포켓 = 지름 +0.2, 깊이 +0.1 (design-method 자석 규칙)
    # ── 설치 좌표: y = 앞뒤(0 = TV 앞면, − = TV 밑으로 들어감), z = 높이(0 = TV 밑면). 수납물은 앞판 앞면(y = T_BACK)보다 앞으로 안 나옴(사용자)
    'TV_D': 99.7,        # TV 두께(외형 깊이, 판매처 자료) — 밑으로 들어가는 깊이 한계
    # ── 앞판: TV 쪽 Ø20×1 5개(뒷면 원형 포켓, 접착)
    'MAG_N': 5, 'MAG_PITCH': 33.0, 'MAG_X0': 17.5,     # TV 쪽 자석 수·간격·첫 중심 x(가운데 정렬)
    'MAG_Z': 20.0,       # TV 쪽 자석 중심 높이(TV 밑면 위) — **가정**: 펜 거치대가 아래 베젤(43.5) 안
    'T_BACK': 3.5,       # 앞판 두께(y) — 포켓 1.1 앞으로 2.4
    'H_TOP': 33.0,       # 앞판 위 끝(z) — 자석 위 끝 30.1 + 살
    'SHELF': 3.0,        # TV 밑면을 받치는 선반 두께(z) — 무게는 TV 가 받고 자석은 앞으로 넘어짐만 막음
    'BWALL': 2.4,        # 뒤 벽(기둥) 두께 — 리모컨 칸·J 고리가 매달림
    # ── 리모컨 칸(MRSVI M5 세움, 사용자)
    'MOUSE_T': 9.0, 'MOUSE_W': 45.0, 'MOUSE_L': 155.0, # MRSVI M5 두께·폭(세운 높이)·길이(설명서)
    'MOUSE_CLR': 1.0,    # 리모컨 칸 여유(한쪽)
    'LIP_R': 10.0,       # 리모컨 칸 앞 입술 높이 — 리모컨 아래를 잡음
    'LIFT': 2.0,         # 리모컨을 입술 위로 들어 넣을 여유(리모컨 위 끝 ↔ 선반 밑면)
    'WALL': 2.4,         # 리모컨 칸 바닥·입술 두께
    # ── 펜 J 고리 2개(리모컨 홈 아래, 위아래) + 펜이 착 붙는 숨은 자석 Ø10×2 3개
    'PEN_S': 13.1, 'PEN_L': 176.0,                     # 펜 최대 지름·길이 (사용자 실측)
    'PEN_CLR': 0.3,      # 펜 홈 = 펜 윤곽 + 한쪽 0.3
    'PEN_S0': 4.5,       # x=0 에 오는 펜 위치(캡 끝에서) — 어깨(11~23)·펜촉 원뿔(148~167)이 둘 다 홈 안 → 좌우로 안 밀림
    'PEN_WALL': 2.0,     # J 고리 둘레 살
    'LIP': 2.0,          # J 앞 입술 끝 = 펜 축보다 2 위 (펜이 굴러 나오지 않음)
    'OPEN': 15.0,        # J 입구 높이(입술 끝 → 위 부재) — 펜 13.1 이 수평으로 들어갈 틈
    'PM_D': 10.0, 'PM_T': 2.0,                         # 펜용 자석 Ø10×2, J 마다 3개 (사용자 지정)
    'PM_X': [(j, dx) for j in (1, 2) for dx in (-45.0, 0.0, 45.0)],   # (J 번호, 가운데에서 x) — J 마다 3개(사용자). 펜 자력은 몸통(두께 12.3~10, 펜 23~148)에만 있음(사용자) → 펜 위치 43·88·133. 위아래 같은 x → 일시정지 3번
    'SKIN': 1.3,         # 펜 홈 바닥 ↔ 자석 사이 살(안 보이게) — 벽 최소 1.2 + 측정 여유 0.1
    'FILLET': 0.9, 'FILLET_IN': 0.8,                   # 바깥·안쪽 모서리 둥글기(2D) — 바깥은 가장 얇은 살 2.0 의 절반 미만
}
COLORS = {'hanger': '#37474f'}
LAYER = 0.2

def derived():
    p = dict(P); p['MS'] = p['MOUSE_T'] + 2 * p['MOUSE_CLR']            # 리모컨 칸 안쪽 폭(y)
    p['MAG_X'] = [p['MAG_X0'] + i * p['MAG_PITCH'] for i in range(p['MAG_N'])]
    p['GW'] = p['PEN_S'] / 2 + p['PEN_CLR']                              # 펜 홈 최대 반지름
    p['RO'] = p['GW'] + p['PEN_WALL']                                     # J 바깥 반지름
    p['Y_B'] = p['T_BACK'] - (p['BWALL'] + 2 * p['GW'] + p['PEN_WALL'])  # 뒤 벽 뒷면 y: J 앞 끝이 앞판 앞면과 같게
    p['Y_BI'] = p['Y_B'] + p['BWALL']                                     # 뒤 벽 앞면 = 리모컨 칸·J 홈 뒤
    p['YC'] = p['Y_BI'] + p['GW']                                         # J 홈 축 y
    p['Z_RF'] = -p['SHELF'] - p['LIFT'] - p['LIP_R'] - p['MOUSE_W']        # 리모컨 칸 바닥 윗면 z
    p['PM_H'] = p['PM_T'] + p['MAG_CLR_T']                                # 펜 자석 슬롯 두께 2.1
    p['HEEL'] = p['GW'] + p['SKIN'] + p['PM_H'] + 1.2                     # 축 → J 바닥 밑면 (자석 아래 살 1.2)
    p['Z1'] = p['Z_RF'] - p['WALL'] - p['OPEN'] - p['LIP']                 # 위 J 축 z (리모컨 칸 바닥 아래 입구 15)
    p['Z2'] = p['Z1'] - p['HEEL'] - p['OPEN'] - p['LIP']                  # 아래 J 축 z
    p['Z_BOT'] = p['Z2'] - p['HEEL']                                      # 아래 끝
    # (J, x, 슬롯 윗면 z): 그 x 의 펜 홈 바닥(펜 반지름 + 0.3) 바로 아래 살 SKIN — 펜이 가늘어지는 곳도 자석과의 거리가 같게
    p['PM'] = [(j, p['W'] / 2 + dx, (p['Z1'] if j == 1 else p['Z2']) - (pen_w(p['W'] / 2 + dx + p['PEN_S0']) / 2 + p['PEN_CLR']) - p['SKIN'])
               for j, dx in p['PM_X']]
    # 숨은 자석 일시정지 높이(출력 z' = 설치 x): 슬롯 윗면(자석 끝 +0.1)을 층 격자로 올림 → 그 층까지 출력 후 멈춤
    r = (p['PM_D'] + p['MAG_CLR_D']) / 2
    p['PAUSE_Z'] = sorted(set(round(math.ceil((x + r + 0.1) / LAYER - 1e-6) * LAYER, 2) for _, x, _ in p['PM']))
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

def profile(p):
    """옆 단면(y, z) 한 덩어리: 앞판(TV 자석) → TV 밑면 받침 선반 → 뒤 벽에 매달린 리모컨 칸(세움) → J 고리 2개(위아래).
    전부 앞판 앞면(y = T_BACK)보다 뒤, TV 밑(y < 0) 쪽. J = 둥근 요람(입술 끝 = 축 + LIP) + 바닥 굽(숨은 자석 자리)."""
    tb, w, yc, ro, yb, ybi = p['T_BACK'], p['WALL'], p['YC'], p['RO'], p['Y_B'], p['Y_BI']
    zr = p['Z_RF']; ylip = ybi + p['MS']
    parts = [sbox(0, -p['SHELF'], tb, p['H_TOP']),                                        # 앞판
             sbox(yb, -p['SHELF'], tb, 0),                                                # TV 밑면 받침 선반
             sbox(yb, p['Z_BOT'] + 2, ybi, 0),                                            # 뒤 벽
             sbox(yb, zr - w, ylip + w, zr), sbox(ylip, zr, ylip + w, zr + p['LIP_R'])]   # 리모컨 칸 바닥·앞 입술
    hw = (p['PM_D'] + p['MAG_CLR_D']) / 2 + 1.5                                          # 굽 반폭: 자석 반지름 + 옆 살 (굽 모서리 R3.5)
    for zc in (p['Z1'], p['Z2']):
        parts += [Point(yc, zc).buffer(ro, 64).intersection(sbox(-200, zc - 50, 100, zc + p['LIP'])),
                  sbox(yb, zc - p['HEEL'], yc + hw, zc).buffer(-3.5, 16).buffer(3.5, 16), sbox(yb, zc - p['HEEL'] + 2, yc, zc + p['LIP'])]
    f, fi = p['FILLET'], p['FILLET_IN']
    out = unary_union(parts).buffer(-f, 8).buffer(f, 8).buffer(fi, 8).buffer(-fi, 8)
    out = out.difference(sbox(-500, 0, 0, 500)).intersection(sbox(-500, -500, tb, 500))   # TV 자리(앞면·밑면 모서리)는 비우고, 앞판 앞면 평면 유지
    if out.geom_type != 'Polygon': raise SystemExit(f'단면이 한 덩어리가 아님: {out.geom_type}')
    return out

def _sweep(prof, W):
    nz = int(math.ceil(W / 2.0)) + 1; path = np.column_stack([np.zeros(nz), np.zeros(nz), np.linspace(0, W, nz)])
    body = trimesh.creation.sweep_polygon(prof.simplify(0.01), path)
    body.apply_transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], float))   # (py, -px) → (px, py)
    return body                                                                # 출력 좌표 (x', y', z') = (y, z, x)

def slot(r, top):
    """숨은 자석 슬롯 단면(u=x, v): 아래 반원 + 위로 곧은 홈(윗면 = top, 층 격자). 일시정지 때 위에서 자석을 떨어뜨려 넣고
    다음 층부터 슬롯 두께(2.1) 폭 브리지로 덮인다."""
    return unary_union([Point(0, 0).buffer(r, 32), sbox(0, -r, top, r)])

INV = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float)    # 설치 → 출력 (MOUNT 의 역)
def _place(poly, h0, h1, L):
    """(u, v) 폴리곤을 h0~h1 로 압출 → 지역 (u, v, h) 를 설치 좌표로 보내는 4×4 L → 출력 좌표."""
    m = trimesh.creation.extrude_polygon(poly, h1 - h0); m.apply_translation([0, 0, h0]); m.apply_transform(INV @ L); return m

def make_parts():
    """출력 방향 공칭 파트 {이름: trimesh}. 출력 좌표 (x', y', z') = (y, z, x)."""
    p = derived(); dep = p['MAG_T'] + p['MAG_CLR_T']; r = (p['PM_D'] + p['MAG_CLR_D']) / 2; cut = []
    for xm in p['MAG_X']:   # TV 쪽 열린 원형 포켓(깊이 1.1 — 천장이 짧아 양끝에 걸쳐 출력, 사용자 요청으로 눈물방울 없앰): 설치 (x, y, z) = (u + xm, h, MAG_Z − v)  (det +1)
        cut.append(_place(Point(0, 0).buffer((p['MAG_D'] + p['MAG_CLR_D']) / 2, 64), -1.0, dep, np.array([[1, 0, 0, xm], [0, 0, 1, 0], [0, -1, 0, p['MAG_Z']], [0, 0, 0, 1]], float)))
    for _, xm, ztop in p['PM']:   # 펜 자석 숨은 슬롯: 설치 (x, y, z) = (u + xm, v + YC, h), h = 윗면 − 2.1 ~ 윗면
        top = math.ceil((xm + r + 0.1) / LAYER - 1e-6) * LAYER - xm
        cut.append(_place(slot(r, top), ztop - p['PM_H'], ztop, np.array([[1, 0, 0, xm], [0, 1, 0, p['YC']], [0, 0, 1, 0], [0, 0, 0, 1]], float)))
    cut += [groove_cutter(p, p['YC'], zc, p['LIP'] + 3.0) for zc in (p['Z1'], p['Z2'])]
    return {'hanger': trimesh.boolean.difference([_sweep(profile(p), p['W'])] + cut, engine='manifold')}

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
          {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items() if k in ('MS', 'GW', 'RO', 'Y_B', 'YC', 'Z_RF', 'HEEL', 'Z1', 'Z2', 'Z_BOT', 'MAG_X', 'PM', 'PAUSE_Z')})
