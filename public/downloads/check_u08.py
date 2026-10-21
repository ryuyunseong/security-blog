#!/usr/bin/env python3
"""로컬 관리자 그룹 구성원을 승인 목록과 읽기 전용으로 비교한다."""
import argparse
import json
import os
import re
import stat
import sys

NAME = re.compile(r"[^\s:,\x00-\x1f\x7f]+\Z")
LIMIT = 4 * 1024 * 1024
MAX_ID = 4294967294


def name(value):
    if not NAME.fullmatch(value) or value.startswith(("+", "-", "#")):
        raise ValueError("지원하지 않는 계정 또는 그룹 이름")
    return value


def number(value):
    # 숫자 길이를 먼저 제한해 과도하게 긴 정수 변환을 피한다.
    if not re.fullmatch(r"[0-9]{1,10}", value):
        raise ValueError("UID 또는 GID 형식 오류")
    parsed = int(value)
    if parsed > MAX_ID:
        raise ValueError("UID 또는 GID 범위 오류")
    return parsed


def rows(path, count):
    # FIFO를 열다가 멈추지 않도록 비차단으로 열고 일반 파일인지 확인한다.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("일반 파일만 읽을 수 있음")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("입력 파일 크기 제한 초과")

    seen, result = set(), []
    for line in data.decode("utf-8").splitlines():
        if not line:
            continue
        parts = line.split(":")
        if len(parts) != count:
            raise ValueError("입력 필드 수 오류")
        key = name(parts[0])
        if key in seen:
            raise ValueError("중복 이름: " + key)
        seen.add(key)
        result.append(parts)
    if not result:
        raise ValueError("빈 계정 또는 그룹 목록")
    return result


def inspect(passwd_path, group_path, target, allowed):
    users = {}
    for p in rows(passwd_path, 7):
        number(p[2])
        users[p[0]] = number(p[3])

    groups = {}
    for g in rows(group_path, 4):
        members = {name(x) for x in g[3].split(",")} if g[3] else set()
        groups[g[0]] = (number(g[2]), members)

    if target not in groups:
        return 1, {
            "그룹": target,
            "결과": "추가 확인",
            "사유": "대상 그룹이 입력에 없음",
        }

    gid = groups[target][0]
    aliases = sorted(k for k, v in groups.items() if v[0] == gid)
    primary = {k for k, v in users.items() if v == gid}
    supplementary = set().union(*(groups[k][1] for k in aliases))
    observed = primary | supplementary
    unknown = supplementary - users.keys()

    report = {
        "그룹": target,
        "GID": gid,
        "같은 GID의 그룹": aliases,
        "기본 그룹 구성원": sorted(primary),
        "명시된 보조 구성원": sorted(supplementary),
        "승인 목록 밖": sorted(observed - allowed),
        "승인됐지만 관찰되지 않음": sorted(allowed - observed),
        "passwd에서 찾지 못한 구성원": sorted(unknown),
    }
    review = bool(observed != allowed or unknown or len(aliases) > 1)
    report["결과"] = "추가 확인" if review else "입력 범위에서 승인 목록과 일치"
    return int(review), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passwd", default="/etc/passwd", help="로컬 계정 파일")
    parser.add_argument("--group-file", default="/etc/group", help="로컬 그룹 파일")
    parser.add_argument("--group", default="root", help="점검할 그룹 이름")
    parser.add_argument(
        "--allow", action="append", required=True, help="승인 계정명, 계정마다 반복"
    )
    args = parser.parse_args()

    try:
        allowed = {name(x) for x in args.allow}
        code, report = inspect(
            args.passwd, args.group_file, name(args.group), allowed
        )
    except (OSError, UnicodeError, ValueError) as error:
        print("실행 오류: " + str(error), file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
