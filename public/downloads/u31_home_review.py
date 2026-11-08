import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키 중복")
        result[key] = value
    return result


def is_uid(value):
    return type(value) is int and value >= 0


def validate(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError("입력은 1~1000건의 목록이어야 함")
    fields = {"id", "accountUid", "home", "state", "ownerUid", "mode", "acl"}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != fields:
            raise ValueError("필드 목록 불일치")
        label = row["id"]
        if not isinstance(label, str) or not re.fullmatch(r"[a-z0-9-]{1,40}", label):
            raise ValueError("id 형식 오류")
        if label in seen:
            raise ValueError("id 중복")
        seen.add(label)
        if not is_uid(row["accountUid"]):
            raise ValueError("accountUid는 음수가 아닌 정수여야 함")
        home = row["home"]
        if not isinstance(home, str) or not re.fullmatch(r"/[A-Za-z0-9_/-]{0,239}", home):
            raise ValueError("home 경로 형식 오류")
        if str(PurePosixPath(home)) != home or ".." in PurePosixPath(home).parts:
            raise ValueError("home은 정규화된 Unix 절대 경로여야 함")
        state = row["state"]
        if state not in ("directory", "symlink", "other_type", "missing", "read_error", "uncollected"):
            raise ValueError("state 형식 오류")
        if state != "directory":
            if any(row[key] is not None for key in ("ownerUid", "mode", "acl")):
                raise ValueError("디렉터리 미확정 상태의 메타데이터는 null이어야 함")
            continue
        if not is_uid(row["ownerUid"]):
            raise ValueError("ownerUid는 음수가 아닌 정수여야 함")
        if not isinstance(row["mode"], str) or not re.fullmatch(r"[0-7]{4}", row["mode"]):
            raise ValueError("mode는 네 자리 8진수 문자열이어야 함")
        if row["acl"] not in ("none", "extended", "unknown"):
            raise ValueError("acl은 none, extended, unknown 중 하나여야 함")
    return rows


def load_rows(path):
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(1_000_001)
    except OSError as error:
        raise ValueError("지정한 입력 파일을 읽지 못함") from error
    if len(raw) > 1_000_000:
        raise ValueError("입력 크기 제한 초과")
    return validate(json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object))


def review(row):
    state = row["state"]
    if state != "directory":
        reasons = {"symlink": "링크와 대상 별도 조회", "other_type": "디렉터리 아님",
                   "missing": "경로 부재 자료, 존재 관리는 U-32와 구분",
                   "read_error": "조회 오류", "uncollected": "자료 미수집"}
        return "보류", reasons[state]
    mode = int(row["mode"], 8)
    write_bits = mode & 0o022
    issues, pending = [], []
    if row["ownerUid"] != row["accountUid"]:
        issues.append("소유 UID 불일치")
    if write_bits:
        issues.append(f"일반모드 쓰기={write_bits:04o}")
    if row["acl"] != "none":
        pending.append("확장 ACL 조사" if row["acl"] == "extended" else "ACL 미수집")
    special = mode & 0o7000
    if special:
        pending.append(f"특수 비트={special:04o} 별도 조사")
    status = "검토 후보" if issues else "보류" if pending else "입력 조건 일치"
    detail = "; ".join(issues + pending) or "소유 UID 일치, 일반모드 쓰기=0000, 확장 ACL 없음"
    return status, detail


def main():
    parser = argparse.ArgumentParser(description="가상 홈 디렉터리 수집 자료 비교")
    parser.add_argument("fixture")
    args = parser.parse_args()
    try:
        rows = load_rows(args.fixture)
    except (ValueError, UnicodeError, RecursionError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        status, detail = review(row)
        if row["state"] == "directory":
            metadata = f"UID={row['accountUid']}/소유={row['ownerUid']}, mode={row['mode']}: "
        else:
            metadata = ""
        print(f"{row['id']}: {metadata}{status} ({detail})")
    print(f"가상 자료 {len(rows)}건 분류 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
