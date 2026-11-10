---
title: "자료구조와 Big-O: 같은 큐에서 꺼내도 비용이 다른 이유"
description: "리스트·스택·큐·해시의 차이를 정리하고, Python 카운터로 선형·로그·제곱 증가를 비교합니다. 자체 문제 5개와 문제별 접힌 해설을 제공합니다."
date: "2026-10-24T18:36:50+09:00"
sourcesChecked: "2026-10-24"
category: "cs-study"
tags: ["전산", "NCS", "자료구조", "시간복잡도", "Python", "Big O"]
draft: false
example: false
---

먼저 들어온 작업부터 꺼내는 큐를 Python 리스트로 만들 수 있어요. `pop(0)`으로 첫 원소를 꺼내면 순서는 맞지만 남은 원소가 앞으로 당겨져요. 같은 FIFO 순서를 `deque.popleft()`로 구현할 때는 양 끝의 삽입·삭제에 맞는 구조를 이용해요.

자료구조를 고를 때는 저장할 값과 자주 수행할 연산을 함께 봐요. 이번 글에서는 시간 대신 반복 횟수를 세어 입력이 커질 때 일이 얼마나 늘어나는지 살펴볼게요.

## 순서를 정하는 규칙과 저장 구조

스택은 마지막에 넣은 것을 먼저 꺼내는 LIFO, 큐는 먼저 넣은 것을 먼저 꺼내는 FIFO 규칙이에요. 이 규칙을 구현하는 방법은 하나가 아니어서 Python의 리스트로 스택을 만들 수도 있고 덱으로 큐를 만들 수도 있어요.

| 구조 | 자주 쓰는 연산 | 비용을 읽을 때의 조건 |
| --- | --- | --- |
| 동적 배열인 Python 리스트 | 인덱스로 접근, 끝에 추가 | 인덱스 접근 O(1), 끝 추가는 분할 상환 O(1), 앞 삭제는 O(n) |
| 연결 리스트 | 알려진 노드 옆 삽입·삭제 | 필요한 앞 노드·연결을 이미 아는 경우 O(1), 위치 탐색은 O(n) |
| `collections.deque` | 양 끝에 추가·삭제 | 양 끝 연산은 대략 O(1), 중간 인덱스 접근은 O(n) |
| 해시 테이블인 dict·set | 키 조회, 포함 여부 | 일반적인 평균 O(1), 충돌 등이 나쁜 경우 최악 O(n) |
| 균형 이진 탐색 트리 | 정렬된 키 탐색·삽입 | 높이가 O(log n)일 때 O(log n), 편향된 일반 트리는 O(n)까지 늘어남 |

이 표는 기본 연산 하나의 비용을 나타내요. 키 비교·해시 계산 비용은 별도로 커질 수 있고 n개를 순서대로 처리하는 전체 비용은 각 연산의 비용을 합쳐야 해요. ‘연결 리스트는 삽입 O(1)’이라는 설명도 삽입 위치를 찾는 과정까지 공짜라는 뜻은 아니에요.

리스트의 끝 추가는 저장 공간을 늘리는 일부 호출에서 복사가 필요할 수 있어요. 여러 번의 호출 비용을 합쳐 한 번당 비용으로 보는 **분할 상환**과 입력 분포를 가정하는 **평균**은 구분해요. [Python 자료구조 안내](https://docs.python.org/3.12/tutorial/datastructures.html)는 리스트를 스택으로 쓰는 예와 큐의 앞쪽 삭제 비용을 설명해요.

## Big-O는 초 단위 시간이 아니다

n을 입력 원소 수, T(n)을 정한 연산의 횟수라고 둘게요. T(n)이 `8n + 3`이면 n이 충분히 커진 뒤 상수배의 n으로 제한되므로 O(n)이에요. 계수 8과 상수항 3은 점근적인 증가율을 비교할 때 제외하지만 실제 작은 입력의 실행 시간에서는 이 값들도 영향을 줘요.

Big-O는 점근적 상한이고 Θ는 같은 증가 차수로 위아래를 제한해요. 예를 들어 `8n + 3`은 Θ(n)이에요. O(n²)라고 해도 상한이라는 뜻에서는 참이지만 보통 비교에 유용한 더 좁은 O(n)을 적어요. [NIST의 Big-O 정의](https://xlinux.nist.gov/dads/HTML/bigOnotation.html)에서도 이 차이를 구분해요.

‘최악 O(n)’은 어떤 경우를 분석했는지 밝힌 표현이에요. Big-O라는 표기 자체가 항상 최악 입력만을 뜻하지는 않아요. 첫 위치에서 찾는 선형 탐색은 한 번의 비교로 끝나지만 맨 끝에 있거나 없는 값을 찾는 경우에는 n번 비교할 수 있어요.

## Python으로 순서와 카운터 대조하기

Python 3.9 이상에서 표준 라이브러리만 사용해요. ZIP을 빈 폴더에 풀고 `04-data-structures-complexity.py`가 있는 폴더에서 `python -I -B -X utf8 04-data-structures-complexity.py`를 실행해요. Linux·WSL의 Bash에서는 `python3`로 바꿔 실행해도 돼요.

입력은 코드에 들어 있는 정수와 작은 리스트예요. 별도 입력 파일·DB·서버·계정은 필요하지 않고 관리자 권한도 사용하지 않아요. Python 파일 두 개 중 문제 검증 파일은 문제를 푼 뒤 실행해요.

[[download]]

다음은 기본 실행 파일의 전체 코드예요. 함수별 자료는 서로 독립적이어서 스택에서 꺼낸 값이 다음 큐 예제로 넘어가지 않아요.

```python
from collections import deque
import json


def show(label, value):
    print(f"{label}: {json.dumps(value, ensure_ascii=False)}")


def containers():
    stack = [10, 20, 30]
    removed = stack.pop()
    assert (removed, stack) == (30, [10, 20])
    show("스택에서 꺼낸 값과 남은 값", [removed, stack])
    queue = deque([10, 20, 30])
    removed = queue.popleft()
    queue.append(40)
    assert (removed, list(queue)) == (10, [20, 30, 40])
    show("큐에서 꺼낸 값과 남은 값", [removed, list(queue)])


def linear_steps(n):
    comparisons = 0
    for value in range(n):
        comparisons += 1
        if value == -1:
            break
    return comparisons


def halving_steps(n):
    steps = 0
    width = n
    while width > 1:
        width //= 2
        steps += 1
    return steps


def pair_steps(n):
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            pairs += 1
    return pairs


def drain_queue(n):
    values = list(range(n))
    queue = deque(values)
    shifted_slots = 0
    list_order = []
    deque_order = []
    while values:
        # 남은 원소를 앞으로 당기는 칸 수의 모형이며 내부 이동 측정이 아니다.
        shifted_slots += len(values) - 1
        list_order.append(values.pop(0))
    while queue:
        deque_order.append(queue.popleft())
    assert list_order == deque_order == list(range(n))
    assert shifted_slots == n * (n - 1) // 2
    return {"앞당김 모형": shifted_slots, "popleft 호출": len(deque_order)}


def main():
    containers()
    for n, expected in [(8, [8, 3, 28]), (16, [16, 4, 120])]:
        counts = [linear_steps(n), halving_steps(n), pair_steps(n)]
        assert counts == expected
        show(f"n={n} 선형 비교·반감 반복·쌍 방문", counts)
        show(f"n={n} FIFO 전체 꺼내기", drain_queue(n))
    print("카운터 기대값과 두 FIFO 반환 순서 일치")


if __name__ == "__main__":
    main()
```

`containers()`의 스택은 끝의 30을 꺼내고 `[10, 20]`을 남겨요. 큐에서는 왼쪽의 10을 꺼낸 다음 40을 오른쪽에 넣어 `[20, 30, 40]`이 돼요. 출력의 첫 값은 꺼낸 원소, 두 번째 리스트는 남은 순서예요. 두 사례 모두 길이가 줄거나 늘었다는 사실보다 어느 끝을 사용했는지가 규칙을 결정해요.

`linear_steps(8)`에서는 `range(8)`의 값 0부터 7까지를 -1과 비교해요. 찾는 값이 없어서 `break`에 도달하지 않고 `comparisons`는 8이 돼요. 비교 횟수에 카운터 증가나 출력 같은 다른 Python 연산을 합산하지는 않았어요.

`halving_steps(8)`은 `width`를 8, 4, 2, 1로 줄이며 반복문 본문에는 3번 들어가요. 이 코드는 반으로 줄어드는 과정만 보여 주고 정렬된 배열에서 값을 찾는 이진 탐색을 구현하지는 않아요. `pair_steps(8)`은 서로 다른 인덱스 쌍을 한 번씩 방문해요. i가 0이면 7개, 다음은 6개를 방문해 합계 28이 돼요.

[[run:1]]

입력을 8에서 16으로 늘렸을 때 선형 비교는 8에서 16, 반감 반복은 3에서 4, 쌍 방문은 28에서 120으로 변했어요. 서로 다른 쌍은 정확히 `n(n-1)/2`개이고 Θ(n²)예요. n이 두 배가 됐을 때 이 작은 두 표본의 비율이 정확히 4가 되지 않아도 제곱 차수라는 해석과 모순되지는 않아요.

## 같은 FIFO 순서에서도 달라지는 전체 작업

`drain_queue()`는 리스트와 덱에 같은 `range(n)` 값을 넣고 전부 꺼내요. 반환 순서 두 개가 원래 순서와 일치하는지 `assert`로 비교해요. 리스트 쪽의 `shifted_slots`에는 삭제 직전 길이에서 1을 뺀 값을 더해요.

[[diagram]]

n이 8이면 앞당길 칸 수의 합은 `7+6+5+4+3+2+1+0`이에요. 이 값은 남은 원소 수로 계산한 비용 모형이며 CPython 내부 복사 횟수나 실행 시간을 직접 측정한 값은 아니에요. 덱 쪽은 실제 `popleft()` 호출 수를 세었고 하나의 삭제에서 뒤 원소 전체를 앞으로 옮기는 모형을 적용하지 않아요.

리스트의 앞 삭제를 n번 반복하는 이 구현은 총 O(n²), 덱의 왼쪽 삭제를 n번 반복하는 구현은 총 O(n)이에요. 각 삭제 비용과 전체 반복 비용을 나눠 읽어 봐요. [deque 공식 문서](https://docs.python.org/3.12/library/collections.html#collections.deque)는 양 끝 연산과 리스트의 앞쪽 이동 비용을 설명해요.

마지막 줄과 종료 코드 0은 카운터 기대값 및 두 FIFO 순서가 코드의 비교식과 일치했다는 뜻이에요. 실행 시간 우열이나 모든 자료구조의 성능을 측정한 결과는 아니에요. 비교식이 틀어지면 `AssertionError`로 멈추고 0으로 끝나지 않아요. `assert`를 끄는 `-O` 옵션은 사용하지 않아요.

## 자체 연습문제 5개

직접 만든 연습문제예요. 각 문제의 정답과 상세 해설은 바로 아래에서 펼칠 수 있어요. 코드 조각은 독립된 예제이며 앞 문제의 상태를 이어받지 않아요.

### 문제 1. 같은 값을 넣은 스택과 큐

다음 코드에서 `stack.pop()`과 `queue.popleft()`가 반환하는 값을 순서대로 적어 보세요.

```python
from collections import deque
stack = ["A", "B"]
queue = deque(["A", "B"])
stack.append("C")
queue.append("C")
print(stack.pop(), queue.popleft())
```

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 문제 1: 끝과 앞에서 꺼낸 값

`C A`예요. 두 컨테이너의 순서는 모두 A, B, C가 되지만 `pop()`은 리스트 끝의 C, `popleft()`는 덱 앞의 A를 반환해요. 같은 추가 순서가 같은 제거 순서를 보장하지는 않아요.

</details>

### 문제 2. 안쪽 반복의 길이가 달라질 때

n이 5일 때 아래 `visits`의 최종값과 n에 대한 시간복잡도를 구해 보세요. 원소 한 쌍을 방문하는 비용은 O(1)이라고 둘게요.

```python
n = 5
visits = 0
for i in range(n):
    for j in range(i + 1, n):
        visits += 1
```

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 문제 2: 각 행의 방문 수를 더한다

최종값은 10이고 전체는 Θ(n²), 따라서 O(n²)예요. i가 0, 1, 2, 3, 4일 때 안쪽 반복이 각각 4, 3, 2, 1, 0번 실행되며 합은 `n(n-1)/2`예요. 안쪽 반복 길이가 일정하지 않다는 이유로 O(n)이라고 볼 수는 없어요.

</details>

### 문제 3. 계수가 큰 선형식

기본 연산 수가 정확히 T(n)=8n+3이에요. O(n), O(n²) 중 성립하는 표기는 무엇인가요? 더 좁은 상한은 어느 쪽이며 입력을 두 배로 늘리면 실제 시간이 항상 두 배라고 말할 수 있을까요?

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 문제 3: 상한과 정확한 시간을 구분한다

두 표기 모두 성립하며 더 좁은 상한은 O(n)이에요. n≥1에서 `8n+3≤11n`으로 제한할 수 있어 Θ(n)으로도 표현해요. n이 10·20일 때 연산 수는 83·163이므로 식 자체도 정확히 두 배는 아니에요. 실제 시간에는 연산별 비용과 실행 환경까지 영향을 주어서 이 표기만으로 정확한 배수를 말하지는 않아요.

</details>

### 문제 4. 리스트에서 앞 원소를 모두 삭제하기

원소가 네 개인 리스트에서 `pop(0)`을 반복해요. 한 번 삭제할 때 남은 원소를 한 칸씩 앞으로 옮긴다는 모형을 사용할게요. 처음 길이가 4이고 빈 리스트가 될 때까지 삭제하면 이동 칸 수의 합은 얼마인가요? 처음 길이가 n일 때 전체 차수도 적어 보세요.

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 문제 4: 삭제 뒤에 남는 수를 합산한다

이동 칸 수는 `3+2+1+0=6`이에요. 길이가 n일 때 합은 `n(n-1)/2`이고 전체 삭제 비용은 O(n²)예요. 마지막 빈 상태에 대한 삭제는 실행하지 않아요. 꺼낸 순서가 정확하다는 사실과 반복 비용이 작다는 평가는 별개예요.

</details>

### 문제 5. 중간에서 끝나는 선형 탐색

`values`가 `[4, 7, 9, 12]`일 때 아래 비교 횟수는 얼마인가요? 이 한 번의 결과로 이 탐색의 최악 시간복잡도를 O(1)이라고 결론 내려도 될까요?

```python
values = [4, 7, 9, 12]
comparisons = 0
for value in values:
    comparisons += 1
    if value == 7:
        break
```

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 문제 5: 관찰한 입력과 최악 입력

두 번 비교해요. 먼저 4를 비교한 뒤 7에서 `break`하므로 9와 12에는 도달하지 않아요. 없는 값이나 마지막 값을 찾는 입력에서는 n번 비교할 수 있어 이 구현의 최악 비교 횟수는 Θ(n)이에요. 한 입력의 실행 횟수로 전체 입력 크기에 대한 최악 상한을 정하지는 않아요.

</details>

## 풀이를 코드와 다시 대조하기

문제를 푼 뒤 같은 폴더에서 `python -I -B -X utf8 04-data-structures-questions.py`를 실행해요. 문제 1·2·4·5는 해당 연산을 실행하고 값과 카운터를 비교해요. 문제 3은 두 n 값의 산술 계산을 대조하며 점근 상한에 대한 설명은 위의 부등식으로 검토해요.

<details class="practice-solutions">
<summary>문제 검증 전체 코드 보기</summary>

```python
from collections import deque
import json


def main():
    answers = {}
    stack = ["A", "B"]
    queue = deque(["A", "B"])
    stack.append("C")
    queue.append("C")
    answers["q1"] = [stack.pop(), queue.popleft()]
    assert answers["q1"] == ["C", "A"]
    n = 5
    visits = 0
    for i in range(n):
        for j in range(i + 1, n):
            visits += 1
    answers["q2"] = visits
    assert visits == 10
    answers["q3"] = {"n=10 값": 83, "n=20 값": 163}
    # 계수와 상수항의 계산만 검증한다. 점근 표기 자체의 증명은 해설에서 다룬다.
    assert 8 * 10 + 3 == 83 and 8 * 20 + 3 == 163
    values = [0, 1, 2, 3]
    moved = 0
    while values:
        moved += len(values) - 1
        values.pop(0)
    answers["q4"] = moved
    assert moved == 6
    values = [4, 7, 9, 12]
    comparisons = 0
    for value in values:
        comparisons += 1
        if value == 7:
            break
    answers["q5"] = comparisons
    assert comparisons == 2
    for name, value in answers.items():
        print(f"{name}: {json.dumps(value, ensure_ascii=False)}")
    print("자체 문제: 코드 4건과 계산 예시 대조 완료")


if __name__ == "__main__":
    main()
```

</details>

종합 출력의 q 번호는 문제 번호예요. q1의 JSON 배열은 문제에서 공백으로 출력한 두 값을 같은 순서로 담아요. 정답을 먼저 보지 않도록 실행 기록도 접어 두었어요.

[[run:2:fold]]

각 입력은 검증 파일 안에서 다시 만들며 다른 문제의 컨테이너를 공유하지 않아요. 실행 뒤 생성되는 파일은 없고 컨테이너는 프로세스 종료와 함께 정리돼요. 오류가 나면 첫 `AssertionError`의 입력과 분기를 살펴봐요.

## 시험 직전 복습

- 스택·큐는 제거 순서의 규칙이에요. 구현에 쓴 자료구조와 연산의 비용을 함께 봐요.
- 위치를 이미 아는 것과 그 위치를 찾는 과정, 연산 한 번과 n번의 합계를 나눠요.
- Big-O는 점근적 상한이고 Θ는 같은 증가 차수로 위아래를 제한해요. 최선·평균·최악·분할 상환 중 어느 조건인지 적어요.
- 반복문이 중첩돼 있어도 실제 반복 길이를 세어 봐요. 일정 비율로 줄어드는 반복은 로그 증가의 근거가 돼요.
- 코드에서 센 카운터, 비용 모형, 실제 초 단위 측정값은 서로 다른 자료예요.
