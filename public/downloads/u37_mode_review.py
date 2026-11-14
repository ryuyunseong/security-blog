import json
from pathlib import Path
import re
import sys


LIMITS = {"command": 0o750, "settings": 0o640}
STATES = {"collected", "absent", "query-error", "uncollected"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("중복 키")
        result[key] = value
    return result


def load_rows(path):
    with path.open("rb") as stream:
        raw = stream.read(32001)
    if len(raw) > 32000:
        raise ValueError("입력 크기")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("목록 크기")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
                "id", "kind", "path", "collection", "uid", "mode"}:
            raise ValueError("행 필드")
        if (not isinstance(row["id"], str)
                or not re.fullmatch(r"[a-z0-9-]{1,24}", row["id"])
                or row["id"] in seen):
            raise ValueError("행 ID")
        seen.add(row["id"])
        if row["kind"] not in LIMITS or row["collection"] not in STATES:
            raise ValueError("종류 또는 수집 상태")
        path_text = row["path"]
        if (not isinstance(path_text, str) or not path_text.startswith("/")
                or len(path_text) > 120 or any(ord(c) < 32 for c in path_text)):
            raise ValueError("가상 경로")
        if row["collection"] == "collected":
            if (type(row["uid"]) is not int or not 0 <= row["uid"] <= 2147483647
                    or not isinstance(row["mode"], str)
                    or not re.fullmatch(r"[0-7]{4}", row["mode"])):
                raise ValueError("소유자 또는 모드")
        elif row["uid"] is not None or row["mode"] is not None:
            raise ValueError("미수집 값은 null")
    return rows


def assess(row):
    if row["collection"] != "collected":
        return "보류", row["collection"]
    mode = int(row["mode"], 8)
    limit = LIMITS[row["kind"]]
    extra = (mode & 0o777) & (~limit & 0o777)
    special = mode & 0o7000
    reasons = []
    if row["uid"] != 0:
        reasons.append(f"소유 UID {row['uid']}")
    if extra:
        reasons.append(f"범위 밖 일반 비트 {extra:04o}")
    if reasons:
        if special:
            reasons.append(f"특수 비트 {special:04o} 별도 조사")
        return "검토 후보", ", ".join(reasons)
    if special:
        return "보류", f"특수 비트 {special:04o} 별도 조사"
    return "일반 권한 범위 내", f"UID 0, 기준 {limit:04o}의 비트 부분집합"


def main():
    if len(sys.argv) != 2:
        print("사용법: python u37_mode_review.py 가상입력.json", file=sys.stderr)
        return 2
    try:
        rows = load_rows(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, TypeError):
        print("가상 권한 비교 미실행")
        print("입력 오류: 경로, UTF-8, JSON, 필드와 수집 상태를 살펴보세요", file=sys.stderr)
        return 2
    counts = {name: 0 for name in ("일반 권한 범위 내", "검토 후보", "보류")}
    for row in rows:
        status, reason = assess(row)
        counts[status] += 1
        print(f"{row['id']}: {status} | {reason}")
    print("가상 자료 " + str(len(rows)) + "건: " + ", ".join(
        f"{name} {count}" for name, count in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
