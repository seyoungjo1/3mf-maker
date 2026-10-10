"""tv-pen-hanger 조립 정의 — 파이프라인이 공칭 파트(parts_nominal.pkl)로 define(parts) 를 불러 검사한다.
출력 좌표 (x', y', z') = (설치 y, 설치 z, 설치 x) → 설치 좌표로 돌리는 행렬 MOUNT (회전, det +1).
파트: hanger 한 덩어리(리모컨 홈 + 아래 J 고리 2, TV 쪽 Ø20 자석 5, J 바닥에 숨은 Ø10×2 펜 자석 3).
내용물(extra): 거치대 면(가정 W×10×25 판), 자석, 펜 2개, 에어마우스(설명서 치수 상자).
치수는 build.py 의 derived() 를 그대로 쓴다(같은 숫자를 두 번 적지 않는다)."""
import os, sys, numpy as np, trimesh
from trimesh.transformations import translation_matrix as T
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import derived

MOUNT = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)    # 출력 → 설치

def _box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float); b = trimesh.creation.box(extents=hi - lo); b.apply_translation((lo + hi) / 2); return b
def _cyl(r, h, axis, center):
    c = trimesh.creation.cylinder(radius=r, height=h, sections=128)
    if axis == 'x': c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    if axis == 'y': c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation(center); return c

def _pen(p, yc, zc):
    """펜 전체 윤곽(캡~펜촉, build.pen_section)을 로프트 — J 홈 축에서 PEN_CLR 만큼 내려앉혀(−0.3 + 0.05, 다각형 현 처짐만큼) 홈 바닥에 얹음."""
    from build import pen_section; from loft import loft_rings
    from shapely.geometry import Polygon
    ss = np.r_[np.arange(0.0, p['PEN_L'], 1.0), p['PEN_L']]
    rings = [(s_, Polygon(np.asarray(pen_section(s_).exterior.coords))) for s_ in ss]
    m = loft_rings(rings, M=160)                                               # (u, v, s)
    m.apply_transform(np.array([[0, 0, 1, -p['PEN_S0']], [1, 0, 0, yc], [0, 1, 0, zc - p['PEN_CLR'] + 0.05], [0, 0, 0, 1]], float))
    return m

def define(parts):
    p = derived(); W = p['W']; mt = p['MAG_T']; rec = p['MAG_CLR_T']
    extra = {'tv': _box([-20, -p['TV_D'], 0], [W + 20, 0, 80])}                            # TV 아래쪽(가정: 앞면 평면·밑면 평평, 자석 거치대는 앞면)
    for i, xm in enumerate(p['MAG_X']):
        extra[f'magnet{i + 1}'] = _cyl(p['MAG_D'] / 2, mt, 'y', [xm, rec + mt / 2, p['MAG_Z']])  # TV 쪽 열린 포켓 바닥에 닿음
    for i, (j, xm, ztop) in enumerate(p['PM']):                                               # 펜 자석: J 굽 밑면 포켓(밑에서 끼움)
        extra[f'pm{i + 1}'] = _cyl(p['PM_D'] / 2, p['PM_T'], 'z', [xm, p['YC'], ztop + p['PM_H'] - p['PM_T'] / 2])   # 포켓 천장에 닿게 접착(밑면에서 0.1 들어감)
    extra['pen1'] = _pen(p, p['YC'], p['Z1']); extra['pen2'] = _pen(p, p['YC'], p['Z2'])
    y0 = p['Y_BI'] + p['MOUSE_CLR']                                                             # 리모컨 세움, 칸 가운데
    from shapely.geometry import box as sbox                                                    # M5 단면: 9 × 45 둥근 사각(모서리 MOUSE_R, 가정), x 로 155
    rU, rM, dy = p['MS'] / 2, p['MOUSE_R'], p['MOUSE_T'] / 2 - p['MOUSE_R']                     # U 바닥에 얹힘: 모서리 원이 U 원에 닿는 높이
    zb = p['Z_RF'] + rU - rM - np.sqrt(max((rU - rM) ** 2 - dy ** 2, 0)) + 0.04   # + 다각형 현 처짐
    sec = sbox(y0, zb, y0 + p['MOUSE_T'], zb + p['MOUSE_W']).buffer(-rM, 64).buffer(rM, 64)
    mo = trimesh.creation.extrude_polygon(sec, p['MOUSE_L']); mo.apply_transform(np.array([[0, 0, 1, W / 2 - p['MOUSE_L'] / 2], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    extra['mouse'] = mo
    mags = [f'magnet{i + 1}' for i in range(len(p['MAG_X']))]; pms = [f'pm{i + 1}' for i in range(len(p['PM']))]
    hung = {'hanger': MOUNT, 'tv': np.eye(4), 'pen1': np.eye(4), 'pen2': np.eye(4), 'mouse': np.eye(4), **{m: np.eye(4) for m in mags + pms}}
    apart = {'hanger': T([0, 40, 0]) @ MOUNT, 'tv': np.eye(4), 'pen1': T([0, 80, 0]), 'pen2': T([0, 80, 0]), 'mouse': T([0, 40, 120]),
             **{m: T([0, 20, 0]) for m in mags}, **{m: T([0, 40, 0]) for m in pms}}
    ymid = p['Y_BI'] + p['MS'] / 2; zr = p['Z_RF']
    pen_side = lambda zc: {'region': [[0, 0, zc - 1], [W, 100, zc + 12]], 'min_gap': 0.2}
    pen_of = {1: 'pen1', 2: 'pen2'}
    return {
        'extra': extra,
        'states': {'분리': apart, '걸림': hung},
        'pairs': [['hanger', 'tv', {'contact': True}]]                                            # 앞판 뒷면·선반 윗면이 TV 에 닿음
                 + [['hanger', m, {'contact': True}] for m in mags] + [['tv', m, {'min_gap': p['MAG_CLR_T'] - 0.01}] for m in mags]
                 + [['hanger', m, {'contact': True}] for m in pms]
                 + [[pen_of[j], f'pm{i + 1}', {'min_gap': p['SKIN']}] for i, (j, _, _) in enumerate(p['PM'])]
                 + [['hanger', 'pen1', {'contact': True}], ['hanger', 'pen2', {'contact': True}], ['hanger', 'mouse', {'contact': True}],
                    ['pen1', 'pen2', {'min_gap': 1.0}], ['pen1', 'mouse', {'min_gap': 1.0}], ['tv', 'mouse', {'min_gap': round(p['Z_RF'] + p['LIP_R'] - zb + p['LIFT'] + p['SHELF'] - 0.1, 2)}],  # 입술 넘김: 밑면(U 위 안착 zb)→입술 위 + 여유 + 선반
                    # 리모컨 옆면 ↔ 칸 벽 여유(U 바닥 위 곧은 구간)
                    ['hanger', 'mouse', {'region': [[0, -100, zr + p['MS'] / 2 + 1], [W, ymid, zr + 40]], 'min_gap': 0.75}],
                    ['hanger', 'mouse', {'region': [[0, ymid, zr + p['MS'] / 2 + 1], [W, 10, zr + 40]], 'min_gap': 0.75}],
                    # 펜 ↔ J 홈 옆벽(바닥 접촉 제외: 축 아래 1 mm 위쪽 — 펜이 0.25 내려앉아 캡(Ø7)처럼 가는 곳은 축 −2 에서 옆 간격 0.17)
                    ['hanger', 'pen1', pen_side(p['Z1'])], ['hanger', 'pen2', pen_side(p['Z2'])]],
        'sweeps': [],
        'notes': [f"TV 쪽 자석 {len(mags)}개: 앞면이 앞판 뒷면에서 {rec} mm 들어감 → TV 거치대 면과 간격 {rec} mm. 무게는 선반이 TV 밑면에 걸려 받음",
                  '리모컨·펜은 모두 앞판 앞면(y = T_BACK)보다 뒤 — 앞으로 안 튀어나옴',
                  f"펜 자석 Ø{p['PM_D']}×{p['PM_T']} {len(pms)}개: J 굽 밑면 포켓에 밑에서 끼워 접착, 펜 홈 바닥까지 살 {p['PM_SKIN']} mm",
                  'TV 밑면 모양·자석 거치대 높이(MAG_Z)는 가정 — 실측 후 build.py P 만 바꾸면 전부 다시 검사된다'],
    }
