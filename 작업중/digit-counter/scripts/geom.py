"""기계식 7세그먼트 2자리 카운터 형상 — 모든 파트를 조립 좌표(mm)로 만든다.
좌표: x 가로(중심 0, -100..100), y 깊이(앞면 0 → 뒤 +), z 높이(바닥 0 → 80). 캠축은 x 방향, 축 중심 (Y_C, Z_C).
각도 θ 는 y-z 평면에서 +y(뒤) → +z(위) 방향(= +x 축 오른손 회전). 드럼은 한 번 셀 때 -36° 돈다(윗면이 뒤로).
치수는 P 하나에서만 읽는다(README 설계 치수표와 같게)."""
import numpy as np, trimesh
from shapely.geometry import Polygon, box as sbox, Point
from shapely.ops import unary_union
from shapely import affinity

P = dict(
    W=200.0, D=61.0, H=80.0, WALL=3.0, FLOOR=3.0, LID=3.0,
    # 숫자(日) — 모듈 안 두 자리 중심 x(모듈 중심 기준), 숫자 중심 높이 z0
    DH=60.0, DW=34.0, T=8.0, CX_TENS=-24.5, CX_ONES=24.5, Z0=40.0,
    SLOT=2.0, PITCH=5.5, STROKE=3.0, SLOT_W_V=4.4, RIB_EXT=1.0, NOSE_H=3.0,
    # y 층: 앞판 / 셔터 / 가운데 판(빗)
    FP_Y0=0.6, FP_T=1.6, SH_Y0=2.6, RIB=0.6, SH_T=3.0, MP_Y0=6.0, MP_T=3.0,
    # 캠축
    Y_C=22.4, Z_C=32.0, R_LO=9.0, R_HI=12.0, DISC_T=2.8,
    RING_X={'f': -15.5, 'e': -12.0, 'a': -4.5, 'g': 0.0, 'd': 4.5, 'c': 12.0, 'b': 15.5},
    TUBE_R=7.0, TUBE_FLAT=6.0, BORE_R=3.5, CLR=0.2,
    # 모듈 가운데(십의 자리 → 일의 자리): 십의 자리 20T | 일의 자리 C(자리올림 이) | L(잠금 링) | R1(+1 래칫)
    G_X=(-7.2, -4.6), C_X=(-4.2, -2.4), L_X=(-2.4, -0.6), R1_X=(-0.6, 2.8),
    PIN_FULL=(-7.0, -2.4), PIN_LONG=(-2.4, -0.8), POST_X=((-9.2, -7.6), (-0.4, 1.0)), PIN_R=1.5,
    # R1 래칫(갈고리 면) — 면 뿌리 = FACE0 + 36k(드럼 좌표, 숫자 0 정지)
    RT_ROOT=11.8, RT_TIP=15.0, FACE0=14.0, HOOK=5.0,
    # +1 플런저 폴(세로 이동, 축 뒤 y = Y_C + PAWL_R0 선)
    PAWL_R0=13.0, PAWL_REST_H=9.0, PAWL_END_ANG=-22.0,
    PL_X=(0.0, 6.6), ARM_X=(0.0, 2.6), BAR_X=(1.2, 5.4), SPR_X=(3.0, 6.6),
    # 별(멈춤쇠)·판스프링, 십의 자리 멈춤 돌기(00 에서 더 안 돌아감)
    STAR_TIP=10.0, STAR_ROOT=8.8, STAR_T=2.0, LEAF_T=1.6, LEAF_L=14.0,
    LUG_R=(10.3, 12.5), LUG_HALF=7.0, LUG_ANG0=162.0, TAB_HZ=1.6, TAB_R=10.6,
    # 축·노브(모듈 A = 왼쪽 노브, B = 오른쪽 노브)
    HEX_V=3.2, HEX_F=2.9, HEX_FW=1.72, SHAFT_X={'A': (-108.0, -1.2), 'B': (-0.8, 108.0)}, KNOB_X=(100.5, 110.5), KNOB_R=16.0,
    POST_C_X=(-4.7, 2.7),
)
SEGS = 'abcdefg'
DIGITS = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcdfg'}
UPPER = set('abf'); LOWER = set('cde')

# ---------------------------------------------------------------- 공통 도구
def clean(poly):
    """닿기만 하는 꼭짓점·실 조각을 없앤다(압출 메시가 닫히도록)."""
    p = poly.buffer(0.005, join_style=2).buffer(-0.005, join_style=2).simplify(0.002)
    if p.geom_type != 'Polygon': p = max(p.geoms, key=lambda g: g.area)
    return p
def _ext(poly, h):
    """구멍 있는 다각형은 manifold 삼각분할로 압출(기본 earcut 은 구멍을 다리로 이어 위상이 틀어진다 — tools/efc.extrude_safe)."""
    from efc import extrude_safe
    m = extrude_safe(clean(poly), h); m.merge_vertices(); return m
def ext_x(poly, x0, x1):
    """y-z 평면 다각형(shapely, 좌표 (y,z))을 x0..x1 로 압출."""
    m = _ext(poly, x1 - x0)
    M = np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
    m.apply_transform(M); return m
def ext_y(poly, y0, y1):
    """x-z 평면 다각형(좌표 (x,z))을 y0..y1 로 압출."""
    m = _ext(poly, y1 - y0)
    M = np.array([[1, 0, 0, 0], [0, 0, -1, y1], [0, 1, 0, 0], [0, 0, 0, 1]], float)   # 회전(거울 아님)
    m.apply_transform(M); return m
def ext_z(poly, z0, z1):
    m = _ext(poly, z1 - z0); m.apply_translation([0, 0, z0]); return m
def U(ms):  return trimesh.boolean.union(ms, engine='manifold')
def SUB(a, bs): return trimesh.boolean.difference([a] + list(bs), engine='manifold')
def polar_poly(rfun, a0=0.0, a1=360.0, n=720, c=(0.0, 0.0)):
    """r(θ°) 윤곽 다각형 (y,z) — 축 중심 c."""
    th = np.linspace(a0, a1, n, endpoint=False)
    pts = [(c[0] + rfun(t) * np.cos(np.radians(t)), c[1] + rfun(t) * np.sin(np.radians(t))) for t in th]
    return Polygon(pts).buffer(0)
def annulus_sector(r0, r1, a0, a1, c, n=None):
    n = n or max(8, int(abs(a1 - a0) / 2))
    th = np.radians(np.linspace(a0, a1, n + 1))
    outer = [(c[0] + r1 * np.cos(t), c[1] + r1 * np.sin(t)) for t in th]
    inner = [(c[0] + r0 * np.cos(t), c[1] + r0 * np.sin(t)) for t in th[::-1]]
    return Polygon(outer + inner).buffer(0)
def AX(): return (P['Y_C'], P['Z_C'])
def ang_norm(t): return (t + 180.0) % 360.0 - 180.0

# ---------------------------------------------------------------- 프로파일 함수(드럼 좌표계 각도)
def seg_on(seg, k): return seg in DIGITS[k % 10]
def cam_r(seg, th):
    """캠 반지름: 숫자 k 의 구역 중심 = 90 + 36k(드럼 좌표). 평탄 ±8°, 그 사이 20° 코사인 경사.
    켜짐 = 낮음(셔터 아래, 줄이 슬롯에), 꺼짐 = 높음(줄이 슬롯 위 살 뒤로 숨음 — 위에서 내려다봐도 안 비침)."""
    u = ((th - 90.0) % 360.0) / 36.0; k0 = int(np.floor(u)); f = (u - k0) * 36.0
    v0, v1 = 1.0 - float(seg_on(seg, k0)), 1.0 - float(seg_on(seg, k0 + 1))
    if f <= 8: v = v0
    elif f >= 28: v = v1
    else: s = (f - 8) / 20.0; v = v0 + (v1 - v0) * (1 - np.cos(np.pi * s)) / 2
    return P['R_LO'] + (P['R_HI'] - P['R_LO']) * v
def r1_poly(c=None):
    """R1 래칫(10 이, 갈고리 면): 면 뿌리(RT_ROOT, F) → 면 끝(RT_TIP, F + HOOK) 이 +θ 로 기울어 폴을 안쪽으로 당긴다.
    이 등은 뿌리 F 에서 다음 면 끝(F+36+HOOK)까지 직선 상승. 드럼 좌표(숫자 0 정지)."""
    c = c or AX(); r0, r1, H = P['RT_ROOT'], P['RT_TIP'], P['HOOK']; pts = []
    for k in range(10):
        F = P['FACE0'] + 36.0 * k
        for t in np.linspace(F, F + 36.0 + H, 40):
            r = r0 + (r1 - r0) * (t - F) / (36.0 + H)
            pts.append((c[0] + r * np.cos(np.radians(t)), c[1] + r * np.sin(np.radians(t))))
    return Polygon(pts).buffer(0)
def star_r(th, center=-90.0, half=9.0):
    d = min(abs(ang_norm(th - center - 36.0 * k)) for k in range(10))
    return P['STAR_TIP'] - (P['STAR_TIP'] - P['STAR_ROOT']) * max(0.0, 1.0 - d / half)

# ---------------------------------------------------------------- 숫자: 세그먼트·슬롯·셔터·스템 (캠 낮음 = 켜짐 위치에서 만든다; 꺼짐 = +STROKE)
def seg_center(s):
    """세그먼트 중심(숫자 중심 기준 상대 x, z)과 방향."""
    h, w, c = P['DH'] / 2, P['DW'] / 2, P['T'] / 2
    return {'a': (0, h - c, 'h'), 'g': (0, 0, 'h'), 'd': (0, -h + c, 'h'),
            'b': (w - c, (h) / 2, 'v'), 'f': (-(w - c), h / 2, 'v'), 'c': (w - c, -h / 2, 'v'), 'e': (-(w - c), -h / 2, 'v')}[s]
def seg_poly(s, cx):
    """앞판에 보이는 세그먼트 윤곽(x,z) — 끝 45°."""
    h, w, t = P['DH'] / 2, P['DW'] / 2, P['T']; c = t / 2; z0 = P['Z0']
    if s in 'agd':
        z = z0 + {'a': h - c, 'g': 0.0, 'd': -h + c}[s]; x0, x1 = cx - w + 0.6 * t, cx + w - 0.6 * t
        return Polygon([(x0, z), (x0 + c, z + c), (x1 - c, z + c), (x1, z), (x1 - c, z - c), (x0 + c, z - c)])
    x = cx + (w - c if s in 'bc' else -w + c); za, zb = ((0.6 * t, h - 0.6 * t) if s in 'bf' else (-h + 0.6 * t, -0.6 * t))
    za, zb = z0 + za, z0 + zb
    return Polygon([(x, za), (x + c, za + c), (x + c, zb - c), (x, zb), (x - c, zb - c), (x - c, za + c)])
def slots(s, cx):
    """앞판 슬롯(x,z 직사각형) — 가로 세그먼트 2개, 세로 3개. 슬롯 높이 SLOT, 피치 PITCH(살 3.5)."""
    z0 = P['Z0']; S = P['SLOT']; Pt = P['PITCH']
    if s in 'agd':
        zc = z0 + seg_center(s)[1]; L = 12.2 - (Pt + S) / 2 - 0.8
        return [sbox(cx - L, zc + o, cx + L, zc + o + S) for o in (-(Pt + S) / 2, (Pt - S) / 2)]
    xc = cx + seg_center(s)[0]; hw = P['SLOT_W_V'] / 2
    zs = [15.0 - S / 2 + k * Pt for k in (-1, 0, 1)]
    if s in 'ce': zs = [-z - S for z in zs]
    return [sbox(xc - hw, z0 + z, xc + hw, z0 + z + S) for z in zs]
def shutter_box(s, cx):
    """셔터 판 범위(x0,x1,z0,z1) — 캠 낮음(켜짐) 위치, 꺼짐은 +STROKE."""
    sl = slots(s, cx); zmin = min(b.bounds[1] for b in sl); zmax = max(b.bounds[3] for b in sl)
    if s in 'agd': x0, x1 = cx - 9.2, cx + 9.2
    elif s in 'bc': x0, x1 = cx + 9.6, cx + 17.4
    else: x0, x1 = cx - 17.4, cx - 9.6
    return x0, x1, zmin - P['RIB_EXT'] - 1.0, zmax + P['STROKE'] + 1.0
def attach_z(s, cx):
    x0, x1, z0, z1 = shutter_box(s, cx)
    if s in UPPER: return z0 + 1.6, z0 + 7.6
    if s in LOWER: return z1 - 7.6, z1 - 1.6
    return z0 + 1.6, z1 - 1.6
FOOT_Z0 = P['Z_C'] + P['R_LO'] + P['NOSE_H']   # 발 막대 아랫면(캠 낮음) 44.0 — 코 높이 3 이면 이웃 구역 높은 캠(12·cos α)에 막대가 안 닿음
STEM_Y = (P['SH_Y0'] + P['SH_T'], P['MP_Y0'] + P['MP_T'])   # 스템 = 셔터 뒷면 ~ 가운데 판 뒷면
def stem_up(s):
    """스템 출력 방향: 장부를 셔터 바깥 모서리에서 먼 쪽으로 0.4 들이고(바닥 쪽은 평평하게), 그쪽을 위로."""
    return (-1, 0, 0) if s in 'ef' else (1, 0, 0)
def tenon_x(s, rx):
    return (rx - 0.6, rx + 1.0) if s in 'ef' else (rx - 1.0, rx + 0.6)
def stem_z(s, cx):
    a0, a1 = attach_z(s, cx)
    if s in UPPER: return FOOT_Z0, a1
    return min(a0, FOOT_Z0), FOOT_Z0 + 2.0
def shutter(s, cx):
    """셔터 = 검정 바탕 판 + 노란 줄(사다리꼴 리브, 앞면). (base, ribs) 반환. 뒷면에 스템 장부 구멍."""
    x0, x1, z0, z1 = shutter_box(s, cx); y0 = P['SH_Y0']; yb = y0 + P['RIB']; y1 = y0 + P['SH_T']
    base = ext_y(sbox(x0, z0, x1, z1), yb, y1)
    rx = cx + P['RING_X'][s]; a0, a1 = attach_z(s, cx)
    tx0, tx1 = tenon_x(s, rx)
    base = SUB(base, [ext_y(sbox(tx0 - 0.1, a0 - 0.1, tx1 + 0.1, a1 + 0.1), y1 - 1.5, y1 + 0.1)])
    ribs = []
    for b in slots(s, cx):
        bx0, bz0, bx1, bz1 = b.bounds; zb0, zb1 = bz0 - P['RIB_EXT'], bz1   # 캠 낮음(켜짐)에서 줄 = 슬롯 + 아래로 1.0(위에서 내려다봐도 노랑)
        tr = Polygon([(yb, zb0), (y0, zb0 + 0.3), (y0, zb1 - 0.3), (yb, zb1)])
        ribs.append(ext_x(tr, bx0 - 0.4, bx1 + 0.4))
    return base, U(ribs)
def stem(s, cx):
    """스템 + 발(코) — y-z 윤곽을 x 두께 2.0 으로. 장부(앞)로 셔터에 꽂는다."""
    rx = cx + P['RING_X'][s]; zl, zh = stem_z(s, cx); a0, a1 = attach_z(s, cx); yc, zc = AX()
    zn = zc + P['R_LO']                                   # 코 끝(캠 낮음) = 캠 낮은 반지름 꼭대기
    y0, y1 = STEM_Y
    prof = unary_union([
        sbox(y0, zl, y1, zh),                            # 스템(가운데 판 슬롯 안)
        sbox(y0, FOOT_Z0, yc + 2.5, FOOT_Z0 + 2.0),      # 발 막대
        sbox(yc - 1.5, zn + 1.5, yc + 1.5, FOOT_Z0 + 0.01),
        Point(yc, zn + 1.5).buffer(1.5, 32)])
    tx0, tx1 = tenon_x(s, rx)
    return U([ext_x(prof, rx - 1.0, rx + 1.0), ext_x(sbox(y0 - 1.4, a0, y0 + 0.05, a1), tx0, tx1)])   # 장부(셔터에 꽂힘)

# ---------------------------------------------------------------- 캠 디스크·코어
def d_profile(r, flat, c=None, ang=-90.0):
    """D 모양(원 r, ang 방향으로 중심에서 flat 거리에서 자름)."""
    c = c or AX(); circ = Point(c).buffer(r, 128)
    cut = affinity.rotate(sbox(flat, -50, 60, 50), ang, origin=(0, 0)); cut = affinity.translate(cut, c[0], c[1])
    return circ.difference(cut)
def disc(s, cx, ones):
    """세그먼트 캠 디스크(+보스 또는 마지막 디스크면 별). 드럼 좌표 = 조립 좌표(숫자 0 정지)."""
    rx = cx + P['RING_X'][s]; t = P['DISC_T']; c = AX()
    bore = d_profile(P['TUBE_R'] + P['CLR'], P['TUBE_FLAT'] + P['CLR'])
    prof = polar_poly(lambda th: cam_r(s, th), c=c).difference(bore)
    ms = [ext_x(prof, rx - t / 2, rx + t / 2)]
    order = sorted(P['RING_X'], key=lambda q: P['RING_X'][q], reverse=not ones)   # 코어 쪽부터
    i = order.index(s); bossprof = Point(c).buffer(8.5, 128).difference(bore)
    if i < len(order) - 1:
        nxt = cx + P['RING_X'][order[i + 1]]
        if ones: ms.append(ext_x(bossprof, rx + t / 2 - 0.01, nxt - t / 2 - 0.0))
        else: ms.append(ext_x(bossprof, nxt + t / 2, rx - t / 2 + 0.01))
    return U(ms)
def lug_poly(c=None):
    """십의 자리 멈춤 돌기(드럼 좌표, 숫자 0 정지): LUG_ANG0 ± LUG_HALF, r LUG_R. 숫자 k 에서 LUG_ANG0 - 36k."""
    c = c or AX(); r0, r1 = P['LUG_R']
    return annulus_sector(r0 - 1.5, r1, P['LUG_ANG0'] - P['LUG_HALF'], P['LUG_ANG0'] + P['LUG_HALF'], c, 28)
def star_disc(cx, ones):
    """멈춤쇠 별(10 홈) — 따로 출력해 마지막 캠 디스크 바깥에 끼운다(D 구멍).
    십의 자리는 바깥쪽에 멈춤 돌기 슬랩(별 ∪ 돌기)이 하나 더 있다: 00 에서 뒤로, 99 에서 앞으로 더 안 돈다(가운데 판 탭에 걸림)."""
    c = AX(); t = P['DISC_T']; bore = d_profile(P['TUBE_R'] + P['CLR'], P['TUBE_FLAT'] + P['CLR'])
    last = cx + P['RING_X']['b' if ones else 'f']; star = polar_poly(lambda th: star_r(th), c=c).difference(bore)
    if ones: return ext_x(star, last + t / 2, last + t / 2 + P['STAR_T'])
    x1 = last - t / 2; x0 = x1 - P['STAR_T']
    return U([ext_x(star, x0, x1), ext_x(star.union(lug_poly()).difference(bore), x0 - P['STAR_T'], x0 + 0.01)])
LUG_SLAB = (P['CX_TENS'] + P['RING_X']['f'] - P['DISC_T'] / 2 - 2 * P['STAR_T'], P['CX_TENS'] + P['RING_X']['f'] - P['DISC_T'] / 2 - P['STAR_T'])
TENS_END = LUG_SLAB[0]                                                          # 십의 자리 관 끝(-45.4)
ONES_END = P['CX_ONES'] + P['RING_X']['b'] + P['DISC_T'] / 2 + P['STAR_T']     # 일의 자리 관 끝(43.4)

# ---------------------------------------------------------------- 전달 피니언(주행거리계식 양방향 자리올림·빌림) — 2D 는 carry.py 에서 설계·검증
import carry as CR
CR.setup(); CARRY = CR.ones_profiles()
def _yz(poly): return affinity.translate(poly, P['Y_C'], P['Z_C'])
PIN_C = (P['Y_C'] + CR.cp()[0], P['Z_C'] + CR.cp()[1])                         # 피니언 축 (y, z)
def pinion_angle(tens_digit, ones_deg=None):
    """피니언 각(°): 십의 자리 k 정지 = PHI_LOCK + 90k. ones_deg(일의 자리 드럼 각)를 주면 자리올림 구간 법칙."""
    base = CR.PHI_LOCK + 90.0 * tens_digit
    if ones_deg is None: return base
    return base + CR.phi_of(ones_deg) - CR.PHI_LOCK
def hex_profile(off=0.0, c=None):
    c = c or AX(); v, f, fw = P['HEX_V'] + off, P['HEX_F'] + off, P['HEX_FW'] + off * 0.5
    return Polygon([(c[0] + x, c[1] + z) for x, z in [(v, 0), (fw, f), (-fw, f), (-v, 0), (-fw, -f), (fw, -f)]])
def core(ones):
    """일의 자리 코어: C(자리올림 이 2개 + 허브) + D 관(육각 구멍 = 노브 축에 물림). 십의 자리 코어: 20T 기어 + 보스 + D 관(둥근 구멍, 축 위에서 자유)."""
    c = AX(); tube = d_profile(P['TUBE_R'], P['TUBE_FLAT'])
    if ones:
        bore = hex_profile(0.15)
        return U([ext_x(_yz(CARRY['C']).difference(bore), *P['C_X']), ext_x(tube.difference(bore), P['C_X'][1] - 0.01, ONES_END)])
    bore = Point(c).buffer(P['BORE_R'], 64)
    gear = _yz(CR.tens_gear()).difference(bore)
    return U([ext_x(gear, *P['G_X']), ext_x(Point(c).buffer(8.5, 128).difference(bore), P['G_X'][0] - 0.4, P['G_X'][0] + 0.01),
              ext_x(tube.difference(bore), TENS_END, P['G_X'][0] - 0.39)])
def lock_disc():
    """일의 자리 L(잠금 링 r_L + 홈) — 따로 납작하게 출력해 D 관에 끼운다(C 와 한 몸이면 어느 쪽을 아래로 해도 오버행)."""
    bore = d_profile(P['TUBE_R'] + P['CLR'], P['TUBE_FLAT'] + P['CLR'])
    return ext_x(_yz(CARRY['L']).difference(bore), *P['L_X'])
def r1_disc():
    """R1 래칫 + 첫 캠 디스크(f)까지 보스(간격 링)."""
    c = AX(); bore = d_profile(P['TUBE_R'] + P['CLR'], P['TUBE_FLAT'] + P['CLR'])
    f0 = P['CX_ONES'] + P['RING_X']['f'] - P['DISC_T'] / 2
    return U([ext_x(r1_poly().difference(bore), *P['R1_X']), ext_x(Point(c).buffer(8.5, 128).difference(bore), P['R1_X'][1] - 0.01, f0)])
def pinion(tens_digit=0):
    """피니언 8T: 온 이(십의 자리 20T + 일의 자리 C) / 긴 이만(일의 자리 L). 십의 자리 숫자 0 정지 자세."""
    phi = pinion_angle(tens_digit); hole = Point(PIN_C).buffer(P['PIN_R'] + 0.25, 48)
    full = affinity.translate(CR.place(CR.P_POLY, phi), *PIN_C).difference(hole)
    long_ = affinity.translate(CR.place(CR.PL_POLY, phi), *PIN_C).difference(hole)
    return U([ext_x(full, *P['PIN_FULL']), ext_x(long_, P['PIN_FULL'][1] - 0.01, P['PIN_LONG'][1])])
def pin():
    """피니언 축 핀 Ø3(밑면 0.3 깎은 D — 눕혀 출력), 양쪽 기둥 구멍에 끼움(0.05)."""
    pr = Point(PIN_C).buffer(P['PIN_R'], 48).difference(sbox(PIN_C[0] - 5, PIN_C[1] - 5, PIN_C[0] + 5, PIN_C[1] - P['PIN_R'] + 0.3))
    return ext_x(pr, P['POST_X'][0][0], P['POST_X'][1][1])

# ---------------------------------------------------------------- +1 버튼: 플런저(세로) + 판스프링 폴, 뚜껑 밑 안내 슬리브, 지그재그 스프링
def _pt(r, a, c=None):
    c = c or AX(); return (c[0] + r * np.cos(np.radians(a)), c[1] + r * np.sin(np.radians(a)))
PAWL_TIP = (P['Y_C'] + P['PAWL_R0'], P['Z_C'] + P['PAWL_REST_H'])          # 폴 이 아래 앞 모서리(미는 점), 정지
ARM_Y = (P['Y_C'] + P['RT_TIP'] + 0.5, P['Y_C'] + P['RT_TIP'] + 1.8)      # 폴 팔(두께 1.3) — R1 끝원 뒤 0.5
BODY_Y = (ARM_Y[1] + 0.6, ARM_Y[1] + 6.2); BODY_Z = (45.0, 60.0)          # 플런저 몸통(정지): 윗면이 슬리브 밑에 닿음
BAR_Y = (BODY_Y[0] + 0.8, BODY_Y[1] - 0.8)
def btn_stroke():
    """누름 행정 = 폴 끝 정지 높이 → 마지막 면 각(PAWL_END_ANG)까지."""
    return P['PAWL_REST_H'] - P['PAWL_R0'] * np.tan(np.radians(P['PAWL_END_ANG']))
def pawl_profile():
    """폴 이(y-z): 아랫면 수평(미는 면), 앞 끝 = 폴 선(y = Y_C + R0)."""
    y0, z0 = PAWL_TIP
    return Polygon([(ARM_Y[0] + 0.05, z0), (y0, z0), (y0, z0 + 1.0), (ARM_Y[0] + 0.05, z0 + 3.0)])
ARM_ROOT_Z = BODY_Z[1] - 2.0
def plunger():
    """몸통(스프링 위) + 앞 판스프링 팔(위 다리에서 매달림, 아래 끝에 폴 이) + 막대(뚜껑 슬리브를 지나 캡)."""
    z_top = 80.0 + btn_stroke() + 4.5
    arm = unary_union([sbox(ARM_Y[0], PAWL_TIP[1], ARM_Y[1], BODY_Z[1]), sbox(ARM_Y[0], ARM_ROOT_Z, BODY_Y[0] + 0.01, BODY_Z[1]), pawl_profile()])
    return U([ext_x(sbox(BODY_Y[0], BODY_Z[0], BODY_Y[1], BODY_Z[1]), *P['PL_X']),
              ext_x(arm, *P['ARM_X']),
              ext_x(sbox(BAR_Y[0], BODY_Z[1] - 0.01, BAR_Y[1], z_top), *P['BAR_X'])])
def cap():
    """버튼 캡 Ø22×5 — 막대 끝이 4.5 깊이로 들어감. 누름 끝에서 캡이 뚜껑에 닿는다(행정 제한)."""
    cy = sum(BAR_Y) / 2; cxm = sum(P['BAR_X']) / 2; bw, bd = P['BAR_X'][1] - P['BAR_X'][0], BAR_Y[1] - BAR_Y[0]
    disk = trimesh.creation.cylinder(radius=11.0, height=5.0, sections=96); disk.apply_translation([cxm, cy, 2.5])
    sock = trimesh.creation.box(extents=[bw + 0.3, bd + 0.3, 4.6]); sock.apply_translation([cxm, cy, 2.3 - 0.01])
    m = SUB(disk, [sock]); m.apply_translation([0, 0, 80.0 + btn_stroke()]); return m
SPRING = dict(N=8, t=1.3, y0=BODY_Y[0] - 2.4, y1=BODY_Y[0] - 2.4 + 20.0, pre=1.2)
def spring(top_z=None):
    """지그재그 판스프링(SPR_X 슬랩, 바닥 홈에 꽂음). 자유 높이 = 몸통 밑 + 예압. top_z 를 주면 z 로 눌러 그린다(조립 확인용 근사)."""
    S = SPRING; free_top = BODY_Z[0] + S['pre']; N, t, y0, y1 = S['N'], S['t'], S['y0'], S['y1']
    z_beam0, z_beam1 = 3.0, free_top - 1.5; g = (z_beam1 - z_beam0 - N * t) / (N - 1)
    parts = [sbox(y0, 1.0, y1, 3.0 + 0.01), sbox(BODY_Y[0] + 0.2, z_beam1 - 1.0, BODY_Y[1] - 0.2, free_top)]
    for i in range(N):
        zb = z_beam0 + i * (t + g); parts.append(sbox(y0, zb, y1, zb + t))
        if i < N - 1:
            if i % 2 == 0: parts.append(sbox(y1 - 1.6, zb + t - 0.01, y1, zb + t + g + 0.01))
            else: parts.append(sbox(y0, zb + t - 0.01, y0 + 1.6, zb + t + g + 0.01))
    m = ext_x(unary_union(parts), *P['SPR_X'])
    if top_z is not None:
        s = (top_z - 1.0) / (free_top - 1.0); m.apply_translation([0, 0, -1.0]); m.apply_scale([1, 1, s]); m.apply_translation([0, 0, 1.0])
    return m
def spring_gap(): S = SPRING; return ((BODY_Z[0] + S['pre'] - 1.5) - 3.0 - S['N'] * S['t']) / (S['N'] - 1)

# ---------------------------------------------------------------- 4자리 00:00 — 같은 모듈 두 벌(A 왼쪽 = 왼쪽 노브, B 오른쪽 = 오른쪽 노브)
PAIRS = {'A': -48.5, 'B': 48.5}        # 모듈 중심 — 숫자 블록 -90.5~90.5, 여백 10, 콜론 칸 14
MOD_LEAF = {'ones': (41.6, 43.2), 'tens': (-43.2, -41.6)}     # 모듈 기준 별 멈춤쇠 판스프링 슬랩
def digit_cxs():
    return {(m, dn): c + (P['CX_TENS'] if dn == 'tens' else P['CX_ONES']) for m, c in PAIRS.items() for dn in ('tens', 'ones')}
def moved(mesh, dx): mesh.apply_translation([dx, 0, 0]); return mesh

# ---------------------------------------------------------------- 별 멈춤쇠 판스프링, 축·칼라·노브
def leaf(slab):
    yc, zc = AX(); top = zc - P['STAR_ROOT'] - 0.3 - 1.0; post_y = yc + P['LEAF_L']
    prof = unary_union([sbox(post_y, 1.0, post_y + 3.0, top), sbox(yc - 1.5, top - P['LEAF_T'], post_y + 0.01, top),
                        Polygon([(yc - 1.2, top - 0.01), (yc, top + 1.0), (yc + 1.2, top - 0.01)])])
    return ext_x(prof, *slab)
def shaft(m):
    return ext_x(hex_profile(), *P['SHAFT_X'][m])
def collar(side):
    """벽 안쪽 칼라(육각 구멍): l = 왼쪽 플랜지(모듈 A 십의 자리 돌기 슬랩 옆), r = 오른쪽 플랜지 + 슬리브(모듈 B 일의 자리 별까지)."""
    c = AX(); hb = hex_profile(0.15); sl = lambda r: Point(c).buffer(r, 96).difference(hb)
    if side == 'l': return ext_x(sl(10.0), -96.6, -94.4)
    b_end = PAIRS['B'] + ONES_END
    return U([ext_x(sl(10.0), 94.4, 96.6), ext_x(sl(5.5), b_end + 0.3, 94.4 + 0.01)])
def knob(side):
    """노브(육각 소켓 7.5) — r: 오른쪽 벽 밖(모듈 B), l: 왼쪽 벽 밖(모듈 A). 화살표는 바깥면."""
    c = AX(); x0, x1 = P['KNOB_X']
    grip = unary_union([Point(c).buffer(P['KNOB_R'] - 1.0, 128)] + [Point(_pt(P['KNOB_R'] - 1.0, a)).buffer(1.2, 16) for a in range(0, 360, 15)])
    arrow = Polygon([_pt(13.0, 90), _pt(9.0, 84), _pt(9.0, 96)])
    if side == 'r':
        return SUB(ext_x(grip, x0, x1), [ext_x(hex_profile(0.12), x0 - 0.1, x0 + 7.5), ext_x(arrow, x1 - 0.6, x1 + 0.01)])
    return SUB(ext_x(grip, -x1, -x0), [ext_x(hex_profile(0.12), -x0 - 7.5, -x0 + 0.1), ext_x(arrow, -x1 - 0.01, -x1 + 0.6)])

# ---------------------------------------------------------------- 콜론(:) — 앞판 슬롯 4개에 끼우는 노란 부품(앞판과 가운데 판 사이에 갇힘)
COLON_SLOTS = [sbox(-2.5, z, 2.5, z + P['SLOT']) for z in (29.0, 34.5, 43.5, 49.0)]
def colon():
    y0, y1 = P['SH_Y0'], P['SH_Y0'] + P['SH_T']
    plugs = [ext_y(b.buffer(-0.2, join_style=2), P['FP_Y0'], y0 + 0.05) for b in COLON_SLOTS]
    return U([ext_y(sbox(-4.0, 27.0, 4.0, 53.0), y0, y1)] + plugs)

# ---------------------------------------------------------------- 하우징·앞판·가운데 판·뚜껑
GROOVES = {'front': (P['FP_Y0'], P['FP_Y0'] + P['FP_T']), 'mid': (P['MP_Y0'], P['MP_Y0'] + P['MP_T'])}
PANEL_HX = 98.4
def teardrop(c, r):
    """위가 뾰족한 구멍 — 옆면 수직에서 30°(층당 0.115 이하): 접점 30°/150°, 꼭짓점 2r."""
    return unary_union([Point(c).buffer(r, 64), Polygon([(c[0] - r * 0.8660, c[1] + r * 0.5), (c[0], c[1] + 2.0 * r), (c[0] + r * 0.8660, c[1] + r * 0.5)])])
def post_profile(c, r_hole, wall):
    """바닥에서 올라온 기둥(y-z): 둘레 = 눈물방울(r_hole + wall), 아래는 바닥까지, 구멍 = 눈물방울 r_hole."""
    R = r_hole + wall
    outer = unary_union([teardrop(c, R), sbox(c[0] - R, P['FLOOR'] - 0.01, c[0] + R, c[1])])
    return outer.difference(teardrop(c, r_hole))
def housing():
    W2, D, Hw = P['W'] / 2, P['D'], 77.0
    body = [ext_z(sbox(-W2, 0, W2, D), 0, P['FLOOR']),
            ext_z(sbox(-W2, 0, -W2 + 3, D), 0, Hw), ext_z(sbox(W2 - 3, 0, W2, D), 0, Hw),
            ext_z(sbox(-W2, D - 3, W2, D), 0, Hw)]
    pp = post_profile(PIN_C, P['PIN_R'] + 0.05, 1.6)
    for c in PAIRS.values():
        for x0, x1 in P['POST_X']: body.append(ext_x(pp, c + x0, c + x1))
    body.append(ext_x(post_profile(AX(), P['HEX_V'] + 0.25, 2.5), *P['POST_C_X']))
    body = U(body)
    cuts = []
    for y0, y1 in GROOVES.values():
        for sgn in (-1, 1):
            cuts.append(ext_z(sbox(min(sgn * 96.0, sgn * (PANEL_HX + 0.2)), y0 - 0.15, max(sgn * 96.0, sgn * (PANEL_HX + 0.2)), y1 + 0.15), P['FLOOR'], Hw + 1))
    hole = teardrop(AX(), P['HEX_V'] + 0.25)
    cuts += [ext_x(hole, -W2 - 1, -W2 + 4), ext_x(hole, W2 - 4, W2 + 1)]
    py = P['Y_C'] + P['LEAF_L']
    for c in PAIRS.values():
        for x0, x1 in MOD_LEAF.values(): cuts.append(ext_z(sbox(c + x0 - 0.2, py - 0.2, c + x1 + 0.2, py + 3.2), 1.0, P['FLOOR'] + 0.1))
        S = SPRING; cuts.append(ext_z(sbox(c + P['SPR_X'][0] - 0.2, S['y0'] - 0.2, c + P['SPR_X'][1] + 0.2, S['y1'] + 0.2), 1.0, P['FLOOR'] + 0.1))
    return SUB(body, cuts)
def front_panel():
    hz0, hz1 = P['FLOOR'] + 0.2, 77.0 - 0.2
    plate = sbox(-PANEL_HX, hz0, PANEL_HX, hz1)
    holes = [b for cx in digit_cxs().values() for s in SEGS for b in slots(s, cx)] + COLON_SLOTS
    return ext_y(plate.difference(unary_union(holes)), *GROOVES['front'])
def mid_slots():
    out = []
    for cx in digit_cxs().values():
        for s in SEGS:
            rx = cx + P['RING_X'][s]; zl, zh = stem_z(s, cx)
            out.append(sbox(rx - 1.3, zl - 0.5, rx + 1.3, zh + P['STROKE'] + 0.5))
    u = unary_union(out)
    return u.buffer(0.75, join_style=2).buffer(-0.75, join_style=2)       # 1.5 mm 미만 살은 슬롯으로 합침
CORE_WIN = (P['POST_X'][0][0] - 0.4, P['R1_X'][1] + 0.4, P['FLOOR'], P['Z_C'] + 16.5 + 0.6)   # 모듈 기준: 기어·피니언·링·래칫·피니언 기둥이 지나는 창(아래가 트인 홈)
def tab_poly():
    """가운데 판 뒷면 멈춤 탭(y-z): 축 앞(180°) 쪽으로 TAB_R 까지."""
    return sbox(P['MP_Y0'] + P['MP_T'] - 0.01, P['Z_C'] - P['TAB_HZ'], P['Y_C'] - P['TAB_R'], P['Z_C'] + P['TAB_HZ'])
def mid_plate():
    """가운데 판(빗): 스템 슬롯 + 모듈마다 기어·피니언 창 + 십의 자리 멈춤 탭(뒷면)."""
    plate = sbox(-PANEL_HX, P['FLOOR'] + 0.2, PANEL_HX, 77.0 - 0.2)
    wins = [sbox(c + CORE_WIN[0], CORE_WIN[2], c + CORE_WIN[1], CORE_WIN[3]) for c in PAIRS.values()]
    cut = mid_slots().union(unary_union(wins)).buffer(0.75, join_style=2).buffer(-0.75, join_style=2)
    tabs = [ext_x(tab_poly(), c + LUG_SLAB[0] + 0.1, c + LUG_SLAB[1] - 0.1) for c in PAIRS.values()]
    return U([ext_y(plate.difference(cut), *GROOVES['mid'])] + tabs)
SLEEVE_W = 1.6
def lid():
    W2, D = P['W'] / 2, P['D']
    top = sbox(-W2, 0, W2, D); sleeves = []
    for c in PAIRS.values():
        hole = sbox(c + P['BAR_X'][0] - 0.2, BAR_Y[0] - 0.2, c + P['BAR_X'][1] + 0.2, BAR_Y[1] + 0.2)
        top = top.difference(hole)
        sleeves.append(hole.buffer(SLEEVE_W, join_style=2).difference(hole))
    lips = unary_union([sbox(-96.8, 12.0, -95.6, 56.0), sbox(95.6, 12.0, 96.8, 56.0), sbox(-90.0, 56.6, 90.0, 57.8)])
    return U([ext_z(top, 77.0, 80.0), ext_z(lips, 74.0, 77.0 + 0.01), ext_z(unary_union(sleeves), BODY_Z[1], 77.0 + 0.01)])

# ---------------------------------------------------------------- 전체 파트 표
BLACK, YELLOW, GRAY, WHITE = '#2b2e33', '#ffb300', '#9aa3ad', '#e8e8e8'
def module_parts(m, c):
    """모듈 m(A/B)의 파트 — 모듈 중심 0 에서 만들어 c 만큼 옮긴다."""
    out = {}
    for dn in ('tens', 'ones'):
        ones = dn == 'ones'; cx = P['CX_ONES'] if ones else P['CX_TENS']
        for s in SEGS:
            b, r = shutter(s, cx)
            out[f'sh_{m}_{dn}_{s}'] = (moved(b, c), BLACK, (0, -1, 0), f'fol:{m}:{dn}:{s}')
            out[f'rib_{m}_{dn}_{s}'] = (moved(r, c), YELLOW, (0, -1, 0), f'fol:{m}:{dn}:{s}')
            out[f'stem_{m}_{dn}_{s}'] = (moved(stem(s, cx), c), BLACK, stem_up(s), f'fol:{m}:{dn}:{s}')
            out[f'disc_{m}_{dn}_{s}'] = (moved(disc(s, cx, ones), c), GRAY, (1, 0, 0) if ones else (-1, 0, 0), f'drum:{m}:{dn}')
        out[f'star_{m}_{dn}'] = (moved(star_disc(cx, ones), c), GRAY, (1, 0, 0), f'drum:{m}:{dn}')
        out[f'core_{m}_{dn}'] = (moved(core(ones), c), GRAY, (1, 0, 0) if ones else (-1, 0, 0), f'drum:{m}:{dn}')
        out[f'leaf_{m}_{dn}'] = (leaf((c + MOD_LEAF[dn][0], c + MOD_LEAF[dn][1])), GRAY, (1, 0, 0), 'fixed')
    out[f'lockdisc_{m}'] = (moved(lock_disc(), c), GRAY, (1, 0, 0), f'drum:{m}:ones')
    out[f'r1disc_{m}'] = (moved(r1_disc(), c), GRAY, (-1, 0, 0), f'drum:{m}:ones')
    out[f'pinion_{m}'] = (moved(pinion(), c), YELLOW, (-1, 0, 0), f'pinion:{m}')
    out[f'pin_{m}'] = (moved(pin(), c), GRAY, (0, 0, 1), 'fixed')
    out[f'plunger_{m}'] = (moved(plunger(), c), GRAY, (1, 0, 0), f'button:{m}')
    out[f'cap_{m}'] = (moved(cap(), c), YELLOW, (0, 0, -1), f'button:{m}')
    out[f'spring_{m}'] = (moved(spring(), c), GRAY, (1, 0, 0), f'spring:{m}')
    out[f'shaft_{m}'] = (shaft(m), GRAY, (0, 0, 1), f'drum:{m}:ones')
    return out
def all_parts():
    """{이름: (메시(조립 좌표·정지·00:00), 색, 출력 '위' 방향 벡터, 종류)}.
    종류: fol:모듈:자리:세그 / drum:모듈:자리(축·노브·칼라 포함 — 일의 자리와 함께 돈다) / pinion:모듈 / button:모듈 / spring:모듈 / fixed"""
    out = {}
    out['housing'] = (housing(), BLACK, (0, 0, 1), 'fixed')
    out['front'] = (front_panel(), BLACK, (0, 1, 0), 'fixed')
    out['mid'] = (mid_plate(), BLACK, (0, 1, 0), 'fixed')
    out['lid'] = (lid(), BLACK, (0, 0, -1), 'fixed')
    out['colon'] = (colon(), YELLOW, (0, -1, 0), 'fixed')
    for m, c in PAIRS.items(): out.update(module_parts(m, c))
    out['collar_l'] = (collar('l'), GRAY, (1, 0, 0), 'drum:A:ones')
    out['collar_r'] = (collar('r'), GRAY, (1, 0, 0), 'drum:B:ones')
    out['knob_l'] = (knob('l'), YELLOW, (1, 0, 0), 'drum:A:ones')
    out['knob_r'] = (knob('r'), YELLOW, (-1, 0, 0), 'drum:B:ones')
    return out
