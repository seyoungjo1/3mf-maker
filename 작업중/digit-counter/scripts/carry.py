"""주행거리계식 전달 피니언(양방향 자리올림·빌림) — 2D 설계·검증.
일의 자리 드럼(축 O) 왼쪽 끝: 잠금 링(R_L) + 자리올림 이 2개(20T 기어의 이웃한 두 이, 그 사이 홈이 피니언 긴 이 하나를 잡아 90° 돌림).
십의 자리 드럼 오른쪽 끝: 20T 기어. 피니언 8T(긴 이 4·짧은 이 4 번갈아, 축 Cp 고정): 짧은 이는 십의 자리 기어 슬랩에만.
잠금: 긴 이 두 개가 잠금 링을 사이에 두고 걸쳐 있어 피니언이 못 돈다 → 십의 자리도 못 돈다. 일의 자리 9↔0 사이(36°)에만 홈이 긴 이 하나를 +45°→-45° 로 넘겨 피니언 90°(= 십의 자리 36°).
좌표: 2D (u, v) = 조립 (y - Y_C, z - Z_C). 각도는 조립과 같이 +y → +z. 드럼은 셀 때 -θ."""
import math, numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely import affinity

M_, Z_G, Z_P, PA = 1.5, 20, 8, 20.0
X_P, X_G = 0.35, 0.0               # 전위 계수(피니언 8T 언더컷 방지)
BACKLASH = 0.15                   # 이 두께에서 뺌(물림당)
P_ANG = -120.0                    # 피니언 축 방향(조립 각) — 앞·아래(가운데 판 창 안, 레버·플런저와 반대쪽)

def inv(a): return math.tan(a) - a
def gear_poly(z, m=M_, x=0.0, pa=PA, backlash=BACKLASH, clearance=0.25, n=20, tip_min=0.6):
    """전위 인벌류트 스퍼 기어 다각형(중심 0, 이 하나가 +u 축 위). 반환 (poly, info)."""
    a = math.radians(pa); r = m * z / 2; rb = r * math.cos(a); ra = r + m * (1 + x); rf = r - m * (1.25 - x)
    s = math.pi * m / 2 + 2 * x * m * math.tan(a) - backlash          # 피치원 이 두께
    psi = s / (2 * r) + inv(a)                                          # 기초원 시작점에서 이 중심선까지 각(인벌류트 기준)
    def thick(rr): t = math.sqrt(max((rr / rb) ** 2 - 1, 0)); return 2 * (psi - (t - math.atan(t))) * rr
    while ra > r and thick(ra) < tip_min: ra -= 0.01                    # 이 끝 두께 ≥ tip_min(노즐 1.5줄) 로 끝을 자름
    tmax = math.sqrt(max((ra / rb) ** 2 - 1, 0))
    flank = []
    for t in np.linspace(0, tmax, n):
        rr = rb * math.sqrt(1 + t * t); ang = psi - (t - math.atan(t))
        flank.append((rr, ang))
    tip_half = flank[-1][1]
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        # 뿌리(이전 이 사이) → 오른쪽 플랭크(아래→위) → 팁 → 왼쪽 플랭크(위→아래)
        if rf < rb: pts.append((rf * math.cos(c - psi), rf * math.sin(c - psi)))
        for rr, ang in flank: pts.append((rr * math.cos(c - ang), rr * math.sin(c - ang)))
        for q in np.linspace(-tip_half, tip_half, 4): pts.append((ra * math.cos(c + q), ra * math.sin(c + q)))
        for rr, ang in flank[::-1]: pts.append((rr * math.cos(c + ang), rr * math.sin(c + ang)))
        if rf < rb: pts.append((rf * math.cos(c + psi), rf * math.sin(c + psi)))
        nxt = c + 2 * math.pi / z
        for q in np.linspace(c + psi + 0.02, nxt - psi - 0.02, 4): pts.append((rf * math.cos(q), rf * math.sin(q)))
    poly = Polygon(pts).buffer(0)
    return poly, dict(r=r, ra=ra, rf=rf, rb=rb, tip_thick=2 * tip_half * ra)

G_POLY, G_INFO = gear_poly(Z_G, x=X_G)
P_POLY, P_INFO = gear_poly(Z_P, x=X_P)
def pinion_long():
    """긴 이만 남긴 피니언(일의 자리 슬랩): 짧은 이(홀수 번호)를 뿌리원 밖에서 잘라냄. 이 0 이 +u 축."""
    keep = Point(0, 0).buffer(P_INFO['rf'] + 0.01, 64)
    for k in range(0, Z_P, 2):
        c = 360.0 * k / Z_P
        wedge = Polygon([(0, 0)] + [(20 * math.cos(math.radians(c + d)), 20 * math.sin(math.radians(c + d))) for d in np.linspace(-22.5, 22.5, 9)])
        keep = keep.union(P_POLY.intersection(wedge))
    return keep.buffer(0)
PL_POLY = pinion_long()

def place(poly, ang_deg, cx=0.0, cy=0.0):
    return affinity.translate(affinity.rotate(poly, ang_deg, origin=(0, 0)), cx, cy)
def overlap(a, b): return a.intersection(b).area

def center_distance():
    """백래시 포함 이 두께로 겹침 0 이 되는 최소 중심거리(위상은 맞물림 최적)."""
    best = None
    for a in np.arange(21.0, 23.0, 0.02):
        cp = (a, 0.0)
        # 기어 이 하나가 축선(+u)에 있고, 피니언은 이 사이가 축선을 향하게(이 하나가 180+22.5°)
        ok = True
        for th in np.linspace(0, 18, 7):
            ph = 180.0 + 22.5 - th * Z_G / Z_P                       # 맞물림 법칙: 피니언 각 = -(20/8)·기어 각 + 위상
            if overlap(place(G_POLY, th), place(P_POLY, ph, *cp)) > 1e-4: ok = False; break
        if ok: best = a; break
    return best

A_C = None
A_EXTRA = 0.3                     # 무백래시 거리(이 두께 -0.15 반영) + 0.3 → 피치원 유격 ≈ 0.2 (FDM)
def setup():
    global A_C
    A_C = round(center_distance() + A_EXTRA, 2)
    return A_C

# ---------------------------------------------------------------- 일의 자리 잠금 링 + 자리올림 이, 운동 법칙
CLR_C = 0.2
def cp():
    a = A_C or setup(); b = math.radians(P_ANG); return (a * math.cos(b), a * math.sin(b))
PHI_LOCK = (P_ANG + 225.0) % 90.0            # 긴 이 두 개가 O 쪽 방향 ±45° 에 걸침(대칭 잠금)
WIN = (-324.0, -360.0)                       # 일의 자리 드럼 각 9 → 10(=0): 이 36° 동안만 피니언 +90°
def phi_of(psi):
    """일의 자리 드럼 각 psi(조립 각, 셀 때 음수) → 피니언 각."""
    w = ((psi % 360.0) - 360.0) if (psi % 360.0) != 0 else 0.0      # (-360, 0]
    if w > WIN[0]: return PHI_LOCK
    return PHI_LOCK + 2.5 * (WIN[0] - w)
def gear_phase(phi, at_psi):
    """기어 이 하나의 조립 각 g 를 피니언 각 phi 와 맞물리게(φ = β + 202.5 − 2.5(g − β) mod 45)."""
    b = P_ANG; g = b + (b + 202.5 - phi) / 2.5
    return g
def lock_tip_r():
    """잠금 자세 긴 이 끝이 O 에 가장 가까이 오는 거리."""
    return Point(0, 0).distance(place(PL_POLY, PHI_LOCK, *cp()))
def sweep(poly, n_lock=81, n_win=161):
    """피니언 다각형이 일의 자리 드럼 좌표에서 한 바퀴 동안 쓸고 지나가는 자리."""
    c = cp(); sw = []
    for psi in np.concatenate([np.linspace(0, -320, n_lock), np.linspace(-320, -360, n_win)]):
        sw.append(affinity.rotate(place(poly, phi_of(psi), *c), -psi, origin=(0, 0)))
    return unary_union(sw).buffer(CLR_C, 32)
def ones_profiles(tip_clr=0.3):
    """일의 자리 두 평면(드럼 좌표 = 숫자 0 정지).
    L(잠금): 링 r_L − 긴 이가 쓴 자리(홈이 생김). 피니언은 긴 이만.
    C(자리올림): 허브(S 이 끝 아래) ∪ 20T 이 2개(끝을 잠긴 긴 이 끝 아래로 잘라 평소엔 그 밑을 지나감) − 피니언 8T 가 쓴 자리.
    자리올림 구간 가운데(psi=-342)에 S 이가 O 를 향하고, 이 A·B 는 그 앞뒤 홈(±9°, 드럼 좌표 mid−9 / mid+9... 진행 방향 뒤쪽 두 개)."""
    tip = lock_tip_r(); rL = tip - 0.45
    rH = A_C - P_INFO['ra'] - tip_clr; rC = tip - tip_clr
    L = Point(0, 0).buffer(rL, 256).difference(sweep(PL_POLY)).buffer(0)
    mid = P_ANG + 342.0
    teeth = []
    for d in (-9.0, 9.0, 27.0):
        t = place(G_POLY, mid + d)
        wedge = Polygon([(0, 0)] + [(30 * math.cos(math.radians(mid + d + q)), 30 * math.sin(math.radians(mid + d + q))) for q in np.linspace(-8.9, 8.9, 9)])
        teeth.append(t.intersection(wedge))
    Cb = unary_union([Point(0, 0).buffer(rH, 256)] + teeth).intersection(Point(0, 0).buffer(rC, 256))
    C = Cb.difference(sweep(P_POLY)).buffer(0)
    return dict(L=L, C=C, rL=rL, rH=rH, rC=rC, tip=tip)
def tens_gear():
    """십의 자리 20T(드럼 좌표 = 숫자 0 정지): 피니언 잠금 각과 맞물리는 위상."""
    return place(G_POLY, gear_phase(PHI_LOCK, 0.0))
def _ov(pr, psi, phi, c):
    return (overlap(affinity.rotate(pr['L'], psi, origin=(0, 0)), place(PL_POLY, phi, *c))
            + overlap(affinity.rotate(pr['C'], psi, origin=(0, 0)), place(P_POLY, phi, *c)))
def simulate(pr, step=1.0):
    """법칙대로 돌릴 때 겹침과 피니언 유격(±δ, 두 평면)."""
    c = cp(); out = []
    for psi in np.arange(0, -360.0 - 1e-9, -step):
        phi = phi_of(psi)
        def free(sign):
            for d in np.arange(0.25, 30.01, 0.25):
                if _ov(pr, psi, phi + sign * d, c) > 1e-3: return d - 0.25
            return 30.0
        out.append((psi, phi, _ov(pr, psi, phi, c), free(+1), free(-1)))
    return out
def push_sim(pr, direction=+1, step=0.25, dstep=0.1, eps=1e-3):
    """멈춤쇠가 십의 자리(=피니언)를 붙잡고 있을 때: 피니언은 밀릴 때만 돈다.
    direction=+1 셀 때(-320 → -364, 피니언 +), -1 되감기(-364 → -320, 피니언 −)."""
    c = cp(); phi = PHI_LOCK if direction > 0 else PHI_LOCK + 90.0
    psis = np.arange(-320.0, -364.0 - 1e-9, -step) if direction > 0 else np.arange(-364.0, -320.0 + 1e-9, step)
    out = []
    for psi in psis:
        d = 0.0
        while _ov(pr, psi, phi + direction * d, c) > eps:
            d += dstep
            if d > 60: return out, None
        phi += direction * d; out.append((psi, phi, d))
    return out, max(r[2] for r in out) / step

def figure(pr, out):
    """설계 그림: 잠금(숫자 0) / 자리올림 중간 / 끝, 두 평면 + 십의 자리 기어."""
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
    c = cp(); T0 = tens_gear()
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))
    def draw(ax, g, **kw):
        for p in getattr(g, 'geoms', [g]):
            x, y = p.exterior.xy; ax.fill(x, y, **kw)
            for h in p.interiors: hx, hy = h.xy; ax.fill(hx, hy, color='white')
    for col, psi in enumerate((-324.0, -342.0, -360.0 + 1e-6)):
        phi = phi_of(psi)
        for row, (name, prof, pin) in enumerate((('L 잠금 평면', pr['L'], PL_POLY), ('C 자리올림 평면', pr['C'], P_POLY))):
            ax = axs[row, col]
            draw(ax, affinity.rotate(prof, psi, origin=(0, 0)), color='#37474f', alpha=0.85)
            draw(ax, place(pin, phi, *c), color='#ffb300', alpha=0.8)
            if row == 1: ax.plot(*affinity.rotate(T0, -(phi - PHI_LOCK) / 2.5, origin=(0, 0)).exterior.xy, color='#4caf50', lw=0.6)
            ax.set_aspect('equal'); ax.set_xlim(-25, 15); ax.set_ylim(-35, 5); ax.grid(alpha=0.3)
            ax.set_title(f'{name}  일의 자리 {psi:.0f}°  피니언 {phi:.1f}°', fontsize=9)
    fig.suptitle(f'전달 피니언 m{M_} 20T/8T  a={A_C}  r_L={pr["rL"]:.2f}  허브 {pr["rH"]:.2f}  자리올림 이 끝 {pr["rC"]:.2f} (초록 = 십의 자리 20T)')
    fig.tight_layout(); fig.savefig(out, dpi=110)
