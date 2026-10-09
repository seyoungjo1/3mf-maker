# 보여주기 규격 — 3d-print 열쇠고리 프로그램(templates/index.html) 그대로

- 장면: 배경 #1a1d21, HemisphereLight(0xffffff,0x444455,1.1) + DirectionalLight(1.2, (-40,-60,90)) + 아래 보조광(0.55), GridHelper 베드, 카메라 z-up.
- 재질: MeshStandardMaterial roughness 0.55, metalness 0.05, **flatShading** (각진 형상을 그대로 — 부드러운 음영은 모서리를 뭉갠다).
- 뷰 버튼: 기본(iso) / 상부 / 측면 / 밑면(격자 끔). 키캡처럼 결합 파트면 분리 / 조립-폄 / 조립-누름 상태 버튼.
- 상태줄: `완료 — 모델 크기 W × D × H mm`, 조각 분리·주의는 ⚠ 줄로 이어 붙임.
- 2색: 밑판 #37474f, 글자 #ffb300, 하부 #ff8f00.
- 헤드리스: `python tools/render_preview.py <파일> --out <dir> [--states states.json] [--colors a=#hex,...]` → view_{iso,top,side,bottom}[_상태].png + turntable.gif(36~54 프레임, 상태 순환). Chromium `/opt/pw-browsers/chromium` + swiftshader.
- 사용자에게는 GIF와 iso PNG를 파일로 보낸다. 조립 상태가 있으면 닫힘/열림/분리 세 상태를 모두 담는다.
- 정점 좌표는 float32 정밀도를 그대로 JSON으로 전달한다. 소수점 3자리 반올림은 얇은 불리언 삼각형을 퇴화·반전시켜 손잡이가 찌그러져 보이게 한다.
- 출력 플레이트는 베드를 표시하지만 조립·작동 렌더는 `show_bed=False`: 조립 좌표의 z<0 부품을 출력판이 가리지 않게 한다. 상태에 없는 부품은 숨기고 카메라 범위에서도 제외한다.
