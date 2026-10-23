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
