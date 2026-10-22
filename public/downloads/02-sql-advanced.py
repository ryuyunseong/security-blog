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
