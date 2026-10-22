# Shuttle6 C R12 / open ID64 / flat horizontal tray / separate cap / rounded detents — 파이프라인 보고

## 1. QC — 출력 방향 파트 (EFC 0.15 반영, 출력물 기준)

| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| shell_lower | 152,766 | O | 1 | 78.2×78.2×135.5 | 227.9 | 4866.3 / 4866.3 | 5.2 | 0.0 | 0.0 (0.0) | ℹ 얇은 살 허용: 키 선단1mm 삽입 유도면의 국부 모서리: 실제 QC5.2mm²,z135.2. 독립 벽/탄성 암이 아니며 뒤쪽 연속 collar 벽은 선단에서도1.85mm 이상, 축부2.20mm·키 폭8mm·길이14mm. 어깨부/키 뿌리는 깎지 않았고 선단의 작은 형상만 허용. 실제 강도 미검증. |
| shell_upper | 126,702 | O | 1 | 78.5×78.5×121.5 | 196.2 | 916.0 / 916.0 | 0.0 | 0.0 | 75.9 (4.9) | ✓ |
| drawer | 39,072 | O | 1 | 221.18×221.18×32.69 | 121.0 | 5746.2 / 5858.0 | 0.0 | 4652.0 | 0.8 (3.3) | ℹ 서포트: 보강 내관의 바닥 양옆 전이부·돌기 아래·새 반원/사각 키 앞끝 전이부. 실제 누적4652.0mm². 트리서포트 사용. |
| cap | 109,904 | O | 1 | 82.2×82.2×10.0 | 55.9 | 4083.8 / 4083.8 | 0.0 | 0.0 | 1459.5 (1.9) | ✓ |
| shell_coupon | 4,146 | O | 1 | 78.5×78.5×36.0 | 61.7 | 1453.4 / 1453.4 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| drawer_coupon | 1,646 | O | 1 | 74.25×74.25×32.69 | 22.1 | 850.7 / 867.1 | 0.0 | 754.8 | 0.8 (3.3) | ℹ 서포트: 내관 시험편의 바닥 양옆 전이부·돌기와 새 앞끝 아래. 실제 누적754.8mm². 트리서포트 사용. |
| tip_coupon | 16,460 | O | 1 | 55.86×55.86×32.6 | 20.9 | 238.1 / 242.6 | 0.0 | 180.0 | 0.0 (0.0) | ℹ 서포트: 눕힌 콘끝 시험편 바닥 양옆 전이부. 실제 QC 누적180.0mm². |

오버행 상위 위치: drawer: z=0.31 222.6 mm² [-4.4, -185.4, 185.4, 4.4]; z=2.91 191.9 mm² [-8.2, -189.2, 189.2, 8.2]; z=0.51 190.6 mm² [-4.8, -185.8, 185.8, 4.8]; z=0.71 181.8 mm² [-5.1, -186.1, 186.1, 5.1] / drawer_coupon: z=2.91 101.1 mm² [-8.2, -42.3, 42.3, 8.2]; z=0.31 32.7 mm² [-4.4, -38.5, 38.5, 4.4]; z=0.51 28.0 mm² [-4.8, -38.8, 38.8, 4.8]; z=0.71 26.7 mm² [-5.1, -39.2, 39.2, 5.1] / tip_coupon: z=0.31 9.0 mm² [-8.8, -15.7, 15.7, 8.8]; z=0.51 7.7 mm² [-9.1, -16.1, 16.1, 9.1]; z=0.71 7.3 mm² [-9.5, -16.4, 16.4, 9.5]; z=0.91 6.8 mm² [-9.8, -16.7, 16.7, 9.8]

브리지 상위 위치(z, mm², 폭): shell_upper: z=14.31 8.4 mm² 폭 4.9; z=14.51 4.5 mm² 폭 1.8; z=14.71 4.5 mm² 폭 2.6; z=14.91 4.4 mm² 폭 2.6 / drawer: z=25.11 0.8 mm² 폭 3.3 / cap: z=0.71 1457.1 mm² 폭 1.6; z=5.11 2.3 mm² 폭 1.9 / drawer_coupon: z=25.11 0.8 mm² 폭 3.3

얇은 살 위치: shell_lower: 5.2 mm² z=135.2 [23.3, 23.3, 29.4, 29.4]

## 2. 플레이트 3MF — 충돌·베드·lib3mf strict

| 플레이트 | 파트 | 범위 x / y (mm) | 충돌 | strict 경고 | 판정 |
|---|---|---|---|---|---|
| P01_body_pair.3mf | shell_lower, shell_upper | 33~223 / 89~167 | 0 | 0 | ✓ |
| P02_horizontal_tray.3mf | drawer | 17~239 / 17~239 | 0 | 0 | ✓ |
| P03_separate_cap.3mf | cap | 87~169 / 87~169 | 0 | 0 | ✓ |
| P04_detent_shell_coupon.3mf | shell_coupon | 89~167 / 89~167 | 0 | 0 | ✓ |
| P05_detent_tray_coupon.3mf | drawer_coupon | 91~165 / 91~165 | 0 | 0 | ✓ |
| P06_tip_coupon.3mf | tip_coupon | 100~156 / 100~156 | 0 | 0 | ✓ |

## 3. 조립 검증 — 상태별 교집합·간격 (표면 샘플 거리: 최소 / 1 % / 5 %)

| 상태 | A | B | 교집합 mm³ | 최소 / 1 % / 5 % mm | 판정 |
|---|---|---|---|---|---|
| 닫힘 | shell | drawer | 0.00 | 0.20 / 0.30 / 0.30 | 접촉(의도) |
| 닫힘 | shell | cap | 0.00 | 0.00 / 0.00 / 0.00 | 접촉(의도) |
| 닫힘 | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 열림 | shell | drawer | 0.00 | 0.30 / 1.35 / 11.63 | 접촉(의도) |
| 열림 | shell | cap | 0.00 | 236.00 / 236.00 / 236.00 | 접촉(의도) |
| 열림 | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 분리 | shell | drawer | 0.00 | 16.31 / 25.33 / 39.42 | 접촉(의도) |
| 분리 | shell | cap | 0.00 | 256.24 / 256.49 / 257.73 | 접촉(의도) |
| 분리 | drawer | cap | 0.00 | 13.29 / 14.19 / 16.30 | 접촉(의도) |
| 몸통 접착 | shell_lower | shell_upper | 0.00 | 0.00 / 0.00 / 0.15 | 접촉(의도) |
| 뚜껑 끼움 전 | drawer | cap | 0.00 | 8.35 / 9.77 / 11.77 | 접촉(의도) |
| 뚜껑 딸깍 통과 | drawer_cap_pressed | cap | 0.00 | 0.02 / 0.20 / 1.18 | 접촉(의도) |
| 뚜껑 끼움 완료 | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |

- R12: Open nominal ID64, flat lower plane and2.6mm floor. Feather compliance is not modelled as rigid plastic.
- Tray prints horizontally on diagonal; cap separately face down. Body only2pieces upright.
- Long clip and release button removed; two integrated round beads meet matching inner-shell pockets. Pull-through feel only, no rated positive lock.
- Bead crossing poses use a geometrically compressed bead for collision checks; this is a kinematic representation, not FEA or force validation.
- Actual dimensional/closed joint overlaps: {'drawer_vs_dimensional_gauge_mm3': 0.0, 'shell_vs_dimensional_gauge_mm3': 0.0, 'cap_joint_overlap_mm3': 0.0, 'cap_joint_measured': {'pocket_depth_mm': 4.0, 'tongue_length_mm': 3.8, 'gap_per_side_mm': 0.2, 'floor_gap_mm': 0.2, 'primary_pocket_floor_z_mm': 6.0, 'minimum_front_wall_mm': 3.0, 'square_pocket_side_mm': 30.0, 'square_pocket_depth_mm': 3.0, 'square_key_side_mm': 29.6, 'square_key_length_mm': 3.0, 'mode': 'Full half-disc socket plus30mm square pocket and protected snap beams. Physical cap retention is not rated.', 'actual_solid_overlap_mm3': 0.0, 'measured_pocket_depth_mm': 4.0, 'measured_solid_tongue_length_mm': 3.8000001907348633, 'measured_floor_gap_mm': 0.19999980926513672, 'measured_square_pocket_depth_mm': 3.0, 'measured_square_pocket_side_mm': 30.0}, 'cap_deflected_insertion_checks': [{'cap_offset_mm': -1.5, 'compressed_overlap_mm3': 0.0}, {'cap_offset_mm': -1.0, 'compressed_overlap_mm3': 0.0}, {'cap_offset_mm': -0.5, 'compressed_overlap_mm3': 0.0}], 'cap_joint_insertion_checks': [{'cap_offset_mm': -6, 'solid_overlap_mm3': 0.0}, {'cap_offset_mm': -4, 'solid_overlap_mm3': 0.0}, {'cap_offset_mm': -2, 'solid_overlap_mm3': 0.11250059008659719}, {'cap_offset_mm': -1, 'solid_overlap_mm3': 1.3000007390974133}, {'cap_offset_mm': 0, 'solid_overlap_mm3': 0.0}], 'detent_crossing_without_compliance': [{'extraction_mm': 0, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 0.25, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 0.5, 'rigid_overlap_mm3': 0.06330499445256048}, {'extraction_mm': 0.75, 'rigid_overlap_mm3': 0.33099676710899456}, {'extraction_mm': 1, 'rigid_overlap_mm3': 0.653018593773254}, {'extraction_mm': 1.5, 'rigid_overlap_mm3': 1.238192061065509}, {'extraction_mm': 2, 'rigid_overlap_mm3': 1.6017929705239264}, {'extraction_mm': 3, 'rigid_overlap_mm3': 1.704580932645096}, {'extraction_mm': 5, 'rigid_overlap_mm3': 1.7045820590750889}, {'extraction_mm': 8, 'rigid_overlap_mm3': 1.7045841052161375}, {'extraction_mm': 10, 'rigid_overlap_mm3': 0.8522903892343834}, {'extraction_mm': 12, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 14, 'rigid_overlap_mm3': 0.0}], 'glue_key_rotation_checks': [{'angle_deg': 0, 'solid_overlap_mm3': 0.0}, {'angle_deg': -0.5, 'solid_overlap_mm3': 2.669155618912763}, {'angle_deg': 0.5, 'solid_overlap_mm3': 2.6691569272463007}, {'angle_deg': -1, 'solid_overlap_mm3': 6.383907867075474}, {'angle_deg': 1, 'solid_overlap_mm3': 6.383907452804654}, {'angle_deg': -3, 'solid_overlap_mm3': 19.98008273016357}, {'angle_deg': 3, 'solid_overlap_mm3': 19.980082377780793}, {'angle_deg': 90, 'solid_overlap_mm3': 79.19498414670063}], 'glue_joint_measured': {'collar_wall_mm': 2.2000007547093503, 'radial_gap_mm': 0.14999962232591457, 'key_tip_gap_mm': 0.14999962232591457, 'key_side_gap_mm': 0.10000082734596782, 'key_width_mm': 7.999998918996401}, 'glue_joint_axial_insertion_checks': [{'remaining_insertion_mm': 0, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 2, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 5, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 10, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 14, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 16, 'overlap_mm3': 0.0}], 'scope': 'Nominal64mm dimensional gauge offset upward2mm over flat floor,6 nested225mm assumption. Not a measured feather envelope or deformation/contact simulation. Rounded beads have intentional elastic crossing; click force not calculated.'}.
- Cap has4mm full half-disc socket plus30x30x3mm square pocket; solid boat nose has protected spring hooks. Nominal closed overlap and deflected passage are checked; no rated real retention strength.
- Full extraction, dimensional gauge and coupon states were verified against the identical meshes in the preceding review_R12. Print-project overview retains seven assembly/cap states; scalar dimensional/interference/rotation/spring checks still run in full_define.

## 4. 렌더 (CPU flat-shaded mesh, 5뷰 + 회전 GIF + 작동 GIF)

- 플레이트 `P01_body_pair.3mf`: `qc/final_R12/plate_P01_body_pair/view_*.png`, `turntable.gif`
- 플레이트 `P02_horizontal_tray.3mf`: `qc/final_R12/plate_P02_horizontal_tray/view_*.png`, `turntable.gif`
- 플레이트 `P03_separate_cap.3mf`: `qc/final_R12/plate_P03_separate_cap/view_*.png`, `turntable.gif`
- 플레이트 `P04_detent_shell_coupon.3mf`: `qc/final_R12/plate_P04_detent_shell_coupon/view_*.png`, `turntable.gif`
- 플레이트 `P05_detent_tray_coupon.3mf`: `qc/final_R12/plate_P05_detent_tray_coupon/view_*.png`, `turntable.gif`
- 플레이트 `P06_tip_coupon.3mf`: `qc/final_R12/plate_P06_tip_coupon/view_*.png`, `turntable.gif`
- 조립 상태(분리/닫힘/열림…): `qc/final_R12/assembly/view_*_<상태>.png`, `turntable.gif`

## 5. 판정

- ℹ shell_lower: 1.2 mm 보다 얇은 살 5.2 mm² (z=135.2, x/y (23.3, 23.3, 29.4, 29.4)) → 허용(키 선단1mm 삽입 유도면의 국부 모서리: 실제 QC5.2mm²,z135.2. 독립 벽/탄성 암이 아니며 뒤쪽 연속 collar 벽은 선단에서도1.85mm 이상, 축부2.20mm·키 폭8mm·길이14mm. 어깨부/키 뿌리는 깎지 않았고 선단의 작은 형상만 허용. 실제 강도 미검증.)
- ℹ drawer: 오버행 4652.0 mm² → 서포트(보강 내관의 바닥 양옆 전이부·돌기 아래·새 반원/사각 키 앞끝 전이부. 실제 누적4652.0mm². 트리서포트 사용., 허용 4700)
- ℹ drawer_coupon: 오버행 754.8 mm² → 서포트(내관 시험편의 바닥 양옆 전이부·돌기와 새 앞끝 아래. 실제 누적754.8mm². 트리서포트 사용., 허용 780)
- ℹ tip_coupon: 오버행 180.0 mm² → 서포트(눕힌 콘끝 시험편 바닥 양옆 전이부. 실제 QC 누적180.0mm²., 허용 190)
- ✓ 경고 없음 — 보낼 수 있음
