# R21 수정·재현·AS

현재 규격은 상위README와 REQUESTS_CURRENT.md입니다. AS의 R18/R19/R20 문서는 변경 이력이며 현재 형상 지침이 아닙니다. 특히 R20은 콘이 뒤쪽에 남았으므로 철회했습니다.

## 실제 형상 변경

1. R20 내관의 뒤쪽 기존 빈 콘을 먼저 솔리드로 채우고 새 Ø65 공간을 Z231~244에 뚫어 잔여 콘을 없앴습니다. Z235 이후 윗면은 원래 양옆 걸림 포스트만 남기고 열었습니다. 끝은 Z244~249.8의5.8mm 두께 반원입니다.
2. R18 원본 뒤컵 갓 Z235~249.8의 실제 메시를 추출했습니다. Tz(259.8)·Ry(180°)로 뚜껑쪽 Z10~24.8로 옮기고 윗면을 열었습니다. 대체 프로파일로 재작성하지 않았습니다.
3. 뒤집은6개 게이지는 Tz(248)·Ry(180°)입니다. 코르크가 앞을 향하고 마지막 깃털 끝은 Z238입니다. 물리적인 콕6개 실측값은 아닙니다.
4. 외관 본체Z3~7.3 안쪽에 맞춤 반원 자리를 추가했습니다. 실제 반원·양옆 포스트·레일 어깨 윤곽을 비워 여유0.2mm, 입구0.35mm를 줬습니다. 끝벽3mm는 보존했습니다.
5. thin_housing.py는 기존 C외곽의 법선으로 외부 표면만 최대1.2mm 옮깁니다. 내면·레일(중앙|Y|≤10)·끝받침·이음부·잠금부는 보존하고30mm 길이로 부드럽게 전이합니다. 장식을 삭제하거나 새 패턴으로 바꾸지 않았습니다. 감소 전후 부피는 qc/housing_thinning.json에 있습니다.
6. 불리언 후 내관에 생성된 부피0의10면 잔여 조각을 확인하여 제거했습니다. 제거 대상 총 절대부피1e-5mm³ 이하를 코드에서 검사합니다. 실제 솔리드를 합쳐 다중조각 문제를 숨기지 않았습니다.

## 재현

저장소 tools가 있는 구조에서 Python환경에 numpy,trimesh,shapely,manifold3d,scipy,mapbox-earcut,matplotlib,Pillow,lib3mf 등을 준비합니다. AS/셔틀콕_전용_동결도구.zip은 당시 공용 도구의 동결 사본입니다. AS/reference_R20_parts.pkl과 reference_R18_parts.pkl은 실제 모델 입력, reference_bambu_template.3mf는 실제 사용자 템플릿입니다. pickle은 신뢰하는 동봉 소스만 읽습니다.

순서: scripts/build.py → print_qc.py → assembly.py → cone_checks.py·keyring_checks.py·stop_checks.py·channel_wall_checks.py → cone_section.py·housing_section.py → preview.py·six_stage_gif.py·dock_preview.py → export_delivery.py → finalize_settings.py.

렌더 환경변수 MM_RENDER_BACKEND=software. MPLCONFIGDIR은 쓰기 가능한 경로를 지정합니다. print_qc.py의 R21_PARTS는 변경 파트만 검사하면서 **이미 동일함을 확인한** 나머지의 출력 메시·QC를 재사용하는 옵션이며, 최초 실행은 전체 파트로 합니다.

## 검사의 해석

반원 자리의 실제 강체 경로는 별도로0~12mm 검사했습니다. 일반 인출의 딸깍 돌기에는 원래 의도된 간섭이 있으므로 assembly.py는 원본 강체 겹침과 기존 눌림 대체모델 결과를 모두 기록합니다. 대체모델은 채널 밖 돌기만 잘라낸 기구 경로 확인이며 변형·힘·수명 해석이 아닙니다. 새로 작동력이나 내구성 검증을 했다고 주장하지 않습니다.

6단계·첫 콕 꺼내기 GIF는 최종 메시를 사용합니다. 치수 게이지는225mm/Ø64mm/포갬28mm 가정이며 실제 깃털에 대한 접촉 해석이 아닙니다. 외관 최대 외형은 보강부 때문에 유지되며, 실제 필라멘트량은 슬라이스로 판단합니다.

R20에서 교체할 부품은 아래통·위통·내관3개입니다. 그 외6개 공칭 메시 배열은 동일합니다. 뚜껑과 클립의 M3 하드웨어·양쪽 스페이서 규격은 상위README를 따릅니다.
