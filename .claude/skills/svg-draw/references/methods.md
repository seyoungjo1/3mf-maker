# 다른 사람들의 방법에서 배운 것 (2026-10-23 조사)

| 출처 | 무엇 | 가져온 것 (`tools/svgdraw.py`) |
|---|---|---|
| **SketchAgent** (Vinker 외, CVPR 2025, MIT CSAIL) — 저장소 `yael-vinker/SketchAgent` 의 `prompts.py` | 고정된 멀티모달 LLM 이 빈 격자(1~50, `x1y1` = 왼쪽 아래)에 획을 하나씩 낸다. 획 = 통과점 + t 값 + 의미 id, 최소제곱 3차 베지어로 맞춤. 꺾임은 같은 점을 두 번, 점 1개는 점. "가장 중요한 부분부터, 진행을 보고, 구조 → 세부" | `through` 함수(같은 점 두 번 = 꺾임·점 1개 = 점), 격자 이름 점 `"x12y7"`, 단계별 격자 PNG, 획마다 의미 id |
| **Primitive** (Michael Fogleman) | 평균색 캔버스에서 시작 → 무작위 도형 후보 → 언덕 오르기(꼭짓점·반지름 흔들어 오차가 줄면 유지) → 최선 하나 확정 → 반복. 색은 찾지 않고 덮이는 픽셀에서 바로 계산, 바뀐 픽셀만 오차 재계산. 담금질도 해 봤으나 비슷하고 느려서 언덕 오르기 | `Tracer`: 후보 40 → 상위 2 언덕 오르기, 닫힌 식 최적 색, 바뀐 상자 안만 점수 계산. 도형 대신 **선·2차 베지어만** |
| **LIVE** (Ma 외, CVPR 2022, Picsart) | 베지어 경로를 층별로 점진적으로 더하고, 성분별 초기화로 경로 순서가 결정적. DiffVG 만으로는 초기화에 민감 | 오차 지도로 다음 획 자리를 고르는 점진 추가, 큰 덩어리 → 세부 단계(층) |
| **String art 탐욕 알고리즘** (Bridges 2022 "A Greedy Algorithm for Generative String Art", 허깅페이스 stringart.py, Datawrapper) | 핀 쌍 직선 중 남은 오차를 가장 많이 줄이는 선을 고르고 선 무게만큼 빼며 반복, 멈춤 조건 | 점수 = 오차 감소량, 감소량이 기준 아래로 연속이면 멈춤 |
| **iso-figure 스킬** (MrBongoC/ai-iso-skill) | 15줄 투영 커널 함수로 모든 면을 그림(손으로 기운 다각형 금지), 표로 상자 치수를 먼저 적고, 뒤 → 앞 순서, 화면 틀은 극점을 계산해 잡고, 헤드리스 브라우저로 확인 | "좌표는 계산한다"·"손으로 점을 늘어놓으면 함수가 빠진 것"·요소 표 먼저·뒤 → 앞·`--browser` 확인 |
| **logo-designer 스킬** (neonwatty, rknall svg-logo-designer) | 여러 단계(탐색 → 시안 3~5개 나란히 → 다듬기) | 단계 모음 그림(steps.png)으로 나란히 보고 고름 |
| **Stroke of Surprise / VideoSketcher** (2026) | 순차 방식(SketchAgent·Chat2SVG·LLM4SVG)은 한 번 낸 획을 굳힌다; LLM 은 무엇을·어떤 순서로는 잘하지만 어떻게 그리는지는 약하다 | 순서·의미는 AI, 위치·색은 함수·점수(최적화)로 나눔. 길 A 결과를 길 B 의 `init` 으로 |
| **Hertzmann, Painterly Rendering with Curved Brush Strokes of Multiple Sizes** (SIGGRAPH 1998) | 큰 붓 → 작은 붓, 붓질 방향은 그림 기울기의 수직 | 굵기·길이 단계 감소, 구조 텐서로 윤곽 방향 |
| 윤곽 따기 도구(potrace, AutoTrace 중심선, centerline-svg, svgo) | 비트맵 윤곽/뼈대를 따라 경로를 만든다 | **쓰지 않는다**(사용자: "vtracing 이 아니라 공간 분석과 색으로 최적 점수를 찾는 로직") — 비교용으로만 기록 |

## 시험 결과 (이 컨테이너, 160 px 작업 해상도)
- 합성 집 그림(400×300, 함수 22획으로 그린 것)을 목표로 트레이싱: 368획, RMSE 0.168 → 0.041(오차 94 % 감소), 256 px 채점 RMSE 0.063·SSIM 0.886·윤곽 F1 0.968, 23 초.
- 실제 사진(주차번호판 참고 사진 crop, 1327×655) 6색 팔레트(k-평균): 379획, RMSE 0.302 → 0.062, 윤곽 F1 0.953, 32 초. 작은 글씨는 이 해상도에서 안 읽힘 → `--size` 를 올리거나 글씨는 길 A 로.
- AI 단계 그림(구도·지붕 4획)의 채점 → 가장 큰 오차 칸 `x7y7`, 목표 색 #fce45e(해) — 다음 단계 근거. 그 위에 `--init` 으로 145획: RMSE 0.138 → 0.047, AI 의 `graph` 획은 함수식 그대로 남음.
- Chromium 렌더 ↔ 내부 래스터 RMSE 0.012(트레이싱)·0.020(단계 그림) — 점수가 실제 렌더와 같다.

## 주소
- SketchAgent: https://sketch-agent.csail.mit.edu/ , https://github.com/yael-vinker/SketchAgent , https://openaccess.thecvf.com/content/CVPR2025/papers/Vinker_SketchAgent_Language-Driven_Sequential_Sketch_Generation_CVPR_2025_paper.pdf
- Primitive: https://github.com/fogleman/primitive
- LIVE: https://openaccess.thecvf.com/content/CVPR2022/papers/Ma_Towards_Layer-Wise_Image_Vectorization_CVPR_2022_paper.pdf
- String art: https://archive.bridgesmathart.org/2022/bridges2022-63.html , https://huggingface.co/spaces/aboalaa147/string-art-maker/blob/main/stringart.py , https://www.datawrapper.de/blog/mariline-monroe-chart-art
- 스킬: https://github.com/MrBongoC/ai-iso-skill , https://github.com/neonwatty/logo-designer-skill , https://github.com/rknall/claude-skills/blob/main/svg-logo-designer/README.md , https://github.com/shanraisshan/claude-code-best-practice/blob/main/.claude/skills/weather-svg-creator/SKILL.md , https://github.com/cathrynlavery/diagram-design
- 순차 스케치 비교: https://arxiv.org/html/2602.12280 , https://arxiv.org/html/2602.15819
- 윤곽 따기(안 씀): https://pypi.org/project/centerline-svg/ , https://github.com/tatarize/potrace
