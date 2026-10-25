from bisect import bisect_left, bisect_right
import json


def show(label, value):
    print(f"{label}: {json.dumps(value, ensure_ascii=False)}")


def insertion_sort(values):
    result = list(values)
    comparisons = shifts = 0
    trace = []
    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if result[j] <= current:
                break
            result[j + 1] = result[j]
            shifts += 1
            j -= 1
        result[j + 1] = current
        trace.append(result.copy())
    return result, comparisons, shifts, trace


def lower_bound(values, target):
    lo, hi = 0, len(values)
    trace = []
    while lo < hi:
        mid = lo + (hi - lo) // 2
        trace.append([lo, hi, mid, values[mid]])
        if values[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo, trace


def main():
    original = [5, 2, 4, 2]
    result, comparisons, shifts, trace = insertion_sort(original)
    assert original == [5, 2, 4, 2]
    assert result == [2, 2, 4, 5] and (comparisons, shifts) == (6, 4)
    assert trace == [[2, 5, 4, 2], [2, 4, 5, 2], [2, 2, 4, 5]]
    show("삽입 단계", trace)
    show("키 비교와 오른쪽 이동", [comparisons, shifts])
    for values, expected in [([1, 2, 3, 4], [3, 0]), ([4, 3, 2, 1], [6, 6])]:
        _, count, moves, _ = insertion_sort(values)
        assert [count, moves] == expected
        show(f"입력 {values}의 비교와 이동", expected)
    values = [2, 2, 4, 5, 9, 12]
    for target, expected in [(5, 3), (6, 4), (20, 6)]:
        position, steps = lower_bound(values, target)
        assert position == expected == bisect_left(values, target)
        found = position < len(values) and values[position] == target
        show(f"값 {target}의 위치와 존재", [position, found])
        show(f"값 {target}의 lo·hi·mid·중간값", steps)
    empty_position, empty_trace = lower_bound([], 5)
    assert (empty_position, empty_trace) == (0, [])
    show("빈 배열의 삽입 위치", empty_position)
    assert (bisect_left(values, 2), bisect_right(values, 2)) == (0, 2)
    show("값 2의 왼쪽·오른쪽 경계", [0, 2])
    rows = [("A", 2), ("B", 1), ("C", 2)]
    ordered = sorted(rows, key=lambda row: row[1])
    assert ordered == [("B", 1), ("A", 2), ("C", 2)]
    show("키만 정렬한 레코드", ordered)
    print("기본 예제의 기대값 대조 완료")


if __name__ == "__main__":
    main()
