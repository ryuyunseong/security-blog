#!/usr/bin/env python3
"""로컬 passwd/group 자료에서 그룹 검토 대상을 수집한다."""
import argparse
import json
import os
import re
import stat
import sys

LIMIT = 4 * 1024 * 1024
NAME = re.compile(r"[^\s:,\x00-\x1f\x7f]+\Z")


def name(value):
    if not NAME.fullmatch(value) or value.startswith(("+", "-", "#")):
        raise ValueError("지원하지 않는 이름 형식")
    return value


def number(value):
    if not re.fullmatch(r"[0-9]{1,10}", value) or int(value) > 4294967294:
        raise ValueError("UID 또는 GID 형식 오류")
    return int(value)


def rows(path, count):
    # 일반 파일만 읽고 FIFO에서 대기하지 않는다.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("일반 파일만 지원함")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("입력 파일이 4 MiB를 초과함")
    result, seen = [], set()
    for line in data.decode("utf-8").splitlines():
        if not line:
            continue
        fields = line.split(":")
        if len(fields) != count:
            raise ValueError("입력 필드 수 오류")
        key = name(fields[0])
        if key in seen:
            raise ValueError("중복 이름 또는 분할 그룹은 수동 확인 필요")
        seen.add(key)
        result.append(fields)
    if not result:
        raise ValueError("빈 계정 또는 그룹 목록")
    return result


def inspect(passwd_path, group_path):
    users, primary, groups = {}, {}, {}
    for row in rows(passwd_path, 7):
        number(row[2])
        gid = number(row[3])
        users[row[0]] = gid
        primary.setdefault(gid, set()).add(row[0])
    for row in rows(group_path, 4):
        gid = number(row[2])
        members = {name(x) for x in row[3].split(",")} if row[3] else set()
        entry = groups.setdefault(gid, {"names": [], "members": set()})
        entry["names"].append(row[0])
        entry["members"].update(members)
    findings = []
    for gid, entry in sorted(groups.items()):
        known = entry["members"] & users.keys()
        unknown = entry["members"] - users.keys()
        reasons = []
        if not primary.get(gid) and not known:
            reasons.append("로컬 구성원 미관찰")
        if unknown:
            reasons.append("명시 구성원의 로컬 계정 미관찰")
        if len(entry["names"]) > 1:
            reasons.append("같은 GID를 사용하는 여러 그룹 이름")
        if reasons:
            findings.append({
                "GID": gid,
                "그룹": sorted(entry["names"]),
                "기본 구성원": sorted(primary.get(gid, set())),
                "보조 구성원": sorted(known),
                "로컬 미관찰 이름": sorted(unknown),
                "사유": reasons,
            })
    missing = [
        {"계정": user, "기본GID": gid}
        for user, gid in sorted(users.items())
        if gid not in groups
    ]
    result = {"그룹 검토 대상": findings, "그룹 정의 없는 기본GID": missing}
    return (1 if findings or missing else 0), result


def main():
    parser = argparse.ArgumentParser(description="로컬 그룹 검토 자료 수집")
    parser.add_argument("--passwd", default="/etc/passwd", help="계정 파일 경로")
    parser.add_argument("--group", default="/etc/group", help="그룹 파일 경로")
    args = parser.parse_args()
    try:
        status, result = inspect(args.passwd, args.group)
    except (OSError, ValueError) as exc:
        print("실행 오류: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("추가 확인 필요" if status else "기계적 검토 대상 없음: 보안 양호 판정은 아님")
    return status


if __name__ == "__main__":
    sys.exit(main())
