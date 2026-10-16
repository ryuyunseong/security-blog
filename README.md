# 보안 노트

Unix와 웹·인프라 보안을 작은 실습과 코드로 확인하는 한국어 기술 블로그입니다. 주통기 점검 시리즈, 알고리즘 풀이, Qualys 문서 해설을 제공합니다.

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
4. 설명 그림을 등록하고 검토를 마친 글만 `draft: false`로 공개합니다.
5. 위 검증과 화면 확인을 마친 뒤 커밋·푸시합니다.

카테고리는 unix·web·infrastructure·cve·qualys입니다. 초안과 미래 날짜의 글은 페이지·목록·검색·RSS에서 제외됩니다. 미래 날짜의 글은 날짜가 지난 뒤 다시 빌드해야 공개됩니다. 공개 저장소의 초안 파일은 누구나 읽을 수 있으므로 비밀 자료를 넣지 않습니다.

## 그림과 실행 기록

도식은 src/data/article-visuals.json을 수정한 뒤 생성합니다.

```bash
node scripts/build-article-diagrams.mjs
```

실행 기록은 src/data/executions.json, 범위와 해석은 execution-context.json에서 관리합니다. 각 기록에 실행 날짜·환경·본문 코드 해시를 남깁니다. 기존 17편의 재현은 Linux에서 다음 명령으로 실행합니다. Python·Bash·awk·GNU stat·OpenSSH·OpenSSL·libacl을 사용하며 별도 Python 패키지는 필요하지 않습니다.

```bash
python3 scripts/run-article-examples.py
```

임시 파일과 루프백만 사용하며 실제 계정·PAM·SSH 설정은 변경하지 않습니다. 기존 17편 재현 후에도 이후 글의 개별 실행 기록은 보존합니다. 사이트 빌드에서는 실습을 자동 실행하지 않습니다. [이미지·실행 기록 기준](docs/article-media.md)을 참고하세요.

## 배포와 운영

main 푸시는 GitHub Actions의 검사·빌드를 거쳐 GitHub Pages로 배포됩니다. PR은 검증만 수행합니다. 배포 활성화 변수는 `PAGES_DEPLOY_ENABLED=true`이며, 사이트 경로는 저장소 정보에서 계산합니다.

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
