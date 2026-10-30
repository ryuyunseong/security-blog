---
title: "정보보안 기초: HMAC, 접근 권한과 SQL 입력의 차이"
description: "암호화·해시·HMAC의 목적을 나누고 가상 문서의 권한, 매개변수 SQL, 재사용된 메시지를 실제 계산으로 비교합니다."
date: "2026-10-30T18:46:04+09:00"
sourcesChecked: "2026-10-30"
category: cs-study
tags: ["전산", "정보보안", "HMAC", "접근통제", "SQL"]
draft: false
---

서명처럼 보이는 값이 메시지 옆에 붙어 있어도 내용을 숨겼는지, 메시지가 바뀌었는지, 그 요청자가 문서를 읽어도 되는지는 서로 다른 질문이다. HMAC이 맞는 메시지를 받은 뒤에도 대상 문서의 권한을 검사해야 한다. 문자열을 SQL에 넣는 방식은 또 별도로 살핀다.

이번 글에서는 메시지 바이트, 가상 주체와 문서, 메모리 DB의 이름 조회를 각각 계산한다. 암호화·사용자 로그인·외부 요청은 실행하지 않는다.

## 무엇을 보호하려는지부터 구분하기

기밀성은 허가되지 않은 공개를 제한하는 성질이고 무결성은 부적절한 변경·훼손을 방지하는 성질이다. 가용성은 필요할 때 적시에 신뢰할 수 있게 정보나 서비스를 이용할 수 있는 성질이다. [NIST의 기밀성](https://csrc.nist.gov/glossary/term/confidentiality), [무결성](https://csrc.nist.gov/glossary/term/integrity), [가용성](https://csrc.nist.gov/glossary/term/availability) 정의를 구분해 읽는다.

허가되지 않은 사람이 문서를 읽으면 기밀성, 금액이 몰래 바뀌면 무결성, 요청을 처리하지 못하면 가용성과 연결된다. 한 사건이 여러 성질에 영향을 줄 수도 있으므로 공격 이름만으로 피해를 하나로 고정하지 않는다.

| 도구·방식 | 주로 제공하는 기능 | 함께 구분할 조건 |
| --- | --- | --- |
| 대칭키 암호 | 공유한 키로 암호화·복호화 | 암호 방식의 운용 모드와 무결성 보호 |
| 공개키 기반 방식 | 개인키·공개키 쌍을 쓰는 암호·서명 기능 | 알고리즘과 용도에 맞는 연산 선택 |
| 암호학적 해시 | 입력에서 고정 길이 요약값 계산 | 비교할 요약값 자체의 신뢰성 |
| HMAC | 공유 키로 메시지 인증 코드 계산 | 키를 공유한 주체의 범위와 재전송 처리 |
| 전자서명 | 개인키로 서명하고 공개키로 검증 | 공개키의 신뢰성·개인키 관리 |

[FIPS 197의 AES](https://csrc.nist.gov/pubs/fips/197/final)는 128비트 블록을 사용하며 AES-128·192·256의 숫자는 키 길이다. AES-256을 ‘256비트 블록’으로 읽지 않는다. [FIPS 186-5](https://csrc.nist.gov/pubs/fips/186-5/final)는 전자서명을 다룬다. 해시·HMAC 계산을 이 서명이나 암호화의 실행 결과로 표현하지 않는다.

## 공개 HMAC 시험 벡터와 가상 자료를 실행하기

Python 3.9 이상과 표준 라이브러리의 `hmac`, `hashlib`, `sqlite3`를 사용한다. 실제 환경은 Windows Python 3.12.1, SQLite 3.43.1이다. 운영 DB·실제 사용자·API 키·서버는 필요하지 않다.

ZIP을 빈 폴더에 풀고 `10-security-models.py`와 `10-security-questions.py`가 함께 있는 글별 폴더에서 실행한다. 입력은 코드에 들어 있으며 DB는 조회할 때마다 메모리에 새로 만든다. 별도의 입력 파일이나 기존 DB를 준비하지 않는다.

[[download]]

```bash
python -I -B -X utf8 10-security-models.py mac
python -I -B -X utf8 10-security-models.py access
python -I -B -X utf8 10-security-models.py sql
```

Linux·WSL에서는 `python3`를 사용할 수 있다. 각 명령 직후 PowerShell의 `$LASTEXITCODE`, Bash의 `echo $?`로 종료 코드를 읽는다. 파일·서버를 생성하지 않아 별도 정리 명령은 없다.

다음 전체 코드에서 세 명령은 `main()`의 서로 다른 분기를 실행한다. HMAC의 `test_key`는 [RFC 4231 시험 사례 1](https://www.rfc-editor.org/rfc/rfc4231.html#section-4.2)에 공개된 `0x0b` 20바이트다. 실제 인증에 쓸 비밀 키가 아니라 결과 재현용 공개 입력이다.

```python
import argparse
from contextlib import closing
import hashlib
import hmac
import sqlite3


def test_vector():
    return bytes([0x0b]) * 20, b"Hi There"


def tag_for(test_key, message):
    return hmac.digest(test_key, message, "sha256")


def can_read(actor, document):
    if actor is None:
        return False
    if actor["role"] == "admin":
        return True
    return actor["role"] == "reader" and actor["id"] == document["owner"]


def lookup_id(name):
    if not isinstance(name, str):
        raise TypeError("이름은 문자열이어야 한다")
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        conn.executemany("INSERT INTO users VALUES (?, ?)", [(1, "alice"), (2, "bob")])
        result = conn.execute("SELECT id FROM users WHERE name = ? ORDER BY id", (name,))
        return [row[0] for row in result]


def main():
    parser = argparse.ArgumentParser(description="공개 시험 벡터와 가상 권한·SQL을 비교한다")
    parser.add_argument("example", choices=("mac", "access", "sql"))
    args = parser.parse_args()
    if args.example == "mac":
        test_key, message = test_vector()
        tag = tag_for(test_key, message)
        print("HMAC-SHA-256: " + tag.hex())
        print(f"원문 대조: {hmac.compare_digest(tag, tag_for(test_key, message))}")
        print(f"변경문 대조: {hmac.compare_digest(tag, tag_for(test_key, message + b'!'))}")
        print(f"SHA-256 길이: {len(hashlib.sha256(message).digest())}바이트")
    elif args.example == "access":
        document = {"id": 7, "owner": 1001}
        for label, actor in [("미인증", None), ("소유자", {"id": 1001, "role": "reader"}), ("다른 계정", {"id": 1002, "role": "reader"}), ("관리자", {"id": 1003, "role": "admin"})]:
            print(f"{label}: {'허용' if can_read(actor, document) else '거부'}")
    else:
        for name in ("alice", "alice' OR 1=1 --", "nobody"):
            print(f"이름={name!r}, 일치 ID={lookup_id(name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`test_vector()`의 메시지 `b"Hi There"`는 바이트 배열이다. `tag_for()`가 같은 시험 키와 메시지를 HMAC-SHA-256에 넣어 32바이트 태그를 반환한다. `tag.hex()`는 그 값을 64자리 16진수로 표시한다. `message + b"!"`는 입력 끝에 바이트 하나를 더한 다른 메시지이며 원문 태그와 대조한 결과가 달라진다.

[[run:1]]

출력한 태그는 RFC 4231의 HMAC-SHA-256 값과 같다. `True`는 같은 키·메시지로 만든 태그가 같다는 결과이고 `False`는 이 변경 메시지에서 태그가 달랐다는 결과다. 메시지 본문은 여전히 코드에서 읽힌다. HMAC은 내용을 암호화하지 않으며 공유 키를 아는 양쪽 모두 태그를 만들 수 있다.

[Python hmac 문서](https://docs.python.org/3.12/library/hmac.html)는 태그 검증에 `compare_digest()` 사용을 권장한다. 이 코드는 같은 타입의 바이트 태그끼리 대조한다. 해시 출력 길이나 태그 일치만으로 사용자 로그인과 요청의 최신성까지 판정하지 않는다.

## 주체가 누구인지와 무엇을 허용할지

인증은 주장한 신원을 검증하고 인가는 그 주체가 특정 대상에 어떤 동작을 할 수 있는지 결정한다. 비밀번호 같은 지식, 기기 같은 소유, 생체 특성과 같은 인증 요소를 조합할 때는 요소의 종류도 구분한다. 비밀번호 두 개를 요구한다고 곧바로 서로 다른 요소의 다중요소 인증이 되는 것은 아니다. [OWASP 인증 설명](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)을 참고한다.

인가 정책에서는 역할에 따라 허용하는 RBAC, 주체·대상의 속성을 조건으로 쓰는 ABAC, 객체 소유자가 권한을 위임하는 임의적 접근 통제(DAC), 중앙의 보안 등급·레이블 정책으로 통제하는 [강제적 접근 통제(MAC)](https://csrc.nist.gov/glossary/term/mandatory_access_control)을 구분한다. 여기서 MAC은 앞 절의 메시지 인증 코드와 같은 약자를 쓰지만 의미가 다르다.

아래 예제의 `actor`는 신원을 이미 검증했다고 가정한 서버 측 자료다. 클라이언트가 보낸 ID·역할을 그대로 신뢰하는 로그인 구현이 아니다. 가상 문서 7의 소유자는 1001이며 정책은 관리자 또는 `reader` 역할의 소유자에게 읽기를 허용한다.

[[diagram]]

`can_read()`는 미인증인 `None`을 먼저 거부한다. 그 뒤 관리자는 허용하고 나머지는 역할이 `reader`이면서 ID가 문서의 `owner`와 같은지 함께 비교한다. 1002인 `reader`는 역할 조건을 만족해도 문서 7의 소유자 조건을 만족하지 못해 거짓을 반환한다. 이 함수는 거부를 예외로 던지지 않고 `False`라는 정상 반환값으로 나타낸다.

[[run:2]]

이 정책은 역할과 대상의 소유 관계를 함께 사용한 작은 모형이다. 다른 대상·동작의 권한은 구현하지 않았다. [OWASP 인가 설명](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)은 기본 거부와 요청마다의 권한 검사를 강조한다. 앞선 요청이 허용됐다는 사실을 다음 문서의 허용 근거로 재사용하지 않는다.

## 조건처럼 보이는 이름도 SQL의 값으로 넘기기

`lookup_id()`는 호출할 때마다 `:memory:` 연결과 가상 `users` 테이블을 만든다. 이름 `alice`는 ID 1, `bob`은 ID 2로 초기화한다. `closing()`은 함수가 끝나거나 예외가 발생할 때 연결을 닫는다. 이전 조회가 다음 문제의 상태를 바꾸지 않는다.

SQL 구조는 코드의 `WHERE name = ?`로 고정하고 입력 문자열은 `(name,)` 튜플로 따로 바인딩한다. 쉼표가 있는 이 표기는 원소 하나인 튜플이다. [Python sqlite3의 매개변수 바인딩](https://docs.python.org/3.12/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries)을 사용하는 방법이다.

[[run:3]]

`"alice' OR 1=1 --"` 전체가 하나의 이름 값으로 처리됐다. 그런 이름의 행을 넣지 않았으므로 빈 목록 `[]`가 나온다. `alice`의 결과 `[1]`은 ID 하나를 담은 목록이다. 0행, ID 숫자 0, SQL의 `NULL`을 같은 결과로 읽지 않는다.

[OWASP SQL 삽입 방어](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)는 구조와 값의 분리를 설명한다. 바인딩은 조회할 행에 대한 호출자의 인가를 대신하지 않는다. 테이블명·열 이름 같은 SQL 구조를 `?`로 선택하는 기능으로도 확대하지 않는다.

## 공격이 이용하는 해석 지점

| 유형 | 문제가 생기는 지점 | 방어에서 비교할 내용 |
| --- | --- | --- |
| SQL 삽입 | 입력이 SQL 구문의 일부로 해석됨 | 고정된 SQL 구조와 값 바인딩 |
| XSS | 신뢰하지 않는 값이 브라우저의 실행 문맥으로 들어감 | 출력 문맥에 맞는 인코딩·필요 시 HTML 정화 |
| CSRF | 브라우저가 인증 정보를 붙이는 환경에서 원치 않는 상태 변경 요청을 보냄 | 서버의 CSRF 검증·출처 검사와 쿠키 정책 |
| 재전송 | 유효했던 메시지나 요청을 다시 사용함 | 프로토콜의 nonce·시각·중복 처리 정책 |
| 서비스 거부 | 자원을 소진시켜 정상 요청을 처리하기 어려워짐 | 자원·요청 제한, 복구와 가용성 대책 |

[OWASP XSS 방어](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)는 HTML·JavaScript·URL 등 출력 문맥을 구분한다. [CSRF 방어](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)는 상태 변경 요청의 서버 측 검증을 다룬다. SQL의 값 바인딩을 이 두 공격의 방어 기법으로 그대로 바꿔 설명하지 않는다. 이 표의 브라우저 공격과 서비스 거부는 직접 실행한 실습이 아니라 문서 해설이다.

## 자체 연습문제 5개

### 문제 1. 조회 요청을 처리할 수 없을 때

허가된 사용자의 데이터가 외부로 공개되거나 변경된 증거는 없지만 서비스가 멈춰 조회를 할 수 없다. 제시한 현상에서 직접 드러나는 보안 성질은 무엇인가? 이것만으로 나머지 성질이 안전하다고 단정할 수 있는가?

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 문제 1 해설

필요할 때 정상 조회를 이용할 수 없으므로 가용성 문제가 직접 드러난다. 공개·변경 증거가 제시되지 않았다는 것은 기밀성·무결성이 검증됐다는 뜻이 아니다. 피해를 분류할 때 관찰한 현상과 아직 조사하지 않은 성질을 구분한다.

</details>

### 문제 2. 같은 HMAC 메시지를 두 번 보내면

시험 키·메시지·태그를 바꾸지 않고 `compare_digest()`로 두 번 대조한다. 두 결과는 무엇인가? 이 대조만으로 두 번째 메시지가 새 요청임을 입증할 수 있는가?

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 문제 2 해설

결과는 `[True, True]`다. 같은 입력과 키로 계산한 태그를 대조하는 동작에는 이전 수신 이력이나 시각을 살피는 코드가 없다. 태그가 맞아도 재사용 여부는 이 함수에서 구분되지 않는다. 실제 프로토콜의 재전송 방어에는 별도의 nonce·시각·중복 처리 규칙이 필요하다.

</details>

### 문제 3. 소유자는 같고 역할이 알려지지 않았을 때

문서 9의 소유자가 1002이고 주체가 `{"id": 1002, "role": "unknown"}`이다. `can_read()`는 어떤 값을 반환하며 어느 조건에서 결정되는가?

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 문제 3 해설

`False`를 반환한다. 주체가 `None`은 아니지만 관리자 역할도 아니다. 마지막 식의 `actor["role"] == "reader"`가 거짓이므로 AND 전체가 거짓이다. ID가 소유자와 같다는 이유만으로 허용하는 별도 분기는 없다. 예외나 SQL의 빈 결과와 구분되는 불리언 반환값이다.

</details>

### 문제 4. bob과 조건 문자열의 조회 결과

`lookup_id("bob")`와 `lookup_id("bob' OR 1=1 --")`를 각각 실행하면 무엇이 반환되는가? 두 번째 문자열에서 조건이 SQL 구문으로 추가되는가?

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 문제 4 해설

각각 `[2]`와 `[]`다. 두 호출은 독립된 메모리 DB에서 같은 초기 자료를 만든다. 첫 값은 이름 bob인 행의 ID 2와 일치한다. 두 번째는 따옴표·조건·주석처럼 보이는 문자까지 포함한 전체 이름 값이므로 일치하는 행이 없다. SQL 구문은 `WHERE name = ?`로 유지된다.

</details>

### 문제 5. 출력 문맥과 원치 않는 요청

게시판의 신뢰하지 않는 값이 브라우저에서 코드로 실행되는 경우와, 다른 페이지에서 유도한 요청에 인증 정보가 자동으로 붙어 상태가 바뀌는 경우를 각각 어떤 공격으로 분류하는가? SQL 바인딩 하나로 두 경우를 해결했다고 할 수 있는가?

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 문제 5 해설

앞의 현상은 XSS, 뒤의 조건은 CSRF와 연결된다. XSS에서는 값을 넣는 출력 문맥과 실행 가능성을, CSRF에서는 인증 정보가 붙는 요청과 서버 측의 원치 않는 상태 변경 방어를 조사한다. SQL 바인딩은 DB에서 구조와 값을 나누는 기법이므로 이 두 검토를 대신하지 않는다.

</details>

## 문제 2~4의 계산을 다시 실행하려면

문제 1과 5는 개념 대조다. 계산 문제의 정답이 포함된 코드·출력은 다음 접힌 영역에 있다. ZIP의 두 Python 파일을 같은 폴더에 둔 채 실행한다.

<details class="study-verification">
<summary>문제 2~4 실행 코드·출력 보기</summary>

`__file__` 옆의 `10-security-models.py`를 경로로 불러오므로 `-I`에서도 같은 모형 파일을 사용한다. 파일이 빠지면 읽기 오류가 나며 원본 두 파일이 같은 폴더에 있는지 살핀다. 검증용 `assert`를 사용하므로 `-O`를 붙이지 않는다.

```bash
python -I -B -X utf8 10-security-questions.py
```

```python
import hmac
import importlib.util
from pathlib import Path


source = Path(__file__).with_name("10-security-models.py")
spec = importlib.util.spec_from_file_location("security_models", source)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)


def main():
    test_key, message = models.test_vector()
    tag = models.tag_for(test_key, message)
    repeated = [hmac.compare_digest(tag, models.tag_for(test_key, message)) for _ in range(2)]
    assert repeated == [True, True]
    print(f"q2: 같은 메시지와 태그 두 번 대조 -> {repeated}")
    document = {"id": 9, "owner": 1002}
    actor = {"id": 1002, "role": "unknown"}
    result = models.can_read(actor, document)
    assert result is False
    print(f"q3: 소유자 일치·알 수 없는 역할 -> {result}")
    plain = models.lookup_id("bob")
    injected = models.lookup_id("bob' OR 1=1 --")
    assert plain == [2] and injected == []
    print(f"q4: bob -> {plain}, 조건처럼 보이는 전체 이름 -> {injected}")
    print("문제 2~4의 가상 계산 대조 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`repeated`는 동일 태그를 두 번 대조한 결과이고 `result`는 가상 정책의 반환값이다. `plain`과 `injected`는 서로 다른 메모리 DB에서 조회한 ID 목록이다. 코드가 이 값들을 기대한 결과와 비교한 뒤 다음 출력을 남겼다.

[[run:4:fold]]

종료 0은 이 세 문제의 대조가 끝났다는 뜻이다. 허용 여부의 `False`나 조회 결과 `[]`도 이 문제에서는 기대한 정상 결과다. 파일 누락·예상하지 않은 예외·`assert` 실패는 처리되지 않은 오류로 종료하며 표준 오류를 함께 살핀다.

</details>

## 시험 직전 복습

- 기밀성·무결성·가용성은 보호하려는 성질이다. 한 공격이 여러 성질에 영향을 줄 수 있다.
- AES의 키 길이와 블록 길이를 구분한다. 해시는 요약값, HMAC은 공유 키 기반 메시지 인증 코드이며 전자서명·암호화와 기능이 다르다.
- 인증은 신원 검증, 인가는 주체·대상·동작의 허용 판단이다. 허용되지 않은 역할·관계에는 기본 거부를 적용한다.
- 매개변수는 SQL의 값 자리에 바인딩한다. 0행·숫자 0·NULL·불리언 거짓을 구분한다.
- XSS의 출력 문맥, CSRF의 상태 변경 요청, 재전송의 이력·시각 조건을 각각 살핀다.

## 참고 자료

- [NIST: Advanced Encryption Standard, FIPS 197](https://csrc.nist.gov/pubs/fips/197/final)
- [NIST: Digital Signature Standard, FIPS 186-5](https://csrc.nist.gov/pubs/fips/186-5/final)
- [RFC 2104: HMAC](https://www.rfc-editor.org/rfc/rfc2104.html)
- [RFC 4231: HMAC-SHA 시험 벡터](https://www.rfc-editor.org/rfc/rfc4231.html)
- [Python 3.12: hmac](https://docs.python.org/3.12/library/hmac.html)
- [Python 3.12: sqlite3](https://docs.python.org/3.12/library/sqlite3.html)
- [OWASP: 인가](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP: SQL 삽입 방어](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
