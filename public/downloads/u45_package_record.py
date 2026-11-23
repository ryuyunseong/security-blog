import re
import sys
from pathlib import Path

REFERENCE = {"lab-a": "1.0-2", "lab-b": "1.0-3"}


def compare_record(line, number):
    parts = line.split("|")
    if len(parts) != 3:
        raise ValueError(f"line {number}: expected channel|state|installed")
    channel, state, installed = parts
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,23}", channel):
        raise ValueError(f"line {number}: invalid channel")
    reference = REFERENCE.get(channel)
    if state == "observed":
        if not re.fullmatch(r"[0-9][A-Za-z0-9.+:~-]{0,47}", installed):
            raise ValueError(f"line {number}: invalid version token")
        if reference is None:
            result = "no-reference"
        elif installed == reference:
            result = "match"
        else:
            result = "different"
    elif state in ("read-error", "not-collected"):
        if installed != "-":
            raise ValueError(f"line {number}: missing value must be -")
        result = state
    else:
        raise ValueError(f"line {number}: invalid collection state")
    return f"{number} {channel} installed={installed} reference={reference or '-'} {result}"


def main(args):
    if len(args) != 1:
        print("usage: u45_package_record.py FILE", file=sys.stderr)
        return 2
    try:
        with Path(args[0]).open("rb") as stream:
            data = stream.read(8193)
        if len(data) > 8192:
            raise ValueError("input exceeds 8192 bytes")
        lines = data.decode("utf-8").splitlines()
        if not lines:
            raise ValueError("empty input")
        output = [compare_record(line, i) for i, line in enumerate(lines, 1)]
    except (OSError, ValueError) as error:
        print("records-emitted=0")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for item in output:
        print(item)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
