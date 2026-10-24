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
