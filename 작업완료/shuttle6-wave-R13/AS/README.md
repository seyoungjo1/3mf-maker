# R13 AS

동결도구 ZIP을 빈 디렉터리에 풀고, 완성 프로젝트를 작업완료/shuttle6-wave-R13에 둡니다. requirements 환경에서 MM_RENDER_BACKEND=software로 tools/mm.py make <프로젝트>/pipeline_review.json을 실행하면 새 메시·QC·조립·렌더를 재현합니다. pipeline_final.json은 통과한 검토 후 출력 플레이트를 생성합니다.

기본 build.py는 이전 리비전 없이 전체 형상을 계산합니다. update_rail_detents.py는 로컬 R12에서 외관 표면을 정확히 유지하는 증분 빌드용이며 R12가 별도로 필요합니다. 형상 원본만으로 다시 만드는 경우 build.py를 사용합니다.

설계검토_근거.md와 개정_기록.md를 먼저 보세요. 일반 미끄럼 간격, 홈 안착 여유, 탄성 통과 간섭은 서로 다른 수치입니다. 실물 피로 수명은 해석/실험 검증 전입니다.
