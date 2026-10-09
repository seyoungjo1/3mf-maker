# 3MF Viewer

`3mf-viewer.html`을 브라우저에서 열고(파일 더블클릭) 3MF를 끌어다 놓습니다. three.js와 fflate를 jsdelivr CDN에서 받으므로 인터넷이 필요합니다.
- 파트별 치수·삼각형 수·위치, 켜기/끄기, 와이어프레임, 256×256 베드
- Bambu 프로젝트: 플레이트 탭, 파트별 필라멘트 색, `3D/Objects/*.model`(p:path) 하위 파일, `model_settings.config` 파트 이름
- 파일 검사: 네임스페이스 누락, 필수 파일 누락, 열린 모서리·잘못된 인덱스
"샘플" 버튼은 `sample/toolbox42.b64.txt`(3MF를 base64로 담은 텍스트)가 옆에 있을 때만 동작합니다.
