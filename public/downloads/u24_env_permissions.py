import argparse
import json
from pathlib import Path
import re
import sys


def validate(row):
    fields = {"case", "homeUid", "ownerUid", "kind", "mode", "acl"}
    if not isinstance(row, dict) or set(row) != fields:
        raise ValueError("필드가 맞지 않는다")
    if not isinstance(row["case"], str) or not row["case"].strip():
        raise ValueError("사례 이름이 필요하다")
    for key in ("homeUid", "ownerUid"):
        if type(row[key]) is not int or row[key] < 0:
            raise ValueError("UID는 0 이상의 정수여야 한다")
    if row["kind"] not in ("file", "link"):
        raise ValueError("종류는 file 또는 link여야 한다")
    if not isinstance(row["mode"], str) or not re.fullmatch(r"[0-7]{4}", row["mode"]):
        raise ValueError("모드는 네 자리 8진수 문자열이어야 한다")
    if row["acl"] not in ("none", "extended", "unknown"):
        raise ValueError("ACL 수집 상태가 맞지 않는다")


def compare(row):
    mode = int(row["mode"], 8)
    if row["kind"] != "file" or row["acl"] != "none" or mode & 0o7000:
        return "추가 조사", "링크·ACL·특수 비트 자료를 별도로 조사"
    reasons = []
    if row["ownerUid"] not in (0, row["homeUid"]):
        reasons.append("소유자 불일치")
    extra_write = mode & 0o022
    if extra_write:
        reasons.append(f"그룹·기타 쓰기 {extra_write:03o}")
    if reasons:
        return "기준 이탈", ", ".join(reasons)
    return "기본 조건 일치", "소유자와 일반 쓰기 비트가 조건에 들어감"


def main():
    parser = argparse.ArgumentParser(description="가상 환경변수 파일의 수집 자료를 비교한다")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        rows = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(rows, list) or not rows:
            raise ValueError("비어 있지 않은 배열이 필요하다")
        seen = set()
        for row in rows:
            validate(row)
            if row["case"] in seen:
                raise ValueError("사례 이름이 중복됐다")
            seen.add(row["case"])
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    counts = {"기본 조건 일치": 0, "기준 이탈": 0, "추가 조사": 0}
    for row in rows:
        state, detail = compare(row)
        counts[state] += 1
        print(f"{row['case']}: {state}; {detail}")
    print("가상 자료 " + str(len(rows)) + "건: " + ", ".join(f"{key} {value}건" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
