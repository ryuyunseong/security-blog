import argparse
import json
from pathlib import Path
import re
import sys


def validate(record):
    if not isinstance(record, dict):
        raise ValueError("각 항목은 객체여야 한다")
    if set(record) != {"name", "uid", "mode", "kind", "acl"}:
        raise ValueError("필드 이름 또는 필수 값 누락")
    if not isinstance(record["name"], str) or not record["name"].strip():
        raise ValueError("이름은 빈 문자열일 수 없다")
    if type(record["uid"]) is not int or record["uid"] < 0:
        raise ValueError("UID는 0 이상의 정수여야 한다")
    if not isinstance(record["mode"], str) or not re.fullmatch(r"[0-7]{4}", record["mode"]):
        raise ValueError("모드는 8진수 네 자리 문자열이어야 한다")
    if record["kind"] not in ("file", "symlink"):
        raise ValueError("파일 종류 오류")
    if record["acl"] not in ("none", "present", "unknown"):
        raise ValueError("ACL 상태 오류")


def review(record):
    if record["kind"] != "file":
        return None, ["링크 대상 조사"]
    mode = int(record["mode"], 8)
    if mode & 0o7000:
        return None, ["특수 비트 조사"]
    extra = mode & (~0o644 & 0o777)
    issues = []
    if record["uid"] != 0:
        issues.append("소유자 불일치")
    if extra:
        issues.append("허용 밖 권한")
    if record["acl"] != "none":
        issues.append("ACL 추가 조사")
    return extra, issues or ["소유자·일반 권한 조건 충족"]


def main():
    parser = argparse.ArgumentParser(description="가상 hosts 속성 JSON만 비교한다")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        records = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(records, list) or not records:
            raise ValueError("비어 있지 않은 배열이 필요하다")
        # 모든 입력을 검증한 뒤에 출력하므로 중간 성공 결과를 남기지 않는다.
        for record in records:
            validate(record)
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for record in records:
        extra, issues = review(record)
        bits = "비교 안 함" if extra is None else f"{extra:03o}"
        print(f"{record['name']}: UID={record['uid']}, 모드={record['mode']}, 추가 비트={bits}, {', '.join(issues)}")
    print(f"가상 자료 {len(records)}건 비교 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
