"""racket-grip-case 조립 정의 — 파이프라인이 공칭 파트(parts_nominal.pkl)로 define(parts) 를 불러 검사한다.
상태
- 펼침(출력): 천 A·B·띠 두 개를 출력 그대로 — 프린트인플레이스 틈(링크끼리 ≥ 0.4)이 지켜지는지 = 출력 중 융착 없음.
- 래칫 물림: 위 띠 머리 터널에 꼬리 토막(probe)을 실제 물린 자리에 넣음 — 교집합 0, 혀 톱니 ↔ 꼬리 골 0.2.
- 감음(조립): 빌드가 만든 감은 메시(wrapped.pkl: 천을 원통으로 굽힘, 행마다 반경이 달라 생기는 전단 포함) + 캡 + G5 8각 손잡이.
스윕
- 링크 꺾임: A 하나 + B 하나(팔이 A 창을 지남)를 창 가운데 축으로 돌려 간섭 0 범위 — 감기에 필요한 꺾임 = 피치/반경 ≈ 37°.
"""
import os, sys, math, pickle
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_v1_links as B
from trimesh.transformations import translation_matrix as T

def define(parts):
    I = np.eye(4); P = B.P; p = P['p']
    wrapped = pickle.load(open(os.path.join(B.PROJ, 'wrapped.pkl'), 'rb'))
    # 링크 꺾임 시험편: A 를 원점, B 를 -x 에 (팔 +x 로 A 왼쪽 창을 지남)
    jA = B.to_tm(B.elem_A(0.0, 0.0)); jB = B.to_tm(B.elem_B(-p, 0.0, [(1, 0)]))
    pivot = [-P['a'] + P['w'] / 2, 0.0, (P['hb'] + P['zt0']) / 2]     # A 왼쪽 창 가운데
    # 래칫 꼬리 토막: 위 띠 꼬리 윤곽에서 골 하나의 수직면이 혀 톱니 수직면(x 2.6)에서 0.2 떨어지게
    L = B.layout(); t0, t1 = L['teeth_top']; v_end = t0 + 10 * P['TP']
    outline = B._tail_outline(t0, t1, t1 + 2.0)
    seg = B.prism(outline, 0, P['BT']) ^ B.box(v_end - 8.8, v_end + 7.2, -5, 5, -1, 5)
    probe = B.to_tm(seg.translate([2.8 - v_end, J_y(), P['BT'] + P['TUN_GAP']]))
    head_box = [[-6.0, J_y() - 6.0, -0.5], [P['LH'] + 0.5, J_y() + 6.0, 5.0]]
    extra = dict(wrapped); extra.update({'jA': jA, 'jB': jB, 'probe': probe})
    flat = {'links_A': I, 'links_B': I, 'band_top': I, 'band_bottom': I}
    wrap = {'w_links_A': I, 'w_links_B': I, 'w_band_top': I, 'w_band_bottom': I, 'cap': I, 'handle': I}
    return {
        'states': {'펼침(출력)': flat, '감음(조립)': wrap, '래칫 물림': {'band_top': I, 'probe': I}},
        'pairs': [
            ['links_A', 'links_B', {'min_gap': 0.38}], ['links_A', 'band_top', {'min_gap': 0.38}], ['links_A', 'band_bottom', {'min_gap': 0.38}],
            ['band_top', 'probe', {'min_gap': 0.2, 'region': head_box}],
            ['w_links_A', 'w_links_B', {'min_gap': 0.05}], ['w_links_A', 'w_band_top', {'min_gap': 0.05}], ['w_links_A', 'w_band_bottom', {'min_gap': 0.05}],
            ['w_band_bottom', 'cap', {'contact': True}], ['w_links_A', 'cap', {'min_gap': 0.3}], ['w_links_B', 'cap', {'min_gap': 0.3}],
            ['handle', 'cap', {'contact': True}], ['handle', 'w_links_A', {'min_gap': 1.0}], ['handle', 'w_links_B', {'min_gap': 1.0}],
            ['handle', 'w_band_top', {'min_gap': 1.0}], ['handle', 'w_band_bottom', {'min_gap': 1.0}],
        ],
        'sweeps': [{'name': '링크 꺾임(베드 면 안쪽으로 감김)', 'part': 'jB', 'pivot': pivot, 'axis': [0, 1, 0], 'base': I,
                    'angles': [-45, -40, -37, -30, -20, -10, 0, 10, 20, 30, 37, 40], 'against': ['jA'], 'need': [-37, 0]}],
        'extra': extra,
        'notes': [f"감음 상태는 헐거운 상태(위 띠 반경 = 천 반경 {B.R_TUBE:.2f}). 위 띠를 끝까지 조이면 안 반경 {B.R_TOP_TIGHT:.2f}(8각 모서리) — 톱니 {t0:.1f}~{t1:.1f} 구간",
                  '링크 꺾임 스윕은 고정 축(창 가운데) 회전이라 보수적이다 — 실물은 팔이 창 안에서 미끄러져 더 꺾인다. 감는 데 필요한 꺾임 = 피치/반경 = 9.8/15.21 = 37°',
                  '빠짐 방지: B 가 위로 들릴 수 있는 양 0.8(팔 윗면 2.8 → 윗 막대 3.6), 그때 끝 기둥 밑면 0.8 이 아래 막대 윗면 1.2 보다 0.4 아래 → 옆으로 못 빠짐',
                  f'손잡이 길이 {P["HANDLE_L"]:.0f} mm·뽕 자리 높이 18 mm 는 가정(실측 전)'],
    }

def J_y(): return B.J * B.P['p']
