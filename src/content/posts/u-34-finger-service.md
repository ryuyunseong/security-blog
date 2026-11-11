---
title: "U-34: Finger 서비스 비활성화"
description: "Finger의 중지 설정과 실행 자료를 구분합니다. inetd·xinetd의 가상 수집값 열 건을 대조하고 설정 파일 부재·미수집을 비활성화로 바꾸지 않는 분기를 따라갑니다."
date: "2026-11-11T18:48:49+09:00"
sourcesChecked: "2026-11-11"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "Finger", "서비스 관리", "KISA"]
draft: false
series: unix-2026
seriesOrder: 34
---

`disable = yes`라고 적힌 설정 자료와 Finger가 수신 중이라는 실행 자료가 함께 있다면 어느 쪽이 대상의 현재 상태를 설명하는지 살펴봐야 해요. 파일의 변경 시점과 서비스에 반영한 시점이 다르거나 다른 실행 경로가 남아 있을 수 있거든요.

Finger는 원격 사용자의 정보를 조회하는 프로토콜이에요. [RFC 1288](https://www.rfc-editor.org/rfc/rfc1288)의 2.1절은 TCP 79번 포트를 사용한다고 설명해요. 다만 79번이라는 숫자만 보고 그 소켓의 프로그램까지 Finger라고 확정하지는 않아요. 실행 주체와 서비스 연결을 함께 조사해야 해요.

## U-34가 요구하는 비활성화

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 항목명은 ‘Finger 서비스 비활성화’이고 중요도는 ‘상’이에요. 항목표 9쪽과 본문 68~69쪽의 코드·항목명·중요도가 일치해요. 대상은 SOLARIS, LINUX, AIX, HP-UX 등이에요.

가이드는 Finger가 비활성화되어 있으면 양호, 활성화되어 있으면 취약으로 구분해요. 원격으로 노출되는 사용자 정보가 비밀번호 공격에 이용될 위험을 설명하고요. 외부에서 포트에 연결되지 않는다는 결과는 방화벽이나 접근 경로 때문에 생길 수도 있으므로 서비스 자체의 비활성화 자료와 구별해요.

가이드의 inetd 사례는 `/etc/inetd.conf`의 Finger 항목을 주석 처리하고 변경을 반영하는 순서예요. Linux의 xinetd 사례는 `/etc/xinetd.d/finger`의 `disable`을 `yes`로 바꾸고 설정을 적용해요. Solaris 5.9 이하와 AIX·HP-UX는 inetd 사례, Solaris 5.10 이상은 `inetadm`으로 서비스 상태를 조사하고 중지하는 사례를 제시해요. 실제 대상에서는 사용하는 관리 방식과 버전에 맞춰 자료를 수집해야 해요.

[xinetd.conf(5)](https://manpages.debian.org/bookworm/xinetd/xinetd.conf.5.en.html)는 `disable = yes`를 서비스 시작을 막는 속성으로 설명해요. `include`·`includedir`, 서비스 ID와 전역 제한도 있으므로 한 파일의 한 줄을 전체 실행 조건으로 대신하지는 않아요. `disable = no`도 다른 제한까지 모두 풀렸다는 뜻이 아니라 이 속성에서 비활성화하지 않았다는 뜻으로 읽어요.

## 같은 설정에 서로 다른 실행 자료를 붙이면

아래 두 사례는 실제 서버 조회 결과가 아닌 가상 입력이에요. 둘 다 xinetd의 `setting`을 `yes`로 두고 실행 자료만 바꿨어요. `x-stop`은 수신 없음, `x-stale`은 Finger 수신이 관찰됐다고 가정해요.

[[diagram]]

중지 설정과 수신 자료가 어긋난 `x-stale`은 적용 시점, 다른 서비스 정의와 실행 주체를 조사할 후보로 남아요. 이 그림에서 가정한 Finger 수신은 단순한 포트 번호가 아니라 실행 주체까지 연결해 수집했다는 의미예요.

실습은 수집된 자료를 다음처럼 정리했다고 가정해요. 설정 원문을 분석하는 파서나 실제 서비스 수집기는 아니에요.

- `manager`는 이번 예제가 다루는 `xinetd` 또는 `inetd`예요. SMF 등 다른 관리 방식은 코드의 지원 범위 밖이에요.
- `collection: collected`일 때 `setting`을 채워요. xinetd는 `yes`·`no`, inetd는 `commented`·`active`를 사용해요. `commented`는 조사 범위의 Finger 실행 항목이 모두 주석 처리됐다는 가정이며 주석 한 줄을 찾았다는 뜻은 아니에요.
- 설정 파일이 없으면 `absent`, 조회 오류가 나면 `query-error`, 자료 자체가 없으면 `uncollected`로 두고 `setting`은 `null`로 남겨요. 파일 부재가 다른 실행 경로의 부재까지 입증하지는 않아요.
- `runtime`은 설정과 별개인 실행 자료예요. `listening`·`not-listening`은 해당 시점의 Finger 수신 있음·없음 가정이고 `unknown`·`query-error`·`uncollected`는 실행 근거가 부족한 상태예요. 프로세스 이름을 못 찾거나 원격 연결이 거절된 결과만으로 `not-listening`을 채우지는 않아요.

## ZIP의 가상 자료 열 건을 분류하기

Python 3.12 이상과 표준 라이브러리만 사용해요. Windows Python 3.12.1의 PowerShell과 Git Bash에서 실행했으며 Linux 파일 모드, 관리자 권한, 별도 패키지는 필요하지 않아요. 코드는 지정한 JSON만 읽고 소켓을 열거나 운영 설정·계정·서비스를 조회하거나 바꾸지 않아요.

ZIP을 빈 폴더에 풀고 `README.md`, `u34_finger_review.py`, `u34_finger_cases.json`, `u34_rejected.json`이 있는 글별 폴더로 이동해 주세요. 입력 두 개가 이미 들어 있으므로 직접 생성하거나 `/etc` 아래 경로를 만들 필요는 없어요. 프로그램도 임시 파일을 만들거나 삭제하지 않아요.

[[download]]

```bash
python -I -B -X utf8 u34_finger_review.py u34_finger_cases.json
```

바로 다음 명령으로 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`를 실행해 숫자 종료 코드를 읽어요. PowerShell의 `$?`는 성공 여부이므로 두 값을 구분해 주세요. README의 두 셸 중 사용하는 블록 하나를 선택하면 실행과 종료 코드 조회가 함께 나와요.

`-I`는 Python 격리 모드, `-B`는 바이트코드 생성 방지, `-X utf8`은 UTF-8 모드예요. 이 옵션이 파일시스템을 격리하지는 않으므로 인수에는 ZIP에 들어 있는 가상 입력을 지정해요.

다음은 ZIP과 같은 전체 코드예요. JSON의 키·필드·상태를 검사한 뒤 모든 행을 분류하므로 입력 형식이 어긋나면 일부 행을 정상 결과처럼 먼저 출력하지 않아요.

```python
import argparse
import json
from pathlib import Path
import re
import sys


STATES = {"collected", "absent", "query-error", "uncollected"}
RUNTIME = {"listening", "not-listening", "unknown", "query-error", "uncollected"}
SETTINGS = {"xinetd": {"yes", "no"}, "inetd": {"commented", "active"}}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키 중복")
        result[key] = value
    return result


def load_cases(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(100001)
    if len(raw) > 100000:
        raise ValueError("입력 크기 제한 초과")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("입력은 1~100건의 목록이어야 합니다")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "manager", "collection", "setting", "runtime"}:
            raise ValueError("입력 필드 불일치")
        name = row["id"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name) or name in seen:
            raise ValueError("ID 형식 오류 또는 중복")
        seen.add(name)
        if not isinstance(row["manager"], str) or row["manager"] not in SETTINGS:
            raise ValueError("지원하지 않는 관리 방식")
        if not isinstance(row["collection"], str) or row["collection"] not in STATES:
            raise ValueError("수집 상태 오류")
        if not isinstance(row["runtime"], str) or row["runtime"] not in RUNTIME:
            raise ValueError("실행 관찰 상태 오류")
        if row["collection"] == "collected":
            if not isinstance(row["setting"], str) or row["setting"] not in SETTINGS[row["manager"]]:
                raise ValueError("수집한 설정값 오류")
        elif row["setting"] is not None:
            raise ValueError("설정 자료가 없으면 setting은 null이어야 합니다")
    return rows


def review(row):
    collected = row["collection"] == "collected"
    stopped = collected and row["setting"] in {"yes", "commented"}
    if row["runtime"] == "listening":
        detail = "Finger 수신 가정"
        if stopped:
            detail += "; 중지 설정과 실행 자료 불일치"
        elif not collected:
            detail += "; 설정 자료 " + row["collection"]
        return "검토 후보", detail
    if not collected:
        return "보류", "설정 자료 " + row["collection"]
    if not stopped:
        return "검토 후보", "실행 허용 설정; 실행 자료 " + row["runtime"]
    if row["runtime"] == "not-listening":
        return "입력 조건 일치", "중지 설정과 수신 없음 가정"
    return "보류", "중지 설정; 실행 자료 " + row["runtime"]


def main():
    parser = argparse.ArgumentParser(description="가상 Finger 설정·실행 자료의 대조")
    parser.add_argument("fixture")
    args = parser.parse_args()
    try:
        rows = load_cases(args.fixture)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print("가상 자료 분류 미실행")
        if isinstance(exc, (json.JSONDecodeError, UnicodeError, RecursionError)):
            message = "JSON 구문·UTF-8 인코딩·중첩 깊이를 살펴보세요"
        elif isinstance(exc, OSError):
            message = "입력 파일의 경로·읽기 권한을 살펴보세요"
        else:
            message = str(exc)
        print("입력 오류: " + message, file=sys.stderr)
        return 2
    counts = {"입력 조건 일치": 0, "검토 후보": 0, "보류": 0}
    for row in rows:
        status, reason = review(row)
        counts[status] += 1
        print(f"{row['id']}: {status} ({reason})")
    print(f"가상 자료 {len(rows)}건: 입력 조건 일치 {counts['입력 조건 일치']}, 검토 후보 {counts['검토 후보']}, 보류 {counts['보류']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

첫 실행에서는 다음과 같이 두 건의 입력 조건 일치, 네 건의 검토 후보, 네 건의 보류가 나왔어요. 상태 이름은 이 예제의 자료 비교 결과이며 U-34의 양호·취약 판정을 자동으로 내린 결과는 아니에요.

[[run:1]]

`x-open`은 현재 수신이 없다는 가정이어도 `disable = no`가 남아 있어 실행 허용 설정을 조사할 후보예요. 반대로 `x-stop`과 `inetd-stop`은 입력된 중지 설정·수신 없음 조건이 함께 맞아요. 두 행도 대상 전체의 다른 정의와 실제 반영 여부를 수집한 결과로 확대하지 않아요.

`missing`, `read-error`, `uncollected`는 설정 자료를 얻은 상황이 서로 다르지만 설정값을 지어내지 않고 보류해요. `runtime-unknown`은 중지 설정만 있고 실행 근거가 부족해 보류해요. `missing-listening`은 설정 파일 부재를 이유로 이미 알려진 수신 가정을 숨기지 않도록 검토 후보와 설정 자료 부재를 함께 남겨요.

## x-stale이 불일치 후보로 남는 경로

첫 명령은 `main()`에서 `args.fixture`를 `u34_finger_cases.json`으로 읽어요. `load_cases()`는 최대 100,000바이트와 1~100건을 허용하고 `unique_object()`로 중복 JSON 키를 거부해요. ID는 중복 없는 소문자·숫자·하이픈 형식인지, 다섯 필드가 정확히 있는지 검사해요. 수집된 설정에는 관리 방식에 맞는 문자열이 필요하고 자료가 없는 설정에는 `null`을 요구해요.

세 번째 행인 `x-stale`의 `manager`는 `xinetd`, `collection`은 `collected`, `setting`은 `yes`, `runtime`은 `listening`이에요. 입력 검사를 거쳐 `review(row)`로 들어가면 `collected = True`이고 `stopped`도 `True`가 돼요. 여기서 `stopped`는 설정값의 의미만 계산한 변수로 실제 서비스가 중지됐다고 수집한 값은 아니에요.

그다음 첫 조건 `row["runtime"] == "listening"`이 참이어서 `detail`을 ‘Finger 수신 가정’으로 만들어요. 안쪽의 `if stopped`도 참이므로 ‘중지 설정과 실행 자료 불일치’를 덧붙인 뒤 `("검토 후보", detail)`을 반환해요. 뒤쪽의 수신 없음 조건에는 도달하지 않아요.

`main()`은 반환 상태로 `counts[status]`를 하나 늘리고 ID·상태·이유를 합쳐요. 실제 기록의 `x-stale: 검토 후보 (Finger 수신 가정; 중지 설정과 실행 자료 불일치)` 한 줄이 이 분기를 거친 결과예요. 설정값 `yes`만 보고 먼저 반환했다면 이 차이를 놓쳤을 거예요.

같은 첫 분기에서 `missing-listening`의 `collected`는 거짓이에요. 따라서 수신 후보를 유지하면서 `absent`라는 설정 자료 상태를 이유에 남겨요. 수신이 없는 `x-open`은 첫 분기를 지나 `not stopped`에서 반환하고, 중지 설정이 있는 `runtime-unknown`은 마지막 보류 반환까지 내려가요. 조건의 순서가 알려진 실행 자료를 가리지 않도록 한 거예요.

## 미수집인데 설정값이 채워진 입력 거부하기

`u34_rejected.json`은 `collection`을 `uncollected`로 두면서 `setting`에 `yes`를 넣은 가상 오류 입력이에요. 자료를 수집하지 않았는데 중지 설정을 관찰한 것처럼 적힌 행을 비교에 섞지 않도록 준비했어요.

```bash
python -I -B -X utf8 u34_finger_review.py u34_rejected.json
```

이 명령 뒤에도 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 종료 코드를 읽어요. 다음 기록의 표준 출력은 분류 미실행을, 표준 오류는 거부 이유를 나타내요. 숫자 종료 코드는 2예요.

[[run:2]]

`load_cases()`의 `elif row["setting"] is not None`에 걸려 `ValueError`가 나고 `main()`이 오류를 출력한 뒤 2를 반환해요. 정상 입력의 종료 0은 열 건의 형식 검사·분류가 끝났다는 뜻이고 이 입력의 종료 2는 분류 전 거부예요. 시험에서 예상한 2를 얻었다는 사실을 입력이 허용됐거나 시스템이 안전하다는 결과로 세지는 않아요.

실제 실행에서 종료 2가 나오면 입력 경로·읽기 권한, UTF-8·JSON 구문과 크기, 중복 ID·키, 수집 상태와 `setting`의 대응을 살펴봐요. 프로그램은 입력을 고치지 않으며 ZIP 원본도 남겨 두어요.

운영 점검에서는 관리 방식·설정의 실제 적용 범위, 수집 시점과 서비스 반영 시점, 수신 소켓의 실행 주체를 같은 대상으로 맞춰야 해요. 변경 후에는 해당 서비스가 다시 시작될 조건과 실행 상태를 대조한 자료까지 남겨 파일 편집과 비활성화 완료를 구분해 주세요.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [RFC 1288: The Finger User Information Protocol](https://www.rfc-editor.org/rfc/rfc1288)
- [xinetd.conf(5): 서비스 속성과 include 설정](https://manpages.debian.org/bookworm/xinetd/xinetd.conf.5.en.html)
- [Python 3.12: JSON 입력 처리](https://docs.python.org/3.12/library/json.html)
