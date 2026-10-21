# 셔틀콕통 R9 인스타그램 미리보기 v3

사용자 최종 수정과 명시적 업로드 요청에 따라 게시했습니다.

게시물: https://www.instagram.com/p/DevvvV4DKvc/ — 이미지 4장 + 24초 영상 1개. 공식 API에서 CAROUSEL_ALBUM 및 첨부 수 5개를 확인했습니다. 게시 원장은 ../../publish-state/shuttle-square-slow-20261021.json입니다.

순서: 01 표지 → 02 모티브·초기 구상 → 03 R9 설계 → 04 상태별 회전 GIF → 05 취미 안내.

- 모델 출처: main 8d42642의 작업완료/shuttle6-wave-R9/review_parts.pkl 및 figures/review_states_R9.json. 기하 형상을 생성형 이미지로 다시 그리지 않았습니다.
- 표준 mm render의 presentation 옵션으로 흰 배경·격자/라벨 없는 캡처를 생성했습니다. 모델 형상은 변경하지 않았습니다.
- 이미지는 HTML 문서 레이아웃에 실제 캡처를 삽입하고 Chromium으로 캡처했습니다. 제목은 Dongle Bold, 본문은 Noto Sans CJK KR입니다.
- 글꼴 Dongle: Google Fonts, SIL Open Font License. https://github.com/google/fonts/tree/main/ofl/dongle
- 02의 프링글스 사진은 사용자 제공 스크린샷이며 원 작업자는 화면에 표시된 MARiiNSITO입니다. 초기 구상 이미지도 사용자 제공 자료입니다. 최종 결과·실물 출력 사진으로 취급하지 않습니다.
- GIF는 닫힘/열림/분리/몸통 두 조각의 회전 미리보기입니다. 연속 인출 동작을 실물로 검증했다는 의미가 아닙니다. Instagram 게시 시 MP4 변환이 필요합니다.
- 사실 근거: 프로젝트 README와 출력_접착_안내.md. 특정 브랜드의 셔틀콕 6개 수납, 출력 성공, 반복 내구는 검증 전입니다.

## 실제 벤치마킹한 계정 자료

Instagram Login API로 @sy_3dprintgarage의 최근 게시물 6개와 각 첫 두 이미지를 읽고 육안 확인했습니다. 원본 연구 기록은 ../../benchmark/status.json과 해당 JPG에 있습니다.

- 포션 키링 https://www.instagram.com/p/Dbk0guCoPNV/ : 둥근 한글, 다색 핵심 제목, 실제 제작 사진 + 공정 이미지.
- 카라비너 https://www.instagram.com/p/DbfdVaHoAmq/ : CAD 캡처와 제작 동기, 진행 중 상태를 솔직히 밝히는 구성.
- 부적 키링 https://www.instagram.com/p/DbdYWwRIM1Q/ : 실물의 큰 비중과 하단 짧은 컬러 제목.
- 셔틀콕 클리커 https://www.instagram.com/p/DbYgC6bkoSg/ : 설계 캡처에서 실출력 사진으로 이어지는 제작 이야기.
- 클리커 https://www.instagram.com/p/DbVq03bFeKh/ : 사진 위에 간결한 둥근 자막.
- 그립 https://www.instagram.com/p/DbVYdgYkpNi/ : 제작 환경과 사용 동기를 보여주는 기록.

개선 방향은 둥근 제목의 친근함을 유지하면서 두꺼운 외곽선·반복 그라데이션·복잡한 UI를 줄이고, 순백 배경·통일된 주황 포인트·짧은 설명·실제 모델 캡처를 사용하는 것입니다. 계정과 비교해 성과가 더 좋다고 검증한 것은 아닙니다.

사용자 피드백 반영: 제목을 더 크게 하고 Dongle Bold로 변경. 표지 제목 154px, 나머지 제목 130~144px, 본문 32~36px로 확대하고 겹침을 확인했습니다.

최종 사용자 수정: 제목은 Jua로 복원, 설명문은 크게 Gamja Flower로 변경했습니다. 마지막 안내는 사용자가 지정한 취미·권리·AI 작성 문구로 교체했습니다. 셔틀콕 모양은 가정된 수납 외피 치수에 맞춘 설명용 시각화이며 프린트할 파트나 실물 수납 검증 결과가 아닙니다. 도면의 몸통·받침 형상은 변경하지 않았습니다.

실제 게시본은 publish/의 JPEG·MP4이며 posts/shuttle-r9/approved.json에서 파일 해시와 원본 커밋을 고정했습니다. 게시 요청은 1회만 실행했고 중복 게시 방지 체크포인트를 저장했습니다.

재게시 수정: 내부 버전명은 독자용 이미지·본문에서 제거했습니다. 둥근 사각형으로 바꾼 과정과 세워 출력할 때 진동으로 깨지는 문제를 피하려고 몸통을 나눈 이유를 설명했습니다. 영상은 원본 동작 대비 5배 느리고 앞뒤 정지 구간을 포함해 24초입니다. 이전 게시물의 보관은 사용자가 직접 하기로 했으며 이 작업에서 삭제하거나 보관하지 않았습니다.
