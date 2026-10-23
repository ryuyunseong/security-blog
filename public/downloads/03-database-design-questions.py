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
