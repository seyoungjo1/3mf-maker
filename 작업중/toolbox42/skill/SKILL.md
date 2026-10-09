---
name: 3d-print-3mf
description: 3D 프린팅 모델 설계·3MF 생성·검사 전 과정 — seyoungjo1/3mf-maker 저장소 기준. Bambu Lab P1S, PLA, Bambu Studio 02.08.x.
---

# 3D 프린팅 · 3MF 워크플로 (3mf-maker)

사용자: Bambu Lab P1S(256×256×250, 노즐 0.4, 층 0.2), **필라멘트는 보통 PLA**(Bambu PLA Basic), Bambu Studio **02.08.02.61**(sample 파일 기준). 답변은 한국어 존댓말, 결론부터.
**이미 출력한 파트와 짝이 맞는 형상(경첩·핀·구멍·끼움)은 치수를 바꾸지 않는다.** 두께를 더하거나 방향을 바꾸는 것은 되지만, 결합 치수(구멍 지름·간격·폭)는 수치로 전/후 비교해 같음을 보인다.

## 0. 저장소 구조와 규칙
- `작업중/<프로젝트>/` 진행 중 → 완성되면 폴더째 `작업완료/<프로젝트>/`. `sample/`은 **참고한 도면·참고 3MF**(사용자가 올림, 기준 자료).
- 완성본의 기준은 하나다: **Bambu Studio에서 열려야 한다.** 열리지 않는 파일은 완성본이 아니다. 아래 2절 방식 외의 "새로운 3MF 구조"를 지어내지 않는다.
- 추측 금지. 파일 구조·설정값은 반드시 (a) `sample/`에 사용자가 올린 실제 Bambu Studio 내보내기 파일, (b) 검증된 기존 코드(3d-print 열쇠고리 프로젝트 `mm3mf.py`), (c) Bambu Studio 소스(`bbs_3mf.cpp`, `Preset.cpp`, `PrintConfig.cpp`, `resources/profiles/BBL/`) 중 하나에서 가져온다.

## 1. 기준 프로젝트 — 3d-print 열쇠고리·키캡 (잘 됐던 방식)
seyoungjo1/3d-print 브랜치 `claude/keyring-groove-feature-t4xnmp`(배포 브랜치 `claude/beautiful-mendel-tpwclc`)의 **🔑 열쇠고리·키캡**만 기준이다. 카라비너·조명등·LP판은 결과가 좋지 않았으므로 참고하지 않는다.
- 출력 파일: `mm3mf.py` `write_multicolor_3mf()` — **일반 3MF + basematerials 색 + `Metadata/model_settings.config` 파트별 extruder + `Slic3r_PE_model.config`**. Bambu Studio가 "형상만 불러옴" 알림을 띄워도 파트 이름·필라멘트 번호가 그대로 들어온다(소스 확인: `bbs_3mf.cpp`의 model_settings 파싱은 설정 로드 여부와 무관).
- 색 쓰임: 2색이 기본. 밑판(Stroke) 어두운색 `#37474f`, 글자 `#ffb300`, 키캡 하부 `#ff8f00`(UI 기본값). 같은 색 = 같은 필라멘트 번호, 첫 등장 색이 1번.
- 일괄 출력은 **상판/하판 파일을 따로** 만든다(한 파일에 한 플레이트). 파트는 베드 좌표(0~256, z≥0)에 배치된 채로 저장한다.
- 키캡: 상판·하부 두 파트, 공차 0.3, 베드에 닿는 큰 면을 아래로.

## 2. 3MF 만드는 법 (완성본 규격)
1. **플레이트마다 일반 3MF 한 장** — `작업중/toolbox42/scripts/generic3mf.py` `write_generic_3mf(path, objects)` (mm3mf 방식 + 오브젝트 여러 개 + 베드 배치). 이것이 **주 산출물**이다.
2. 선택: Bambu 프로젝트 3MF(플레이트·필라멘트 색 포함) — `bbl_project.py`. 단, `project_settings.config`는 **반드시 `sample/`의 실제 내보내기 파일에서 유도**한다(`build_project_settings.py`: 키 집합 동일, 필라멘트별 키는 `Preset.cpp s_Preset_filament_options`, 노즐 변형별 키는 `PrintConfig.cpp filament_options_with_variant`, 값은 `resources/profiles/BBL/filament/` 공식 프로파일 체인). ChatGPT 등이 만든 설정 JSON은 쓰지 않는다. 사용자가 열어 보기 전까지는 "검증된 구조"라고만 하고 "열린다"고 단정하지 않는다.
3. STL은 파트별로 함께 둔다(슬라이서에 직접 넣는 대안).

## 3. 보내기 전 검사 (필수, 수치로 보고)
- 메시: watertight, `is_volume`, 파트 간 교집합 부피 0.
- 접지: 파트마다 **z=0 바닥 접촉 면적**과 첫 층 면적을 센다. 바닥이 들떠 있으면(링·돌기만 닿음) 출력물이 휜다 — 걸쇠가 그랬다(7 mm² → 775 mm²로 수정).
- 오버행: `overhang_check.py`(0.2 mm 층당 수평 돌출 ≤ 0.115 mm). 같은 오브젝트의 다른 파트가 받치는 면(로고 인레이 천장)과 수평 구멍 천장(⌀3.4 핀 구멍)은 위반이 아니다. 설계상 돌출(경첩 돌기, 본체 앞 귀)은 면적·높이를 적고 서포트 위치로 보고.
- 결합 치수: 수정 전/후 구멍 지름·중심·간격·단면적을 표로.
- 파일: lib3mf strict(일반 3MF는 경고 0이어야 함) / lenient(프로젝트 3MF는 `Unknown Model Metadata`·`Invalid Attribute` 경고만 허용 — sample 파일과 같은 경고 집합). 구조는 sample 파일과 파일 목록·루트 속성·metadata 이름을 대조.

## 4. 설계·메시 취급
- 3MF 정점은 XML 직접 파싱 → `trimesh.Trimesh(V,F,process=False)` (`load3mf.py`, p:path 하위 모델 지원). STL 왕복·정점 병합 금지.
- transform 12개: `M[:3,:3]=v[:9].reshape(3,3).T, M[:3,3]=v[9:]`. 정점 높이와 같은 z 단면은 깨짐 → 오프셋.
- 불리언은 manifold3d. 두께 보강은 "채움 솔리드 유니온"(기존 면을 깎지 않음). 바닥 접지는 z=1 윤곽을 z 0~1로 압출해 유니온(필렛 제거 → 접지 확보).
- 도구: 필렛·글자·STEP build123d / 메시 trimesh+manifold3d / 유기적 형태 Meshy(결과는 3절 검사 후).
- 벽 ≥1.2(실용 1.6), 끼움 공차 0.2~0.3, 관통 구멍 +0.3, 큰 면을 바닥으로. 다리·판처럼 휘는 부재는 2.7 mm는 얇다 → 5 mm 이상.

## 5. 보고
- 결론 한 줄 → 검사 수치 → 보낸 파일과 슬라이서에서 할 일(알림 문구, 필라멘트 2 지정 확인, 브림, 서포트) → 다음 한 걸음. 여기서 Bambu Studio 실행은 불가하므로 사용자가 열어 본 결과(알림 문구)를 받아 다음 판단을 한다.
- 뷰어 `viewer/3mf-viewer.html`로 파트·색 확인 가능.
