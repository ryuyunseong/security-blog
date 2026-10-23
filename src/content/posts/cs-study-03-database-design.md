---
title: "정규화·트랜잭션·인덱스: 중복 데이터와 변경 결과 다루기"
description: "회원·강좌 테이블을 나누는 이유, SQL 오류 뒤 ROLLBACK이 필요한 경우, 인덱스로 달라지는 조회 계획을 SQLite 실습과 자체 문제 5개로 살펴봅니다."
date: "2026-10-23T18:39:49+09:00"
sourcesChecked: "2026-10-23"
category: "cs-study"
tags: ["전산", "NCS", "SQL", "정규화", "트랜잭션", "인덱스", "SQLite"]
draft: false
example: false
---

회원 이름을 수강 신청 행마다 저장하면 개명 한 번에 여러 행을 고쳐야 한다. 한 행만 수정하면 같은 회원에게 이름이 둘 생긴다. 테이블을 나누는 정규화는 이런 중복과 갱신 이상을 줄이는 설계 방법이다.

한편 이체의 두 UPDATE는 트랜잭션으로 함께 확정한다. 특정 회원의 행을 빠르게 찾을 방법을 마련할 때는 인덱스를 쓴다. 세 개념이 해결하는 문제를 나눠 살펴보자. [앞 글의 조인과 집계](../cs-study-02-sql-advanced/)는 나눈 테이블을 다시 조회할 때 사용한다.

## 수강 신청 한 행에 무엇을 저장할까

가상 업무 규칙을 먼저 정한다. 회원 번호는 이름 하나를, 강좌 번호는 강좌명과 강사 번호 하나를 결정한다. 강사 한 명은 강의실 하나를 사용한다. 한 회원은 같은 강좌에 한 번만 신청하므로 신청의 후보 키는 `(member_id, course_id)`다. 다른 후보 키는 없다고 가정한다.

| member_id | course_id | member_name | course_name | instructor_id | room |
| --- | --- | --- | --- | --- | --- |
| 1 | 10 | 가온 | SQL | 7 | 301호 |
| 2 | 10 | 나래 | SQL | 7 | 301호 |
| 2 | 20 | 나래 | 네트워크 | 7 | 301호 |

이 표에서 강좌 10번의 이름은 두 번 저장돼 있다. 한쪽만 바꾸면 강좌명이 달라지는 갱신 이상이 생긴다. 신청이 있어야 강좌를 저장하는 구조라면 신청자 없는 새 강좌를 넣기 어렵고, 마지막 신청을 지울 때 강좌 정보까지 사라진다. 각각 삽입 이상과 삭제 이상이다.

함수 종속 `X → Y`는 X 값이 정해지면 Y 값도 하나로 정해진다는 업무 규칙이다. 지금 보이는 세 행에서 우연히 값이 같다는 사실만으로 종속을 정하지 않는다. 강사마다 여러 강의실을 쓸 수 있는 업무라면 위의 강사·강의실 규칙부터 달라져야 한다.

## 1NF에서 3NF까지 분리하는 기준

- **1NF:** 한 속성에는 정한 도메인의 원자 값을 저장한다. 신청 강좌를 `10,20`이라는 목록으로 한 칸에 넣는 대신 신청마다 행을 둔다. 문자열에 쉼표가 있다는 이유만으로 모두 위반인 것은 아니다. 주소나 문장처럼 그 도메인에서 하나의 값으로 다루는 경우와 구별한다.
- **2NF:** 1NF를 만족하고, 후보 키에 속하지 않는 속성이 후보 키의 일부에만 종속되지 않아야 한다. 위 표의 강좌명은 복합 키 전체가 아니라 `course_id`만으로 정해진다. 회원 이름도 `member_id`만으로 정해지므로 신청 테이블에서 분리한다.
- **3NF:** 2NF에서 비키 속성 사이의 종속도 살핀다. 이번 규칙에서는 `course_id → instructor_id → room`으로 이어지므로 강의실을 강사 테이블로 옮긴다. 정식 조건은 비자명한 함수 종속 `X → A`마다 X가 슈퍼 키이거나 A가 후보 키에 속하는 속성이어야 한다는 것이다.

분리 뒤에는 회원, 강좌, 강사, 신청 테이블이 남는다. 정규화 단계를 높인다는 이유만으로 모든 열을 독립된 테이블로 쪼개지는 않는다. 키와 종속을 보존하고, 조인할 때 가짜 조합이 생기지 않는 분해인지도 살핀다. [Microsoft의 정규화 기초 설명](https://learn.microsoft.com/en-us/office/troubleshoot/access/database-normalization-description)은 중복 저장과 변경 이상을 예제로 설명한다.

## ZIP으로 SQLite 예제 실행하기

Python 3.12와 `sqlite3` 표준 모듈을 사용한다. 아래 기록은 Python 3.12.1·SQLite 3.43.1에서 남겼다. 별도 설치 패키지, DB 서버, 계정이나 입력 파일은 필요하지 않다. 모든 자료를 새 메모리 연결에 만들고 함수가 끝날 때 연결을 닫는다. `.db` 파일이나 로그를 디스크에 남기지 않는다.

ZIP을 빈 폴더에 풀고 Python 파일 두 개가 있는 폴더로 이동한다. 먼저 `python -I -B -X utf8 03-database-design.py`를 실행한다. Bash에서는 `python3`로 실행할 수 있다. 문제 풀이용 파일은 뒤에서 별도로 안내한다.

[[download]]

다음은 기본 실행 파일의 전체 코드다. 길어서 접어 두었으며 각 함수는 독립된 자료와 연결을 사용한다. 일부 SQL만 떼어 실행하려면 해당 함수의 테이블 생성과 초기 INSERT도 같은 연결에서 먼저 실행해야 한다.

```python
import json
import sqlite3


def show(label, value):
    print(f"{label}: {json.dumps(value, ensure_ascii=False)}")


def normalization():
    conn = sqlite3.connect(":memory:", isolation_level=None)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript("""
            CREATE TABLE members (member_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE instructors (instructor_id INTEGER PRIMARY KEY, room TEXT NOT NULL);
            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY, title TEXT NOT NULL,
                instructor_id INTEGER NOT NULL REFERENCES instructors(instructor_id)
            );
            CREATE TABLE enrollments (
                member_id INTEGER NOT NULL REFERENCES members(member_id),
                course_id INTEGER NOT NULL REFERENCES courses(course_id),
                PRIMARY KEY (member_id, course_id)
            );
            INSERT INTO members VALUES (1, '가온'), (2, '나래');
            INSERT INTO instructors VALUES (7, '301호');
            INSERT INTO courses VALUES (10, 'SQL', 7), (20, '네트워크', 7);
            INSERT INTO enrollments VALUES (1, 10), (2, 10), (2, 20);
        """)
        changed = conn.execute("UPDATE courses SET title = 'SQL 기초' WHERE course_id = 10").rowcount
        rows = conn.execute("""
            SELECT e.member_id, c.title, i.room FROM enrollments AS e
            JOIN courses AS c ON c.course_id = e.course_id
            JOIN instructors AS i ON i.instructor_id = c.instructor_id
            ORDER BY e.member_id, e.course_id
        """).fetchall()
        assert changed == 1
        assert rows == [(1, 'SQL 기초', '301호'), (2, 'SQL 기초', '301호'), (2, '네트워크', '301호')]
        show("수정한 강좌 행 수", changed)
        show("분리한 테이블의 조회", rows)
    finally:
        conn.close()


def transaction():
    # isolation_level=None으로 Python의 암시적 BEGIN을 끄고 SQL로 경계를 정한다.
    conn = sqlite3.connect(":memory:", isolation_level=None)
    try:
        conn.executescript("""
            CREATE TABLE wallets (id INTEGER PRIMARY KEY, balance INTEGER CHECK(balance >= 0));
            INSERT INTO wallets VALUES (1, 100), (2, 50);
        """)
        balances = lambda: conn.execute("SELECT id, balance FROM wallets ORDER BY id").fetchall()
        conn.execute("BEGIN")
        conn.execute("UPDATE wallets SET balance = balance - 30 WHERE id = 1")
        try:
            # 의도한 오류: 두 번째 잔액을 음수로 만들어 CHECK가 거부하게 한다.
            conn.execute("UPDATE wallets SET balance = -90 WHERE id = 2")
        except sqlite3.IntegrityError:
            show("오류 직후 같은 연결", balances())
            assert balances() == [(1, 70), (2, 50)]
            conn.execute("ROLLBACK")
        else:
            raise AssertionError("음수 잔액이 거부되지 않음")
        show("ROLLBACK 뒤", balances())
        assert balances() == [(1, 100), (2, 50)]
        conn.execute("BEGIN")
        conn.execute("UPDATE wallets SET balance = balance - 30 WHERE id = 1")
        conn.execute("UPDATE wallets SET balance = balance + 30 WHERE id = 2")
        conn.execute("COMMIT")
        assert balances() == [(1, 70), (2, 80)]
        show("정상 이체 COMMIT 뒤", balances())
    finally:
        conn.close()


def index_plan():
    conn = sqlite3.connect(":memory:", isolation_level=None)
    try:
        conn.execute("CREATE TABLE events (event_id INTEGER PRIMARY KEY, member_id INTEGER NOT NULL)")
        conn.executemany("INSERT INTO events VALUES (?, ?)", [(i, i % 10) for i in range(1, 101)])
        sql = "SELECT event_id FROM events WHERE member_id = 2 ORDER BY event_id"
        before_rows = conn.execute(sql).fetchall()
        before = [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql)]
        conn.execute("CREATE INDEX idx_events_member ON events(member_id)")
        after_rows = conn.execute(sql).fetchall()
        after = [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql)]
        assert before_rows == after_rows == [(i,) for i in range(2, 100, 10)]
        show("인덱스 전 계획", before)
        show("인덱스 후 계획", after)
        show("두 조회가 반환한 행 수", len(after_rows))
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"Python sqlite3 실습 / SQLite {sqlite3.sqlite_version}")
    normalization()
    transaction()
    index_plan()
    print("정규화 조회·트랜잭션·인덱스 결과 비교 완료")
```

`normalization()`은 `courses`의 강좌명 한 행을 수정하고 신청·강좌·강사 테이블을 조인한다. 반환 열은 회원 번호, 강좌명, 강의실 순서다. 강좌 10번의 행은 한 건만 수정했지만 조인 결과의 회원 1·2번 모두 새 강좌명을 읽는다. 두 신청 행을 UPDATE한 결과와 구별한다. `rowcount`와 실제 행 목록을 각각 비교한다.

## 오류 난 SQL 앞의 변경은 어디에 남을까

`transaction()`은 잔액 100·50인 지갑 두 개로 시작한다. `isolation_level=None`으로 Python의 암시적 BEGIN을 끄고 `BEGIN`, `COMMIT`, `ROLLBACK`을 SQL로 직접 실행한다. 이 설정에서 명시적 트랜잭션 없이 각 UPDATE를 실행하면 두 변경을 한 묶음으로 되돌릴 수 없다.

첫 이체는 의도적으로 실패시킨다. 1번 잔액에서 30을 뺀 뒤 2번을 -90으로 바꾸려 한다. `CHECK(balance >= 0)` 때문에 두 번째 UPDATE는 `IntegrityError`가 된다. 이 예제의 기본 ABORT 동작은 실패한 문장을 취소하지만 같은 트랜잭션의 앞선 UPDATE는 남겨 둔다. 코드가 오류를 잡은 직후 같은 연결에서 잔액을 조회하면 첫 차감이 보인다.

[[diagram]]

오류 처리 분기에서 `ROLLBACK`을 실행해야 이체 전 상태로 돌아간다. `else`의 `AssertionError`는 잘못된 입력이 예상대로 거부되지 않았을 때 시험을 중단하는 장치다. 임의의 모든 예외를 정상 결과로 바꾸지 않는다. SQLite의 [트랜잭션 경계](https://www.sqlite.org/lang_transaction.html)와 [ABORT 동작](https://www.sqlite.org/lang_conflict.html)은 다른 DBMS를 다루는 문제에 그대로 일반화하지 않는다.

두 번째 이체는 차감과 입금을 모두 성공시킨 뒤 COMMIT한다. ACID의 원자성은 이처럼 한 작업 묶음의 전부 또는 전무를 뜻한다. 일관성은 정의한 제약과 규칙의 유지, 격리성은 동시 트랜잭션의 관찰 관계, 지속성은 확정한 변경의 보존이다. 이번 단일 연결·메모리 DB 실습은 동시성이나 장애 뒤 디스크 복구를 시험하지 않는다.

## 인덱스가 바꾸는 조회 방법

`index_plan()`의 가상 이벤트는 100건이다. 회원 번호는 `i % 10`으로 정하며, 회원 2번의 이벤트 번호는 2부터 10씩 증가한다. 인덱스 전후에 같은 SELECT를 실행하고 결과 값과 순서가 같은지 비교한다. `ORDER BY event_id`가 있으므로 행 순서도 대조할 수 있다.

`EXPLAIN QUERY PLAN`의 마지막 열은 조회 방법을 설명한다. 이번 실행에서는 인덱스 전의 `SCAN events`가 인덱스 생성 후 `SEARCH events USING COVERING INDEX ...`로 바뀌었다. SQLite의 일반 인덱스에는 rowid가 포함되고, 이 테이블의 `INTEGER PRIMARY KEY`인 event_id는 rowid의 별칭이므로 조회 열을 인덱스에서 얻을 수 있다.

[[run:1]]

실행 기록의 ‘오류 직후 같은 연결’은 70·50, ‘ROLLBACK 뒤’는 100·50이다. 잘못된 두 번째 변경은 거부됐지만 앞선 차감은 ROLLBACK 전까지 남아 있었다. 정상 이체 COMMIT 뒤의 70·80은 두 UPDATE가 함께 확정된 결과다. 음수 -90이 저장된 성공 사례로 읽지 않는다.

인덱스 전후의 반환 행 수는 모두 10이다. 시간 측정은 하지 않았으므로 이 결과에 속도 개선 배수를 붙이지 않는다. 실행 계획 문구와 선택은 SQLite 버전·통계·자료 분포에 따라 달라질 수 있다. 인덱스에는 추가 저장 공간이 필요하고 쓰기 시 갱신 비용도 든다. 자세한 조회 방식은 [SQLite Query Planning](https://www.sqlite.org/queryplanner.html)에서 볼 수 있다.

프로세스는 각 `assert`가 실제 행과 기대 행을 대조한 뒤 마지막 줄을 출력한다. 종료 코드 0과 빈 표준 오류를 함께 기록했다. 출력만 복사해서 통과를 판단하기보다 프로그램이 끝까지 실행됐는지 함께 살핀다. 검사를 끄는 Python의 `-O` 옵션은 사용하지 않는다.

## 자체 연습문제 5개

아래 문제는 직접 만든 연습용 자료다. 정답과 해설은 각 문제 바로 아래에서 펼쳐 볼 수 있다.

### 문제 1. 복합 키 중 일부만으로 정해지는 값

신청 테이블의 유일한 후보 키는 `(member_id, course_id)`이고 `course_id → course_name`이 성립한다. 테이블은 1NF를 만족한다. 강좌명을 이 테이블에 두면 2NF 조건을 만족하는가? 이유를 설명하자.

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 문제 1: 강좌명이 키 일부에 종속된다

만족하지 않는다. 후보 키에 속하지 않는 `course_name`이 전체 키의 진부분집합인 `course_id`만으로 정해지는 부분 함수 종속이 있다. 강좌 정보를 강좌 테이블로 분리하고 신청 테이블에는 두 식별자를 남긴다. 열 이름이 길거나 같은 문자열이 반복된다는 사실이 아니라 명시한 함수 종속으로 판단한다.

</details>

### 문제 2. 이름 한 행만 바꾼 결과

`registrations`에 `(1, 10, '가온')`, `(1, 20, '가온')` 두 행이 있고 열 순서는 회원 번호, 강좌 번호, 회원 이름이다. 다음 UPDATE 뒤 강좌 번호로 정렬해 조회한 `(course_id, member_name)` 두 행을 적자.

```sql
UPDATE registrations SET member_name = '새이름'
WHERE member_id = 1 AND course_id = 10;
```

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 문제 2: 같은 회원의 이름이 둘로 갈라진다

결과는 `(10, '새이름')`, `(20, '가온')`이다. WHERE가 강좌 10번 행만 선택했으므로 20번 행은 바뀌지 않는다. 회원 이름을 회원 테이블에 한 번 저장하면 이 불일치를 줄일 수 있다. 키 제약을 위반하지 않았다는 사실과 업무 자료가 일관된다는 판단은 다르다.

</details>

### 문제 3. 강의실의 저장 위치

`courses(course_id, instructor_id, room)`에서 후보 키는 `course_id` 하나다. 업무 규칙은 `course_id → instructor_id`, `instructor_id → room`이며 한 강사가 여러 강좌를 담당한다. 3NF를 고려하면 테이블을 어떻게 나눌 수 있는가?

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 문제 3: 강사 번호로 강의실을 분리한다

`courses(course_id, instructor_id)`와 `instructors(instructor_id, room)`으로 나눈다. 원래 테이블의 강사 번호는 슈퍼 키가 아니고 강의실도 후보 키의 일부가 아니므로 `instructor_id → room`이 3NF 조건에 맞지 않는다. 강좌마다 강의실이 달라지는 업무라면 이 함수 종속 자체가 달라진다.

</details>

### 문제 4. COMMIT 뒤에 새로 시작한 변경

지갑 잔액이 1번 100, 2번 50이다. 첫 트랜잭션에서 1번의 20을 차감하고 2번에 20을 더한 뒤 COMMIT한다. 두 번째 트랜잭션에서는 같은 방향으로 10을 옮긴 뒤 ROLLBACK한다. 마지막 잔액은 각각 얼마인가?

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 문제 4: 두 번째 변경만 취소된다

1번 80, 2번 70이다. 첫 묶음은 이미 COMMIT했으므로 두 번째 BEGIN의 출발점은 80·70이다. 두 번째 차감·입금만 ROLLBACK으로 취소된다. ROLLBACK을 데이터베이스 생성 이후의 모든 변경을 되돌리는 명령으로 이해하면 틀린다.

</details>

### 문제 5. 복합 인덱스와 조회 순서

`enrollments`의 `(member_id, course_id)` 인덱스와 `(2, 30)`, `(1, 10)`, `(2, 20)` 세 행이 있다. 다음 SELECT의 결과를 적고, 인덱스의 앞쪽 열과 조회 조건이 어떻게 대응하는지 설명하자.

```sql
SELECT course_id FROM enrollments
WHERE member_id = 2 ORDER BY course_id;
```

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 문제 5: 회원을 고른 뒤 강좌 번호순으로 읽는다

결과는 20, 30 순서의 두 행이다. 복합 인덱스는 회원 번호가 먼저, 같은 회원 안에서는 강좌 번호순으로 정렬돼 있어 동등 조건과 정렬 조건에 대응한다. 실제 사용 여부는 실행 계획으로 살핀다. 인덱스가 있다는 이유만으로 SQL의 정렬 보장이 생기지는 않으므로 ORDER BY를 유지한다. 앞쪽 열 조건이 없는 조회가 어떤 경우에도 인덱스를 쓰지 못한다고 단정하지도 않는다.

</details>

## 문제의 SQL을 직접 대조하기

문제를 푼 뒤 같은 폴더에서 `python -I -B -X utf8 03-database-design-questions.py`를 실행한다. SQL 문제 2·4·5는 각각 새 메모리 DB를 만들어 실제 행 목록을 비교한다. 개념 문제 1·3은 위에서 제시한 업무 규칙과 함수 종속으로 해설을 검토했으며, 표준 출력의 문장만으로 정규형이 자동 증명되는 것은 아니다.

<details class="practice-solutions">
<summary>문제 검증 전체 코드 보기</summary>

```python
import json
import sqlite3


def main():
    answers = {}
    # 문제 1의 속성 종속을 집합으로 비교한다.
    key = {"member_id", "course_id"}
    determinant = {"course_id"}
    assert determinant < key
    answers["q1"] = "course_name은 복합 키 일부인 course_id에 종속"
    conn = sqlite3.connect(":memory:", isolation_level=None)
    try:
        conn.executescript("""
            CREATE TABLE registrations (member_id INTEGER, course_id INTEGER, member_name TEXT,
                PRIMARY KEY(member_id, course_id));
            INSERT INTO registrations VALUES (1, 10, '가온'), (1, 20, '가온');
            UPDATE registrations SET member_name = '새이름' WHERE member_id = 1 AND course_id = 10;
        """)
        answers["q2"] = conn.execute("SELECT course_id, member_name FROM registrations ORDER BY course_id").fetchall()
        assert answers["q2"] == [(10, '새이름'), (20, '가온')]
    finally:
        conn.close()
    # 문제 3의 함수 종속은 명시한 가상 업무 규칙이다.
    answers["q3"] = ["courses(course_id, instructor_id)", "instructors(instructor_id, room)"]
    conn = sqlite3.connect(":memory:", isolation_level=None)
    try:
        conn.executescript("""
            CREATE TABLE wallets (id INTEGER PRIMARY KEY, balance INTEGER);
            INSERT INTO wallets VALUES (1, 100), (2, 50);
            BEGIN;
            UPDATE wallets SET balance = balance - 20 WHERE id = 1;
            UPDATE wallets SET balance = balance + 20 WHERE id = 2;
            COMMIT;
            BEGIN;
            UPDATE wallets SET balance = balance - 10 WHERE id = 1;
            UPDATE wallets SET balance = balance + 10 WHERE id = 2;
            ROLLBACK;
        """)
        answers["q4"] = conn.execute("SELECT id, balance FROM wallets ORDER BY id").fetchall()
        assert answers["q4"] == [(1, 80), (2, 70)]
    finally:
        conn.close()
    conn = sqlite3.connect(":memory:", isolation_level=None)
    try:
        conn.executescript("""
            CREATE TABLE enrollments (member_id INTEGER, course_id INTEGER);
            INSERT INTO enrollments VALUES (2, 30), (1, 10), (2, 20);
            CREATE INDEX idx_enrollments_member_course ON enrollments(member_id, course_id);
        """)
        answers["q5"] = conn.execute("SELECT course_id FROM enrollments WHERE member_id = 2 ORDER BY course_id").fetchall()
        assert answers["q5"] == [(20,), (30,)]
    finally:
        conn.close()
    for name, result in answers.items():
        print(f"{name}: {json.dumps(result, ensure_ascii=False)}")
    print("자체 문제: SQL 3건 실행, 개념 2건의 비교 자료 출력")


if __name__ == "__main__":
    main()
```

</details>

기록의 `q` 번호는 해당 문제와 대응한다. 아래 종합 출력도 처음에는 접혀 있다. 질문의 기대값을 바꾸려면 초기 자료와 검증 식을 함께 검토하며, 앞 문제에서 바꾼 테이블을 다음 문제의 연결로 가져오지 않는다.

[[run:2:fold]]

입력 자료는 두 Python 파일 안에 있고 실행 뒤 남는 생성 파일은 없다. SQL 문법이나 예상 행이 어긋나면 예외로 멈추므로, 이때는 첫 오류가 난 SQL과 초기 테이블 생성 여부를 살핀다.

## 시험 직전 복습

- 정규형은 현재 몇 행이 중복돼 보이는지가 아니라 후보 키와 함수 종속을 보고 판단한다.
- 2NF는 부분 함수 종속, 3NF는 비키 속성을 거치는 종속까지 구분한다.
- 트랜잭션의 경계는 BEGIN과 COMMIT·ROLLBACK으로 정한다. 오류가 난 문장과 전체 묶음의 취소는 같지 않을 수 있다.
- 인덱스의 조회 계획 변화와 반환 행의 정확성, 실제 실행 시간은 따로 검증한다.
