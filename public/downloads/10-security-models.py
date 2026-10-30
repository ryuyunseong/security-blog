import argparse
from contextlib import closing
import hashlib
import hmac
import sqlite3


def test_vector():
    return bytes([0x0b]) * 20, b"Hi There"


def tag_for(test_key, message):
    return hmac.digest(test_key, message, "sha256")


def can_read(actor, document):
    if actor is None:
        return False
    if actor["role"] == "admin":
        return True
    return actor["role"] == "reader" and actor["id"] == document["owner"]


def lookup_id(name):
    if not isinstance(name, str):
        raise TypeError("이름은 문자열이어야 한다")
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        conn.executemany("INSERT INTO users VALUES (?, ?)", [(1, "alice"), (2, "bob")])
        result = conn.execute("SELECT id FROM users WHERE name = ? ORDER BY id", (name,))
        return [row[0] for row in result]


def main():
    parser = argparse.ArgumentParser(description="공개 시험 벡터와 가상 권한·SQL을 비교한다")
    parser.add_argument("example", choices=("mac", "access", "sql"))
    args = parser.parse_args()
    if args.example == "mac":
        test_key, message = test_vector()
        tag = tag_for(test_key, message)
        print("HMAC-SHA-256: " + tag.hex())
        print(f"원문 대조: {hmac.compare_digest(tag, tag_for(test_key, message))}")
        print(f"변경문 대조: {hmac.compare_digest(tag, tag_for(test_key, message + b'!'))}")
        print(f"SHA-256 길이: {len(hashlib.sha256(message).digest())}바이트")
    elif args.example == "access":
        document = {"id": 7, "owner": 1001}
        for label, actor in [("미인증", None), ("소유자", {"id": 1001, "role": "reader"}), ("다른 계정", {"id": 1002, "role": "reader"}), ("관리자", {"id": 1003, "role": "admin"})]:
            print(f"{label}: {'허용' if can_read(actor, document) else '거부'}")
    else:
        for name in ("alice", "alice' OR 1=1 --", "nobody"):
            print(f"이름={name!r}, 일치 ID={lookup_id(name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
