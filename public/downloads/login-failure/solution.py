from collections import deque
import sys


def detect(events, window, threshold):
    """시간순 실패 기록에서 IP별 최초 임계값 도달을 내보낸다."""
    active = deque()
    counts = {}
    reported = set()

    for timestamp, ip in events:
        # 왼쪽 경계는 제외하므로 timestamp - window까지 제거한다.
        while active and active[0][0] <= timestamp - window:
            _, old_ip = active.popleft()
            counts[old_ip] -= 1
            if counts[old_ip] == 0:
                del counts[old_ip]

        active.append((timestamp, ip))
        counts[ip] = counts.get(ip, 0) + 1

        # 구간에서 사라졌다 다시 나타나도 같은 IP는 한 번만 알린다.
        if counts[ip] >= threshold and ip not in reported:
            reported.add(ip)
            yield timestamp, ip


def read_events(stream, size):
    # 문제의 입력 조건을 만족하는 기록을 한 줄씩 읽는다.
    for _ in range(size):
        timestamp, ip = stream.readline().split()
        yield int(timestamp), ip


def solve(stream, output):
    size, window, threshold = map(int, stream.readline().split())
    found = False
    for timestamp, ip in detect(read_events(stream, size), window, threshold):
        output.write(f"{timestamp} {ip}\n")
        found = True
    if not found:
        output.write("NONE\n")


if __name__ == "__main__":
    solve(sys.stdin, sys.stdout)
