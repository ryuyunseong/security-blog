import argparse
import os
from pathlib import Path
import stat
import sys


def file_kind(mode):
    for test, name in ((stat.S_ISREG, "file"), (stat.S_ISDIR, "dir"),
                       (stat.S_ISLNK, "link"), (stat.S_ISFIFO, "fifo"),
                       (stat.S_ISCHR, "char"), (stat.S_ISBLK, "block"),
                       (stat.S_ISSOCK, "socket")):
        if test(mode):
            return name
    return "other"


def collect(root):
    root = root.resolve(strict=True)
    if root.parent != Path("/tmp") or not root.name.startswith("u26-fixture-"):
        raise ValueError("준비기가 만든 /tmp 실습 폴더만 지정한다")
    if (root / ".u26-fixture").read_text(encoding="utf-8") != "synthetic-u26\n":
        raise ValueError("실습 폴더 표지가 맞지 않는다")
    rows = []

    def visit(folder):
        with os.scandir(folder) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                path = Path(entry.path)
                if path == root / ".u26-fixture":
                    continue
                relative = path.relative_to(root)
                kind = file_kind(entry.stat(follow_symlinks=False).st_mode)
                review = "검색 대상 아님"
                if kind == "file":
                    review = "예외 영역 검토" if relative.parts[0] in {"shm", "mqueue"} else "일반 파일 조사"
                rows.append((relative.as_posix(), kind, review))
                if kind == "dir":
                    visit(path)

    visit(root)
    return sorted(rows)


def main():
    parser = argparse.ArgumentParser(description="가상 dev 자료의 파일 종류를 분류한다")
    parser.add_argument("lab", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        print("이 실습은 Linux의 /tmp에서 실행한다", file=sys.stderr)
        return 2
    try:
        rows = collect(args.lab)
    except (OSError, ValueError, UnicodeError):
        print("수집 오류: 실습 경로·표지·읽기 권한을 살핀다", file=sys.stderr)
        return 2
    for name, kind, review in rows:
        print(f"{name}: {kind}, {review}")
    regular = sum(kind == "file" for _, kind, _ in rows)
    exceptions = sum(review == "예외 영역 검토" for _, _, review in rows)
    print(f"항목 {len(rows)}건, 일반 파일 {regular}건, 예외 영역 {exceptions}건")
    for label, mode in (("문자", stat.S_IFCHR | 0o600), ("블록", stat.S_IFBLK | 0o600)):
        print(f"메모리 모드 예시 {label}: {file_kind(mode)}, {stat.filemode(mode)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
