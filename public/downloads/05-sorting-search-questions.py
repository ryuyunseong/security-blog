from bisect import bisect_left, bisect_right
import json


def show(number, value):
    print(f"q{number}: {json.dumps(value, ensure_ascii=False)}")


def main():
    rows = [("가", 3), ("나", 1), ("다", 3), ("라", 1)]
    answer1 = [name for name, key in sorted(rows, key=lambda row: row[1])]
    assert answer1 == ["나", "라", "가", "다"]
    show(1, answer1)

    values = [7, 3, 5]
    current = values[1]
    j = 0
    while j >= 0 and values[j] > current:
        values[j + 1] = values[j]
        j -= 1
    values[j + 1] = current
    assert values == [3, 7, 5]
    show(2, values)

    values = [0, 4, 4, 4, 8, 9]
    left, right = bisect_left(values, 4), bisect_right(values, 4)
    assert (left, right, right - left) == (1, 4, 3)
    show(3, [left, right, right - left])

    values = [8, 3, 6]
    copied = sorted(values)
    returned = values.sort()
    assert (values, copied, returned) == ([3, 6, 8], [3, 6, 8], None)
    assert copied is not values
    show(4, [values, copied, returned])
    print("문제 코드 4건 대조 완료")


if __name__ == "__main__":
    main()
