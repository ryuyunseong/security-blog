# 도식과 실행 기록

설명 도식은 `src/data/article-visuals.json`과 `scripts/build-article-diagrams.mjs`에서 생성합니다. 실제 제품 화면이 아닌 개념도입니다. 넓은 화면용 SVG와 767px 이하 화면용 `.mobile.svg`는 같은 데이터를 사용합니다.

## 도식 데이터

`title`은 대체 텍스트와 SVG 제목, `note`는 SVG 설명, `caption`은 본문 캡션입니다. 지원 형식과 검증은 `src/lib/diagram-spec.mjs`에 있습니다.

| kind | 관계 | 노드 수 |
| --- | --- | --- |
| flow | 처리 순서 | 3 |
| compare | 두 조건 비교 | 2 |
| layers | 독립된 점검 지점 | 3 |
| merge | 두 입력의 합류 | 3 |
| matrix | 항목별 역할 | 3 |
| timeline | 사건 순서 | 3 |
| decision | 질문·예·아니요 | 3 |
| cycle | 반복 절차 | 3 |
| topology | 두 주체와 공통 대상 | 3 |
| intervals | 정수 구간과 병합 결과 | 4 |

`timeline`의 간격은 시간에 비례하지 않습니다. `intervals` 노드는 `[이름, 시작, 끝]`이며 시작과 끝은 0~255 정수 문자열입니다. 마지막 행은 병합 결과이고 막대는 양 끝을 포함한 원소 수에 비례합니다.

`compare`에는 선택 항목 `detail`을 지정할 수 있습니다. `{"kind":"path-tree"}`는 두 부분으로 된 상대 경로를 폴더와 파일로, `{"kind":"path-order"}`는 ` → `로 구분한 두 디렉터리를 탐색 순서로 표시합니다. 두 형식은 각 노드의 두 번째 문구를 사용합니다. `{"kind":"permission-bits","modes":["0400","0600"]}`는 각 노드에 적힌 모드를 소유자·그룹·기타의 `rwx` 셀로 표시합니다. `modes`는 노드 순서대로 두 개이며 특수 비트를 제외한 4자리 8진수만 받습니다. 이 그림은 파일이나 디렉터리를 직접 조회하지 않습니다.

## 구조화된 설명 그림

`scene`을 지정하면 기존 `nodes` 대신 표의 행, 파일 속성, 계정, 배열 원소처럼 구조가 있는 자료를 그립니다. `layout`은 `sequence`(순서), `compare`·`parallel`(독립 비교), `merge`(두 입력의 합류), `fork`(한 입력의 두 분류)입니다. 패널은 1~3개이고 합류·분기는 3개를 사용합니다.

`panels`의 `type`은 `table`, `file`, `actor`, `set`, `array`, `split`, `numberline`, `states`, `bytes`, `attachments`를 지원합니다. 표는 `headers`·`rows`, 파일은 `mode`·`status`, 배열·집합은 `values`, 상태 그래프는 `nodes`·`edges`, 바이트 막대는 `[이름, 정수 바이트]`의 `bars`를 받습니다. `attachments`는 `source: [이름, 아이콘]`과 `targets: [[대상 이름, 아이콘, 연결 역할]]`로 같은 목록의 연결 위치를 표시합니다. 공통 `fields`는 `[필드명, 값]` 쌍입니다. 종류별로 허용하지 않는 필드와 잘못된 범위·인덱스는 거부합니다.

파일의 `status`는 `present`, `absent`, `error`, `unknown`으로 수집 자료를 구별하며 보안 판정을 뜻하지 않습니다. `mode`의 일반 `rwx`와 SUID·SGID·Sticky는 따로 표시합니다. 수직선과 바이트 막대는 값에 비례합니다. 모바일의 좁은 표에서 식별자가 잘게 나뉘면 열 이름과 값을 행별로 배치합니다. 렌더러는 `src/lib/article-scenes.mjs`, 검증은 `validateScene`을 사용하며 파일 조회나 네트워크 접속은 수행하지 않습니다.

`array`의 선택 항목 `after`는 첫 원소를 제거한 뒤의 배열이며 `values`의 두 번째 원소부터 끝까지와 일치해야 합니다. `movement: "shift"`는 남은 원소를 앞 칸으로 옮긴 모습, `movement: "head"`는 다음 원소에서 꺼내는 모습을 나란히 표시합니다. 실제 메모리 배치를 측정하는 기능은 아닙니다. `states`의 각 `edges` 항목은 `[이전 상태 인덱스, 다음 상태 인덱스, 변경 조건]`이며 시작·도착 상태와 조건을 한 경로씩 표시합니다.

## 본문 표식

표식은 표·목록·코드 밖의 독립된 줄에서 컴포넌트로 변환됩니다.

| 표식 | 자료 |
| --- | --- |
| `[[diagram]]` | 해당 글의 설명 도식 |
| `[[photo]]` | 등록된 이미지 |
| `[[download]]` | 글별 실습 ZIP |
| `[[run:1]]` | 첫 실행 기록 |
| `[[run:1:fold]]` | 접힌 첫 실행 기록 |

여러 기록은 `[[run:2]]`처럼 저장 순서를 사용합니다. 누락·중복·순서 오류는 빌드 검사 대상입니다. 70줄을 넘는 코드는 원문 전체를 접어 제공하며, 16줄을 넘는 출력은 전체 펼치기를 제공합니다.

실행 기록이 있는 글은 `[[download]]`를 한 번 사용합니다. 실습 준비 설명과 코드 사이에 놓으면 해당 글의 ZIP 링크와 압축 해제 안내가 표시됩니다. 첫 실행 기록보다 앞에 있어야 하며 코드·표·목록 안에는 넣지 않습니다.

## 실행 데이터

`src/data/executions.json`에는 명령·표준 출력·표준 오류·종료 코드와 실행 날짜·환경·본문 코드 해시가 있습니다. 범위와 해석은 `src/data/execution-context.json`에 있습니다. `reproduction: "article"`은 별도 준비 파일 없이 본문 코드로 재현하는 예제입니다.

기존 재현 스크립트는 가상 계정·그룹·파일과 루프백을 사용합니다. U-01은 별도 설정의 OpenSSH 해석, U-02~U-10은 파일 수집·비교입니다. Qualys 제품을 실행한 결과는 아닙니다.

`public/assets/posts/isolated-learning-lab.png`는 AI 생성 설명 이미지이며 실제 장비나 제품 화면의 증거가 아닙니다.

## 표시 확인

미리보기 서버 실행 후 전체 공개 글의 화면 검사는 다음 명령을 사용합니다.

```bash
BLOG_QA_ALL=1 node scripts/verify-daily-browser.mjs
```

1440·767·390·320px에서 그림 경계·글자 크기·코드·출력·앵커·가로 넘침을 검사합니다. 기존 `figures/글-슬러그/` 주소는 해당 본문의 `#article-diagram`으로 연결됩니다.
