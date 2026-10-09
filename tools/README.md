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
