---
title: "로그에서 반복 로그인 실패 IP 찾기"
description: "슬라이딩 윈도와 덱으로 최근 구간에 로그인 실패가 반복된 IPv4 주소를 찾습니다."
date: "2026-10-10T21:22:40+09:00"
updated: "2026-10-21"
category: "coding-test"
tags: ["Python", "알고리즘", "로그"]
draft: false
example: false
---

최근 10초의 로그인 실패를 세려면 시간이 흐를 때 오래된 기록을 집계에서 빼야 한다. 모든 과거 기록을 매번 읽는 대신 현재 구간만 덱에 남기면 비교 횟수를 줄일 수 있다.

가상 로그인 실패 기록에서 최근 구간의 실패 횟수가 기준에 처음 도달한 IP를 찾는 문제다. 슬라이딩 윈도와 덱, 딕셔너리로 풀이한다.

## 문제와 입출력 규칙

로그인 실패 기록 N개가 시간순으로 주어진다. 각 줄을 읽은 직후, 같은 IP의 최근 W초 내 실패가 K회 이상이면 그 시각과 IP를 출력한다. 같은 IP는 전체 입력에서 처음 조건을 만족했을 때 한 번만 출력한다.

```text
N W K
timestamp ip
...
```
| 항목 | 규칙 |
| --- | --- |
| 입력 크기 | 0 ≤ N ≤ 200,000, 1 ≤ W ≤ 10⁹, 1 ≤ K ≤ 200,000 |
| 시각 | 초 단위 정수이며 0 ≤ timestamp ≤ 10¹². 입력 시각은 감소하지 않는다. |
| IP | 네 부분이 각각 0~255인 IPv4 점 표기 문자열. 0 자체를 제외한 앞자리 0은 없으며 입력은 조건을 만족한다. |
| 집계 대상 | 모든 줄이 로그인 실패 한 건이다. 시각과 IP가 같아도 별도 실패로 센다. 성공 기록은 없다. |
| 시간 구간 | `t − W < 기록 시각 ≤ t`인 기록 중 현재 줄까지 읽은 것만 센다. |
| 같은 시각 | 주어진 줄 순서대로 처리하며 아직 읽지 않은 기록은 포함하지 않는다. |
| 출력 순서 | 각 IP가 처음 K회에 도달한 기록의 입력 순서. 같은 시각도 IP순으로 정렬하지 않는다. |
| 출력 형식 | 각 줄에 시각과 IP를 공백 하나로 구분한다. 결과가 없으면 NONE 한 줄을 출력한다. |

W=10, t=10이면 구간은 (0, 10]이다. 0초 기록은 제외하고 1초부터 10초까지 포함하므로, 만료 기록을 지울 때 왼쪽 경계도 함께 제거해야 한다.

## 입출력 예제

**입력 1**

```text
9 10 3
0 192.0.2.10
1 198.51.100.20
4 192.0.2.10
9 192.0.2.10
10 198.51.100.20
11 198.51.100.20
12 198.51.100.20
20 192.0.2.10
21 192.0.2.10
```
**출력 1**

```text
9 192.0.2.10
12 198.51.100.20
```
| 시각·IP | 구간 안 기록 | 판단 |
| --- | --- | --- |
| 9 · 192.0.2.10 | 0, 4, 9 | 처음 3회가 되어 출력한다. |
| 11 · 198.51.100.20 | 10, 11 | 1초 기록은 왼쪽 경계라 제외된다. 아직 2회다. |
| 12 · 198.51.100.20 | 10, 11, 12 | 처음 3회가 되어 출력한다. |
| 21 · 192.0.2.10 | 20, 21 | 현재 2회다. 이후 기준에 다시 도달해도 이미 출력한 IP는 알리지 않는다. |

**입력 2**

```text
2 10 2
0 192.0.2.10
10 192.0.2.10
```
**출력 2**

```text
NONE
```
10초 기록을 읽을 때 0초 기록은 구간에서 빠진다. 남은 실패는 한 건이므로 임계값 2에 도달하지 않는다. N=0인 입력도 NONE을 출력한다.

## 덱으로 최근 구간만 유지한다

매번 앞선 모든 기록을 훑어 같은 IP의 실패를 세면 최대 1+2+…+N번 비교해 O(N²) 시간이 든다. 작은 입력의 정답을 확인하는 데는 쓸 수 있지만, N이 커지면 비효율적이다.

입력 시각이 감소하지 않으므로 구간 밖으로 밀려난 기록은 다시 필요하지 않다. 최근 기록은 하나의 덱에 넣고, IP별 횟수는 딕셔너리로 관리한다.

1. 덱 맨 앞 시각이 t−W 이하이면 꺼내고 해당 IP의 횟수를 줄인다. 조건을 만족하는 기록이 없을 때까지 반복한다.
2. 현재 기록을 덱 끝에 넣고 해당 IP의 횟수를 늘린다.
3. 현재 IP의 횟수가 K 이상이고 아직 출력하지 않았다면 결과를 내보낸다.

새 기록으로 실패 횟수가 늘어나는 IP는 현재 IP 하나뿐이다. 다른 IP의 횟수는 그대로이거나 줄어드므로 전부 검사할 필요가 없다. 덱에서 만료 기록을 지울 때 `counts`도 갱신해 두 자료의 개수를 맞춘다.

리스트의 `pop(0)`은 나머지 항목을 이동시켜야 한다. 반면 덱의 `append()`와 `popleft()`는 양 끝에서 대략 O(1)로 동작한다. 다만 W는 초 단위 시간이므로 기록 개수를 제한하는 `deque(maxlen=W)`로 바꾸면 안 된다.

[[diagram]]

## Python 구현

다음 코드를 `solution.py`로 저장한다. Python 3의 표준 라이브러리만 사용하며, 입력 조건을 만족하는 코딩 테스트 데이터용 풀이이다.

직접 복사하는 대신 [solution.py](../../downloads/login-failure/solution.py), [첫 번째 예제의 input.txt](../../downloads/login-failure/input.txt), [test_solution.py](../../downloads/login-failure/test_solution.py)를 내려받아 새 폴더 하나에 함께 둘 수도 있다. 파일 이름을 유지하고 그 폴더에서 실행한다. CIDR 글도 `solution.py`라는 이름을 사용하므로 두 문제는 폴더를 나눠 보관한다. 실제 서버 로그나 로그인 계정은 필요 없다.

```python
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
```
`read_events()`는 기록을 한 줄씩 읽고, `detect()`는 조건을 만족한 결과를 차례로 내보낸다. 전체 입력과 결과를 목록으로 저장하지 않는다. `reported`는 이미 출력한 IP를 기억하며, 해당 IP의 기록이 구간에서 사라져도 지우지 않는다.

`input.txt`에 예제 입력을 넣고 다음 명령으로 실행한다.

```bash
python3 solution.py < input.txt
```
위 명령은 Bash의 입력 리다이렉션이다. PowerShell에서는 `Get-Content .\input.txt | python .\solution.py`로 예제 텍스트를 전달할 수 있다. `input.txt`에는 `입력 1`이라는 제목이나 코드 블록 표시를 넣지 않고 첫 줄 `9 10 3`부터 기록한다.

예제 1에서는 9초와 12초의 두 IP가 출력된다. 이 시각은 문제의 집계 조건을 처음 만족한 시각이다. `solve()`는 첫 줄에서 N·W·K를 읽고 `read_events()`가 정확히 N줄을 공급하도록 한다. `detect()`가 결과를 하나 내보낼 때마다 출력하고, 끝까지 하나도 없었을 때만 `NONE`을 한 줄 쓴다. 입력이 잘못된 경우를 교정하는 파서는 아니므로 헤더나 기록이 빠지면 예외로 중단할 수 있다.

## 복잡도와 자주 틀리는 부분

각 기록은 덱에 한 번 들어가고 최대 한 번 나온다. while문이 있어도 전체 제거 횟수는 N을 넘지 않는다. 딕셔너리와 집합 연산을 평균 O(1)로 보면 전체 시간은 O(N)이다. 해시 충돌을 포함한 최악 시간까지 보장하는 것은 아니다.

M을 구간 안에 남는 최대 기록 수, U를 전체 서로 다른 IP 수라고 하면 보조 공간은 O(M+U)이다. `reported`가 이미 알린 IP를 계속 기억하기 때문이다. 모든 기록의 시각이 같으면 M=N이므로 메모리가 항상 적게 필요한 풀이는 아니다.

| 실수 | 이유와 수정 |
| --- | --- |
| `old_time < t−W`로 제거 | 왼쪽 경계가 남는다. 이 문제에서는 ≤로 제거한다. |
| 같은 시각을 IP순으로 정렬 | 출력 순서가 바뀐다. 주어진 줄 순서를 유지한다. |
| 횟수가 0이면 reported도 삭제 | 같은 IP가 나중에 중복 출력된다. reported는 계속 유지한다. |
| 길이 W인 덱 사용 | 시간과 기록 개수는 다르다. 만료된 시각을 기준으로 제거한다. |
| 역순 로그에 그대로 적용 | 이미 버린 기록이 다시 필요할 수 있다. 비감소 시각이라는 전제를 확인한다. |

## 경계 조건과 단순 풀이로 검증한다

다음 코드를 같은 폴더의 `test_solution.py`로 저장한다. 경계·동시각·재도달 사례를 먼저 확인하고, 작은 무작위 입력 2,000건에서 앞선 기록을 모두 세는 단순 풀이와 결과를 비교한다. 시드를 고정해 같은 입력을 다시 만들 수 있다.

```python
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
```
```bash
python3 test_solution.py
```
`test_solution.py`의 `from solution import ...`는 같은 폴더의 풀이를 가져온다. 두 파일을 따로 두면 모듈을 찾지 못하거나 다른 풀이를 읽을 수 있다. 테스트 명령에는 `-I`를 추가하지 않는다. 격리 모드에서는 이 폴더가 모듈 검색 경로에서 빠지기 때문이다. `input.txt`는 풀이를 직접 실행할 때 쓰며, 테스트 파일은 자체 문자열과 목록으로 자료를 만든다.

세 출력 줄은 각각 다음 검사를 마쳤다는 뜻이다. 첫 줄은 이름을 붙인 경계 사례 9개, 두 번째는 고정 시드의 무작위 입력 2,000건과 `brute_force()`의 결과 비교, 세 번째는 `StringIO`로 첫 예제·빈 입력·왼쪽 경계를 넣은 입출력 비교다. 기대값이 다르면 해당 `assert`에서 중단하므로 `python -O`로 검사를 끄지 않고 실행한다. 모두 통과하면 종료 코드 0이다.

```text
경계·동시각·중복 알림 확인: 성공
무작위 입력과 전수 탐색 비교: 성공
입출력 예제 확인: 성공
```
무작위 비교 외에도 왼쪽 경계와 동시각 처리 순서를 따로 시험했다. 덱에 현재 구간의 기록만 남고 IP별 횟수가 그 기록 수와 일치한다는 관계로 풀이의 동작을 설명할 수 있다. 무작위 비교만으로 정확성이 증명되는 것은 아니다.

[[run:1:fold]]

## 보안 로그에 적용할 때

이 집계는 짧은 시간에 실패가 몰린 출발지를 좁혀 보는 데 활용할 수 있다. 다만 NAT 뒤의 여러 사용자가 같은 IP를 공유할 수 있고, 여러 IP로 분산된 시도는 IP별 기준 아래에 머물 수 있다.

운영 로그에는 성공·실패 구분, 신뢰할 수 있는 출발지 필드, IPv6 표기 통일, 중복 수집, 수집 지연과 시계 차이를 반영해야 한다. 이 풀이는 각 줄을 별도 실패로 세므로 중복 로그도 그대로 집계한다. 전체 입력에서 한 번만 알리는 정책 역시 상시 감시의 재알림·보관 만료 정책과는 다르다.

K=3은 풀이를 위한 예시값이다. 실제 로그인 제한과 계정 잠금에는 계정별 실패 횟수, 관찰 구간, 잠금 시간, 다른 사용자의 계정을 잠그는 서비스 거부 위험도 함께 고려한다. 이 글에서 확인한 것은 예제 데이터의 집계 정확성이며, 출력된 IP를 공격자로 확정하거나 자동 차단하는 기준은 아니다.

## 참고 자료

- [Python 3.12 문서: collections.deque](https://docs.python.org/3.12/library/collections.html#collections.deque)
- [Python 튜토리얼: 리스트를 큐로 사용하기](https://docs.python.org/3.12/tutorial/datastructures.html#using-lists-as-queues)
- [RFC 5737: 문서와 예제용 IPv4 주소 대역](https://www.rfc-editor.org/rfc/rfc5737.html)
- [OWASP Authentication Cheat Sheet: Login Throttling](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#login-throttling)
