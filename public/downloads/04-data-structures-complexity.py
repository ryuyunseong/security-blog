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
