---
title: "C·Java·Python 출력 문제: 나눗셈과 변수 변경 따라가기"
description: "같은 정수도 언어와 연산자에 따라 몫·나머지가 달라집니다. 단락 평가, 함수 인수, 배열·리스트 변경을 직접 실행하고 자체 문제 5개로 연습합니다."
date: "2026-10-26T18:47:53+09:00"
sourcesChecked: "2026-10-26"
category: "cs-study"
tags: ["전산", "NCS", "C", "Java", "Python", "출력 문제"]
draft: false
example: false
---

`-7`을 `3`으로 나눈 정수 몫은 C와 Java에서 `-2`, Python의 `//`에서는 `-3`이에요. 부호가 다른 두 정수를 만나면 ‘소수 부분을 없앤다’는 암기만으로는 출력을 맞히기 어려워요. **변수의 자료형과 사용한 연산자**를 먼저 적고 계산해야 해요.

이번 글에서는 작은 프로그램의 상태를 따라가 봐요. [앞 글의 정렬·탐색](../cs-study-05-sorting-search/)처럼 중간 값을 써 보되 알고리즘의 비용 대신 언어가 식과 대입을 처리하는 규칙에 집중해요. 예제와 문제는 자체 제작했어요.

## 음수 나눗셈에서 갈라지는 몫과 나머지

C11과 Java의 정수 `/`는 0을 향해 몫을 잘라요. Python의 정수 `//`는 몫을 음의 무한대 방향으로 내리고요. 이 차이 때문에 `-7 / 3`의 정수 몫 `-2`와 `-7 // 3`의 `-3`이 갈라져요. Python의 `/`는 여기서 비교하는 정수 몫 연산과 달라요.

[[diagram]]

두 경우 모두 피제수는 ‘몫 × 제수 + 나머지’로 복원돼요. C·Java에서는 `-2 * 3 + (-1) = -7`, Python에서는 `-3 * 3 + 2 = -7`이에요. 나머지는 무조건 양수가 나온다고 외우지 않고 어느 나눗셈 규칙과 짝인지 살펴봐요. [C11 공개 위원회 초안 N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)의 6.5.5, [Java 표현식 명세](https://docs.oracle.com/javase/specs/jls/se25/html/jls-15.html#jls-15.17.2), [Python 표현식 문서](https://docs.python.org/3.12/reference/expressions.html#binary-arithmetic-operations)에서 이 규칙을 대조할 수 있어요.

## 세 언어의 예제를 같은 입력으로 실행하기

ZIP을 빈 폴더에 풀고 `06-run-examples.py`가 있는 폴더에서 README의 언어별 명령을 실행해요. 입력은 각 소스 안의 작은 정수와 배열이므로 별도 입력 파일·서버·계정이나 관리자 권한은 필요하지 않아요.

- 실행 도우미에는 Python 3.9 이상과 표준 라이브러리가 필요해요.
- C에는 `gcc`와 C11 지원, Java에는 `javac`·`java`가 있는 JDK 17 이상이 필요해요. 각 도구가 해당 터미널의 PATH에 있어야 해요.
- 실제 검증은 C를 WSL Ubuntu 24.04의 GCC 13.3.0·Python 3.12.3에서, Java를 Windows의 JDK 25·Python 3.12.1에서 수행했어요. Python 예제도 Windows Python 3.12.1에서 실행했어요.

[[download]]

아래 명령은 Bash 기준이에요. Windows PowerShell에서 Java·Python을 실행할 때는 `python3`를 `python`으로 바꾸고 바로 다음 줄에서 `$LASTEXITCODE`를 읽어요. C는 GCC가 설치된 Linux·WSL 터미널을 사용해요. 이 글에서 새 도구를 자동 설치하지는 않아요.

Windows의 현재 압축 해제 폴더에서 이미 설치된 WSL Ubuntu 24.04로 C 예제를 실행하려면 다음 선택 절차를 쓸 수 있어요. 두 변수는 이 명령에서 직접 정의해요.

```powershell
$practicePath = (Get-Location).Path
$wslPractice = wsl -d Ubuntu-24.04 -- wslpath -a "$practicePath"
wsl -d Ubuntu-24.04 --cd "$wslPractice" -- python3 -I -B -X utf8 06-run-examples.py c
$LASTEXITCODE
```

### C의 int 계산과 건너뛰는 반복

일반 예제 파일은 `06-programming-basics.c`예요. `bump()`는 받은 정수에 1을 더해 반환하지만 `number` 자체에 대입하지는 않으므로 호출한 쪽의 5는 그대로 남아요.

```c
#include <stdio.h>

static int bump(int value) {
    return value + 1;
}

int main(void) {
    int denominator = 0;
    int number = 5;
    int total = 0;
    int values[] = {1, 2, 3};
    for (int i = 0; i < 3; ++i) {
        if (values[i] == 2) {
            continue;
        }
        total += values[i];
    }
    printf("division: %d %d\n", -7 / 3, -7 % 3);
    printf("guard: %d\n", denominator != 0 && 12 / denominator > 1);
    printf("value: %d %d\n", number, bump(number));
    printf("total: %d\n", total);
    return 0;
}
```

도우미는 `gcc -std=c11 -Wall -Wextra -Werror`로 컴파일한 뒤 생성한 임시 실행 파일을 시작해요. `-Werror`는 컴파일 경고도 실패로 처리해요. 다음 명령에서 도구 누락이나 컴파일 실패가 나온다면 `gcc`의 PATH와 원래 오류 메시지부터 살펴봐요.

```bash
python3 -I -B -X utf8 06-run-examples.py c
```

[[run:1]]

`denominator`가 0이므로 `denominator != 0`은 거짓이에요. `&&`의 오른쪽인 `12 / denominator > 1`은 실행하지 않아서 0 나눗셈이 생기지 않아요. 출력의 `guard: 0`은 그 논리식의 거짓을 정수로 표시한 값이에요.

반복문에서 `values[1]`의 2를 만나면 `continue`가 덧셈을 건너뛰어요. 인덱스 증가와 다음 조건 검사는 계속되므로 1과 3만 더한 `total: 4`가 나와요. `value: 5 6`의 두 열은 원래 `number`와 `bump(number)`의 반환값이에요.

### Java의 같은 계산과 boolean 출력

파일명 `ProgrammingBasics.java`와 공개 클래스명 `ProgrammingBasics`를 맞춰 주세요. 기본형 `int` 인수는 값이 복사되므로 `bump()`의 반환값과 호출 쪽 변수를 구분해요.

```java
public class ProgrammingBasics {
    static int bump(int value) {
        return value + 1;
    }

    public static void main(String[] args) {
        int denominator = 0;
        int number = 5;
        int total = 0;
        int[] values = {1, 2, 3};
        for (int value : values) {
            if (value == 2) {
                continue;
            }
            total += value;
        }
        System.out.println("division: " + (-7 / 3) + " " + (-7 % 3));
        System.out.println("guard: " + (denominator != 0 && 12 / denominator > 1));
        System.out.println("value: " + number + " " + bump(number));
        System.out.println("total: " + total);
    }
}
```

```bash
python3 -I -B -X utf8 06-run-examples.py java
```

[[run:2]]

몫·나머지와 합계는 C 예제와 같아요. `guard: false`는 Java의 boolean을 출력한 문자열이라 C의 `0`과 표시 형식이 달라요. `for (int value : values)`는 배열의 각 값을 순서대로 읽고 2에서만 덧셈을 건너뛰어요.

### Python의 들여쓰기와 //

`06-programming-basics.py`는 블록을 들여쓰기로 구분해요. C·Java의 정수 `/`와 비교하려고 여기서는 `//`를 사용했어요.

```python
def bump(value):
    return value + 1


def main():
    denominator = 0
    number = 5
    total = 0
    values = [1, 2, 3]
    for value in values:
        if value == 2:
            continue
        total += value
    print("division:", -7 // 3, -7 % 3)
    print("guard:", denominator != 0 and 12 // denominator > 1)
    print("value:", number, bump(number))
    print("total:", total)


if __name__ == "__main__":
    main()
```

```bash
python3 -I -B -X utf8 06-run-examples.py python
```

[[run:3]]

`division: -3 2`의 첫 값은 내림한 몫이고 둘째는 그 몫과 짝을 이루는 나머지예요. `guard: False`는 이 예제의 두 비교식이 bool 값을 만들어서 나온 결과예요. 다만 Python의 `and`가 모든 경우에 bool만 반환하지는 않아요. 왼쪽이 거짓이면 그 피연산자를, 그렇지 않으면 오른쪽의 값을 반환하는 규칙도 [Python boolean 연산 문서](https://docs.python.org/3.12/reference/expressions.html#boolean-operations)에서 함께 살펴봐요.

세 실행의 마지막 완료 문구는 도우미가 선택한 프로그램의 stdout을 기대 문자열과 대조했다는 뜻이에요. 컴파일러와 프로그램의 종료 코드 0·빈 stderr도 요구해요. 도구 누락·컴파일 오류·출력 차이는 도우미의 종료 코드 2로 나타나며 프로그램 하나가 실패하면 완료 문구를 출력하지 않아요.

## 대입과 인수 전달에서 무엇이 바뀌는가

| 읽을 지점 | C11 | Java | Python |
| --- | --- | --- | --- |
| 정수 예제의 변수 | `int` 선언 | `int` 선언 | 이름이 정수 객체에 연결됨 |
| 블록 | 중괄호 | 중괄호 | 들여쓰기 |
| 논리적 단락 평가 | `&&`, `||` | `&&`, `||` | `and`, `or` |
| 이번 `bump()` | 인수의 정수 값과 반환값 구분 | 기본형 인수 값과 반환값 구분 | 함수 안의 이름과 새 정수 반환값 구분 |
| 배열·리스트를 다룰 때 | 포인터·배열의 규칙을 별도로 읽기 | 참조 값의 복사와 객체 변경 구분 | 같은 객체 연결과 복사 구분 |

대입이 항상 새 배열이나 리스트를 만들지는 않아요. Java에서 배열 참조 값을 복사한 인수는 같은 배열을 가리킬 수 있어요. 그 배열의 원소를 바꾸는 것과 매개변수에 새 배열 참조를 대입하는 것은 호출 쪽에 다른 영향을 줘요. 다음 문제에서 [Java 인수 평가와 매개변수 초기화](https://docs.oracle.com/javase/specs/jls/se25/html/jls-15.html#jls-15.12.4.5)의 규칙을 추적해 볼게요.

Python의 `items[:]`는 새 리스트를 만드는 얕은 복사예요. 여기서는 원소가 정수인 한 단계 목록만 사용하므로 중첩된 가변 객체까지 독립적으로 복사했다고 확대하지 않아요. [Python 리스트 복사 설명](https://docs.python.org/3.12/tutorial/datastructures.html#more-on-lists)도 참고할 수 있어요.

## 자체 연습문제 5개

아래 문제는 자체 제작했어요. 각 파일은 독립적으로 실행하며 해설은 해당 문제 바로 아래에 접혀 있어요. C 출력 문제에는 범위를 넘는 정수 연산이나 한 식 안의 모호한 중복 변경을 넣지 않았어요.

### 문제 1. C의 후위 증가를 두 문장으로 나누면

`06-question1.c`의 한 줄 출력은 무엇인가?

```c
#include <stdio.h>

int main(void) {
    int value = 4;
    int before = value++;
    printf("%d %d\n", before, value);
    return 0;
}
```

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 해설 1. 대입에 쓰인 값과 변경 뒤의 값

`4 5`예요. `value++` 식의 값인 4가 `before`에 들어간 뒤 `value`는 5가 돼요. 다음 문장의 `printf()`는 그 두 변수의 현재 값을 읽어요. `printf()`의 인수에서 같은 변수를 여러 번 변경하는 식으로 바꾸면 같은 설명을 그대로 적용할 수는 없어요.

</details>

### 문제 2. Java 배열 원소 변경 뒤에 새 배열을 대입하면

`Question2.java`가 출력하는 값은 무엇인가?

```java
public class Question2 {
    static void change(int[] values) {
        values[0] = 7;
        values = new int[] {9};
    }

    public static void main(String[] args) {
        int[] data = {2};
        change(data);
        System.out.println(data[0]);
    }
}
```

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 해설 2. 같은 배열을 가리키는 동안의 변경

`7`이에요. 호출 직후 `values`에는 `data`와 같은 배열을 가리키는 참조 값이 복사돼요. `values[0] = 7`은 그 배열을 바꿔요. 이후 `values = new int[] {9}`는 함수 안 매개변수만 새 배열로 돌리므로 `data`는 처음 배열을 계속 가리켜요. 이를 Java가 변수 자체를 참조로 전달한다고 설명하지는 않아요.

</details>

### 문제 3. Python의 별명과 얕은 복사

`06-question3.py`의 두 줄 출력은 무엇인가?

```python
items = [1, 2]
alias = items
copied = items[:]
alias.append(5)
copied[0] = 9
print(items)
print(copied)
```

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 해설 3. append가 바꾼 객체

첫째 줄은 `[1, 2, 5]`, 둘째 줄은 `[9, 2]`예요. `alias = items`는 같은 리스트에 다른 이름을 붙이므로 `alias.append(5)`가 `items`에서도 보여요. `copied`는 append 전에 `items[:]`로 만든 별도 리스트라서 첫 원소를 9로 바꿔도 원래 `items`의 첫 원소는 1이에요.

</details>

### 문제 4. C의 continue와 단락 평가

`06-question4.c`의 두 출력 필드는 각각 얼마인가? 0 나눗셈이 실제로 실행되는지도 답하라.

```c
#include <stdio.h>

int main(void) {
    int total = 0;
    int denominator = 0;
    for (int i = 0; i < 7; ++i) {
        if (i % 2 == 0) {
            continue;
        }
        total += i;
    }
    int safe = denominator != 0 && 10 / denominator > 1;
    printf("%d %d\n", total, safe);
    return 0;
}
```

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 해설 4. 더한 반복과 건너뛴 식

`9 0`이에요. `i`가 0·2·4·6일 때는 `continue`가 덧셈을 건너뛰므로 1·3·5만 더해요. `denominator != 0`이 거짓이라 `10 / denominator > 1`은 평가하지 않아요. 두 번째 0은 그 논리식의 결과이며 나눗셈을 실행해서 얻은 0은 아니에요.

</details>

### 문제 5. 정수 범위를 넘긴 식에도 출력 하나가 정해질까

“C의 부호 있는 `int` 덧셈이 범위를 넘으면 Java의 `int` 덧셈처럼 값이 순환하므로, 실행해서 나온 숫자를 정답으로 외우면 된다”는 설명이 맞는가? Python의 정수도 함께 비교하라. 실제 출력값을 요구하는 문제가 아니다.

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 해설 5. 실행 전에 정해야 할 규칙

맞지 않아요. C11에서 표현 범위를 넘는 부호 있는 정수 덧셈은 정의되지 않은 동작이므로 출력 하나를 이식 가능한 정답으로 정하지 않아요. Java의 `int` 덧셈에는 정해진 오버플로 규칙이 있고 Python 정수는 고정 32비트 `int` 범위로 제한하지 않아요. 다만 Python도 메모리 등 실행 자원의 한계는 있어요.

이 비교는 [N1570의 6.5절](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf), [Java 정수 연산 명세](https://docs.oracle.com/javase/specs/jls/se25/html/jls-4.html#jls-4.2.2), [Python 숫자형 문서](https://docs.python.org/3.12/library/stdtypes.html#numeric-types-int-float-complex)를 근거로 해요. 정의되지 않은 C 연산을 실행해서 정답처럼 제시하지는 않았어요.

</details>

## 풀이 파일과 실행 도우미를 대조하려면

문제를 푼 뒤 ZIP의 `06-run-examples.py`에 `--questions`를 붙여요. C는 1·4번, Java는 2번, Python은 3번 파일을 실행해요. 문제 5는 명세를 비교하는 개념 문제예요.

<details class="study-verification">
<summary>문제 검증 명령·전체 도우미·실제 출력 보기</summary>

다음 도우미는 소스 파일을 바꾸지 않아요. `root`는 도우미가 저장된 폴더이고 `run_one()`은 언어별 컴파일·실행을 맡아요. C와 Java의 컴파일 결과는 이번 실행이 만든 임시 폴더에만 놓고 정상·실패 시 그 폴더를 정리해요. Python 실행에는 `-I -B`를 사용해요.

```python
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def require(name):
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"필요한 도구를 찾을 수 없습니다: {name}")
    return executable


def execute(command):
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode != 0 or result.stderr:
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"실행 실패 또는 표준 오류 발생: {Path(command[0]).name}, 종료 {result.returncode}")
    return result.stdout


def run_one(language, source):
    # 컴파일 결과는 이번 실행이 만든 임시 폴더에만 저장한다.
    with tempfile.TemporaryDirectory(prefix="cs06-") as folder:
        work = Path(folder)
        if language == "c":
            binary = work / ("program.exe" if sys.platform == "win32" else "program")
            execute([require("gcc"), "-std=c11", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)])
            return execute([str(binary)])
        if language == "java":
            execute([require("javac"), "-encoding", "UTF-8", "-d", str(work), str(source)])
            return execute([require("java"), "-cp", str(work), source.stem])
        return execute([sys.executable, "-I", "-B", "-X", "utf8", str(source)])


def main():
    parser = argparse.ArgumentParser(description="묶음에 포함된 작은 예제를 실행하고 기대값과 대조한다")
    parser.add_argument("language", choices=("c", "java", "python"))
    parser.add_argument("--questions", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    demos = {
        "c": [("06-programming-basics.c", "division: -2 -1\nguard: 0\nvalue: 5 6\ntotal: 4\n")],
        "java": [("ProgrammingBasics.java", "division: -2 -1\nguard: false\nvalue: 5 6\ntotal: 4\n")],
        "python": [("06-programming-basics.py", "division: -3 2\nguard: False\nvalue: 5 6\ntotal: 4\n")],
    }
    questions = {
        "c": [("06-question1.c", "4 5\n"), ("06-question4.c", "9 0\n")],
        "java": [("Question2.java", "7\n")],
        "python": [("06-question3.py", "[1, 2, 5]\n[9, 2]\n")],
    }
    completed = []
    try:
        for name, expected in (questions if args.questions else demos)[args.language]:
            actual = run_one(args.language, root / name)
            if actual != expected:
                raise RuntimeError(f"기대 출력과 다릅니다: {name}")
            completed.append((name, actual))
    except (OSError, RuntimeError, subprocess.TimeoutExpired, UnicodeError) as error:
        print(f"실행 오류: {error}", file=sys.stderr)
        return 2
    for name, output in completed:
        print(f"파일: {name}")
        print(output, end="")
    print(f"예제 {len(completed)}건 기대값 대조 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`execute()`는 종료 코드와 stderr를 모두 검사해요. `completed`에는 기대 출력과 일치한 결과만 모은 뒤 선택한 묶음이 모두 끝나야 출력해요. 컴파일 오류의 원래 stderr는 숨기지 않아요. 이 파일의 기대 문자열에는 문제의 풀이가 포함돼 있어 처음에는 접어 두었어요.

```bash
python3 -I -B -X utf8 06-run-examples.py c --questions
```

[[run:4]]

C의 두 파일을 따로 컴파일해 두 문제의 출력이 각각 맞는지 비교했어요. ‘2건’은 두 실행 파일의 기대 출력 대조 수예요.

```bash
python3 -I -B -X utf8 06-run-examples.py java --questions
```

[[run:5]]

배열 참조를 다룬 파일 하나의 출력과 종료 상태를 대조했어요. 일반 Java 예제의 상태를 이어받지는 않아요.

```bash
python3 -I -B -X utf8 06-run-examples.py python --questions
```

[[run:6]]

리스트 두 줄의 값과 순서를 함께 비교했어요. 도우미가 출력하는 완료 문구는 각 언어의 기대값 대조이며 문제 5의 명세 비교까지 실행으로 증명한 것은 아니에요. 소스 파일과 ZIP은 그대로 남고 컴파일용 임시 파일은 정리됐어요.

</details>

## 시험 직전 복습

- 식을 읽기 전에 언어·자료형·연산자를 적어 봐요. C·Java 정수 `/`와 Python `//`는 음수에서 몫이 다를 수 있어요.
- 단락 평가에서 오른쪽 식을 실제로 실행했는지 구분해요. 출력의 거짓과 계산 결과 0은 혼동하지 않아요.
- `continue` 뒤의 문장만 건너뛰는지, 반복 전체를 끝내는지 따라가요.
- 함수의 반환값, 호출 쪽 변수, 매개변수가 가리키는 객체의 변경을 따로 기록해요.
- 별명과 얕은 복사, 원소 변경과 새 객체 대입을 구분해요.
- 범위 초과·정의되지 않은 동작이 있으면 한 번 실행한 출력으로 언어 규칙을 정하지 않아요.
