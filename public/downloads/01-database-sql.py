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
