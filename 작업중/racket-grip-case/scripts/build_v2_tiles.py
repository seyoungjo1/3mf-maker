#!/usr/bin/env python3
"""racket-grip-case v2 빌드 — 배드민턴 라켓 손잡이(G5) 보관 케이스: **비늘(타일) 적층섬유** 원뿔 통 + 래칫 조임띠 2개(막과 한 몸) + 바닥 캡.
`python tools/mm.py make 작업중/racket-grip-case/pipeline.json` 이 이 스크립트를 프로젝트 폴더에서 실행한다.

- 적층섬유(사용자 정의: 비늘·타일 연결): 6×6 사각 타일(높이 1.6, 윗 모서리 0.4 챔퍼)을 틈 3 으로 놓고, 첫 2층(0.4)의 얇은 막이
  타일 사이를 이어 한 장으로 휜다. 막은 휘기만 하고 늘어나지 않으므로 통은 '펼칠 수 있는' 원뿔(아래 띠 16.41 → 위 띠 15.21)로 만든다.
- 매개 좌표 (s, y, z): s = 아래 원(반경 R_G) 기준 호 길이, y = 손잡이 축, z = 두께(베드 면 = 감았을 때 안쪽).
  출력 판 = 매개 좌표를 원뿔 전개도로 굽힌 것(warp_flat), 감은 상태 = 원뿔로 감은 것(warp_wrap). 같은 매개 메시에서 두 가지를 만든다.
- 조임띠·캡·손잡이 모형은 v1(scripts/build_v1_links.py)의 검증된 부품을 그대로 쓴다(띠 위 링크 기둥만 없음).
산출: parts_nominal.pkl / parts.pkl(첫 층 +0.15) / wrapped.pkl / models/racket-grip-case_A.3mf
"""
import os, sys, math, pickle, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROJ))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, HERE)
import trimesh, manifold3d as mf
from efc import pre_expand_first_layer
from generic3mf import write_generic_3mf
import build_v1_links as V1
from build_v1_links import box, union, to_tm, band, make_cap, handle_dummy, R_TUBE, R_G, R_TOP_TIGHT, Y0_Z, NOTCH_ARC

# ── 설계 치수표 (README.md 와 같게) ─────────────────────────────────────────────
P = dict(V1.P)
P.update(
    TILE=6.0, TILE_GAP=3.0, TILE_H=1.6, TILE_CH=0.4,   # 타일 6×6, 틈 3(위 띠 쪽 실제 틈), 높이(막 위), 윗 모서리 챔퍼 — 사용자 선택 A
    FILM=0.4,                                          # 막 두께 = 2층(0.2)
    EDGE_GAP=0.6,                                      # 띠에 안 붙는 구간에서 막 ↔ 띠 틈
    OVERLAP=13.0,                                      # 이음 겹침(아래 둘레 기준)
    Y_TOP=166.0,                                       # 위 띠 중심(아래 띠 중심 기준) → 조립 z 196.1 (손잡이 끝 z 202 의 5.9 아래)
    Y_FIRST=9.0,                                       # 첫 타일 줄 아래 끝(조립 z 39.1) — 캡 윗면(34.4) 위. 띠 ~ 첫 줄은 열마다 막 탭(캡 위 턱을 넘어 휨)
)
R_BOT, R_TOP = R_G, R_TUBE                             # 원뿔: 아래(홈 바닥) 16.41 → 위(옆 여유 2) 15.21
SIN_A = (R_BOT - R_TOP) / P['Y_TOP']; RHO_BOT = R_BOT / SIN_A     # 원뿔 반각 sin, 꼭짓점 ~ 아래 원 거리(전개도 반경 ≈ 2270)
def R(y): return R_BOT - SIN_A * y
K_TOP = R_BOT / R_TOP                                   # 위 띠를 매개 좌표로 옮길 때 s 배율(감으면 실제 치수)

COLORS = {'fabric': '#ffb300', 'cap': '#37474f'}
PRINT_COLOR = '#37474f'

# ── 배치 ─────────────────────────────────────────────────────────────────────
def layout():
    LH, T, G = P['LH'], P['TILE'], P['TILE_GAP']
    s0 = LH + 0.6
    pitch_s = (T + G) * R_BOT / R_TOP                   # 매개 열 피치 9.71 → 위 띠 쪽 실제 피치 9.0(틈 3.0), 아래 쪽 9.71(틈 3.71)
    C_bot = 2 * math.pi * R_BOT
    n_col = math.ceil((C_bot + P['OVERLAP']) / pitch_s); s_end = s0 + n_col * pitch_s
    y_lo, y_hi = P['Y_FIRST'], P['Y_TOP'] - P['BW'] / 2 - G / 2
    n_row = int((y_hi - y_lo + G) // (T + G)); y_pad = y_hi - y_lo - (n_row * (T + G) - G)
    rows = [y_lo + j * (T + G) + T / 2 for j in range(n_row)]
    cols = [s0 + (k + 0.5) * pitch_s for k in range(n_col)]
    C_top_loose, C_top_tight = 2 * math.pi * R_TOP, 2 * math.pi * R_TOP_TIGHT
    return dict(s0=s0, s_end=s_end, pitch_s=pitch_s, rows=rows, cols=cols, C_bot=C_bot, C_top_loose=C_top_loose, C_top_tight=C_top_tight,
                attach_bot=C_bot - 12.0, attach_top=C_top_tight - 9.0,           # 막이 띠에 붙는 끝(그 뒤는 꼬리가 머리를 지나는 구간)
                teeth_bot=(C_bot - 6.0, C_bot + LH + 8.0), teeth_top=(C_top_tight - 6.0, C_top_loose + LH + 8.0), s_c=s0 + n_col * pitch_s / 2)

# ── 매개 좌표 부품 ─────────────────────────────────────────────────────────────
def tile(cs, cy):
    """매개 좌표 타일: 실제 6×6 이 되도록 s 폭을 R_BOT/R(y) 배로. 막 위(z 0.4)부터 1.6, 윗 모서리 0.4 챔퍼(안쪽으로 좁아짐 = 오버행 0)."""
    T, F, H, ch = P['TILE'], P['FILM'], P['TILE_H'], P['TILE_CH']
    k = R_BOT / R(cy); hs, hy = T / 2 * k, T / 2
    lo = box(cs - hs, cs + hs, cy - hy, cy + hy, F - 0.05, F + H - ch)
    top = mf.Manifold.batch_hull([box(cs - hs, cs + hs, cy - hy, cy + hy, F + H - ch, F + H - ch + 0.01),
                                  box(cs - hs + ch * k, cs + hs - ch * k, cy - hy + ch, cy + hy - ch, F + H - 0.01, F + H)])
    return union([lo, top])

def film(L):
    F, BW, EG = P['FILM'], P['BW'], P['EDGE_GAP']; yT = P['Y_TOP']
    y_main = P['Y_FIRST'] - P['TILE_GAP'] / 2                                                   # 본 막은 첫 줄 아래 1.5 부터
    ms = [box(L['s0'], L['s_end'], y_main, yT - BW / 2 - EG, 0, F)]
    for cs in L['cols']:                                                                         # 아래 띠 ~ 본 막: 열마다 막 탭(따로따로 → 턱을 넘을 때 둘레가 늘어나도 됨)
        hs = P['TILE'] / 2 * R_BOT / R(P['Y_FIRST'])
        y0 = BW / 2 - 0.1 if cs + hs <= L['attach_bot'] else BW / 2 + EG                        # 꼬리 구간 열은 띠에 안 붙음
        ms.append(box(cs - hs, cs + hs, y0, y_main + 0.05, 0, F))
    ms += [
          box(L['s0'], L['attach_top'] * K_TOP, yT - BW / 2 - EG - 0.05, yT - BW / 2 + 0.1, 0, F)]   # 위 띠에 붙는 구간(매개 s)
    return union(ms)

def bands(L):
    top = band([], *L['teeth_top'], tab=True).scale([K_TOP, 1, 1]).translate([0, P['Y_TOP'], 0])
    bot = band([], *L['teeth_bot'], tab=False).mirror([0, 1, 0])           # 머리 혀·레일이 캡 쪽(-y), 왼 벽이 천 쪽
    return top, bot

def fabric_param(L):
    ts = [tile(cs, cy) for cy in L['rows'] for cs in L['cols']]
    top, bot = bands(L)
    return union([film(L), mf.Manifold.compose(ts), top, bot]), len(ts)

# ── 굽히기 ──────────────────────────────────────────────────────────────────
def _mf(m): return m if isinstance(m, mf.Manifold) else mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))

def warp_flat(m, L):
    """매개 → 출력 판(원뿔 전개도). θ = (s − s_c)/R_BOT, ρ = ρ_bot − y, φ = θ·sinα → (ρ sinφ + s_c, ρ_bot − ρ cosφ, z)."""
    s_c = L['s_c']
    def f(v):
        s, y, z = v; th = (s - s_c) / R_BOT; rho = RHO_BOT - y; ph = th * SIN_A
        return [rho * math.sin(ph) + s_c, RHO_BOT - rho * math.cos(ph), z]
    return to_tm(_mf(m).refine_to_length(3.0).warp(f))

def warp_wrap(m, L, lift_tail=1.4):
    """매개 → 감은 원뿔(헐거운 상태: 위 띠 = 천 반경). r = R(y) + z + 겹침 오프셋(한 바퀴 넘는 부분: 막 쪽은 판 두께 + 0.4, 띠 꼬리는 터널 높이 1.4)."""
    s_c = L['s_c']; thick = P['FILM'] + P['TILE_H'] + 0.4
    def f(v):
        s, y, z = v; Rv = R(y); th = (s - s_c) / R_BOT
        band_row = (y < P['BW'] / 2 + 0.3) or (y > P['Y_TOP'] - P['BW'] / 2 - 0.3)
        u = (s if band_row else s - L['s0']) * Rv / R_BOT; ramp = 8.0 if band_row else 25.0; lift = lift_tail if band_row else thick
        t = min(max((u - (2 * math.pi * Rv - ramp)) / ramp, 0.0), 1.0); off = lift * t * t * (3 - 2 * t)
        r = Rv + z + off + lip_bump(y) + (0.06 if y < P['BW'] / 2 + 0.3 else 0.0)     # 아래 띠: 홈 바닥 접촉(다각형 근사 현 오차만큼 띄움)
        return [r * math.cos(th), r * math.sin(th), Y0_Z + y]
    return to_tm(_mf(m).refine_to_length(1.2).warp(f))

def lip_bump(y):
    """감은 상태에서 아래 띠 ~ 첫 줄 사이 막 탭이 캡 위 턱(16.41 → 17.41, z 32.4~34.4)을 넘어가는 바깥 오프셋(+0.3 여유)."""
    z = Y0_Z + y; zg, zc, z1 = V1.GROOVE_Z1, V1.CAP_H, Y0_Z + P['Y_FIRST'] - 0.5
    zb = Y0_Z + P['BW'] / 2                                                                     # 띠 윗변
    if z <= zb or z >= z1: return 0.0
    if z <= zg: return 0.3 * (z - zb) / (zg - zb)
    if z <= zc: return 0.3 + (z - zg) / (zc - zg) * (V1.R_0 - R_G)
    t = (z - zc) / (z1 - zc); peak = 0.3 + V1.R_0 - R_G; return peak * (1 - t * t * (3 - 2 * t))

def notch_deg(L): return math.degrees((P['LH'] / 2 - L['s_c']) / R_BOT)

def make_parts():
    L = layout(); fab, n_tiles = fabric_param(L)
    parts = {'fabric': warp_flat(fab, L), 'cap': to_tm(make_cap(notch_deg(L)))}
    lo = parts['fabric'].bounds[0]; parts['fabric'].apply_translation([0, 0, -lo[2]])
    return parts, fab, L, n_tiles

def plate(parts):
    f = parts['fabric'].copy(); lo = f.bounds[0]; f.apply_translation([10.0 - lo[0], 10.0 - lo[1], 0])
    cap = parts['cap'].copy(); cap.apply_translation([f.bounds[1][0] + 12.0 + V1.R_CAP_OUT, 10.0 + V1.R_CAP_OUT, 0])
    return [{'name': 'fabric_case', 'parts': [(f, PRINT_COLOR, 'fabric')]}, {'name': 'cap', 'parts': [(cap, PRINT_COLOR, 'cap')]}]

if __name__ == '__main__':
    os.chdir(PROJ); os.makedirs('models', exist_ok=True)
    nominal, fab, L, n_tiles = make_parts()
    pickle.dump(nominal, open('parts_nominal.pkl', 'wb'))
    printed = {n: pre_expand_first_layer(m) for n, m in nominal.items()}; pickle.dump(printed, open('parts.pkl', 'wb'))
    write_generic_3mf('models/racket-grip-case_A.3mf', plate(printed), 'racket-grip-case')
    top_nat = to_tm(band([], *L['teeth_top'], tab=True))                   # 래칫 검사용(실제 치수, 굽히지 않음)
    pickle.dump({'w_fabric': warp_wrap(fab, L), 'handle': handle_dummy(), 'band_top_nat': top_nat}, open('wrapped.pkl', 'wb'))
    k_bot = (L['pitch_s'] - P['TILE']) ; k_top = (L['pitch_s'] * R_TOP / R_BOT - P['TILE'])
    def strain(gap, pitch, Rv): return P['FILM'] / 2 / (gap / (pitch / Rv))           # 막 굽힘 변형률 = (t/2)/r, r = 틈 / 꺾임각
    meta = dict(n_tiles=n_tiles, n_rows=len(L['rows']), n_cols=len(L['cols']), sheet_s=[L['s0'], L['s_end']], R_bot=R_BOT, R_top=R_TOP,
                rho_bot=RHO_BOT, gap_bottom=round(k_bot, 2), gap_top=round(k_top, 2),
                film_strain_pct={'bottom': round(100 * strain(k_bot, L['pitch_s'], R_BOT), 2), 'top_loose': round(100 * strain(k_top, L['pitch_s'] * R_TOP / R_BOT, R_TOP), 2),
                                 'top_tight': round(100 * strain(k_top, L['pitch_s'] * R_TOP / R_BOT, R_TOP_TIGHT), 2)},
                notch_deg=round(notch_deg(L), 1), extents={n: [round(v, 2) for v in m.extents] for n, m in nominal.items()},
                volume_cm3={n: round(m.volume / 1000, 2) for n, m in nominal.items()})
    json.dump(meta, open('build_meta.json', 'w'), ensure_ascii=False, indent=1)
    print('build ok', json.dumps(meta, ensure_ascii=False))
