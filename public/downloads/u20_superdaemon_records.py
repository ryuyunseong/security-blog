import argparse
import json
from pathlib import Path
import re
import sys


def validate(item):
    if not isinstance(item, dict) or set(item) != {"path", "kind", "uid", "mode"}:
        raise ValueError("필드는 path, kind, uid, mode여야 한다")
    if not isinstance(item["path"], str) or not item["path"].startswith("/"):
        raise ValueError("경로 표시는 /로 시작하는 문자열이어야 한다")
    if item["kind"] not in ("file", "directory", "missing", "symlink"):
        raise ValueError("종류가 올바르지 않다")
    if item["kind"] == "missing":
        if item["uid"] is not None or item["mode"] is not None:
            raise ValueError("미수집 항목의 UID와 모드는 null이어야 한다")
        return
    if type(item["uid"]) is not int or item["uid"] < 0:
        raise ValueError("UID는 0 이상의 정수여야 한다")
    if not isinstance(item["mode"], str) or not re.fullmatch(r"[0-7]{4}", item["mode"]):
        raise ValueError("모드는 8진수 네 자리 문자열이어야 한다")


def inspect(item):
    if item["kind"] == "missing":
        return "미수집", "설치·사용 여부와 실제 적용 경로 조사"
    if item["kind"] == "directory":
        return "대상 구분", "디렉터리는 파일의 0600 기준으로 판정하지 않음"
    if item["kind"] == "symlink":
        return "대상 조사", "링크가 가리키는 실제 파일 자료 필요"
    mode = int(item["mode"], 8)
    if mode & 0o7000:
        return "추가 조사", "특수 비트가 있어 일반 권한 비교를 보류"
    extra = mode & (~0o600 & 0o777)
    differences = []
    if item["uid"] != 0:
        differences.append("root 소유가 아님")
    if extra:
        differences.append(f"허용 밖 비트 {extra:03o}")
    return ("기준 차이", ", ".join(differences)) if differences else ("조건 충족", "UID 0, 허용 밖 비트 000")


def main():
    parser = argparse.ArgumentParser(description="명시한 가상 수집 자료만 읽는다")
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
        status, detail = inspect(item)
        print(f"{item['path']}: {status}, {detail}")
    print(f"가상 자료 {len(items)}건 비교 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
