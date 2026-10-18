# 콘텐츠 형식

글 원문은 `src/content/posts/`의 Markdown 파일입니다. 메타데이터 정의는 `src/content.config.ts`, 카테고리·대상 정의는 `src/lib/taxonomy.mjs`에 있습니다.

| category | 내용 |
| --- | --- |
| critical-infrastructure | 주요정보통신기반시설 점검 항목 |
| unix | 일반 Unix·Linux 설정과 동작 |
| application-security | 인증·접근 제어·입력·파일 처리 |
| infrastructure | 시스템·네트워크 설정과 통신 |
| qualys | Qualys 기능과 공식 문서 해설 |
| coding-test | 자료구조·알고리즘 문제 풀이 |

`title`, `description`, `date`, `category`, `tags`가 기본 메타데이터입니다. 날짜는 `2026-10-17T09:00:00+09:00`처럼 시간대를 포함합니다. `sourcesChecked`는 참고 문서 확인 날짜입니다.

주통기 글은 `assessmentTarget`, `series`, 숫자 `seriesOrder`를 사용합니다. Unix 예시는 `assessmentTarget: unix`, `series: unix-2026`입니다. 대상·연도별로 번호순 목차가 생성됩니다. [주통기 항목 데이터](assessment-series.md)에 대상 ID와 범위가 있습니다.

`draft: true`와 미래 날짜 글은 페이지·검색·RSS에서 제외됩니다. 날짜가 지난 글은 다시 빌드한 시점에 반영됩니다. 홈은 최근 8편, 전체 목록은 페이지당 12편이며 글이 없는 대상은 표시되지 않습니다.
