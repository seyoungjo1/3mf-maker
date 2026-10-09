# 3mf-maker

3D 프린팅 모델을 설계하고 Bambu Studio용 3MF를 만드는 저장소입니다. **모델링·검사·렌더링·3MF 작업은 반드시 `.claude/skills/3d-print-3mf/SKILL.md`의 순서(설계 규칙 → 모델링 → QC → 조립 검증 → 보여주기 → 3MF → 보고)를 따릅니다.**

- 도구: `tools/qc_model.py`(QC), `tools/render_preview.py`(three.js 렌더·GIF), `tools/snapfit.py`·`tools/beam.py`(힘·휨), `tools/load3mf.py`, `tools/overhang.py`
- 폴더: `작업중/`(진행), `작업완료/`(완성), `sample/`(사용자가 올리는 참고 도면·3MF — 올라오면 분석해 스킬 references 에 반영)
- 답변은 한국어 존댓말. 커밋·푸시·PR·main 병합까지 자동으로 진행합니다.
