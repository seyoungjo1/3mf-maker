# tools — 표준 프로그램 `mm.py` 와 부품 도구

**입구는 하나: `python tools/mm.py <명령>`** (명령줄 · `import mm; mm.run(...)` · HTTP `serve` · Claude API `schema`)

| 명령 | 하는 일 |
|---|---|
| `new <이름> [--desc …]` | 새 도면 틀: `작업중/<이름>/` README(체크리스트·치수표)·`scripts/build.py`·`scripts/assembly.py`·`pipeline.json` — 바로 `make` 통과 |
| `make <config>` | build → pipeline → Bambu 프로젝트 3MF(`*_bambu.3mf`) → 체크리스트. `ok=false` 면 보내지 않는다 |
| `checklist <config>` | report.json(stages)·산출물·README 로 체크리스트 10항목 자동 판정(`line` 을 보고 첫머리에 그대로) |
| `assemble <config> --override '{"base":"v8parts_nominal.pkl:base"}'` | 조립 검증만, 파트 바꿔 끼워 호환 확인 |
| `bambu --plate a.3mf --out a_bambu.3mf` | Bambu 프로젝트 3MF(사용자 내보내기 틀 기반) + 구조 검증 |
| `wallscan <메시…>` / `crop` | 바깥 벽 단차(가로줄) 위치 / 상자로 잘라 STL |
| `doctor` | 의존 라이브러리·Chromium·git 상태 |
| `qc <메시…>` | 출력 방향 QC(닫힘·조각·접지·얇은 살·**벽 속 수평 틈**·오버행/브리지, EFC 0.15 반영) |
| `slits <메시…>` | 벽 속 수평 틈만 — 출력물 옆면 줄의 원인 |
| `section <메시…> --plane y=130 --out a.png [--xlim a b --ylim a b]` | 단면 겹침 그림(실측 근거) |
| `render <메시…> --out dir [--colors '{"lid":"#37474f"}' --states '{…}']` | three.js 5뷰 + 회전 GIF |
| `check3mf <3mf…>` | lib3mf strict 경고 수 |
| `pipeline <config>` / `make <config>` | 게이트 파이프라인 / 빌드→파이프라인 일괄 |
| `selftest` | 도구 자가검사 |

메시 지정: `a.3mf` · `a.3mf:lid` · `a.stl` · `parts.pkl:lid`.
HTTP: `python tools/mm.py serve --port 8765` → `curl -X POST localhost:8765/run -d '{"cmd":"slits","args":{"files":["a.3mf"]}}'`.
Claude API: `python tools/mm.py schema` 의 `tools` 를 Messages API `tools=` 에 넣고, `tool_use` 의 `name`(mm_ 접두어 제거)/`input` 을 `mm.run(name, **input)` 으로 실행해 결과를 `tool_result` 로 돌려준다.

**API 에이전트** `mm_agent.py`: `python tools/mm_agent.py "요청" --project <이름>` — Claude API(claude-opus-5-5, 적응형 사고, 스트리밍, `fallbacks: "default"`) 도구 루프. 시스템 프롬프트 = CLAUDE.md + SKILL.md + references 전부(캐시), 도구 = mm 명령 + 저장소 파일 읽기/쓰기(쓰기는 작업중/·작업완료/·sample/·references 만), 입력 검증, 거절 턴 도구 미실행, **체크리스트 게이트**(미통과면 끝내지 못하고 실패 항목을 되돌려 받음). `--serve` → `POST /agent`. Actions `mm-agent`(수동 실행)도 같은 코드.
**실제 Bambu Studio 검증** `bambu_cli.py`: Actions `bambu-verify` 가 AppImage 로 `--slice 0` 해 G-code 머리말 설정이 3MF project_settings 와 같은지 판정.

부품 도구(mm.py 가 부름): `qc_model.py`, `overhang.py`, `efc.py`(첫 층 선반영), `loft.py`(링 로프트 — 판 쌓기 금지), `meshops.py`(계산 찌꺼기 제거), `render_preview.py`, `check3mf.py`, `generic3mf.py`, `pipeline.py`, `selftest.py`, `snapfit.py`·`beam.py`, `gear.py`·`hinge.py`, `load3mf.py`.

---

# tools — 모델 검사·렌더·계산 도구

| 도구 | 용도 | 예 |
|---|---|---|
| `qc_model.py` | 닫힘·조각·삼각형·크기·무게·접지·얇은 살·오버행·충돌 | `python tools/qc_model.py 작업중/toolbox42/models/Toolbox42_v5_A_base_handle_latch.3mf --out 작업중/toolbox42/qc/v5_A --no-render` |
| `render_preview.py` | 열쇠고리 프로그램식 three.js 렌더(4뷰 PNG + 회전 GIF, 상태 순환) | `python tools/render_preview.py a.stl b.stl --out qc/asm --states states.json --colors a=#37474f,b=#ffb300` |
| `snapfit.py` | 캔틸레버 스냅 변형률·힘·토크 | `python tools/snapfit.py --L 25 --t 3 --b 10 --Y 1.5 --lead 35 --return 60 --r 17.5` |
| `beam.py` | 보 처짐·응력 | `python tools/beam.py --mode simple --L 76 --b 12.7 --h 9 --P 20` |
| `load3mf.py`, `overhang.py`, `efc.py` | 3MF 정점 로더(p:path), 오버행/브리지 규칙, 첫 층 EFC 선반영 | 라이브러리 |
| `gear.py`, `hinge.py` | 인벌류트 기어, 핀 경첩 생성 | 라이브러리 |

의존: `pip install trimesh shapely rtree manifold3d mapbox_earcut scipy networkx lib3mf numpy matplotlib fast-simplification pillow playwright` (Chromium 자동 탐색: `CHROME_PATH` → `/opt/pw-browsers` → playwright 설치본 → 시스템 Chrome/Edge. 점검: `python tools/render_preview.py --check`).
