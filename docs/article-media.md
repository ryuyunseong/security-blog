# 글 이미지와 실행 기록

SVG는 개념을 설명하는 편집 도식이다. 실제 시스템이나 제품 화면이 아니며 `scripts/build-article-diagrams.mjs`와 `src/data/article-visuals.json`에서 재생성한다. 이미지 안의 짧은 설명 외에 본문의 캡션과 대체 텍스트를 제공한다.

## 본문 안에 배치하기

그림과 실행 기록을 글의 시작이나 끝에 한꺼번에 붙이지 않는다. 개념을 비교하는 문단 뒤에 그림을, 코드를 실행한 뒤 결과를 해석하는 문단 근처에 실행 기록을 둔다. 비교표가 이미 결과를 설명한다면 원본 출력은 접어 중복을 줄인다. 모든 글의 자료 순서를 같게 맞추지 않는다.

Markdown에서 다음 표식을 각각 독립된 줄에 넣는다. 앞뒤에는 관련 설명을 두며 표·목록·코드 블록 안이나 문장 중간에는 넣지 않는다. 링크 정의나 각주가 있다면 참조하는 문장과 같은 구간에 둔다.

| 표식 | 표시하는 자료 | 배치 기준 |
| --- | --- | --- |
| `[[diagram]]` | 해당 글의 설명 도식 | 흐름·관계·비교를 이해해야 하는 지점에 한 번 |
| `[[photo]]` | 등록한 사진·표현 이미지 | 사진이 있는 글에서 준비물이나 환경 설명 옆에 한 번 |
| `[[run:1]]` | 첫 번째 실제 실행 기록 | 관련 코드 뒤에 출력과 함께 표시 |
| `[[run:1:fold]]` | 접힌 첫 번째 실행 기록 | 앞의 표·짧은 출력과 내용이 겹칠 때 사용 |

여러 실행 기록은 저장된 순서에 따라 `[[run:2]]`, `[[run:3:fold]]`처럼 각각 배치한다. 기록이 없는 문서 해설 글에는 run 표식을 넣지 않는다. 빌드와 예약 발행 검사는 누락·중복·순서 오류와 설명 없이 자료가 붙은 구성을 거부한다. 표식은 서버 빌드에서 컴포넌트로 바뀌므로 JavaScript 없이도 본문과 자료를 읽을 수 있다.

70줄을 넘는 본문 코드는 전체 내용을 보존해 접어 제공한다. 펼친 코드에도 복사 버튼을 제공한다. 열린 실행 기록에서 출력이 16줄보다 길면 앞부분과 전체 출력 펼치기를 함께 제공한다. 명령·표준 출력·표준 오류·종료 코드와 실행 환경은 원본 기록을 사용한다. 실습 결과를 다시 실행한 것처럼 날짜를 갱신하지 않는다.

화면 확인 시 `node scripts/verify-daily-browser.mjs`는 예약 글 묶음이 있으면 그 글을, 없으면 전체 공개 글을 검사한다. `BLOG_QA_ALL=1`로 항상 전체를 검사할 수 있다. 1440·390·320px에서 도식·사진·모든 원본 코드와 출력·접기 동작·앵커·가로 넘침을 확인한다.

본문의 그림을 누르면 `figures/글-슬러그/` HTML 페이지에서 본다. 처음에는 화면 너비에 맞춰 전체 그림을 보여 주고, `그림 확대`를 선택하면 원본 크기 이상으로 넓혀 그림 영역만 좌우로 스크롤한다. `화면에 맞추기`로 돌아가거나 원문으로 이동하고, 원본 SVG를 내려받을 수도 있다. 그림 페이지도 공개 글만 대상으로 생성하고, 검색 색인에서는 제외하며 canonical은 원문을 가리킨다.

SVG를 문서로 직접 열면 Codex 내장 브라우저의 `Electron Isolated Context`와 Edge의 확장 프로그램에서 `animation` 관련 예외가 재현됐다. SVG 자체에는 스크립트나 XML 파싱 오류가 없고 표시도 정상이었다. HTML 안의 `<img>`로 열어 이 경로를 피한다. 브라우저·확장 프로그램 자체의 오류를 고친 것은 아니며, SVG를 직접 여는 주소는 그대로 남아 있다.

`public/assets/posts/isolated-learning-lab.png`는 Qualys 학습 환경 글에 쓰는 표현 이미지다. 내장 image_gen 도구로 생성했고 제품이나 운영 경험의 증거로 사용하지 않는다. 최종 생성 프롬프트:

> Create a refined editorial photograph for a Korean information-security learning blog article about preparing an isolated home security lab. Wide landscape 3:2 composition, understated daylight, a clean warm white desk with a small unbranded compact computer, two Ethernet patch cables in muted forest green, and a closed dark notebook, a small unbranded network switch with cables connected. Soft depth of field, natural realistic materials, calm precise independent technical writer's workspace. No people, no screens, no software dashboards, no brand logos, no readable text, no hacker cliches, no glowing binary or locks. The photo is conceptual illustrative content, not evidence of a real deployment. High quality understated magazine photography, white and forest green palette.

코드 실행 출력은 생성 이미지에 넣지 않고 접근 가능한 HTML 텍스트로 표시한다. `scripts/run-article-examples.py`가 본문 코드를 추출해 실행하고 `src/data/executions.json`에 출력·종료 코드·환경·본문 코드 해시를 기록한다. 설명과 판단 범위는 `src/data/execution-context.json`에 둔다. 임시 절대 경로만 `$LAB`으로 통일하며, 출력 내용을 성공처럼 꾸미거나 종료 코드를 바꾸지 않는다.

가상 계정·그룹·파일만 사용한다. U-01은 별도 설정의 OpenSSH 해석만, U-02~U-10은 파일 수집·비교만 확인했다. TLS·CORS는 루프백 통신이다. 실행 시 생성한 인증서·키·파일은 임시 폴더 정리와 함께 제거했다. Qualys 제품은 실행하지 않았고 실행 결과로 표시하지 않는다.
