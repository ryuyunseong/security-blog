import argparse
import json
import re
import sys
from pathlib import Path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키 중복")
        result[key] = value
    return result


def validate(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError("입력은 1~1000건의 목록이어야 함")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "source", "state", "value"}:
            raise ValueError("id, source, state, value 필드 필요")
        label = row["id"]
        if not isinstance(label, str) or not re.fullmatch(r"[a-z0-9-]{1,40}", label):
            raise ValueError("id 형식 오류")
        if label in seen:
            raise ValueError("id 중복")
        seen.add(label)
        if row["source"] not in ("config", "process"):
            raise ValueError("source는 config 또는 process")
        state = row["state"]
        if state not in ("available", "read_error", "missing", "not_collected"):
            raise ValueError("state 형식 오류")
        if state == "missing" and row["source"] != "config":
            raise ValueError("missing은 설정 파일 부재에만 사용")
        value = row["value"]
        if state == "available":
            if not isinstance(value, str) or not re.fullmatch(r"0[0-7]{3}", value):
                raise ValueError("수집값은 네 자리 8진수 문자열이어야 함")
        elif value is not None:
            raise ValueError("미확정 상태의 value는 null이어야 함")
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


def calculate(value):
    mask = int(value, 8)
    numeric = "이상" if mask >= 0o022 else "미만"
    missing = 0o022 & (0o777 ^ mask)
    allowed = 0o777 ^ mask
    return numeric, missing, 0o666 & allowed, 0o777 & allowed


def describe(row):
    label = row["id"]
    source = {"config": "설정", "process": "실행"}[row["source"]]
    state = row["state"]
    if state != "available":
        reason = {"read_error": "조회 오류", "missing": "설정 파일 부재",
                  "not_collected": "자료 미수집"}[state]
        return f"{label}: {reason}, 값 비교 보류"
    numeric, missing, file_mode, dir_mode = calculate(row["value"])
    return (f"{label}: {source}={row['value']}, 022 {numeric}, "
            f"쓰기 차단 누락={missing:04o}, 파일={file_mode:04o}, 디렉터리={dir_mode:04o}")


def self_test():
    expected = {
        "0000": ("미만", 0o022, 0o666, 0o777),
        "0021": ("미만", 0o002, 0o646, 0o756),
        "0022": ("이상", 0, 0o644, 0o755),
        "0027": ("이상", 0, 0o640, 0o750),
        "0031": ("이상", 0o002, 0o646, 0o746),
        "0077": ("이상", 0, 0o600, 0o700),
        "0111": ("이상", 0o022, 0o666, 0o666),
    }
    for value, result in expected.items():
        if calculate(value) != result:
            raise RuntimeError("계산 기대값 불일치")
    base = {"id": "sample", "source": "process", "state": "available", "value": "0022"}
    bad = [[], [base, base], [dict(base, extra=1)], [dict(base, id="../x")],
           [dict(base, source="unknown")], [dict(base, state="absent")],
           [dict(base, value=22)], [dict(base, value="022")],
           [dict(base, value="0088")], [dict(base, value="1022")],
           [dict(base, state="read_error")],
           [dict(base, state="missing", value=None)]]
    for rows in bad:
        try:
            validate(rows)
        except ValueError:
            continue
        raise RuntimeError("잘못된 입력을 허용함")
    print(f"계산 사례 {len(expected)}건 일치, 입력 거부 {len(bad)}건 일치")


def main():
    parser = argparse.ArgumentParser(description="가상 UMASK 수집값 비교")
    parser.add_argument("fixture", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        if args.fixture is not None:
            parser.error("--self-test에는 입력 파일을 지정하지 않음")
        self_test()
        return 0
    if args.fixture is None:
        parser.error("JSON 입력 파일 필요")
    try:
        rows = load_rows(args.fixture)
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        print(describe(row))
    print(f"가상 자료 {len(rows)}건 계산 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
