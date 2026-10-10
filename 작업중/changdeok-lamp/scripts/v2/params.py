"""인정전 램프 v2 — 치수표 (단위 mm, 1:150, 기준면 z=0 = 월대 윗면). 실측 출처: refs/dims (DWG 치수선 + 스캔 정합), 추정값은 '추정' 표기."""
K = 1000/150.0                      # m → mm
# ---- 실측 (DWG DIMENSION) ----
BAYS_X = [4.5945, 4.5844, 6.1244, 4.5875, 4.5583]      # 정면 5칸 (m)
BAYS_Y = [4.5842, 4.5807, 4.5878, 4.5917]              # 하층 측면 4칸 (m, 앞→뒤) — 측면도 아래 치수 줄 18344.4 (73391→91736)
UBAYS_X = [3.0582, 4.5844, 6.1244, 4.5875, 3.0484]     # 상층 정면 5칸 (정면도 위 치수 줄, 하층 기둥에서 1536.3/1509.9 들어감)
UBAYS_Y = [3.0364, 4.6171, 4.4565, 3.2958]             # 상층 측면 4칸 15405.8 (측면도 위 치수 줄, 하층 기둥에서 1392/1547 들어감)
UPPER_INSET_X = 1.52                                   # 상층 외곽 기둥 들여쓰기(정면) m
UPPER_SPAN_Y = sum(UBAYS_Y)                            # 상층 측면 폭 15.406 m (이전 9.17 은 평면도 고주 2칸을 잘못 읽은 값)
H_LOWER_COL_TOP = 4.651; H_LOWER_PLATE_TOP = 5.181     # 하층 창방 밑 / 평방 위 (m)
H_UPPER_COL_TOP = 10.706; H_UPPER_PLATE_TOP = 11.239   # 상층 창방 밑 / 평방 위
H_RIDGE = 21.182                                       # 용마루 위
EAVE_PROJ_LOWER_X = 3.82; EAVE_PROJ_LOWER_Y = 3.83     # 하층 처마 내밀기(정면: 스캔 실루엣, 측면: 치수 23066.7)
EAVE_PROJ_UPPER = 4.15                                 # 상층 처마 내밀기 정면(스캔 실루엣 정합)
EAVE_PROJ_UPPER_Y = 4.15                               # 상층 처마 내밀기 측면(측면 스캔 실루엣 정합)
RIB_PITCH = 0.335; RAFTER_PITCH = 0.335                # 수키와 골·서까래 피치(스캔 자기상관)
# ---- 램프 치수 (mm) ----
SPAN_X = sum(BAYS_X)*K; SPAN_Y = sum(BAYS_Y)*K         # 163.0 × 122.3 (하층 기둥 중심)
PLAN_CURVE_OLD = 6.0                                   # 이전 모서리 밀기(정면·측면 실루엣 정합 기준) — 모서리 위치 유지용
PLAN_CURVE_RATIO = 0.0436                              # 안허리곡: 변 가운데가 모서리보다 들어간 양 / 변 반길이 (평면 스캔 앞변 12.5 px / 287 px)
PLAN_CURVE_P = 2.7                                     # 들어간 양 ∝ (변 위치 t)^2.7 (평면 스캔 7점 맞춤, 평균 오차 0.059)
RIDGE_RISE = 2.2; RIDGE_RISE_AT = 56.0                 # 용마루 휨: 가운데 141.0 → |x|=56 에서 143.2 (정면 스캔), 2.2·(x/56)²
EAVE_LX0 = SPAN_X + 2*EAVE_PROJ_LOWER_X*K              # 213.9 (안허리곡 전 직사각)
EAVE_LY0 = SPAN_Y + 2*EAVE_PROJ_LOWER_Y*K              # 173.4
USPAN_X = SPAN_X - 2*UPPER_INSET_X*K                   # 142.7
USPAN_Y = UPPER_SPAN_Y*K                               # 102.7
EAVE_UX0 = USPAN_X + 2*EAVE_PROJ_UPPER*K               # 198.0
EAVE_UY0 = USPAN_Y + 2*EAVE_PROJ_UPPER_Y*K             # 158.0
# 안허리곡을 변 전체로 바꿔도 모서리(스캔 실루엣 정합점)는 그대로: 변 가운데 = 모서리 − 비율×반길이
_k = lambda ex, ey: (ex + 2*(PLAN_CURVE_OLD - PLAN_CURVE_RATIO*ey/2), ey + 2*(PLAN_CURVE_OLD - PLAN_CURVE_RATIO*ex/2))
EAVE_LX, EAVE_LY = _k(EAVE_LX0, EAVE_LY0)               # 218.4 × 176.0 (변 가운데), 모서리 225.9 × 185.4 그대로
EAVE_UX, EAVE_UY = _k(EAVE_UX0, EAVE_UY0)               # 203.2 × 161.4, 모서리 210.2 × 170.4
# 높이(mm, 월대 윗면 기준). 창방·평방은 실측, 그 사이 띠 높이는 사진 비례(추정)
Z_LOWER_WALL_TOP = H_LOWER_COL_TOP*K                   # 31.0 창방 밑
LOWER_BEAM = 2.4                                       # 창방(벽 판 위 가로대) 두께, 그 위 평방 링
RING_T = 2.0                                           # 평방 링 두께 → 윗면 34.5 ≈ 5.18 m
BAND_H = 8.0; BAND_STEP = 2.0; BAND_TIERS = 3           # 공포 띠 높이(1.2 m)·단 돌출
BRACKET_PITCH = 1.53*K                                  # 포간 10.2 mm (칸 4.59 m 에 주간포 2)
LOWER_ROOF_SLOPE_DEG = 24.0; UPPER_ROOF_SLOPE_DEG = 38.8
EAVE_PITCH = 2.8                                        # 서까래·수키와 공통 피치(실제 0.335 m=2.23 → 과장 1.25배, SKP 모델도 서까래를 크게·성기게 그림)
SOFFIT_T = 5.0; LINE_T = 1.0; TOOTH_PITCH = EAVE_PITCH  # 처마밑 두께, 흰 처마선 두께
RAFTER_D = 2.2; RAFTER_OUT = 0.6; RAFTER_RAMP = 1.8     # 둥근 서까래 마구리(SKP): 지름 2.2·틈 0.6, 처마 면에서 0.6 돌출(0.4 묻힘), 윗면 경사 깊이 1.0/높이 1.8(뒤집어 출력 시 층당 0.111)
RIB_W = 1.2; RIB_H = 0.6; RIB_PITCH_MM = EAVE_PITCH     # 수키와 골 1.2×0.6, 서까래와 같은 피치(SKP: 막새 줄과 서까래 줄이 같은 간격)
MAKSAE_D = 2.0
CORNER_RISE = 1.5; CORNER_FRAC = 0.28                   # 앙곡: 모서리 들림, 변 길이의 28 % 구간
COL_D = 4.8                                             # 하층 기둥 지름(부조 반원), 실제 0.6 m×K=4.0 → 과장 1.2
UCOL_D = 4.0
WALL_BASE = 1.2                                         # 창호틀 판(갈색, 창 부분 뚫림) 두께 — 흰 발광 통은 안쪽에 따로
CLR = 0.3
# 월대
PLAT_UP = (SPAN_X + 2*1.47*K, SPAN_Y + 2*1.47*K, 3.5)   # 상단 월대 (183 × 122 × 3.5)
PLAT_LO = (SPAN_X + 2*3.5*K, SPAN_Y + 2*3.5*K, 19.0)    # 하단 월대 (210 × 149 × 19) — 높이는 LED 퍽(18) 자리 때문에 과장
APRON_Y = 24.0                                          # 정면 하월대 앞치마(계단 자리)
STEP_RISE = 1.4; STEP_TREAD = 2.0                       # 계단 한 단 (실제 0.17/0.3 m → 1.1/2.0, 층 7개)
LED_D = 59; LED_H = 18; LED_CLR = 0.5; CABLE_W = 6; CABLE_H = 5

# ---- 조립 높이 (mm, 월대 윗면 z=0). 측면 스캔(정합 일치: 5000×2422 원본 = 2000×969 사본) 기준 ----
FLOOR_T = 3.0; FLOOR_Z0 = -1.0                         # 하층 바닥판 z -1~2 (월대 홈 1)
LOWER_WALL_H = 33.4                                    # 벽 판 높이(창방 포함) → 윗면 35.4 (실측 평방 34.5)
RING_W_OUT = 3.6; RING_W_IN = 2.7                      # 평방 링: 중심선 바깥 3.6, 안 2.7 (밑면 홈 −1.5~+2.6 안쪽에 1.2 턱을 남겨 홈 천장을 양쪽 지지 브리지로)
LIP_W = 1.6; LIP_H = 1.5                               # 벽 안쪽 위치 턱
RIM_IN = 1.5; RIM_OUT = 0.4                            # 림: 중심선 안 2.0 ~ 바깥 0.4
LOWER_BAND_H = 8.0; UPPER_BAND_H = 8.0
LOWER_ROOF_RISE = 12.8                                 # 하층 지붕 처마(7.0 m)→상층 바닥(9.9 m) = 2.9 m
UPPER_GABLE = (137.0, 14.0, 50.8)                        # 용마루 길이, 합각 밑 높이, 용마루 높이(기와 시작 기준)
EAVE_RISE = 3.0                                        # 처마선 들림(모서리 끝): 정면 스캔 처마 끝선 u=-69 → 끝 +3.0 mm, 창경궁 SKP 도 서까래·기와 끝 줄이 모서리로 들림
RISE_T0 = 0.55                                         # 들림 시작: 변 반길이의 55 % 부터 (t−0.55)/0.45 의 제곱 (스캔: u=-69 까지 거의 0)
SAG_LOWER = 1.5; SAG_UPPER = 3.0                       # 지붕면 오목 곡(가운데 처짐)
WARP_EDGE = 6.5
TILE_BASE = 0.6                                        # 기와 밑판(흰 테 위) 두께 → 기와 시작 z_t = z0+SOFFIT_T+LINE_T+TILE_BASE
SOFFIT_RISE = 4.0                                      # 처마밑 밑면 모서리 들림(뒤집어 출력하므로 윗면 쪽에서 변형)
RING_BAND = 10.0                                       # 흰 처마선 테 폭(바깥 1 mm 만 보임)
DOWEL_D = 2.0; DOWEL_DEPTH = 2.0                       # 1.75 필라멘트 핀 구멍
FIT = 0.2                                              # 끼움 여유(한쪽)
DIFFUSER_T = 0.8; DIFFUSER_GAP = 0.3                   # 안쪽 흰 발광 통(일본 랜턴 샘플 방식 단일 벽)
GABLE_T = 2.0; GABLE_IN = 1.2                          # 합각 널 두께 2.0 중 1.2 를 기와 포켓(+0.2 여유)에 끼움
CHUNYEO_W = 3.0; CHUNYEO_OUT = 1.8                     # 추녀 끝(창경궁 SKP 모서리 세로 각재): 폭 3.0, 처마 모서리 밖으로 1.8(대각) 돌출
