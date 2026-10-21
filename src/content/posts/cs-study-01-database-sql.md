---
title: "데이터베이스·SQL 기초: SELECT, NULL, 데이터 변경"
description: "가상 도서 목록으로 SELECT·NULL·데이터 변경을 실행하고, 직접 만든 다섯 문제의 정답과 SQLite 결과를 비교합니다."
date: "2026-10-21T18:52:52+09:00"
sourcesChecked: "2026-10-21"
category: "cs-study"
tags: ["전산", "NCS", "SQL", "데이터베이스", "SQLite"]
draft: false
example: false
---

도서 목록에서 “재고가 있고 2만 원 이상인 책 중 비싼 두 권”을 고른다고 해 보자. SQL로 옮기려면 세 가지를 정해야 한다. 어떤 테이블을 읽을지, 어떤 행을 남길지, 남은 행을 어떤 순서로 보여 줄지다.

예제와 연습문제는 직접 만든 가상 도서 목록을 사용한다.

## 1. 조건과 결과를 구분해야 하는 이유

SQL 출력 문제는 문법을 알고도 틀릴 수 있다. 재고 조건을 빠뜨리면 품절 도서가 포함되고, 정렬하기 전에 두 행을 고른다고 생각하면 엉뚱한 결과를 예상하게 된다. 먼저 조건에 맞는 행을 골라 낸 다음, 표시할 열과 정렬 기준을 따로 살펴보자.

설정 값을 조회하거나 로그를 집계할 때도 같은 구분이 필요하다. 특히 수정·삭제 문장에서는 “어떤 행이 대상인가”를 먼저 읽어야 변경 범위를 이해할 수 있다.

## 2. 데이터베이스, DBMS, 테이블은 무엇이 다른가

| 용어 | 뜻과 예 |
| --- | --- |
| 데이터베이스(DB) | 일정한 구조로 저장해 조회·관리하는 데이터의 모음. 이 글에서는 도서 목록을 담는 공간이다. |
| DBMS | 데이터베이스를 생성하고 조회·변경하는 소프트웨어. SQLite, PostgreSQL, MySQL 등이 있다. |
| SQL | 관계형 데이터베이스의 구조와 데이터를 다루는 언어. 제품 자체의 이름이 아니다. |
| 테이블 | 행과 열로 구성된 데이터 구조. books는 도서 목록 테이블의 이름이다. |
| 행(row) | 도서 한 권에 해당하는 레코드. 도서 번호·제목·가격 등이 함께 들어 있다. |
| 열(column) | title, price처럼 행마다 값을 담는 항목. 각 열에는 자료형과 제약 조건을 지정할 수 있다. |

관계형 모델의 기본 키는 한 행을 식별하는 값이며 중복과 NULL을 허용하지 않는다. 이 예제에서는 제목 대신 `book_id`를 기본 키로 쓴다. 같은 제목의 책이 여러 권 있어도 번호로 구분할 수 있다. 기본 키는 여러 열을 조합해 지정할 수도 있다.

아래 SQLite 예제의 `INTEGER PRIMARY KEY`는 저장된 번호의 유일성을 보장한다. 다만 새 행을 넣을 때 이 번호를 생략하거나 NULL을 주면 SQLite가 정수를 배정한다. “NULL 입력은 무조건 오류”라고 일반화하지 말고, 기본 키의 개념과 제품별 입력 동작을 구분하자.

## 3. SELECT 문을 읽는 순서

다음은 이 글에서 사용할 조회 형태다. 대괄호는 생략 가능한 절을 나타내는 설명 기호이므로 실제 SQL에 입력하지 않는다.

```text
SELECT [DISTINCT] 표시할_열
FROM 테이블
[WHERE 행을_남길_조건]
[ORDER BY 정렬할_열 ASC 또는 DESC]
[LIMIT 최대_행_수];
```

1. `FROM`: 어느 테이블의 데이터를 읽는지 정한다.
2. `WHERE`: 조건이 참인 행만 남긴다. 거짓이나 UNKNOWN인 행은 통과하지 않는다.
3. `SELECT`: 결과에 표시할 열이나 계산식을 정한다.
4. `DISTINCT`: 선택된 결과 행이 같으면 중복을 제거한다. 원본 테이블을 바꾸지 않는다.
5. `ORDER BY`: 결과를 정렬한다. `ASC`는 오름차순, `DESC`는 내림차순이다.
6. `LIMIT`: 정렬된 결과에서 반환할 행 수를 제한한다. 여기서는 SQLite 문법을 사용한다.

위 순서는 이 형태의 조회 결과를 이해하는 논리적 순서다. DBMS가 내부에서 실제로 데이터를 읽고 계산하는 물리적 실행 순서와 같다는 뜻은 아니다. 다른 DBMS에서는 행 수 제한에 `FETCH FIRST`나 `TOP` 등을 쓰기도 한다.

`ORDER BY`가 없으면 결과 행의 순서는 보장되지 않는다. 정렬 값이 같은 행끼리도 순서를 정하려면 두 번째 기준이 필요하다. 이 글은 `book_id`를 추가해 결과를 재현할 수 있게 했다.

## 4. 가상 도서 목록으로 SQL 실행하기

예제는 외부 연결 없이 메모리 데이터베이스에서 실행했다. 실행 환경은 Python 3.12.1의 sqlite3 모듈, SQLite 3.43.1이며 실행일은 2026-10-20이다. 아래 예제와 뒤의 문제는 각각 처음의 도서 5건에서 독립적으로 시작한다.

### 4-1. 테이블을 만들고 다섯 행 넣기

```sql
-- 가상의 도서 목록을 만든다. 가격 단위는 원이다.
CREATE TABLE books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT,
    price INTEGER NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)
);

INSERT INTO books (book_id, title, category, price, stock)
VALUES
    (1, 'SQL 첫걸음', 'DB', 20000, 3),
    (2, '네트워크 입문', 'Network', 25000, 0),
    (3, '파이썬 기초', 'Programming', 18000, 5),
    (4, '운영체제 노트', NULL, 22000, 2),
    (5, '보안 기초', 'Security', 25000, 1);
```

`TEXT`는 문자열, `INTEGER`는 정수에 사용했다. SQLite의 일반 테이블은 유연한 자료형 규칙을 적용하므로 INTEGER 선언 하나가 모든 잘못된 문자열 입력을 거부한다고 생각하면 안 된다. 아래 `NOT NULL`은 NULL을, `CHECK (price >= 0)`는 음수 가격을 제한하는 별도 조건이다.

`DEFAULT 0`은 INSERT에서 재고 열을 생략했을 때 쓸 값이다. NULL을 명시적으로 입력하는 것과는 다르다. 문자열은 작은따옴표로 감싸고, 값이 없음을 나타내는 NULL에는 따옴표를 붙이지 않는다.

생성 직후의 `books`는 다음과 같다. NULL 표시는 미입력 상태를 나타내며 실제로 “NULL”이라는 네 글자를 저장한 것이 아니다.

| book_id | title | category | price | stock |
| --- | --- | --- | --- | --- |
| 1 | SQL 첫걸음 | DB | 20000 | 3 |
| 2 | 네트워크 입문 | Network | 25000 | 0 |
| 3 | 파이썬 기초 | Programming | 18000 | 5 |
| 4 | 운영체제 노트 | NULL | 22000 | 2 |
| 5 | 보안 기초 | Security | 25000 | 1 |

가격 단위는 원, 재고 단위는 권이다. 표나 코드가 화면보다 넓으면 해당 영역을 좌우로 움직여 전체를 읽을 수 있다.

### 4-2. 조건을 적용한 뒤 정렬하고 두 행 고르기

```sql
SELECT book_id, title, price
FROM books
WHERE stock > 0 AND price >= 20000
ORDER BY price DESC, book_id ASC
LIMIT 2;
```

```text
book_id | title | price
5 | 보안 기초 | 25000
4 | 운영체제 노트 | 22000
(2행)
```

재고가 0인 2번과 가격이 2만 원 미만인 3번은 제외된다. 남은 도서를 가격 내림차순으로 정렬하면 5번, 4번, 1번이다. `LIMIT 2`가 마지막 한 행을 제외하므로 위의 두 도서가 반환된다.

[[diagram]]

그림은 위 조회의 논리적 결과를 줄여 표시한 것이다. 실제 데이터를 읽는 경로나 처리 계획을 나타내지는 않는다.

| 조건식 | 뜻 | 도서 번호 |
| --- | --- | --- |
| price BETWEEN 20000 AND 25000 | 2만 원 이상, 2만5천 원 이하. 양 끝 포함 | 1, 2, 4, 5 |
| category IN ('DB', 'Security') | 나열한 두 분류 중 하나와 같은 값 | 1, 5 |
| title LIKE 'SQL%' | 제목이 SQL로 시작. %는 0개 이상의 문자 | 1 |

위 조건은 각각 따로 적용한 결과다. `AND`와 `OR`를 섞을 때에는 AND가 먼저 결합한다. 의도한 묶음을 괄호로 표시하면 해석이 분명해진다.

```sql
SELECT book_id
FROM books
WHERE category = 'DB'
   OR category = 'Security' AND stock = 0
ORDER BY book_id;
```

```text
book_id
1
(1행)
```

이 조건은 “DB 분류이거나, Security 분류이면서 재고가 0”이라는 뜻이다. 1번은 DB 분류이므로 재고가 있어도 포함된다. 두 분류 전체에 재고 0 조건을 적용하려면 다음과 같이 바꾼다.

```sql
SELECT book_id
FROM books
WHERE (category = 'DB' OR category = 'Security')
  AND stock = 0
ORDER BY book_id;
```

```text
book_id
(0행)
```

두 분류 모두 재고가 있으므로 두 번째 조회에서는 반환되는 행이 없다.

### 4-3. 행 추가, 값 수정, 행 삭제

```sql
-- 재고를 생략하면 DEFAULT 값인 0이 들어간다.
INSERT INTO books (book_id, title, category, price)
VALUES (6, 'SQL 연습 노트', 'DB', 15000);

-- 새로 넣은 도서의 재고만 바꾼다.
UPDATE books SET stock = 2 WHERE book_id = 6;

-- 2번 도서 한 행만 지운다.
DELETE FROM books WHERE book_id = 2;

SELECT book_id, title, stock FROM books ORDER BY book_id;
```

```text
book_id | title | stock
1 | SQL 첫걸음 | 3
3 | 파이썬 기초 | 5
4 | 운영체제 노트 | 2
5 | 보안 기초 | 1
6 | SQL 연습 노트 | 2
(5행)
```

INSERT는 6번 도서를 추가하고, UPDATE는 그 도서의 재고를 2로 바꾼다. DELETE는 2번 도서만 지운다. 이 세 문장이 테이블의 구조를 바꾸는 것은 아니다.

WHERE 없는 UPDATE와 DELETE는 테이블의 모든 행을 대상으로 한다. 수정할 때에는 같은 조건의 SELECT로 대상 행을 먼저 살펴볼 수 있다. 여러 사용자가 동시에 바꾸는 환경에서는 그 조회만으로 이후의 변경 범위가 고정되지는 않으므로 트랜잭션 등도 함께 고려해야 한다.

입력값을 SQL 문자열에 이어 붙이는 방식도 피해야 한다. Python sqlite3에서는 다음처럼 매개변수로 값을 전달한다. conn은 위 도서 목록을 만든 연결이라고 가정한다.

```python
# 도서 번호를 SQL 문장과 분리해서 전달한다.
rows = conn.execute(
    "SELECT title FROM books WHERE book_id = ?;",
    (1,)
).fetchall()
print(rows)
```

```text
[('SQL 첫걸음',)]
```

`?`는 값을 넣을 자리다. 이 방식은 입력값이 SQL 조건식으로 합쳐지는 것을 막는다. 조회 권한이나 반환할 데이터 범위를 정하는 일은 별도로 필요하다.

## 5. 결과를 예상할 때 혼동하기 쉬운 개념

| 비교 | 구분할 점 |
| --- | --- |
| WHERE / SELECT | WHERE는 행을 고르는 조건, SELECT 목록은 결과에 표시할 열·식을 정한다. |
| NULL / 0 / 빈 문자열 | NULL은 값이 없거나 알려지지 않은 상태다. 숫자 0이나 빈 문자열과 같은 개념이 아니다. DBMS별 빈 문자열 처리 차이는 따로 확인해야 한다. |
| = NULL / IS NULL | = NULL은 참이 되지 않아 WHERE에서 행을 선택하지 못한다. NULL 여부는 IS NULL 또는 IS NOT NULL로 검사한다. |
| COUNT(*) / COUNT(category) | COUNT(*)는 모든 행, COUNT(category)는 category가 NULL이 아닌 행을 센다. 중복 값도 각각 센다. |
| DISTINCT / ORDER BY | DISTINCT는 선택 결과의 중복 제거, ORDER BY는 정렬이다. 중복 제거가 정렬을 보장하지 않는다. |
| DELETE / DROP TABLE | DELETE는 행을 지우고 테이블 구조는 남긴다. DROP TABLE은 테이블 자체를 제거한다. |

예를 들어 처음 데이터에서 가격만 선택하면 25000이 두 번 나온다. `SELECT DISTINCT price FROM books ORDER BY price;`를 실행하면 다음 네 값만 남는다.

```text
price
18000
20000
22000
25000
(4행)
```

중복 제거의 기준은 선택한 열 전체다. `book_id, price`를 함께 선택하면 번호가 모두 다르므로 같은 가격의 두 행도 서로 다른 결과로 남는다.

## 6. 직접 풀어 보는 연습문제 5개

모두 자체 제작한 연습문제다. 각 문제는 처음의 books 다섯 행에서 시작하며 앞 문제의 수정·삭제 결과를 이어받지 않는다. 먼저 답을 적고 다음 절의 해설과 대조해 보자.

### 문제 1. 기본 개념

다음 설명 중 옳은 것은?

1. SQL은 데이터베이스를 관리하는 소프트웨어 제품의 이름이다.
2. 테이블의 한 열은 도서 한 권의 모든 정보를 뜻한다.
3. 기본 키는 한 행을 식별하며, 여러 열을 조합해 지정할 수도 있다.
4. SELECT 결과의 행은 ORDER BY가 없어도 기본 키 오름차순으로 보장된다.

### 문제 2. 조건과 정렬

다음 SQL의 결과를 출력되는 순서대로 적어 보자.

```sql
SELECT title, price
FROM books
WHERE stock > 0 AND price <= 22000
ORDER BY price ASC, book_id ASC;
```

### 문제 3. NULL 비교

아래 두 조회가 각각 반환하는 book_id는 무엇인가? 행이 없으면 “0행”이라고 답한다.

```sql
SELECT book_id FROM books WHERE category = NULL ORDER BY book_id;
```

```sql
SELECT book_id FROM books WHERE category IS NULL ORDER BY book_id;
```

### 문제 4. 수정 뒤 삭제

두 변경 문장을 차례로 실행한 뒤 마지막 SELECT의 결과를 적어 보자.

```sql
UPDATE books SET stock = stock - 1 WHERE book_id = 1;
DELETE FROM books WHERE stock = 0;

SELECT book_id, stock FROM books ORDER BY book_id;
```

### 문제 5. 행 수와 값의 수

다음 결과의 row_count와 category_count를 각각 구하고, 두 값이 달라지는 이유를 설명해 보자.

```sql
SELECT COUNT(*) AS row_count, COUNT(category) AS category_count FROM books;
```

## 7. 정답과 상세 해설

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 문제 1: ③

기본 키는 행을 식별하며 하나의 열 또는 여러 열의 조합으로 지정할 수 있다. ①의 DBMS는 관리 소프트웨어이고 SQL은 언어다. ②에서 도서 한 권 전체에 해당하는 것은 행이다. ④처럼 정렬 조건이 없는 결과를 기본 키 순서라고 단정할 수는 없다.

</details>

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 문제 2: 파이썬 기초, SQL 첫걸음, 운영체제 노트

```text
title | price
파이썬 기초 | 18000
SQL 첫걸음 | 20000
운영체제 노트 | 22000
(3행)
```

2번 도서는 재고가 0이고, 5번 도서는 가격이 22000을 넘는다. 남은 1·3·4번을 가격 오름차순으로 정렬하면 3·1·4번이다. 경계값 22000은 `<=`에 포함된다.

</details>

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 문제 3: 첫 조회는 0행, 두 번째는 4

```text
book_id
(0행)
```

```text
book_id
4
(1행)
```

NULL과 일반 비교 연산을 하면 결과는 UNKNOWN이 된다. NULL인 행도 `category = NULL` 조건을 참으로 만들지 못한다. WHERE는 참인 행만 남기므로 첫 조회는 0행이고, `IS NULL`을 쓴 두 번째 조회는 4번을 반환한다.

</details>

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 문제 4: 1번의 재고는 2, 2번 도서는 삭제

```text
book_id | stock
1 | 2
3 | 5
4 | 2
5 | 1
(4행)
```

UPDATE가 바꾸는 행은 book_id가 1인 도서 한 건이다. 재고는 3에서 2로 줄어든다. 이어서 DELETE가 재고 0인 행을 지우므로 처음부터 재고가 없던 2번 도서만 제거된다. 나머지 도서의 재고는 유지된다.

</details>

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 문제 5: row_count는 5, category_count는 4

```text
row_count | category_count
5 | 4
(1행)
```

전체 행은 다섯 개지만 4번 도서의 category가 NULL이다. `COUNT(*)`는 그 행까지 세고 `COUNT(category)`는 제외한다. 이 문제에서는 중복 제거를 지시하지 않았으므로 분류 값이 같더라도 NULL이 아니면 각각 한 번씩 센다.

</details>

## 전체 예제를 한 파일로 실행하기

조회 결과와 다섯 문제의 SQL 정답은 같은 초기 도서 목록에서 각각 실행했다. 아래 파일은 SQLite 메모리 데이터베이스를 만들고 조회 22건과 제약 조건 오류 세 건을 비교한다. 시스템의 실제 데이터베이스에는 연결하지 않는다.

[전체 Python 예제 다운로드](/security-blog/downloads/01-database-sql.py) 후 `python -I -B -X utf8 01-database-sql.py`로 실행할 수 있다. `--record`는 새 JSON 기록 파일을 만드는 선택 사항이며 기존 파일이 있으면 덮어쓰지 않는다.

```python
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json
import platform
import sqlite3
import sys

BASE = "-- 가상의 도서 목록을 만든다. 가격 단위는 원이다.\nCREATE TABLE books (\n    book_id INTEGER PRIMARY KEY,\n    title TEXT NOT NULL,\n    category TEXT,\n    price INTEGER NOT NULL CHECK (price >= 0),\n    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)\n);\n\nINSERT INTO books (book_id, title, category, price, stock)\nVALUES\n    (1, 'SQL 첫걸음', 'DB', 20000, 3),\n    (2, '네트워크 입문', 'Network', 25000, 0),\n    (3, '파이썬 기초', 'Programming', 18000, 5),\n    (4, '운영체제 노트', NULL, 22000, 2),\n    (5, '보안 기초', 'Security', 25000, 1);\n"
CASES = [{'id': 'base',
  'sql': 'SELECT * FROM books ORDER BY book_id;',
  'expected': [[1, 'SQL 첫걸음', 'DB', 20000, 3],
               [2, '네트워크 입문', 'Network', 25000, 0],
               [3, '파이썬 기초', 'Programming', 18000, 5],
               [4, '운영체제 노트', None, 22000, 2],
               [5, '보안 기초', 'Security', 25000, 1]]},
 {'id': 'filter',
  'sql': 'SELECT book_id, title, price\n'
         'FROM books\n'
         'WHERE stock > 0 AND price >= 20000\n'
         'ORDER BY price DESC, book_id ASC\n'
         'LIMIT 2;',
  'expected': [[5, '보안 기초', 25000], [4, '운영체제 노트', 22000]]},
 {'id': 'between',
  'sql': 'SELECT book_id FROM books WHERE price BETWEEN 20000 AND 25000 ORDER BY book_id;',
  'expected': [[1], [2], [4], [5]]},
 {'id': 'in',
  'sql': "SELECT book_id FROM books WHERE category IN ('DB', 'Security') ORDER BY book_id;",
  'expected': [[1], [5]]},
 {'id': 'like',
  'sql': "SELECT book_id FROM books WHERE title LIKE 'SQL%' ORDER BY book_id;",
  'expected': [[1]]},
 {'id': 'precedence',
  'sql': 'SELECT book_id\n'
         'FROM books\n'
         "WHERE category = 'DB'\n"
         "   OR category = 'Security' AND stock = 0\n"
         'ORDER BY book_id;',
  'expected': [[1]]},
 {'id': 'parentheses',
  'sql': 'SELECT book_id\n'
         'FROM books\n'
         "WHERE (category = 'DB' OR category = 'Security')\n"
         '  AND stock = 0\n'
         'ORDER BY book_id;',
  'expected': []},
 {'id': 'distinct',
  'sql': 'SELECT DISTINCT price FROM books ORDER BY price;',
  'expected': [[18000], [20000], [22000], [25000]]},
 {'id': 'distinct-identity',
  'sql': 'SELECT DISTINCT book_id, price FROM books ORDER BY book_id;',
  'expected': [[1, 20000], [2, 25000], [3, 18000], [4, 22000], [5, 25000]]},
 {'id': 'auto-key',
  'before': "INSERT INTO books (book_id, title, price) VALUES (NULL, '번호 배정 예제', 10000);",
  'sql': "SELECT book_id FROM books WHERE title = '번호 배정 예제';",
  'expected': [[6]]},
 {'id': 'changes',
  'before': '-- 재고를 생략하면 DEFAULT 값인 0이 들어간다.\n'
            'INSERT INTO books (book_id, title, category, price)\n'
            "VALUES (6, 'SQL 연습 노트', 'DB', 15000);\n"
            '\n'
            '-- 새로 넣은 도서의 재고만 바꾼다.\n'
            'UPDATE books SET stock = 2 WHERE book_id = 6;\n'
            '\n'
            '-- 2번 도서 한 행만 지운다.\n'
            'DELETE FROM books WHERE book_id = 2;',
  'sql': 'SELECT book_id, title, stock FROM books ORDER BY book_id;',
  'expected': [[1, 'SQL 첫걸음', 3],
               [3, '파이썬 기초', 5],
               [4, '운영체제 노트', 2],
               [5, '보안 기초', 1],
               [6, 'SQL 연습 노트', 2]]},
 {'id': 'default',
  'before': "INSERT INTO books (book_id, title, price) VALUES (6, '기본값 예제', 10000);",
  'sql': 'SELECT category, stock FROM books WHERE book_id = 6;',
  'expected': [[None, 0]]},
 {'id': 'binding',
  'sql': 'SELECT title FROM books WHERE book_id = ?;',
  'parameters': [1],
  'expected': [['SQL 첫걸음']]},
 {'id': 'binding-input',
  'sql': 'SELECT title FROM books WHERE book_id = ?;',
  'parameters': ['1 OR 1=1'],
  'expected': []},
 {'id': 'q2',
  'sql': 'SELECT title, price\n'
         'FROM books\n'
         'WHERE stock > 0 AND price <= 22000\n'
         'ORDER BY price ASC, book_id ASC;',
  'expected': [['파이썬 기초', 18000], ['SQL 첫걸음', 20000], ['운영체제 노트', 22000]]},
 {'id': 'q3-equal',
  'sql': 'SELECT book_id FROM books WHERE category = NULL ORDER BY book_id;',
  'expected': []},
 {'id': 'q3-is',
  'sql': 'SELECT book_id FROM books WHERE category IS NULL ORDER BY book_id;',
  'expected': [[4]]},
 {'id': 'q4',
  'before': 'UPDATE books SET stock = stock - 1 WHERE book_id = 1;\n'
            'DELETE FROM books WHERE stock = 0;',
  'sql': 'SELECT book_id, stock FROM books ORDER BY book_id;',
  'expected': [[1, 2], [3, 5], [4, 2], [5, 1]]},
 {'id': 'q5',
  'sql': 'SELECT COUNT(*) AS row_count, COUNT(category) AS category_count FROM books;',
  'expected': [[5, 4]]},
 {'id': 'all-update',
  'before': 'UPDATE books SET stock = 9;',
  'sql': 'SELECT COUNT(*) AS changed_rows FROM books WHERE stock = 9;',
  'expected': [[5]]},
 {'id': 'all-delete',
  'before': 'DELETE FROM books;',
  'sql': 'SELECT COUNT(*) AS remaining_rows FROM books;',
  'expected': [[0]]},
 {'id': 'drop',
  'before': 'DROP TABLE books;',
  'sql': "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = 'books';",
  'expected': []}]


def run():
    results = []
    for case in CASES:
        # 예제마다 같은 초기 데이터를 만들어 독립적으로 실행한다.
        conn = sqlite3.connect(':memory:')
        try:
            conn.executescript(BASE)
            if case.get('before'):
                conn.executescript(case['before'])
            cursor = conn.execute(case['sql'], case.get('parameters', []))
            rows = [list(row) for row in cursor.fetchall()]
            if rows != case['expected']:
                raise AssertionError(f"{case['id']}: {rows!r}")
            results.append(dict(id=case['id'], sql=case['sql'],
                                before=case.get('before', ''),
                                parameters=case.get('parameters', []),
                                columns=[col[0] for col in cursor.description], rows=rows))
        finally:
            conn.close()

    # 제약 조건을 어긴 입력은 별도의 메모리 데이터베이스에서 시험한다.
    invalid = [
        ('duplicate-primary-key', "INSERT INTO books VALUES (1, '중복 도서', 'DB', 100, 1);"),
        ('null-title', "INSERT INTO books VALUES (6, NULL, 'DB', 100, 1);"),
        ('negative-price', "INSERT INTO books VALUES (6, '음수 가격', 'DB', -1, 1);")
    ]
    constraints = []
    for name, sql in invalid:
        conn = sqlite3.connect(':memory:')
        try:
            conn.executescript(BASE)
            try:
                conn.execute(sql)
            except sqlite3.IntegrityError as error:
                constraints.append(dict(id=name, sql=sql, exception=type(error).__name__, message=str(error)))
            else:
                raise AssertionError(f'{name}: 거부되어야 하는 입력이 저장됨')
            assert conn.execute('SELECT COUNT(*) FROM books').fetchone() == (5,)
        finally:
            conn.close()

    # 본문에 실은 Python 매개변수 예제도 그대로 실행한다.
    conn = sqlite3.connect(':memory:')
    conn.executescript(BASE)
    rows = conn.execute(
        "SELECT title FROM books WHERE book_id = ?;",
        (1,)
    ).fetchall()
    assert rows == [('SQL 첫걸음',)]
    conn.close()
    proof = dict(recordedAt=datetime.now().astimezone().isoformat(timespec='seconds'),
                 environment=dict(python=platform.python_version(), sqlite=sqlite3.sqlite_version,
                                  system=platform.system(), release=platform.release()),
                 command='python -X utf8 01-database-sql.py --record', exitCode=0,
                 scope='가상 도서 5건을 메모리 데이터베이스에 생성. 실제 데이터와 외부 연결을 사용하지 않음.',
                 sourceCodeSha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                 cases=results, constraints=constraints, pythonBindingOutput=repr(rows))
    print(f"SQL 결과 {len(results)}건 및 제약 조건 {len(constraints)}건 통과")
    print(f"Python {platform.python_version()} / SQLite {sqlite3.sqlite_version}")
    for item in results:
        print(f"{item['id']}: {item['rows']!r}")
    if '--record' in sys.argv:
        # 기존 실행 기록을 덮어쓰지 않는다.
        target = Path(__file__).with_suffix('.verification.json')
        with target.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(proof, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
    return proof


if __name__ == '__main__':
    run()
```

각 SQL은 독립된 초기 자료에서 실행한다. 출력의 `q2`부터 `q5`까지를 위 해설과 비교할 수 있고, `q3-equal`의 빈 목록과 `q3-is`의 4번 행이 NULL 비교 차이를 보여 준다.

[[run:1:fold]]

실행 기록은 2026-10-20에 남긴 결과를 보존했다. SQL 방언과 버전이 바뀌면 자료형·NULL·행 수 제한의 동작도 해당 DBMS에서 다시 시험해야 한다.

## 8. 시험 직전에 기억할 내용

- **DB는 데이터의 모음, DBMS는 관리 소프트웨어, SQL은 언어다.** 행은 레코드, 열은 항목이다.
- 기본 키는 행을 식별한다. 여러 열을 조합할 수 있고, 제목처럼 중복될 수 있는 값과 구분한다.
- 기본 조회는 **FROM → WHERE → SELECT → DISTINCT → ORDER BY → LIMIT** 순으로 결과를 생각한다. 실제 물리적 실행 순서를 외우는 표가 아니다.
- AND와 OR를 섞으면 AND가 먼저 결합한다. 필요한 묶음을 괄호로 적는다. BETWEEN은 양 끝을 포함한다.
- NULL 여부는 **IS NULL / IS NOT NULL**로 검사한다. `= NULL`을 쓰지 않는다.
- **COUNT(*)는 행 수, COUNT(열)은 NULL이 아닌 값의 수**다. DISTINCT를 쓰지 않으면 중복도 센다.
- ORDER BY가 없으면 행 순서가 보장되지 않는다. 같은 정렬 값 사이의 순서도 필요하면 추가 기준을 둔다.
- WHERE 없는 UPDATE·DELETE는 모든 행이 대상이다. DELETE는 행 삭제, DROP TABLE은 테이블 제거다.

## 참고 자료

- [SQLite SELECT: 조회·정렬·행 수 제한](https://www.sqlite.org/lang_select.html)
- [SQLite CREATE TABLE: 기본 키와 제약 조건](https://www.sqlite.org/lang_createtable.html)
- [SQLite Expressions: 연산자·NULL·매개변수](https://www.sqlite.org/lang_expr.html)
- [SQLite Aggregate Functions: COUNT](https://www.sqlite.org/lang_aggfunc.html)
- [SQLite Datatypes: 자료형 친화도와 변환](https://www.sqlite.org/datatype3.html)
- [Python 3.12 sqlite3: 매개변수 바인딩](https://docs.python.org/3.12/library/sqlite3.html)
