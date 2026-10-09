# QC 보고 — lower_band.stl, lower_body.stl, lower_roof.stl, lower_roof_trim.stl, lower_screen.stl, platform.stl, upper_band.stl, upper_body.stl, upper_roof.stl, upper_roof_trim.stl, upper_screen.stl

| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | 부피 cm³ / PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| lower_band | 96 | O | 1 | 113.3×80.3×5.0 | 9.08 / 11.3 | 2841.6 / 2841.6 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| lower_body | 9,456 | O | 1 | 103.3×70.3×36.0 | 49.36 / 61.2 | 5323.4 / 5323.4 | 0.0 | 0.0 | 1131.3 (2.8) | ✓ |
| lower_roof | 186 | O | 1 | 136.0×100.0×19.79 | 108.26 / 134.2 | 8010.6 / 8010.6 | 0.0 | 16.5 | 955.4 (4.3) | ✓ |
| lower_roof_trim | 56 | O | 1 | 140.3×104.3×4.0 | 3.85 / 4.8 | 1033.3 / 1033.3 | 0.0 | 16.5 | 0.0 (0.0) | ✓ |
| lower_screen | 64 | O | 1 | 90.7×57.7×19.7 | 4.63 / 5.7 | 321.6 / 321.6 | 233.9 | 0.0 | 0.0 (0.0) | ✓ (단일 벽(발광 갓) 234 mm² — 의도된 0.8 mm 두 줄 벽) |
| platform | 592 | O | 1 | 160.3×138.7×23.0 | 349.45 / 433.3 | 20448.0 / 20448.0 | 0.0 | 0.0 | 185.0 (6.0) | ✓ |
| upper_band | 96 | O | 1 | 105.3×71.3×5.0 | 8.19 / 10.2 | 2569.6 / 2569.6 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| upper_body | 7,440 | O | 1 | 95.3×61.3×27.0 | 31.81 / 39.5 | 2195.4 / 2195.4 | 0.0 | 0.0 | 1021.7 (2.6) | ✓ |
| upper_roof | 166 | O | 1 | 124.0×89.0×42.0 | 201.44 / 249.8 | 10204.4 / 10204.4 | 0.0 | 14.9 | 851.0 (4.3) | ✓ |
| upper_roof_trim | 56 | O | 1 | 128.3×93.3×4.0 | 3.49 / 4.3 | 934.4 / 934.4 | 0.0 | 14.9 | 0.0 (0.0) | ✓ |
| upper_screen | 64 | O | 1 | 82.7×48.7×9.7 | 2.02 / 2.5 | 284.2 / 284.2 | 206.7 | 0.0 | 0.0 (0.0) | ✓ (단일 벽(발광 갓) 207 mm² — 의도된 0.8 mm 두 줄 벽) |

합계: 삼각형 18,272, PLA 통짜 무게 956.8 g (실제는 인필 비율에 따라 30~50 %)

## 파트 간 충돌·간격

| A | B | 교집합 mm³ | 최소 간격 mm | 판정 |
|---|---|---|---|---|
| lower_band | lower_body | 4545.313 | -1.666 | ⚠ 충돌 |
| lower_band | lower_roof | 9079.847 | -0.0 | ⚠ 충돌 |
| lower_band | lower_roof_trim | 0.0 | 9.85 | ✓ |
| lower_band | lower_screen | 0.0 | 3.3 | ✓ |
| lower_band | platform | 9055.547 | -0.96 | ⚠ 충돌 |
| lower_band | upper_band | 2428.758 | -1.667 | ⚠ 충돌 |
| lower_band | upper_body | 0.0 | 1.0 | ✓ |
| lower_band | upper_roof | 9079.847 | -0.0 | ⚠ 충돌 |
| lower_band | upper_roof_trim | 0.0 | 4.35 | ✓ |
| lower_band | upper_screen | 0.0 | 7.3 | ✓ |
| lower_body | lower_roof | 20263.687 | -2.609 | ⚠ 충돌 |
| lower_body | lower_roof_trim | 0.0 | 14.85 | ✓ |
| lower_body | lower_screen | 719.304 | -1.5 | ⚠ 충돌 |
| lower_body | platform | 33229.659 | -2.864 | ⚠ 충돌 |
| lower_body | upper_band | 6674.429 | -2.898 | ⚠ 충돌 |
| lower_body | upper_body | 7717.428 | -1.99 | ⚠ 충돌 |
| lower_body | upper_roof | 27640.526 | -2.798 | ⚠ 충돌 |
| lower_body | upper_roof_trim | 0.0 | 9.35 | ✓ |
| lower_body | upper_screen | 561.507 | -1.499 | ⚠ 충돌 |
| lower_roof | lower_roof_trim | 0.0 | -0.0 | 접촉(얹힘·면접촉) |
| lower_roof | lower_screen | 4228.106 | -2.361 | ⚠ 충돌 |
| lower_roof | platform | 106203.608 | -6.387 | ⚠ 충돌 |
| lower_roof | upper_band | 5850.472 | -2.7 | ⚠ 충돌 |
| lower_roof | upper_body | 12860.986 | -4.112 | ⚠ 충돌 |
| lower_roof | upper_roof | 69504.48 | -4.806 | ⚠ 충돌 |
| lower_roof | upper_roof_trim | 3485.278 | -3.85 | ⚠ 충돌 |
| lower_roof | upper_screen | 0.0 | 2.0 | ✓ |
| lower_roof_trim | lower_screen | 0.0 | 21.15 | ✓ |
| lower_roof_trim | platform | 3848.658 | -0.361 | ⚠ 충돌 |
| lower_roof_trim | upper_band | 0.0 | 14.35 | ✓ |
| lower_roof_trim | upper_body | 0.0 | 19.35 | ✓ |
| lower_roof_trim | upper_roof | 0.0 | 5.5 | ✓ |
| lower_roof_trim | upper_roof_trim | 0.0 | 3.35 | ✓ |
| lower_roof_trim | upper_screen | 0.0 | 25.65 | ✓ |
| lower_screen | platform | 4112.773 | -0.391 | ⚠ 충돌 |
| lower_screen | upper_band | 964.794 | -0.4 | ⚠ 충돌 |
| lower_screen | upper_body | 4029.449 | -0.391 | ⚠ 충돌 |
| lower_screen | upper_roof | 3905.873 | -0.4 | ⚠ 충돌 |
| lower_screen | upper_roof_trim | 0.0 | 15.65 | ✓ |
| lower_screen | upper_screen | 0.0 | 2.9 | ✓ |
| platform | upper_band | 8089.526 | -5.0 | ⚠ 충돌 |
| platform | upper_body | 24695.859 | -10.992 | ⚠ 충돌 |
| platform | upper_roof | 123245.902 | -11.499 | ⚠ 충돌 |
| platform | upper_roof_trim | 3479.278 | -4.0 | ⚠ 충돌 |
| platform | upper_screen | 1658.689 | -9.7 | ⚠ 충돌 |
| upper_band | upper_body | 4084.273 | -1.654 | ⚠ 충돌 |
| upper_band | upper_roof | 8193.806 | -0.0 | ⚠ 충돌 |
| upper_band | upper_roof_trim | 0.0 | 8.85 | ✓ |
| upper_band | upper_screen | 0.0 | 3.3 | ✓ |
| upper_body | upper_roof | 22162.046 | -2.882 | ⚠ 충돌 |
| upper_body | upper_roof_trim | 0.0 | 13.85 | ✓ |
| upper_body | upper_screen | 842.385 | -1.737 | ⚠ 충돌 |
| upper_roof | upper_roof_trim | 0.0 | -0.0 | 접촉(얹힘·면접촉) |
| upper_roof | upper_screen | 2020.689 | -7.481 | ⚠ 충돌 |
| upper_roof_trim | upper_screen | 0.0 | 20.15 | ✓ |

## 오버행(한쪽 지지) 상위 위치 (z, mm², x/y 범위)

- lower_roof: z=0.31 16.5 mm² (-68.0, -50.0, 68.0, 50.0)
- lower_roof_trim: z=0.31 16.5 mm² (-68.0, -50.0, 68.0, 50.0)
- upper_roof: z=0.31 14.9 mm² (-62.0, -44.5, 62.0, 44.5)
- upper_roof_trim: z=0.31 14.9 mm² (-62.0, -44.5, 62.0, 44.5)

## 브리지(양쪽 지지) 상위 위치 (z, mm², 폭)

- lower_body: z=23.11 382.7 mm² 폭 2.8; z=10.71 374.3 mm² 폭 2.8; z=16.51 374.3 mm² 폭 2.8
- lower_roof: z=2.31 955.4 mm² 폭 4.3
- platform: z=8.51 185.0 mm² 폭 6.0
- upper_body: z=14.11 345.6 mm² 폭 2.6; z=8.31 338.1 mm² 폭 2.6; z=10.91 338.1 mm² 폭 2.6
- upper_roof: z=2.31 851.0 mm² 폭 4.3
