# Shuttle6 R14 / full round64 chamber / additive external cradle / six detents in rail — 파이프라인 보고

## 1. QC — 출력 방향 파트 (EFC 0.15 반영, 출력물 기준)

| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| shell_lower | 140,924 | O | 1 | 78.2×78.2×143.5 | 203.0 | 4990.6 / 4990.6 | 5.2 | 0.0 | 0.0 (0.0) | ℹ 얇은 살 허용: 키 선단 삽입 유도면의 국부 모서리5.2mm²만 허용. 독립 벽·탄성 암이 아니며 연속 collar와 폭8mm 키 뿌리 유지. 접착 끼움22mm, 실제 강도 미검증. |
| shell_upper | 119,804 | O | 1 | 78.5×78.5×121.5 | 169.4 | 924.6 / 924.6 | 0.0 | 0.0 | 3.5 (4.4) | ✓ |
| drawer | 61,086 | O | 1 | 221.18×221.18×35.2 | 190.1 | 11402.5 / 11402.5 | 0.0 | 85.4 | 0.8 (3.3) | ℹ 서포트: 앞쪽 사각 뚜껑 연결키 아래만 국부 서포트. 실제85.4mm²; 긴 받침·레일 돌기에는 불필요. |
| cap | 109,744 | O | 1 | 82.2×82.2×10.0 | 54.6 | 4083.8 / 4083.8 | 0.0 | 0.0 | 1459.5 (1.9) | ✓ |
| shell_coupon | 4,782 | O | 1 | 78.5×78.5×36.0 | 53.8 | 1279.3 / 1279.3 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| drawer_coupon | 3,890 | O | 1 | 74.25×74.25×35.2 | 32.3 | 1687.7 / 1687.7 | 0.0 | 85.4 | 0.8 (3.3) | ℹ 서포트: 앞쪽 사각 뚜껑 연결키 아래만 국부 서포트. 실제85.4mm²; 긴 받침·레일 돌기에는 불필요. |
| tip_coupon | 16,104 | O | 1 | 55.86×55.86×35.2 | 24.0 | 472.2 / 472.2 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |

오버행 상위 위치: drawer: z=5.51 85.4 mm² [-8.2, -14.8, 14.8, 8.2] / drawer_coupon: z=5.51 85.4 mm² [-8.2, -14.8, 14.8, 8.2]

브리지 상위 위치(z, mm², 폭): shell_upper: z=22.31 3.5 mm² 폭 4.4 / drawer: z=27.71 0.8 mm² 폭 3.3 / cap: z=0.71 1457.1 mm² 폭 1.6; z=5.11 2.3 mm² 폭 1.9 / drawer_coupon: z=27.71 0.8 mm² 폭 3.3

얇은 살 위치: shell_lower: 5.2 mm² z=143.2 [23.3, 23.3, 29.4, 29.4]

## 2. 플레이트 3MF — 충돌·베드·lib3mf strict

| 플레이트 | 파트 | 범위 x / y (mm) | 충돌 | strict 경고 | 판정 |
|---|---|---|---|---|---|

## 3. 조립 검증 — 상태별 교집합·간격 (표면 샘플 거리: 최소 / 1 % / 5 %)

| 상태 | A | B | 교집합 mm³ | 최소 / 1 % / 5 % mm | 판정 |
|---|---|---|---|---|---|
| 닫힘 | shell | drawer | 0.00 | 0.20 / 0.20 / 0.30 | 접촉(의도) |
| 닫힘 | shell | cap | 0.00 | 0.00 / 0.00 / 0.00 | 접촉(의도) |
| 닫힘 | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 열림 | shell | drawer | 0.00 | 0.30 / 0.95 / 12.26 | 접촉(의도) |
| 열림 | shell | cap | 0.00 | 236.00 / 236.00 / 236.00 | 접촉(의도) |
| 열림 | drawer | cap | 0.00 | 0.12 / 0.20 / 0.20 | 접촉(의도) |
| 분리 | shell | drawer | 0.00 | 16.33 / 23.92 / 38.85 | 접촉(의도) |
| 분리 | shell | cap | 0.00 | 256.27 / 256.55 / 257.97 | 접촉(의도) |
| 분리 | drawer | cap | 0.00 | 13.25 / 14.50 / 16.65 | 접촉(의도) |
| 인출 36mm | shell | drawer | 0.00 | 0.20 / 0.30 / 0.30 | 접촉(의도) |
| 인출 36mm | shell | cap | 0.00 | 36.00 / 36.00 / 36.02 | 접촉(의도) |
| 인출 36mm | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 인출 72mm | shell | drawer | 0.00 | 0.20 / 0.30 / 0.30 | 접촉(의도) |
| 인출 72mm | shell | cap | 0.00 | 72.00 / 72.00 / 72.01 | 접촉(의도) |
| 인출 72mm | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 인출 108mm | shell | drawer | 0.00 | 0.20 / 0.30 / 0.30 | 접촉(의도) |
| 인출 108mm | shell | cap | 0.00 | 108.00 / 108.00 / 108.01 | 접촉(의도) |
| 인출 108mm | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 인출 144mm | shell | drawer | 0.00 | 0.20 / 0.30 / 0.30 | 접촉(의도) |
| 인출 144mm | shell | cap | 0.00 | 144.00 / 144.00 / 144.00 | 접촉(의도) |
| 인출 144mm | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 인출 180mm | shell | drawer | 0.00 | 0.20 / 0.30 / 5.16 | 접촉(의도) |
| 인출 180mm | shell | cap | 0.00 | 180.00 / 180.00 / 180.00 | 접촉(의도) |
| 인출 180mm | drawer | cap | 0.00 | 0.11 / 0.20 / 0.20 | 접촉(의도) |
| 몸통 접착 | shell_lower | shell_upper | 0.00 | 0.00 / 0.00 / 0.15 | 접촉(의도) |
| 뚜껑 끼움 전 | drawer | cap | 0.00 | 8.31 / 10.36 / 12.26 | 접촉(의도) |
| 뚜껑 딸깍 통과 | drawer_cap_pressed | cap | 0.00 | 0.15 / 0.20 / 1.20 | 접촉(의도) |
| 뚜껑 끼움 완료 | drawer | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 18mm | shell | drawer_compressed | 0.00 | 0.02 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 18mm | shell | cap | 0.00 | 18.00 / 18.00 / 18.04 | 접촉(의도) |
| 딸깍 통과 18mm | drawer_compressed | cap | 0.00 | 0.10 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 시험편 닫힘 | shell_coupon | drawer_coupon | 0.00 | 0.20 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 시험편 통과 | shell_coupon | coupon_compressed | 0.00 | 0.02 / 0.30 / 0.30 | 접촉(의도) |

- R14: Open nominal ID64, full circular inside and external additive cradle. Feather compliance is not modelled as rigid plastic.
- Tray prints horizontally on diagonal; cap separately face down. Body only2pieces upright.
- Long clip and release button removed; six pairs of low broad solid beads meet matching inner-shell pockets. Pull-through feel only, no rated positive lock.
- Bead crossing poses use a geometrically compressed bead for collision checks; this is a kinematic representation, not FEA or force validation.
- Actual dimensional/closed joint overlaps: {'drawer_vs_dimensional_gauge_mm3': 0.0, 'shell_vs_dimensional_gauge_mm3': 0.0, 'cap_joint_overlap_mm3': 0.0, 'rail_and_detents': {'measurements': {'inner_radius_min_mm': 31.9961916294096, 'inner_radius_max_mm': 32.0, 'inner_bottom_y_mm': np.float64(-32.0), 'outer_cradle_bottom_y_mm': np.float64(-35.20000076293945), 'bottom_total_mm': np.float64(3.200000762939453), 'rail_normal_gap_mm': 0.29999952917161066, 'flat_base_width_mm': 46.370680930741514}, 'inner_chamber_ray_radii_mm': [31.996192362475767, 31.9961916294096, 31.99999956738326, 31.996192236037484, 31.99619236803526, 31.99999956517308, 31.996191724800052, 31.996191863457756, 31.99999945234333, 31.996191863457756, 31.996191724800052, 31.999999565173084, 31.99619236803526, 31.996192236037484, 31.999999567383256, 31.9961916294096, 31.996192362475767, 32.0, 31.996192362475767, 31.9961916294096, 31.999999567383256, 31.996192236037484, 31.99619236803526, 31.99999956517308, 31.996191724800052, 31.996191863457756, 31.99999945234333, 31.996191863457756, 31.99619172480005, 31.99999956517308, 31.99619236803526, 31.996192236037484, 31.999999567383256, 31.9961916294096, 31.996192362475767], 'stage_checks': [{'extraction_mm': 0, 'overlap_mm3': 0.0}, {'extraction_mm': 36, 'overlap_mm3': 0.0}, {'extraction_mm': 72, 'overlap_mm3': 0.0}, {'extraction_mm': 108, 'overlap_mm3': 0.0}, {'extraction_mm': 144, 'overlap_mm3': 0.0}, {'extraction_mm': 180, 'overlap_mm3': 0.0}, {'extraction_mm': 216, 'overlap_mm3': 0.0}, {'extraction_mm': 236, 'overlap_mm3': 0.0}], 'rotation_checks': [{'angle_deg': 0, 'overlap_mm3': 0.0}, {'angle_deg': -0.25, 'overlap_mm3': 0.0}, {'angle_deg': 0.25, 'overlap_mm3': 0.0}, {'angle_deg': -0.5, 'overlap_mm3': 0.06540705004843517}, {'angle_deg': 0.5, 'overlap_mm3': 0.065407037325798}, {'angle_deg': -1, 'overlap_mm3': 171.51492711558723}, {'angle_deg': 1, 'overlap_mm3': 171.5148283755358}, {'angle_deg': -2, 'overlap_mm3': 1783.0021156710668}, {'angle_deg': 2, 'overlap_mm3': 1783.0030027028502}, {'angle_deg': -3, 'overlap_mm3': 3720.5360665473463}, {'angle_deg': 3, 'overlap_mm3': 3720.5367340385565}, {'angle_deg': 90, 'overlap_mm3': 41780.8667293112}, {'angle_deg': 180, 'overlap_mm3': 47680.174085036255}], 'scope': 'Actual nominal meshes; chamber is circular and not filled. Compressed cams are kinematic trimming only, not shell elasticity, force, wear or fatigue simulation.'}, 'cap_joint_measured': {'pocket_depth_mm': 4.0, 'tongue_length_mm': 3.8, 'gap_per_side_mm': 0.2, 'floor_gap_mm': 0.2, 'primary_pocket_floor_z_mm': 6.0, 'minimum_front_wall_mm': 3.0, 'square_pocket_side_mm': 30.0, 'square_pocket_depth_mm': 3.0, 'square_key_side_mm': 29.6, 'square_key_length_mm': 3.0, 'mode': 'Full half-disc socket plus30mm square pocket and protected snap beams. Physical cap retention is not rated.', 'actual_solid_overlap_mm3': 0.0, 'measured_pocket_depth_mm': 4.0, 'measured_solid_tongue_length_mm': 3.8000001907348633, 'measured_floor_gap_mm': 0.19999980926513672, 'measured_square_pocket_depth_mm': 3.0, 'measured_square_pocket_side_mm': 30.0}, 'cap_deflected_insertion_checks': [{'cap_offset_mm': -1.5, 'compressed_overlap_mm3': 0.0}, {'cap_offset_mm': -1.0, 'compressed_overlap_mm3': 0.0}, {'cap_offset_mm': -0.5, 'compressed_overlap_mm3': 0.0}], 'cap_joint_insertion_checks': [{'cap_offset_mm': -6, 'solid_overlap_mm3': 0.0}, {'cap_offset_mm': -4, 'solid_overlap_mm3': 0.0}, {'cap_offset_mm': -2, 'solid_overlap_mm3': 0.11250059008659719}, {'cap_offset_mm': -1, 'solid_overlap_mm3': 1.3000007390974133}, {'cap_offset_mm': 0, 'solid_overlap_mm3': 0.0}], 'detent_crossing_without_compliance': [{'extraction_mm': 0, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 0.5, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 2, 'rigid_overlap_mm3': 1.5574287780860914}, {'extraction_mm': 10, 'rigid_overlap_mm3': 2.1692085291618164}, {'extraction_mm': 18, 'rigid_overlap_mm3': 1.971989904302177}, {'extraction_mm': 34, 'rigid_overlap_mm3': 1.2981918413096878}, {'extraction_mm': 36, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 54, 'rigid_overlap_mm3': 1.5775931797461074}, {'extraction_mm': 72, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 90, 'rigid_overlap_mm3': 1.183191593603927}, {'extraction_mm': 108, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 126, 'rigid_overlap_mm3': 0.7887947500394906}, {'extraction_mm': 144, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 162, 'rigid_overlap_mm3': 0.394397041509895}, {'extraction_mm': 180, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 190, 'rigid_overlap_mm3': 0.19722083351688488}, {'extraction_mm': 216, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 236, 'rigid_overlap_mm3': 0.0}], 'glue_key_rotation_checks': [{'angle_deg': 0, 'solid_overlap_mm3': 0.0}, {'angle_deg': -0.5, 'solid_overlap_mm3': 10.280799906964186}, {'angle_deg': 0.5, 'solid_overlap_mm3': 10.280803881336965}, {'angle_deg': -1, 'solid_overlap_mm3': 29.13623108772784}, {'angle_deg': 1, 'solid_overlap_mm3': 29.136228462136575}, {'angle_deg': -3, 'solid_overlap_mm3': 99.70592863347429}, {'angle_deg': 3, 'solid_overlap_mm3': 99.70593342702553}, {'angle_deg': 90, 'solid_overlap_mm3': 774.0982303426063}], 'glue_joint_measured': {'collar_wall_mm': 2.2000007547093503, 'radial_gap_mm': 0.14999962232590747, 'key_tip_gap_mm': 0.14999962232591457, 'key_side_gap_mm': 0.10000095077246973, 'key_width_mm': 7.999998918996401}, 'glue_joint_axial_insertion_checks': [{'remaining_insertion_mm': 0, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 2, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 5, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 10, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 14, 'overlap_mm3': 0.0}, {'remaining_insertion_mm': 16, 'overlap_mm3': 0.0}], 'scope': 'Nominal64mm dimensional gauge centered atY0 over the restored circular inner floor,6 nested225mm assumption. Not a measured feather envelope or deformation/contact simulation. Six paired broad beads have intentional elastic crossing; shell/rail compliance is not simulated and click force is not calculated.'}.
- Cap has4mm full half-disc socket plus30x30x3mm square pocket; solid boat nose has protected spring hooks. Nominal closed overlap and deflected passage are checked; no rated real retention strength.
- Full extraction, dimensional gauge and coupon states were verified against the identical meshes in the preceding review_R14. Print-project overview retains seven assembly/cap states; scalar dimensional/interference/rotation/spring checks still run in full_define.

## 4. 렌더 (CPU flat-shaded mesh, 5뷰 + 회전 GIF + 작동 GIF)

- 조립 상태(분리/닫힘/열림…): `qc/review_R14/assembly/view_*_<상태>.png`, `turntable.gif`

## 5. 판정

- ℹ shell_lower: 1.2 mm 보다 얇은 살 5.2 mm² (z=143.2, x/y (23.3, 23.3, 29.4, 29.4)) → 허용(키 선단 삽입 유도면의 국부 모서리5.2mm²만 허용. 독립 벽·탄성 암이 아니며 연속 collar와 폭8mm 키 뿌리 유지. 접착 끼움22mm, 실제 강도 미검증.)
- ℹ drawer: 오버행 85.4 mm² → 서포트(앞쪽 사각 뚜껑 연결키 아래만 국부 서포트. 실제85.4mm²; 긴 받침·레일 돌기에는 불필요., 허용 100)
- ℹ drawer_coupon: 오버행 85.4 mm² → 서포트(앞쪽 사각 뚜껑 연결키 아래만 국부 서포트. 실제85.4mm²; 긴 받침·레일 돌기에는 불필요., 허용 100)
- ✓ 경고 없음 — 보낼 수 있음
