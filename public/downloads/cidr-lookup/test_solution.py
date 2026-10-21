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
