"""digit-counter 조립 정의 — 공칭 파트(parts_nominal.pkl, 조립 좌표·숫자 00 정지)를 상태별 상대 행렬로 움직인다.
운동: 드럼(코어+디스크)은 캠축(x) 기준 -36°/카운트, 팔로워(셔터+줄+스템)는 캠 반지름만큼 z 이동, 레버는 -SWING 회전,
버튼(플런저+캡)은 패드를 따라 내려가고(놀이 1.0), 스프링은 z 로 눌린 근사, 축·칼라·노브는 리셋 때 회전.
강체로 판정할 수 없는 판스프링 폴·키·멈춤쇠·세그먼트 보임은 checks(2D 운동학·변형률)로 판정한다."""
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
import geom as G
P = G.P; AXP = [0.0, P['Y_C'], P['Z_C']]

def rotx(deg): return R(np.radians(deg), [1, 0, 0], AXP)
def drum_angles(tens, ones, press):
    """누름 비율 press(0..1) 에서 드럼 각(°). 폴은 2° 틈을 지나 민다. 일의 자리가 9 이면 십의 자리도(올림)."""
    ext = max(0.0, P['SWING'] * press - 2.0)
    return -36.0 * tens - (ext if ones % 10 == 9 else 0.0), -36.0 * ones - ext
def follower_dz(seg, drum_deg): return G.cam_r(seg, 90.0 - drum_deg) - P['R_LO']
def pad_z(lever_deg): return G._pt(P['PAD_R'], P['PAD_ANG'] + lever_deg)[1]
def state(names, tens=0, ones=0, press=0.0, shaft=0.0, explode=0.0):
    t_ang, o_ang = drum_angles(tens, ones, press); lev = -P['SWING'] * press
    dzp = 0.0 if press <= 0 else (pad_z(lev) - pad_z(0.0) - 1.0)
    lip_bottom = G.PAD_REST[1] - P['PAD_D'] / 2 - 3.0
    sp = (lip_bottom + dzp - 1.0) / (lip_bottom + 1.2 - 1.0)
    M = {}
    for n in names:
        k = META[n]['kind']; m = np.eye(4)
        if k.startswith('drum:'): m = rotx(t_ang if k.endswith('tens') else o_ang)
        elif k.startswith('fol:'):
            _, dn, s = k.split(':'); m = T([0, 0, follower_dz(s, t_ang if dn == 'tens' else o_ang)])
        elif k == 'lever': m = rotx(lev)
        elif k == 'button': m = T([0, 0, dzp])
        elif k == 'spring': m = T([0, 0, 1.0]) @ np.diag([1, 1, sp, 1]) @ T([0, 0, -1.0])
        elif k == 'shaft': m = rotx(shaft)
        if explode:
            e = {'fixed': 0, 'lever': 1, 'button': 2, 'spring': 1, 'shaft': 1}.get(k.split(':')[0], 1)
            if n in ('lid',): m = T([0, 0, 40 * explode]) @ m
            elif n == 'front': m = T([0, -95 * explode, 0]) @ m
            elif n == 'mid': m = T([0, -30 * explode, 0]) @ m
            elif k.startswith('fol:'): m = T([0, -68 * explode, 0]) @ m
            elif k.startswith('drum') or k in ('lever', 'shaft'): m = T([0, 0, 0]) @ m
        M[n] = m
    return M

META = json.load(open(os.path.join(os.path.dirname(HERE), 'meta.json'), encoding='utf-8'))

def checks():
    """기구 판정 — 값·기준·ok. 실패하면 파이프라인이 ⚠ 로 남긴다."""
    out = []
    def add(name, value, need, ok): out.append({'name': name, 'value': value, 'need': need, 'ok': bool(ok)})
    # 1) 숫자 0~9 마다 세그먼트 보임: 켜짐 = 줄이 슬롯을 100 % 덮음, 꺼짐 = 줄이 슬롯과 0 % 겹침(검정 홈만 보임)
    bad = []
    for k in range(10):
        for s in G.SEGS:
            dz = follower_dz(s, -36.0 * k); on = G.seg_on(s, k)
            ov = []
            for b in G.slots(s, 0.0):
                z0, z1 = b.bounds[1], b.bounds[3]; r0, r1 = z0 - P['RIB_EXT'] + dz + 0.3, z1 + dz - 0.3   # 줄 앞면(사다리꼴 윗변)
                ov.append(max(0.0, min(z1, r1) - max(z0, r0)) / (z1 - z0))
            f = min(ov) if on else max(ov)
            if (on and f < 0.69) or (not on and f > 0.0): bad.append(f'{k}{s}:{f:.2f}')
    add('세그먼트 보임(0~9, 켜짐=줄 앞면이 슬롯 70 % 이상, 꺼짐=0 %)', '전부 맞음' if not bad else ', '.join(bad[:6]), '70 % / 0 %', not bad)
    # 2) 숫자 차례: 00→99→00 을 버튼 100 번으로(올림은 일의 자리 9 에서만)
    v = 0; seq_ok = True
    for i in range(100):
        t, o = divmod(v, 10); carry = (o == 9); o = (o + 1) % 10; t = (t + (1 if carry else 0)) % 10; v = t * 10 + o
        seq_ok &= (v == (i + 1) % 100)
    add('카운트 차례 00→99→00 (버튼 100 번)', '맞음' if seq_ok else '틀림', '100 번 뒤 00', seq_ok)
    # 3) 폴 물림 깊이(톱니 끝 15.0 - 폴 끝 반지름) — 일의 자리 R1(P1), 올림 Rc(P2)
    tip = G.ratchet_r(P['FACE0'] + 2.0) + 0.3
    add('P1·P2 물림 깊이 (톱니 면)', f'{P["RT_TIP"] - tip:.2f} mm', '≥ 1.8', P['RT_TIP'] - tip >= 1.8)
    # 4) 마스크: 9 가 아닐 때 P2 가 톱니 끝 위로 뜸(마스크 테 - 톱니 끝), 9 일 때 홈이 P2 를 덮는 각
    add('마스크 테가 P2 를 톱니 위로 띄움', f'{P["M1_RIM"] - P["RT_TIP"]:.2f} mm', '≥ 0.5', P['M1_RIM'] - P['RT_TIP'] >= 0.5)
    p2_push = (G.NOTCH[0], G.NOTCH[0] + 8.0)    # 누르기 시작(2° 틈 닫힘) P2 이 = 드럼 324-2 ~ +8
    floor_ok = all(G.mask_r(a) <= G.ratchet_r(a) + 1e-6 for a in np.linspace(p2_push[0] + 0.01, p2_push[1], 40))
    add('일의 자리 9: 마스크 홈 바닥 = 톱니 경사(P2 가 R1·Rc 면까지 내려감)', f'홈 {G.NOTCH[0]:.0f}~{G.NOTCH[1]:.0f}°, P2 이 {p2_push[0]:.0f}~{p2_push[1]:.0f}°', '홈이 이를 덮음', floor_ok)
    over = max(G.ratchet_r(a) - G.mask_r(a) for a in np.linspace(0, 360, 3601))
    add('R1 이 M1 위로 나온 양(코어 출력 오버행)', f'{over:.2f} mm', '≤ 0.05', over <= 0.05)
    # 5) 판스프링 변형률 ε = 1.5·t·δ/L² (캔틸레버, PLA 반복 ≤ 4 %, 늘 휘어 있는 것은 ≤ 1.2 %)
    t = P['ARM_T']; L1 = np.radians(P['P1_ROOT'] - P['P1_ANG']) * P['P1_ARM_R']; L2 = np.radians(P['P2_ROOT'] - P['P2_ANG']) * P['P2_ARM_R']
    d1 = P['RT_TIP'] + 0.2 - tip; d2 = P['M1_RIM'] - tip
    e1, e2 = 1.5 * t * d1 / L1 ** 2 * 100, 1.5 * t * d2 / L2 ** 2 * 100
    add(f'P1 폴 팔 변형률(톱니 넘을 때 δ {d1:.2f}, L {L1:.1f})', f'{e1:.2f} %', '≤ 4 %', e1 <= 4)
    add(f'P2 폴 팔 변형률(마스크 테 위 상시 δ {d2:.2f}, L {L2:.1f})', f'{e2:.2f} %', '≤ 1.2 %', e2 <= 1.2)
    Lk = np.radians(160) * 4.1; dk = P['HEX_V'] - 2.0; ek = 1.5 * 1.2 * dk / Lk ** 2 * 100
    add(f'리셋 키 팔 변형률(육각 모서리 δ {dk:.2f}, L {Lk:.1f})', f'{ek:.2f} %', '≤ 2 %', ek <= 2)
    Ll = P['LEAF_L']; el = 1.5 * P['LEAF_T'] * (P['STAR_TIP'] - P['STAR_ROOT'] - 0.2) / Ll ** 2 * 100
    add(f'멈춤쇠 판스프링 변형률(별 끝 넘을 때, L {Ll:.0f})', f'{el:.2f} %', '≤ 4 %', el <= 4)
    # 6) 리셋 키·홈: 00 에서 이가 홈 안(걸림벽 96° ↔ 이 걸림면 94°, 홈 바닥 1.8 < 이 끝 2.0)
    add('리셋: 00 에서 키 이가 축 홈 안', '걸림 틈 2°, 바닥 여유 0.20 mm', '이 끝 > 홈 바닥', 2.0 > 1.8)
    # 7) 버튼 스프링: 지그재그 8 줄 L 20 t 1.2 — 줄당 처짐·변형률, 힘(고정-안내 보 12EI/L³, 직렬)
    lip_bottom = G.PAD_REST[1] - P['PAD_D'] / 2 - 3.0; free = lip_bottom + 1.2 - 1.0; stroke = G.btn_stroke(); comp = 1.2 + stroke
    zb1 = lip_bottom + 1.2 - 1.5; g = (zb1 - 3.0 - 8 * 1.2) / 7
    db = comp / 8; es = 3 * 1.2 * db / 20 ** 2 * 100; b = P['SPR_X'][1] - P['SPR_X'][0]
    k = 1 / (8 * 20 ** 3 / (12 * 3300 * b * 1.2 ** 3 / 12))
    add('버튼 스프링 줄 틈 > 줄당 눌림', f'틈 {g:.2f} / 눌림 {db:.2f} mm', '틈 > 눌림 + 0.5', g > db + 0.5)
    add('버튼 스프링 변형률(완전 누름)', f'{es:.2f} %', '≤ 2.5 %', es <= 2.5)
    add('버튼 힘(스프링, 정지 → 끝)', f'{k * 1.2:.2f} → {k * comp:.2f} N', '0.3 ~ 8 N', 0.3 <= k * 1.2 and k * comp <= 8)
    add('버튼 행정', f'{stroke:.1f} mm (레버 {P["SWING"]:.0f}° = 36° + 틈 2° + 넘침 2°)', '8 ~ 14 mm', 8 <= stroke <= 14)
    return out

def define(parts):
    names = list(parts)
    st = {'00 정지': state(names, 0, 0),
          '47 정지': state(names, 4, 7),
          '09 누름 끝(→10)': state(names, 0, 9, press=1.0),
          '99 누름 끝(→00)': state(names, 9, 9, press=1.0),
          '분리': state(names, 4, 7, explode=1.0)}
    pairs = []
    def pr(a, b, **o): pairs.append([a, b, o])
    for dn in ('tens', 'ones'):
        segs = G.SEGS
        for s in segs:
            pr('front', f'rib_{dn}_{s}', min_gap=0.3); pr('mid', f'sh_{dn}_{s}', min_gap=0.3); pr('mid', f'stem_{dn}_{s}', min_gap=0.25)
            pr(f'stem_{dn}_{s}', f'disc_{dn}_{s}', contact=True)
            order = sorted(segs, key=lambda q: P['RING_X'][q]); i = order.index(s)
            for j in (i - 1, i + 1):
                if 0 <= j < len(order): pr(f'stem_{dn}_{s}', f'disc_{dn}_{order[j]}', min_gap=0.3)
            pr(f'disc_{dn}_{s}', 'mid', min_gap=0.5)
        for i, s in enumerate(segs):
            for s2 in segs[i + 1:]: pr(f'sh_{dn}_{s}', f'sh_{dn}_{s2}', min_gap=0.3)
    for s in 'bc': pr(f'sh_tens_{s}', f'sh_ones_{"f" if s == "b" else "e"}', min_gap=0.3)
    pr('lever', 'disc_ones_f', min_gap=0.5); pr('lever', 'core_tens', contact=True); pr('lever', 'housing', min_gap=0.5)
    pr('lever', 'plunger', contact=True); pr('lever', 'spring', min_gap=0.3)
    pr('plunger', 'disc_ones_f', min_gap=0.5); pr('plunger', 'lid', contact=True); pr('plunger', 'spring', contact=True); pr('plunger', 'housing', min_gap=0.3)
    pr('cap', 'lid', contact=True)
    pr('leaf_ones', 'star_ones', contact=True); pr('leaf_tens', 'star_tens', contact=True); pr('star_ones', 'disc_ones_b', contact=True); pr('star_tens', 'disc_tens_f', contact=True); pr('leaf_shaft', 'collar_r', contact=True)
    pr('shaft', 'housing', min_gap=0.2); pr('collar_r', 'housing', min_gap=0.3); pr('collar_l', 'housing', min_gap=0.3)
    pr('collar_r', 'core_ones', min_gap=0.3); pr('collar_l', 'core_tens', min_gap=0.3); pr('core_ones', 'core_tens', min_gap=0.3)
    pr('knob', 'housing', min_gap=0.4)
    for n in ('core_ones', 'core_tens', 'lever'): pr(n, 'mid', min_gap=0.5); pr(n, 'front', min_gap=0.5)
    pr('star_ones', 'collar_r', min_gap=0.3); pr('leaf_ones', 'collar_r', min_gap=0.3); pr('leaf_shaft', 'star_ones', min_gap=0.3)
    pr('front', 'housing', contact=True); pr('mid', 'housing', contact=True); pr('lid', 'housing', contact=True)
    pr('lid', 'front', contact=True); pr('lid', 'mid', contact=True)
    # 작동 GIF 프레임: 08 → 누름 → 09 → 누름(올림) → 10 … 99 → 00, 리셋 노브 한 바퀴
    fr = {}
    for v in (8, 9, 19, 99):
        t, o = divmod(v, 10)
        for p_ in (0.0, 0.35, 0.7, 1.0, 0.5):
            fr[f'{v:02d} 누름 {int(p_ * 100)}%'] = state(names, t, o, press=p_)
    fr['47 리셋 전'] = state(names, 4, 7)
    for a in (-60, -120, -180, -240, -300, -360):
        fr[f'리셋 노브 {abs(a)}°'] = reset_state(names, 4, 7, a)
    # 휘는 부품이 '안 휘어야 하는' 상태에서 실제 메시 교집합 0 인지(강체 쌍에서 뺀 것의 근거)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'tools'))
    from pipeline import inter, tf
    ck = checks()
    for lab, (t_, o_), a_, b_ in [('09 정지: P2 가 마스크 홈에 떨어짐(레버∩일의 자리 코어)', (0, 9), 'lever', 'core_ones'),
                                  ('00 정지: 일의 자리 키가 축 홈 안(코어∩축)', (0, 0), 'core_ones', 'shaft'),
                                  ('00 정지: 십의 자리 키가 축 홈 안(코어∩축)', (0, 0), 'core_tens', 'shaft')]:
        Ms = state([a_, b_], t_, o_); v_ = inter(tf(parts[a_], Ms[a_]), tf(parts[b_], Ms[b_]))
        ck.append({'name': lab, 'value': f'교집합 {v_:.2f} mm³', 'need': '0', 'ok': 0 <= v_ <= 0.01})
    Ms = state(['lever', 'core_ones'], 0, 0); v_ = inter(tf(parts['lever'], Ms['lever']), tf(parts['core_ones'], Ms['core_ones']))
    ck.append({'name': '00 정지: P2 는 마스크 테 위(공칭 모양과 겹침 = 판스프링 휨, 0 보다 커야 함)', 'value': f'{v_:.2f} mm³', 'need': '> 0', 'ok': v_ > 1.0})
    return {'states': st, 'pairs': pairs, 'checks': ck, 'frames': fr,
            'notes': ['판스프링 폴(P1·P2)·리셋 키·멈춤쇠는 공칭(안 휜) 모양이라 강체 교집합에서 제외하고 checks(2D 운동학·변형률)로 판정했다: lever↔core_ones, core_*↔shaft.',
                      '스프링은 z 방향 균일 압축 근사(실제는 지그재그 줄이 휜다).',
                      '셔터·스템은 무게로 내려온다(스프링 없음) — 팔로워 1 g 안팎이라 끼임 마찰에 민감: 시험편 확인 필요.']}

def reset_state(names, tens, ones, shaft_deg):
    """리셋 노브를 shaft_deg(음수=시계방향, 셀 때와 같은 방향)만큼: 축 홈이 각 드럼 키를 만나면 그 드럼을 끌고 감."""
    def drum(d): return min(-36.0 * d, shaft_deg)     # 홈(축 90°+shaft)이 키(90°-36d)에 닿는 축 각 = -36d, 그 뒤로 함께 돈다
    t_ang, o_ang = drum(tens), drum(ones)
    M = state(names, tens, ones)
    for n in names:
        k = META[n]['kind']
        if k.startswith('drum:'): M[n] = rotx(t_ang if k.endswith('tens') else o_ang)
        elif k.startswith('fol:'):
            _, dn, s = k.split(':'); M[n] = T([0, 0, follower_dz(s, t_ang if dn == 'tens' else o_ang)])
        elif k == 'shaft': M[n] = rotx(shaft_deg)
    return M
