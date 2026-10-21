from io import StringIO
from random import Random
from solution import detect, solve


def brute_force(events, window, threshold):
    # 앞선 모든 기록을 다시 세어 비교 기준으로 사용한다.
    answer = []
    reported = set()
    for i, (timestamp, ip) in enumerate(events):
        count = sum(
            old_ip == ip and timestamp - window < old_time <= timestamp
            for old_time, old_ip in events[:i + 1]
        )
        if count >= threshold and ip not in reported:
            reported.add(ip)
            answer.append((timestamp, ip))
    return answer


def run_tests():
    a, b = "192.0.2.10", "198.51.100.20"
    cases = [
        ("빈 입력", [], 10, 3, []),
        ("왼쪽 경계 제외", [(0, a), (10, a)], 10, 2, []),
        ("경계 바로 안쪽", [(1, a), (10, a)], 10, 2, [(10, a)]),
        ("같은 시각의 입력 순서",
         [(5, b), (5, a), (5, b), (5, a)],
         1, 2, [(5, b), (5, a)]),
        ("임계값 1", [(0, a), (0, b), (100, a)],
         1, 1, [(0, a), (0, b)]),
        ("한 IP의 재도달", [(0, a), (1, a), (20, a), (21, a)],
         5, 2, [(1, a)]),
        ("서로 다른 IP", [(0, a), (1, b)], 10, 2, []),
        ("시각의 큰 공백", [(0, a), (1, b), (10**12, a)],
         1, 2, []),
        ("기록보다 큰 임계값", [(0, a)], 10, 2, []),
    ]
    for label, events, window, threshold, expected in cases:
        assert list(detect(iter(events), window, threshold)) == expected, label
    print("경계·동시각·중복 알림 확인: 성공")

    random = Random(20261010)
    for _ in range(2000):
        timestamp = 0
        events = []
        for _ in range(random.randrange(51)):
            timestamp += random.randrange(5)
            events.append((timestamp, random.choice([a, b, "203.0.113.30"])))
        window, threshold = random.randint(1, 15), random.randint(1, 8)
        assert list(detect(iter(events), window, threshold)) == brute_force(
            events, window, threshold
        ), (events, window, threshold)
    print("무작위 입력과 전수 탐색 비교: 성공")

    example = """9 10 3
0 192.0.2.10
1 198.51.100.20
4 192.0.2.10
9 192.0.2.10
10 198.51.100.20
11 198.51.100.20
12 198.51.100.20
20 192.0.2.10
21 192.0.2.10
"""
    output = StringIO()
    solve(StringIO(example), output)
    assert output.getvalue() == "9 192.0.2.10\n12 198.51.100.20\n"
    for source in (
        "0 10 3\n",
        "2 10 2\n0 192.0.2.10\n10 192.0.2.10\n",
    ):
        output = StringIO()
        solve(StringIO(source), output)
        assert output.getvalue() == "NONE\n"
    print("입출력 예제 확인: 성공")


if __name__ == "__main__":
    run_tests()
