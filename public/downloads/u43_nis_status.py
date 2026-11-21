import json
import re
import sys
from pathlib import Path

STATES = {"on", "off", "error", "missing"}


def compare(nis, nisplus):
    if nis == "on":
        return "nis-active"
    if nis == "off":
        if nisplus == "on":
            return "plus-only"
        return "nis-inactive"
    return "need-nis-status"


def read_rows(path):
    with path.open("rb") as source:
        data = source.read(8193)
    if len(data) > 8192:
        raise ValueError("file exceeds 8192 bytes")
    records = json.loads(data.decode("utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("expected a nonempty list")

    seen = set()
    output = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {"case", "nis", "nisplus"}:
            raise ValueError("expected case, nis and nisplus")
        name, nis, nisplus = (record[k] for k in ("case", "nis", "nisplus"))
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z-]{0,29}", name):
            raise ValueError("invalid case name")
        if name in seen:
            raise ValueError("duplicate case name")
        if not all(isinstance(v, str) and v in STATES for v in (nis, nisplus)):
            raise ValueError(f"{name}: unexpected state")
        seen.add(name)
        output.append(f"{name} nis={nis} nisplus={nisplus} result={compare(nis, nisplus)}")
    return output


def main(args):
    if len(args) != 1:
        print("rows-emitted=0")
        print("입력 오류: JSON 파일 하나를 지정하세요.", file=sys.stderr)
        return 2
    try:
        rows = read_rows(Path(args[0]))
    except (OSError, ValueError, RecursionError) as error:
        print("rows-emitted=0")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
