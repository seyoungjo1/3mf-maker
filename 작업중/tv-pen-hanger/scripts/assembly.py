"""tv-pen-hanger 조립 정의 — 파이프라인이 공칭 파트(parts_nominal.pkl)로 define(parts) 를 불러 검사한다.
출력 좌표 (x', y', z') = (설치 y, 설치 z, 설치 x) → 설치 좌표로 돌리는 행렬 MOUNT (회전, det +1).
파트: hanger(리모컨 걸이, TV 쪽 자석 5) · penholder(J 고리 2, 걸이 밑면에 묻힌 자석 3쌍으로 붙음).
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
    p = derived(); W = p['W']; mt = p['MAG_T']; rec = p['MAG_CLR_T']; sk = p['SKIN']; r = p['MAG_D'] / 2
    # 거치대 면(가정): 걸이대 폭 W × 높이 25 판, 자석 중심 높이에 띠
    extra = {'holder': _box([0, -10, p['MAG_Z'] - 12.5], [W, 0, p['MAG_Z'] + 12.5])}
    for i, xm in enumerate(p['MAG_X']):
        extra[f'magnet{i + 1}'] = _cyl(r, mt, 'y', [xm, rec + mt / 2, p['MAG_Z']])              # TV 쪽 열린 포켓, 바닥(y 1.1)에 닿음
    for i, xm in enumerate(p['JM_X']):                                                     # 묻힌 결합 자석: 서로 끌려 결합면 쪽 살(SKIN)에 붙음
        extra[f'jm_up{i + 1}'] = _cyl(r, mt, 'z', [xm, p['JM_Y'], sk + mt / 2])
        extra[f'jm_dn{i + 1}'] = _cyl(r, mt, 'z', [xm, p['JM_Y'], -sk - mt / 2])
    extra['pen1'] = _pen(p, p['YC'], p['Z1']); extra['pen2'] = _pen(p, p['YC'], p['Z2'])
    y0 = p['T_BACK'] + p['MOUSE_CLR']
    extra['mouse'] = _box([W / 2 - p['MOUSE_L'] / 2, y0, p['FLOOR']], [W / 2 + p['MOUSE_L'] / 2, y0 + p['MOUSE_T'], p['FLOOR'] + p['MOUSE_W']])
    mags = [f'magnet{i + 1}' for i in range(len(p['MAG_X']))]
    ups = [f'jm_up{i + 1}' for i in range(len(p['JM_X']))]; dns = [f'jm_dn{i + 1}' for i in range(len(p['JM_X']))]
    hung = {'hanger': MOUNT, 'penholder': MOUNT, 'holder': np.eye(4), 'pen1': np.eye(4), 'pen2': np.eye(4), 'mouse': np.eye(4),
            **{m: np.eye(4) for m in mags + ups + dns}}
    apart = {'hanger': T([0, 40, 0]) @ MOUNT, 'penholder': T([0, 40, -40]) @ MOUNT, 'holder': np.eye(4),
             'pen1': T([0, 80, -40]), 'pen2': T([0, 80, -60]), 'mouse': T([0, 40, 120]),
             **{m: T([0, 20, 0]) for m in mags}, **{m: T([0, 40, 0]) for m in ups}, **{m: T([0, 40, -40]) for m in dns}}
    ymid = (p['T_BACK'] + p['Y_MW']) / 2
    pen_side = lambda zc: {'region': [[0, 0, zc - 1], [W, 100, zc + 12]], 'min_gap': 0.2}
    return {
        'extra': extra,
        'states': {'분리': apart, '걸림': hung},
        'pairs': [['hanger', 'holder', {'contact': True}], ['hanger', 'penholder', {'contact': True}]]
                 + [['hanger', m, {'contact': True}] for m in mags] + [['holder', m, {'contact': True}] for m in mags]
                 + [['hanger', m, {'contact': True}] for m in ups] + [['penholder', m, {'contact': True}] for m in dns]
                 + [[u, d, {'min_gap': 2 * sk - 0.05}] for u, d in zip(ups, dns)]
                 + [['penholder', 'pen1', {'contact': True}], ['penholder', 'pen2', {'contact': True}], ['hanger', 'mouse', {'contact': True}],
                    ['pen1', 'pen2', {'min_gap': 1.0}], ['pen1', 'mouse', {'min_gap': 1.0}], ['hanger', 'pen1', {'min_gap': 1.0}],
                    # 마우스 옆면 ↔ 홈 벽 여유(바닥 접촉 제외)
                    ['hanger', 'mouse', {'region': [[0, -1, p['FLOOR'] + 3], [W, ymid, 80]], 'min_gap': 0.75}],
                    ['hanger', 'mouse', {'region': [[0, ymid, p['FLOOR'] + 3], [W, p['Y_MW'] + 1, 80]], 'min_gap': 0.75}],
                    # 펜 ↔ J 홈 옆벽(바닥 접촉 제외: 축 아래 1 mm 위쪽 — 펜이 0.25 내려앉아 캡(Ø7)처럼 가는 곳은 축 −2 에서 옆 간격이 0.17 로 준다)
                    ['penholder', 'pen1', pen_side(p['Z1'])], ['penholder', 'pen2', pen_side(p['Z2'])]],
        'sweeps': [],
        'notes': [f"TV 쪽 자석 {len(mags)}개: 앞면이 걸이대 뒷면에서 {rec} mm 들어감 → 거치대 면과 간격 {rec} mm",
                  f"결합 자석 {len(ups)}쌍: 살 {sk} mm 속에 묻힘(안 보임) → 자석끼리 면 간격 {2 * sk} mm (= 철판 간격 {sk} 와 같은 힘, 거울상)",
                  '거치대 면·펜·마우스는 가정 치수 — 치수 조사·실측 후 build.py P 만 바꾸면 전부 다시 검사된다'],
    }
