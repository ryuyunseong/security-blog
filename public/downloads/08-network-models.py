import argparse
from ipaddress import IPv4Address, IPv4Network
import struct
import sys


ROUTES = [
    (IPv4Network("0.0.0.0/0"), IPv4Address("192.0.2.1")),
    (IPv4Network("192.0.2.0/24"), None),
    (IPv4Network("198.51.100.0/24"), IPv4Address("192.0.2.254")),
]


def route_for(destination):
    address = IPv4Address(destination)
    candidates = [(network, gateway) for network, gateway in ROUTES if address in network]
    if not candidates:
        raise ValueError("일치하는 가상 경로가 없다")
    network, gateway = max(candidates, key=lambda item: item[0].prefixlen)
    return str(network), str(gateway if gateway is not None else address)


def udp_fields(packet):
    if len(packet) < 8:
        raise ValueError("UDP 헤더보다 짧다")
    source, destination, length, checksum = struct.unpack("!HHHH", packet[:8])
    if length < 8 or length != len(packet):
        raise ValueError("UDP 길이와 받은 바이트 수가 다르다")
    return source, destination, length, packet[8:]


def main():
    parser = argparse.ArgumentParser(description="네트워크 연결 없이 경로와 헤더를 계산한다")
    parser.add_argument("example", choices=["routes", "udp"])
    args = parser.parse_args()
    try:
        if args.example == "routes":
            for address in ["192.0.2.20", "198.51.100.8", "203.0.113.9"]:
                network, next_hop = route_for(address)
                print(f"{address}: 경로={network}, 다음 홉={next_hop}")
        else:
            packet = struct.pack("!HHHH", 53000, 53, 12, 0) + b"ABCD"
            source, destination, length, payload = udp_fields(packet)
            print(f"UDP: 출발지={source}, 목적지={destination}, 전체={length}, 데이터={len(payload)}")
            print(f"데이터 바이트: {payload.hex()}")
    except ValueError as error:
        print(f"계산 오류: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
