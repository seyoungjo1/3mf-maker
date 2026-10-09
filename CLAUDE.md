# 3mf-maker

3D 프린팅 모델을 설계하고 Bambu Studio용 3MF를 만드는 저장소입니다.

**절대 규칙 — 작업할 때마다 스킬을 읽는다**: 사용자 요청으로 작업(모델링·수정·QC·렌더·3MF·커밋·푸시·병합 포함)을 시작할 때마다, 기억이나 요약을 믿지 말고 **매번** 스킬 도구로 `3d-print-3mf` 를 불러(또는 `.claude/skills/3d-print-3mf/SKILL.md` 를 Read) 전문을 읽은 뒤 그 순서대로만 진행한다. 대화가 길어져 요약된 뒤에도, 같은 세션의 두 번째·세 번째 작업이어도 다시 읽는다.
**허락 규칙**: 모델을 만들거나 고치면 QC 후 렌더 사진(정면·분리 PNG + GIF)을 보내고 **사용자 허락을 받은 뒤에만** 3MF·커밋·푸시·병합으로 넘어간다. 장식 모델은 모델링 전에 요소 목록·스케일·부재·배열·색 분할 표(1~5)를 보여 검사받는다.

**시작 규칙 (모든 세션)**: 작업 전에 main 최신 내용을 기준으로 시작하고, `.claude/skills/3d-print-3mf/SKILL.md` 와 그 references(design_rules·presentation·bambu_3mf, 주제에 맞는 studies)를 **반드시 먼저 읽는다**. 세션 시작 훅(`.claude/hooks/session-start.sh`)이 main 동기화·의존 설치·렌더러 점검을 하고 스킬 전문을 출력한다. 훅 출력이 보이지 않으면 직접 `git merge origin/main` 후 SKILL.md 를 Read 한다. 렌더(`tools/render_preview.py`) 없이 결과를 보고하지 않는다 — 렌더러가 안 되면 `python tools/render_preview.py --check` 로 원인을 고친다. **모델링·검사·렌더링·3MF 작업은 반드시 `.claude/skills/3d-print-3mf/SKILL.md`의 순서(설계 규칙 → 모델링 → QC → 조립 검증 → 보여주기 → 3MF → 보고)를 따릅니다.**

- 도구: `tools/qc_model.py`(QC: 오버행/브리지 구분·EFC 반영), `tools/render_preview.py`(three.js 렌더·GIF), `tools/snapfit.py`·`tools/beam.py`(힘·휨), `tools/load3mf.py`, `tools/overhang.py`, `tools/efc.py`(첫 층 +0.15 선반영), `tools/gear.py`·`tools/hinge.py`
- 폴더: `작업중/`(진행), `작업완료/`(완성), `sample/`(사용자가 올리는 참고 도면·3MF — 올라오면 분석해 스킬 references 에 반영)
- 답변은 한국어 존댓말. 커밋·푸시·PR·main 병합까지 자동으로 진행합니다.
