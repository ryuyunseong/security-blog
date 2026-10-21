import sys
from bisect import bisect_right
from ipaddress import IPv4Address, IPv4Network


def parse_ip(text):
    address = IPv4Address(text)
    if str(address) != text:
        raise ValueError("IPv4 주소는 앞자리 0 없이 입력한다.")
    return int(address)


def parse_cidr(text):
    # 호스트 비트를 잘라내지 않고 잘못된 네트워크 주소를 거부한다.
    network = IPv4Network(text, strict=True)
    if str(network) != text:
        raise ValueError("CIDR은 네트워크 주소/접두사 길이로 입력한다.")
    return int(network.network_address), int(network.broadcast_address)


def build_index(cidrs):
    intervals = sorted(parse_cidr(cidr) for cidr in cidrs)
    merged = []
    for left, right in intervals:
        # 중첩뿐 아니라 빈 주소가 없는 인접 구간도 합친다.
        if merged and left <= merged[-1][1] + 1:
            old_left, old_right = merged[-1]
            merged[-1] = (old_left, max(old_right, right))
        else:
            merged.append((left, right))
    starts = [left for left, _ in merged]
    return starts, merged


def contains(index, address):
    starts, merged = index
    position = bisect_right(starts, address) - 1
    return position >= 0 and address <= merged[position][1]


def read_token(stream):
    fields = stream.readline().split()
    if len(fields) != 1:
        raise ValueError("각 데이터 줄에는 값 하나가 필요하다.")
    return fields[0]


def solve(source, destination):
    header = source.readline().split()
    if len(header) != 2:
        raise ValueError("첫 줄에는 N과 Q가 필요하다.")
    n, q = map(int, header)
    if not (0 <= n <= 200_000 and 0 <= q <= 200_000):
        raise ValueError("N과 Q는 0부터 200000까지여야 한다.")
    index = build_index(read_token(source) for _ in range(n))
    for _ in range(q):
        address = parse_ip(read_token(source))
        destination.write("ALLOW\n" if contains(index, address) else "DENY\n")
    if any(line.strip() for line in source):
        raise ValueError("입력 개수보다 데이터가 많다.")


if __name__ == "__main__":
    try:
        solve(sys.stdin, sys.stdout)
    except ValueError as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        sys.exit(2)
