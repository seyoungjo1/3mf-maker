# Toolbox42 — Bambu P1S 3MF 프로젝트

42슬롯 소형 툴박스(본체 / 뚜껑+로고 / 손잡이 / 걸쇠)를 Bambu Lab P1S로 출력하기 위한 작업 기록입니다.
ChatGPT가 만든 원본 3MF가 열리지 않던 문제에서 시작해, **Bambu Studio가 실제로 저장하는 3MF 구조를 소스 코드에서 확인하고 그대로 생성하는 작성기**, 출력 가능성 검사기, 브라우저 뷰어, 작업 지침(스킬)까지 한곳에 모았습니다.

```
toolbox42/
├─ README.md                 ← 이 문서
├─ docs/BAMBU_3MF_STRUCTURE.md  Bambu Studio 3MF 실제 구조 (내보내기 코드 기준)
├─ models/                   중간 도면·최종 파일
├─ figures/                  검증 그림
├─ scripts/                  3MF 작성기·검사기·수정 스크립트
├─ skill/SKILL.md            Claude 작업 지침 (3d-print-3mf)
└─ viewer/3mf-viewer.html    브라우저 3MF 뷰어
```

## 1. 최종 파일

| 파일 | 내용 |
|---|---|
| `models/Toolbox42_P1S_v4.3mf` | **출력용.** 플레이트 3장(01 본체 / 02 뚜껑+로고 2색 / 03 손잡이+걸쇠). Bambu Studio 내보내기 구조 그대로 |
| `models/Toolbox42_lid_flat.3mf` | 뚜껑+로고만 (일반 멀티컬러 3MF, PrusaSlicer/Orca 호환) |
| `models/Toolbox42_*.stl` | 파트별 STL (원본 형상, 출력 방향) — `lid_flat`은 수정된 뚜껑 |

### 원본 대비 바뀐 것 (이것만 바뀜)
- **뚜껑 윗면 테두리 1 mm 단차 제거** — 원본은 로고 패널만 1 mm 솟아 있어 뒤집어 출력하면 테두리 띠(2,452 mm²)가 공중에 떠 서포트가 깔렸음. 띠를 채워 윗면 전체가 베드에 닿게 하고, 메운 모서리는 본체 바닥 곡선과 같은 프로파일(단, 층당 수평 돌출 0.115 mm 상한에 걸리는 아래 1 mm만 30° 직선)로 로프트.
- **걸쇠 놓는 방향** — 형상 변경 없이 긴 옆면으로 세움(원래 방향은 0.7 mm 돌기 하나로 서 있어 725 mm²가 떠 있었음).
- 본체·손잡이·경첩·로고: 원본 그대로.

### 아직 남은 문제 (다음 작업)
- 걸쇠(클립) 베드 안착 불량, 손잡이 두께 부족, 클립 스냅 토크(열리지 않을 위험) — `figures/parts_geom.png`에 현재 단면 치수가 있음. 손잡이 바 단면 12.7 × 9 mm, 다리 2 mm 두께; 걸쇠 두께 5.6 mm 쐐기형.
- 뚜껑 뒤 경첩 돌기 밑면 114 mm²(8.3 mm 높이, 5.5 mm 돌출)는 설계상 오버행 → 그 부위만 슬라이서 서포트.

## 2. 왜 원본이 안 열렸나

원본(`models/00_original_chatgpt_…3mf`)은 `BambuStudio:3mfVersion` 메타데이터와 `Application=BambuStudio-…` 태그로 "Bambu 프로젝트"인 척했지만 다음이 빠져 있었습니다.
- `xmlns:BambuStudio`, `xmlns:p` 네임스페이스 선언 (규격 리더는 여기서 즉시 거부: lib3mf `Could not get XML Namespace for a metadatum`)
- `p:UUID`, 하위 모델 파일(`3D/Objects/*.model`) 구조, `3D/_rels/3dmodel.model.rels`
- project_settings의 `version`, `curr_bed_type`, `flush_volumes_*`
- slice_info.config, cut_information.xml, 썸네일

Bambu Studio 로더(`bbs_3mf.cpp`)는 네임스페이스는 안 보지만, GUI(`Plater.cpp`)가 `Application` 태그·`printer_model`·버전으로 프로젝트 여부를 판정하고, 실패하면 "형상만 불러옴" 알림을 띄웁니다. 자세한 구조는 `docs/BAMBU_3MF_STRUCTURE.md`.

## 3. 스크립트

| 파일 | 역할 |
|---|---|
| `scripts/bbl_project.py` | **Bambu 프로젝트 3MF 작성기** — `write_bbl_project(path, plates, project_settings_json)` |
| `scripts/overhang_check.py` | 0.2 mm 층당 수평 돌출 0.115 mm 규칙 검사 (`python overhang_check.py`) |
| `scripts/load3mf.py` | 3MF에서 정점을 손실 없이 읽어 trimesh로 (STL 왕복 금지 — watertight 깨짐) |
| `scripts/build_parts.py` | 뚜껑 테두리 로프트 + 걸쇠 세우기 → `parts_v3.pkl` |
| `scripts/lid_loft.py` | 본체 바닥 프로파일 그대로 로프트하는 변형 (규칙 미적용 버전) |
| `scripts/inspect_3mf.py` / `repair_3mf.py` | 구조·메시 검사, generic/fixed 수리본 생성 |
| `scripts/mm3mf.py` | 일반 슬라이서용 멀티컬러 3MF 작성기 (저장소 기존 코드) |

```bash
pip install trimesh shapely rtree manifold3d mapbox_earcut lib3mf numpy matplotlib
python scripts/overhang_check.py            # 원본 5파트 검사
python scripts/build_parts.py               # 뚜껑 수정 + 걸쇠 방향
python - <<'EOF'
import sys, pickle, json, zipfile; sys.path.insert(0,'scripts')
from bbl_project import write_bbl_project
P=pickle.load(open('parts_v3.pkl','rb'))
ps=json.loads(zipfile.ZipFile('models/00_original_chatgpt_Toolbox42_P1S_Compact_M3.3mf').read('Metadata/project_settings.config'))
plates=[{'name':'01 Base','objects':[{'name':'base','extruder':1,'parts':[(P['base'],'base',1)]}]}]
write_bbl_project('out.3mf', plates, ps, title='Toolbox42')
EOF
```

## 4. 뷰어

`viewer/3mf-viewer.html`을 브라우저에서 열고 3MF를 끌어다 놓으면 파트별 치수·플레이트·필라멘트 색·구조/메시 검사 결과가 보입니다. three.js·fflate를 CDN(jsdelivr)에서 받으므로 인터넷이 필요합니다. 하위 모델 파일(`p:path`)과 `model_settings.config`의 파트 이름/익스트루더를 읽습니다.

## 5. 그림

- `figures/lid_flat_check.png` — 뚜껑 모서리 프로파일 전/후 vs 본체 바닥, 서포트 자리 맵
- `figures/lid_edge_profile.png` — 로프트 전 계단 버전과 비교
- `figures/sections.png` — 걸쇠·경첩·본체 뒤쪽 단면
- `figures/parts_geom.png` — 손잡이·걸쇠 단면 치수 (다음 수정의 출발점)
- `figures/viewer_v4.png` — 최종 파일을 뷰어로 읽은 화면
