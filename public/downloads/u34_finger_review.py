import argparse
import json
from pathlib import Path
import re
import sys


STATES = {"collected", "absent", "query-error", "uncollected"}
RUNTIME = {"listening", "not-listening", "unknown", "query-error", "uncollected"}
SETTINGS = {"xinetd": {"yes", "no"}, "inetd": {"commented", "active"}}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키 중복")
        result[key] = value
    return result


def load_cases(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(100001)
    if len(raw) > 100000:
        raise ValueError("입력 크기 제한 초과")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("입력은 1~100건의 목록이어야 합니다")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "manager", "collection", "setting", "runtime"}:
            raise ValueError("입력 필드 불일치")
        name = row["id"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name) or name in seen:
            raise ValueError("ID 형식 오류 또는 중복")
        seen.add(name)
        if not isinstance(row["manager"], str) or row["manager"] not in SETTINGS:
            raise ValueError("지원하지 않는 관리 방식")
        if not isinstance(row["collection"], str) or row["collection"] not in STATES:
            raise ValueError("수집 상태 오류")
        if not isinstance(row["runtime"], str) or row["runtime"] not in RUNTIME:
            raise ValueError("실행 관찰 상태 오류")
        if row["collection"] == "collected":
            if not isinstance(row["setting"], str) or row["setting"] not in SETTINGS[row["manager"]]:
                raise ValueError("수집한 설정값 오류")
        elif row["setting"] is not None:
            raise ValueError("설정 자료가 없으면 setting은 null이어야 합니다")
    return rows


def review(row):
    collected = row["collection"] == "collected"
    stopped = collected and row["setting"] in {"yes", "commented"}
    if row["runtime"] == "listening":
        detail = "Finger 수신 가정"
        if stopped:
            detail += "; 중지 설정과 실행 자료 불일치"
        elif not collected:
            detail += "; 설정 자료 " + row["collection"]
        return "검토 후보", detail
    if not collected:
        return "보류", "설정 자료 " + row["collection"]
    if not stopped:
        return "검토 후보", "실행 허용 설정; 실행 자료 " + row["runtime"]
    if row["runtime"] == "not-listening":
        return "입력 조건 일치", "중지 설정과 수신 없음 가정"
    return "보류", "중지 설정; 실행 자료 " + row["runtime"]


def main():
    parser = argparse.ArgumentParser(description="가상 Finger 설정·실행 자료의 대조")
    parser.add_argument("fixture")
    args = parser.parse_args()
    try:
        rows = load_cases(args.fixture)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print("가상 자료 분류 미실행")
        if isinstance(exc, (json.JSONDecodeError, UnicodeError, RecursionError)):
            message = "JSON 구문·UTF-8 인코딩·중첩 깊이를 살펴보세요"
        elif isinstance(exc, OSError):
            message = "입력 파일의 경로·읽기 권한을 살펴보세요"
        else:
            message = str(exc)
        print("입력 오류: " + message, file=sys.stderr)
        return 2
    counts = {"입력 조건 일치": 0, "검토 후보": 0, "보류": 0}
    for row in rows:
        status, reason = review(row)
        counts[status] += 1
        print(f"{row['id']}: {status} ({reason})")
    print(f"가상 자료 {len(rows)}건: 입력 조건 일치 {counts['입력 조건 일치']}, 검토 후보 {counts['검토 후보']}, 보류 {counts['보류']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
