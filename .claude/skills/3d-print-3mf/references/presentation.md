# 보여주기 규격 — 3d-print 열쇠고리 프로그램(templates/index.html) 그대로

- 장면: 배경 #1a1d21, HemisphereLight(0xffffff,0x444455,1.1) + DirectionalLight(1.2, (-40,-60,90)) + 아래 보조광(0.55), GridHelper 베드, 카메라 z-up.
- 재질: MeshStandardMaterial roughness 0.55, metalness 0.05, **flatShading** (각진 형상을 그대로 — 부드러운 음영은 모서리를 뭉갠다).
- 뷰 버튼: 기본(iso) / 상부 / 측면 / 밑면(격자 끔). 키캡처럼 결합 파트면 분리 / 조립-폄 / 조립-누름 상태 버튼.
- 상태줄: `완료 — 모델 크기 W × D × H mm`, 조각 분리·주의는 ⚠ 줄로 이어 붙임.
- 2색: 밑판 #37474f, 글자 #ffb300, 하부 #ff8f00.
- 헤드리스: `python tools/render_preview.py <파일> --out <dir> [--states states.json] [--colors a=#hex,...]` → view_{iso,top,side,bottom}[_상태].png + turntable.gif(36~54 프레임, 상태 순환). Chromium `/opt/pw-browsers/chromium` + swiftshader.
- 사용자에게는 GIF와 iso PNG를 파일로 보낸다. 조립 상태가 있으면 닫힘/열림/분리 세 상태를 모두 담는다.

## 설치 좌표 모델이 렌더에서 안 보이던 문제 (tv-pen-hanger v7, 2026-10-10)
- 조립을 설치 좌표(예: TV 밑면 z=0, 걸이대는 z<0)로 정의하면 모델이 베드 판 아래에 들어가 GIF에 거의 안 보였다. 사용자: "gif가 나한테 보여주는게 맞아? 안 보이는데".
- 이제 렌더러가 보이는 파트의 최저 z < −0.5 면 베드·격자를 숨긴다(`render_below_case` 자가검사). 주변물(TV 등)은 `'#hex@0.18'` 반투명.
- 단면 윤곽이 핵심인 압출형 부품은 `view_profile*.png`(x 방향 옆모습)를 함께 본다. 어두운 배경에서는 본체 색을 밝게(`#64b5f6` 등) 둔다.
- 보내기 전 GIF 프레임을 몇 장 뽑아 실제로 모델이 보이는지 확인한다.
