import json
import re
import sys
from pathlib import Path, PurePosixPath

COLLECTIONS = {"collected", "absent", "query-error", "uncollected"}
TARGET_NAMES = {"automountd", "automount", "autofs"}
KEYS = {"id", "collection", "processes"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키가 중복됐어요")
        result[key] = value
    return result


def load_rows(path):
    with path.open("rb") as source:
        raw = source.read(16001)
    if len(raw) > 16000:
        raise ValueError("입력은 16000바이트 이하여야 해요")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 12:
        raise ValueError("사례 목록은 1~12건이어야 해요")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != KEYS:
            raise ValueError("입력 행의 키가 맞지 않아요")
        case_id = row["id"]
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9-]{1,32}", case_id):
            raise ValueError("id 형식이 잘못됐어요")
        if case_id in ids:
            raise ValueError("id가 중복됐어요")
        ids.add(case_id)
        state = row["collection"]
        if not isinstance(state, str) or state not in COLLECTIONS:
            raise ValueError("collection 지원 값이 아니에요")
        items = row["processes"]
        if state != "collected":
            if items is not None:
                raise ValueError("미수집 상태의 processes는 null이어야 해요")
            continue
        if not isinstance(items, list) or len(items) > 16:
            raise ValueError("processes는 16행 이하 목록이어야 해요")
        pids = set()
        for item in items:
            if not isinstance(item, dict) or set(item) != {"pid", "argv"}:
                raise ValueError("프로세스 행의 키가 맞지 않아요")
            pid, argv = item["pid"], item["argv"]
            if type(pid) is not int or not 1 <= pid <= 999999 or pid in pids:
                raise ValueError("PID 범위 또는 중복 오류예요")
            pids.add(pid)
            if not isinstance(argv, list) or not 1 <= len(argv) <= 8:
                raise ValueError("argv는 1~8개 문자열 목록이어야 해요")
            if any(not isinstance(arg, str) or not 1 <= len(arg) <= 160 or any(c in arg for c in "\x00\r\n") for arg in argv):
                raise ValueError("인수는 제어 문자 없는 160자 이하 문자열이어야 해요")
            if "\\" in argv[0] or not PurePosixPath(argv[0]).name:
                raise ValueError("argv[0]에 POSIX 끝 이름이 필요해요")
    return rows


def assess(row):
    if row["collection"] != "collected":
        return "해석 보류", "수집 상태 " + row["collection"]
    items = row["processes"]
    if not items:
        return "해석 보류", "가상 목록이 비었어요"
    matches = []
    for item in items:
        name = PurePosixPath(item["argv"][0]).name
        if name in TARGET_NAMES:
            matches.append(f"{name}@{item['pid']}")
    count = len(items)
    if matches:
        return "이름 후보", ", ".join(matches) + f"; 비교 행={count}"
    return "대상 이름 없음", f"비교 행={count}"


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 JSON 파일 하나를 지정해 주세요")
        rows = load_rows(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("가상 프로세스 이름 대조 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        status, detail = assess(row)
        print(f"{row['id']}: {status} | {detail}")
    print(f"가상 사례: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
