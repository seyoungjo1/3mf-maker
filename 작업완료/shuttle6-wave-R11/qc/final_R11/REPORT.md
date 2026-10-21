# Shuttle6 C R11 / open ID64 / flat horizontal tray / separate cap / rounded detents — 파이프라인 보고

## 1. QC — 출력 방향 파트 (EFC 0.15 반영, 출력물 기준)

| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| shell_lower | 64,520 | O | 1 | 78.2×78.2×135.5 | 224.8 | 4867.2 / 4867.2 | 5.2 | 0.0 | 0.0 (0.0) | ℹ 얇은 살 허용: 키 선단1mm 삽입 유도면의 국부 모서리: 실제 QC5.2mm²,z135.2. 독립 벽/탄성 암이 아니며 뒤쪽 연속 collar 벽은 선단에서도1.85mm 이상, 축부2.20mm·키 폭8mm·길이14mm. 어깨부/키 뿌리는 깎지 않았고 선단의 작은 형상만 허용. 실제 강도 미검증. |
| shell_upper | 49,012 | O | 1 | 78.5×78.5×121.5 | 193.8 | 916.1 / 916.1 | 0.0 | 0.0 | 75.9 (4.9) | ✓ |
| drawer | 39,190 | O | 1 | 222.74×222.74×32.69 | 111.7 | 5798.1 / 5910.8 | 0.0 | 4610.4 | 0.0 (0.0) | ℹ 서포트: 눕힌 보강 내관: 바닥 평면 양옆 둥근 전이부와 둥근 돌기 아래. 실제 QC 누적4610.4mm²; 트리 지지 대상이며 완전 무서포트가 아님. |
| cap | 110,274 | O | 1 | 82.2×82.2×10.0 | 66.2 | 4083.8 / 4083.8 | 0.0 | 0.0 | 1460.0 (2.9) | ✓ |
| shell_coupon | 4,146 | O | 1 | 78.5×78.5×36.0 | 61.7 | 1453.4 / 1453.4 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| drawer_coupon | 1,580 | O | 1 | 75.8×75.8×32.69 | 12.8 | 902.5 / 919.9 | 0.0 | 713.1 | 0.0 (0.0) | ℹ 서포트: 눕힌 내관 시험편 바닥 양옆 전이부와 돌기 아래. 실제 QC 누적713.1mm². |
| tip_coupon | 16,460 | O | 1 | 55.86×55.86×32.6 | 20.9 | 238.1 / 242.6 | 0.0 | 180.0 | 0.0 (0.0) | ℹ 서포트: 눕힌 콘끝 시험편 바닥 양옆 전이부. 실제 QC 누적180.0mm². |

오버행 상위 위치: drawer: z=0.31 224.6 mm² [-6.0, -185.4, 185.4, 6.0]; z=0.51 192.3 mm² [-6.3, -185.8, 185.8, 6.3]; z=0.71 183.5 mm² [-6.7, -186.1, 186.1, 6.7]; z=0.91 170.3 mm² [-7.0, -186.5, 186.5, 7.0] / drawer_coupon: z=0.31 34.7 mm² [-6.0, -38.5, 38.5, 6.0]; z=0.51 29.7 mm² [-6.3, -38.8, 38.8, 6.3]; z=0.71 28.4 mm² [-6.7, -39.2, 39.2, 6.7]; z=0.91 26.3 mm² [-7.0, -39.5, 39.5, 7.0] / tip_coupon: z=0.31 9.0 mm² [-8.8, -15.7, 15.7, 8.8]; z=0.51 7.7 mm² [-9.1, -16.1, 16.1, 9.1]; z=0.71 7.3 mm² [-9.5, -16.4, 16.4, 9.5]; z=0.91 6.8 mm² [-9.8, -16.7, 16.7, 9.8]

브리지 상위 위치(z, mm², 폭): shell_upper: z=14.31 8.4 mm² 폭 4.9; z=14.51 4.5 mm² 폭 1.8; z=14.71 4.5 mm² 폭 2.6; z=14.91 4.4 mm² 폭 2.6 / cap: z=0.71 1457.1 mm² 폭 1.6; z=7.71 2.8 mm² 폭 2.9

얇은 살 위치: shell_lower: 5.2 mm² z=135.2 [23.3, 23.3, 29.4, 29.4]

## 2. 플레이트 3MF — 충돌·베드·lib3mf strict

| 플레이트 | 파트 | 범위 x / y (mm) | 충돌 | strict 경고 | 판정 |
|---|---|---|---|---|---|
| P01_body_pair.3mf | shell_lower, shell_upper | 33~223 / 89~167 | 0 | 0 | ✓ |
| P02_horizontal_tray.3mf | drawer | 17~239 / 17~239 | 0 | 0 | ✓ |
| P03_separate_cap.3mf | cap | 87~169 / 87~169 | 0 | 0 | ✓ |
| P04_detent_shell_coupon.3mf | shell_coupon | 89~167 / 89~167 | 0 | 0 | ✓ |
| P05_detent_tray_coupon.3mf | drawer_coupon | 90~166 / 90~166 | 0 | 0 | ✓ |
| P06_tip_coupon.3mf | tip_coupon | 100~156 / 100~156 | 0 | 0 | ✓ |

## 3. 조립 검증 — 상태별 교집합·간격 (표면 샘플 거리: 최소 / 1 % / 5 %)

| 상태 | A | B | 교집합 mm³ | 최소 / 1 % / 5 % mm | 판정 |
|---|---|---|---|---|---|
| 닫힘 | shell | drawer | 0.00 | 0.20 / 0.30 / 0.30 | 접촉(의도) |
| 닫힘 | shell | cap | 0.00 | 0.00 / 0.00 / 0.00 | 접촉(의도) |
| 닫힘 | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 0.5mm | shell | drawer_compressed | 0.00 | 0.19 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 0.5mm | shell | cap | 0.00 | 0.50 / 0.50 / 0.50 | 접촉(의도) |
| 딸깍 통과 0.5mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 1mm | shell | drawer_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 1mm | shell | cap | 0.00 | 1.00 / 1.00 / 1.00 | 접촉(의도) |
| 딸깍 통과 1mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 2mm | shell | drawer_compressed | 0.00 | 0.22 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 2mm | shell | cap | 0.00 | 2.00 / 2.00 / 2.00 | 접촉(의도) |
| 딸깍 통과 2mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 5mm | shell | drawer_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 5mm | shell | cap | 0.00 | 5.00 / 5.02 / 5.11 | 접촉(의도) |
| 딸깍 통과 5mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 8mm | shell | drawer_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 8mm | shell | cap | 0.00 | 8.00 / 8.01 / 8.07 | 접촉(의도) |
| 딸깍 통과 8mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 10mm | shell | drawer_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 10mm | shell | cap | 0.00 | 10.00 / 10.01 / 10.06 | 접촉(의도) |
| 딸깍 통과 10mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 14mm | shell | drawer | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 14mm | shell | cap | 0.00 | 14.00 / 14.01 / 14.05 | 접촉(의도) |
| 인출 14mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 40mm | shell | drawer | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 40mm | shell | cap | 0.00 | 40.00 / 40.00 / 40.01 | 접촉(의도) |
| 인출 40mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 80mm | shell | drawer | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 80mm | shell | cap | 0.00 | 80.00 / 80.00 / 80.01 | 접촉(의도) |
| 인출 80mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 120mm | shell | drawer | 0.00 | 0.30 / 0.30 / 0.41 | 접촉(의도) |
| 인출 120mm | shell | cap | 0.00 | 120.00 / 120.00 / 120.00 | 접촉(의도) |
| 인출 120mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 180mm | shell | drawer | 0.00 | 0.30 / 0.30 / 5.72 | 접촉(의도) |
| 인출 180mm | shell | cap | 0.00 | 180.00 / 180.00 / 180.00 | 접촉(의도) |
| 인출 180mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 236mm | shell | drawer | 0.00 | 0.30 / 1.44 / 11.09 | 접촉(의도) |
| 인출 236mm | shell | cap | 0.00 | 236.00 / 236.00 / 236.00 | 접촉(의도) |
| 인출 236mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 열림 | shell | drawer | 0.00 | 0.30 / 1.08 / 11.06 | 접촉(의도) |
| 열림 | shell | cap | 0.00 | 236.00 / 236.00 / 236.00 | 접촉(의도) |
| 열림 | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 분리 | shell | drawer | 0.00 | 16.38 / 22.81 / 38.07 | 접촉(의도) |
| 분리 | shell | cap | 0.00 | 256.24 / 256.50 / 257.46 | 접촉(의도) |
| 분리 | drawer | cap | 0.00 | 14.00 / 14.06 / 14.60 | 접촉(의도) |
| 몸통 접착 | shell_lower | shell_upper | 0.00 | 0.00 / 0.00 / 0.30 | 접촉(의도) |
| 뚜껑 끼움 전 | drawer | cap | 0.00 | 9.00 / 9.07 / 9.81 | 접촉(의도) |
| 뚜껑 끼움 완료 | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 64 공칭 게이지 | drawer | contents | 0.00 | 0.25 / 2.34 / 10.78 | 접촉(의도) |
| 딸깍 시험편 닫힘 | shell_coupon | drawer_coupon | 0.00 | 0.25 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 시험편 통과 | shell_coupon | coupon_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |

- R11: Open nominal ID64, flat lower plane and2.6mm floor. Feather compliance is not modelled as rigid plastic.
- Tray prints horizontally on diagonal; cap separately face down. Body only2pieces upright.
- Long clip and release button removed; two integrated round beads meet matching inner-shell pockets. Pull-through feel only, no rated positive lock.
- Bead crossing poses use a geometrically compressed bead for collision checks; this is a kinematic representation, not FEA or force validation.
- Actual dimensional/closed joint overlaps: {'drawer_vs_dimensional_gauge_mm3': 0.0, 'shell_vs_dimensional_gauge_mm3': 0.0, 'cap_joint_overlap_mm3': 0.0, 'detent_crossing_without_compliance': [{'extraction_mm': 0, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 0.25, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 0.5, 'rigid_overlap_mm3': 0.06330501824573768}, {'extraction_mm': 0.75, 'rigid_overlap_mm3': 0.33099677410226985}, {'extraction_mm': 1, 'rigid_overlap_mm3': 0.6530186215914568}, {'extraction_mm': 1.5, 'rigid_overlap_mm3': 1.23819207143913}, {'extraction_mm': 2, 'rigid_overlap_mm3': 1.601793075464684}, {'extraction_mm': 3, 'rigid_overlap_mm3': 1.7045807754001696}, {'extraction_mm': 5, 'rigid_overlap_mm3': 1.704582016379921}, {'extraction_mm': 8, 'rigid_overlap_mm3': 1.704584144943927}, {'extraction_mm': 10, 'rigid_overlap_mm3': 0.8522908562589843}, {'extraction_mm': 12, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 14, 'rigid_overlap_mm3': 0.0}], 'glue_key_rotation_checks': [{'angle_deg': 0, 'solid_overlap_mm3': 0.0}, {'angle_deg': -0.5, 'solid_overlap_mm3': 2.669155618912763}, {'angle_deg': 0.5, 'solid_overlap_mm3': 2.669156927246263}, {'angle_deg': -1, 'solid_overlap_mm3': 6.383907867075455}, {'angle_deg': 1, 'solid_overlap_mm3': 6.383907452804654}, {'angle_deg': -3, 'solid_overlap_mm3': 19.980082778048352}, {'angle_deg': 3, 'solid_overlap_mm3': 19.980082377780793}, {'angle_deg': 90, 'solid_overlap_mm3': 79.19498414670063}], 'glue_joint_measured': {'collar_wall_mm': 2.2000007547093503, 'radial_gap_mm': 0.14999962232591457, 'key_tip_gap_mm': 0.14999962232591457, 'key_side_gap_mm': 0.10000082734596782, 'key_width_mm': 7.999998918996401}, 'glue_joint_axial_insertion_checks': [{'remaining_insertion_mm': 0, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 2, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 5, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 10, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 14, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 16, 'overlap_mm3': 0.0}], 'scope': 'Nominal64mm dimensional gauge offset upward2mm over flat floor,6 nested225mm assumption. Not a measured feather envelope or deformation/contact simulation. Rounded beads have intentional elastic crossing; click force not calculated.'}.
- Cap has6mm U-shaped keyed insertion and0.2mm per-side clearance; retention/friction must be checked physically.

## 4. 렌더 (CPU flat-shaded mesh, 5뷰 + 회전 GIF + 작동 GIF)

- 플레이트 `P01_body_pair.3mf`: `qc/final_R11/plate_P01_body_pair/view_*.png`, `turntable.gif`
- 플레이트 `P02_horizontal_tray.3mf`: `qc/final_R11/plate_P02_horizontal_tray/view_*.png`, `turntable.gif`
- 플레이트 `P03_separate_cap.3mf`: `qc/final_R11/plate_P03_separate_cap/view_*.png`, `turntable.gif`
- 플레이트 `P04_detent_shell_coupon.3mf`: `qc/final_R11/plate_P04_detent_shell_coupon/view_*.png`, `turntable.gif`
- 플레이트 `P05_detent_tray_coupon.3mf`: `qc/final_R11/plate_P05_detent_tray_coupon/view_*.png`, `turntable.gif`
- 플레이트 `P06_tip_coupon.3mf`: `qc/final_R11/plate_P06_tip_coupon/view_*.png`, `turntable.gif`
- 조립 상태(분리/닫힘/열림…): `qc/final_R11/assembly/view_*_<상태>.png`, `turntable.gif`

## 5. 판정

- ℹ shell_lower: 1.2 mm 보다 얇은 살 5.2 mm² (z=135.2, x/y (23.3, 23.3, 29.4, 29.4)) → 허용(키 선단1mm 삽입 유도면의 국부 모서리: 실제 QC5.2mm²,z135.2. 독립 벽/탄성 암이 아니며 뒤쪽 연속 collar 벽은 선단에서도1.85mm 이상, 축부2.20mm·키 폭8mm·길이14mm. 어깨부/키 뿌리는 깎지 않았고 선단의 작은 형상만 허용. 실제 강도 미검증.)
- ℹ drawer: 오버행 4610.4 mm² → 서포트(눕힌 보강 내관: 바닥 평면 양옆 둥근 전이부와 둥근 돌기 아래. 실제 QC 누적4610.4mm²; 트리 지지 대상이며 완전 무서포트가 아님., 허용 4700)
- ℹ drawer_coupon: 오버행 713.1 mm² → 서포트(눕힌 내관 시험편 바닥 양옆 전이부와 돌기 아래. 실제 QC 누적713.1mm²., 허용 720)
- ℹ tip_coupon: 오버행 180.0 mm² → 서포트(눕힌 콘끝 시험편 바닥 양옆 전이부. 실제 QC 누적180.0mm²., 허용 190)
- ✓ 경고 없음 — 보낼 수 있음
