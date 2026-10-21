# Instagram 연결과 게시 운영

## 확인된 연결

- 저장소: `seyoungjo1/3mf-maker`, 작업 브랜치: `codex/instagram-publishing`
- 계정: `@sy_3dprintgarage`, Instagram 계정 ID: `17841465071386831`
- 방식: Instagram Login + GitHub Actions
- 사용 중인 API 버전: `v25.0` (이 계정으로 조회·게시 확인)
- 설정: [config.json](config.json). 토큰 값은 포함하지 않습니다.
- 인증: GitHub 저장소의 Actions Secret **IG_ACCESS_TOKEN**
- 연결 확인과 이미지·영상 캐러셀의 실제 게시까지 완료했습니다. 결과는 게시글별 history에 기록합니다.

## 비밀번호 없이 운영

사용자가 Meta/Instagram 공식 화면에서 직접 로그인하고 필요한 권한을 승인합니다. 발급된 토큰은 GitHub Settings → Secrets and variables → Actions에 직접 저장합니다. 비밀번호·2FA 코드·토큰·앱 시크릿을 채팅이나 저장소에 기록하지 않습니다.

Instagram Login 경로는 `graph.instagram.com`을 사용합니다. Facebook Login용 호스트·권한·토큰과 섞지 않습니다. 필요한 게시 권한은 `instagram_business_basic`, `instagram_business_content_publish`입니다. 토큰 만료·권한 철회에 대비해 발급 응답과 Meta 콘솔의 유효기간을 확인합니다. 자동 토큰 갱신은 아직 구현하지 않았습니다.

## 실행 코드

- `.github/scripts/instagram_check.py`: 토큰 소유 계정의 ID와 username을 읽기 요청으로 대조
- `.github/scripts/instagram_benchmark.py`: 계정의 최근 게시물과 이미지를 읽어 참고 자료로 저장
- `.github/scripts/instagram_publish.py`: 명시적으로 승인한 캐러셀을 생성·게시하고 체크포인트 기록
- `.github/workflows/instagram-publish.yml`: `instagram/posts/**/publish-request.json` 변경에만 반응

문서·이미지·본문 수정이나 폴더 정리만으로 게시하지 않습니다. 과거 승인 파일은 history에 보관하고 새 요청 파일과 구분합니다.

## 게시 절차

1. 게시글 폴더에서 caption.md와 이미지·영상을 준비하고 검토합니다.
2. 사용자의 게시 요청이 확인되면 실제 업로드 JPEG·MP4를 커밋합니다.
3. 그 커밋 SHA와 각 파일의 SHA-256, 확정된 본문, 새 post_id를 `publish-request.json`에 기록합니다. `approved_by_user`는 실제 요청이 있을 때만 true로 둡니다.
4. 요청 파일 하나를 별도 커밋으로 push합니다. Actions가 바뀐 요청 하나를 선택해 `IG_POST_MANIFEST`로 전달합니다.
5. 계정·파일 해시·공개 미디어 URL을 확인한 뒤 컨테이너를 만들고 처리 완료를 기다려 게시합니다.
6. 해당 게시글의 history에 상태를 매 단계 저장합니다. 성공은 media_id·permalink·첨부 수로 확인합니다.

같은 post_id의 재실행은 기존 원장을 확인합니다. 게시 응답이 불명확하면 unknown으로 멈추고 결과를 확인하며 무조건 재시도하지 않습니다. 계정별 concurrency를 사용하고 원장을 push할 수 없으면 외부 쓰기 단계로 넘어가지 않습니다.

## 이미지·영상 제공

실제 게시 파일은 승인 당시 커밋의 `raw.githubusercontent.com` URL로 고정합니다. 현재 브랜치 파일이 바뀌어도 승인 당시 내용이 바뀌지 않도록 합니다. 과거 승인 JSON에 남아 있는 `docs/social/...` 경로는 당시 커밋에서 유효하므로 그대로 보존합니다.

정지 이미지는 JPEG, 영상은 H.264/AAC MP4로 준비합니다. GIF는 Instagram 게시 전에 MP4로 변환합니다. 공개 URL·파일 크기·비율·영상 처리 상태를 확인하고 최신 API 규격이 달라지면 재검토합니다.

## 게시 후 수정

이미지·영상 교체가 필요한 경우 수정본을 새 게시물로 올립니다. 원래 글의 보관·삭제는 사용자 지시와 지원 기능에 따라 별도로 처리합니다. 셔틀콕통은 사용자가 기존 글을 직접 보관하기로 선택했습니다.

## 공식 참고 자료

- [Meta 공식 Instagram API 컬렉션](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)
- [Meta Instagram Login 콘텐츠 게시](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [최초 조사 기록](history/initial-api-study.md)
