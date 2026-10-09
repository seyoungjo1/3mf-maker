# Bambu Studio 프로젝트 3MF — 실제 구조

출처: `bambulab/BambuStudio` `src/libslic3r/Format/bbs_3mf.cpp` (`_BBS_3MF_Exporter`, `_BBS_3MF_Importer`), `src/slic3r/GUI/Plater.cpp`, `src/slic3r/GUI/PartPlate.cpp`. GUI의 "프로젝트 저장"은 `SaveStrategy::SplitModel | ShareMesh` (SplitModel = 0x1000 | ProductionExt).

## 파일 목록 (내보내기 순서)

| 경로 | 내용 |
|---|---|
| `[Content_Types].xml` | `rels`, `model`, `png`, `gcode` 4개 Default |
| `Metadata/plate_N.png`, `plate_N_small.png` | 플레이트 썸네일 (있으면 model_settings에 `thumbnail_file`) |
| `Metadata/project_settings.config` | 전체 설정 JSON. 값은 문자열 또는 문자열 배열. `version` 포함 |
| `Metadata/model_settings.config` | 오브젝트/파트/플레이트/assemble (아래) |
| `Metadata/cut_information.xml` | 오브젝트마다 `<object id><cut_id id check_sum connectors_cnt/>` |
| `Metadata/slice_info.config` | `<header>` X-BBL-Client-Type=slicer, X-BBL-Client-Version; 슬라이스된 플레이트가 있으면 plate 섹션 |
| `3D/_rels/3dmodel.model.rels` | 하위 모델 파일마다 `Relationship Target="/3D/Objects/object_N.model" Type=".../2013/01/3dmodel"` |
| `3D/Objects/object_N.model` | ModelObject 하나당 하나. 메시 오브젝트만, `<build/>` 비어 있음 |
| `3D/3dmodel.model` | 메타데이터 + components 오브젝트 + build |
| `_rels/.rels` | rel-1 모델, rel-2 thumbnail(`/Metadata/plate_1.png`), rel-4 `bambulab.com/package/2021/cover-thumbnail-middle`, rel-5 `cover-thumbnail-small`(`plate_1_small.png`) |

## 3D/3dmodel.model

```xml
<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
       xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
       xmlns:BambuStudio="http://schemas.bambulab.com/package/2021"
       xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="Application">BambuStudio-02.00.00.00</metadata>   <!-- 'BambuStudio-'로 시작해야 m_is_bbl_3mf=true -->
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Copyright"></metadata> <metadata name="CreationDate">2026-10-09</metadata>
 <metadata name="Description"></metadata> <metadata name="Designer"></metadata> <metadata name="DesignerCover"></metadata>
 <metadata name="DesignerUserId"></metadata> <metadata name="License"></metadata> <metadata name="ModificationDate">…</metadata>
 <metadata name="Origin"></metadata> <metadata name="ProfileCover"></metadata> <metadata name="ProfileDescription"></metadata>
 <metadata name="ProfileTitle"></metadata> <metadata name="Title">Toolbox42</metadata>
 <resources>
  <object id="2" p:UUID="00000001-61cb-4c03-9d28-80fed5dfa1dc" type="model">
   <components>
    <component p:path="/3D/Objects/object_1.model" objectid="1" p:UUID="00010000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
   </components>
  </object>
 </resources>
 <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">
  <item objectid="2" p:UUID="00000002-b1ec-4553-aec9-835e5b724bb4" transform="1 0 0 0 1 0 0 0 1 128 128 0" printable="1"/>
 </build>
</model>
```

- **ID 규칙**: 오브젝트 순서대로 볼륨(파트) id를 먼저 매기고(1,2,…) 그 다음 번호가 오브젝트 id. `backup_id`는 1부터 오브젝트 순번.
- **UUID 접미사** (`hex8` = 8자리 16진수):
  - 오브젝트 `hex8(backup_id)` + `-61cb-4c03-9d28-80fed5dfa1dc` (공유 메시면 `-71cb-…`)
  - 메시(볼륨) `hex8(index + (backup_id<<16))` + `-81cb-4c03-9d28-80fed5dfa1dc`
  - component `hex8(index + (backup_id<<16))` + `-b206-40ff-9872-83e8017abed1`
  - build 고정 `2c7c17d8-22b5-4d84-8835-1976022ea369`, item `hex8(object_id)` + `-b1ec-4553-aec9-835e5b724bb4`
- transform 12개 = 3×4 열 우선(`m00 m10 m20 m01 … tx ty tz` 순이 아니라 c=0..3, r=0..2 순서로 `tr(r,c)`): 결과적으로 `1 0 0 0 1 0 0 0 1 tx ty tz`. 행벡터 규약 `v' = v·M + t`.
- 정점 좌표 `%.9g`. 메시는 오브젝트 로컬 좌표, 배치는 build item transform.

## 3D/Objects/object_N.model

같은 헤더. 메타데이터는 `BambuStudio:3mfVersion`만. `<resources>`에 `<object id="V" p:UUID="…-81cb-…" type="model"><mesh><vertices>…</vertices><triangles>…</triangles></mesh></object>`, 마지막 `<build/>`.

## Metadata/model_settings.config

```xml
<config>
  <object id="2">
    <metadata key="name" value="base"/>
    <metadata key="extruder" value="1"/>            <!-- 오브젝트 config 키들 -->
    <metadata face_count="23016"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="base"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>   <!-- 4x4 행 우선 -->
      <metadata key="extruder" value="1"/>           <!-- 파트 config 키들 -->
      <mesh_stat face_count="23016" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="01 Base"/>
    <metadata key="locked" value="false"/>
    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>
    <model_instance>
      <metadata key="object_id" value="2"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="100"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="2" instance_id="0" transform="1 0 0 0 1 0 0 0 1 128 128 0" offset="0 0 0" />
  </assemble>
</config>
```
- 선택 키: `bed_type`, `print_sequence`, `first_layer_print_sequence`, `filament_map_mode`, `filament_map`, `gcode_file`(슬라이스 저장 시), `thumbnail_no_light_file`, `top_file`, `pick_file`.
- part subtype: `normal_part`, `negative_part`, `modifier_part`, `support_blocker`, `support_enforcer`.

## 플레이트 배치 (PartPlateList)

- n장 → `cols = round(√n)`, `√n > round(√n)`이면 +1. 플레이트 i(0부터): `col = i % cols`, `row = i / cols`.
- 원점 = `(col·W·(1+0.2), −row·D·(1+0.2))`. P1S(256): 플레이트 2 = (307.2, 0), 플레이트 3 = (0, −307.2).

## 로더가 프로젝트로 인정하는 조건 (Plater.cpp)

1. `Application`이 `BambuStudio-`로 시작 → `m_bambuslicer_generator_version` 설정, 아니면 config를 아예 읽지 않음 → "The 3mf is not from Bambu Lab, load geometry data only".
2. `project_settings.config`의 `printer_model`이 설치된 BBL 벤더 모델명과 일치(`is_bbl_vendor_config`) 또는 `nozzle_diameter` 개수와 `extruder_type` 개수 일치(`check_project_config`). 아니면 "The 3mf file has invalid config, load geometry data only".
3. 파일 버전 > 앱 버전이면 `Newer3mfVersionDialog`; major가 크면 "lower version… cannot be fully loaded". 2.0.0 미만이면 prime tower 등 구형 변환. **기본값 `02.00.00.00` 권장.**
4. `model_settings.config` 파싱 실패 시 "Archive does not contain a valid model config"로 실패(bbl 3mf일 때만).
5. 로더는 XML 네임스페이스를 검사하지 않지만(expat 문자열 비교), 규격 리더(lib3mf, Windows 3D 뷰어)는 선언이 없으면 거부하므로 항상 선언한다.

## 검증 방법

- `lib3mf` lenient 읽기: 경고 `Unknown Model Metadata`(Title 등 Bambu 메타), `Invalid Attribute in namespace`(`printable`)는 정상. strict에서 네임스페이스 오류가 나면 안 됨.
- `viewer/3mf-viewer.html`로 p:path·플레이트·필라멘트 확인.
- 여기서 Bambu Studio 실행은 불가. 실제 열어본 결과(알림 문구)로 위 1~4 중 어느 조건인지 역추적.
