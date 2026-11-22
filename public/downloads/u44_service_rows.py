import json
import sys
from pathlib import Path

SERVICES = ("tftp", "talk", "ntalk")
STATES = ("active", "inactive", "query-error")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def summarize(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    observed = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError("expected [service, state]")
        service, state = row
        if service not in SERVICES or state not in STATES:
            raise ValueError("unknown service or state")
        if service in observed:
            raise ValueError(f"duplicate service: {service}")
        observed[service] = state
    fields = [f"{name}={observed.get(name, 'no-row')}" for name in SERVICES]
    return " ".join(fields)


def main(args):
    if len(args) != 1:
        print("usage: u44_service_rows.py FILE", file=sys.stderr)
        return 2
    try:
        with Path(args[0]).open("rb") as stream:
            raw = stream.read(8193)
        if len(raw) > 8192:
            raise ValueError("input exceeds 8192 bytes")
        samples = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys)
        if not isinstance(samples, dict) or not samples:
            raise ValueError("expected named samples")
        lines = []
        for label, rows in samples.items():
            if not label.isascii() or not label.isalpha() or len(label) > 20:
                raise ValueError("invalid sample name")
            lines.append(f"{label}: {summarize(rows)}")
    except (OSError, ValueError, RecursionError) as error:
        print("samples-emitted=0")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
