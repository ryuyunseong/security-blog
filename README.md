# 보안 노트

Unix 점검 방법, 웹 보안 실습, Qualys 기능을 정리한 한국어 기술 블로그입니다. 주통기 점검 시리즈, 알고리즘 풀이, Qualys 공식 문서 해설을 제공합니다.

[블로그](https://ryuyunseong.github.io/security-blog/) · [주통기 시리즈](https://ryuyunseong.github.io/security-blog/series/critical-infrastructure-unix-2026/) · [GitHub](https://github.com/ryuyunseong)

## 시작하기

Node.js 22.22 이상이 필요합니다.

```bash
npm ci
npm run dev
```

로컬 주소는 http://localhost:4321/ 입니다.

```bash
npm run check
npm test
npm run build
npm run verify
```

`check`는 Astro·TypeScript 진단, `test`는 콘텐츠·코드·검색 회귀 검사, `verify`는 생성된 페이지의 링크·이미지·앵커·SEO·검색/RSS/사이트맵 일관성 검사입니다.

## 글 작성

1. templates/post.md를 src/content/posts/영문-슬러그.md로 복사합니다.
2. 제목·설명·날짜·카테고리·태그와 본문을 작성합니다. 한국 시간은 `2026-10-17T09:00:00+09:00`처럼 시각과 시간대를 명시합니다.
3. 실습 환경과 실제 결과, 해석과 한계를 확인합니다. 시리즈 글은 `series: unix-2026`과 숫자 `seriesOrder`를 함께 지정합니다.
4. 설명 그림과 실제 실행 기록을 등록하고, 관련 본문 사이에 배치 표식을 넣습니다. [그림·캡션 검토 순서](docs/article-media.md)로 본문·노드·캡션을 대조하고, 검토를 마친 글만 `draft: false`로 공개합니다.
5. 위 검증과 화면 확인을 마친 뒤 커밋·푸시합니다.

공개 카테고리는 unix·web·infrastructure·qualys입니다. 홈은 최근 8편, 전체 글 목록은 페이지당 12편을 보여 줍니다. 초안과 미래 날짜의 글은 페이지·목록·검색·RSS에서 제외됩니다. 미래 날짜의 글은 날짜가 지난 뒤 다시 빌드해야 공개됩니다. 공개 저장소의 초안 파일은 누구나 읽을 수 있으므로 비밀 자료를 넣지 않습니다.

## 그림과 실행 기록

도식은 src/data/article-visuals.json을 수정한 뒤 생성합니다.

```bash
node scripts/build-article-diagrams.mjs
```

실행 기록은 src/data/executions.json, 범위와 해석은 execution-context.json에서 관리합니다. 각 기록에 실행 날짜·환경·본문 코드 해시를 남깁니다. 기존 17편의 재현은 Linux에서 다음 명령으로 실행합니다. Python·Bash·awk·GNU stat·OpenSSH·OpenSSL·libacl을 사용하며 별도 Python 패키지는 필요하지 않습니다.

그림은 본문의 `[[diagram]]`, 실행 기록은 코드 뒤의 `[[run:1]]` 위치에 표시합니다. 표가 이미 결과를 설명한다면 `[[run:1:fold]]`로 원본 로그를 접어 제공합니다. 자료를 모아서 붙이거나 모든 글을 같은 순서로 구성하지 않습니다. 70줄보다 긴 코드는 원문을 유지한 채 펼쳐 읽도록 표시합니다.

```bash
python3 scripts/run-article-examples.py
```

임시 파일과 루프백만 사용하며 실제 계정·PAM·SSH 설정은 변경하지 않습니다. 기존 17편 재현 후에도 이후 글의 개별 실행 기록은 보존합니다. 사이트 빌드에서는 실습을 자동 실행하지 않습니다. [이미지·실행 기록 기준](docs/article-media.md)을 참고하세요.

## 배포와 운영

main 푸시는 GitHub Actions의 검사·빌드를 거쳐 GitHub Pages로 배포됩니다. PR은 검증만 수행합니다. 배포 활성화 변수는 `PAGES_DEPLOY_ENABLED=true`이며, 사이트 경로는 저장소 정보에서 계산합니다.

작성 시각은 한국 시간 매일 18:30입니다. 주통기·Qualys를 각각 최대 1편, 수·토요일에는 추가 실습을 1편까지 검토합니다. 추가 글은 주 2편 이내이며 품질 기준을 충족할 때만 발행합니다. 현재 활성화된 Codex 예약은 PC와 앱이 켜져 있어야 실행됩니다. 같은 시각으로 구성한 GitHub 호스팅 워크플로는 API 키 연결 복구와 생성 미리보기 검증을 남겨 비활성 상태입니다. `OPENAI_API_KEY` Secret 등록 후 `DAILY_PUBLISH_ENABLED=true`로 활성화하며 그때 로컬 예약을 중지해 중복을 방지합니다. 클라우드 생성에는 별도 API 요금이 발생합니다. [실행 모드·보류·복구 절차](docs/publishing.md)를 확인하세요.

프로젝트 Pages 경로를 로컬에서 확인하려면 PowerShell에서 다음을 실행합니다.

```powershell
$env:SITE_URL = 'https://ryuyunseong.github.io'
$env:BASE_PATH = '/security-blog/'
npm run build
npm run verify
```

글 목록과 본문은 JavaScript 없이 읽을 수 있습니다. 검색·코드 복사·수동 테마 선택은 JavaScript가 필요합니다. 검색은 제목·설명·태그·카테고리를 대상으로 합니다.

## 문서

- [작성 기준](docs/content-plan.md)
- [매일 발행 운영](docs/publishing.md)
- [화면 기준](docs/design.md)
- [검증과 인수인계](docs/review-notes.md)
- [2026-10-17 전체 화면·문체 검토](docs/site-review-2026-10-17.md)
