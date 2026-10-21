# Shuttle6 C R10 / open ID64 / flat horizontal tray / separate cap / rounded detents — 파이프라인 보고

## 1. QC — 출력 방향 파트 (EFC 0.15 반영, 출력물 기준)

| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| shell_lower | 63,724 | O | 1 | 74.6×74.6×131.5 | 163.6 | 4381.9 / 4381.9 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| shell_upper | 52,180 | O | 1 | 74.9×74.9×121.5 | 142.6 | 704.7 / 704.7 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| drawer | 39,520 | O | 1 | 221.89×221.89×32.09 | 92.0 | 5747.0 / 5859.7 | 0.0 | 4490.0 | 0.0 (0.0) | ℹ 서포트: 눕힌 내관: 바닥 평면 양옆의 둥근 전이부와 둥근 돌기 아래. QC 누적4490.0mm², 콘 안쪽 천장은 없음. 트리 자동 지지 배치 확인. |
| cap | 101,636 | O | 1 | 78.6×78.6×10.0 | 60.3 | 3699.3 / 3699.3 | 0.9 | 0.0 | 1320.5 (2.9) | ✓ |
| shell_coupon | 4,152 | O | 1 | 74.9×74.9×36.0 | 45.1 | 1078.4 / 1078.4 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| drawer_coupon | 1,576 | O | 1 | 74.95×74.95×32.09 | 9.7 | 894.5 / 911.9 | 0.0 | 695.0 | 0.0 (0.0) | ℹ 서포트: 눕힌 내관 시험편의 바닥 양옆 둥근 전이부와 딸깍 돌기 아래. QC 누적695.0mm². |
| tip_coupon | 16,476 | O | 1 | 55.01×55.01×32.0 | 20.2 | 236.0 / 240.5 | 0.0 | 175.4 | 0.0 (0.0) | ℹ 서포트: 눕힌 콘끝 시험편의 바닥 평면 양옆 전이부. QC 누적175.4mm². |

오버행 상위 위치: drawer: z=0.31 219.6 mm² (-5.9, -185.3, 185.3, 5.9); z=0.51 192.3 mm² (-6.2, -185.7, 185.7, 6.2); z=0.71 178.4 mm² (-6.6, -186.0, 186.0, 6.6); z=0.91 170.3 mm² (-6.9, -186.4, 186.4, 6.9) / drawer_coupon: z=0.31 33.9 mm² (-5.9, -38.4, 38.4, 5.9); z=0.51 29.7 mm² (-6.2, -38.8, 38.8, 6.2); z=0.71 27.6 mm² (-6.6, -39.1, 39.1, 6.6); z=0.91 26.3 mm² (-6.9, -39.4, 39.4, 6.9) / tip_coupon: z=0.31 8.8 mm² [-8.7, -15.6, 15.6, 8.7]; z=0.51 7.7 mm² [-9.1, -16.0, 16.0, 9.1]; z=0.71 7.1 mm² [-9.4, -16.3, 16.3, 9.4]; z=0.91 6.8 mm² [-9.7, -16.7, 16.7, 9.7]

브리지 상위 위치(z, mm², 폭): cap: z=0.71 1317.6 mm² 폭 1.6; z=7.71 2.9 mm² 폭 2.9

얇은 살 위치: 

## 2. 플레이트 3MF — 충돌·베드·lib3mf strict

| 플레이트 | 파트 | 범위 x / y (mm) | 충돌 | strict 경고 | 판정 |
|---|---|---|---|---|---|

## 3. 조립 검증 — 상태별 교집합·간격 (표면 샘플 거리: 최소 / 1 % / 5 %)

| 상태 | A | B | 교집합 mm³ | 최소 / 1 % / 5 % mm | 판정 |
|---|---|---|---|---|---|
| 닫힘 | shell | drawer | 0.00 | 0.20 / 0.20 / 0.30 | 접촉(의도) |
| 닫힘 | shell | cap | 0.00 | 0.00 / 0.00 / 0.00 | 접촉(의도) |
| 닫힘 | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 0.5mm | shell | drawer_compressed | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 0.5mm | shell | cap | 0.00 | 0.50 / 0.50 / 0.50 | 접촉(의도) |
| 딸깍 통과 0.5mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 1mm | shell | drawer_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 1mm | shell | cap | 0.00 | 1.00 / 1.00 / 1.00 | 접촉(의도) |
| 딸깍 통과 1mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 2mm | shell | drawer_compressed | 0.00 | 0.06 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 2mm | shell | cap | 0.00 | 2.00 / 2.00 / 2.00 | 접촉(의도) |
| 딸깍 통과 2mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 5mm | shell | drawer_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 5mm | shell | cap | 0.00 | 5.00 / 5.01 / 5.09 | 접촉(의도) |
| 딸깍 통과 5mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 8mm | shell | drawer_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 8mm | shell | cap | 0.00 | 8.00 / 8.01 / 8.06 | 접촉(의도) |
| 딸깍 통과 8mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 딸깍 통과 10mm | shell | drawer_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 통과 10mm | shell | cap | 0.00 | 10.00 / 10.01 / 10.05 | 접촉(의도) |
| 딸깍 통과 10mm | drawer_compressed | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 14mm | shell | drawer | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 14mm | shell | cap | 0.00 | 14.00 / 14.00 / 14.03 | 접촉(의도) |
| 인출 14mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 40mm | shell | drawer | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 40mm | shell | cap | 0.00 | 40.00 / 40.00 / 40.01 | 접촉(의도) |
| 인출 40mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 80mm | shell | drawer | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 80mm | shell | cap | 0.00 | 80.00 / 80.00 / 80.01 | 접촉(의도) |
| 인출 80mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 120mm | shell | drawer | 0.00 | 0.30 / 0.30 / 0.30 | 접촉(의도) |
| 인출 120mm | shell | cap | 0.00 | 120.00 / 120.00 / 120.00 | 접촉(의도) |
| 인출 120mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 180mm | shell | drawer | 0.00 | 0.30 / 0.30 / 4.05 | 접촉(의도) |
| 인출 180mm | shell | cap | 0.00 | 180.00 / 180.00 / 180.00 | 접촉(의도) |
| 인출 180mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 인출 236mm | shell | drawer | 0.00 | 0.30 / 1.01 / 10.50 | 접촉(의도) |
| 인출 236mm | shell | cap | 0.00 | 236.00 / 236.00 / 236.00 | 접촉(의도) |
| 인출 236mm | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 열림 | shell | drawer | 0.00 | 0.30 / 0.92 / 11.20 | 접촉(의도) |
| 열림 | shell | cap | 0.00 | 236.00 / 236.00 / 236.00 | 접촉(의도) |
| 열림 | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 분리 | shell | drawer | 0.00 | 18.86 / 26.01 / 41.11 | 접촉(의도) |
| 분리 | shell | cap | 0.00 | 256.42 / 256.74 / 257.87 | 접촉(의도) |
| 분리 | drawer | cap | 0.00 | 14.00 / 14.06 / 14.54 | 접촉(의도) |
| 몸통 접착 | shell_lower | shell_upper | 0.00 | 0.00 / 0.00 / 0.30 | 접촉(의도) |
| 뚜껑 끼움 전 | drawer | cap | 0.00 | 9.00 / 9.07 / 9.69 | 접촉(의도) |
| 뚜껑 끼움 완료 | drawer | cap | 0.00 | 0.20 / 0.20 / 0.20 | 접촉(의도) |
| 64 공칭 게이지 | drawer | contents | 0.00 | 0.33 / 2.32 / 11.29 | 접촉(의도) |
| 딸깍 시험편 닫힘 | shell_coupon | drawer_coupon | 0.00 | 0.25 / 0.30 / 0.30 | 접촉(의도) |
| 딸깍 시험편 통과 | shell_coupon | coupon_compressed | 0.00 | 0.05 / 0.30 / 0.30 | 접촉(의도) |

- R10: Open nominal ID64, flat lower plane and2mm floor. Feather compliance is not modelled as rigid plastic.
- Tray prints horizontally on diagonal; cap separately face down. Body only2pieces upright.
- Long clip and release button removed; two integrated round beads meet matching inner-shell pockets. Pull-through feel only, no rated positive lock.
- Bead crossing poses use a geometrically compressed bead for collision checks; this is a kinematic representation, not FEA or force validation.
- Actual dimensional/closed joint overlaps: {'drawer_vs_dimensional_gauge_mm3': 0.0, 'shell_vs_dimensional_gauge_mm3': 0.0, 'cap_joint_overlap_mm3': 0.0, 'detent_crossing_without_compliance': [{'extraction_mm': 0, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 0.25, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 0.5, 'rigid_overlap_mm3': 0.0635607050648493}, {'extraction_mm': 0.75, 'rigid_overlap_mm3': 0.33192304157618463}, {'extraction_mm': 1, 'rigid_overlap_mm3': 0.6546826614844955}, {'extraction_mm': 1.5, 'rigid_overlap_mm3': 1.2412645525982953}, {'extraction_mm': 2, 'rigid_overlap_mm3': 1.6059384607733591}, {'extraction_mm': 3, 'rigid_overlap_mm3': 1.709335808754228}, {'extraction_mm': 5, 'rigid_overlap_mm3': 1.7093323904557185}, {'extraction_mm': 8, 'rigid_overlap_mm3': 1.7093327570828478}, {'extraction_mm': 10, 'rigid_overlap_mm3': 0.8546673750161441}, {'extraction_mm': 12, 'rigid_overlap_mm3': 0.0}, {'extraction_mm': 14, 'rigid_overlap_mm3': 0.0}], 'scope': 'Nominal64mm dimensional gauge offset upward2mm over flat floor,6 nested225mm assumption. Not a measured feather envelope or deformation/contact simulation. Rounded beads have intentional elastic crossing; click force not calculated.'}.
- Cap has6mm U-shaped keyed insertion and0.2mm per-side clearance; retention/friction must be checked physically.

## 4. 렌더 (CPU flat-shaded mesh, 5뷰 + 회전 GIF + 작동 GIF)

- 조립 상태(분리/닫힘/열림…): `qc/review_R10/assembly/view_*_<상태>.png`, `turntable.gif`

## 5. 판정

- ℹ drawer: 오버행 4490.0 mm² → 서포트(눕힌 내관: 바닥 평면 양옆의 둥근 전이부와 둥근 돌기 아래. QC 누적4490.0mm², 콘 안쪽 천장은 없음. 트리 자동 지지 배치 확인., 허용 4600)
- ℹ drawer_coupon: 오버행 695.0 mm² → 서포트(눕힌 내관 시험편의 바닥 양옆 둥근 전이부와 딸깍 돌기 아래. QC 누적695.0mm²., 허용 720)
- ℹ tip_coupon: 오버행 175.4 mm² → 서포트(눕힌 콘끝 시험편의 바닥 평면 양옆 전이부. QC 누적175.4mm²., 허용 190)
- ✓ 경고 없음 — 보낼 수 있음
