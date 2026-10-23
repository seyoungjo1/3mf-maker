---
name: svg-draw
description: SVG 를 한 번에 쓰지 않고 단계적으로 그리는 지침과 도구(tools/svgdraw.py, mm svgdraw·svgtrace·svgscore). 모든 획은 선과 함수(line·bezier·through·arc·graph·param·polar·sine…)뿐. 참고 그림이 있으면 공간 분석(오차 지도·윤곽 방향)과 색(최적 색·팔레트)으로 점수가 가장 좋은 획을 하나씩 고르는 최적화 트레이싱. 로고·문양·일러스트·도면 SVG, 그림을 SVG 로 옮기기, 3D 부조용 선 그림에 쓴다.
---

# 단계적 SVG 그리기 (선과 함수만)

**한 번에 다 그리지 않는다.** LLM 은 "무엇을 어떤 순서로" 는 잘 정하지만 "정확히 어디에 어떻게" 는 약하다(VideoSketcher·SketchAgent 관찰).
그래서 순서와 의미는 AI 가 단계마다 정하고, 좌표는 함수로 계산하고, 맞는지는 렌더와 점수로 판정한다. 출처·배운 점: `references/methods.md`.

## 0. 규칙
1. **획 = 함수.** 모든 획은 `tools/svgdraw.py` 의 함수(아래 표) 하나다. SVG 에는 `M…L…` 꺾은선 + `data-fn`(원래 함수식)으로 남아 다시 고칠 수 있다. 채움은 닫힌 함수 곡선 안쪽만.
2. **단계마다 렌더하고 본다.** `python tools/mm.py svgdraw <스펙> --out <dir>` → `step_NN.png`(격자·칸 번호) 를 Read 로 열어 보고 다음 단계를 정한다. 보지 않고 다음 단계로 넘어가지 않는다.
3. **좌표는 계산한다.** 눈대중 숫자 대신 중심·반지름·비율에서 계산하고, 대칭은 `tf.mirror`, 반복은 `repeat`(dx·dy·rotate), 곡선은 식(`graph`·`param`·`polar`)으로. 손으로 다각형 점을 늘어놓고 있으면 함수가 빠진 것이다.
4. **점수로 판정한다.** 참고 그림이 있으면 `mm svgscore` 의 RMSE·SSIM·윤곽 F1 과 오차 큰 칸(`x?y?`, 목표 색, 윤곽 방향)으로 다음 단계를 고른다. "비슷해 보인다" 대신 숫자로.
5. 마지막에 `--browser` 로 Chromium 렌더 ↔ 내부 래스터 RMSE(≈0.02 이하)를 확인하고 보고한다.

## 1. 길 A — AI 가 단계별로 그린다 (SketchAgent 방식)
스펙 JSON 하나를 단계마다 늘려 간다(앞 단계는 고치지 않으면 그대로 둔다).
```json
{"width":400,"height":300,"background":"#ffffff","grid":20,
 "steps":[{"name":"1 구도","strokes":[{"fn":"line","p0":[20,250],"p1":[380,250],"stroke":"#555","width":3,"id":"땅선"}]},
          {"name":"2 큰 형태","strokes":[{"fn":"ellipse","c":[200,170],"rx":110,"ry":70,"stroke":"#333","width":4,"id":"몸통"}]}]}
```
| 단계 | 하는 일 | 끝나면 |
|---|---|---|
| 0 | 캔버스 크기·배경·격자(보통 20칸) 정하기, 참고 그림이 있으면 `svgscore` 로 빈 캔버스 점수 | 기준 점수 |
| 1 요소 목록 | 그릴 요소를 큰 것 → 작은 것 순서로 적고 각 요소의 함수를 정한다(id = 의미 이름) | 표 |
| 2 구도 | 땅선·중심선·바깥 상자 같은 기준선. 전체 비율·여백 | step_01 확인 |
| 3 큰 형태 | 덩어리 윤곽(ellipse·rect·poly·through) | step 확인, 비율 고침 |
| 4 구조·연결 | 형태 사이 연결선, 겹침 순서(뒤 → 앞) | step 확인 |
| 5 세부 | 반복 부재(`repeat`), 무늬(`sine`·`spiral`·`polar`), 작은 요소 | step 확인 |
| 6 색·채움 | 닫힌 곡선 `fill`, 선 굵기 위계(외곽 굵게·세부 가늘게) | step 확인 |
| 7 검증 | `svgscore`(참고 그림), `--browser`, 오차 칸을 고쳐 다시 6~7 | 점수표 |

점은 `[x, y]`(SVG 좌표, y 아래) 또는 격자 이름 `"x12y7"`(1부터, y 는 아래에서 위로 — 격자 PNG 의 가장자리 번호 그대로).

## 2. 길 B — 점수 최적화 트레이싱 (참고 그림 → 선·곡선)
윤곽을 따는 것(potrace·vtracer)이 아니다. 획을 하나씩 **고르는** 것이다:
1. **공간 분석**: 오차 지도 `Wm·|T−C|²`(Wm = 1 + 윤곽 세기, 윤곽을 더 중히) → 흐림 → 1.5 제곱에 비례해 후보 자리를 뽑는다.
2. **방향**: 목표 그림의 구조 텐서로 그 자리의 윤곽 방향·일관성 → 일관성이 높으면 윤곽을 따라, 낮으면 아무 방향.
3. **색**: 덮임 a 일 때 최적 색 `c = Σ Wm·a·(T−(1−a)C) / Σ Wm·a²`(닫힌 식) 또는 팔레트(필라멘트 색) 중 오차가 가장 작은 색.
4. **점수**: 그 획을 그었을 때 오차 감소량. 후보 40개 → 상위 2개를 언덕 오르기(끝점·조절점·굵기·위치 흔들기)로 다듬어 최선을 확정.
5. **단계**: 굵기·길이를 큰 덩어리 → 중간 → 세부로 줄인다. 감소량이 기준 아래로 5번 연속이면 멈춘다.
```
python tools/mm.py svgtrace 그림.png --out dir --strokes 300 --size 160 [--colors 4 | --palette '#37474f' '#ffb300'] [--kinds line | line,curve] [--init ai_steps.json]
```
결과: `trace.json`(스펙 — 길 A 로 다시 고칠 수 있다)·`trace.svg`·`progress.gif`(목표 | 진행). 160 px·300 획 ≈ 20~30 초.

## 3. 섞기 (권장)
AI 가 길 A 로 구도·큰 형태(의미 있는 함수 획)를 그리고 → `svgscore` 로 오차 칸을 보고 → 부족한 세부·색은 `svgtrace --init <AI 스펙>` 이 이어 그린다(AI 획은 함수식 그대로 남음). 반대로 트레이싱 결과에서 의미 있는 획만 남겨 다듬어도 된다.

## 4. 함수 표 (`FUNCS`)
| fn | 인자 | 비고 |
|---|---|---|
| line | p0 p1 | 직선 |
| polyline | pts closed | 꺾은선(가능하면 아래 함수로) |
| rect · poly | x y w h · c r sides rot | 사각·정다각형 |
| circle · ellipse · arc | c r · c rx ry rot a0 a1 · c r a0 a1 | 도 단위 |
| bezier | pts | 임의 차수 조절점 |
| through | pts t | 통과점 + t 값 → 최소제곱 3차 베지어, **같은 점 두 번 = 꺾임**, 점 1개 = 점 |
| graph | f x0 x1 origin scale | y = f(x) (수학 좌표, 위가 +) |
| param | x y t0 t1 | x(t), y(t) |
| polar | r th0 th1 c | r(th), th 도 단위 범위 · 식 안에서는 라디안 |
| sine · spiral | p0 p1 amp cycles · c r0 r1 turns | 물결·나선 |
공통: `stroke width opacity fill fill_opacity id n tf{scale,rotate,translate,mirror,about} repeat{n,dx,dy,rotate,about}`. 식은 numpy 이름(sin cos sqrt abs exp log pi …)만 쓰는 안전한 식.

## 5. 3D 로 (이 저장소)
`svgdraw.to_shapely(spec, width_mm)` → 선은 굵기만큼 버퍼, 채움은 다각형, y 위·(0,0) 왼쪽 아래(`svg2d.load_svg` 와 같은 규칙) → 판 위 부조·인레이로 압출. 그 전에 `svg2d.thin_parts(g, 0.8)` 로 0.8 mm 미만 선을 확인한다(3d-print-3mf 디테일 최소치). 모델링이 되면 3d-print-3mf 스킬 순서를 따른다.

## 6. 보고
결론 한 줄 → 단계 모음(`steps.png`) 또는 `progress.gif` → 점수(RMSE·SSIM·윤곽 F1, 처음 → 끝) → `--browser` RMSE → 파일(SVG·스펙) → 다음 단계(오차 큰 칸).
