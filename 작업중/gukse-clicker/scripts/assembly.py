"""gukse-clicker 조립 정의 — 파이프라인이 공칭 파트(parts_nominal.pkl)로 define(parts) 를 불러 검사한다.
states: 상태별 파트 4×4 행렬(조립 GIF 로 순환) · pairs: [a, b, {"contact": True} | {"min_gap": 0.3, "region": [[x0,y0,z0],[x1,y1,z1]]}]
sweeps: 회전 부품 각도 스윕(간섭 0 범위·작동 GIF). need 범위를 못 채우면 ⚠. 결합부 좌표는 상대 파트에서 측정한 값으로 넣는다."""
import numpy as np
from trimesh.transformations import rotation_matrix as R, translation_matrix as T

def define(parts):
    b = parts['base'].bounds; W, D, H = b[1] - b[0]; t = parts['lid'].extents[2]
    closed = T([0, D, H + t]) @ R(np.pi, [1, 0, 0])          # 뒤집어 출력한 뚜껑을 본체 윗면에 얹음(윗면 접촉)
    piv = [0, D, H + t]                                       # 뒤 모서리 경첩축(틀 예시). 축 -x 방향 회전 = 앞쪽이 위로 들림(+x 면 상자 안으로 돈다)
    return {
        'states': {'분리': {'base': np.eye(4), 'lid': T([0, 0, 25]) @ closed}, '조립-닫힘': {'base': np.eye(4), 'lid': closed}},
        'pairs': [['base', 'lid', {'contact': True}]],
        'sweeps': [{'name': '뚜껑 열기', 'part': 'lid', 'pivot': piv, 'axis': [-1, 0, 0], 'base': closed, 'angles': [0, 30, 60, 90, 120],
                    'against': ['base'], 'need': [0, 120]}],
        'notes': ['틀 예시 — 실제 도면의 결합부로 바꿀 것'],
    }
