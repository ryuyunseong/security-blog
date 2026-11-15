import json
import re
import sys
from pathlib import Path

TARGETS = {"echo", "discard", "daytime", "chargen"}
SOCKETS = {"tcp": "stream", "udp": "dgram"}
STATES = {"collected", "absent", "query-error", "uncollected"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키가 중복됐어요")
        result[key] = value
    return result


def load_cases(path):
    with path.open("rb") as source:
        raw = source.read(20001)
    if len(raw) > 20000:
        raise ValueError("입력은 20000바이트 이하여야 해요")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("사례 목록은 1~30건이어야 해요")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "collection", "text"}:
            raise ValueError("각 행에는 id, collection, text만 필요해요")
        case_id, state, text = row["id"], row["collection"], row["text"]
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9-]{1,32}", case_id):
            raise ValueError("id 형식이 잘못됐어요")
        if case_id in ids:
            raise ValueError("id가 중복됐어요")
        ids.add(case_id)
        if not isinstance(state, str) or state not in STATES:
            raise ValueError("지원하지 않는 수집 상태예요")
        if state == "collected":
            if not isinstance(text, str) or len(text) > 2000 or "\0" in text:
                raise ValueError("collected의 text는 NUL 없는 2000자 이하 문자열이어야 해요")
        elif text is not None:
            raise ValueError("수집하지 않은 text는 null이어야 해요")
    return rows


def inspect_text(text):
    active, comments, issues, seen = [], [], [], set()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        commented = line.startswith("#")
        fields = (line[1:].strip() if commented else line).split()
        if not fields or fields[0] not in TARGETS:
            continue
        if (len(fields) != 6 or fields[2] not in SOCKETS
                or fields[1] != SOCKETS.get(fields[2])
                or fields[3] not in {"wait", "nowait"}
                or fields[4:] != ["root", "internal"]):
            issues.append(f"행 {number}: 지원 범위 밖 대상 행")
            continue
        pair = f"{fields[0]}/{fields[2]}"
        if commented:
            comments.append(f"{pair}@{number}")
        else:
            if pair in seen:
                issues.append(f"행 {number}: 활성 {pair} 중복")
            seen.add(pair)
            active.append(f"{pair}@{number}")
    if issues:
        return "해석 보류", "; ".join(issues)
    detail = f"활성 {', '.join(active) or '없음'}; 주석 {', '.join(comments) or '없음'}"
    return ("활성 설정 후보" if active else "활성 행 없음"), detail


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 JSON 파일 하나를 지정해 주세요")
        rows = load_cases(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("가상 설정 비교 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    counts = {"활성 설정 후보": 0, "활성 행 없음": 0, "해석 보류": 0}
    for row in rows:
        if row["collection"] == "collected":
            status, detail = inspect_text(row["text"])
        else:
            status, detail = "해석 보류", f"수집 상태 {row['collection']}"
        counts[status] += 1
        print(f"{row['id']}: {status} | {detail}")
    print("사례 합계: " + ", ".join(f"{name} {count}" for name, count in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
