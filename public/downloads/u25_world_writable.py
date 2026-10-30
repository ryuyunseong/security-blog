import argparse
import os
from pathlib import Path
import stat
import sys


def collect(root):
    root = root.resolve(strict=True)
    if root.parent != Path("/tmp") or not root.name.startswith("u25-fixture-"):
        raise ValueError("준비기가 만든 /tmp 실습 폴더만 지정한다")
    if (root / ".u25-fixture").read_text(encoding="utf-8") != "synthetic-u25\n":
        raise ValueError("실습 폴더 표지가 맞지 않는다")
    rows = []
    with os.scandir(root) as entries:
        for entry in sorted(entries, key=lambda item: item.name):
            if entry.name == ".u25-fixture":
                continue
            info = entry.stat(follow_symlinks=False)
            kind = "file" if stat.S_ISREG(info.st_mode) else "dir" if stat.S_ISDIR(info.st_mode) else "link" if stat.S_ISLNK(info.st_mode) else "other"
            mode = stat.S_IMODE(info.st_mode)
            other_write = bool(mode & stat.S_IWOTH)
            candidate = kind == "file" and other_write
            rows.append((entry.name, kind, mode, other_write, candidate))
    return rows


def main():
    parser = argparse.ArgumentParser(description="격리 실습 폴더의 일반 파일 쓰기 비트를 수집한다")
    parser.add_argument("lab", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        print("이 실습은 Linux의 /tmp에서 실행한다", file=sys.stderr)
        return 2
    try:
        rows = collect(args.lab)
    except (OSError, ValueError, UnicodeError):
        print("수집 오류: 준비기가 만든 폴더와 표지를 살핀다", file=sys.stderr)
        return 2
    for name, kind, mode, other_write, candidate in rows:
        print(f"{name}: {kind}, {mode:04o}, other 쓰기={'있음' if other_write else '없음'}, 일반 파일 후보={'예' if candidate else '아니요'}")
    count = sum(row[4] for row in rows)
    print(f"항목 {len(rows)}건, 일반 파일 후보 {count}건 수집 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
