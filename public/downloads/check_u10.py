#!/usr/bin/env python3
"""passwd 자료에서 같은 숫자 UID를 사용하는 계정을 찾는다."""
import argparse
import json
import os
import re
import stat
import sys

LIMIT = 4 * 1024 * 1024


def number(value):
    if not re.fullmatch(r"[0-9]{1,10}", value):
        raise ValueError("UID 또는 GID 형식 오류")
    result = int(value)
    if result > 4294967294:
        raise ValueError("이 예제의 UID 또는 GID 범위 초과")
    return result


def inspect(path):
    # FIFO 등에서 대기하지 않고 일반 파일만 읽는다.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("일반 파일만 입력할 수 있음")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("입력 파일은 4 MiB 이하여야 함")

    names, by_uid = set(), {}
    for line_no, line in enumerate(data.decode("utf-8").split("\n"), 1):
        line = line.removesuffix("\r")
        if not line:
            continue
        if any(ord(c) < 32 or ord(c) == 127 for c in line):
            raise ValueError(f"{line_no}행: 제어 문자 포함")
        fields = line.split(":")
        if len(fields) != 7:
            raise ValueError(f"{line_no}행: 필드 수 오류")
        name = fields[0]
        if (
            not name
            or name.startswith(("+", "-", "#"))
            or any(c.isspace() or c == "," for c in name)
        ):
            raise ValueError(f"{line_no}행: 지원하지 않는 계정 이름")
        if name in names:
            raise ValueError(f"{line_no}행: 계정 이름 중복")
        names.add(name)
        uid = number(fields[2])
        number(fields[3])
        by_uid.setdefault(uid, []).append(name)

    if not names:
        raise ValueError("계정 자료가 비어 있음")
    duplicates = [
        {"UID": uid, "계정": sorted(users)}
        for uid, users in sorted(by_uid.items())
        if len(users) > 1
    ]
    return {"확인한 계정 수": len(names), "중복 UID": duplicates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passwd", default="/etc/passwd", help="읽을 passwd 파일")
    args = parser.parse_args()
    try:
        report = inspect(args.passwd)
    except (OSError, UnicodeError, ValueError) as error:
        print("실행 오류: " + str(error), file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    found = bool(report["중복 UID"])
    print(
        "중복 발견: 해당 계정과 영향 범위 확인 필요"
        if found else "입력 범위에서 중복 UID 미발견"
    )
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
