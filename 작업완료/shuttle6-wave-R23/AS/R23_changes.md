# R23 — 뚜껑도 원형으로 파서 앞콘 원형 뿌리를 받침

요청: 기존 뚜껑의 반원 홈을 그대로 두고 앞콘 위쪽만 얇게 만들지 말고, 뚜껑 홈도 원형으로 파서 연결한다.

AS/reference_R22_parts.pkl의 실제 내관과 뚜껑에서 시작합니다. 앞콘 아래 원형 뿌리를 반경34.6mm, Z6.2~10.1까지 연장해 기존 콘과0.1mm 겹쳐 합칩니다. 뚜껑에는 반경34.8mm 원형 홈을 Z6~10.2로 파며, 기존 좁은 하부 받침 자리·깊은30mm 사각 키 자리는 유지합니다. 사각 키의 원래 휨 여유 슬롯을 새 원통에서 똑같이 빼서 메우지 않습니다. 새로운 얇은 팔이나 별도 소형 부품을 추가하지 않습니다.

원형 뿌리 축방향 살은 실제 광선 측정5.049997mm입니다. 바닥 여유0.1999998mm, 끼움3.8000002mm. 3개 단면×32방향96개 표본으로 내관 외면과 뚜껑 내면의 간격을 측정했고 최소·1%·5%는0.199999mm입니다. 원형 구간 및 전체 뚜껑-내관 솔리드 겹침0mm³. 실제 출력 조립감과 반복 강도는 미검증입니다. 모든 원본 수치는 qc/front_joint_checks.json에 있습니다.

뒤 반원·외관 두 조각·클립·멈춤블록·시험편은 수정하지 않았으며7개 파트의 공칭 정점·면 배열이 R22와 같음을 검사했습니다. R22에서 내관과 뚜껑2개를 같이 교체합니다.

재현 순서: build.py → print_qc.py → assembly.py → front_joint_checks.py·cone_checks.py·keyring_checks.py → front_joint_section.py → front_cone_preview.py·preview.py·six_stage_gif.py·dock_preview.py → export_delivery.py → finalize_settings.py → release_check.py. R23_PARTS=drawer,cap는 기존7개 출력 메시·QC가 동일할 때만 쓰는 부분 재검사 옵션입니다. 처음 전체 재생성은 옵션 없이 검사합니다. 렌더는 MM_RENDER_BACKEND=software, MPLCONFIGDIR은 쓰기 가능한 폴더를 지정합니다.

공용 tools가 있는 저장소 구조에서 실행합니다. AS/셔틀콕_전용_동결도구.zip은 도구 동결 사본이고 reference_bambu_template.3mf는 실제 사용자 템플릿입니다. 신뢰하는 동봉 pickle 입력만 읽으십시오. AS의 R18~R22 문서·소스는 변경 이력이며 최신 규격은 상위README와 REQUESTS_CURRENT.md입니다.

원형 앞콘의 개별 콕 수직 인출 제한은 이번 결합부 보강과 별개입니다. 예전 GIF처럼 메시를 관통해 콕을 위로 꺼내지 않습니다. 잠금 해제·6단계 인출과 끝225mm 멈춤까지만 보여줍니다. 실물 콕 마찰·후퇴·기울임·사용 힘·피로는 검증하지 않았습니다.
