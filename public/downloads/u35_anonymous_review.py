import argparse
import json
from pathlib import Path
import re
import sys


STATES = {"collected", "absent", "query-error", "uncollected"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키 중복")
        result[key] = value
    return result


def load_cases(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(20001)
    if len(raw) > 20000:
        raise ValueError("입력 크기 제한 초과")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("입력은 1~30건의 목록이어야 합니다")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "collection", "text"}:
            raise ValueError("입력 필드 불일치")
        name = row["id"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name) or name in seen:
            raise ValueError("ID 형식 오류 또는 중복")
        seen.add(name)
        if not isinstance(row["collection"], str) or row["collection"] not in STATES:
            raise ValueError("수집 상태 오류")
        if row["collection"] == "collected":
            if not isinstance(row["text"], str) or len(row["text"]) > 2000:
                raise ValueError("수집한 설정 본문 오류")
        elif row["text"] is not None:
            raise ValueError("설정 자료가 없으면 text는 null이어야 합니다")
    return rows


def inspect_text(text):
    values, malformed = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        if not re.match(r"anonymous_enable\b", line.lstrip()):
            continue
        match = re.fullmatch(r"anonymous_enable=(YES|NO)", line)
        if match is None:
            malformed.append(number)
        else:
            values.append((number, match[1]))
    if malformed:
        return "보류", "대상 항목 형식 재검토: 행 " + ",".join(map(str, malformed))
    if len(values) != 1:
        return "보류", f"활성 대상 항목 {len(values)}개; 생략·중복 조사"
    number, value = values[0]
    status = "명시적 제한값" if value == "NO" else "검토 후보"
    return status, f"anonymous_enable={value}; 행 {number}"


def main():
    parser = argparse.ArgumentParser(description="가상 vsftpd 설정의 익명 로그인 항목 추출")
    parser.add_argument("fixture")
    args = parser.parse_args()
    try:
        rows = load_cases(args.fixture)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print("가상 설정 비교 미실행")
        if isinstance(exc, (json.JSONDecodeError, UnicodeError, RecursionError)):
            message = "JSON 구문·UTF-8 인코딩·중첩 깊이를 살펴보세요"
        elif isinstance(exc, OSError):
            message = "입력 파일의 경로·읽기 권한을 살펴보세요"
        else:
            message = str(exc)
        print("입력 오류: " + message, file=sys.stderr)
        return 2
    counts = {"명시적 제한값": 0, "검토 후보": 0, "보류": 0}
    for row in rows:
        if row["collection"] == "collected":
            status, reason = inspect_text(row["text"])
        else:
            status, reason = "보류", "설정 자료 " + row["collection"]
        counts[status] += 1
        print(f"{row['id']}: {status} ({reason})")
    print(f"가상 설정 {len(rows)}건: 명시적 제한값 {counts['명시적 제한값']}, 검토 후보 {counts['검토 후보']}, 보류 {counts['보류']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
