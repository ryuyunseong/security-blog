---
title: "CIDR 허용 목록에서 IP 찾기: 구간 병합과 이진 탐색"
description: "IPv4 CIDR을 정수 구간으로 병합한 뒤 이진 탐색으로 허용 목록 포함 여부를 계산합니다."
date: "2026-10-11T16:01:39+09:00"
updated: "2026-10-16T00:00:00+09:00"
category: "infrastructure"
tags: ["Python", "알고리즘", "CIDR"]
draft: false
example: false
sourceUrl: "https://neoflux.tistory.com/40"
migrated: "2026-10-16"
---

CIDR 대역과 조회 IP가 많아지면 목록 전체를 반복해서 비교하는 비용이 커진다. IPv4 주소를 정수 구간으로 바꾸고 겹치는 범위를 합치면 조회마다 후보 구간 하나만 확인할 수 있다.

직접 구성한 코딩 테스트 문제다. 정렬·구간 병합·이진 탐색으로 포함 여부를 계산하며, 실제 네트워크 요청이나 방화벽 설정은 변경하지 않는다.

## 문제와 입력 규칙

허용 목록에 IPv4 CIDR이 N개 등록되어 있고, 조회할 IPv4 주소가 Q개 주어진다. 각 주소가 하나 이상의 CIDR에 포함되면 ALLOW, 어디에도 포함되지 않으면 DENY를 출력한다. 목록의 순서나 같은 CIDR의 중복 등록은 결과에 영향을 주지 않는다.

```text
N Q
CIDR 1
...
CIDR N
조회 IP 1
...
조회 IP Q
```
첫 줄에는 N과 Q를 입력하고, 이후에는 한 줄에 값 하나를 입력한다. 줄 앞뒤의 공백은 허용한다. CIDR 목록은 조회 전에 고정되며 처리 도중에는 바뀌지 않는다.

| 항목 | 조건 |
| --- | --- |
| N, Q | 각각 0 이상 200,000 이하 |
| IPv4 주소 | 0부터 255까지의 십진수 네 부분을 점으로 연결. 0 자체를 제외한 앞자리 0은 허용하지 않음 |
| CIDR | 192.0.2.0/24처럼 네트워크 주소와 0부터 32까지의 접두사 길이 사용 |
| 허용하지 않는 표기 | /024, 점으로 쓴 넷마스크, 접두사 생략, IPv6 |
| 호스트 비트 | 모두 0이어야 함. 192.0.2.1/24는 자동 보정하지 않고 입력 오류로 처리 |
| /0 | 0.0.0.0/0만 올바른 입력이며 IPv4 전체를 포함 |
| /32 | 지정한 주소 하나만 포함 |

네트워크 주소와 브로드캐스트 주소도 포함한다. 예를 들어 192.0.2.0/24에는 192.0.2.0과 192.0.2.255가 모두 들어간다. 사용 가능한 호스트 주소만 찾는 문제가 아니므로 hosts()로 주소 목록을 만들지 않는다.

결과는 조회 입력 순서대로 한 줄씩 출력한다. 같은 주소가 반복되어도 매번 출력하며, N이 0이면 모든 조회가 DENY, Q가 0이면 출력이 없다. 입력 끝의 빈 줄은 무시하되, 정해진 개수를 넘는 데이터는 오류로 처리한다.

잘못된 입력은 표준 오류에 메시지를 남기고 종료 코드 2로 끝낸다. 조회 도중 오류를 발견하면 이미 출력한 결과는 남을 수 있다.

## 중첩·인접 대역이 섞인 예제

두 /25 대역과 그 안에 포함된 /26 대역, 별도의 /32 주소를 함께 넣어보자.

예제 입력:

```text
4 7
192.0.2.0/25
192.0.2.128/25
192.0.2.64/26
198.51.100.10/32
192.0.1.255
192.0.2.0
192.0.2.127
192.0.2.255
192.0.3.0
198.51.100.10
198.51.100.11
```
예제 출력:

```text
DENY
ALLOW
ALLOW
ALLOW
DENY
ALLOW
DENY
```
192.0.2.0/25와 192.0.2.128/25 사이에는 빠진 주소가 없다. 두 대역을 합치면 192.0.2.0부터 192.0.2.255까지 하나의 연속 구간이 된다. 그 안에 있는 192.0.2.64/26은 허용 범위를 늘리지 않는다. 198.51.100.10/32는 주소 하나만 별도로 남는다.

## IPv4 주소를 정수 구간으로 바꾼다

가장 단순한 풀이는 조회 주소마다 모든 CIDR을 순회하는 것이다. N개 대역과 Q개 주소를 비교하므로 시간 복잡도는 O(NQ)다. N과 Q가 각각 200,000이면 최대 400억 번의 포함 검사가 필요하다. 작은 입력의 기준 답안을 만들 때는 쓸 수 있지만, 최대 입력을 처리할 풀이로는 적합하지 않다.

CIDR 안의 모든 주소를 집합에 넣는 방법도 피해야 한다. /0 하나에 주소가 2³²개 들어가므로, 대역의 개수가 작아도 주소를 전부 펼치는 비용이 크다.

IPv4 주소 a.b.c.d는 a×2²⁴ + b×2¹⁶ + c×2⁸ + d로 나타낼 수 있다. 값의 범위는 0부터 2³²−1까지이며, 주소의 크기 순서를 그대로 보존한다. 문자열을 사전순으로 정렬하는 것과는 다르다.

접두사 길이가 p인 CIDR에는 2^(32−p)개의 주소가 연속해서 들어간다. 시작 주소가 L이면 끝 주소는 L + 2^(32−p) − 1이다. 구현에서는 IPv4Network의 network_address와 broadcast_address를 정수로 바꿔 양 끝을 포함하는 닫힌 구간 [L, R]을 만든다.

## 정렬만으로는 부족하다

시작점만 정렬한 뒤 이진 탐색하면 중첩 대역에서 틀릴 수 있다. 허용 목록에 192.0.2.0/24와 192.0.2.64/26이 있고, 조회 주소가 192.0.2.200이라고 해보자.

조회 주소 이하의 시작점 중 가장 오른쪽에 있는 값은 192.0.2.64다. 그 /26 구간만 검사하면 DENY가 나오지만, 조회 주소는 앞의 /24에 포함되므로 정답은 ALLOW다. 후보 하나로 판단하려면 중첩을 먼저 제거해야 한다.

각 구간을 시작점 순으로 정렬하고, 현재 구간의 시작점이 마지막 병합 구간의 끝점에 1을 더한 값 이하이면 두 구간을 합친다. 겹치는 경우와 빈 주소가 없는 인접 구간을 함께 처리하는 조건이다. 끝점은 두 구간 중 더 큰 값으로 갱신하고, 조건을 만족하지 않으면 새 구간을 추가한다.

병합 결과가 항상 하나의 CIDR로 표현되는 것은 아니다. 예를 들어 주소 세 개가 연속된 구간은 CIDR 하나로 나타낼 수 없다. 여기서는 주소 포함 여부만 필요하므로 정수 구간으로 유지하면 된다.

병합이 끝나면 구간은 서로 겹치지 않고, 시작점과 끝점이 모두 증가한다. 이제 조회 주소 x 이하의 시작점 중 가장 오른쪽 값을 찾는다.

```text
position = bisect_right(starts, x) - 1
```
위치가 음수이면 x 이하에서 시작하는 구간이 없다. 후보가 있으면 x가 그 구간의 끝점 이하인지 확인한다. 더 앞선 구간은 후보 시작점보다 먼저 끝나고, 더 뒤의 구간은 x보다 뒤에서 시작하므로 다른 구간을 검사할 필요가 없다.

이 구현에서 bisect_right를 쓰는 이유는 시작점과 정확히 같은 주소도 후보 구간에 포함하기 위해서다. bisect_left(starts, x) - 1을 사용하면 일치하는 시작점의 바로 앞 구간을 선택하게 된다.

병합 후 구간 수를 M이라 하면 정상 입력을 처리하는 비용은 다음과 같다.

| 처리 | 복잡도 |
| --- | --- |
| CIDR 변환·정렬·병합 | O(N log(N+1)) |
| 주소 하나 조회 | O(log(M+2)) |
| 전체 처리 | O(1 + N log(N+1) + Q log(M+2)) |
| 추가 메모리 | O(N+1) |

조회 주소와 결과는 한 줄씩 처리하므로 Q개를 모두 저장하지 않는다. 빈 허용 목록을 조회할 때도 입력과 출력에는 상수 시간이 든다.

## Python 구현

아래 코드를 solution.py로 저장한다. Python 3의 표준 라이브러리만 사용한다.

```python
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
```
parse_ip()는 조회 주소를 정수로 바꾼다. parse_cidr()는 strict=True로 호스트 비트가 남은 네트워크 주소를 거부하고, 양 끝 주소를 반환한다. 정규화된 문자열을 원문과 비교해 접두사 생략이나 넷마스크 표기처럼 문제에서 허용하지 않은 형식도 걸러낸다.

build_index()는 정렬과 병합을 마친 뒤 시작점 배열을 만든다. contains()는 검증된 정수 주소를 받아 이진 탐색한다. solve()는 줄 형식과 입력 개수를 확인하며 결과를 순서대로 출력한다. CIDR 목록은 첫 조회 전에 모두 검증하므로 목록에 오류가 있으면 조회 결과를 출력하기 전에 실패한다.

예제 입력을 input.txt에 저장한 뒤 실행한다.

```bash
python3 solution.py < input.txt
```
## 경계 주소와 기준 풀이로 확인한다

범위 조회는 시작점과 끝점, 그 바로 바깥에서 오류가 드러나기 쉽다. 빈 목록, /0, /32, 중복 대역, 포함 관계와 인접 구간을 확인한다. 특히 두 구간 사이에 주소 하나만 빠져 있으면 병합하지 않아야 한다.

아래 코드를 solution.py와 같은 폴더의 test_solution.py에 저장한다. 무작위 비교에서는 고정된 시드로 입력을 재현한다. 일부 입력은 192.0.2.0/24와 양쪽 경계 주소를 모두 비교하고, 나머지는 IPv4 전체 범위에서 조회 주소를 고른다. 기준 답은 각 CIDR에 ipaddress의 포함 연산을 차례로 적용해 구한다.

```python
import io
import random
import unittest
from ipaddress import IPv4Address, IPv4Network
from solution import build_index, contains, parse_cidr, parse_ip, solve


class AllowlistTests(unittest.TestCase):
    def test_boundaries(self):
        cases = [
            ([], "0.0.0.0", False),
            (["192.0.2.0/24", "192.0.2.64/26"], "192.0.2.200", True),
            (["0.0.0.0/0"], "0.0.0.0", True),
            (["0.0.0.0/0"], "255.255.255.255", True),
            (["255.255.255.255/32"], "255.255.255.254", False),
            (["255.255.255.255/32"], "255.255.255.255", True),
            (["192.0.2.0/24"], "192.0.1.255", False),
            (["192.0.2.0/24"], "192.0.2.0", True),
            (["192.0.2.0/24"], "192.0.2.255", True),
            (["192.0.2.0/24"], "192.0.3.0", False),
        ]
        for cidrs, address, expected in cases:
            with self.subTest(cidrs=cidrs, address=address):
                self.assertEqual(contains(build_index(cidrs), parse_ip(address)), expected)

    def test_merge(self):
        cidrs = ["192.0.2.128/25", "192.0.2.0/25", "192.0.2.64/26",
                 "192.0.2.0/25", "192.0.3.1/32"]
        starts, merged = build_index(cidrs)
        self.assertEqual(merged, [(parse_ip("192.0.2.0"), parse_ip("192.0.2.255")),
                                  (parse_ip("192.0.3.1"), parse_ip("192.0.3.1"))])
        self.assertFalse(contains((starts, merged), parse_ip("192.0.3.0")))

    def test_invalid(self):
        for cidr in ["192.0.2.1/24", "192.0.2.0", "192.0.2.0/024",
                     "192.0.2.0/255.255.255.0", "192.0.2.0/33", "::/0",
                     "192.000.2.0/24", "1.0.0.0/0", "192.0.2.0/-1"]:
            with self.subTest(cidr=cidr), self.assertRaises(ValueError):
                parse_cidr(cidr)
        for address in ["192.0.2.256", "192.0.2", "192.000.2.1", "::1"]:
            with self.subTest(address=address), self.assertRaises(ValueError):
                parse_ip(address)

    def test_io(self):
        for source, expected in [
            ("2 3\n192.0.2.0/25\n192.0.2.128/25\n192.0.2.0\n192.0.2.255\n192.0.3.0\n",
             "ALLOW\nALLOW\nDENY\n"),
            ("0 2\n0.0.0.0\n255.255.255.255\n", "DENY\nDENY\n"),
            ("0 0\n", "")]:
            output = io.StringIO()
            solve(io.StringIO(source), output)
            self.assertEqual(output.getvalue(), expected)

    def test_random_reference(self):
        # 같은 시드로 같은 입력을 재현한다. 작은 주소 공간도 모두 비교한다.
        rng = random.Random(20261011)
        for case in range(400):
            networks = []
            for _ in range(rng.randrange(35)):
                if case % 2 == 0:
                    address, prefix = 0xC0000200 + rng.randrange(256), rng.randrange(24, 33)
                else:
                    address, prefix = rng.getrandbits(32), rng.randrange(33)
                networks.append(IPv4Network((address, prefix), strict=False))
            index = build_index(str(network) for network in networks)
            queries = [0, (1 << 32) - 1] + [rng.getrandbits(32) for _ in range(30)]
            if case % 2 == 0:
                queries.extend(range(0xC00001FF, 0xC0000301))
            for network in networks:
                for edge in (int(network.network_address), int(network.broadcast_address)):
                    queries.extend(value for value in (edge - 1, edge, edge + 1)
                                   if 0 <= value < (1 << 32))
            for address in queries:
                expected = any(IPv4Address(address) in network for network in networks)
                self.assertEqual(contains(index, address), expected)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AllowlistTests)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log).run(suite)
    if not result.wasSuccessful():
        print(log.getvalue())
        raise SystemExit(1)
    print("경계 조건·입력 형식·기준 풀이 비교: 성공")
```
무작위 테스트의 strict=False는 테스트용 주소를 네트워크 주소로 정리하는 데 사용한다. 생성한 CIDR을 문자열로 바꿔 풀이에 전달하며, 실제 입력을 받는 parse_cidr()는 strict=True를 유지한다.

```bash
python3 test_solution.py
```
코드를 실행해 다음 출력을 확인했다.

```text
경계 조건·입력 형식·기준 풀이 비교: 성공
```
'성공'은 테스트의 예상 결과와 일치했다는 뜻이다. 예제 출력, 구간 경계와 병합 조건, 잘못된 주소 표기, 400개 무작위 데이터 묶음의 기준 풀이 비교를 확인했다. 검증 대상은 주소의 포함 여부를 계산하는 코드이며, 실제 장비의 접근 허용 여부를 확인한 결과는 아니다.

## 실무에서는 허용 목록의 의미부터 맞춘다

이 방식은 고정된 CIDR 목록과 로그의 IP를 대조하거나 관리 대상 주소 범위에 포함되는지 확인하는 데 사용할 수 있다. 목록을 한 번 정리한 뒤 많은 주소를 조회할 때 적합하다. 목록이 자주 바뀌면 이 구현은 정렬과 병합을 다시 해야 한다.

ALLOW는 입력 주소가 허용 목록의 합집합에 들어간다는 뜻이다. 거부 규칙, 규칙 우선순위, 포트, 프로토콜, 연결 상태까지 판단하는 방화벽 정책은 다루지 않는다. 그런 규칙에서 CIDR만 합치면 원래 정책의 의미가 달라질 수 있다.

로그에서 읽은 IP의 신뢰성도 별도로 확인해야 한다. 사용자가 임의로 보낸 요청 헤더의 주소를 그대로 신뢰하거나 잘못된 CIDR을 조용히 보정하면, 탐색 코드가 정확해도 의도한 정책과 다른 결과가 나올 수 있다.

## 참고 자료

- Python, [ipaddress — IPv4/IPv6 manipulation library](https://docs.python.org/3/library/ipaddress.html)
- Python, [bisect — Array bisection algorithm](https://docs.python.org/3/library/bisect.html)
- RFC Editor, [RFC 4632: Classless Inter-domain Routing (CIDR): The Internet Address Assignment and Aggregation Plan](https://www.rfc-editor.org/rfc/rfc4632.html)
