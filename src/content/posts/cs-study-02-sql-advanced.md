---
title: "SQL JOIN과 집계: ON·WHERE, GROUP BY·HAVING, 서브쿼리"
description: "회원 네 명과 주문 다섯 건으로 조인 행 수와 NULL 보충 행을 비교합니다. SQLite 실행 예제와 자체 연습문제 5개로 조건 위치에 따른 결과를 풉니다."
date: "2026-10-22T18:46:15+09:00"
sourcesChecked: "2026-10-22"
category: "cs-study"
tags: ["전산", "NCS", "SQL", "JOIN", "SQLite"]
draft: false
example: false
---

회원은 네 명인데 주문 내역을 붙이자 다섯 행이 나왔다. 조인 결과를 그대로 세면 회원 수가 아니라 회원과 주문이 짝지어진 횟수를 세게 된다. 주문이 없는 회원까지 포함할 때는 NULL로 채운 행도 생긴다.

[앞 글의 SELECT·NULL 기초](../cs-study-01-database-sql/)에서 한 테이블의 행을 골랐다면, 이번에는 두 테이블을 연결한 뒤 행과 그룹을 서로 다른 단계에서 고른다. 예제와 문제는 직접 만든 가상 자료다.

## 1. 회원 네 명과 주문 다섯 건 준비하기

Python 3.12의 `sqlite3` 표준 모듈을 사용한다. 아래 실행 기록은 Python 3.12.1·SQLite 3.43.1에서 남겼다. 별도 DB 서버, 계정, `.db` 파일은 필요하지 않다. ZIP을 풀고 `02-sql-advanced.py`가 있는 폴더에서 `python -I -B -X utf8 02-sql-advanced.py`로 실행한다. Bash에서는 `python3`를 써도 된다.

[[download]]

ZIP의 Python 파일은 테이블 생성과 자료 입력, 조회 결과 비교까지 한 번에 실행한다. 아래 SQL은 그 파일에서 사용한 생성문이다. 처음에는 파일을 그대로 실행하고, 조회를 바꿔 보고 싶을 때 같은 연결에서 SQL을 시험하면 된다.

SQL만 따로 실행하려면 SQLite에 전달할 연결을 먼저 준비한다. Python에서는 `import sqlite3`를 한 뒤, 아래 SQL 전체를 삼중 따옴표 문자열 `BASE`로 저장한다. 이어서 `conn = sqlite3.connect(':memory:')`와 `conn.executescript(BASE)`를 같은 Python 세션에서 실행한다.

조회문도 문자열로 `conn.execute()`에 넘기고 `fetchall()`로 행 목록을 받는다. SQL을 PowerShell에 바로 입력하는 방식과 구별하자. 연결과 초기화를 포함한 전체 코드는 글 뒤에 접어 두었다.

```sql
CREATE TABLE members (
    member_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(member_id),
    amount INTEGER CHECK (amount >= 0),
    status TEXT NOT NULL CHECK (status IN ('paid', 'pending'))
);
INSERT INTO members VALUES
    (1, '가온'), (2, '나래'), (3, '다온'), (4, '라온');
INSERT INTO orders VALUES
    (101, 1, 10000, 'paid'), (102, 1, 20000, 'pending'),
    (103, 2, 5000, 'paid'), (104, 2, 15000, 'paid'),
    (105, 4, NULL, 'paid');
```

`members.member_id`는 회원을 구별하고, `orders.member_id`는 주문한 회원을 가리킨다. 1·2번은 주문이 두 건씩 있고 3번은 주문이 없다. 4번의 주문은 결제 상태지만 금액이 NULL이다. **주문 없음**과 **주문은 있으나 금액이 없음**을 구별하기 위한 자료다.

다음 조회는 모두 이 초기 자료에서 시작한다. `ORDER BY`를 적어 출력 순서를 고정했다. 별도 연결에서 SQL을 실행했다면 그 연결에도 먼저 자료를 만들어야 한다. 실행 후에는 `conn.close()`로 닫는다. Python 연결 사용법은 [sqlite3 공식 문서](https://docs.python.org/3.12/library/sqlite3.html)를 참고할 수 있다.

## 2. 조인 결과의 한 행은 무엇인가

```sql
SELECT m.member_id, o.order_id
        FROM members AS m INNER JOIN orders AS o
          ON o.member_id = m.member_id
        ORDER BY m.member_id, o.order_id
```

```text
member_id | order_id
1 | 101
1 | 102
2 | 103
2 | 104
4 | 105
```

INNER JOIN은 `ON` 조건에 맞는 쌍을 반환한다. 회원 1번에 주문 두 건이 연결됐으므로 회원 번호 1이 두 번 나온다. 회원 기본 키가 중복 저장된 상황과는 다르다. 주문별 행이 필요한 보고서에서 이 중복을 무조건 `DISTINCT`로 지우면 필요한 주문 구분까지 잃는다.

LEFT JOIN은 오른쪽에서 일치하는 행을 찾지 못해도 왼쪽 회원을 남긴다. 이때 주문 쪽 열이 NULL인 보충 행을 만든다. [SQLite SELECT 문서](https://www.sqlite.org/lang_select.html)는 조인 조건과 이 보충 행이 만들어지는 순서를 설명한다.

## 3. NULL 보충 행에서는 무엇을 세는가

```sql
SELECT m.member_id, COUNT(*), COUNT(o.order_id), SUM(o.amount)
        FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id
        GROUP BY m.member_id
        ORDER BY m.member_id
```

| member_id | COUNT(*) | COUNT(o.order_id) | SUM(o.amount) |
| --- | --- | --- | --- |
| 1 | 2 | 2 | 30000 |
| 2 | 2 | 2 | 20000 |
| 3 | 1 | 0 | NULL |
| 4 | 1 | 1 | NULL |

3번은 조인 결과에 보충 행 한 개가 있으므로 `COUNT(*)`가 1이다. 주문 기본 키는 NULL이라 `COUNT(o.order_id)`는 0이다. 반면 4번은 실제 주문 번호 105가 있어 주문 수가 1이다.

두 회원 모두 SUM은 NULL이지만 이유는 다르다. 3번은 주문이 없고, 4번은 주문 금액이 NULL이다. `SUM`은 NULL을 제외한 금액을 더하므로 두 그룹에는 합산할 숫자가 없다. 주문 유무는 합계와 주문 기본 키의 COUNT를 함께 읽어 구별한다. `COUNT(X)`와 `SUM(X)`의 NULL 처리는 [SQLite 집계 함수 문서](https://sqlite.org/lang_aggfunc.html)에 나온다.

화면에 합계를 0으로 표시한다면 주문 수나 금액 누락 여부도 함께 보여 주어야 두 상황이 섞이지 않는다.

## 4. ON과 WHERE에 같은 조건을 놓아 보기

결제 주문만 붙이면서 회원은 모두 남기려면 오른쪽 행을 고르는 조건을 `ON`에 둔다.

```sql
SELECT m.member_id, COUNT(o.order_id)
        FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id AND o.status = 'paid'
        GROUP BY m.member_id
        ORDER BY m.member_id
```

이번에는 회원 번호와 결제 주문 수가 `(1, 1)`, `(2, 2)`, `(3, 0)`, `(4, 1)`로 나왔다. `o.status = 'paid'`를 ON에서 빼고 WHERE로 옮긴 조회는 3번을 반환하지 않았다.

[[diagram]]

아래 조회에서는 조인 뒤에 `WHERE o.status = 'paid'`를 적용한다. 주문이 없는 3번의 보충 행은 `status`도 NULL이다. 이 비교는 참이 되지 않으므로 그 행이 빠진다.

```sql
SELECT m.member_id, COUNT(o.order_id)
        FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id
        WHERE o.status = 'paid'
        GROUP BY m.member_id
        ORDER BY m.member_id
```

이 차이는 미탐지 자산을 포함한 집계에서도 생길 수 있다. 자산과 탐지 결과를 LEFT JOIN한 뒤 오른쪽 상태만 WHERE에서 고르면, 대응하는 결과가 없는 자산을 보고서에서 지울 수 있다. 이 글의 회원 자료로 조인 의미를 설명한 예이며 실제 보안 제품의 보고서 결과는 아니다.

## 5. 행을 고른 다음 그룹을 고르기

```sql
SELECT o.member_id, COUNT(*) AS paid_count, SUM(o.amount) AS total
        FROM orders AS o
        WHERE o.status = 'paid'
        GROUP BY o.member_id
        HAVING SUM(o.amount) >= 15000
        ORDER BY o.member_id
```

조회 결과는 `member_id=2`, `paid_count=2`, `total=20000` 한 행이다. WHERE에서 미결제 주문 102번을 제외하므로 1번의 합계는 10000원이다. 2번은 5000원과 15000원을 합쳐 20000원이고, 4번의 합계는 NULL이다. HAVING 비교에서 1번과 4번이 제외돼 2번만 남는다. 이는 SQL 결과를 설명하는 논리적 순서이며 DBMS가 내부에서 수행할 물리적 실행 순서를 지정한 것은 아니다.

| 구문 | 이 조회에서 하는 일 |
| --- | --- |
| ON | 서로 연결할 회원·주문 쌍을 고름 |
| WHERE | 집계하기 전의 주문 행을 고름 |
| GROUP BY | 같은 회원 번호를 한 그룹으로 모음 |
| HAVING | 집계한 그룹을 남길 조건을 적용 |

SUM이나 COUNT 같은 함수로 집계하지 않은 열을 SELECT에 더 넣을 때는 그 열도 그룹 기준에 포함할지 생각한다. SQLite가 일부 비집계 열을 허용한다는 이유로 다른 DBMS도 같은 행의 값을 고를 것이라고 가정하지 않는다. 이 글의 집계 SELECT는 그룹 기준 열과 집계식으로 구성했다.

## 6. 행을 붙이지 않고 존재 여부만 묻기

결제 주문이 한 건이라도 있는 회원 목록만 필요하면, 주문의 모든 열을 붙이는 대신 EXISTS로 물을 수 있다.

```sql
SELECT m.member_id FROM members AS m
        WHERE EXISTS (
            SELECT 1 FROM orders AS o
            WHERE o.member_id = m.member_id AND o.status = 'paid'
        )
        ORDER BY m.member_id
```

결과는 회원 1·2·4번이다. 내부 조회가 바깥쪽 회원 번호를 참조하므로 상관 서브쿼리다. 2번에게 결제 주문이 두 개 있어도 바깥 회원 행은 한 번만 선택된다. 안쪽의 `SELECT 1`은 행이 있다는 사실을 묻는 표현이며 주문 수를 세는 명령이 아니다. 반환 열의 값보다 행 존재 여부를 사용한다는 정의는 [SQLite EXISTS 문서](https://www.sqlite.org/lang_expr.html#the_exists_operator)에서 볼 수 있다.

## 7. 직접 풀어 보는 연습문제 5개

모두 앞의 초기 자료를 사용한다. 뒤의 전체 코드와 실행 기록에는 문제별 결과도 들어 있으므로, 먼저 풀고 펼쳐 본다.

### 문제 1. 기본 키가 있는데 왜 두 행인가

INNER JOIN 결과에서 회원 2번을 골랐더니 두 행이 나왔다. 회원 기본 키가 손상됐다는 증거인가? 행이 두 개가 된 이유와 회원 목록만 필요할 때 사용할 수 있는 방법을 설명하자.

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 문제 1: 주문 두 건이 각각 연결됐다

회원 2번의 행 한 개에 주문 103·104번이 각각 대응한다. 결과의 단위가 회원과 주문의 쌍이므로 두 행이 된다. `members`에 같은 기본 키가 두 번 저장됐다는 뜻이 아니다. 회원 존재 여부만 필요하다면 EXISTS로 주문 존재를 검사할 수 있다. 회원 열만 고른 뒤 DISTINCT를 쓰는 방식도 가능하지만, 필요한 출력 단위를 먼저 정해야 한다.

</details>

### 문제 2. 미결제 주문만 연결한 COUNT

다음 조회의 네 행을 순서대로 적자. 두 COUNT 값이 달라지는 이유도 설명하자.

```sql
SELECT m.member_id, COUNT(*), COUNT(o.order_id)
        FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id AND o.status = 'pending'
        GROUP BY m.member_id
        ORDER BY m.member_id
```

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 문제 2: 주문이 없는 쪽도 보충 행은 남는다

```text
member_id | COUNT(*) | COUNT(o.order_id)
1 | 1 | 1
2 | 1 | 0
3 | 1 | 0
4 | 1 | 0
```

미결제 주문은 1번의 102번 주문뿐이다. 나머지 회원은 ON에 맞는 주문이 없어 NULL 보충 행을 한 개씩 갖는다. 따라서 COUNT(*)는 1이고 주문 번호를 세는 COUNT(o.order_id)는 0이다. 결제 주문이 있는 2·4번도 이번 조인의 미결제 조건에는 맞지 않는다.

</details>

### 문제 3. 금액 조건을 옮기면 누가 남는가

다음 조회에서 반환하는 회원 번호를 적자. 이어서 `o.amount >= 15000`을 ON에서 빼고 WHERE로 옮겼을 때의 번호를 적자. 정렬 조건은 그대로 둔다.

```sql
SELECT m.member_id FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id AND o.amount >= 15000
        ORDER BY m.member_id, o.order_id
```

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 문제 3: ON은 1·2·3·4, WHERE는 1·2

ON에서는 1번의 20000원 주문과 2번의 15000원 주문이 연결된다. 3·4번은 금액 조건에 맞는 주문이 없어 보충 행으로 남는다. WHERE로 옮기면 그 보충 행의 금액 비교가 참이 되지 않아 제거된다. 결제 상태 조건은 없으므로 미결제인 102번 주문도 금액 비교에 포함된다.

</details>

### 문제 4. WHERE와 HAVING을 차례로 적용하기

반환하는 행과 세 열의 값을 적자.

```sql
SELECT member_id, COUNT(*) AS n, SUM(amount) AS total
        FROM orders
        WHERE status = 'paid'
        GROUP BY member_id
        HAVING COUNT(*) >= 2 AND SUM(amount) >= 20000
        ORDER BY member_id
```

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 문제 4: 회원 2번, 주문 2건, 합계 20000

WHERE를 통과하는 주문은 101·103·104·105번이다. 회원 1번은 한 건이어서 COUNT 조건에 맞지 않는다. 2번은 두 건의 금액 5000과 15000을 더해 20000이 된다. 4번은 주문 수가 한 건이고 합계도 NULL이므로 제외된다. 결과는 `(2, 2, 20000)` 한 행이다.

</details>

### 문제 5. NOT IN에 NULL이 섞이면

첫 조회의 결과를 적고, 주문이 전혀 없는 회원을 찾으려는 목적에 맞게 NOT EXISTS로 바꿔 보자.

```sql
SELECT member_id FROM members
        WHERE member_id NOT IN (
            SELECT member_id FROM orders UNION ALL SELECT NULL
        )
        ORDER BY member_id
```

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 문제 5: 첫 조회는 0행, NOT EXISTS는 3번

1·2·4번은 안쪽 목록에 있으므로 NOT IN 조건이 거짓이다. 3번은 목록에 없지만 NULL과의 비교 때문에 조건이 참으로 결정되지 않는다. WHERE가 이 행도 남기지 않아 전체 결과는 0행이다. 목록에 NULL이 포함돼도 단순히 무시한다고 풀면 틀린다.

```sql
SELECT m.member_id FROM members AS m
        WHERE NOT EXISTS (
            SELECT 1 FROM orders AS o WHERE o.member_id = m.member_id
        )
        ORDER BY m.member_id
```

이 조회는 각 회원과 연결되는 주문 행이 없는지를 직접 묻는다. 회원 3번만 해당한다. 주문 금액이 NULL인 4번도 주문 행 자체는 있으므로 제외된다.

</details>

## 8. 전체 검증 코드와 출력 열어 보기

다음 Python 파일에는 문제의 기대값도 들어 있다. 코드와 실행 기록은 기본 접힘 상태이며, 문제를 푼 뒤 열어 대조한다. 실행 파일은 별도 기록 파일을 만들지 않고 메모리 연결만 사용한다.

```python
import json
import sqlite3

# 사례마다 이 초기 자료를 새 메모리 데이터베이스에 만든다.
BASE = """
CREATE TABLE members (
    member_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(member_id),
    amount INTEGER CHECK (amount >= 0),
    status TEXT NOT NULL CHECK (status IN ('paid', 'pending'))
);
INSERT INTO members VALUES
    (1, '가온'), (2, '나래'), (3, '다온'), (4, '라온');
INSERT INTO orders VALUES
    (101, 1, 10000, 'paid'), (102, 1, 20000, 'pending'),
    (103, 2, 5000, 'paid'), (104, 2, 15000, 'paid'),
    (105, 4, NULL, 'paid');
"""

CASES = (
    ("inner", """
        SELECT m.member_id, o.order_id
        FROM members AS m INNER JOIN orders AS o
          ON o.member_id = m.member_id
        ORDER BY m.member_id, o.order_id
    """, [(1, 101), (1, 102), (2, 103), (2, 104), (4, 105)]),
    ("left-count", """
        SELECT m.member_id, COUNT(*), COUNT(o.order_id), SUM(o.amount)
        FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id
        GROUP BY m.member_id
        ORDER BY m.member_id
    """, [(1, 2, 2, 30000), (2, 2, 2, 20000),
           (3, 1, 0, None), (4, 1, 1, None)]),
    ("on-paid", """
        SELECT m.member_id, COUNT(o.order_id)
        FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id AND o.status = 'paid'
        GROUP BY m.member_id
        ORDER BY m.member_id
    """, [(1, 1), (2, 2), (3, 0), (4, 1)]),
    ("where-paid", """
        SELECT m.member_id, COUNT(o.order_id)
        FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id
        WHERE o.status = 'paid'
        GROUP BY m.member_id
        ORDER BY m.member_id
    """, [(1, 1), (2, 2), (4, 1)]),
    ("having", """
        SELECT o.member_id, COUNT(*) AS paid_count, SUM(o.amount) AS total
        FROM orders AS o
        WHERE o.status = 'paid'
        GROUP BY o.member_id
        HAVING SUM(o.amount) >= 15000
        ORDER BY o.member_id
    """, [(2, 2, 20000)]),
    ("exists-paid", """
        SELECT m.member_id FROM members AS m
        WHERE EXISTS (
            SELECT 1 FROM orders AS o
            WHERE o.member_id = m.member_id AND o.status = 'paid'
        )
        ORDER BY m.member_id
    """, [(1,), (2,), (4,)]),
    ("q1-cardinality", """
        SELECT COUNT(*) FROM members AS m JOIN orders AS o
          ON m.member_id = o.member_id
        WHERE m.member_id = 2
    """, [(2,)]),
    ("q2-pending", """
        SELECT m.member_id, COUNT(*), COUNT(o.order_id)
        FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id AND o.status = 'pending'
        GROUP BY m.member_id
        ORDER BY m.member_id
    """, [(1, 1, 1), (2, 1, 0), (3, 1, 0), (4, 1, 0)]),
    ("q3-on", """
        SELECT m.member_id FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id AND o.amount >= 15000
        ORDER BY m.member_id, o.order_id
    """, [(1,), (2,), (3,), (4,)]),
    ("q3-where", """
        SELECT m.member_id FROM members AS m LEFT JOIN orders AS o
          ON o.member_id = m.member_id
        WHERE o.amount >= 15000
        ORDER BY m.member_id, o.order_id
    """, [(1,), (2,)]),
    ("q4-having", """
        SELECT member_id, COUNT(*) AS n, SUM(amount) AS total
        FROM orders
        WHERE status = 'paid'
        GROUP BY member_id
        HAVING COUNT(*) >= 2 AND SUM(amount) >= 20000
        ORDER BY member_id
    """, [(2, 2, 20000)]),
    ("q5-not-in", """
        SELECT member_id FROM members
        WHERE member_id NOT IN (
            SELECT member_id FROM orders UNION ALL SELECT NULL
        )
        ORDER BY member_id
    """, []),
    ("q5-not-exists", """
        SELECT m.member_id FROM members AS m
        WHERE NOT EXISTS (
            SELECT 1 FROM orders AS o WHERE o.member_id = m.member_id
        )
        ORDER BY m.member_id
    """, [(3,)]),
)


def main():
    results = []
    for label, sql, expected in CASES:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(BASE)
            rows = conn.execute(sql).fetchall()
            if rows != expected:
                raise AssertionError(f"{label}: {rows!r} != {expected!r}")
            results.append((label, rows))
        finally:
            conn.close()
    print(f"SQL 사례 {len(results)}건 통과; SQLite {sqlite3.sqlite_version}")
    for label, rows in results:
        print(f"{label}: {json.dumps(rows, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
```

`BASE`에는 테이블과 초기 행이 들어 있고, `CASES`의 각 항목에는 사례 이름·SQL·기대 행 목록이 들어 있다. `main()`은 매번 새 메모리 연결을 만들고 외래 키 검사를 켠 다음 `executescript(BASE)`로 자료를 넣는다. 앞선 조회나 자료 변경을 이어받지 않으므로 각 사례를 같은 출발점에서 비교한다.

`rows`는 `fetchall()`로 받은 실제 행 목록이다. 열의 값뿐 아니라 열의 위치와 행 순서까지 `expected`와 같아야 `results`에 추가된다. 다르면 사례 이름과 두 목록을 담은 `AssertionError`로 멈춘다. 이때도 `finally`에서 연결을 닫는다. 입력 SQL에 오류가 생기면 빈 목록으로 숨기지 않고 예외가 그대로 드러난다.

결과는 Python의 튜플 목록으로 비교하고, 출력할 때는 JSON으로 바꾼다. 따라서 화면의 `null`은 SQL NULL이며, `[]`는 결과 행이 없다는 뜻이다. 한 행에 숫자 0이 있는 `[[0]]`과 구별한다.

[[run:1:fold]]

첫 줄의 사례 수는 본문 조회와 문제 검증을 합친 수이며 연습문제 개수는 5개다. `q`로 시작하는 줄은 위 해설과 대응한다. 기대값 비교가 모두 통과한 뒤 출력하며, 종료 코드 0과 빈 표준 오류를 함께 기록했다. Bash에서는 명령 직후 `echo $?`, PowerShell에서는 `$LASTEXITCODE`로 프로세스 결과를 볼 수 있다.

## 9. 시험 직전 복습

- 조인의 한 행이 회원 한 명인지, 회원과 주문 한 쌍인지부터 정한다.
- LEFT JOIN의 NULL 보충 행에서 COUNT(*)와 오른쪽 기본 키의 COUNT는 다를 수 있다.
- ON은 연결할 쌍을, WHERE는 조인 뒤의 행을 고른다.
- WHERE는 집계 전 행, HAVING은 집계한 그룹에 적용한다.
- EXISTS는 행 존재 여부를 묻는다. NOT IN의 NULL과 같은 방식으로 해석하지 않는다.
