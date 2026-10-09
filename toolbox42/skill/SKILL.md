---
name: 3d-print-3mf
description: 3D 프린팅 모델 설계·Bambu Studio 프로젝트 3MF 생성·검사·수리 전 과정 — Bambu 내보내기 코드에서 확인한 실제 파일 구조와 seyoungjo1/3d-print 파이프라인 기준
---

# 3D 프린팅 · Bambu 3MF 워크플로

사용자는 3MF 프로젝트 파일을 선호하고 프린터는 Bambu Lab P1S(256×256×250, 노즐 0.4, 층 0.2)다. 답변은 한국어 존댓말, 결론부터. **이미 출력한 파트와 짝이 맞는 형상(경첩·끼움·손잡이)은 사용자 허락 없이 절대 바꾸지 않는다.** 바꾸고 싶으면 안을 설명하고 묻는다.

## 1. 교훈
- 손으로 짠 "Bambu 프로젝트 3MF"는 열리지 않았다. 반쪽만 흉내 내면 Bambu Studio가 프로젝트로 인식하지 않는다. 일반 3MF는 열리지만 "형상만 불러옴" 알림이 뜨고 플레이트·필라멘트 배정을 잃는다.
- 해결: Bambu Studio 소스 `src/libslic3r/Format/bbs_3mf.cpp`의 `_BBS_3MF_Exporter`가 쓰는 구조를 그대로 따른다. 구현: `scripts/bbl_project.py`, 구조 설명: `docs/BAMBU_3MF_STRUCTURE.md` (저장소 seyoungjo1/3d-print, 브랜치 toolbox42, 폴더 toolbox42/).
- 소스 확인: `git clone --depth 1 --filter=blob:none --sparse https://github.com/bambulab/bambustudio` 후 `git sparse-checkout set src/libslic3r/Format src/slic3r/GUI`.

## 2. Bambu 프로젝트 3MF 구조 요약 (SaveStrategy::SplitModel)
- 파일: `[Content_Types].xml`, `_rels/.rels`(모델·썸네일·cover-thumbnail-middle/small), `3D/3dmodel.model`(메타+components+build), `3D/_rels/3dmodel.model.rels`, `3D/Objects/object_N.model`(메시), `Metadata/model_settings.config`, `project_settings.config`(전체 설정 JSON+version), `slice_info.config`, `cut_information.xml`, `plate_N.png`.
- 메타: `Application=BambuStudio-XX.XX.XX.XX`(필수), `BambuStudio:3mfVersion=1`, 네임스페이스 `xmlns:BambuStudio`, `xmlns:p` + `requiredextensions="p"`.
- ID: 볼륨 id 먼저, 다음 번호가 오브젝트 id. UUID 접미사: 오브젝트 `-61cb-4c03-9d28-80fed5dfa1dc`, 메시 `-81cb-…`, component `-b206-40ff-9872-83e8017abed1`, item `-b1ec-4553-aec9-835e5b724bb4`, build `2c7c17d8-22b5-4d84-8835-1976022ea369`.
- 플레이트 배치: cols=round(√n)(√n>round면 +1), 원점 (col·W·1.2, −row·D·1.2). P1S 간격 307.2.
- 프로젝트 인정 조건: Application 태그, `printer_model`이 BBL 벤더 모델명과 일치, 파일 버전 ≤ 앱 버전(기본 02.00.00.00). 알림 문구로 역추적: "not from Bambu Lab"(태그 없음) / "invalid config"(프린터 불일치) / 버전 대화상자.

## 3. 작성기 사용
```python
from bbl_project import write_bbl_project
plates=[{'name':'01 Base','objects':[{'name':'base','extruder':1,'parts':[(mesh,'base',1)]}]}]
write_bbl_project('out.3mf', plates, project_settings_json, app_version='02.00.00.00', title='…')
```
메시는 플레이트 로컬 좌표(0~256, z≥0). project_settings는 실제 Bambu Studio가 내보낸 전체 설정 JSON(사용자 기존 3MF에서 꺼냄). 검증: lib3mf lenient(경고 'Unknown Model Metadata'/'Invalid Attribute'는 정상) + 3MF Viewer 아티팩트.

## 4. 출력 가능성 검사 (보내기 전 필수)
- 규칙: 0.2 mm 층당 수평 돌출 ≤ 0.115 mm, 바닥면 전부 베드 접지. `scripts/overhang_check.py`(0.2 간격 +0.0137 오프셋 슬라이스, `cur − prev.buffer(0.115)`; 단면은 `section().to_2D()`→`polygons_full`→to_3D 행렬로 복귀).
- 같은 객체의 다른 파트가 받치는 면(로고 인레이 바닥)은 위반 아님. 배치는 형상 변경이 아니므로 회전으로 해결. 설계상 돌출(경첩 돌기 밑면)은 면적·높이를 명시해 서포트 위치로 보고.
- 모서리 맞추기: 기준 파트 프로파일 g(z)를 여러 x 단면에서 재고(내부 형상 >3 mm 값 버림), 기울기 s 제한 포락 f(z)=min_{z'≥z}[g(z')+s(z'−z)]. 계단 유니온이 아니라 실루엣 링 로프트 단일 곡면 + manifold 불리언. 안쪽 끼움 벽은 원래 단면으로 마스크.

## 5. 메시 취급
- 3MF 정점은 XML 직접 파싱 → `trimesh.Trimesh(V,F,process=False)` (`scripts/load3mf.py`). STL 왕복·정점 병합 금지(watertight 깨짐).
- transform 12개: `M[:3,:3]=v[:9].reshape(3,3).T, M[:3,3]=v[9:]`. 정점 높이와 같은 z 단면은 깨짐 → 오프셋.
- 다색: 파트별 extruder는 model_settings part에. 파트 간 교집합 부피 0 확인.

## 6. 도구·설계 수치
- 필렛·글자·STEP: build123d(3.10~3.12) / 파라미터 상자: OpenSCAD / 메시 가공: trimesh+manifold3d / 유기적 형태: Meshy(`meshy-3d-agent:*`, 결과는 4절 검사 후).
- 저장소 기존 코드: `mm3mf.py`(일반 슬라이서용 다색 3MF), `tools3d.py`, `threemf_splitter/`, run.bat→venv→updater 구조. 새 도구도 같은 구조(.bat CP949+CRLF, ASCII 파일명, goto).
- 벽 ≥1.2(실용 1.6), 끼움 공차 0.2~0.3, 관통 구멍 +0.3, 큰 면을 바닥으로.

## 7. 보고·뷰어
- 결론 한 줄 → 규칙 검사 수치 → 보낸 파일과 슬라이서에서 할 일(버전 대화상자, 브림, 로컬 서포트) → 다음 한 걸음. 여기서 Bambu Studio 실행은 불가.
- 뷰어 `viewer/3mf-viewer.html`(아티팩트 "3MF Viewer"): p:path·model_settings 이름/익스트루더·플레이트·검사. fflate는 jsdelivr(`fflate@0.8.2/umd/index.js`). 헤드리스 캡처: Playwright `executablePath:'/opt/pw-browsers/chromium'`, `--headless=new --use-angle=swiftshader`.
