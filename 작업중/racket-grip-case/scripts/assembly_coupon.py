"""쿠폰 조립 정의: 출력 상태 A↔B 틈(융착 없음) + 이음매 꺾임 스윕(A 하나·B 하나).
꺾임 축은 탐색으로 고른 한 가지 움직임 경로(축 위치가 다르면 같은 각도라도 간섭이 다르다 — 간섭 0 경로가 하나라도 있으면 그 각도로 꺾일 수 있다).
비늘 바깥(베드 면 볼록) +, 비늘 안쪽 −. 손잡이에 비늘 바깥으로 감을 때 필요한 꺾임 ≈ 피치 / 비늘 면 반경 = 9.2 / 19 ≈ 28°."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nasa, coupon

def define(parts):
    I = np.eye(4); p = nasa.N['p']
    jA = coupon.to_tm(nasa.elem_A(0, 0)); jB = coupon.to_tm(nasa.elem_B(-p, 0, [(1, 0)]))
    return {
        'states': {'출력(펼침)': {'coupon_A': I, 'coupon_B': I}},
        'pairs': [['coupon_A', 'coupon_B', {'min_gap': 0.38}]],
        'sweeps': [{'name': '이음매 꺾임 — 비늘 바깥', 'part': 'jB', 'pivot': [-4.0, 0.0, 0.8], 'axis': [0, 1, 0], 'base': I,
                    'angles': [0, 5, 10, 15, 20, 25, 30, 35], 'against': ['jA'], 'need': [0, 30]},
                   {'name': '이음매 꺾임 — 비늘 안쪽', 'part': 'jB', 'pivot': [-3.5, 0.0, 0.4], 'axis': [0, 1, 0], 'base': I,
                    'angles': [0, -5, -10, -15, -20, -25, -30, -35, -40], 'against': ['jA'], 'need': [-35, 0]}],
        'extra': {'jA': jA, 'jB': jB},
        'notes': ['비늘 한 변 8.8, 틈 0.4, 피치 9.2, 두께 4.6(비늘 1.2 + 고리). 앞면 = 베드 면'],
    }
