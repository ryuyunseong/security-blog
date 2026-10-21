def endpoints(rows):
    result = set()
    for protocol, port in rows:
        if protocol not in {"tcp", "udp"}:
            raise ValueError("프로토콜은 tcp 또는 udp여야 함")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("포트는 1~65535 정수여야 함")
        result.add((protocol, port))
    return result


services = endpoints([("tcp", 443), ("tcp", 8443), ("tcp", 53), ("udp", 53)])
selected = endpoints([("tcp", 22), ("tcp", 443), ("udp", 53)])
missing = services - selected
assert missing == {("tcp", 53), ("tcp", 8443)}
assert ("udp", 53) in selected
assert ("tcp", 53) not in selected
assert endpoints([("tcp", 443), ("tcp", 443)]) == {("tcp", 443)}
for invalid in [[("icmp", 53)], [("tcp", 0)], [("udp", 65536)], [("tcp", True)]]:
    try:
        endpoints(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("잘못된 프로토콜·포트를 거부해야 함")

for protocol, port in sorted(services):
    scope = "선택 목록에 포함" if (protocol, port) in selected else "선택 목록 밖"
    print(f"{protocol}/{port}: {scope}")
print("목록에 빠진 조합:", ", ".join(f"{p}/{n}" for p, n in sorted(missing)))
revised = selected | missing
assert services <= revised
assert selected == endpoints([("tcp", 22), ("tcp", 443), ("udp", 53)])
print("가상 목록 보완 후 빠진 조합 수:", len(services - revised))
