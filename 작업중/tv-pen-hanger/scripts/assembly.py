"""tv-pen-hanger 조립 정의 — 파이프라인이 공칭 파트(parts_nominal.pkl)로 define(parts) 를 불러 검사한다.
출력 좌표 (x', y', z') = (설치 y, 설치 z, 설치 x) → 설치 좌표로 돌리는 행렬 MOUNT (회전, det +1).
내용물(extra): 거치대 면(가정 120×10×25 판), 자석 3개(포켓 바닥에 닿고 앞면이 뒷면에서 0.1 들어감), 펜 2개, 에어마우스(가정 치수 상자).
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

def _pen(p, yc):
    """펜 굵은 쪽 단면(12.5 각 R4)을 길이 전체로 — 가는 쪽(Ø10)은 더 작아 홈 안에서 굵은 쪽이 먼저 닿는다. 홈 바닥에 +0.02 띄워 얹음(접촉)."""
    from shapely.geometry import box as sbox
    s, r = p['PEN_S'], p['PEN_R']; sec = sbox(-s / 2, -s / 2, s / 2, s / 2).buffer(-r, 16).buffer(r, 16)
    m = trimesh.creation.extrude_polygon(sec, p['PEN_L'])                       # (u, v, w): w = 길이
    m.apply_transform(np.array([[0, 0, 1, p['W'] / 2 - p['PEN_L'] / 2], [1, 0, 0, yc], [0, 1, 0, p['Z_G'] + s / 2 + 0.02], [0, 0, 0, 1]], float))
    return m

def define(parts):
    p = derived(); W = p['W']; mt = p['MAG_T']; rec = p['MAG_CLR_T']
    extra = {'holder': _box([W / 2 - 60, -10, p['MAG_Z'] - 12.5], [W / 2 + 60, 0, p['MAG_Z'] + 12.5])}
    for i, xm in enumerate(p['MAG_X']):
        extra[f'magnet{i + 1}'] = _cyl(p['MAG_D'] / 2, mt, 'y', [xm, rec + mt / 2, p['MAG_Z']])        # 포켓 바닥(y 1.1)에 닿음
    for k, yc in (('pen1', p['Y_P1']), ('pen2', p['Y_P2'])):
        extra[k] = _pen(p, yc)
    y0 = p['T_BACK'] + p['MOUSE_CLR']
    extra['mouse'] = _box([W / 2 - p['MOUSE_L'] / 2, y0, p['WALL']], [W / 2 + p['MOUSE_L'] / 2, y0 + p['MOUSE_T'], p['WALL'] + p['MOUSE_W']])
    mags = [f'magnet{i + 1}' for i in range(len(p['MAG_X']))]
    hung = {'hanger': MOUNT, 'holder': np.eye(4), 'pen1': np.eye(4), 'pen2': np.eye(4), 'mouse': np.eye(4), **{m: np.eye(4) for m in mags}}
    apart = {'hanger': T([0, 40, 0]) @ MOUNT, 'holder': np.eye(4), 'pen1': T([0, 40, 70]), 'pen2': T([0, 40, 90]), 'mouse': T([0, 40, 120]),
             **{m: T([0, 20, 0]) for m in mags}}
    ymid = (p['T_BACK'] + p['Y_MW']) / 2
    return {
        'extra': extra,
        'states': {'분리': apart, '걸림': hung},
        'pairs': [['hanger', 'holder', {'contact': True}]]
                 + [['hanger', m, {'contact': True}] for m in mags] + [['holder', m, {'contact': True}] for m in mags]
                 + [['hanger', 'pen1', {'contact': True}], ['hanger', 'pen2', {'contact': True}], ['hanger', 'mouse', {'contact': True}],
                    ['pen1', 'pen2', {'min_gap': 1.0}], ['pen1', 'mouse', {'min_gap': 1.0}],
                    # 마우스 옆면 ↔ 홈 벽 여유(바닥 접촉 제외: 마우스 옆면 z 6~40 만)
                    ['hanger', 'mouse', {'region': [[0, -1, 6], [W, ymid, 40]], 'min_gap': 0.75}],
                    ['hanger', 'mouse', {'region': [[0, ymid, 6], [W, p['Y_MW'] + 1, 40]], 'min_gap': 0.75}],
                    # 펜 ↔ 홈 옆벽(바닥·바닥 모서리 접촉 제외: 홈 바닥 R 위쪽)
                    ['hanger', 'pen1', {'region': [[0, 0, p['Z_G'] + p['GR'] + 0.5], [W, 100, 40]], 'min_gap': 0.4}],
                    ['hanger', 'pen2', {'region': [[0, 0, p['Z_G'] + p['GR'] + 0.5], [W, 100, 40]], 'min_gap': 0.4}]],
        'sweeps': [],
        'notes': [f"자석 앞면은 걸이대 뒷면에서 {rec} mm 들어감 → 거치대 면과 간격 {rec} mm (흡착력 계산 gap)",
                  '거치대 면·펜·마우스는 가정 치수 — 치수 조사·실측 후 build.py P 만 바꾸면 전부 다시 검사된다'],
    }
