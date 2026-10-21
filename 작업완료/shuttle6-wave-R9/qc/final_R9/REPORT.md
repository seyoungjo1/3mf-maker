# Shuttle6 C R9 / 입구45도부터 즉시 곡률→끝30도·브리지4mm / 몸통2분할 — 파이프라인 보고

## 1. QC — 출력 방향 파트 (EFC 0.15 반영, 출력물 기준)

| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| shell_lower | 64,396 | O | 1 | 82.0×82.0×131.5 | 198.4 | 5397.3 / 5397.3 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| shell_upper | 52,560 | O | 1 | 82.3×82.3×121.5 | 172.8 | 883.4 / 883.4 | 0.0 | 0.0 | 7.5 (4.0) | ✓ |
| drawer | 124,250 | O | 1 | 85.95×86.0×249.8 | 185.6 | 4519.7 / 4519.7 | 0.0 | 19.5 | 2631.4 (4.4) | ✓ |
| shell_coupon | 3,608 | O | 1 | 82.3×82.3×36.0 | 53.7 | 1286.0 / 1286.0 | 0.0 | 0.0 | 7.8 (4.1) | ✓ |
| drawer_coupon | 17,956 | O | 1 | 85.95×86.0×42.0 | 85.9 | 5989.7 / 5989.7 | 0.0 | 11.1 | 0.0 (0.0) | ✓ |
| tip_coupon | 18,640 | O | 1 | 75.7×38.0×9.8 | 25.6 | 1899.8 / 1904.1 | 0.0 | 1.6 | 222.2 (4.4) | ✓ |

오버행 상위 위치: drawer: z=30.11 11.1 mm² [38.8, -4.0, 40.2, 4.0]; z=45.51 3.9 mm² [35.6, -2.0, 37.7, 0.0] / drawer_coupon: z=30.11 11.1 mm² [38.8, -4.0, 40.2, 4.0]

브리지 상위 위치(z, mm², 폭): shell_upper: z=106.91 7.5 mm² 폭 4.0 / drawer: z=0.71 1591.1 mm² 폭 1.7; z=227.51 10.0 mm² 폭 2.6; z=228.51 10.0 mm² 폭 3.7; z=229.31 10.0 mm² 폭 3.4 / shell_coupon: z=21.31 7.8 mm² 폭 4.1 / tip_coupon: z=0.31 8.7 mm² 폭 3.0; z=0.51 7.7 mm² 폭 2.4; z=0.91 7.5 mm² 폭 3.1; z=0.71 7.4 mm² 폭 2.3

얇은 살 위치: 

## 2. 플레이트 3MF — 충돌·베드·lib3mf strict

| 플레이트 | 파트 | 범위 x / y (mm) | 충돌 | strict 경고 | 판정 |
|---|---|---|---|---|---|
| P01_body_pair.3mf | shell_lower, shell_upper | 31~225 / 87~169 | 0 | 0 | ✓ |
| P02_drawer.3mf | drawer | 85~171 / 85~171 | 0 | 0 | ✓ |
| P03_shell_coupon.3mf | shell_coupon | 87~169 / 87~169 | 0 | 0 | ✓ |
| P04_drawer_coupon.3mf | drawer_coupon | 85~171 / 85~171 | 0 | 0 | ✓ |
| P05_tip_coupon.3mf | tip_coupon | 90~166 / 109~147 | 0 | 0 | ✓ |

## 3. 조립 검증 — 상태별 교집합·간격 (표면 샘플 거리: 최소 / 1 % / 5 %)

| 상태 | A | B | 교집합 mm³ | 최소 / 1 % / 5 % mm | 판정 |
|---|---|---|---|---|---|
| 닫힘 | shell | drawer | 0.00 | 0.00 / 0.00 / 0.30 | 접촉(의도) |
| 걸쇠 누름 | shell | drawer_pressed | 0.00 | 0.00 / 0.00 / 0.30 | 접촉(의도) |
| 인출 0mm | shell | drawer_pressed | 0.00 | 0.00 / 0.00 / 0.30 | 접촉(의도) |
| 인출 5mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 10mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 20mm | shell | drawer_pressed | 0.00 | 0.27 / 0.30 / 0.30 | 접촉(의도) |
| 인출 40mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 60mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 80mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 100mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 120mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 140mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 160mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 2.30 | 접촉(의도) |
| 인출 180mm | shell | drawer_pressed | 0.00 | 0.30 / 0.30 / 5.53 | 접촉(의도) |
| 인출 200mm | shell | drawer_pressed | 0.00 | 0.30 / 0.93 / 7.37 | 접촉(의도) |
| 인출 220mm | shell | drawer_pressed | 0.00 | 0.30 / 1.26 / 9.08 | 접촉(의도) |
| 인출 236mm | shell | drawer_pressed | 0.00 | 0.30 / 1.05 / 13.54 | 접촉(의도) |
| 열림 | shell | drawer | 0.00 | 0.30 / 1.72 / 14.03 | 접촉(의도) |
| 분리 | shell | drawer | 0.00 | 16.34 / 26.86 / 44.47 | 접촉(의도) |
| 몸통 접착 | shell_lower | shell_upper | 0.00 | 0.00 / 0.00 / 0.30 | 접촉(의도) |
| 수납 여유 | drawer | clearance | 0.00 | 0.00 / 0.00 / 7.95 | 접촉(의도) |
| 내용물 누름 | drawer_pressed | contents | 0.00 | 0.00 / 0.00 / 8.97 | 접촉(의도) |
| 시험편 닫힘 | shell_coupon | drawer_coupon | 0.00 | 0.00 / 0.00 / 0.00 | 접촉(의도) |
| 시험편 해제 | shell_coupon | coupon_pressed | 0.00 | 0.00 / 0.00 / 0.00 | 접촉(의도) |

- 몸통은 가로 분할. 하단131.5mm / 상단121.5mm, 겹침턱10mm·반경 접착 틈0.30mm. 접착제가 경화된 뒤 사용.
- 해제하지 않고3mm 강제 인출 시 걸림 교집합 1.31mm³.
- 가상 여유 외피 교집합: {'drawer_vs_clearance_mm3': 0.0, 'shell_vs_clearance_mm3': 0.0, 'scope': 'Assumed six-stack envelope225mm, featherD68/baseD28/length85/pitch28; offset1.5mm, clipped only at front resting face. Not measured brand fit.', 'sampled_surface_distance_mm_not_min_clearance': (10.355755041081693, 10.371901157596131, 11.558040868395697)}. 실제 브랜드·출력 반복 내구 검증 전.
- 새 콘: 시작부터45→30도 연속 곡면·외부 채움. 끝 접선45→30도(베드 기준), 개구71.4→4mm, 마지막4mm 브리지. 걸쇠 턱z30·슬롯 끝z45.5에 작은 서포트.
- 30.5×3×8 스프링·누름1.5mm·뿌리 아래3.5mm. 이론 선형 근사이며 정격 파손 힘·피로 수명·비틀림 내력 아님.

## 4. 렌더 (CPU flat-shaded mesh, 5뷰 + 회전 GIF + 작동 GIF)

- 플레이트 `P01_body_pair.3mf`: `qc/final_R9/plate_P01_body_pair/view_*.png`, `turntable.gif`
- 플레이트 `P02_drawer.3mf`: `qc/final_R9/plate_P02_drawer/view_*.png`, `turntable.gif`
- 플레이트 `P03_shell_coupon.3mf`: `qc/final_R9/plate_P03_shell_coupon/view_*.png`, `turntable.gif`
- 플레이트 `P04_drawer_coupon.3mf`: `qc/final_R9/plate_P04_drawer_coupon/view_*.png`, `turntable.gif`
- 플레이트 `P05_tip_coupon.3mf`: `qc/final_R9/plate_P05_tip_coupon/view_*.png`, `turntable.gif`
- 조립 상태(분리/닫힘/열림…): `qc/final_R9/assembly/view_*_<상태>.png`, `turntable.gif`

## 5. 판정

- ✓ 경고 없음 — 보낼 수 있음
