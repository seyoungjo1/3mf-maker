#!/usr/bin/env python3
"""racket-grip-case 빌드 — 배드민턴 라켓 손잡이(G5) 보관 케이스: 적층섬유(프린트인플레이스 패브릭) 원통 + 래칫 조임띠 2개 + 바닥 캡.
`python tools/mm.py make 작업중/racket-grip-case/pipeline.json` 이 이 스크립트를 프로젝트 폴더에서 실행한다.

출력 좌표(평평하게 한 판): x = 띠 방향(감으면 둘레, s), y = 손잡이 축 방향(아래 띠 y=0 → 위 띠 y=J·p), z = 두께(베드 면이 감았을 때 안쪽).
- 천: A(우리: 바닥 링 + 모서리 기둥 + 윗 링 브리지) · B(가운데 기둥 + 팔 브리지 + 끝 기둥) 체커보드. B 팔이 이웃 A 옆 창을 지나고
  끝 기둥이 A 안에서 아래·위 막대에 걸려 빠지지 않는다. 모든 면 수직 + 양쪽 지지 브리지(≤ 7) → 한쪽 지지 오버행 0.
- 띠: 위(해제 탭, 손잡이 위쪽을 조임) / 아래(탭 없음 = 영구, 캡 홈에 물림 → 캡과 천이 분리되지 않음). 머리는 수평 터널 +
  XY 평면에서 휘는 혀(층과 나란히 휨 — Z 적층 약점 없음), 꼬리 옆 가장자리 톱니.
- 캡: 위가 열린 컵(바로 세워 출력), 바깥 홈(띠 자리) 위 턱은 층당 0.1 경사.
산출: parts_nominal.pkl / parts.pkl(첫 층 +0.15) / wrapped.pkl(감은 상태 — 조립 검증·렌더용) / models/racket-grip-case_A.3mf
"""
import os, sys, math, pickle
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROJ))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import trimesh, manifold3d as mf
from efc import pre_expand_first_layer
from generic3mf import write_generic_3mf

# ── 설계 치수표 (README.md 와 같게) ─────────────────────────────────────────────
P = dict(
    G5_CIRC=83.0,        # G5 그립 둘레(Toby's Sports Yonex 표 G5 83 mm; 다른 판매처 3.25 in = 82.6)
    CLR_SIDE=2.0,        # 손잡이 옆 여유(한쪽) — 사용자
    CLR_END=4.0,         # 끝(뽕) 굵기 여유(한쪽) — 사용자
    HANDLE_L=200.0,      # 손잡이 길이 — 가정(실측 필요)
    CAP_FLOOR=2.0, CAP_INNER_H=22.0,          # 캡 바닥 두께, 안 깊이(뽕 높이 미정 — 가정)
    GROOVE_WALL=1.2,     # 홈 자리 캡 벽(≥1.2)
    # 천 링크
    p=9.8, a=4.4, w=1.3, s=1.4, hb=1.2, zt0=3.6, zt1=4.6,     # 피치 · A 반폭 · 막대 폭 · 기둥 · 바닥 막대 높이 · 윗 막대 z
    c=2.0, wa=1.3, za0=1.8, za1=2.8, hh=1.3, hy=2.0, g=0.4,   # B 가운데 기둥 · 팔 폭 · 팔 z · 끝 기둥(깊이·폭) · 끝 기둥↔막대 틈
    # 래칫 띠
    BW=4.0, BT=1.0, LH=10.0,                                 # 띠 폭 · 두께 · 머리 길이
    TP=2.0, TD=0.8, TE=0.6,                                  # 톱니 피치 · 깊이 · 물림
    TONGUE_T=1.2, TUN_GAP=0.4,                               # 혀 두께 · 터널 틈
)
J = 17                                                       # 행 수(아래 띠 0 … 위 띠 J) — 위 띠가 손잡이 끝(조립 z 202)보다 9 mm 아래

D_H = P['G5_CIRC'] / math.pi                                  # 26.42 (원 환산 지름)
R_TUBE = D_H / 2 + P['CLR_SIDE']                              # 15.21 천 안쪽 반경
R_CAP_IN = D_H / 2 + P['CLR_END']                             # 17.21 캡 안 반경(뽕 자리, 끝 여유 4)
R_CAP_OUT = R_CAP_IN + P['GROOVE_WALL']                       # 18.41 캡 아래 바깥 반경
NECK_Z0 = P['CAP_FLOOR'] + 18.0                               # 20.0 뽕 자리 위 끝 → 목으로 좁아지기 시작
NECK_Z1 = NECK_Z0 + (R_CAP_IN - R_TUBE) / 0.1 * 0.2           # 24.0 목 안쪽 경사(층당 0.1)
R_G = R_TUBE + P['GROOVE_WALL']                               # 16.41 목 홈 바닥(아래 띠 안쪽면) — 목 안 반경 = 천 안 반경(옆 여유 2)
R_0 = R_G + P['BT']                                           # 17.41 홈 위 턱 반경
HEAD_DN, HEAD_UP = 5.8, 3.8                                   # 아래 띠 머리가 띠 중심에서 아래(캡 쪽)·위(천 쪽)로 나온 폭
Y0_Z = NECK_Z1 + 0.3 + HEAD_DN                                # 30.1 아래 띠 중심(조립 z) — 머리가 목 홈 노치 안(z 24.3~)에 들어감
GROOVE_Z0 = Y0_Z - P['BW'] / 2 - 0.3; GROOVE_Z1 = Y0_Z + P['BW'] / 2 + 0.3   # 27.8 ~ 32.4 둘레 홈
LIP_H = 2.0                                                   # 위 턱 경사 높이(1.0 / 10층 = 0.1/층)
CAP_H = GROOVE_Z1 + LIP_H                                     # 34.4
NOTCH_ARC = P['LH'] + 3.0                                     # 머리 자리 노치(호 길이 13 → 45°): 홈 바닥 반경으로 z 24 부터 위가 열림
OCT_SIDE = P['G5_CIRC'] / 8; OCT_RC = OCT_SIDE / (2 * math.sin(math.pi / 8))   # 손잡이 8각 꼭짓점 반경 13.56
R_TOP_TIGHT = OCT_RC + 0.05                                   # 위 띠 끝까지 조였을 때 안쪽 반경(8각 모서리)

COLORS = {'links_A': '#37474f', 'links_B': '#ffb300', 'band_top': '#ff8f00', 'band_bottom': '#ff8f00', 'cap': '#37474f'}
PRINT_COLOR = '#37474f'                                       # 3MF 는 한 색(PLA 1롤)

def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def prism(pts, z0, z1):
    return mf.CrossSection([[(float(x), float(y)) for x, y in pts]]).extrude(z1 - z0).translate([0, 0, z0])

def union(ms):
    return mf.Manifold.batch_boolean(ms, mf.OpType.Add)

def to_tm(m):
    g = m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)

# ── 반경 프로파일: 행 y → 감았을 때 안쪽 반경 ─────────────────────────────────────
TAPER = (P['p'], 4 * P['p'])                                 # 아래 띠 반경(16.41) → 천 반경(15.21)을 1~4행(29.4 mm)에 나눠 줄임(링크 옆 놀이 안)
def r_of_y(y):
    if y <= TAPER[0]: return R_G
    if y >= TAPER[1]: return R_TUBE
    t = (y - TAPER[0]) / (TAPER[1] - TAPER[0]); return R_G * (1 - t) + R_TUBE * t

def circ(y): return 2 * math.pi * r_of_y(y)

# ── 링크 부재 ────────────────────────────────────────────────────────────────
def elem_A(cx, cy):
    a, w, s, hb, zt0, zt1 = P['a'], P['w'], P['s'], P['hb'], P['zt0'], P['zt1']
    ring = lambda z0, z1: [box(cx - a, cx + a, cy - a, cy - a + w, z0, z1), box(cx - a, cx + a, cy + a - w, cy + a, z0, z1),
                           box(cx - a, cx - a + w, cy - a, cy + a, z0, z1), box(cx + a - w, cx + a, cy - a, cy + a, z0, z1)]
    posts = [box(cx + sx * a - (s if sx > 0 else 0), cx + sx * a + (0 if sx > 0 else s), cy + sy * a - (s if sy > 0 else 0), cy + sy * a + (0 if sy > 0 else s), 0, zt1)
             for sx in (-1, 1) for sy in (-1, 1)]
    return union(ring(0, hb) + ring(zt0, zt1) + posts)

def arm_head(cx, cy, d, z_post_top):
    """B 중심 (cx,cy) 에서 방향 d(±x/±y 단위) 로 팔 + 끝 기둥."""
    p, a, w, g, hh, hy, wa, za0, za1, c, zt1 = (P[k] for k in ('p', 'a', 'w', 'g', 'hh', 'hy', 'wa', 'za0', 'za1', 'c', 'zt1'))
    h0 = p - a + w + g; h1 = h0 + hh                           # 7.0 ~ 8.2
    dx, dy = d
    def seg(u0, u1, half, z0, z1):                             # 축 방향 구간 u0..u1, 폭 ±half
        if dx: xs = sorted([cx + dx * u0, cx + dx * u1]); return box(xs[0], xs[1], cy - half, cy + half, z0, z1)
        ys = sorted([cy + dy * u0, cy + dy * u1]); return box(cx - half, cx + half, ys[0], ys[1], z0, z1)
    return [seg(c / 2 - 0.05, h0 + 0.05, wa / 2, za0, za1), seg(h0, h1, hy / 2, 0, za1)]   # 끝 기둥은 팔 높이까지(아래 막대에 걸림) — 높으면 꺾일 때 모서리가 막대를 긁는다

def elem_B(cx, cy, dirs):
    c, za1 = P['c'], P['za1']
    ms = [box(cx - c / 2, cx + c / 2, cy - c / 2, cy + c / 2, 0, za1)]
    for d in dirs: ms += arm_head(cx, cy, d, za1)
    return union(ms)

# ── 래칫 띠(위 띠 기준 지역 좌표: 띠 중심 y=0, 천은 -y 쪽, 혀는 +y 쪽) ──────────────
def band(s_posts, s_teeth0, s_teeth1, tab, arm_dir=(0, -1)):
    BW, BT, LH, TP, TD, TE, TT, TG = (P[k] for k in ('BW', 'BT', 'LH', 'TP', 'TD', 'TE', 'TONGUE_T', 'TUN_GAP'))
    hw = BW / 2                                                # 2.0
    tun_z0 = BT + TG; tun_z1 = tun_z0 + BT                     # 꼬리가 지나는 높이 1.4 ~ 2.4
    tongue_y0 = hw + TG; tongue_y1 = tongue_y0 + TT            # 2.4 ~ 3.6
    rail_y0 = tongue_y1 + TE + 0.2; rail_y1 = rail_y0 + 1.4    # 4.4 ~ 5.8 (혀가 휘는 자리 0.8)
    wall_y1 = -(hw + TG); wall_y0 = wall_y1 - 1.4              # -2.4 ~ -3.8
    tongue_z1 = tun_z1 + 0.2                                   # 2.6
    roof_z0 = tongue_z1 + TG; roof_z1 = roof_z0 + 1.0          # 3.0 ~ 4.0
    tip_y = hw - TE                                            # 1.4 혀 톱니 끝
    ms = []
    # 머리
    ms.append(box(0, LH, wall_y1 + 0.4, tip_y - 0.4, 0, BT))                     # 머리 아래 띠 시작부(-2.0 ~ 1.0)
    ms.append(box(0, LH, wall_y0, wall_y1, 0, roof_z1))                          # 왼 벽
    ms.append(box(0, LH, wall_y0, wall_y1 + 0.4, 0, BT))                         # 왼 벽 ↔ 띠 연결
    ms.append(box(0, LH, rail_y0, rail_y1, 0, roof_z1))                          # 바깥 레일
    ms.append(box(LH - 2.0, LH, wall_y0, rail_y1, 0, BT))                        # 뿌리 블록(꼬리 아래)
    ms.append(box(LH - 2.0, LH, tongue_y0, rail_y1, 0, roof_z1))                 # 뿌리 블록(혀 뿌리·레일)
    ms.append(box(0, LH, wall_y0, rail_y1, roof_z0, roof_z1))                    # 지붕(브리지 6.8)
    t0 = -4.0 if tab else 0.5
    ms.append(box(t0, LH - 2.0 + 0.05, tongue_y0, tongue_y1, 0, tongue_z1))      # 혀
    ms.append(prism([(0.8, tongue_y0 + 0.05), (2.2, tip_y), (2.6, tip_y), (2.6, tongue_y0 + 0.05)], 0, tongue_z1))  # 혀 톱니(XY 평면)
    if tab: ms.append(box(-4.0, -0.6, tongue_y0, rail_y1, 0, tongue_z1))         # 해제 탭(손가락으로 +y 로 밀면 풀림)
    # 띠 몸통 + 꼬리(옆 톱니) + 끝
    s_end = s_teeth1 + 2.0
    ms.append(prism(_tail_outline(s_teeth0, s_teeth1, s_end), 0, BT))
    # 띠 위 B 기둥 + 천 쪽 팔
    for sx in s_posts:
        ms.append(box(sx - P['c'] / 2, sx + P['c'] / 2, -P['c'] / 2, P['c'] / 2, 0, P['za1']))
        ms += arm_head(sx, 0.0, arm_dir, P['za1'])
    return union(ms)

def _tail_outline(s0, s1, s_end):
    """꼬리 평면 윤곽(반시계). +y 가장자리 톱니: +x 로 가며 마루(hw) → 1.4 동안 경사로 골(hw-TD)로 내려감 → 골 0.6 → 수직으로 마루.
    꼬리가 +x(조임)로 움직이면 혀 톱니가 경사를 타고 밀려나고, -x(풀림)로는 골 끝 수직면에 걸린다."""
    hw, TP, TD, LH = P['BW'] / 2, P['TP'], P['TD'], P['LH']
    lower = [(LH - 2.0, -hw), (s_end, -hw), (s_end + 6.0, -0.6), (s_end + 6.0, 0.6), (s_end, hw)]
    top = []                                                   # +x → -x 순서(반시계 윤곽의 윗변)
    n = int((s1 - s0) // TP)
    for i in range(n, 0, -1):
        k0 = s0 + (i - 1) * TP                                 # 이 톱니 구간 [k0, k0+TP]
        top += [(k0 + TP, hw), (k0 + TP, hw - TD), (k0 + 1.4, hw - TD), (k0, hw)]
    top.append((LH - 2.0, hw))
    return _dedupe(lower + top)

def _dedupe(pts):
    out = []
    for q in pts:
        if not out or abs(q[0] - out[-1][0]) > 1e-9 or abs(q[1] - out[-1][1]) > 1e-9: out.append(q)
    if abs(out[0][0] - out[-1][0]) < 1e-9 and abs(out[0][1] - out[-1][1]) < 1e-9: out.pop()
    return out

# ── 캡 ───────────────────────────────────────────────────────────────────────
def make_cap(notch_deg=0.0):
    """바로 세워 출력하는 컵. 뽕 자리(안 반경 17.21, 끝 여유 4) → 층당 0.1 경사로 목(안 반경 15.21 = 천과 같은 옆 여유 2) →
    목 바깥 홈(바닥 16.41)에 아래 띠, 위 턱 17.41(층당 0.1 경사). 머리 자리 노치(45°)는 홈 바닥 반경으로 z 24 부터 위까지 열림."""
    prof = [(0, 0), (R_CAP_OUT, 0), (R_CAP_OUT, GROOVE_Z0), (R_G, GROOVE_Z0), (R_G, GROOVE_Z1), (R_0, CAP_H),
            (R_TUBE, CAP_H), (R_TUBE, NECK_Z1), (R_CAP_IN, NECK_Z0), (R_CAP_IN, P['CAP_FLOOR']), (0, P['CAP_FLOOR'])]
    cup = mf.CrossSection([prof]).revolve(160)
    half = math.radians(NOTCH_ARC / R_G * 180 / math.pi / 2); c = math.radians(notch_deg)
    pts = [(0.0, 0.0)] + [(30 * math.cos(c + t), 30 * math.sin(c + t)) for t in np.linspace(-half, half, 9)]
    wedge = prism(pts, NECK_Z1, CAP_H + 1.0) - mf.Manifold.cylinder(CAP_H + 2.0, R_G, R_G, 160).translate([0, 0, NECK_Z1 - 0.5])
    return cup - wedge

# ── 배치 ─────────────────────────────────────────────────────────────────────
def layout():
    """행·열 격자에서 A/B 위치와 각 띠의 B 기둥 s, 톱니 구간을 정한다. 반환 dict."""
    p, a, LH = P['p'], P['a'], P['LH']
    s0 = LH + 0.6                                              # 천 시작(머리 뒤)
    x0 = s0 + a                                                # 0번 열 중심
    C_bot = 2 * math.pi * R_G; C_top_loose = 2 * math.pi * R_TUBE; C_top_tight = 2 * math.pi * R_TOP_TIGHT
    post_max = {0: C_bot - 12.0, J: C_top_tight - 9.0}         # 띠 위 기둥은 꼬리가 머리를 지나는 구간 앞에서 끝
    cells = {}
    W = 2 * math.pi * R_G + 13.0                                 # 직사각 천: 가장 큰 둘레(아래 띠) + 겹침 13 (작은 둘레 행은 더 겹침)
    for j in range(1, J):
        s_end = s0 + W
        for i in range(0, 40):
            cx = x0 + i * p
            if (i + j) % 2 == 0 and cx + a <= s_end: cells[(i, j)] = 'A'
            elif (i + j) % 2 == 1 and cx + 1.0 <= s_end: cells[(i, j)] = 'B'
    for jb in (0, J):
        for i in range(0, 40):
            cx = x0 + i * p
            if (i + jb) % 2 == 1 and cx <= post_max[jb]: cells[(i, jb)] = 'Bband'
    # 이웃 A 가 없는 B 는 버린다
    nb = lambda i, j: [(d, (i + d[0], j + d[1])) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    for k, t in list(cells.items()):
        if t.startswith('B') and not any(cells.get(q) == 'A' for _, q in nb(*k)): del cells[k]
    # 연결성: 모든 A 가 띠까지 이어지는지
    adj = {k: [q for _, q in nb(*k) if q in cells and (cells[q] == 'A') != (cells[k] == 'A')] for k in cells}
    seen, stack = set(), [k for k, t in cells.items() if t == 'Bband']
    while stack:
        k = stack.pop()
        if k in seen: continue
        seen.add(k); stack += adj[k]
    lonely = [k for k in cells if k not in seen]
    return dict(cells=cells, x0=x0, s0=s0, W=W, C_bot=C_bot, C_top_loose=C_top_loose, C_top_tight=C_top_tight,
                teeth_bot=(C_bot - 6.0, C_bot + LH + 8.0), teeth_top=(C_top_tight - 6.0, C_top_loose + LH + 8.0), lonely=lonely, nb=nb)

def notch_deg(L):
    """감은 상태에서 아래 띠 머리 가운데의 각도(조립 좌표) — 캡 노치를 여기에 둔다(실물에서는 머리를 노치에 맞춰 조인다)."""
    return math.degrees((P['LH'] / 2 - (L['s0'] + L['W'] / 2)) / R_G)

def make_parts():
    """출력 방향 공칭 파트. 반환 (parts, meta)."""
    L = layout(); cells, x0, p = L['cells'], L['x0'], P['p']
    As, Bs = [], []
    for (i, j), t in cells.items():
        cx, cy = x0 + i * p, j * p
        if t == 'A': As.append(elem_A(cx, cy))
        elif t == 'B':
            dirs = [d for d, q in L['nb'](i, j) if cells.get(q) == 'A']; Bs.append(elem_B(cx, cy, dirs))
    sp = lambda jb: [x0 + i * p for (i, j), t in cells.items() if t == 'Bband' and j == jb]
    top = band(sorted(sp(J)), *L['teeth_top'], tab=True, arm_dir=(0, -1)).translate([0, J * p, 0])
    bot = band(sorted(sp(0)), *L['teeth_bot'], tab=False, arm_dir=(0, -1)).mirror([0, 1, 0])   # y 거울 → 천 쪽 +y, 혀 -y
    parts = {'links_A': to_tm(mf.Manifold.compose(As)), 'links_B': to_tm(mf.Manifold.compose(Bs)),
             'band_top': to_tm(top), 'band_bottom': to_tm(bot), 'cap': to_tm(make_cap(notch_deg(L)))}
    meta = dict(n_A=len(As), n_B=len(Bs), n_band_posts={'top': len(sp(J)), 'bottom': len(sp(0))}, lonely=L['lonely'],
                C_bot=L['C_bot'], C_top_loose=L['C_top_loose'], C_top_tight=L['C_top_tight'], teeth_top=L['teeth_top'], teeth_bot=L['teeth_bot'])
    return parts, meta

# ── 감은 상태(조립 검증·렌더용) ────────────────────────────────────────────────
def wrap(m, kind, L):
    """평판 메시 → 원통(헐거운 상태: 위 띠 = 천 반경). 베드 면이 안쪽. 모든 행·띠가 같은 기준 s_c(천 가운데)에서 θ = (s − s_c)/R(y),
    r = R + z + 겹침 오프셋(한 바퀴를 넘는 부분이 바깥으로 올라탐 — 천은 두께+0.4, 꼬리는 머리 터널 높이 1.4).
    행마다 R 이 다르면 같은 s 의 위아래 링크가 θ 로 어긋난다 = 링크가 받아야 하는 전단 → 감은 상태 교집합으로 검사된다."""
    s_c = L['s0'] + L['W'] / 2
    if kind == 'band_top': Rb, u0, lift = R_TUBE, 0.0, 1.4
    elif kind == 'band_bottom': Rb, u0, lift = R_G + 0.06, 0.0, 1.4      # 홈 바닥에 닿음(다각형 근사 현 오차만큼 띄움)
    else: Rb, u0, lift = None, L['s0'], P['zt1'] + 0.4      # 천 두께(4.6) + 0.4
    def f(v):
        s, y, z = v
        R = Rb if Rb else r_of_y(y)
        RAMP = 8.0 if Rb else 25.0                           # 천은 완만하게 올라탐(링크가 기울기에 찌그러지지 않게)
        u = s - u0; t = min(max((u - (2 * math.pi * R - RAMP)) / RAMP, 0.0), 1.0); off = lift * t * t * (3 - 2 * t)
        th = (s - s_c) / R; r = R + z + off
        return [r * math.cos(th), r * math.sin(th), Y0_Z + y]
    g = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32))).refine_to_length(1.2)
    return to_tm(g.warp(f))

def handle_dummy():
    """G5 8각 손잡이(둘레 83) — 캡 바닥(z 2.0)부터 HANDLE_L."""
    ang = [math.pi / 8 + k * math.pi / 4 for k in range(8)]
    poly = [(OCT_RC * math.cos(t), OCT_RC * math.sin(t)) for t in ang]
    return to_tm(prism(poly, P['CAP_FLOOR'], P['CAP_FLOOR'] + P['HANDLE_L']))

def plate(parts):
    """플레이트: 천 오브젝트(파트 4개, 한 색) x 10~, 캡은 오른쪽."""
    fab = ['links_A', 'links_B', 'band_top', 'band_bottom']
    lo = np.min([parts[n].bounds[0] for n in fab], axis=0)
    sh = [10.0 - lo[0], 10.0 - lo[1], 0]
    objs = [{'name': 'fabric_case', 'parts': [(parts[n].copy().apply_translation(sh), PRINT_COLOR, n) for n in fab]}]
    hi = np.max([parts[n].bounds[1] for n in fab], axis=0) + sh
    cap = parts['cap'].copy(); cap.apply_translation([hi[0] + 12.0 + R_0, 10.0 + R_0, 0])
    objs.append({'name': 'cap', 'parts': [(cap, PRINT_COLOR, 'cap')]})
    return objs

if __name__ == '__main__':
    os.chdir(PROJ); os.makedirs('models', exist_ok=True)
    nominal, meta = make_parts(); L = layout()
    pickle.dump(nominal, open('parts_nominal.pkl', 'wb'))
    printed = {n: pre_expand_first_layer(m) for n, m in nominal.items()}; pickle.dump(printed, open('parts.pkl', 'wb'))
    write_generic_3mf('models/racket-grip-case_A.3mf', plate(printed), 'racket-grip-case')
    wrapped = {f'w_{n}': wrap(nominal[n], n, L) for n in ('links_A', 'links_B', 'band_top', 'band_bottom')}
    wrapped['handle'] = handle_dummy()
    pickle.dump(wrapped, open('wrapped.pkl', 'wb'))
    meta['extents'] = {n: [round(v, 2) for v in m.extents] for n, m in nominal.items()}
    meta['volume_cm3'] = {n: round(m.volume / 1000, 2) for n, m in nominal.items()}
    import json; json.dump(meta, open('build_meta.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('build ok', json.dumps(meta, ensure_ascii=False, default=str))
