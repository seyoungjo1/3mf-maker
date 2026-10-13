"""racket-grip-case v2 조립 정의 — 파이프라인이 공칭 파트(parts_nominal.pkl)로 define(parts) 를 불러 검사한다.
상태
- 감음(조립): 빌드가 만든 감은 원뿔 통(wrapped.pkl: 같은 매개 메시를 원뿔로 감음) + 캡 + G5 8각 손잡이.
- 래칫 물림: 위 띠(실제 치수) 머리 터널에 꼬리 토막(probe)을 실제 물린 자리에 넣음 — 교집합 0, 혀 톱니 ↔ 꼬리 골 0.2.
막 휨은 계산(build_meta.json film_strain_pct)으로: 변형률 = (막 두께/2) / (틈 / 꺾임각), 꺾임각 = 피치 / 반경.
"""
import os, sys, pickle
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_v2_tiles as B

def define(parts):
    I = np.eye(4); P = B.P
    wrapped = pickle.load(open(os.path.join(B.PROJ, 'wrapped.pkl'), 'rb'))
    L = B.layout(); t0, t1 = L['teeth_top']; v_end = t0 + 10 * P['TP']
    seg = B.V1.prism(B.V1._tail_outline(t0, t1, t1 + 2.0), 0, P['BT']) ^ B.box(v_end - 8.8, v_end + 7.2, -5, 5, -1, 5)
    probe = B.to_tm(seg.translate([2.8 - v_end, 0, P['BT'] + P['TUN_GAP']]))
    head_box = [[-6.0, -6.0, -0.5], [P['LH'] + 0.5, 6.0, 5.0]]
    extra = dict(wrapped); extra['probe'] = probe
    return {
        'states': {'래칫 물림': {'band_top_nat': I, 'probe': I}, '감음(조립)': {'w_fabric': I, 'cap': I, 'handle': I}},
        'pairs': [
            ['w_fabric', 'cap', {'contact': True}],                          # 아래 띠 안쪽면이 홈 바닥에 닿음
            ['handle', 'cap', {'contact': True}],                            # 손잡이 끝이 캡 바닥에 얹힘
            ['handle', 'w_fabric', {'min_gap': 1.0}],                        # 원뿔 통 안쪽 ↔ 8각 손잡이(위 1.65 ~ 아래 2.85)
            ['band_top_nat', 'probe', {'min_gap': 0.2, 'region': head_box}],
        ],
        'extra': extra,
        'notes': [f"원뿔 통: 안 반경 아래 {B.R_BOT:.2f} → 위 {B.R_TOP:.2f}(옆 여유 2). 막은 늘어나지 않아 펼칠 수 있는 원뿔로만 감김 — 출력 판은 그 전개도(반경 {B.RHO_BOT:.0f} 호)",
                  f"감음 상태는 헐거운 상태(위 띠 반경 = {B.R_TOP:.2f}). 끝까지 조이면 {B.R_TOP_TIGHT:.2f} — 톱니 {t0:.1f}~{t1:.1f}",
                  f'손잡이 길이 {P["HANDLE_L"]:.0f} mm·뽕 자리 높이 18 mm 는 가정(실측 전)'],
    }
