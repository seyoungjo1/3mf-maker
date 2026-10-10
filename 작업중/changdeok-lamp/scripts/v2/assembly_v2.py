"""인정전 램프 v2 조립 정의(pipeline). 공칭 메시(parts_nominal.pkl)는 이미 조립 좌표라 '조립' 상태는 모두 단위행렬.
쌓는 구조: 아래 부재 윗면에 위 부재가 얹힌다(contact). 흰 테는 처마밑·기와 사이에 위아래 0.15 틈(휜 곡면 분할 차이 흡수)."""
import json, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
def define(parts):
    I = np.eye(4).tolist(); n = list(parts)
    lift = json.load(open(os.path.join(HERE, '..', '..', 'qc', 'states_v2.json'), encoding='utf-8'))['분리']
    T = lambda d: [[1, 0, 0, d[0]], [0, 1, 0, d[1]], [0, 0, 1, d[2]], [0, 0, 0, 1]]
    sep = {k: list(lift.get(k, [0, 0, 0])) for k in n}
    for g, sx in (('U_roof_gableL', -1), ('U_roof_gableR', 1)):        # 합각 널은 기와 옆면 포켓에 옆으로 끼운다 → 분리 상태도 옆으로 뺀다
        if g in sep: sep[g] = [sx * 30.0, 0, lift.get('U_roof_tile', [0, 0, 0])[2]]
    states = {'분리': {k: T(sep[k]) for k in n}, '조립': {k: I for k in n}}
    C = {'contact': True}
    pairs = [['platform', 'L_floor', C]] + [['L_floor', w, C] for w in ('wall_front', 'wall_back', 'wall_left', 'wall_right', 'L_diffuser')]
    pairs += [[w, 'L_ring', C] for w in ('wall_front', 'wall_back', 'wall_left', 'wall_right')]
    pairs += [['wall_front', 'wall_left', C], ['wall_front', 'wall_right', C], ['wall_back', 'wall_left', C], ['wall_back', 'wall_right', C]]
    pairs += [['L_ring', 'L_band', C], ['L_band', 'L_roof_soffit', C], ['L_roof_soffit', 'L_roof_eave_white', C], ['L_roof_eave_white', 'L_roof_tile', C]]
    pairs += [['L_roof_tile', f'L_roof_hip{i}', C] for i in range(1, 5)] + [['L_roof_tile', 'U_floor', C]]
    pairs += [['U_floor', w, C] for w in ('uwall_front', 'uwall_back', 'uwall_left', 'uwall_right', 'U_diffuser')]
    pairs += [[w, 'U_ring', C] for w in ('uwall_front', 'uwall_back', 'uwall_left', 'uwall_right')]
    pairs += [['U_ring', 'U_band', C], ['U_band', 'U_roof_soffit', C], ['U_roof_soffit', 'U_roof_eave_white', C], ['U_roof_eave_white', 'U_roof_tile', C]]
    pairs += [['U_roof_tile', p, C] for p in ['U_roof_ridge', 'U_roof_gableL', 'U_roof_gableR'] + [f'U_roof_hip{i}' for i in range(1, 5)] + [f'U_roof_desc{i}' for i in range(1, 5)]]
    # 떨어져 있어야 하는 곳(최소 간격)
    pairs += [['wall_front', 'L_diffuser'], ['wall_left', 'L_diffuser'], ['L_ring', 'L_diffuser', {'min_gap': 0.25}], ['L_band', 'wall_front'],
              ['uwall_front', 'U_diffuser'], ['U_ring', 'U_diffuser', {'min_gap': 0.25}], ['L_roof_tile', 'uwall_front'], ['L_roof_tile', 'uwall_left'],
              ['L_roof_soffit', 'L_roof_tile'], ['U_roof_soffit', 'U_roof_tile'], ['L_roof_eave_white', 'L_roof_hip1'], ['U_roof_eave_white', 'U_roof_hip1']]
    # 무게중심·넘어지는 각(쌓는 조립)
    vol = sum(m.volume for m in parts.values()); c = sum(m.volume * m.center_mass for m in parts.values()) / vol
    pb = parts['platform'].bounds; h = c[2] - pb[0, 2]
    tip = [np.degrees(np.arctan2(min(c[a] - pb[0, a], pb[1, a] - c[a]), h)) for a in (0, 1)]
    notes = [f'무게중심 ({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f}) mm, 월대 밑에서 높이 {h:.1f} → 넘어지는 각 좌우 {tip[0]:.1f}° · 앞뒤 {tip[1]:.1f}°',
             '흰 테(0.7)는 평평하게 출력해 끼우면 처마밑 들림(모서리 3.0)을 따라 휜다 — 휨 변형률 ≈0.25 %',
             '조명: Bambu LED Lamp Kit 001(Ø59×18) — 월대 포켓, 하층 바닥판이 덮음']
    return {'states': states, 'pairs': pairs, 'notes': notes}
