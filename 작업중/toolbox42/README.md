# Toolbox42 — Bambu P1S 3MF 프로젝트

42슬롯 소형 툴박스(본체 / 뚜껑+로고 / 손잡이 / 걸쇠)를 Bambu Lab P1S, PLA로 출력하기 위한 작업 기록입니다.

## 0. v6 (현재) — 뚜껑 외곽 들뜸 수정

| 파일 | 내용 |
|---|---|
| `models/Toolbox42_v6_B_lid_logo.3mf` | **플레이트 B v6**: 뚜껑 v6 + 로고(필라멘트 2). 일반 3MF, lib3mf strict 경고 0 |
| `models/Toolbox42_lid_v6.stl` | 뚜껑 v6 STL |
| `models/Toolbox42_v5_A_base_handle_latch.3mf` | 플레이트 A는 v5 그대로(본체·손잡이·걸쇠 변화 없음). 조립은 M3×14 볼트 |

### 왜 v5 뚜껑 외곽이 들떴나 (사용자 지적으로 정정)
모델에서는 뚜껑 윗면 곡선이 층당 0.115 mm였지만, 슬라이서 코끼리발 보정 0.15 mm가 첫 층을 깎아 **출력물의 1→2층 차이는 0.265 mm**가 됐습니다. 2층이 허공에 쌓여 눌렸고, 멀티컬러(로고 인레이가 첫 3층)라 층 시간이 길어 이미 식은 위에 쌓인 것이 겹쳤습니다. 본체 바닥 곡선도 층당 0.18 mm로 규칙 밖(서포트도 못 놓는 애매한 구간)이라 "본체와 똑같이"는 규칙과 양립하지 않습니다. 이전에 적었던 "팬이 꺼져서 말렸다"는 설명은 근거 없는 추측이라 철회합니다.

| 높이 z | 본체 바닥 inset | v5 뚜껑 inset | **v6 뚜껑 inset** |
|---|---|---|---|
| 0.11 | 1.89 | 1.69 | −0.15 (첫 층, 보정 전) |
| 0.31~0.71 | 1.71~1.39 | 1.57~1.34 | **0.00** (수직) |
| 1.0 | 1.23 | 1.18 | 1.64 (곡선 시작, 안쪽 턱) |
| 2.0 | 0.67 | 0.70 | 1.06 |
| 7.7 | 0 | 0 | 0 |

### v6 수정
- 윗면 모서리를 **바닥에서 0.8 mm(4층)는 전체 윤곽으로 수직**, 그 위부터 층당 0.115 mm 곡선(v5 곡선을 0.8 mm 올림). **첫 층은 코끼리발 보정 0.15 전용으로 0.15 mm 미리 키움** → 출력물 기준 1→2층 0.00, 이후 층당 0.115. 보정을 0으로 출력하면 첫 층에 0.15 mm 턱이 남으므로 보정 0.15로 출력하세요. 첫 층 접지 17,593 → **18,563 mm²**.
- 로고 포켓(교집합 0), 경첩 귀, 걸쇠 탭(기둥 포함)은 그대로. 삼각형 110,432(예산 20만 이내), 닫힌 메시, 층당 바깥 돌출 최대 0.115 mm.
- 겉모습: 윗면 테두리에 0.8 mm 높이의 수직 띠가 생기고 둥근 모서리는 그대로입니다. 그림: `figures/lid_v6_profile.png`, 렌더·GIF: `qc/v6_B/`.
- 슬라이서: 브림 auto(5 mm), 텍스처 PEI, 첫 층 50 mm/s 그대로. 그래도 들뜨면 다음 안은 수직 띠 1.2 mm 또는 외곽 챔퍼(45°)입니다.

---

## 0-1. v5 — 플레이트 A(본체·손잡이·걸쇠)는 이 파일 사용

| 파일 | 내용 |
|---|---|
| `models/Toolbox42_v5_A_base_handle_latch.3mf` | **플레이트 A**: 본체 + 손잡이(v5) + 걸쇠(v5). 일반 3MF — 3d-print 열쇠고리 프로젝트에서 실제 출력에 성공한 `mm3mf.py` 방식 그대로 |
| `models/Toolbox42_v5_B_lid_logo.3mf` | **플레이트 B**: 뚜껑(뒤집어 출력) + 로고(필라멘트 2) |
| `models/Toolbox42_P1S_v5_project.3mf` | Bambu 프로젝트 3MF(플레이트 2장, PLA 2색). 설정은 `sample/test+lunch+box(1).3mf`(사용자 Bambu Studio 02.08.02.61 내보내기)에서 유도 — 열리는지는 사용자 확인 전 |
| `models/Toolbox42_latch_v5.stl`, `models/Toolbox42_handle_v5.stl` | 바뀐 두 파트의 STL |

Bambu Studio에서 A·B 파일을 열면 "not from Bambu Lab, load geometry data only" 알림이 뜹니다. **정상입니다** — 파트 이름과 필라멘트 번호(로고 = 2번)는 그대로 들어옵니다(열쇠고리 프로젝트와 같은 동작). 필라멘트 1·2를 PLA로 지정하고, 뚜껑 플레이트는 브림, 서포트는 "빌드 플레이트에만"으로 켜면 됩니다.

### v4 → v5 바뀐 것
| 파트 | 문제 | 수정 | 수치 |
|---|---|---|---|
| 걸쇠(클립) | 눕히면 판 밑면이 z=0.55에 떠 있고 링 두 개만 바닥에 닿음(접지 7 mm²) → 출력물이 들떠 오그라듦. 세우면 접지 8 mm² | 바깥면 쪽을 z 0~1 채워 바닥 전면 접지. 링 구멍 ⌀3.4·중심·암 간격 38, 쐐기(안쪽 윗면) 변화 없음 | 접지 7 → **775 mm²**, 부피 2875 → 3296 mm³, z>2 상반부 부피 동일(1779.9) |
| 손잡이 | 다리 2.7 mm로 너무 얇음 | 곧은 다리 구간(y −187.6~−172)을 다리 끝 폭 5.4 mm로 두껍게. 다리 끝(구멍 ⌀3.3, 폭 5.4, 간격 72.8 — 본체 앞 귀 쌍 간격 72.8과 일치)은 그대로 | y=−163·−168·−171 단면적 전/후 동일, y=−180 단면 43.7 → 97.2 mm² |
| 뚜껑 | 원본은 윗면 테두리 1 mm 단차 → 뒤집어 출력하면 첫 층 15,196 mm²뿐, 띠 2,923 mm²가 공중 | v4의 `lid_flat` 그대로(확인만) | 첫 층 **17,593 mm²**(윗면 전체 접지). z<1 증가분 916 mm²는 로고 인레이 천장(615)과 모서리 로프트(층당 0.12) |
| 본체·로고 | 변화 없음 | | 본체 앞 귀(손잡이 힌지) 밑면 z=13.5, 162 mm²는 설계상 돌출 → 서포트 |

그림: `figures/v5_latch_handle.png`.

### QC·조립 검증·렌더 (v5)
- `qc/v5_A`, `qc/v5_B`: `tools/qc_model.py` 보고(report.md) + 열쇠고리 프로그램식 렌더 4뷰·회전 GIF(`turntable.gif`).
- `qc/v5_assembly`: 조립 상태(닫힘 / 열림 90° / 분리) 렌더·GIF. 수치는 `docs/ASSEMBLY_v5.md` — 경첩 0~120° 간섭 0, 손잡이 −90~90° 간섭 0(간격 0.06), 뚜껑 끼움 0.1~0.2 mm, **걸쇠는 본체 귀와 치수가 맞지 않아 재설계 필요**(v6 안 포함), 휨·스냅 토크 표.
- 재현: `scripts/assembly_v5.py v5parts.pkl`.


### 왜 v4 프로젝트 3MF가 안 열렸나 (추정 아님, 바뀐 방침)
v4의 `project_settings.config`는 ChatGPT 원본에서 가져온 것이라 Bambu Studio 02.08에 없는 키 15개와 배열 길이 불일치가 섞여 있었습니다. 원인 특정 대신 **방침을 바꿨습니다**: 주 산출물은 검증된 일반 3MF(A·B), 프로젝트 3MF는 사용자 샘플에서만 유도(`scripts/build_project_settings.py`, 결과 `docs/project_settings_v5.json`).

---

## 1. 이전 기록 (v4까지)
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

### 1-1. v4 파일

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

### 1-2. 왜 원본이 안 열렸나

원본(`models/00_original_chatgpt_…3mf`)은 `BambuStudio:3mfVersion` 메타데이터와 `Application=BambuStudio-…` 태그로 "Bambu 프로젝트"인 척했지만 다음이 빠져 있었습니다.
- `xmlns:BambuStudio`, `xmlns:p` 네임스페이스 선언 (규격 리더는 여기서 즉시 거부: lib3mf `Could not get XML Namespace for a metadatum`)
- `p:UUID`, 하위 모델 파일(`3D/Objects/*.model`) 구조, `3D/_rels/3dmodel.model.rels`
- project_settings의 `version`, `curr_bed_type`, `flush_volumes_*`
- slice_info.config, cut_information.xml, 썸네일

Bambu Studio 로더(`bbs_3mf.cpp`)는 네임스페이스는 안 보지만, GUI(`Plater.cpp`)가 `Application` 태그·`printer_model`·버전으로 프로젝트 여부를 판정하고, 실패하면 "형상만 불러옴" 알림을 띄웁니다. 자세한 구조는 `docs/BAMBU_3MF_STRUCTURE.md`.

### 1-3. 스크립트

| 파일 | 역할 |
|---|---|
| `scripts/bbl_project.py` | **Bambu 프로젝트 3MF 작성기** — `write_bbl_project(path, plates, project_settings_json)` |
| `scripts/overhang_check.py` | 0.2 mm 층당 수평 돌출 0.115 mm 규칙 검사 (`python overhang_check.py`) |
| `scripts/load3mf.py` | 3MF에서 정점을 손실 없이 읽어 trimesh로 (STL 왕복 금지 — watertight 깨짐) |
| `scripts/build_parts.py` | 뚜껑 테두리 로프트 + 걸쇠 세우기 → `parts_v3.pkl` |
| `scripts/lid_loft.py` | 본체 바닥 프로파일 그대로 로프트하는 변형 (규칙 미적용 버전) |
| `scripts/inspect_3mf.py` / `repair_3mf.py` | 구조·메시 검사, generic/fixed 수리본 생성 |
| `scripts/mm3mf.py` | 열쇠고리 프로젝트의 멀티컬러 3MF 작성기 (검증된 원본) |
| `scripts/generic3mf.py` | **v5 주 작성기** — mm3mf 방식 + 오브젝트 여러 개 + 베드 배치 |
| `scripts/build_project_settings.py` | 샘플 3MF의 project_settings → PLA n색 설정 유도·검사 |
| `scripts/build_v5.py` | v5 파일 일괄 생성 (`python scripts/build_v5.py v5parts.pkl`) |
| `scripts/lid_v6.py`, `scripts/build_v6.py` | 뚜껑 v6(수직 띠 0.8 + 곡선) 생성 → 플레이트 B v6 |
| `scripts/assembly_v5.py` | 조립 검증(경첩·손잡이 스윕, 간격) |

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

### 1-4. 뷰어

`viewer/3mf-viewer.html`을 브라우저에서 열고 3MF를 끌어다 놓으면 파트별 치수·플레이트·필라멘트 색·구조/메시 검사 결과가 보입니다. three.js·fflate를 CDN(jsdelivr)에서 받으므로 인터넷이 필요합니다. 하위 모델 파일(`p:path`)과 `model_settings.config`의 파트 이름/익스트루더를 읽습니다.

### 1-5. 그림

- `figures/lid_flat_check.png` — 뚜껑 모서리 프로파일 전/후 vs 본체 바닥, 서포트 자리 맵
- `figures/lid_edge_profile.png` — 로프트 전 계단 버전과 비교
- `figures/sections.png` — 걸쇠·경첩·본체 뒤쪽 단면
- `figures/parts_geom.png` — 손잡이·걸쇠 단면 치수 (다음 수정의 출발점)
- `figures/viewer_v4.png` — 최종 파일을 뷰어로 읽은 화면
