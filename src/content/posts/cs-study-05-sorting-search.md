---
title: "정렬과 이진 탐색: 배열이 바뀌는 과정과 경계 읽기"
description: "삽입 정렬의 비교·이동을 세고, 정렬된 배열에서 이진 탐색의 범위를 좁혀 봅니다. 안정 정렬과 bisect 경계를 자체 문제 5개로 연습합니다."
date: "2026-10-25T18:37:56+09:00"
sourcesChecked: "2026-10-25"
category: "cs-study"
tags: ["전산", "NCS", "정렬", "탐색", "알고리즘", "Python"]
draft: false
example: false
---

`[5, 2, 4, 2]`를 오름차순으로 정렬하면 `[2, 2, 4, 5]`가 된다. 최종 배열만 보면 어떤 원소를 몇 번 비교하고 옮겼는지는 드러나지 않는다. 정렬 알고리즘의 중간 상태와 탐색 구간을 써 보면 반복문이 하는 일이 보인다.

[앞 글의 Big-O와 자료구조](../cs-study-04-data-structures-complexity/)에서 비용의 증가율을 살폈다면 이번에는 실제 배열을 따라가며 비교·이동·삽입 위치를 구분한다. 예제와 문제는 직접 만든 가상 자료다.

## 정렬된 앞부분에 다음 값을 넣는 방법

삽입 정렬은 앞부분을 정렬된 상태로 유지하면서 다음 원소를 알맞은 자리에 넣는다. 배열 `[5, 2, 4, 2]`에서 처음의 `5` 하나는 이미 정렬돼 있다. 다음 `2`를 꺼내 `5`를 오른쪽으로 옮기고 빈자리에 넣는다. 이때 전체 배열은 `[2, 5, 4, 2]`이며 뒤의 `4, 2`는 아직 처리하지 않았다.

다음에는 `4`, 마지막에는 두 번째 `2`를 같은 방식으로 넣는다. ‘한 단계가 끝났다’는 말은 앞부분이 하나 늘었다는 뜻이며 전체 정렬 완료와 구분한다.

[[diagram]]

이번 구현은 같은 값일 때 더 옮기지 않는다. 앞에 있던 `2`를 뒤의 `2`가 넘어가지 않으므로 같은 키의 원래 순서가 유지된다. 이를 **안정 정렬**이라고 한다. 숫자만으로는 두 `2`를 구별하기 어려워 뒤에서는 이름이 붙은 레코드로도 대조한다.

## 직접 실행하며 비교와 이동 세기

Python 3.9 이상과 표준 라이브러리를 사용한다. ZIP을 빈 폴더에 풀고 `05-sorting-search.py`가 있는 폴더에서 다음 명령을 실행한다. Linux·WSL에서는 `python`을 `python3`로 바꿔도 된다.

입력 배열은 코드 안에 있다. 별도 데이터 파일·서버·DB·계정이나 관리자 권한은 필요하지 않다. 함께 들어 있는 `05-sorting-search-questions.py`는 문제를 푼 뒤 실행한다.

[[download]]

```bash
python -I -B -X utf8 05-sorting-search.py
```

다음 전체 코드에는 삽입 정렬과 이진 탐색의 경계 함수가 함께 있다. 각 예제는 새 배열을 사용한다.

```python
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
```

`insertion_sort()`는 `list(values)`로 복사한 `result`를 정렬한다. `current`에 이번 원소를 보관하고 `j`를 왼쪽으로 움직인다. `result[j] <= current`이면 멈추며 더 큰 원소만 오른쪽으로 옮긴다. `trace.append(result.copy())`도 복사여서 뒤 단계의 변경이 앞 단계 기록을 덮어쓰지 않는다.

`comparisons`는 원소와 `current`를 비교한 횟수이고 `shifts`는 더 큰 원소를 한 칸 옮긴 횟수다. 반복 조건인 `j >= 0`의 검사나 `current`를 빈자리에 쓰는 대입은 이 카운터에 포함하지 않았다. 실행 시간이나 모든 CPU 연산을 측정한 값도 아니다.

[[run:1]]

첫 입력에서는 비교 6회, 오른쪽 이동 4회가 나왔다. 마지막 `current=2`는 `5`와 `4`를 옮기고 앞에 있는 같은 값 `2`와 비교한 뒤 멈춘다. 이 단계가 비교 3회·이동 2회를 더하므로 두 카운터가 달라진다.

네 원소가 이미 오름차순이면 비교 3회·이동 0회이고 역순이면 각각 6회다. 이 구현의 최선은 O(n), 최악은 O(n²)다. [NIST의 삽입 정렬 설명](https://xlinux.nist.gov/dads/HTML/insertionSort.html)과 함께 이동할 원소의 수를 세어 읽을 수 있다.

## 이진 탐색이 남겨 두는 반열린 구간

이진 탐색은 **정렬된 자료**에서 탐색 범위를 좁힌다. 여기서는 인덱스 `lo` 이상 `hi` 미만인 `[lo, hi)`를 후보로 둔다. `hi=len(values)`이므로 `hi` 자체는 원소 인덱스로 읽지 않는다.

`lower_bound()`의 중간값이 목표보다 작으면 `lo=mid+1`로 옮긴다. 그렇지 않으면 같은 값이 더 왼쪽에도 있을 수 있으므로 `hi=mid`로 줄인다. 끝나면 목표값 이상인 첫 원소의 위치를 반환하고 그런 원소가 없으면 배열 길이를 반환한다. [Python bisect_left 문서](https://docs.python.org/3.12/library/bisect.html)의 경계와 같다.

예제 배열 `[2, 2, 4, 5, 9, 12]`에서 값 `5`를 찾는 기록은 다음 순서다. 각 출력 행은 `[lo, hi, mid, 중간값]`이다.

- `[0, 6, 3, 5]`: 같은 값을 만나도 `hi`를 3으로 줄인다.
- `[0, 3, 1, 2]`: 2가 더 작으므로 `lo`를 2로 옮긴다.
- `[2, 3, 2, 4]`: 4도 작으므로 `lo`가 3이 된다. 구간이 비어 위치 3을 반환한다.

값 `6`은 배열에 없어도 삽입 위치 4가 나온다. `position < len(values) and values[position] == target`을 추가로 대조해야 존재 여부를 알 수 있다. 값 `20`의 위치 6과 빈 배열의 위치 0도 정상적인 삽입 경계다. 해당 위치의 원소가 있다는 뜻은 아니다.

반복마다 구간을 반으로 줄이는 비교는 O(log n)이다. 그러나 `bisect.insort`처럼 실제 삽입까지 하면 Python 리스트의 뒤쪽 원소 이동이 O(n)일 수 있다. 삽입 위치 탐색과 삽입 작업의 전체 비용을 나눠 읽는다.

## 안정성·원본 변경·전체 비용 비교

| 비교할 조건 | 구분할 내용 |
| --- | --- |
| 안정 정렬 | 같은 키를 가진 레코드의 기존 순서를 유지하는가 |
| `sorted(values)` | 새 정렬 리스트를 반환하고 원래 리스트를 그대로 두는가 |
| `values.sort()` | 원래 리스트를 바꾸고 반환값은 `None`인가 |
| 선형 탐색 | 정렬하지 않은 자료에도 적용할 수 있는가 |
| 이진 탐색 | 같은 정렬 기준으로 정돈된 배열인가 |
| 전체 작업 | 정렬·복사·삽입 비용도 함께 계산했는가 |

기본 예제의 레코드는 `("A", 2), ("B", 1), ("C", 2)`다. 키만 정렬한 결과는 B·A·C 순서이며 같은 키 2의 A가 C보다 앞에 남는다. [Python 정렬 안내](https://docs.python.org/3.12/howto/sorting.html)는 정렬 안정성과 두 정렬 API의 차이를 설명한다. 튜플 전체를 비교하는 것과 지정한 키만 비교하는 것도 구분한다.

삽입 정렬의 O(n²) 최악 비용과 이진 탐색의 O(log n) 비교 횟수는 서로 다른 작업의 분석이다. 탐색을 빠르게 하려고 먼저 정렬했다면 정렬 비용도 전체에 더한다. 비교 비용·자료의 상태·추가 공간이 달라지면 실제 실행 시간도 달라진다.

## 자체 연습문제 5개

아래 문제는 자체 제작했다. 각 문제 바로 아래의 해설은 처음에는 접혀 있다.

### 문제 1. 같은 키의 이름 순서

다음 코드가 출력하는 이름 목록은 무엇인가?

```python
rows = [("가", 3), ("나", 1), ("다", 3), ("라", 1)]
print([name for name, key in sorted(rows, key=lambda row: row[1])])
```

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 해설 1. 키가 같은 두 쌍

`['나', '라', '가', '다']`다. 키 1의 나·라가 먼저 오고 키 3의 가·다가 뒤에 온다. 각 키 안에서는 원래 순서를 유지한다. 정렬 키 함수가 이름을 반환하지 않으므로 이름순으로 동률을 다시 정렬하지 않는다.

</details>

### 문제 2. 삽입 정렬의 첫 단계

다음 코드는 두 번째 원소만 앞부분에 삽입한다. 출력 배열은 무엇인가?

```python
values = [7, 3, 5]
current = values[1]
j = 0
while j >= 0 and values[j] > current:
    values[j + 1] = values[j]
    j -= 1
values[j + 1] = current
print(values)
```

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 해설 2. 처리한 앞부분의 길이

`[3, 7, 5]`다. `current=3`을 보관한 채 7을 오른쪽으로 옮기면 `j=-1`이 되고 `values[0]`에 3을 넣는다. 마지막 5를 삽입하는 단계는 아직 실행하지 않았다.

</details>

### 문제 3. 중복 값의 경계

두 경계와 그 차이를 출력하면 각각 얼마인가? 인덱스는 0부터 센다.

```python
from bisect import bisect_left, bisect_right
values = [0, 4, 4, 4, 8, 9]
left, right = bisect_left(values, 4), bisect_right(values, 4)
print(left, right, right - left)
```

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 해설 3. 오른쪽 경계는 다음 위치

`1 4 3`이다. 4가 처음 나타나는 위치는 1이고 오른쪽 삽입 경계 4는 마지막 4 뒤의 위치다. `values[1:4]`가 세 개의 4를 담으므로 차이는 3이다. 오른쪽 경계를 마지막 원소의 인덱스 3으로 착각하지 않는다.

</details>

### 문제 4. 정렬한 결과와 반환값

세 줄의 출력은 무엇인가?

```python
values = [8, 3, 6]
copied = sorted(values)
returned = values.sort()
print(values)
print(copied)
print(returned)
```

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 해설 4. 리스트 두 개와 None

첫째·둘째 줄은 각각 `[3, 6, 8]`, 마지막은 `None`이다. `sorted()`가 새 리스트를 만든 뒤 `sort()`는 원래 `values`를 직접 바꾼다. 두 리스트의 값이 같아도 서로 다른 객체다. `returned`를 정렬 리스트라고 간주하면 안 된다.

</details>

### 문제 5. 한 번 검색할 자료를 먼저 정렬할까

정렬되지 않은 n개 자료에서 특정 값을 한 번만 찾는다. “이진 탐색이 O(log n)이므로 항상 정렬 후 이진 탐색이 선형 탐색보다 유리하다”는 설명이 맞는가? 정렬 비용도 포함해 답하라.

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 해설 5. 한 번의 탐색 앞에 생기는 작업

항상 유리하다는 설명은 맞지 않는다. 선형 탐색은 최악 O(n)이고 별도 정렬이 필요 없다. 비교 기반 O(n log n) 정렬을 먼저 하면 그 비용에 O(log n) 탐색이 더해진다. 여러 번 검색하거나 이미 정렬된 자료를 유지하는 경우에는 비용을 따로 계산할 수 있지만 한 번의 검색에서 정렬 비용을 지울 수는 없다.

</details>

## 문제 풀이를 실행으로 대조하기

문제를 푼 뒤 ZIP의 `05-sorting-search-questions.py`를 실행한다. 앞의 네 코드 문제마다 새 자료를 만들며 앞 문제의 정렬 결과를 이어받지 않는다. 5번은 전체 비용을 비교하는 개념 문제로 실행 결과를 만들지 않았다.

<details class="study-verification">
<summary>문제 검증 코드와 종합 출력 보기</summary>

다음은 검증 파일 전체다. `q` 번호는 문제 번호다. 목록과 여러 줄 출력은 같은 순서의 JSON 배열로 묶었으며 Python의 `None`은 JSON에서 `null`로 표시된다.

```python
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
```

```bash
python -I -B -X utf8 05-sorting-search-questions.py
```

[[run:2]]

마지막 완료 문구와 종료 코드 0은 네 코드 문제의 값이 `assert`의 기대값과 맞았다는 뜻이다. 문제 5의 설명까지 프로그램이 증명했다는 의미는 아니다. 두 실행 파일은 결과 파일을 만들지 않으며 사용한 메모리 자료는 프로세스 종료와 함께 사라진다.

</details>

## 시험 직전 복습

- 삽입 정렬은 정렬된 앞부분을 늘린다. 한 단계의 배열과 전체 정렬 결과를 구분한다.
- 비교 횟수·이동 횟수·실제 실행 시간은 서로 다른 자료다.
- 안정 정렬은 같은 키의 기존 순서를 유지한다.
- 이진 탐색의 정렬 조건과 `[lo, hi)` 경계를 함께 적는다. 삽입 위치를 얻은 뒤 값의 존재를 따로 대조한다.
- `sorted()`의 새 리스트와 `sort()`의 제자리 변경·`None` 반환을 구분한다.
- 정렬·복사·삽입이 앞뒤에 붙으면 그 비용도 전체 작업에 포함한다.
