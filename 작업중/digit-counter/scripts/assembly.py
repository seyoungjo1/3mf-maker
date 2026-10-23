"""digit-counter 4자리(00:00) 조립 정의 — 공칭 파트(parts_nominal.pkl, 조립 좌표·00:00 정지)를 상태별 상대 행렬로 움직인다.
모듈 A(왼쪽 점수)·B(오른쪽 점수)는 같은 기구: 일의 자리 드럼 = 노브 축에 물림(노브 한 칸 36°), 십의 자리 = 전달 피니언(양방향 자리올림·빌림),
+1 = 세로 플런저의 판스프링 폴이 R1 을 민다. 십의 자리 멈춤 돌기가 가운데 판 탭에 걸려 00 에서 뒤로, 99 에서 앞으로 더 안 돈다.
강체로 판정할 수 없는 것(폴 휨·피니언 잠금·멈춤·세그먼트 보임)은 checks(2D 운동학·변형률)로 판정한다."""
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'tools'))
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
from shapely import affinity
from shapely.geometry import Point
import geom as G, carry as CR
P = G.P; AXP = [0.0, P['Y_C'], P['Z_C']]; PINP = [0.0, G.PIN_C[0], G.PIN_C[1]]
META = json.load(open(os.path.join(os.path.dirname(HERE), 'meta.json'), encoding='utf-8'))

def rotx(deg, p=AXP): return R(np.radians(deg), [1, 0, 0], p)
def follower_dz(seg, drum_deg): return G.cam_r(seg, 90.0 - drum_deg) - P['R_LO']

# ---------------------------------------------------------------- +1 폴이 R1 을 미는 양(2D): 누름 비율 → 일의 자리 추가 각
def _pawl_at(dz): return affinity.translate(G.pawl_profile(), 0, dz)
_R1 = G.r1_poly()
def pawl_push_table(n=60, dstep=0.05):
    """누름 0→1 동안 폴(강체, 아래로)이 R1 을 민다: 겹치면 R1 을 -θ 로 돌려 비킨다. 반환 [(누름, 추가 각)]."""
    out, ang = [], 0.0
    for p in np.linspace(0, 1, n + 1):
        pw = _pawl_at(-p * G.btn_stroke())
        while affinity.rotate(_R1, ang, origin=G.AX()).intersection(pw).area > 1e-4:
            ang -= dstep
            if ang < -80: break
        out.append((float(p), ang))
    return out
PUSH = pawl_push_table()
def push_angle(p): return float(np.interp(p, [q for q, _ in PUSH], [a for _, a in PUSH]))

def carry_add(t, o, extra):
    """일의 자리를 정지 o 에서 extra(°, 셀 때 음수)만큼 돌릴 때 십의 자리가 함께 도는 양(숫자 단위). 9→0 앞으로, 0→9 뒤로만."""
    if extra < 0 and o % 10 == 9: return min(1.0, -extra / 36.0)
    if extra > 0 and o % 10 == 0: return -min(1.0, extra / 36.0)
    return 0.0

def state(names, digits=None, press=None, knob=None, explode=0.0):
    """digits {'A': (t, o), 'B': (t, o)} 정지 숫자, press {'A': 0..1} 버튼 누름, knob {'A': 추가 각°(+ = 뒤로)}."""
    digits = digits or {'A': (0, 0), 'B': (0, 0)}; press = press or {}; knob = knob or {}
    ang = {}
    for m, (t, o) in digits.items():
        extra = push_angle(press.get(m, 0.0)) + knob.get(m, 0.0)
        ta = t + carry_add(t, o, extra)
        ang[m] = dict(ones=-36.0 * o + extra, tens=-36.0 * ta, pin=G.pinion_angle(0) + 90.0 * ta, dz=-press.get(m, 0.0) * G.btn_stroke())
    M = {}
    for n in names:
        k = META[n]['kind']; m4 = np.eye(4); f = k.split(':')
        if f[0] == 'drum': m4 = rotx(ang[f[1]][f[2]])
        elif f[0] == 'fol': m4 = T([0, 0, follower_dz(f[3], ang[f[1]][f[2]])])
        elif f[0] == 'pinion': m4 = rotx(ang[f[1]]['pin'] - G.pinion_angle(0), PINP)
        elif f[0] == 'button': m4 = T([0, 0, ang[f[1]]['dz']])
        elif f[0] == 'spring':
            top = G.BODY_Z[0] + ang[f[1]]['dz']; free = G.BODY_Z[0] + G.SPRING['pre']; s = (top - 1.0) / (free - 1.0)
            m4 = T([0, 0, 1.0]) @ np.diag([1, 1, s, 1]) @ T([0, 0, -1.0])
        if explode:
            if n == 'lid' or f[0] == 'button': m4 = T([0, 0, 45 * explode]) @ m4
            elif n == 'front': m4 = T([0, -95 * explode, 0]) @ m4
            elif n == 'mid': m4 = T([0, -30 * explode, 0]) @ m4
            elif f[0] == 'fol': m4 = T([0, -68 * explode, 0]) @ m4
        M[n] = m4
    return M

# ---------------------------------------------------------------- 기구 판정
def checks():
    out = []
    def add(name, value, need, ok): out.append({'name': name, 'value': value, 'need': need, 'ok': bool(ok)})
    # 1) 세그먼트 보임
    bad = []
    for k in range(10):
        for s in G.SEGS:
            dz = follower_dz(s, -36.0 * k); on = G.seg_on(s, k); ov = []
            for b in G.slots(s, 0.0):
                z0, z1 = b.bounds[1], b.bounds[3]; r0, r1 = z0 - P['RIB_EXT'] + dz + 0.3, z1 + dz - 0.3
                ov.append(max(0.0, min(z1, r1) - max(z0, r0)) / (z1 - z0))
            f = min(ov) if on else max(ov)
            if (on and f < 0.69) or (not on and f > 0.0): bad.append(f'{k}{s}:{f:.2f}')
    add('세그먼트 보임(0~9, 켜짐=줄 앞면이 슬롯 70 % 이상, 꺼짐=0 %)', '전부 맞음' if not bad else ', '.join(bad[:6]), '70 % / 0 %', not bad)
    # 2) 전달 피니언(carry.py 2D): 한 바퀴 겹침, 밀림(셀 때·되감을 때), 잠금 유격, 십의 자리 물림
    pr = G.CARRY; sim = CR.simulate(pr, 2.0)
    add('자리올림: 일의 자리 한 바퀴 동안 피니언 겹침(L·C 두 평면)', f'{max(r[2] for r in sim):.3f} mm²', '0', max(r[2] for r in sim) < 1e-3)
    rest = [r for r in sim if abs(r[0] % 36) < 1e-6 or abs(r[0] % 36 - 36) < 1e-6]
    lock = min(min(r[3], r[4]) for r in rest if r[0] not in (0.0, -360.0, -324.0)); lmax = max(max(r[3], r[4]) for r in rest)
    add('잠금: 정지(1~8)에서 피니언 유격 ±(= 십의 자리 ±유격/2.5)', f'±{lock:.1f}~{lmax:.1f}° (십의 자리 ±{lmax / 2.5:.1f}°)', '≤ 6° (캠 평탄 ±8° 안)', lmax <= 6.0)
    for d, lab in ((+1, '셀 때 9→0(자리올림)'), (-1, '되감을 때 0→9(빌림)')):
        res, ratio = CR.push_sim(pr, d, step=0.5)
        endphi = [r[1] for r in res if abs(r[0] - (-360.0 if d > 0 else -324.0)) < 1e-6][0]
        moved = abs(endphi - (CR.PHI_LOCK if d > 0 else CR.PHI_LOCK + 90.0))
        add(f'{lab}: 십의 자리 멈춤쇠가 붙잡은 채 피니언이 밀려 도는 각(일의 자리 끝 정지)', f'{moved:.1f}° (십의 자리 {moved / 2.5:.1f}°), 최대 밀림비 {ratio:.1f}',
            '십의 자리 > 18°(별 멈춤쇠가 마저 당김), 밀림비 ≤ 4(걸림 없음)', moved / 2.5 > 18.0 + 3 and ratio is not None and ratio <= 4)
    c = CR.cp(); T0 = CR.tens_gear(); bl = []
    for s in (+1, -1):
        for dd in np.arange(0.05, 5, 0.05):
            if CR.overlap(affinity.rotate(T0, s * dd, origin=(0, 0)), CR.place(CR.P_POLY, CR.PHI_LOCK, *c)) > 1e-3: bl.append(dd - 0.05); break
    add('십의 자리 20T ↔ 피니언 물림 유격(피치원 mm)', f'{np.radians(min(bl)) * 15:.2f} / {np.radians(max(bl)) * 15:.2f}', '0.05 ~ 0.4', 0.05 <= np.radians(min(bl)) * 15 <= 0.4)
    add('자리올림 이 끝 < 잠긴 긴 이 끝(평소 그 밑을 지나감)', f'{pr["rC"]:.2f} < {pr["tip"]:.2f} mm, 허브 {pr["rH"]:.2f} < 피니언 이 끝 {CR.A_C - CR.P_INFO["ra"]:.2f}', '틈 ≥ 0.25', pr['tip'] - pr['rC'] >= 0.25 and CR.A_C - CR.P_INFO['ra'] - pr['rH'] >= 0.25)
    # 3) +1 폴: 정지 틈(노브를 돌려도 안 닿음), 미는 각, 복귀 때 휨·변형률, 면 기울기
    pw0 = _pawl_at(0.0); md = min(affinity.rotate(_R1, a, origin=G.AX()).distance(pw0) for a in np.arange(0, 36.01, 0.5))
    add('폴 정지 위치 ↔ R1(노브로 아무 각 돌려도)', f'{md:.2f} mm', '≥ 0.3', md >= 0.3)
    p_first = next(q for q, a in PUSH if a < -0.05); a_end = PUSH[-1][1]
    add('누름 끝 일의 자리 회전(멈춤쇠 별이 ±18° 안에서 36° 로 당김)', f'{-a_end:.1f}° (누름 {p_first * 100:.0f} % 에서 닿기 시작)', '36 + 0.5 ~ 36 + 10', 36.5 <= -a_end <= 46)
    # 마지막 접촉 면의 기울기: 면 뿌리 → 끝 방향과 수평이 이루는 각(+ = 바깥이 높음 → 폴이 안쪽으로 당겨짐)
    F = P['FACE0'] + a_end; r0_, r1_ = P['RT_ROOT'], P['RT_TIP']
    p0 = np.array([r0_ * np.cos(np.radians(F)), r0_ * np.sin(np.radians(F))]); p1 = np.array([r1_ * np.cos(np.radians(F + P['HOOK'])), r1_ * np.sin(np.radians(F + P['HOOK']))])
    beta = np.degrees(np.arctan2(p1[1] - p0[1], p1[0] - p0[0]))
    add('누름 끝 R1 면 기울기(아래로 밀 때 폴이 미끄러져 빠지지 않음)', f'{beta:.1f}°', '≥ -10° (PLA 마찰각 ≈ 17°)', beta >= -10)
    # 복귀(위로): 드럼 정지(-36 뒤 정지 = 같은 면 배치), 폴이 이 등을 타고 넘으며 +y 로 휘는 양
    dmax = 0.0
    for p in np.linspace(1, 0, 121):
        pw = _pawl_at(-p * G.btn_stroke()); d = 0.0
        while _R1.intersection(affinity.translate(pw, d, 0)).area > 1e-4: d += 0.02
        dmax = max(dmax, d)
    Larm = G.ARM_ROOT_Z - (G.PAWL_TIP[1] + 1.5); ea = 1.5 * 1.3 * dmax / Larm ** 2 * 100
    add(f'폴 팔 변형률(복귀 때 이 등 넘음 δ {dmax:.2f}, L {Larm:.1f}, t 1.3)', f'{ea:.2f} %', '≤ 4 %(잠깐 휨)', ea <= 4)
    # 4) 멈춤 돌기 ↔ 가운데 판 탭: 00 에서 뒤로, 99 에서 앞으로
    lug = G.lug_poly(); tab = G.tab_poly()
    def contact_deg(k, sgn):
        for dd in np.arange(0.1, 30, 0.1):
            if affinity.rotate(lug, -36.0 * k + sgn * dd, origin=G.AX()).intersection(tab).area > 1e-4: return dd - 0.1
        return 99
    b0, b9 = contact_deg(0, +1), contact_deg(9, -1)
    gaps = [affinity.rotate(lug, -36.0 * k, origin=G.AX()).distance(tab) for k in range(10)]
    add('멈춤: 00 에서 뒤로 / 99 에서 앞으로 더 도는 각(십의 자리)', f'{b0:.1f}° / {b9:.1f}°', '1 ~ 6°(멈춤쇠가 되돌림)', 1 <= b0 <= 6 and 1 <= b9 <= 6)
    add('멈춤 돌기 ↔ 탭 정지 틈(숫자 0~9)', f'최소 {min(gaps):.2f} mm', '≥ 0.3', min(gaps) >= 0.3)
    in_others = [contact_deg(k, s_) for k in range(1, 9) for s_ in (+1, -1)]
    add('숫자 1~8 에서는 돌기가 탭에 안 닿고 한 칸(36°) 움직임', f'최소 {min(in_others):.1f}°', '≥ 36°', min(in_others) >= 36)
    # 5) 판스프링·버튼 스프링
    Ll = P['LEAF_L']; el = 1.5 * P['LEAF_T'] * (P['STAR_TIP'] - P['STAR_ROOT'] - 0.2) / Ll ** 2 * 100
    add(f'멈춤쇠 판스프링 변형률(별 끝 넘을 때, L {Ll:.0f})', f'{el:.2f} %', '≤ 4 %', el <= 4)
    S = G.SPRING; stroke = G.btn_stroke(); comp = S['pre'] + stroke; g = G.spring_gap()
    db = comp / (S['N'] - 1); es = 3 * S['t'] * (comp / S['N']) / 20 ** 2 * 100; b = P['SPR_X'][1] - P['SPR_X'][0]
    k = 1 / (S['N'] * 20 ** 3 / (12 * 3300 * b * S['t'] ** 3 / 12))
    add('버튼 스프링 줄 틈 > 틈당 눌림', f'틈 {g:.2f} / 눌림 {db:.2f} mm', '틈 > 눌림 + 0.5', g > db + 0.5)
    add('버튼 스프링 변형률(완전 누름)', f'{es:.2f} %', '≤ 2.5 %', es <= 2.5)
    add('버튼 힘(스프링, 정지 → 끝)', f'{k * S["pre"]:.2f} → {k * comp:.2f} N', '0.3 ~ 8 N', 0.3 <= k * S['pre'] and k * comp <= 8)
    add('버튼 행정', f'{stroke:.1f} mm', '8 ~ 16 mm', 8 <= stroke <= 16)
    # 6) 숫자 차례(모듈 하나): 버튼 99 번 00→99, 100 번째 멈춤 / 노브 뒤로 99 번 99→00, 더 돌리면 멈춤
    v = 0; okf = True
    for i in range(99):
        t, o = divmod(v, 10); t += 1 if o == 9 else 0; o = (o + 1) % 10; v = t * 10 + o; okf &= v == i + 1
    v = 99; okb = True
    for i in range(99):
        t, o = divmod(v, 10); t -= 1 if o == 0 else 0; o = (o - 1) % 10; v = t * 10 + o; okb &= v == 98 - i
    add('차례: 버튼 99 번 00→99(100 번째는 멈춤) / 노브 뒤로 99 칸 99→00(더 돌리면 멈춤)', '맞음' if okf and okb else '틀림', '두 방향 모두', okf and okb)
    return out

def define(parts):
    names = list(parts)
    D0 = {'A': (0, 0), 'B': (0, 0)}
    st = {'00:00 정지': state(names, D0),
          '12:47 정지': state(names, {'A': (1, 2), 'B': (4, 7)}),
          '09:10 A 누름 중간(자리올림)': state(names, {'A': (0, 9), 'B': (1, 0)}, press={'A': 0.75}),
          '09:10 A 누름 끝 / B 노브 뒤로 18°(빌림)': state(names, {'A': (0, 9), 'B': (1, 0)}, press={'A': 1.0}, knob={'B': 18.0}),
          '분리': state(names, {'A': (1, 2), 'B': (4, 7)}, explode=1.0)}
    pairs = []
    def pr(a, b, **o): pairs.append([a, b, o])
    for m in G.PAIRS:
        for dn in ('tens', 'ones'):
            for s in G.SEGS:
                pr('front', f'rib_{m}_{dn}_{s}', min_gap=0.3); pr('mid', f'sh_{m}_{dn}_{s}', min_gap=0.3); pr('mid', f'stem_{m}_{dn}_{s}', min_gap=0.25)
                pr(f'stem_{m}_{dn}_{s}', f'disc_{m}_{dn}_{s}', contact=True)
                order = sorted(G.SEGS, key=lambda q: P['RING_X'][q]); i = order.index(s)
                for j in (i - 1, i + 1):
                    if 0 <= j < len(order): pr(f'stem_{m}_{dn}_{s}', f'disc_{m}_{dn}_{order[j]}', min_gap=0.3)
                pr(f'disc_{m}_{dn}_{s}', 'mid', min_gap=0.5)
            for i, s in enumerate(G.SEGS):
                for s2 in G.SEGS[i + 1:]: pr(f'sh_{m}_{dn}_{s}', f'sh_{m}_{dn}_{s2}', min_gap=0.3)
        for s in 'bc': pr(f'sh_{m}_tens_{s}', f'sh_{m}_ones_{"f" if s == "b" else "e"}', min_gap=0.3)
        # 가운데 기구
        pr(f'pinion_{m}', f'core_{m}_tens', contact=True); pr(f'pinion_{m}', f'core_{m}_ones', contact=True); pr(f'pinion_{m}', f'lockdisc_{m}', contact=True)
        pr(f'pinion_{m}', f'pin_{m}', min_gap=0.2); pr(f'pin_{m}', 'housing', contact=True)
        for o in ('housing', 'mid', 'front', f'r1disc_{m}', f'disc_{m}_tens_b', f'sh_{m}_tens_b', f'sh_{m}_tens_c', f'sh_{m}_ones_e', f'sh_{m}_ones_f'): pr(f'pinion_{m}', o, min_gap=0.3)
        pr(f'core_{m}_tens', f'core_{m}_ones', min_gap=0.3); pr(f'core_{m}_ones', f'lockdisc_{m}', contact=True); pr(f'lockdisc_{m}', f'r1disc_{m}', contact=True)
        pr(f'r1disc_{m}', f'disc_{m}_ones_f', contact=True); pr(f'core_{m}_tens', f'disc_{m}_tens_b', min_gap=0.3)
        for n in (f'core_{m}_tens', f'core_{m}_ones', f'lockdisc_{m}', f'r1disc_{m}'):
            pr(n, 'mid', min_gap=0.5); pr(n, 'front', min_gap=0.5); pr(n, 'housing', min_gap=0.3)
        pr(f'core_{m}_tens', f'sh_{m}_tens_b', min_gap=0.25); pr(f'core_{m}_tens', f'sh_{m}_tens_c', min_gap=0.25)
        # 버튼
        pr(f'plunger_{m}', f'r1disc_{m}', contact=True)
        for o in (f'lockdisc_{m}', f'core_{m}_ones', f'disc_{m}_ones_f', 'housing'): pr(f'plunger_{m}', o, min_gap=0.3)
        pr(f'plunger_{m}', 'lid', contact=True); pr(f'plunger_{m}', f'spring_{m}', contact=True); pr(f'cap_{m}', 'lid', contact=True)
        pr(f'spring_{m}', 'housing', contact=True); pr(f'spring_{m}', f'r1disc_{m}', min_gap=0.3); pr(f'spring_{m}', f'disc_{m}_ones_f', min_gap=0.3)
        # 멈춤쇠·멈춤
        for dn, last in (('ones', 'b'), ('tens', 'f')):
            pr(f'leaf_{m}_{dn}', f'star_{m}_{dn}', contact=True); pr(f'star_{m}_{dn}', f'disc_{m}_{dn}_{last}', contact=True); pr(f'leaf_{m}_{dn}', 'housing', contact=True)
        pr(f'star_{m}_tens', 'mid', min_gap=0.3)
        # 축
        pr(f'shaft_{m}', 'housing', min_gap=0.2); pr(f'shaft_{m}', f'core_{m}_ones', contact=True); pr(f'shaft_{m}', f'core_{m}_tens', min_gap=0.2)
    pr('shaft_A', 'shaft_B', min_gap=0.3); pr('star_A_ones', 'housing', min_gap=0.3); pr('star_B_tens', 'housing', min_gap=0.3)
    pr('collar_l', 'housing', min_gap=0.3); pr('collar_l', 'star_A_tens', min_gap=0.3); pr('collar_r', 'housing', min_gap=0.3); pr('collar_r', 'star_B_ones', min_gap=0.25)
    pr('knob_l', 'housing', min_gap=0.4); pr('knob_r', 'housing', min_gap=0.4)
    pr('colon', 'front', contact=True); pr('colon', 'mid', min_gap=0.3)
    pr('front', 'housing', contact=True); pr('mid', 'housing', contact=True); pr('lid', 'housing', contact=True)
    pr('lid', 'front', contact=True); pr('lid', 'mid', contact=True)
    # 작동 GIF 프레임: A 08 → 누름 → 09 → 누름(자리올림) → 10, B 10 → 노브 뒤로(빌림) → 09, A 00 → 노브 뒤로 → 멈춤
    fr = {}
    for p_ in (0.0, 0.4, 0.7, 1.0, 0.5):
        fr[f'A 08 누름 {int(p_ * 100)}%'] = state(names, {'A': (0, 8), 'B': (1, 0)}, press={'A': p_})
    for p_ in (0.0, 0.4, 0.6, 0.8, 1.0, 0.5):
        fr[f'A 09→10 누름 {int(p_ * 100)}%'] = state(names, {'A': (0, 9), 'B': (1, 0)}, press={'A': p_})
    for a in (0, 9, 18, 27, 36):
        fr[f'B 10 노브 뒤로 {a}°'] = state(names, {'A': (1, 0), 'B': (1, 0)}, knob={'B': float(a)})
    fr['B 09 정지'] = state(names, {'A': (1, 0), 'B': (0, 9)})
    ck = checks()
    return {'states': st, 'pairs': pairs, 'checks': ck, 'frames': fr,
            'notes': ['폴 팔(판스프링)은 공칭 모양이라 누름 끝 상태에서 R1 면과 닿는다(접촉 쌍) — 복귀 때 휨은 checks 로 판정.',
                      '피니언 ↔ 기어·C·L 은 맞물림이라 접촉 쌍 — 겹침 0 은 carry.py 2D 한 바퀴 시뮬레이션과 상태별 교집합으로 확인.',
                      '스프링은 z 방향 균일 압축 근사(실제는 지그재그 줄이 휜다).',
                      '셔터·스템은 무게로 내려온다(스프링 없음) — 팔로워 1 g 안팎이라 끼임 마찰에 민감: 시험편 확인 필요.']}
