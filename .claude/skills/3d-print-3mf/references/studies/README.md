# 스터디 기록 (계속 추가)

| 날짜 | 제목 | 핵심 |
|---|---|---|
| 2026-10-09 | [design-method.md](design-method.md) | 도면을 짜는 순서와 규칙 전반 — 치수 잡기, 방향, 두께, 공차, 기구(경첩·기어·스냅·나사/인서트·자석), 상자·뚜껑, 시험편, 검증 |
| 2026-10-09 | [lunchbox-sample.md](lunchbox-sample.md) | 사용자 샘플(MakerWorld Utility Box, Imagn) 실측 — 벽 3 mm 통일, 뚜껑은 뒤집어 45° 챔퍼(0.2/층), 본체 바닥 필렛은 숨김 |
| 2026-10-09 | [hinge.md](hinge.md) | 핀 경첩·프린트인플레이스 경첩 규칙, `tools/hinge.py` |
| 2026-10-09 | [gear.md](gear.md) | 인벌류트 기어·헤링본 규칙, `tools/gear.py` |
| 2026-10-09 | [lantern-sample.md](lantern-sample.md) | 일본 LED 랜턴 샘플 실측 — 정방향 지붕(오버행 0), 0.8 mm 발광 갓, 색별 파트/플레이트, 전용 서포트 파트 |
| 2026-10-09 | [korean-palace-lamp-motif.md](korean-palace-lamp-motif.md) | 창덕궁 인정전 모티브 램프 — 한국답게 보이는 요소(팔작·합각·공포 띠·월대 계단·둥근 기둥·띠살 창호), 파트=색 구성 초안, 결정 사항 |
| 2026-10-09 | [toolbox42-lessons.md](toolbox42-lessons.md) | Toolbox42 v4~v6에서 배운 것(실패 포함) |

추가 샘플(미실측, 다음 차례): Click_Pen(클릭 펜 기구), Clock_box(태엽 시계 상자), Desk Organizer(OpenSCAD), Little Trees Slider Vent(슬라이더), Mento_Dog, POJEMNICZEK1(트위스트 락 통), 所有部件集合(모듈형 책상 도구, P2S 9 플레이트).

규칙: `sample/`에 새 파일이 오면 (1) `tools/qc_model.py` (2) 모서리·벽·구멍 실측 (3) 조립 상태 간격 (4) 렌더 → 이 폴더에 `<이름>.md`로 남기고 이 표에 한 줄 추가, main에 병합.
