# 보안 노트

Astro 기반 한국어 정보보안 기술 블로그입니다. 기존 [티스토리](https://neoflux.tistory.com/)의 공개 글 24편 중 21편을 다듬어 이전했습니다. 주통기 Unix U-01~U-10은 모두 포함했고, 실습 5편·알고리즘 2편·Qualys 해설 4편을 선정했습니다. 최초 교육용 예제 5편은 초안으로 보관합니다.

블로그: [보안 노트](https://ryuyunseong.github.io/security-blog/) · [주통기 시리즈](https://ryuyunseong.github.io/security-blog/series/critical-infrastructure-unix-2026/) · [글별 이전 기록](docs/migration.md)

## 로컬 실행

Node.js 22.22 이상이 필요합니다. 이 작업에서는 Node.js 24를 사용했습니다.

```powershell
npm ci
npm run dev
```

출력되는 로컬 주소에서 확인합니다. 기본 주소는 `http://localhost:4321/`입니다.

```powershell
npm run check
npm test
npm run build
npm run verify
npm run preview
```

별도 린터는 추가하지 않았습니다. `check`는 Astro/TypeScript 진단, `test`는 공개 여부·경로·검색 유틸리티 검사, `verify`는 빌드된 전체 내부 링크·앵커·SEO·초안 제외·RSS·검색·사이트맵 일관성 검사입니다.

## 글 작성

1. `templates/post.md`를 `src/content/posts/영문-슬러그.md`로 복사합니다.
2. 제목, 설명, 날짜, 카테고리, 태그와 본문을 수정합니다. 날짜는 ISO `YYYY-MM-DD` 형식이며 해당 날짜의 UTC 00:00부터 공개 조건을 만족합니다. 한국 시간 자정을 지정하려면 `2026-10-16T00:00:00+09:00`처럼 시각과 시간대를 명시합니다.
3. 실제로 검증한 내용만 적고 공개 범위를 확인합니다. 예제라면 `example: true`를 사용합니다.
4. 검토를 마친 글만 `draft: false`로 바꿉니다. 필드가 없으면 기본값은 초안입니다.
5. 위 검증 명령을 실행해 화면을 확인합니다.

카테고리 ID는 `unix`, `web`, `infrastructure`, `cve`, `qualys`입니다. 태그는 한글·영문·숫자·공백·밑줄·하이픈을 허용하며 태그 페이지가 자동 생성됩니다. 파일 이름을 바꾸면 글 주소도 바뀝니다. 본문 내부 링크는 프로젝트 Pages의 하위 경로를 포함하는지 `npm run verify`로 확인합니다.

`draft: true`인 글과 미래 날짜의 글은 목록, 글 페이지, 카테고리, 태그, 검색, RSS, 사이트맵에서 제외합니다. 정적 사이트이므로 미래 날짜의 글은 날짜가 지난 뒤 재빌드해야 나타납니다. 두 검증용 문서는 실제 빌드 제외를 검증하기 위해 포함했습니다. 주통기 글은 `series: unix-2026`과 숫자 `seriesOrder`를 함께 지정하면 번호순 목차와 이전·다음 글 탐색으로 연결됩니다.

**주의:** 공개 GitHub 저장소에서는 초안 Markdown 원본도 공개됩니다. `draft`는 접근 제어가 아닙니다. 비밀·원문 로그·미공개 제보를 프로젝트에 넣지 마세요. Markdown은 저장소 편집 권한이 있는 신뢰된 작성자만 수정하는 전제이며 HTML도 작성할 수 있습니다.

## 구현 범위

- 정적 Markdown 콘텐츠, 스키마 검증, 코드 강조, 본문 목차, 코드 복사
- 카테고리·태그 페이지, 제목·설명·태그·카테고리 로컬 검색
- 밝은/어두운 테마, 시스템 기본값과 선택 저장, 모바일 한 열 배치
- 한국어 메타데이터, canonical, Open Graph, 구조화 데이터, RSS, 사이트맵, robots, 404
- [GitHub 프로필](https://github.com/ryuyunseong)과 기존 티스토리를 연결하는 포트폴리오

글 목록과 탐색은 JavaScript 없이 작동합니다. 검색·코드 복사·수동 테마 선택은 JavaScript가 필요합니다. 검색은 본문 전체를 색인하지 않습니다. 테마 외에는 방문자 데이터를 저장하지 않으며 외부 글꼴·분석 도구·추적기를 사용하지 않습니다.

## GitHub Pages

사용자 승인에 따라 `ryuyunseong/security-blog` 공개 저장소를 사용합니다. 실제 실행 결과는 [검증 및 인수인계](docs/review-notes.md)에 기록합니다.

배포 설정:

1. 저장소를 정하고 검토한 파일만 커밋·푸시합니다. 공개 저장소라면 Markdown 초안도 공개된다는 점을 확인합니다.
2. GitHub 저장소 Settings → Pages → Source에서 GitHub Actions를 선택합니다.
3. 저장소 Actions 변수 `PAGES_DEPLOY_ENABLED`를 `true`로 설정합니다. 이 값이 없으면 빌드만 수행하며 실제 배포 job은 실행하지 않습니다.
4. main 브랜치에 푸시하거나 워크플로를 수동 실행합니다. 이후 main 변경은 자동 배포됩니다. PR은 검증만 수행합니다.

워크플로는 GitHub 저장소 정보에서 `site`와 `base`를 계산합니다. 일반 저장소는 `https://OWNER.github.io/REPOSITORY/`, `OWNER.github.io` 저장소는 루트 주소를 사용합니다. 커스텀 도메인은 저장소 변수 `SITE_URL`과 `BASE_PATH`로 설정합니다. 루트 경로는 `BASE_PATH=/`로 명시합니다. `CNAME`이나 DNS는 이번 작업에 포함하지 않았습니다.

로컬에서 프로젝트 Pages 경로를 검증하려면:

```powershell
$env:SITE_URL = 'https://ryuyunseong.github.io'
$env:BASE_PATH = '/security-blog/'
npm run build
npm run verify
Remove-Item Env:SITE_URL
Remove-Item Env:BASE_PATH
```

위 명령은 로컬 빌드 검증이며 실제 배포는 main 푸시 또는 Actions 수동 실행으로 수행합니다.

배포 구성 참고: [Astro 공식 GitHub Pages 가이드](https://docs.astro.build/en/guides/deploy/github/). 배포 권한은 deploy job에만 부여했습니다. 제한된 개발 환경에서 Astro의 설정 폴더 접근이 막히면 해당 셸에서 `ASTRO_TELEMETRY_DISABLED=1`을 적용해 검증할 수 있습니다.

## 검토 자료

- [콘텐츠와 공개 범위](docs/content-plan.md)
- [글별 이전 기록](docs/migration.md)
- [화면 기준](docs/design.md)
- [검증 및 인수인계](docs/review-notes.md)

설정·컴포넌트·콘텐츠를 분리했습니다. 사이트 이름과 공개 프로필은 `src/lib/site.ts`, 화면 스타일은 `src/styles/global.css`, 배포 경로는 `astro.config.mjs`에서 관리합니다.
