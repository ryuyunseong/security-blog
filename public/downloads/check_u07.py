#!/usr/bin/env python3
import argparse
import json
import os
import re
import stat
import sys

LIMIT = 2 * 1024 * 1024
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*\$?", re.ASCII)


def read_text(path):
    # 일반 파일만 읽고 입력 크기를 제한한다. 설정은 변경하지 않는다.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("일반 파일이 아닌 입력")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("입력 파일이 2 MiB를 초과함")
    return data.decode("utf-8")


def parse_passwd(text):
    accounts = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line:
            continue
        fields = line.split(":")
        if len(fields) != 7 or not NAME.fullmatch(fields[0]):
            raise ValueError(f"passwd {number}행: 지원하지 않는 계정 형식")
        name, _, uid, gid, _, home, shell = fields
        if not all(re.fullmatch(r"[0-9]{1,10}", value) for value in (uid, gid)):
            raise ValueError(f"passwd {number}행: UID/GID 형식 확인 필요")
        if name in accounts:
            raise ValueError(f"passwd {number}행: 계정 이름 중복")
        accounts[name] = {
            "계정": name,
            "UID": int(uid),
            "홈": home,
            "셸": shell or "(빈 값)",
        }
    if not accounts:
        raise ValueError("passwd에서 계정을 읽지 못함")
    return accounts


def parse_approved(text):
    approved = set()
    for number, line in enumerate(text.splitlines(), 1):
        name = line.strip()
        # 승인 목록에서만 빈 줄과 #으로 시작하는 설명을 허용한다.
        if not name or name.startswith("#"):
            continue
        if not NAME.fullmatch(name) or name in approved:
            raise ValueError(f"승인 목록 {number}행: 이름 형식 또는 중복 확인 필요")
        approved.add(name)
    if not approved:
        raise ValueError("승인 목록이 비어 있음")
    return approved


def main():
    parser = argparse.ArgumentParser(
        description="로컬 계정과 승인 목록을 읽기 전용으로 비교"
    )
    parser.add_argument(
        "--passwd", default="/etc/passwd", help="점검할 passwd 파일"
    )
    parser.add_argument(
        "--approved", required=True, help="유지 필요성이 검토된 로컬 계정 목록"
    )
    args = parser.parse_args()

    try:
        accounts = parse_passwd(read_text(args.passwd))
        approved = parse_approved(read_text(args.approved))
    except (OSError, UnicodeError, ValueError) as error:
        print("오류: " + str(error), file=sys.stderr)
        return 2

    extra = sorted(set(accounts) - approved)
    missing = sorted(approved - set(accounts))
    result = {
        "수집한 로컬 계정 수": len(accounts),
        "승인 목록에 없는 계정": [accounts[name] for name in extra],
        "로컬 파일에 없는 승인 계정": missing,
        "결과": "추가 확인 필요" if extra or missing else "목록 대조 완료",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if extra or missing else 0


if __name__ == "__main__":
    sys.exit(main())
