---
title: "소프트웨어공학: 요구조건을 상태와 테스트 사례로 바꾸기"
description: "개발 생명주기와 UML의 역할을 구분하고 가상 배송비의 경계값과 주문 상태 전이를 코드·실제 출력으로 대조합니다."
date: "2026-10-29T18:46:57+09:00"
sourcesChecked: "2026-10-29"
category: cs-study
tags: ["전산", "소프트웨어공학", "UML", "테스트", "경계값"]
draft: false
---

‘5만원부터 배송비 무료’라는 요구조건은 금액 50000을 무료 구간에 넣는다. 구현이 `amount > 50000`을 쓰면 60000에서는 정상으로 보이다가 정확히 50000에서 다른 결과를 낸다. 개발 과정에서 요구조건을 문장으로 합의하고 설계로 나누고 실행 사례로 대조하는 일이 연결되는 지점이다.

이번 예제는 정수 금액과 문자열 상태만 계산한다. 실제 주문·결제·배송 서버를 연결하지 않는다. 생명주기 모델과 UML은 이 계산을 언제 검토하고 무엇을 표현할지 설명하는 데 사용한다.

## 개발 순서를 고르는 일과 산출물을 검사하는 일

개발 생명주기(SDLC)는 요구 분석, 설계, 구현, 테스트, 배포와 유지보수 같은 활동을 조직하는 방식이다. [ISTQB CTFL v4.0.1](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf)의 2장은 순차 모델과 반복·점증 모델에 따라 테스트 활동을 배치하는 방법을 설명한다.

| 접근 | 작업을 나누는 관점 | 검토할 질문 |
| --- | --- | --- |
| 순차 개발 | 앞 단계 산출물을 바탕으로 뒤 단계를 진행 | 요구조건과 설계가 구현·테스트로 이어지는가 |
| 반복 개발 | 같은 대상을 여러 차례 다듬음 | 이번 반복에서 얻은 결과로 무엇을 수정하는가 |
| 점증 개발 | 사용할 기능 범위를 나눠 늘림 | 이번 증가분이 기존 기능과 함께 동작하는가 |

반복과 점증은 함께 사용할 수 있다. ‘폭포수’는 순차 개발의 대표적인 설명이고 V 모델은 명세·설계 수준에 대응하는 테스트 관점을 함께 놓는다. 단계 이름을 외울 때 테스트를 구현이 끝난 뒤 처음 생각하는 활동으로 제한하지 않는다. 요구서 검토와 설계 검토는 코드를 실행하지 않는 정적 테스트에 해당할 수 있다.

[애자일 선언의 원칙](https://agilemanifesto.org/principles.html)은 동작하는 소프트웨어의 잦은 전달과 변화하는 요구 수용을 다룬다. 문서나 설계를 생략한다는 뜻으로 적용하지 않는다. 보안 검토도 개발 모델에 맞춰 배치해야 하며 [NIST SSDF v1.1](https://csrc.nist.gov/pubs/sp/800/218/final)은 여러 SDLC 구현에 통합할 보안 실무를 제시한다.

## UML에서는 관계와 사건을 나눠 표현한다

UML은 개발 일정이나 특정 방법론이 아니라 모델을 표현하는 언어다. [OMG UML 2.5.1](https://www.omg.org/spec/UML/2.5.1/PDF)에서 클래스·연관은 구조를, 상태 기계·상호작용은 동작을 표현한다. 같은 주문 시스템이라도 필요한 질문에 따라 다른 도식을 고른다.

- 클래스 다이어그램: 고객·주문 같은 타입, 속성, 연관과 다중도.
- 유스케이스 다이어그램: 외부 액터가 시스템에서 수행하려는 기능과 시스템 경계.
- 시퀀스 다이어그램: 참여자 사이의 메시지 교환 순서.
- 상태 다이어그램: 객체가 현재 상태와 사건에 따라 어느 상태로 전이하는가.

예를 들어 고객과 주문의 연관에서 고객 쪽 끝에 `1`, 주문 쪽 끝에 `0..*`가 붙으면 주문 하나는 고객 하나와 연결되고 고객 하나는 주문이 없거나 여러 개일 수 있다. 화살표 방향만 보고 이 수를 뒤집어 읽지 않는다. 단순 연관만으로 객체가 함께 소멸하는 합성 관계까지 주장할 수도 없다.

아래 가상 주문은 `DRAFT`에서 결제하면 `PAID`, 결제된 주문을 배송하면 `SHIPPED`가 된다. 취소는 `DRAFT`와 `PAID`에서만 허용한다고 정했다. 이는 학습 예제의 규칙이며 실제 주문 시스템의 취소 정책을 대신하지 않는다.

| 현재 상태 | 사건 | 다음 상태 |
| --- | --- | --- |
| `DRAFT` | `pay` | `PAID` |
| `DRAFT` | `cancel` | `CANCELLED` |
| `PAID` | `ship` | `SHIPPED` |
| `PAID` | `cancel` | `CANCELLED` |

표에 없는 전이는 오류로 거부한다. 상태 다이어그램으로 옮기면 상태가 정점, 사건에 따른 전이가 연결이 된다. 조건이 필요한 전이에는 가드를 함께 적는다. 여기서는 순수 함수가 다음 상태 문자열을 반환하므로 저장·동시성·결제 실패 복구 같은 기능은 구현하지 않는다.

## 배송비 규칙의 경계와 상태 전이를 실행하기

가상 금액은 원 단위 정수이며 허용 범위는 0~100000이다. 50000 이상이면 배송비 0, 그 미만이면 3000으로 정했다. 숫자처럼 보이는 문자열과 불리언도 받지 않는다. 입력 구간을 나눠 사례를 고르는 동등 분할과 구간이 바뀌는 지점을 고르는 경계값 분석은 CTFL 4.2절의 블랙박스 테스트 기법이다.

[[diagram]]

Python 3.9 이상과 표준 라이브러리만 사용하며 Windows Python 3.12.1에서 검증했다. ZIP을 빈 폴더에 풀고 `09-shipping-rules.py`, `09-software-questions.py`가 함께 있는 폴더에서 아래 명령을 실행한다. 입력 값은 코드에 있으므로 별도 파일·DB·계정·서버·관리자 권한이 필요하지 않다.

[[download]]

```bash
python -I -B -X utf8 09-shipping-rules.py fees
python -I -B -X utf8 09-shipping-rules.py states
```

PowerShell에서는 각 명령 직후 `$LASTEXITCODE`, Bash에서는 `echo $?`로 종료 코드를 읽는다. Linux·WSL에서는 `python3`로 바꿀 수 있다. 예제는 파일을 생성하거나 기존 자료를 수정하지 않으며 정리할 서버·임시 계정도 없다.

다음 전체 코드는 두 명령이 사용하는 함수와 출력 부분을 함께 담고 있다.

```python
import argparse


def shipping_fee(amount):
    if type(amount) is not int:
        raise TypeError("금액은 정수여야 한다")
    if not 0 <= amount <= 100000:
        raise ValueError("금액 범위는 0~100000이다")
    return 0 if amount >= 50000 else 3000


def transition(state, event):
    edges = {
        ("DRAFT", "pay"): "PAID",
        ("DRAFT", "cancel"): "CANCELLED",
        ("PAID", "ship"): "SHIPPED",
        ("PAID", "cancel"): "CANCELLED",
    }
    if (state, event) not in edges:
        raise ValueError("허용하지 않은 상태 전이")
    return edges[state, event]


def main():
    parser = argparse.ArgumentParser(description="가상 배송비와 주문 상태를 계산한다")
    parser.add_argument("example", choices=("fees", "states"))
    args = parser.parse_args()
    if args.example == "fees":
        for amount in (-1, 0, 49999, 50000, 100000, 100001):
            try:
                print(f"금액={amount}, 배송비={shipping_fee(amount)}")
            except ValueError as error:
                print(f"금액={amount}, 예상한 거부: {error}")
    else:
        state = "DRAFT"
        for event in ("pay", "ship", "cancel"):
            try:
                after = transition(state, event)
                print(f"{state} + {event} -> {after}")
                state = after
            except ValueError as error:
                print(f"{state} + {event} -> 예상한 거부: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`shipping_fee(49999)`는 `type(amount) is int`와 범위 검사를 지나 `amount >= 50000`에서 거짓이 되어 3000을 반환한다. 50000은 같은 비교에서 참이므로 0을 반환한다. Python에서 `bool`은 `int`의 하위 타입이지만 여기서는 `type(...) is int`로 `True`를 금액으로 받지 않는다.

[[run:1]]

금액 0과 100000은 허용 범위의 양 끝이다. -1과 100001은 범위 밖이라 `ValueError`를 만들고 `main()`이 이를 잡아 ‘예상한 거부’로 출력했다. 이 두 입력이 배송비 계산에 허용됐다는 뜻은 아니다. 종료 0은 준비된 사례를 끝까지 실행했다는 뜻이다. 코드 오류로 처리하지 않은 예외가 나오면 프로그램은 실패하며 표준 오류도 남는다.

`transition()`의 `edges`는 `(현재 상태, 사건)` 튜플을 키로 삼는다. `main()`의 `state`는 처음 `DRAFT`이고 `pay`를 넣어 얻은 `after`를 다시 대입한다. 다음 `ship`이 `PAID`와 함께 조회되므로 `SHIPPED`가 된다. 마지막 `cancel`은 표에 없어 예외가 발생하고 대입문까지 도달하지 않는다.

[[run:2]]

마지막 줄의 거부 뒤에도 `state`는 `SHIPPED`다. 함수가 상태를 외부 저장소에서 바꾸는 것이 아니라 반환한 문자열을 호출자가 대입하는 구조라서 이 순서를 코드에서 따라갈 수 있다.

## 테스트 수준, 종류와 재실행 목적

컴포넌트 테스트는 함수·모듈 같은 개별 단위에, 통합 테스트는 단위 또는 시스템 사이의 상호작용에 초점을 둔다. 시스템 테스트는 시스템 전체의 동작을 다루고 인수 테스트는 사용자·업무 요구 수용을 살핀다. 한편 기능 테스트와 성능·사용성 같은 비기능 테스트는 테스트 대상의 특성에 따른 구분이다. 수준과 종류를 같은 축으로 나열하지 않는다.

확인 테스트와 회귀 테스트는 목적이 다르다. 확인 테스트는 수정한 오류가 사라졌는지 다시 본다. 회귀 테스트는 그 수정이 다른 부분에 부작용을 냈는지 본다. 무료 경계를 `>`에서 `>=`로 고쳤다면 50000을 다시 실행하는 것은 수정 확인에 쓰이고 기존 유료 구간과 입력 거부·상태 계산도 다시 비교하는 것은 회귀 범위가 된다.

문장·분기 커버리지는 선택한 코드 범위에서 무엇이 실행됐는지 나타낸다. 요구조건의 정확성, 빠뜨린 요구, 실행하지 않은 입력까지 보증하지 않는다. 블랙박스 사례로 49999와 50000을 고른 뒤 코드의 예외 분기까지 살피는 식으로 서로 다른 관점을 함께 쓸 수 있다.

## 자체 연습문제 5개

### 문제 1. 요구조건이 계속 바뀌는 기능

작은 기능을 전달한 뒤 사용자 피드백으로 같은 기능을 다듬고 다음 기능을 추가하려 한다. 반복과 점증 중 어느 관점이 각각 드러나는가? 이 방식이면 요구서 검토를 생략해도 되는가?

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 문제 1 해설

같은 기능을 피드백으로 수정하는 부분은 반복이고 사용할 기능을 더하는 부분은 점증이다. 두 관점은 함께 나타날 수 있다. 요구서와 설계를 검토해 해석 차이를 줄이는 활동은 계속 필요하다. 애자일의 변화 수용을 문서·정적 검토의 생략으로 바꾸지 않는다.

</details>

### 문제 2. 연관 끝의 다중도

고객과 주문이 연결되어 있다. 고객 쪽 끝에는 `1`, 주문 쪽 끝에는 `0..*`가 적혀 있다. 고객 한 명의 주문 수와 주문 하나의 고객 수를 각각 쓰라. 이 표시만으로 고객 삭제 시 주문도 반드시 삭제된다고 말할 수 있는가?

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 문제 2 해설

고객 하나에 주문은 0개 이상, 주문 하나에 고객은 정확히 1명이다. 고객에서 바라본 주문 수는 반대쪽인 주문 끝의 `0..*`로 읽는다. 다중도는 연결 가능한 수를 나타내며 이 표시만으로 합성 관계나 삭제 정책을 확정할 수 없다.

</details>

### 문제 3. 무료 구간의 경계 세 값

`shipping_fee()`에 49999, 50000, 50001을 차례로 넣으면 무엇을 반환하는가? 비교를 `>`로 잘못 바꿨을 때 세 사례 중 어느 값이 오류를 드러내는가?

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 문제 3 해설

반환값은 `[3000, 0, 0]`이다. 49999는 무료 구간 아래이고 50000과 50001은 `>= 50000`을 만족한다. `>`로 바꾸면 정확히 50000만 조건에서 빠져 3000을 반환한다. 경계 양옆뿐 아니라 경계 자체를 넣는 이유가 이 사례에서 드러난다.

</details>

### 문제 4. 취소 뒤 결제 요청

현재 상태가 `DRAFT`일 때 `cancel`을 처리하고 그 반환값을 현재 상태에 대입했다. 이어 `pay`를 넣으면 어떤 결과가 생기는가? 이 예외를 잡았다고 결제가 처리됐다고 써도 되는가?

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 문제 4 해설

첫 조회의 키 `("DRAFT", "cancel")`은 `CANCELLED`를 반환한다. 다음 키 `("CANCELLED", "pay")`는 `edges`에 없어 `ValueError`가 발생한다. 호출자가 예외를 잡은 것은 거부 동작을 다뤘다는 뜻이며 결제 성공은 아니다. 상태를 바꾸는 새 대입이 없으므로 직전 `CANCELLED`를 유지한다.

</details>

### 문제 5. 정상 출력 두 개로 검증 범위를 정하면

10000과 60000을 넣어 유료·무료 출력을 모두 얻었다. 이를 근거로 잘못된 금액도 모두 거부한다고 결론 내릴 수 있는가? -1을 추가하면 어느 분기를 실행하며 어떤 값이 반환되는가?

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 문제 5 해설

두 정상 금액은 배송비를 고르는 조건의 양쪽 결과만 살핀다. 타입 오류와 범위 오류를 일으키는 입력은 따로 실행하지 않았다. -1은 정수 검사를 지나지만 범위 검사에서 `ValueError`를 발생시켜 배송비를 반환하지 않는다. 문제 실행 파일은 이 예외를 잡아 예상한 거부로 대조한다. 함수 전체의 분기나 문장 커버리지 비율을 계산한 실습은 아니다.

</details>

## 문제의 계산과 거부를 별도로 대조하기

다음 접힌 영역에는 문제 3~5의 답을 담은 코드와 실제 출력이 있다. 문제 1~2는 공식 자료와 모델 표기를 대조하는 개념 문제다. ZIP에 포함된 두 파일을 같은 폴더에 둔 채 실행한다.

<details class="study-verification">
<summary>문제 3~5 실행 코드·출력 보기</summary>

`09-software-questions.py`는 `__file__` 옆의 `09-shipping-rules.py`를 절대 경로로 불러온다. 현재 작업 폴더를 모듈 검색 경로에 넣지 않는 `-I`에서도 같은 파일을 선택한다. 파일이 빠지면 읽기 오류가 발생하므로 ZIP의 두 파일이 함께 있는지 살핀다.

```bash
python -I -B -X utf8 09-software-questions.py
```

```python
import importlib.util
from pathlib import Path


source = Path(__file__).with_name("09-shipping-rules.py")
spec = importlib.util.spec_from_file_location("shipping_rules", source)
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)


def main():
    values = [49999, 50000, 50001]
    result = [rules.shipping_fee(value) for value in values]
    assert result == [3000, 0, 0]
    print(f"q3: {values} -> {result}")
    assert rules.transition("DRAFT", "cancel") == "CANCELLED"
    try:
        rules.transition("CANCELLED", "pay")
    except ValueError as error:
        print(f"q4: CANCELLED + pay, 예상한 거부: {error}")
    else:
        raise AssertionError("잘못된 전이를 허용했다")
    normal = [rules.shipping_fee(10000), rules.shipping_fee(60000)]
    assert normal == [3000, 0]
    print(f"q5: 정상 금액 두 건 -> {normal}")
    try:
        rules.shipping_fee(-1)
    except ValueError as error:
        print(f"q5: -1, 예상한 거부: {error}")
    else:
        raise AssertionError("잘못된 금액을 허용했다")
    print("문제 3~5의 가상 계산 대조 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`assert`가 기대한 목록과 반환값을 비교하고 거부를 기대한 곳에서는 `else`가 잘못된 허용을 실패로 만든다. 이 검증에는 최적화 옵션 `-O`를 붙이지 않는다. 코드의 `normal`은 두 정상 금액의 출력만 담으며 예외 입력 -1의 결과를 정상 반환값에 섞지 않는다.

[[run:3:fold]]

문제 파일의 종료 0은 문제 3~5에 적힌 계산·거부와 결과가 일치했다는 뜻이다. 자체 제작한 제한된 사례의 대조이며 전체 주문 기능에 대한 테스트 결과로 확대하지 않는다.

</details>

## 시험 직전 복습

- 반복은 같은 대상을 다듬는 관점, 점증은 사용할 기능을 늘리는 관점이다. 테스트 활동은 개발 모델에 맞춰 배치한다.
- UML은 모델링 언어다. 클래스의 관계·다중도, 메시지 순서, 객체의 상태 전이는 서로 다른 질문에 답한다.
- 동등 분할은 비슷하게 처리되는 구간에서 대표값을 고르고 경계값 분석은 구간이 바뀌는 지점과 주변을 살핀다.
- 테스트 수준은 단위·연결·전체·수용 범위를, 테스트 종류는 기능·비기능 같은 특성을 구분한다.
- 수정 확인과 회귀는 재실행 목적이 다르다. 커버리지 수치는 측정한 코드 범위의 실행 정도로 해석한다.

## 참고 자료

- [ISTQB: Certified Tester Foundation Level Syllabus v4.0.1](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf)
- [OMG: Unified Modeling Language 2.5.1](https://www.omg.org/spec/UML/2.5.1/PDF)
- [애자일 선언: 선언 이면의 원칙](https://agilemanifesto.org/principles.html)
- [NIST: Secure Software Development Framework v1.1](https://csrc.nist.gov/pubs/sp/800/218/final)
