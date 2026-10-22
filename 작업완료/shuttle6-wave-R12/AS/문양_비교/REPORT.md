# R12 문양 비교 — 왼쪽 기존 / 오른쪽 수정 — 파이프라인 보고

## 1. QC — 출력 방향 파트 (EFC 0.15 반영, 출력물 기준)

| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| existing | 7,058 | O | 1 | 48.3×14.15×36.0 | 12.2 | 287.9 / 287.9 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |
| proposed | 124,322 | O | 1 | 48.3×14.27×36.0 | 12.5 | 296.5 / 296.5 | 0.0 | 0.0 | 0.0 (0.0) | ✓ |

오버행 상위 위치: 

브리지 상위 위치(z, mm², 폭): 

얇은 살 위치: 

## 2. 플레이트 3MF — 충돌·베드·lib3mf strict

| 플레이트 | 파트 | 범위 x / y (mm) | 충돌 | strict 경고 | 판정 |
|---|---|---|---|---|---|

## 3. 조립 검증 — 상태별 교집합·간격 (표면 샘플 거리: 최소 / 1 % / 5 %)

| 상태 | A | B | 교집합 mm³ | 최소 / 1 % / 5 % mm | 판정 |
|---|---|---|---|---|---|

- Pattern wall segments compared at the same scale, material and lighting. No joint or complete case is being revised in this preview.
- Each segment is a single closed solid. No physical print prediction or ringing diagnosis is inferred.

## 4. 렌더 (CPU flat-shaded mesh, 5뷰 + 회전 GIF + 작동 GIF)

- 조립 상태(분리/닫힘/열림…): `qc/review_R12/assembly/view_*_<상태>.png`, `turntable.gif`

## 5. 판정

- ✓ 경고 없음 — 보낼 수 있음
