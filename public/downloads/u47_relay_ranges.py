from ipaddress import IPv4Network
from pathlib import Path
import sys


APPROVED = IPv4Network("192.0.2.0/28")


def describe(row, number):
    fields = row.split("|")
    if len(fields) != 2:
        raise ValueError(f"line {number}: expected two fields")
    state, value = fields
    if state in ("read-error", "not-collected") and value == "-":
        return f"{number} state={state} outside=unknown"
    if state != "observed":
        raise ValueError(f"line {number}: invalid state or value")
    try:
        network = IPv4Network(value, strict=True)
        if str(network) != value:
            raise ValueError
    except ValueError:
        raise ValueError(f"line {number}: expected canonical IPv4 CIDR") from None

    first = max(network.network_address, APPROVED.network_address)
    last = min(network.broadcast_address, APPROVED.broadcast_address)
    overlap = max(0, int(last) - int(first) + 1)
    outside = network.num_addresses - overlap
    return f"{number} network={network} listed={network.num_addresses} outside={outside}"


def main(args):
    try:
        if len(args) != 1:
            raise ValueError("expected one input file")
        with Path(args[0]).open("rb") as stream:
            data = stream.read(4097)
        if len(data) > 4096:
            raise ValueError("input exceeds 4096 bytes")
        rows = data.decode("utf-8").splitlines()
        if not rows:
            raise ValueError("empty input")
        results = [describe(row, n) for n, row in enumerate(rows, start=1)]
    except (OSError, UnicodeError):
        print("입력 오류: cannot read UTF-8 file", file=sys.stderr)
    except ValueError as error:
        print(f"입력 오류: {error}", file=sys.stderr)
    else:
        print(*results, sep="\n")
        return 0
    print("records-emitted=0")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
