# gukse-clicker

국새 클리커 — 하부 80 정사각(검정, 굴곡 단면+구름무늬) + 국새 몸통(금색 버튼, MX 스위치 2개 대각) + Tripo 거북

## 체크리스트 (작업 시작 전에 적고, 끝나면 `python tools/mm.py checklist 작업중/gukse-clicker/pipeline.json` 으로 자동 판정)
`[ ] Skill 호출 [ ] SKILL.md+references 전부 읽음 [ ] 올라온 파일은 sample/ 복사·단면 실측 그림·스터디 기록 [ ] 설계 치수표(결합 치수는 상대 파트에서 측정) [ ] QC [ ] 조립 검증(실제 좌표에 놓은 교집합·간격·스윕) [ ] 렌더 5뷰+GIF 눈으로 확인 [ ] EFC 선반영·서포트 위치 명시 [ ] 3MF strict 0 [ ] 보고`

## 설계 치수표
`scripts/build.py` 의 `P` 와 같게 유지한다. 결합 치수는 '출처'에 상대 파트에서 잰 근거(단면 그림 파일·측정 명령)를 적는다. 바꾸기 전에 사용자에게 묻는다.

| 이름 | 값 (mm) | 의미 | 출처 |
|---|---|---|---|
| W | 40.0 | 본체 폭 | 틀 기본값 |
| D | 30.0 | 본체 깊이 | 틀 기본값 |
| H | 15.0 | 본체 높이 | 틀 기본값 |
| WALL | 3.0 | 벽 두께(≥1.2) | 틀 기본값 |
| FLOOR | 3.0 | 바닥 두께 | 틀 기본값 |
| LID_T | 2.0 | 뚜껑 두께 | 틀 기본값 |

## 출력 조건
- Bambu P1S · PLA · 층 0.2 · 노즐 0.4 · 코끼리발 보정 0.15 → 첫 층 +0.15 선반영(`tools/efc.py`, build.py 가 함)
- 서포트 위치: (오버행이 있으면 pipeline.json `support_zones` 에 파트·높이·면적을 적는다 — 없으면 '없음')

## 실행
```
python tools/mm.py make 작업중/gukse-clicker/pipeline.json      # 빌드 → QC → 3MF → 조립 → 렌더/GIF → REPORT.md → Bambu 프로젝트 3MF → 체크리스트
```
