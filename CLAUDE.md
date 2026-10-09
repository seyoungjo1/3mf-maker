# 3mf-maker

3D 프린팅 모델을 설계하고 Bambu Studio용 3MF를 만드는 저장소입니다.

**시작 규칙 (모든 세션)**: 작업 전에 main 최신 내용을 기준으로 시작하고, `.claude/skills/3d-print-3mf/SKILL.md` 와 그 references(design_rules·presentation·bambu_3mf, 주제에 맞는 studies)를 **반드시 먼저 읽는다**. 세션 시작 훅(`.claude/hooks/session-start.sh`)이 main 동기화·의존 설치·렌더러 점검을 하고 스킬 전문을 출력한다. 훅 출력이 보이지 않으면 직접 `git merge origin/main` 후 SKILL.md 를 Read 한다. 렌더(`tools/render_preview.py`) 없이 결과를 보고하지 않는다 — 렌더러가 안 되면 `python tools/render_preview.py --check` 로 원인을 고친다. **모델링·검사·렌더링·3MF 작업은 반드시 `.claude/skills/3d-print-3mf/SKILL.md`의 순서(설계 규칙 → 모델링 → QC → 조립 검증 → 보여주기 → 3MF → 보고)를 따릅니다.**

- 도구: `tools/qc_model.py`(QC: 오버행/브리지 구분·EFC 반영), `tools/render_preview.py`(three.js 렌더·GIF), `tools/snapfit.py`·`tools/beam.py`(힘·휨), `tools/load3mf.py`, `tools/overhang.py`, `tools/efc.py`(첫 층 +0.15 선반영), `tools/gear.py`·`tools/hinge.py`
- 폴더: `작업중/`(진행), `작업완료/`(완성), `sample/`(사용자가 올리는 참고 도면·3MF — 올라오면 분석해 스킬 references 에 반영)
- 답변은 한국어 존댓말. 커밋·푸시·PR·main 병합까지 자동으로 진행합니다.

## 작업 시작 규칙 (절대 규칙 — 어기면 작업 무효)
1. **읽고 → 체크하고 → 시작한다.** 어떤 모델링·검사·렌더·3MF 작업이든 시작 전에 `Skill` 도구로 `3d-print-3mf`를 호출하고, `SKILL.md`와 `references/` 전부(`design_rules.md`, `presentation.md`, `bambu_3mf.md`, `snapfit_beam.md`, `sources.md`, `studies/*.md`)를 읽는다. 읽기 전에는 치수·방향·결론을 한 마디도 말하지 않는다.
2. 읽은 뒤 답변 첫머리에 아래 체크리스트를 적고 시작한다.
   `[ ] Skill 호출 [ ] SKILL.md+references 전부 읽음 [ ] 올라온 파일은 sample/ 복사·단면 실측 그림·스터디 기록 [ ] 설계 치수표(결합 치수는 상대 파트에서 측정) [ ] QC [ ] 조립 검증(실제 좌표에 놓은 교집합·간격·스윕) [ ] 렌더 5뷰+GIF 눈으로 확인 [ ] EFC 선반영·서포트 위치 명시 [ ] 3MF strict 0 [ ] 보고`
3. **스킬 순서(설계 규칙 → 모델링 → QC → 조립 검증 → 보여주기 → 3MF → 보고)에 어긋나는 작업은 절대 금지.** 단계를 건너뛰거나 순서를 바꾸지 않는다. 한 단계라도 빠지면 그 결과물은 보내지 않는다.
4. 금지 목록: 사용자가 올린 파일을 단면 그림 없이 설명하는 것 / 결합·끼움을 메시를 실제 좌표에 놓은 수치 없이 "맞다·안 맞다" 말하는 것 / QC 표·조립 수치·렌더 확인 없이 파일을 보내는 것 / 코끼리발 선반영(`tools/efc.py`)과 서포트 위치 명시 없이 3MF를 만드는 것 / 숫자 비교만으로 결합 가능성을 단정하는 것.
5. 당연한 단계(문서 읽기·실측·QC·커밋·푸시·병합)는 허락을 묻지 않고 진행한다. 묻는 것은 결합 치수 변경과 설계 방향의 선택뿐이며, 그때도 실측 그림을 먼저 보여준다.

## 파이프라인 규칙 (절대 규칙)
- **모든 결과물은 `python tools/pipeline.py <프로젝트>/pipeline_*.json` 을 통과한 것만 낸다.** QC → 플레이트 3MF(충돌·베드·lib3mf strict) → 조립 검증(상태별 교집합·간격·영역 간격·각도 스윕) → 렌더(플레이트 5뷰+회전 GIF, 조립 상태 GIF, 작동 GIF) → `REPORT.md` → 종료 코드(⚠ 있으면 1). 종료 코드 1 이면 파일을 보내지 않고 설계로 돌아간다.
- 프로젝트마다 `scripts/assembly_*.py` 의 `define(parts)` 로 상태·결합 쌍·스윕·추가 파트(명판 같은 내용물)를 정의한다. 결합 쌍은 접촉(`contact`)과 간격 요구(`min_gap`, `region`)를 명시한다.
- **검사 항목은 계속 추가한다.** 새 실패·새 규칙이 나오면 `tools/pipeline.py`(또는 `qc_model.py`·`overhang.py`)에 검사를 넣고 `tools/selftest.py` 에 그 경우를 추가한 뒤 PASS 를 확인하고 main 에 병합한다. 도구를 고치면 반드시 `python tools/selftest.py` 를 돌린다.
- 재사용 도구: `tools/generic3mf.py`(플레이트 3MF), `tools/check3mf.py`(strict), `tools/efc.py`(첫 층 선반영), `tools/render_preview.py`(렌더·GIF), `tools/qc_model.py`, `tools/snapfit.py`·`beam.py`.
