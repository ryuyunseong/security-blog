# 글 이미지와 실행 기록

SVG는 개념을 설명하는 편집 도식이다. 실제 시스템이나 제품 화면이 아니며 `scripts/build-article-diagrams.mjs`와 `src/data/article-visuals.json`에서 재생성한다. 이미지 안의 짧은 설명 외에 본문의 캡션과 대체 텍스트를 제공한다.

본문의 그림을 누르면 `figures/글-슬러그/` HTML 페이지에서 크게 본다. 작은 화면에서는 그림 영역만 좌우로 스크롤하며, 원문으로 돌아가거나 원본 SVG를 내려받을 수 있다. 그림 페이지도 공개 글만 대상으로 생성하고, 검색 색인에서는 제외하며 canonical은 원문을 가리킨다.

SVG를 문서로 직접 열면 Codex 내장 브라우저의 `Electron Isolated Context`와 Edge의 확장 프로그램에서 `animation` 관련 예외가 재현됐다. SVG 자체에는 스크립트나 XML 파싱 오류가 없고 표시도 정상이었다. HTML 안의 `<img>`로 열어 이 경로를 피한다. 브라우저·확장 프로그램 자체의 오류를 고친 것은 아니며, SVG를 직접 여는 주소는 그대로 남아 있다.

`public/assets/posts/isolated-learning-lab.png`는 Qualys 학습 환경 글에 쓰는 표현 이미지다. 내장 image_gen 도구로 생성했고 제품이나 운영 경험의 증거로 사용하지 않는다. 최종 생성 프롬프트:

> Create a refined editorial photograph for a Korean information-security learning blog article about preparing an isolated home security lab. Wide landscape 3:2 composition, understated daylight, a clean warm white desk with a small unbranded compact computer, two Ethernet patch cables in muted forest green, and a closed dark notebook, a small unbranded network switch with cables connected. Soft depth of field, natural realistic materials, calm precise independent technical writer's workspace. No people, no screens, no software dashboards, no brand logos, no readable text, no hacker cliches, no glowing binary or locks. The photo is conceptual illustrative content, not evidence of a real deployment. High quality understated magazine photography, white and forest green palette.

코드 실행 출력은 생성 이미지에 넣지 않고 접근 가능한 HTML 텍스트로 표시한다. `scripts/run-article-examples.py`가 본문 코드를 추출해 실행하고 `src/data/executions.json`에 출력·종료 코드·환경·본문 코드 해시를 기록한다. 설명과 판단 범위는 `src/data/execution-context.json`에 둔다. 임시 절대 경로만 `$LAB`으로 통일하며, 출력 내용을 성공처럼 꾸미거나 종료 코드를 바꾸지 않는다.

가상 계정·그룹·파일만 사용한다. U-01은 별도 설정의 OpenSSH 해석만, U-02~U-10은 파일 수집·비교만 확인했다. TLS·CORS는 루프백 통신이다. 실행 시 생성한 인증서·키·파일은 임시 폴더 정리와 함께 제거했다. Qualys 제품은 실행하지 않았고 실행 결과로 표시하지 않는다.
