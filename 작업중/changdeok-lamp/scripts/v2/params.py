"""인정전 램프 v2 — 치수표 (단위 mm, 1:150, 기준면 z=0 = 월대 윗면). 실측 출처: refs/dims (DWG 치수선 + 스캔 정합), 추정값은 '추정' 표기."""
K = 1000/150.0                      # m → mm
# ---- 실측 (DWG DIMENSION) ----
BAYS_X = [4.5945, 4.5844, 6.1244, 4.5875, 4.5583]      # 정면 5칸 (m)
BAYS_Y = [3.0364, 4.4565, 4.6171, 3.2958]              # 측면 4칸 (m)
UPPER_INSET_X = 1.52                                   # 상층 외곽 기둥 들여쓰기(정면) m
UPPER_SPAN_Y = 9.170                                   # 상층 측면 폭 m (77983→87153)
H_LOWER_COL_TOP = 4.651; H_LOWER_PLATE_TOP = 5.181     # 하층 창방 밑 / 평방 위 (m)
H_UPPER_COL_TOP = 10.706; H_UPPER_PLATE_TOP = 11.239   # 상층 창방 밑 / 평방 위
H_RIDGE = 21.182                                       # 용마루 위
EAVE_PROJ_LOWER_X = 4.40; EAVE_PROJ_LOWER_Y = 3.83     # 하층 처마 내밀기(정면: 스캔 실루엣, 측면: 치수 23066.7)
EAVE_PROJ_UPPER = 4.50                                 # 상층 처마 내밀기(스캔 비 0.916, 추정 ±0.3)
RIB_PITCH = 0.335; RAFTER_PITCH = 0.335                # 수키와 골·서까래 피치(스캔 자기상관)
# ---- 램프 치수 (mm) ----
SPAN_X = sum(BAYS_X)*K; SPAN_Y = sum(BAYS_Y)*K         # 163.0 × 102.7 (기둥 중심)
EAVE_LX = SPAN_X + 2*EAVE_PROJ_LOWER_X*K               # 221.6
EAVE_LY = SPAN_Y + 2*EAVE_PROJ_LOWER_Y*K               # 153.8
USPAN_X = SPAN_X - 2*UPPER_INSET_X*K                   # 142.7
USPAN_Y = UPPER_SPAN_Y*K                               # 61.1
EAVE_UX = USPAN_X + 2*EAVE_PROJ_UPPER*K                # 202.7
EAVE_UY = USPAN_Y + 2*4.0*K                            # 114.4 (측면 내밀기 4.0 추정)
# 높이(mm, 월대 윗면 기준). 창방·평방은 실측, 그 사이 띠 높이는 사진 비례(추정)
Z_LOWER_WALL_TOP = H_LOWER_COL_TOP*K                   # 31.0 창방 밑
LOWER_BEAM = 2.4                                       # 창방(벽 판 위 가로대) 두께, 그 위 평방 링
RING_T = 2.0                                           # 평방 링 두께 → 윗면 34.5 ≈ 5.18 m
BAND_H = 8.0; BAND_STEP = 2.0; BAND_TIERS = 3           # 공포 띠 높이(1.2 m)·단 돌출
BRACKET_PITCH = 1.53*K                                  # 포간 10.2 mm (칸 4.59 m 에 주간포 2)
LOWER_ROOF_SLOPE_DEG = 24.0; UPPER_ROOF_SLOPE_DEG = 38.8
SOFFIT_T = 2.2; LINE_T = 0.8; TOOTH = 1.0; TOOTH_PITCH = RAFTER_PITCH*K   # 처마: 서까래 끝 1.0 각, 피치 2.23
RIB_W = 1.0; RIB_H = 0.6; RIB_PITCH_MM = RIB_PITCH*K    # 수키와 골 1.0×0.6, 피치 2.23
MAKSAE_D = 1.6
CORNER_RISE = 5.0; CORNER_FRAC = 0.28                   # 앙곡: 모서리 들림, 변 길이의 28 % 구간
COL_D = 4.8                                             # 하층 기둥 지름(부조 반원), 실제 0.6 m×K=4.0 → 과장 1.2
UCOL_D = 4.0
WALL_BASE = 0.6                                         # 흰 바탕판(빛 통과)
CLR = 0.3
# 월대
PLAT_UP = (SPAN_X + 2*1.47*K, SPAN_Y + 2*1.47*K, 3.5)   # 상단 월대 (183 × 122 × 3.5)
PLAT_LO = (SPAN_X + 2*3.5*K, SPAN_Y + 2*3.5*K, 16.5)    # 하단 월대 (210 × 149 × 16.5) — 높이는 LED 퍽 자리 때문에 과장
APRON_Y = 24.0                                          # 정면 하월대 앞치마(계단 자리)
STEP_RISE = 1.4; STEP_TREAD = 2.0                       # 계단 한 단 (실제 0.17/0.3 m → 1.1/2.0, 층 7개)
LED_D = 59; LED_H = 18; LED_CLR = 0.5; CABLE_W = 6; CABLE_H = 5
