import argparse
import json
from pathlib import Path
import re
import stat
import sys


def load_cases(text):
    rows = json.loads(text)
    if not isinstance(rows, list) or not rows:
        raise ValueError("비어 있지 않은 배열이 필요하다")
    names = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"case", "owner", "kind", "mode"}:
            raise ValueError("case, owner, kind, mode 필드가 필요하다")
        if any(not isinstance(row[key], str) or not row[key] for key in row):
            raise ValueError("모든 필드는 비어 있지 않은 문자열이어야 한다")
        if row["case"] in names or row["kind"] not in {"file", "dir"}:
            raise ValueError("사례 이름 중복 또는 파일 종류 오류")
        if not re.fullmatch(r"[0-7]{4}", row["mode"]):
            raise ValueError("mode는 네 자리 8진수여야 한다")
        names.add(row["case"])
    return rows


def classify(row):
    mode = int(row["mode"], 8)
    flags = [name for bit, name in [(stat.S_ISUID, "SUID"), (stat.S_ISGID, "SGID"), (stat.S_ISVTX, "Sticky")]
             if mode & bit]
    selected = row["owner"] == "root" and row["kind"] == "file" and bool(mode & 0o6000)
    file_type = stat.S_IFREG if row["kind"] == "file" else stat.S_IFDIR
    return flags, selected, stat.filemode(file_type | mode)


def main():
    parser = argparse.ArgumentParser(description="가상 수집 자료의 특수 비트만 분류한다")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        rows = load_cases(args.file.read_text(encoding="utf-8"))
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    selected_count = 0
    for row in rows:
        flags, selected, display = classify(row)
        selected_count += selected
        print(f"{row['case']}: {','.join(flags) or '없음'}; 검색 조건={'예' if selected else '아니요'}; {display}")
    print(f"가상 자료 {len(rows)}건, root 일반 파일의 SUID/SGID 검색 조건 {selected_count}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
