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
    # 숫자(日) — 두 자리 중심 x, 숫자 중심 높이 z0
    DH=60.0, DW=34.0, T=8.0, CX_TENS=-24.5, CX_ONES=24.5, Z0=40.0,
    SLOT=2.0, PITCH=5.5, STROKE=3.0, SLOT_W_V=4.4, RIB_EXT=1.0, NOSE_H=3.0,
    # y 층: 앞판 / 셔터 / 가운데 판(빗)
    FP_Y0=0.6, FP_T=1.6, SH_Y0=2.6, RIB=0.6, SH_T=3.0, MP_Y0=6.0, MP_T=3.0,
    # 캠축
    Y_C=22.4, Z_C=32.0, R_LO=9.0, R_HI=12.0, DISC_T=2.8,
    RING_X={'f': -15.5, 'e': -12.0, 'a': -4.5, 'g': 0.0, 'd': 4.5, 'c': 12.0, 'b': 15.5},
    TUBE_R=7.0, TUBE_FLAT=6.0, BORE_R=3.5, CLR=0.2,
    # 래칫·마스크(일의 자리 왼쪽 끝)와 올림 래칫(십의 자리 오른쪽 끝)
    RT_ROOT=12.6, RT_TIP=15.0, M1_RIM=15.8, FACE0=34.0,
    RC_X=(-7.0, -3.4), M1_X=(-3.0, -0.6), R1_X=(-0.6, 3.0), LEVER_X=(3.4, 6.6),
    # 레버
    HUB_R=(7.3, 10.5), P1_ANG=-72.0, P2_ANG=-108.0, P1_ARM_R=17.5, P2_ARM_R=20.2, ARM_T=1.2,
    P1_ROOT=-2.0, P2_ROOT=-30.0, PAWL_TIP=13.0, PAD_ANG=24.0, PAD_R=16.0, PAD_D=4.0, SWING=40.0,
    # 버튼·스프링
    PL_X=(3.4, 10.6), SPR_X=(7.0, 10.6),
    # 별(멈춤쇠)·판스프링
    STAR_TIP=10.0, STAR_ROOT=8.8, STAR_T=2.0, LEAF_T=1.6, LEAF_L=14.0,
    # 축
    HEX_V=3.2, HEX_F=2.9, HEX_FW=1.72, SHAFT_X=(-99.5, 108.0), KNOB_X=(100.5, 110.5), KNOB_R=16.0,
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
def ratchet_r(th):
    """톱니(10개): 면 = FACE0 + 36k. 면 바로 뒤(+θ) 뿌리 → 다음 면 직전 끝까지 직선 상승."""
    g = ((th - P['FACE0']) % 36.0) / 36.0
    return P['RT_ROOT'] + (P['RT_TIP'] - P['RT_ROOT']) * g
NOTCH = ((P['P2_ANG'] + 324.0 - 2.0) % 360.0, (P['P2_ANG'] + 324.0 + 28.0) % 360.0)    # 일의 자리 9 일 때 P2(드럼 좌표 P2+324)가 떨어지는 마스크 홈(214~244°)
def mask_r(th):
    t = th % 360.0; a0, a1 = NOTCH
    if a0 <= t < a0 + 12.0: return ratchet_r(t)                         # 홈 바닥 = 톱니 경사(오버행 0)
    if a0 + 12.0 <= t < a1:
        r0 = ratchet_r(a0 + 12.0); return r0 + (P['M1_RIM'] - r0) * (t - a0 - 12.0) / (a1 - a0 - 12.0)
    return P['M1_RIM']
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
def star_disc(cx, ones):
    """멈춤쇠 별(10 홈) — 따로 출력해 마지막 캠 디스크 바깥에 끼운다(D 구멍)."""
    c = AX(); t = P['DISC_T']; bore = d_profile(P['TUBE_R'] + P['CLR'], P['TUBE_FLAT'] + P['CLR'])
    last = cx + P['RING_X']['b' if ones else 'f']; star = polar_poly(lambda th: star_r(th), c=c).difference(bore)
    return ext_x(star, last + t / 2, last + t / 2 + P['STAR_T']) if ones else ext_x(star, last - t / 2 - P['STAR_T'], last - t / 2)
KEY_ANG = 90.0
def key_cut_and_tooth():
    """코어 관 끝의 리셋 키: 호 모양 판스프링(r 3.5~4.7, 84°→244°, 뿌리 244°) + 안쪽으로 나온 이(걸림면 94°, 끝 r 2.0)."""
    c = AX(); k = KEY_ANG
    slit = annulus_sector(4.7, 5.3, k - 10, k + 154, c)
    endcut = annulus_sector(P['BORE_R'] - 0.5, 5.3, k - 10, k - 6, c)
    def pt(r, a): return (c[0] + r * np.cos(np.radians(a)), c[1] + r * np.sin(np.radians(a)))
    tooth = Polygon([pt(P['BORE_R'] + 0.3, k + 4), pt(2.0, k + 4), pt(2.0, k + 1), pt(P['BORE_R'] + 0.3, k - 6)])
    return unary_union([slit, endcut]), tooth
def core(ones):
    """일의 자리 코어: M1(마스크)+R1(래칫)+D관(+키). 십의 자리: Rc(래칫)+D관(+키)."""
    c = AX(); bore = Point(c).buffer(P['BORE_R'], 64); tube = d_profile(P['TUBE_R'], P['TUBE_FLAT']).difference(bore)
    cut, tooth = key_cut_and_tooth()
    if ones:
        m1 = polar_poly(mask_r, c=c, n=1440).difference(bore); r1 = polar_poly(ratchet_r, c=c, n=1440).difference(bore)
        parts = [ext_x(m1, *P['M1_X']), ext_x(r1, P['R1_X'][0] - 0.01, P['R1_X'][1]),
                 ext_x(tube, P['R1_X'][1] - 0.01, 39.6), ext_x(tube.difference(cut).union(tooth), 39.6 - 0.01, 43.6)]
    else:
        rc = polar_poly(ratchet_r, c=c, n=1440).difference(bore)
        parts = [ext_x(rc, *P['RC_X']), ext_x(tube, -39.6, P['RC_X'][0] + 0.01),
                 ext_x(tube.difference(cut).union(tooth), -43.6, -39.6 + 0.01)]
    return U(parts)

# ---------------------------------------------------------------- 레버(정지 위치에서; 누름 = 축 기준 -SWING 회전)
def _pt(r, a, c=None):
    c = c or AX(); return (c[0] + r * np.cos(np.radians(a)), c[1] + r * np.sin(np.radians(a)))
def _spoke(r0, r1, a, w):
    p0, p1 = _pt(r0, a), _pt(r1, a); from shapely.geometry import LineString
    return LineString([p0, p1]).buffer(w / 2, cap_style=2)
def pawl_tooth(face, ring_r, back_end, drum_off):
    """미는 면(-θ 쪽, 각 face)에서 +θ 로 8° 폭, 아랫면 = 래칫 경사 + 0.3, 뒤는 back_end 각에서 ring_r 로 올라감."""
    pts = [_pt(ring_r + 0.2, face)]
    for a in np.linspace(face, face + 8.0, 9): pts.append(_pt(ratchet_r(a + drum_off) + 0.3 + (P['PAWL_TIP'] - 13.0), a))
    pts.append(_pt(ring_r + 0.2, back_end))
    return Polygon(pts).buffer(0)
def lever():
    c = AX(); x0, x1 = P['LEVER_X']; h0, h1 = P['HUB_R']
    plate = unary_union([annulus_sector(h0, h1, 0, 360, c, 180),
                         _spoke(h1 - 1, P['PAD_R'], P['PAD_ANG'], 2.4), Point(_pt(P['PAD_R'], P['PAD_ANG'])).buffer(P['PAD_D'] / 2, 32),
                         _spoke(h1 - 1, P['P1_ARM_R'] + 0.6, P['P1_ROOT'] - 2.5, 3.6),
                         _spoke(h1 - 1, P['P2_ARM_R'] + 0.6, P['P2_ROOT'] - 2.5, 3.6)])
    r1a = P['P1_ARM_R']; t = P['ARM_T']
    p1 = unary_union([annulus_sector(r1a - t / 2, r1a + t / 2, P['P1_ANG'], P['P1_ROOT'], c),
                      pawl_tooth(P['P1_ANG'], r1a - t / 2, P['P1_ANG'] + 18.0, 0.0)])
    r2a = P['P2_ARM_R']
    p2 = unary_union([annulus_sector(r2a - t / 2, r2a + t / 2, P['P2_ANG'], P['P2_ROOT'], c),
                      pawl_tooth(P['P2_ANG'], r2a - t / 2, P['P2_ANG'] + 13.0, 324.0)])
    root1 = annulus_sector(r1a - t / 2, r1a + t / 2 + 0.6, P['P1_ROOT'] - 5, P['P1_ROOT'], c)
    root2 = annulus_sector(r2a - t / 2, r2a + t / 2 + 0.6, P['P2_ROOT'] - 5, P['P2_ROOT'], c)
    return U([ext_x(plate.union(root1).union(root2), x0, x1),
              ext_x(p1, P['R1_X'][0] + 0.4, x1), ext_x(p2, P['RC_X'][0] + 0.2, x1)])

# ---------------------------------------------------------------- 버튼(플런저+캡)·스프링
PAD_REST = _pt(P['PAD_R'], P['PAD_ANG'])
def plunger_profile():
    py, pz = PAD_REST; lip_top = pz - P['PAD_D'] / 2; top_lip = pz + P['PAD_D'] / 2 + 1.0
    return unary_union([sbox(36.4, lip_top - 3.0, 44.6, lip_top),            # 아래 턱(패드를 받쳐 레버를 끌어올림)
                        sbox(40.8, lip_top - 3.0, 44.6, top_lip + 3.0),      # 뒷벽
                        sbox(36.4, top_lip, 44.6, top_lip + 3.0),            # 위 턱(누르면 패드를 내림)
                        sbox(38.6, top_lip + 2.9, 44.6, 74.1),               # 막대
                        sbox(36.6, 74.0, 46.6, 77.0),                        # 걸림턱(뚜껑 밑)
                        sbox(38.8, 76.9, 44.4, 96.4)])                       # 뚜껑 위로
STROKE_BTN = None
def plunger(): return ext_x(plunger_profile(), *P['PL_X'])
def cap():
    """버튼 캡 Ø22×5 — 막대 끝(7.2×5.6)이 4.5 깊이로 들어감."""
    cy = (38.8 + 44.4) / 2; cxm = sum(P['PL_X']) / 2
    disk = trimesh.creation.cylinder(radius=11.0, height=5.0, sections=96); disk.apply_translation([cxm, cy, 0])
    sock = trimesh.creation.box(extents=[7.2 + 0.3, 5.6 + 0.3, 4.6]); sock.apply_translation([cxm, cy, -2.5 + 2.3])
    m = SUB(disk, [sock]); stroke = btn_stroke(); m.apply_translation([0, 0, 80.0 + stroke + 2.5]); return m
def btn_stroke():
    """누름 행정 = 패드 이동(정지→-SWING) + 놀이 1.0."""
    pz0 = PAD_REST[1]; pz1 = _pt(P['PAD_R'], P['PAD_ANG'] - P['SWING'])[1]
    return pz0 - pz1 + 1.0
def spring(top_z=None):
    """지그재그 판스프링(SPR_X 슬랩). 자유 높이로 만들고 top_z 를 주면 z 를 그 높이로 눌러 그린다(조립 확인용 근사)."""
    lip_bottom = PAD_REST[1] - P['PAD_D'] / 2 - 3.0
    free_top = lip_bottom + 1.2                                  # 예압 1.2
    N, t, y0, y1 = 8, 1.3, 35.6, 55.6
    z_beam0, z_beam1 = 3.0, free_top - 1.5; g = (z_beam1 - z_beam0 - N * t) / (N - 1)
    parts = [sbox(y0, 1.0, y1, 3.0 + 0.01), sbox(36.6, z_beam1 - 0.01, 44.0, free_top)]
    for i in range(N):
        zb = z_beam0 + i * (t + g); parts.append(sbox(y0, zb, y1, zb + t))
        if i < N - 1:
            if i % 2 == 0: parts.append(sbox(y1 - 1.6, zb + t - 0.01, y1, zb + t + g + 0.01))
            else: parts.append(sbox(y0, zb + t - 0.01, y0 + 1.6, zb + t + g + 0.01))
    parts.append(sbox(36.6, z_beam1 - 1.0, 44.0, z_beam1 + 0.01))
    m = ext_x(unary_union(parts), *P['SPR_X'])
    if top_z is not None:
        s = (top_z - 1.0) / (free_top - 1.0); m.apply_translation([0, 0, -1.0]); m.apply_scale([1, 1, s]); m.apply_translation([0, 0, 1.0])
    return m
SPRING_INFO = {}

# ---------------------------------------------------------------- 별 멈춤쇠 판스프링 3개, 축·칼라·노브
LEAF_SLABS = {'leaf_ones': (41.6, 43.2), 'leaf_shaft': (44.2, 45.8), 'leaf_tens': (-43.2, -41.6)}
def leaf(slab):
    yc, zc = AX(); top = zc - P['STAR_ROOT'] - 0.3 - 1.0; post_y = yc + P['LEAF_L']
    prof = unary_union([sbox(post_y, 1.0, post_y + 3.0, top), sbox(yc - 1.5, top - P['LEAF_T'], post_y + 0.01, top),
                        Polygon([(yc - 1.2, top - 0.01), (yc, top + 1.0), (yc + 1.2, top - 0.01)])])
    return ext_x(prof, *slab)
def hex_profile(off=0.0, c=None):
    c = c or AX(); v, f, fw = P['HEX_V'] + off, P['HEX_F'] + off, P['HEX_FW'] + off * 0.5
    return Polygon([(c[0] + x, c[1] + z) for x, z in [(v, 0), (fw, f), (-fw, f), (-v, 0), (-fw, -f), (fw, -f)]])
def groove_cut():
    """축 홈(정지 시 +90° 방향 평면): 걸림벽 96°(r 1.8→3.4), 바닥 r 1.8 96→88°, 경사 88→76°."""
    return Polygon([_pt(3.6, 96.0), _pt(1.8, 96.0), _pt(1.8, 88.0), _pt(3.6, 74.0)])
def shaft():
    return ext_x(hex_profile().difference(groove_cut()), *P['SHAFT_X'])
def collar(right):
    c = AX(); hb = hex_profile(0.15)
    if right:
        star = polar_poly(lambda th: star_r(th), c=c).difference(hb)
        return U([ext_x(star, 44.0, 46.0), ext_x(Point(c).buffer(5.5, 96).difference(hb), 46.0 - 0.01, 96.6)])
    return U([ext_x(Point(c).buffer(10.0, 96).difference(hb), -96.6, -94.6), ext_x(Point(c).buffer(5.5, 96).difference(hb), -94.6 - 0.01, -44.0)])
def knob():
    c = AX(); x0, x1 = P['KNOB_X']
    grip = unary_union([Point(c).buffer(P['KNOB_R'] - 1.0, 128)] + [Point(_pt(P['KNOB_R'] - 1.0, a)).buffer(1.2, 16) for a in range(0, 360, 15)])
    m = ext_x(grip, x0, x1)
    sock = ext_x(hex_profile(0.12), x0 - 0.1, x0 + 7.5)
    arrow = ext_x(Polygon([_pt(13.0, 90), _pt(9.0, 84), _pt(9.0, 96)]), x1 - 0.6, x1 + 0.01)
    return SUB(m, [sock, arrow])

# ---------------------------------------------------------------- 하우징·앞판·가운데 판·뚜껑
CXS = {'tens': P['CX_TENS'], 'ones': P['CX_ONES']}
GROOVES = {'front': (P['FP_Y0'], P['FP_Y0'] + P['FP_T']), 'mid': (P['MP_Y0'], P['MP_Y0'] + P['MP_T'])}
PANEL_HX = 98.4
def teardrop(c, r):
    """위가 뾰족한 구멍 — 옆면 수직에서 30°(층당 0.115 이하): 접점 30°/150°, 꼭짓점 2r."""
    return unary_union([Point(c).buffer(r, 64), Polygon([(c[0] - r * 0.8660, c[1] + r * 0.5), (c[0], c[1] + 2.0 * r), (c[0] + r * 0.8660, c[1] + r * 0.5)])])
def housing():
    W2, D, Hw = P['W'] / 2, P['D'], 77.0
    body = U([ext_z(sbox(-W2, 0, W2, D), 0, P['FLOOR']),
              ext_z(sbox(-W2, 0, -W2 + 3, D), 0, Hw), ext_z(sbox(W2 - 3, 0, W2, D), 0, Hw),
              ext_z(sbox(-W2, D - 3, W2, D), 0, Hw)])
    cuts = []
    for y0, y1 in GROOVES.values():
        for sgn in (-1, 1):
            cuts.append(ext_z(sbox(min(sgn * 96.0, sgn * (PANEL_HX + 0.2)), y0 - 0.15, max(sgn * 96.0, sgn * (PANEL_HX + 0.2)), y1 + 0.15), P['FLOOR'], Hw + 1))
    hole = teardrop(AX(), P['HEX_V'] + 0.25)
    cuts += [ext_x(hole, -W2 - 1, -W2 + 4), ext_x(hole, W2 - 4, W2 + 1)]
    yc = P['Y_C']; py = yc + P['LEAF_L']
    for x0, x1 in LEAF_SLABS.values(): cuts.append(ext_z(sbox(x0 - 0.2, py - 0.2, x1 + 0.2, py + 3.2), 1.0, P['FLOOR'] + 0.1))
    cuts.append(ext_z(sbox(P['SPR_X'][0] - 0.2, 35.4, P['SPR_X'][1] + 0.2, 55.8), 1.0, P['FLOOR'] + 0.1))
    return SUB(body, cuts)
def front_panel():
    hz0, hz1 = P['FLOOR'] + 0.2, 77.0 - 0.2
    plate = sbox(-PANEL_HX, hz0, PANEL_HX, hz1)
    holes = [b for cx in CXS.values() for s in SEGS for b in slots(s, cx)]
    return ext_y(plate.difference(unary_union(holes)), *GROOVES['front'])
def mid_slots():
    out = []
    for cx in CXS.values():
        for s in SEGS:
            rx = cx + P['RING_X'][s]; zl, zh = stem_z(s, cx)
            out.append(sbox(rx - 1.3, zl - 0.5, rx + 1.3, zh + P['STROKE'] + 0.5))
    u = unary_union(out)
    return u.buffer(0.75, join_style=2).buffer(-0.75, join_style=2)       # 1.5 mm 미만 살은 슬롯으로 합침
CORE_WIN = (P['RC_X'][0] - 0.6, P['LEVER_X'][1] + 0.4, P['Z_C'] - P['P2_ARM_R'] - 1.5, P['Z_C'] + P['M1_RIM'] + 1.2)   # 코어 플랜지·레버 폴이 지나는 창
def mid_plate():
    """가운데 판(빗): 스템 슬롯 + 두 자리 사이 코어 플랜지(M1 r 15.8)가 지나가는 창."""
    plate = sbox(-PANEL_HX, P['FLOOR'] + 0.2, PANEL_HX, 77.0 - 0.2)
    win = sbox(CORE_WIN[0], CORE_WIN[2], CORE_WIN[1], CORE_WIN[3])
    cut = mid_slots().union(win).buffer(0.75, join_style=2).buffer(-0.75, join_style=2)   # 창과 슬롯 사이 1.5 미만 살은 없앤다
    return ext_y(plate.difference(cut), *GROOVES['mid'])
def lid():
    W2, D = P['W'] / 2, P['D']
    top = sbox(-W2, 0, W2, D).difference(sbox(P['PL_X'][0] - 0.2, 38.6, P['PL_X'][1] + 0.2, 44.6))
    lips = unary_union([sbox(-96.8, 12.0, -95.6, 56.0), sbox(95.6, 12.0, 96.8, 56.0), sbox(-90.0, 56.6, 90.0, 57.8)])
    return U([ext_z(top, 77.0, 80.0), ext_z(lips, 74.0, 77.0 + 0.01)])

# ---------------------------------------------------------------- 전체 파트 표
BLACK, YELLOW, GRAY, WHITE = '#2b2e33', '#ffb300', '#9aa3ad', '#e8e8e8'
def all_parts():
    """{이름: (메시(조립 좌표·정지·숫자 00), 색, 출력 '위' 방향 벡터, 종류)}. 종류: follower/disc/core/... (조립 상태 변환용)"""
    out = {}
    out['housing'] = (housing(), BLACK, (0, 0, 1), 'fixed')
    out['front'] = (front_panel(), BLACK, (0, 1, 0), 'fixed')
    out['mid'] = (mid_plate(), BLACK, (0, 1, 0), 'fixed')
    out['lid'] = (lid(), BLACK, (0, 0, -1), 'fixed')
    for dn, cx in CXS.items():
        ones = dn == 'ones'
        for s in SEGS:
            b, r = shutter(s, cx)
            out[f'sh_{dn}_{s}'] = (b, BLACK, (0, -1, 0), f'fol:{dn}:{s}')
            out[f'rib_{dn}_{s}'] = (r, YELLOW, (0, -1, 0), f'fol:{dn}:{s}')
            out[f'stem_{dn}_{s}'] = (stem(s, cx), BLACK, stem_up(s), f'fol:{dn}:{s}')
            out[f'disc_{dn}_{s}'] = (disc(s, cx, ones), GRAY, (1, 0, 0) if ones else (-1, 0, 0), f'drum:{dn}')
        out[f'star_{dn}'] = (star_disc(cx, ones), GRAY, (1, 0, 0), f'drum:{dn}')
        out[f'core_{dn}'] = (core(ones), GRAY, (1, 0, 0) if ones else (-1, 0, 0), f'drum:{dn}')
    out['lever'] = (lever(), YELLOW, (-1, 0, 0), 'lever')
    out['plunger'] = (plunger(), GRAY, (1, 0, 0), 'button')
    out['cap'] = (cap(), YELLOW, (0, 0, -1), 'button')
    out['spring'] = (spring(), GRAY, (1, 0, 0), 'spring')
    for n, sl in LEAF_SLABS.items(): out[n] = (leaf(sl), GRAY, (1, 0, 0), 'fixed')
    out['shaft'] = (shaft(), GRAY, (0, 0, 1), 'shaft')
    out['collar_r'] = (collar(True), GRAY, (1, 0, 0), 'shaft')
    out['collar_l'] = (collar(False), GRAY, (1, 0, 0), 'shaft')
    out['knob'] = (knob(), YELLOW, (-1, 0, 0), 'shaft')
    return out
