import re
import stat
import sys
from pathlib import Path


def describe(line, number):
    fields = line.split("|")
    if len(fields) != 2:
        raise ValueError(f"line {number}: expected state|mode")
    state, value = fields
    if state == "observed":
        if not re.fullmatch(r"0[0-7]{3}", value):
            raise ValueError(f"line {number}: expected four octal digits starting with 0")
        mode = int(value, 8)
        other_x = "set" if mode & stat.S_IXOTH else "clear"
    elif state in ("read-error", "not-collected"):
        if value != "-":
            raise ValueError(f"line {number}: mode must be - for {state}")
        other_x = "unknown"
    else:
        raise ValueError(f"line {number}: unknown collection state")
    return f"{number} state={state} mode={value} other-x={other_x}"


def main(args):
    if len(args) != 1:
        print("usage: u46_mode_record.py FILE", file=sys.stderr)
        return 2
    try:
        with Path(args[0]).open("rb") as source:
            data = source.read(4097)
        if len(data) > 4096:
            raise ValueError("input exceeds 4096 bytes")
        lines = data.decode("utf-8").splitlines()
        if not lines:
            raise ValueError("empty input")
        results = [describe(line, n) for n, line in enumerate(lines, 1)]
    except (OSError, ValueError) as error:
        print("records-emitted=0")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for result in results:
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
