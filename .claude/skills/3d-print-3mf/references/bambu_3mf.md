# Bambu Studio용 3MF 규칙 (검증된 것만)

- **주 산출물**: 일반 3MF (`작업중/toolbox42/scripts/generic3mf.py` = 열쇠고리 `mm3mf.py` 방식). 구조: `[Content_Types].xml`, `_rels/.rels`, `3D/3dmodel.model`(basematerials displaycolor + 파트 object + components 조립 object + build item), `Metadata/model_settings.config`(object/part name·matrix·extruder), `Metadata/Slic3r_PE_model.config`. Bambu Studio는 "not from Bambu Lab, load geometry only" 알림을 띄우지만 model_settings 의 파트 이름·extruder 는 읽는다(bbs_3mf.cpp 확인). lib3mf strict 경고 0 이어야 한다.
- 플레이트마다 파일 1장(상판/하판처럼). 파트는 베드 좌표(0~256) 그대로.
- **프로젝트 3MF**(선택): `bbl_project.py`. 구조는 `sample/`의 사용자 내보내기 파일과 대조(파일 목록·루트 속성·metadata 이름·UUID 규칙). `project_settings.config`는 `build_project_settings.py`로 샘플에서 유도: 키 집합 동일, 필라멘트별 키(Preset.cpp `s_Preset_filament_options`) 1→n, 변형별 키(PrintConfig.cpp `filament_options_with_variant`) 2→2n, `filament_dev_*`는 그대로, 공식 프로파일 체인(fdm_filament_common→pla→Bambu PLA Basic @base→@BBL P1S 0.4 nozzle) 값. 실제로 열리는지는 사용자 확인 후에만 "검증됨"으로 적는다.
- 실패 사례: ChatGPT가 만든 project_settings(없는 키 15개·배열 길이 불일치)를 넣은 v4는 열리지 않았다. 손으로 지어낸 Bambu 메타·설정 금지.
- 사용자 환경 샘플: `sample/test+lunch+box(1).3mf` — BambuStudio-02.08.02.61, P1S 0.4, Textured PEI, PETG HF 1색, 플레이트 2장, Auxiliaries 썸네일.
- **단색 플레이트(AMS 없이 색마다 따로 출력)**: 플레이트마다 그 색을 **1번 필라멘트**로 쓴다(`write_generic_3mf(material_order=[그 색])`). 사용자 틀(`sample/` 내보내기)의 필라멘트가 3개뿐이라 전 플레이트 공통 5색 번호를 쓰면 4·5번 플레이트의 Bambu 프로젝트 변환이 실패한다("필라멘트 4번 > 틀의 필라멘트 수 3", 인정전 램프 v2). 프로젝트 3MF 의 1번 필라멘트 색은 `pipeline.json` 의 `bambu.plate_colors {플레이트: [색]}` 으로 플레이트마다 준다(`mm make` 지원).
