# 3mf-maker

3D 프린터용 3MF 파일을 만드는 프로젝트 저장소입니다.

## 폴더 구조

```
3mf-maker/
├─ 작업중/      진행 중인 프로젝트 (프로젝트별 하위 폴더)
├─ 작업완료/    완성된 프로젝트 (작업중에서 완료 후 이동)
└─ sample/      참고한 도면·참고 3MF (사용자가 올림, 작업의 기준 자료)
```

## 도구와 스킬

- 작업 지침(항상 적용): `.claude/skills/3d-print-3mf/SKILL.md` + `references/` (설계 규칙·스냅/휨 식·보여주기 규격·Bambu 3MF 규칙·출처)
- 스터디 기록: `.claude/skills/3d-print-3mf/references/studies/` (설계 방법론, 샘플 실측, 경첩, 기어, 교훈). 시험 파트·렌더는 `작업중/_study/`
- 도구: `tools/` — QC(`qc_model.py`), 렌더·GIF(`render_preview.py`), 스냅/휨 계산(`snapfit.py`, `beam.py`). 사용법 `tools/README.md`

## 기본 환경

- 프린터 Bambu Lab P1S, 필라멘트는 보통 **PLA**, Bambu Studio 02.08.x.
- 완성본은 **Bambu Studio에서 열리는 3MF**여야 합니다.
- 참고 프로젝트: seyoungjo1/3d-print의 열쇠고리·키캡 (출력 방식·색 구성의 기준).

## 작업 흐름

1. 새 프로젝트는 `작업중/<프로젝트명>/` 폴더에서 시작합니다.
2. 모델·스크립트·문서·검증 결과를 해당 폴더 안에 모아 둡니다.
3. 출력 검증까지 끝나 완성되면 폴더 전체를 `작업완료/<프로젝트명>/`으로 이동합니다.

## 현재 프로젝트

| 상태 | 프로젝트 | 설명 |
|---|---|---|
| 작업중 | [toolbox42](작업중/toolbox42/README.md) | Bambu P1S용 42슬롯 소형 툴박스. v5: 걸쇠 접지·손잡이 두께 수정, 플레이트별 일반 3MF |
