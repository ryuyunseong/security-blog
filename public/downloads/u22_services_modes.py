import argparse
import json
from pathlib import Path
import re
import sys


def validate(item):
    if not isinstance(item, dict) or set(item) != {"case", "owner", "mode"}:
        raise ValueError("필드는 case, owner, mode여야 한다")
    for field in ("case", "owner"):
        if not isinstance(item[field], str) or not item[field].strip():
            raise ValueError(f"{field} 문자열이 필요하다")
    if not isinstance(item["mode"], str) or not re.fullmatch(r"[0-7]{4}", item["mode"]):
        raise ValueError("모드는 8진수 네 자리 문자열이어야 한다")


def compare(item):
    mode = int(item["mode"], 8)
    if mode & 0o7000:
        return "추가 조사", "특수 비트가 있어 일반 권한 비교를 보류"
    extra = mode & (~0o644 & 0o777)
    differences = []
    if item["owner"] not in {"root", "bin", "sys"}:
        differences.append("허용 소유자 목록 밖")
    if extra:
        differences.append(f"허용 밖 비트 {extra:03o}")
    return ("기준 차이", ", ".join(differences)) if differences else ("조건 충족", "허용 밖 비트 000")


def main():
    parser = argparse.ArgumentParser(description="가정한 services 일반 파일의 소유자와 모드를 비교한다")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        items = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(items, list) or not items:
            raise ValueError("비어 있지 않은 배열이 필요하다")
        for item in items:
            validate(item)
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for item in items:
        state, detail = compare(item)
        print(f"{item['case']}: {state}, {detail}")
    print(f"일반 파일 가상 자료 {len(items)}건 비교 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
