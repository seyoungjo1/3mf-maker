# 인스타그램 작업실

계정: **@sy_3dprintgarage**. 기획·캡처·글 작성·검토·게시 기록을 이 폴더에서 관리합니다.

- [글·이미지 작성 방법](WRITING_GUIDE.md)
- [좋은 문장과 게시글 예시](EXAMPLES.md)
- [새 게시글 폴더 템플릿](templates/POST_TEMPLATE.md)
- [API와 GitHub Actions 연결](API_SETUP.md)
- [실제 계정 벤치마킹 자료](references/account/status.json)

## 게시글 목록

| 작업 | 상태 | 자료 | 실제 게시물 |
|---|---|---|---|
| 셔틀콕통 — 슬라이드 모티브·사각형 개선·분할 출력 | 재게시 완료 | [게시글 폴더](posts/2026-10-21-shuttlecock/README.md) | [현재 게시물](https://www.instagram.com/p/DevvvV4DKvc/) |
| 나만의 로고 부품케이스 — 자석 이름표 보관에서 시작 | 검토용 초안 | [게시글 폴더](posts/2026-10-21-logo-parts-case/README.md) | 미게시 |

## 폴더 규칙

```text
instagram/
├── WRITING_GUIDE.md        작성·캡처·글꼴·영상 규칙
├── EXAMPLES.md             문장과 실제 게시글 예시
├── API_SETUP.md            연결·토큰·게시 절차
├── config.json             계정 ID·username·API 버전 (토큰 제외)
├── templates/              새 게시글 양식
├── references/             계정 분석·참고 자료
├── history/                이전 지침 보존
└── posts/
    └── YYYY-MM-DD-topic/
        ├── README.md       기획·출처·구성·상태·게시 링크
        ├── caption.md      실제 게시할/게시한 글
        ├── *.png           검토용 이미지
        ├── *.gif           검토용 애니메이션
        ├── publish/        실제 업로드한 JPEG·MP4
        ├── history/        수정 이력·승인 원본·게시 결과
        └── publish-request.json  새 게시 요청 시에만 생성
```

본문·이미지를 수정하거나 폴더를 옮기는 것만으로 인스타그램에 게시하지 않습니다. **사용자가 게시를 요청한 경우에만** `publish-request.json`을 작성합니다. 실제 게시 결과는 해당 게시글의 history에 기록합니다.

GitHub Actions 실행 코드는 `.github/`에, 공용 모델 렌더 도구는 `tools/`에 둡니다. 토큰은 GitHub Secret `IG_ACCESS_TOKEN`에만 보관합니다. 원본 3MF와 모델 프로젝트는 기존 `작업중/`·`작업완료/`에 보존합니다.
