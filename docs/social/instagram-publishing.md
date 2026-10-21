# GitHub Actions + Instagram 공식 API 운영안

작성일: 2026-10-21 / 사용자 표시 시간대: Asia/Seoul

대상 저장소: seyoungjo1/3mf-maker. 작업 브랜치: `codex/instagram-publishing`.
주 소재는 이 저장소의 3MF 캡처 결과물이다. 이미지 선택·문구·해시태그를 함께 준비하며 [게시글 편집 기준](editorial-guide.md)을 따른다. 이번 단계는 지침과 스터디 기록이며 main 병합이나 자동 게시 활성화는 포함하지 않는다.

## 결정과 확인 범위

사용자가 선택한 방식은 GitHub Actions와 Instagram 공식 API이다. 본인 계정 하나를 운영하는 것으로 시작한다. Instagram API with Instagram Login을 우선 선택한다. Meta 공식 Postman 자료에 따르면 Business/Creator 계정이 대상이며 Facebook 페이지 연결은 필수가 아니다.[1]

“내 계정”은 소유권에 대한 설명이므로 개인 계정 유형인지 프로페셔널 계정인지 별도로 확인해야 한다. 개인 유형이면 API 게시 전에 전환이 필요하다. 프로페셔널 전환에 따른 공개 범위 등은 Instagram 전환 화면에서 확인하고 사용자가 결정한다.

Meta 개발자 문서 일부는 이번 조사에서 429 또는 접근 실패가 발생했다. 확인 가능한 Meta 공식 Postman 자료와 GitHub 공식 문서를 근거로 구조를 정리했다. 앱 심사·접근 등급, 토큰 수명과 갱신 조건, 최신 미디어 제한 및 API 버전은 실제 설정 시 개발자 콘솔과 연결된 공식 문서에서 다시 확인한다. 외부 블로그의 수치를 확정 규칙으로 사용하지 않는다.

## 권장 구조

초안 JSON + 이미지 → 내용 검증 → GitHub Actions 수동 실행 → 계정 확인 → 미디어 컨테이너 생성 → 처리 상태 확인 → 게시 → 게시 결과 조회 → 영속 기록

- 저장소에는 코드와 게시 초안만 둔다. 비공개 초안은 비공개 저장소에 보관한다.
- 이미지 제공은 별도 HTTPS 저장소/CDN을 권장한다. Meta 서버가 인증 없이 가져올 수 있는 실제 파일 URL이어야 한다. 만료형 URL이면 처리 완료까지 충분한 유효 시간을 확보한다.
- 비공개 GitHub 파일이나 로그인 필요한 Drive 공유 링크를 이미지 원본 URL로 가정하지 않는다.
- 초기 범위는 단일 JPEG 이미지 + 캡션이다. 릴스·캐러셀은 별도 미디어 규격과 흐름을 검증한 후 확장한다.
- Instagram은 일반 텍스트만으로 피드 게시하는 경로가 아니다. 이미지 또는 영상 콘텐츠를 준비한다.

## 준비 순서

1. 대상 GitHub 저장소와 Instagram username을 확정한다.
2. Instagram 앱에서 계정 유형을 확인한다. Business/Creator가 아니라면 전환 여부를 결정한다.
3. Meta for Developers에서 앱을 만들고 Instagram Login 구성을 선택한다. 본인 계정을 앱 설정에 연결하고 필요한 역할/초대 수락을 완료한다.
4. 최소 권한 instagram_business_basic, instagram_business_content_publish를 구성한다.[1] 본인 계정용 접근 등급과 테스트 권한을 콘솔에서 확인한다. 제3자 계정 서비스로 확장할 경우 심사 요구사항을 별도로 검토한다.
5. 공식 로그인 또는 콘솔에서 제공하는 지원 절차로 Instagram User access token을 발급한다. Facebook Page token을 대신 사용하지 않는다.
6. 지원 API 버전을 선택해 고정하고 읽기 요청으로 계정 ID와 username을 대조한다.
7. 미디어 호스팅을 준비하고 Meta가 접근 가능한지 검증한다.
8. 아래 Secrets/Variables를 설정한다. 실제 값을 문서에 기록하지 않는다.
9. 로컬 검증과 dry-run 후, 사용자가 요청한 테스트 게시 한 건으로 실제 동작을 확인한다.
10. 수동 게시와 중복 방지·상태 복구가 검증된 다음 예약 기능을 활성화한다.

## GitHub 설정

### 비밀번호 없이 연결하고 작성부터 업로드까지 처리하기

사용자는 Instagram/Meta 공식 화면에서 직접 로그인하고 권한을 승인한다. 에이전트에게 ID/비밀번호·2FA 코드·세션 쿠키를 전달하지 않는다. OAuth를 쓸 경우 등록된 redirect URI와 state 검증을 구성하고 code 교환은 신뢰하는 서버/로컬 환경에서 수행한다. 개발자 콘솔에서 해당 계정용 토큰 발급을 지원하면 공식 절차를 사용할 수 있다.

발급된 토큰은 사용자가 GitHub 저장소 Settings → Secrets and variables → Actions에 IG_ACCESS_TOKEN으로 직접 입력한다. 앱 시크릿이 필요한 교환 작업이 있으면 별도 Secret으로 저장한다. 에이전트는 비밀 값을 읽지 않고 코드에서 Secret 참조만 구성한다. 토큰도 비밀번호처럼 취급한다.

목표 운영은 사용자 요청 → 프로젝트 기록 검토 → 공개용 캡처와 캡션 준비 → 확정된 게시 내용으로 Actions 실행 → 공식 API 게시 → permalink 확인이다. 로그인은 초기 연결 및 재인증 때 사용자가 수행한다. 이후 매번 Instagram에 로그인하지 않고 게시할 수 있도록 설계한다. 현재 Actions 실행 경로와 게시 워크플로는 아직 구현·검증하지 않았으므로 채팅에서 즉시 업로드 가능하다고 보고하지 않는다.

향후 기본 자동 게시 범위(어느 프로젝트·이미지·말투·시점)를 사용자가 정하면 그 범위 안에서 작성과 업로드를 묶어 수행할 수 있다. 현재의 연결 방식 상담은 개별 게시물의 발행 요청으로 취급하지 않는다.

| 종류 | 이름 | 용도 |
| --- | --- | --- |
| Secret | IG_ACCESS_TOKEN | Instagram Login으로 발급한 사용자 토큰 |
| Variable | IG_USER_ID | 검증된 대상 계정 ID |
| Variable | IG_EXPECTED_USERNAME | 잘못된 계정 게시를 막는 비교 값 |
| Variable | META_API_VERSION | 콘솔에서 확인한 고정 버전 |
| Secret | IG_APP_SECRET | 초기 토큰 교환 등 필요한 작업에만 제공 |
| Secret | 미디어 저장소 인증 정보 | 업로드가 필요한 경우에만 추가 |

Secrets는 Actions의 secrets 컨텍스트에서 환경변수로 전달한다.[3] 기본 GITHUB_TOKEN으로 저장소 Secrets를 자동 갱신할 수 있다고 가정하지 않는다. 자동 토큰 갱신을 구현할 경우 별도 최소 권한 자격 또는 전용 비밀 저장소의 갱신 기능을 설계한다.

Actions는 workflow_dispatch로 시작한다. permissions는 기본 contents: read로 제한하고, 게시 상태를 저장소에 커밋하는 설계일 때만 필요한 쓰기 권한을 추가한다. 게시 작업에는 계정별 concurrency와 cancel-in-progress: false를 사용한다. concurrency는 동시 실행 제어이며 영속적인 중복 방지를 대체하지 않는다.

workflow 입력값을 shell 명령 문자열에 직접 삽입하지 않는다. JSON 파일이나 환경변수로 전달하고 Python에서 검증한다. 제3자 Action은 검증 후 커밋 SHA로 고정한다. fork PR과 pull_request_target에서 비밀을 사용해 게시하지 않는다.

## 게시 데이터 예시

```json
{
  "post_id": "2026-10-21-first-post",
  "image_url": "https://YOUR-CDN.example/photo.jpg",
  "caption": "게시할 문구와 해시태그",
  "scheduled_at": null,
  "status": "draft"
}
```

URL은 설명용이며 실제 실행 불가하다. 예약할 때 scheduled_at에는 2026-10-22T19:00:00+09:00처럼 시간대가 있는 ISO 8601 값을 쓴다. 같은 post_id의 이미지·문구를 바꾸어 재게시하지 말고 변경 이력과 새 게시 의도를 구분한다.

## 게시 API 흐름

Instagram Login용 기본 호스트는 graph.instagram.com이다. 버전과 계정 ID를 붙여 media 컨테이너를 생성하고, 처리 상태를 조회한 뒤 media_publish에 creation_id를 전달하는 구조로 구현한다. Meta 공식 컬렉션은 컨테이너 처리 완료 후 게시하는 흐름을 제공한다.[2] 컬렉션에는 Facebook Login 예제도 포함되어 있으므로 URL과 토큰을 그대로 복사하지 않는다.

구현 시 상태 머신:

draft → validated → creating → container_created → ready → publishing → published

별도 예외 상태: failed / unknown

- 외부 쓰기 전에 post_id와 실행 의도를 영속 기록한다. 기록 저장소에 접근할 수 없으면 게시하지 않는다.
- 컨테이너 ID를 받으면 다음 단계 전에 저장한다. 상태 조회는 제한 시간 내에서 수행한다.
- 게시 직전에 publishing 상태를 저장하고, 성공 응답의 media_id 및 permalink를 기록한다.
- 응답 유실이나 프로세스 종료가 발생하면 컨테이너 상태와 계정 미디어를 조회해 대조한다. 확정할 수 없으면 unknown에서 멈춘다.
- 재실행 시 published는 건너뛰고, publishing/unknown은 확인 절차로 진입한다. 새 컨테이너를 곧바로 만들지 않는다.
- Actions cache/artifact만을 유일한 게시 원장으로 사용하지 않는다. 별도 DB 또는 동시성·충돌 처리가 있는 저장소 기록을 사용한다.

## 예약과 토큰 관리

Actions schedule은 실행이 지연되거나 높은 부하에서 누락될 수 있고 기본 브랜치의 워크플로를 사용한다.[4] 사용자에게 정시 보장을 약속하지 않는다. 초 단위/분 단위 정확도가 필요한 경우 다른 스케줄러를 검토한다.

구현 시 서울 시간과 스케줄러 시간대 설정을 명확히 한다. UTC cron을 사용할 경우 KST 19:17은 UTC 10:17이다. 정각을 피하는 편이 부하를 줄이는 데 도움이 되지만 지연을 없애지는 않는다. 늦게 실행된 게시물을 자동으로 게시할지 건너뛸지는 활성화 전에 운영 기준으로 정한다.

토큰은 영구 자격으로 취급하지 않는다. 발급 응답의 expires_in과 공식 토큰 문서를 확인해 만료 시점을 저장하고 충분한 여유를 두고 갱신한다.[5] 갱신 토큰은 비밀 저장소에 저장하고 다음 실행에서 새 값으로 읽기 검증을 한다. 만료·권한 철회·비밀번호 변경 등 인증 오류 발생 시 게시를 중지하고 공식 재인증 절차로 복구한다. 자동 갱신이 준비되기 전에는 수동 갱신과 만료 알림 절차로 운영한다.

## 구현 완료 판정

- dry-run에서 Meta 쓰기 요청이 0회인지 확인한다.
- ID/username 불일치, 접근 불가능한 이미지, 누락된 Secret은 게시 전에 실패한다.
- 같은 post_id를 연속 실행해도 두 번째 게시가 생기지 않는다.
- 게시 POST 응답 유실 상황에서 무조건 재시도하지 않는다.
- 로그와 오류 보고서에 토큰·앱 시크릿·서명된 민감 URL이 남지 않는다.
- 실제 게시 테스트는 사용자 요청 범위 안에서 한 건 수행하고 permalink로 확인한다.

## 남은 입력 및 현재 상태

확인된 정보: GitHub 저장소 seyoungjo1/3mf-maker, 별도 작업 브랜치, 주 게시 소재는 3MF 캡처 결과물.
필요한 정보: Instagram username과 계정 유형, Meta 앱 생성 여부, 미디어 호스팅 선택.
비밀번호·토큰·앱 시크릿은 채팅으로 요청하지 않는다. 사용자가 GitHub Secrets 또는 적절한 비밀 저장소에 직접 입력한다.

현재 문서와 작업 지침을 별도 브랜치에 작성했다. workflow/script 배포, 계정 연결, 토큰 발급, 실제 게시 및 예약 활성화는 수행하지 않았다. 원격 반영 여부는 실제 push 결과로 별도 보고한다.

## 공식 참고 자료

1. Meta 공식 Instagram Login 컬렉션: https://www.postman.com/meta/instagram/folder/6raa77c/instagram-api-with-instagram-login
2. Meta 공식 Instagram API 컬렉션: https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
3. GitHub Secrets: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
4. GitHub 워크플로 이벤트: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
5. Meta 토큰 참고 문서(실설정 시 재확인): https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token/
6. Meta 게시 문서(이번 조사 직접 접근 제한): https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing

## 2026-10-21 연결 확인 결과

- 사용자 제공 계정 ID: `17841465071386831`.
- GitHub Actions에서 `IG_ACCESS_TOKEN`을 참조해 `GET /v25.0/me?fields=user_id,username` 읽기 확인에 성공했다. 계정은 `sy_3dprintgarage`이며 제공 ID와 일치한다.
- `config/instagram.json`에 ID와 username을 고정하고 `.github/scripts/instagram_check.py`가 대조한다. 토큰 값은 저장소·로그에 기록하지 않는다.
- `.github/workflows/instagram-check.yml`은 연결 확인만 한다. 확인을 위한 push 트리거는 해당 브랜치의 연결 코드/설정 변경에만 반응한다.
- 증거: `connection-status.json`. 이 성공은 프로필 읽기 확인이며 콘텐츠 게시 권한·미디어 업로드·캐러셀 게시 성공을 의미하지 않는다.
- 게시 실행 워크플로, 공개용 이미지 호스팅, 마지막 안내 장 제작·캐러셀, 중복 방지 원장은 다음 구현 범위다. 자동 예약과 실제 게시는 활성화하지 않았다.
