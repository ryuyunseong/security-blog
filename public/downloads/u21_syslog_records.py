import argparse
import json
from pathlib import Path
import re
import sys


def validate(item):
    if not isinstance(item, dict) or set(item) != {"path", "kind", "owner", "mode"}:
        raise ValueError("필드는 path, kind, owner, mode여야 한다")
    if not isinstance(item["path"], str) or not item["path"].startswith("/"):
        raise ValueError("경로 표시는 /로 시작하는 문자열이어야 한다")
    if item["kind"] not in ("file", "directory", "missing", "symlink"):
        raise ValueError("파일 종류가 올바르지 않다")
    if item["kind"] == "missing":
        if item["owner"] is not None or item["mode"] is not None:
            raise ValueError("미수집 항목의 소유자와 모드는 null이어야 한다")
        return
    if not isinstance(item["owner"], str) or not item["owner"].strip():
        raise ValueError("수집한 소유자 계정명이 필요하다")
    if not isinstance(item["mode"], str) or not re.fullmatch(r"[0-7]{4}", item["mode"]):
        raise ValueError("모드는 8진수 네 자리 문자열이어야 한다")


def compare(item):
    if item["kind"] == "missing":
        return "미수집", "로그 데몬과 실제 설정 경로 조사"
    if item["kind"] == "directory":
        return "대상 구분", "디렉터리에는 파일의 0640 기준을 적용하지 않음"
    if item["kind"] == "symlink":
        return "대상 조사", "링크 대상 파일의 소유자와 모드 필요"
    mode = int(item["mode"], 8)
    if mode & 0o7000:
        return "추가 조사", "특수 비트가 있어 일반 권한 비교를 보류"
    extra = mode & (~0o640 & 0o777)
    reasons = []
    if item["owner"] not in {"root", "bin", "sys"}:
        reasons.append("허용 소유자 목록 밖")
    if extra:
        reasons.append(f"허용 밖 비트 {extra:03o}")
    if reasons:
        return "기준 차이", ", ".join(reasons)
    return "조건 충족", f"소유자 {item['owner']}, 허용 밖 비트 000"


def main():
    parser = argparse.ArgumentParser(description="명시한 가상 로그 설정 자료만 비교한다")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        items = json.loads(args.input.read_text(encoding="utf-8"))
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
        status, detail = compare(item)
        print(f"{item['path']}: {status}, {detail}")
    print(f"가상 자료 {len(items)}건 비교 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
