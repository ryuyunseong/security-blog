import argparse
from pathlib import Path
import sys


TARGETS = {"shell": ("rsh", 514), "login": ("rlogin", 513),
           "exec": ("rexec", 512)}
STATES = ("collected", "absent", "query-error", "uncollected")


def read_rows(path):
    with path.open("rb") as stream:
        raw = stream.read(20001)
    if len(raw) > 20000:
        raise ValueError("입력 크기 상한")
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if len(lines) > 200:
        raise ValueError("입력 행 수 상한")
    rows = {name: [] for name in (*TARGETS, "rsync")}
    for number, line in enumerate(lines, 1):
        value = line.strip()
        if not value:
            continue
        commented = value.startswith("#")
        fields = value.removeprefix("#").strip().split()
        if commented and (not fields or fields[0] not in rows):
            continue
        if (len(fields) < 7 or fields[0] not in rows
                or fields[1] != "stream"
                or fields[2] not in ("tcp", "tcp4", "tcp6")
                or fields[3] != "nowait" or fields[4] != "root"
                or not fields[5].startswith("/")):
            raise ValueError("가상 입력 형식")
        rows[fields[0]].append((number, commented, fields[5]))
    return rows


def describe(rows):
    active_count = 0
    comment_count = 0
    output = []
    for service, (command, port) in TARGETS.items():
        active = [row for row in rows[service] if not row[1]]
        comments = [row for row in rows[service] if row[1]]
        if active:
            active_count += 1
            details = ", ".join(f"{n}행 {server}" for n, _, server in active)
            output.append(f"{service} ({command}, TCP {port}): 활성 행 후보 | {details}")
        elif comments:
            comment_count += 1
            numbers = ",".join(str(row[0]) for row in comments)
            output.append(f"{service} ({command}, TCP {port}): 주석 행만 있음 | {numbers}행")
        else:
            output.append(f"{service} ({command}, TCP {port}): 대상 행 없음, 보류")
    separate = [row for row in rows["rsync"] if not row[1]]
    if separate:
        numbers = ",".join(str(row[0]) for row in separate)
        output.append(f"rsync: 별도 조사 | {numbers}행, 전송 방식과 실제 사용 조사")
    output.append(f"파일 내 서비스 수: 활성 후보 {active_count}, 주석만 {comment_count}, "
                  f"별도 조사 {int(bool(separate))}")
    return output


def main():
    parser = argparse.ArgumentParser(description="가상 inetd 입력의 세 서비스 행 비교")
    parser.add_argument("--collection", choices=STATES, required=True)
    parser.add_argument("fixture", type=Path, nargs="?")
    args = parser.parse_args()
    if args.collection != "collected":
        if args.fixture is not None:
            parser.error("미수집 상태에는 입력 파일을 지정하지 않아요")
        print(f"보류: {args.collection}, 설정 본문 비교 미실행")
        return 0
    if args.fixture is None:
        parser.error("collected에는 가상 입력 파일이 필요해요")
    try:
        rows = read_rows(args.fixture)
        output = describe(rows)
    except (OSError, UnicodeError, ValueError):
        print("가상 설정 비교 미실행")
        print("입력 오류: UTF-8, 파일 접근, 크기 또는 지원 형식을 살펴보세요", file=sys.stderr)
        return 2
    print("\n".join(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
