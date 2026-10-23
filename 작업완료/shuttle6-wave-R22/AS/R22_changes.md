# R22 — 앞콘 원형 복원

요청 정정: 원형으로 바꿀 대상은 앞콘입니다. 뒤끝은 반원을 유지합니다. 이전 R21에서 앞콘의 위쪽을 잘라낸 것을 복원했습니다.

## 모델링과 재현

AS/reference_R21_parts.pkl에서 시작합니다. AS/reference_R18_parts.pkl의 기존 갓 원본 Z235~249.8을 반경34.6mm의 원통으로 추출하고 Tz(259.8)·Ry(180°)로 앞쪽 Z10~24.8로 옮깁니다. 위쪽 절반을 제거하지 않고 내관과 합칩니다. 뒤끝·맞춤 홈·바깥통은 다시 만들지 않고 R21 실제 배열을 그대로 유지합니다. 결과에서 내관 이외8파트 정점·면 배열이 R21과 같음을 검사합니다.

불리언·간소화 후5개 단면×16각도에서 원형 내면을 확인하고 원본 곡선과 비교합니다. 소스 복사 최대 오차0.0262mm, 실제 방사방향 반지름 범위 최대0.0538mm이며 메시 다각화·간소화의 오차를 포함합니다. 각도별 내면에 모두 닿으므로 위쪽이 열린 반콘이 아닙니다. 실제 단면·확대 렌더는 최종 메시를 사용합니다.

실행 순서: scripts/build.py → print_qc.py → assembly.py → cone_checks.py·keyring_checks.py·stop_checks.py → cone_section.py → front_cone_preview.py·preview.py·six_stage_gif.py·dock_preview.py → export_delivery.py → finalize_settings.py → release_check.py.

공용 tools가 있는 저장소 구조에서 실행하며 AS/셔틀콕_전용_동결도구.zip은 도구 동결 사본입니다. MM_RENDER_BACKEND=software, MPLCONFIGDIR은 쓰기 가능한 위치를 지정합니다. R22_PARTS=drawer는 기존8파트 출력 메시와QC가 동일할 때만 사용하는 부분 검사 옵션이며 최초 재생성 시에는 전체 검사를 실행합니다. AS/reference_R21_build.py와 이전 버전 문서는 이력입니다. 최신 형상 기준은 상위README·REQUESTS_CURRENT.md입니다. 신뢰하는 동봉 pickle 입력만 읽으십시오.

## 실제 동작의 한계

앞콘이 원형으로 닫히면 기존 수직 콕 꺼내기 장면은 내관을 통과합니다. raw 충돌 검사를 보존하고 GIF에서 그 장면을 제거했습니다. 잠금 해제·6단계 인출·225mm 양옆 멈춤까지는 실제 최종 메시로 표시합니다. 후퇴·기울임을 포함한 개별 콕 인출 경로·깃털 간 마찰·손 접근은 검증하지 않았습니다. 수납 게이지와 서랍 경로·출력 파일 검증을 실물 사용성·수명 검증으로 표현하지 않습니다.

## 교체

R21에서 내관1개만 교체합니다. 뚜껑·클립·스토퍼·외관·시험편은8개 모두 그대로입니다. M3 하드웨어는 상위README와 같습니다. 현재 AS에는 수정에 쓰인 입력·Bambu 템플릿·소스·검사 자료를 동봉합니다.
