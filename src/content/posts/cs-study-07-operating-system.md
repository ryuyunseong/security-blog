---
title: "운영체제: 프로세스의 메모리, 페이지 주소와 교착상태"
description: "프로세스와 스레드의 변수 변경을 실행하고, 페이지 주소 변환과 자원 대기 순환을 작은 모형으로 추적합니다. 자체 문제 5개와 접힌 해설을 제공합니다."
date: "2026-10-27T18:46:03+09:00"
sourcesChecked: "2026-10-27"
category: "cs-study"
tags: ["전산", "NCS", "운영체제", "프로세스", "스레드", "가상 메모리", "교착상태"]
draft: false
example: false
---

실행 중인 작업이 멈춰 보일 때는 CPU 차례를 기다리는지, 입력 완료를 기다리는지, 다른 작업이 잡은 자원을 기다리는지부터 나눠 본다. 같은 ‘대기’라도 다음에 실행될 조건이 다르다. 메모리도 변수 이름만 보고 공유 여부를 판단하지 않고 어느 프로세스의 주소 공간에 있는지 살핀다.

이번에는 프로세스·스레드의 실제 변수 변경을 짧게 실행한 뒤 주소 변환과 교착상태를 별도의 모형으로 계산한다. 예제와 문제는 자체 제작했으며 실제 페이지 테이블이나 커널의 대기 상태를 수집하지 않는다.

## 실행할 수 있는 상태와 사건을 기다리는 상태

실행 준비 상태는 CPU를 배정받으면 진행할 수 있는 상태다. 입출력 완료나 사용 중인 락을 기다리는 작업은 그 사건이 해결돼야 다시 실행할 수 있다. 입출력이 끝나도 곧바로 CPU를 얻는다고 단정하지 않고 실행 준비로 돌아간 뒤의 스케줄링을 구분한다.

프로세스는 실행 중인 프로그램과 그 자원 관리 단위이며 스레드는 그 안의 실행 흐름이다. 일반적으로 프로세스마다 별도의 가상 주소 공간이 있고 같은 프로세스의 스레드는 데이터·힙 같은 메모리를 공유한다. 각 스레드의 실행 위치·레지스터·스택은 따로 관리한다. 다른 스레드가 그 스택의 주소에 절대로 접근할 수 없다는 뜻은 아니다. [Linux pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)은 공유하는 속성과 스레드별 속성을 나눠 설명한다.

프로세스 사이에서도 공유 메모리나 파일 등으로 자료를 주고받을 수 있다. 별도의 주소 공간이라는 설명을 ‘어떤 자료도 공유할 수 없다’로 외우지 않는다.

## 같은 1에서 시작한 값이 달라지는 실행

Python 3.9 이상과 표준 라이브러리를 사용한다. 실제 검증 환경은 Windows Python 3.12.1이다. ZIP을 빈 폴더에 풀고 `07-os-examples.py`가 있는 폴더에서 실행한다. 문제 검증 파일 `07-os-questions.py`도 같은 폴더에 둔다. 서버·계정·관리자 권한이나 별도의 입력 파일은 필요하지 않다.

[[download]]

```bash
python -I -B -X utf8 07-os-examples.py sharing
```

Linux·WSL에서는 `python3`로 실행해도 된다. PowerShell에서는 바로 다음 줄에서 `$LASTEXITCODE`, Bash에서는 `echo $?`를 읽는다. `-I -B`는 격리된 Python 실행과 바이트코드 파일 생성 억제에 사용한다.

다음은 일반 예제 파일 전체다. `sharing`만 실제 자식 프로세스와 두 작업 스레드를 만들며 `paging`·`waiting`은 메모리 안의 자료를 계산한다.

```python
import argparse
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
from threading import Barrier, Lock


def sharing():
    value = [1]
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-X", "utf8", "-c", "value = 1; value += 100; print(value)"],
        capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    if result.returncode != 0 or result.stderr:
        raise RuntimeError("자식 프로세스가 정상적으로 끝나지 않았다")
    child = int(result.stdout.strip())
    parent = value[0]
    lock = Lock()
    ready = Barrier(2)

    def increase():
        ready.wait(timeout=10)
        for _ in range(2):
            with lock:
                value[0] += 1

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(increase) for _ in range(2)]
        for job in jobs:
            job.result()
    assert (parent, child, value[0]) == (1, 101, 5)
    print(f"별도 프로세스: parent={parent} child={child}")
    print(f"같은 프로세스의 스레드: shared={value[0]}")


def translate(address, page_size, table):
    if type(address) is not int or address < 0 or type(page_size) is not int or page_size <= 0:
        raise ValueError("주소는 음이 아닌 정수, 페이지 크기는 양의 정수여야 한다")
    page, offset = divmod(address, page_size)
    if page not in table:
        return page, offset, None, "unmapped"
    frame = table[page]
    if frame is None:
        return page, offset, None, "not_present"
    if type(frame) is not int or frame < 0:
        raise ValueError("프레임 번호는 음이 아닌 정수여야 한다")
    return page, offset, frame * page_size + offset, "mapped"


def paging():
    table = {2: 9, 3: None}
    for address in (8195, 12288, 16384):
        page, offset, physical, state = translate(address, 4096, table)
        print(f"{state}: page={page} offset={offset} physical={physical}")


def wait_cycle(wait_for):
    for start in sorted(wait_for):
        seen, path = {}, []
        current = start
        while current is not None:
            if current in seen:
                return path[seen[current]:] + [current]
            seen[current] = len(path)
            path.append(current)
            current = wait_for.get(current)
    return []


def waiting():
    before = wait_cycle({"A": "B", "B": "A"})
    after = wait_cycle({"A": "B", "B": None})
    assert before == ["A", "B", "A"] and after == []
    print("대기 순환: " + " -> ".join(before))
    print("순환 해제 모형: " + (" -> ".join(after) if after else "없음"))


def main():
    parser = argparse.ArgumentParser(description="작은 프로세스·스레드 실험과 메모리·대기 관계 모형")
    parser.add_argument("example", choices=("sharing", "paging", "waiting"))
    args = parser.parse_args()
    try:
        {"sharing": sharing, "paging": paging, "waiting": waiting}[args.example]()
    except (OSError, ValueError, RuntimeError, AssertionError, subprocess.TimeoutExpired) as error:
        print(f"실행 오류: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`sharing()`에서 부모의 `value`는 `[1]`이다. `subprocess.run()`은 새 Python 인터프리터에 `value = 1`을 별도로 정의한 명령을 보낸다. 자식이 100을 더해 101을 출력해도 부모의 리스트는 1이다. 이 과정은 fork로 부모 메모리의 복사 시점을 관찰한 실험이 아니다.

이어 두 `increase()` 작업은 부모의 같은 리스트를 사용한다. `Barrier(2)`는 두 작업 스레드가 시작 지점에 도착하도록 맞추며 `Lock`은 덧셈 구간을 한 번에 하나만 수행하게 한다. 두 작업이 각각 두 번 더하므로 최종값은 `1 + 2 + 2`다. 실행 순서나 CPU 병렬 속도를 측정한 코드는 아니다. CPython 3.12의 GIL 조건도 [threading 문서](https://docs.python.org/3.12/library/threading.html)에 설명돼 있다.

[[run:1]]

`parent=1`·`child=101`은 별도 인터프리터의 값이며 `shared=5`는 같은 프로세스의 공유 리스트를 변경한 결과다. `pool.submit()`이 돌려준 `Future`에 `job.result()`를 호출하므로 작업 안의 예외도 호출 쪽으로 전달된다. [Future.result() 문서](https://docs.python.org/3.12/library/concurrent.futures.html#concurrent.futures.Future.result)에서 이 동작을 대조할 수 있다.

자식은 종료까지 기다리고 풀의 `with`를 벗어날 때 작업 스레드를 정리한다. 결과 파일이나 네트워크 연결은 만들지 않는다. 일반 예제는 시작 실패·10초 자식 제한 시간 초과·모형 값 오류 등을 처리해 stderr에 오류를 남기고 종료 2로 끝난다. 성공한 실행은 종료 0·빈 stderr였다.

## 가상 주소 8195는 물리 주소 8195와 다르다

페이지 크기를 **4096바이트**로 가정하면 가상 주소 8195는 페이지 번호 2와 페이지 안의 변위 3으로 나뉜다. 이 프로세스의 페이지 2가 물리 프레임 9에 연결됐다고 두면 물리 주소는 `9 * 4096 + 3`이다. 변위는 그대로 두고 페이지 번호를 프레임 번호로 바꾼다.

[[diagram]]

실제 운영체제는 권한 비트·여러 단계의 페이지 테이블·TLB 등을 함께 사용한다. [Linux 페이지 테이블 문서](https://docs.kernel.org/mm/page_tables.html)의 설명과 구분해 여기서는 한 단계 사전으로 필요한 산술만 표현했다.

```bash
python -I -B -X utf8 07-os-examples.py paging
```

`translate()`는 `divmod(address, page_size)`로 페이지와 변위를 얻는다. `table = {2: 9, 3: None}`에서 2는 프레임 9에 연결돼 있고 3은 유효한 영역이지만 아직 프레임이 없다는 가정이다. 사전에 없는 페이지는 이 모형에서 아예 매핑하지 않은 영역으로 구분한다.

[[run:2]]

첫 행의 `physical=36867`은 프레임 9의 시작 36864에 변위 3을 더한 값이다. 둘째 행은 페이지 3의 프레임이 `None`인 `not_present`, 셋째 행은 페이지 4가 사전에 없는 `unmapped`다. 두 경우 모두 이 모형은 물리 주소를 만들지 않아 `None`을 출력한다. 숫자 0을 뜻하지 않는다.

실제 페이지 폴트에는 물리 메모리에 데이터가 없는 경우 외에도 접근 권한 위반 등이 있다. 지연 할당·쓰기 시 복사·스왑 등 원인도 구분한다. TLB에 번역이 없다는 캐시 미스와 페이지 폴트를 같은 사건으로 보지 않는다. 여기서 출력한 `not_present`는 커널이 실제로 페이지 폴트를 발생시켰다는 기록이 아니다.

## 누가 가진 자원을 기다리는지 연결하기

작업 A가 락 L1을 잡고 L2를 기다리고 B는 L2를 잡고 L1을 기다린다고 두자. 두 락은 각각 하나뿐이며 배타적으로 사용한다. 잡은 락을 기다리는 동안 유지하고 외부에서 빼앗지 않는 조건이면 두 작업이 서로 진행을 막는다.

이 교착상태의 네 조건은 상호 배제, 점유하며 대기, 비선점, 순환 대기다. 예방은 그중 한 조건이 성립하지 않게 하는 방법이며, 안전 상태를 검사하는 회피나 발생 후 탐지·복구와 구분한다. [OSTEP의 동시성 문제 장](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-deadlock.pdf)은 락 획득 순서를 통일해 순환을 막는 예를 설명한다.

`wait_cycle()`의 사전은 작업에서 **현재 기다리는 자원의 소유 작업**으로 향하는 연결이다. `{"A": "B", "B": "A"}`를 따라가면 `A -> B -> A`가 된다. `seen`은 이번 경로에서 방문한 위치를 저장하고 같은 작업을 다시 만나면 그 위치부터 순환을 잘라 반환한다.

```bash
python -I -B -X utf8 07-os-examples.py waiting
```

락 획득 순서를 모두 L1 다음 L2로 맞춘 상황을 `{"A": "B", "B": None}`로 표현했다. 이 예에서는 B가 L1을 가진 상태로 L2까지 사용하고 있고 A는 아직 L1을 얻지 못해 기다린다. B가 추가 자원을 기다리지 않고 끝낼 수 있는 상태라 순환이 끊긴다.

[[run:3]]

둘째 행의 ‘없음’은 주어진 사전에서 순환을 찾지 못했다는 뜻이다. 실제로 락을 걸어 교착을 만들거나 운영체제가 이를 해제한 실험은 하지 않았다. 자원마다 여러 인스턴스가 있는 일반 상황까지 이 단일 대기 연결 모형의 판정을 확대하지 않는다. 기아는 특정 작업이 계속 선택되지 못하는 문제로, 이 예의 자원 대기 순환과도 구분한다.

## 자체 연습문제 5개

각 문제는 독립된 입력을 사용하며 해설은 바로 아래에 접혀 있다.

### 문제 1. 입출력이 끝나기 전과 후

어떤 스레드가 디스크 읽기 완료를 기다린다. CPU만 즉시 배정하면 계속 실행할 수 있는가? 읽기가 완료되면 반드시 그 순간 실행되는지도 설명하라.

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 해설 1. 기다리는 사건과 실행 준비

읽기 완료가 필요한 동안은 CPU 차례만 얻어서는 해당 작업을 계속할 수 없다. 입출력이 끝나면 실행 준비 상태로 돌아갈 수 있으며 실제 CPU 배정은 스케줄러의 정책과 다른 실행 준비 작업에 따라 달라진다. 사건 완료와 즉시 실행을 구분한다.

</details>

### 문제 2. 다른 가상 주소의 변환

위의 `translate()`에 주소 12345, 페이지 크기 4096, 사전 `{3: 12}`를 전달하면 페이지 번호·변위·물리 주소는 각각 얼마인가? 주소 단위는 바이트다.

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 해설 2. 페이지를 바꿔도 변위는 유지

`12345 = 3 * 4096 + 57`이므로 페이지는 3, 변위는 57이다. 사전의 프레임 번호가 12이므로 물리 주소는 `12 * 4096 + 57 = 49209`다. 함수 반환값은 `(3, 57, 49209, "mapped")`다. 프레임 12를 물리 주소 12로 바로 사용하는 계산은 페이지 크기를 빠뜨린 것이다.

</details>

### 문제 3. 프레임이 없는 페이지

주소 8192와 페이지 크기 4096, 사전 `{2: None}`을 `translate()`에 전달했다. 물리 주소가 0으로 반환되는가? 이 출력만으로 실제 스왑 입출력이 일어났다고 말할 수 있는지도 답하라.

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 해설 3. 주소 미생성과 숫자 0

페이지 2와 변위 0까지는 계산하지만 프레임이 `None`이므로 물리 주소도 `None`, 상태는 `"not_present"`다. `0 * 4096 + 0`을 계산한 결과가 아니다. 이 함수는 메모리의 사전만 읽으므로 커널의 페이지 폴트나 스왑 입출력을 관찰하지 않았다.

</details>

### 문제 4. 끝나는 대기 연결

자원은 각각 하나이며 `wait_cycle({"A": "B", "B": "C", "C": None})`를 실행한다. 반환값과 그 값으로 말할 수 있는 범위를 설명하라. C는 추가 자원 없이 작업을 끝내고 가진 자원을 반납할 수 있다고 가정한다.

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 해설 4. 순환 없이 끝나는 경로

빈 리스트 `[]`다. A에서 B, C를 지난 다음 `None`에서 반복을 끝낸다. 이 연결에는 순환이 없으며 C의 완료 후 B, A가 진행할 수 있는 조건이다. 모든 작업이 즉시 실행된다거나 실제 시스템의 모든 자원을 조사했다는 결론은 포함하지 않는다.

</details>

### 문제 5. 락 순서 통일의 목적

단일 락 M·N을 사용하며 P는 M을 잡고 N을, Q는 N을 잡고 M을 기다린다. 이 관계를 함수 입력으로 쓰고 반환되는 순환을 적어라. 모든 작업이 M 다음 N 순서로 얻도록 바꿀 때 주로 막는 조건도 설명하라.

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 해설 5. 같은 락을 먼저 요구하게 하기

`{"P": "Q", "Q": "P"}`이며 반환값은 `["P", "Q", "P"]`다. 일관된 획득 순서는 순환 대기를 막는다. 예를 들어 Q가 M·N을 사용하고 P가 M을 기다리는 동안 Q는 P가 잡은 다른 락을 기다리지 않는다. 이 순간을 `{"P": "Q", "Q": None}`로 표현하면 반환값은 `[]`다. 이미 교착된 실제 작업을 코드가 강제로 복구했다는 뜻은 아니다.

</details>

## 문제의 계산을 별도로 실행하기

문제를 푼 뒤 같은 압축 해제 폴더에서 검증 파일을 실행한다. 문제 1은 상태 전이에 관한 개념 해설이며 나머지 네 문제의 모형 값만 코드로 대조한다.

<details class="study-verification">
<summary>문제 검증 전체 코드·명령·출력 보기</summary>

`07-os-questions.py`의 전체 코드다. `runpy.run_path()`는 같은 폴더의 일반 예제 파일에서 함수를 읽는다. 이 호출의 실행 이름은 `__main__`이 아니므로 일반 예제의 CLI는 시작하지 않는다. `-I`로 실행하므로 일반적인 같은 폴더 모듈 탐색에 기대지 않고 정확한 파일 경로를 구성했다.

```python
from pathlib import Path
import runpy


def main():
    namespace = runpy.run_path(str(Path(__file__).resolve().with_name("07-os-examples.py")))
    translate = namespace["translate"]
    wait_cycle = namespace["wait_cycle"]
    answer2 = translate(12345, 4096, {3: 12})
    assert answer2 == (3, 57, 49209, "mapped")
    answer3 = translate(8192, 4096, {2: None})
    assert answer3 == (2, 0, None, "not_present")
    answer4 = wait_cycle({"A": "B", "B": "C", "C": None})
    assert answer4 == []
    answer5 = wait_cycle({"P": "Q", "Q": "P"})
    ordered = wait_cycle({"P": "Q", "Q": None})
    assert answer5 == ["P", "Q", "P"] and ordered == []
    print(f"q2: {answer2}")
    print(f"q3: {answer3}")
    print(f"q4: {answer4}")
    print(f"q5: {answer5}, 순서 통일 모형={ordered}")
    print("문제 2~5의 모형 값 대조 완료")


if __name__ == "__main__":
    main()
```

```bash
python -I -B -X utf8 07-os-questions.py
```

`answer2`·`answer3`은 서로 다른 새 사전으로 주소를 계산하고 `answer4`·`answer5`·`ordered`도 각자의 연결을 사용한다. 다른 문제에서 변경한 자료를 이어받지 않는다.

[[run:4]]

튜플의 앞 두 값은 페이지와 변위이고 세 번째가 물리 주소, 마지막이 모형의 상태 문자열이다. q4의 빈 리스트와 q5의 두 리스트는 각각 찾은 순환을 담는다. 마지막 완료 문구와 종료 0은 네 문제의 반환값이 `assert`의 기대값과 일치한 결과다. 이 검증 파일은 파일 누락·기대값 차이로 생긴 예외를 그대로 출력하고 종료 1로 끝난다. 이때는 두 파일의 위치와 첫 오류를 살핀다. 일반 예제의 처리된 오류 종료 2와 구분한다.

</details>

## 시험 직전 복습

- 실행 준비와 입출력·락 대기를 구분한다. 사건 완료 뒤에도 CPU 배정 절차가 있다.
- 같은 프로세스의 스레드는 주소 공간을 공유하면서 각자의 실행 문맥을 갖는다. 프로세스 간 명시적 공유도 가능하다.
- 가상 주소를 페이지 번호와 변위로 나눈 뒤 프레임 번호에 페이지 크기를 곱한다. 주소·크기의 단위를 맞춘다.
- TLB 미스, 페이지 폴트, 스왑 입출력은 같은 표현이 아니다. `None`은 숫자 0과 다르다.
- 교착의 네 조건, 획득 순서를 통한 예방, 안전 상태를 보는 회피, 탐지·복구를 구분한다.
- 모형의 순환 판정과 실제 락 실행, 기아와 교착상태를 섞어 설명하지 않는다.
