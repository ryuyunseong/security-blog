---
title: "U-30: UMASK 설정 관리, 설정값과 실행값 대조하기"
description: "UMASK 022 이상이라는 공식 기준을 수집값에 대입하고, 0031에서 기타 사용자 쓰기가 남는 이유를 계산합니다. 설정 파일·프로세스 자료와 미수집 상태를 구분하는 가상 실습입니다."
date: "2026-11-07T20:17:08+09:00"
sourcesChecked: "2026-11-07"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "umask", "파일 권한", "KISA"]
draft: false
series: unix-2026
seriesOrder: 30
---

`/etc/profile`에 `umask 022`가 적혀 있는 상황을 가정해 보자. 새 로그인 셸이 그 설정을 읽는지, 이미 실행 중인 서비스에도 같은 값이 적용됐는지는 각각 조사할 대상이다. umask는 프로세스가 새 파일을 만들 때 제외할 권한 비트이며 자식 프로세스에 상속된다. 설정 파일의 한 줄을 서버 전체의 실행값으로 기록하면 생성 주체 사이의 차이를 놓친다.

## U-30의 022 기준을 적용할 자료

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-30은 ‘UMASK 설정 관리’, 중요도는 ‘중’이다. 항목표 9쪽과 본문 62~64쪽을 대조했으며 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다. 양호 기준은 UMASK가 022 이상인 경우, 취약 기준은 022 미만인 경우다. 조치 사례는 설정값 022를 제시한다.

가이드에는 `/etc/profile`, 개인 셸 초기화 파일, 운영체제별 로그인 설정과 FTP 프로그램의 설정 예시가 나온다. Linux 예시의 `/etc/login.defs`에 적힌 `UMASK`와 셸에서 실행하는 `umask`는 서로 다른 설정 경로다. 사용하는 로그인 방식·셸·프로그램이 어떤 자료를 읽는지부터 조사한다. 설정 변경의 영향 범위와 새 로그인·재시작 필요성도 해당 실행 경로에 따라 달라진다.

수집 자료는 다음처럼 구분할 수 있다. 아래 상황은 실습 입력을 설명하기 위한 가정이며 실제 서버에서 수집한 결과가 아니다.

- 설정 파일에서 값을 읽었다면 `source: config`, `state: available`로 적는다. 해당 파일 경로·설정 줄·수집 시점과 이를 읽는 프로그램을 별도 근거로 남긴다. 이 값만으로 실행 중인 프로세스의 값을 확정하지 않는다.
- 대상 셸의 `umask` 출력이나 Linux 4.7 이후 `/proc/<PID>/status`의 `Umask`를 읽었다면 `source: process`, `state: available`이다. 대상 프로세스·계정·실행 시점이 같은 자료인지 대조한다. 현재 셸의 출력은 다른 서비스의 값이 아니다.
- 조회가 실패했다면 `read_error`, 설정 파일의 부재가 입증됐다면 `config`의 `missing`, 자료를 받지 못했다면 `not_collected`로 남긴다. 세 경우 모두 값은 `null`이다. 설정 파일이 없어도 상속받은 umask가 있으므로 부재를 0000이나 양호로 바꾸지 않는다.

이 구분을 입력에 남기면 값의 출처를 유지한 채 숫자를 비교할 수 있다. 실습 프로그램은 입력된 상태를 읽을 뿐, 조회 오류나 파일 부재를 입증하는 수집기는 아니다.

## 0031에서 기타 사용자 쓰기가 남는 계산

umask의 각 자리는 8진수다. `0022`는 그룹 쓰기 `0020`과 기타 사용자 쓰기 `0002`를 차단한다. 기본 ACL이 없는 부모 디렉터리에서 프로그램이 일반 파일 `0666`, 디렉터리 `0777`을 요청한다면 결과는 각각 `0644`, `0755`다. 요청하지 않은 실행 권한을 umask가 추가하지는 않는다.

그런데 `0031`은 숫자로 `0022`보다 크면서 기타 사용자 쓰기 비트 `0002`를 포함하지 않는다. 가이드의 ‘022 이상’이라는 숫자 비교와 쓰기 비트가 모두 차단됐는지를 나누어 출력하면 이 차이를 드러낼 수 있다.

[[diagram]]

그림은 기본 ACL이 없고 새 일반 파일을 `0666`으로 요청한 경우만 계산한다. 기본 ACL이 있으면 상속 ACL과 요청 모드로 권한이 결정되며 기존 파일을 다시 열거나 생성 후 권한을 바꾸는 경우도 별도로 조사한다. 실제 파일 생성과 ACL 비교는 [umask와 파일 권한 실습](/security-blog/posts/umask-and-file-permissions/)에서 다뤘다.

여기서는 공식 기준 문구를 바꾸지 않고 `022 이상/미만`을 숫자 비교 결과로 표시한다. 추가로 `쓰기 차단 누락`을 계산해 비트 구성을 살핀다. 이 두 필드를 합쳐 자동 양호 판정을 내리지는 않는다. 특이한 마스크는 생성 권한과 공유 요구사항을 함께 조사할 대상으로 남긴다.

## ZIP에서 가상 수집 자료 계산하기

Python 3.9 이상과 표준 라이브러리만 필요하다. Windows Python 3.12.1에서 PowerShell과 Git Bash로 실행했다. 입력 문자열과 정수만 계산하므로 관리자 권한·Linux 파일시스템·실제 Unix 설정 파일이 필요하지 않다. `os.umask()`나 권한 변경 함수를 호출하지 않으며 결과 파일도 쓰지 않는다.

ZIP을 빈 폴더에 풀고 `README.md`, `u30_umask_review.py`, `u30_umask_cases.json`이 함께 있는 글별 폴더로 이동한다. README의 각 단계에서 사용하는 셸의 블록 하나만 선택한다. 포함된 입력은 다시 만들지 않는다.

[[download]]

```bash
python -I -B -X utf8 u30_umask_review.py u30_umask_cases.json
```

명령 직후 PowerShell에서는 `$LASTEXITCODE`, Bash에서는 `echo $?`로 숫자 종료 코드를 읽는다. PowerShell의 `$?`는 성공 여부를 나타내는 값이다. `-I`는 Python의 환경 변수와 사용자 경로 등의 영향을 제한하고, `-B`는 바이트코드 파일 생성을 막는다. 공백이 있는 다른 입력 경로를 지정한다면 경로를 따옴표로 감싼다.

입력 열 건에는 마스크 여섯 가지와 설정 파일 값 한 건, 값 비교를 보류할 세 상태가 들어 있다. `value`는 네 자리 8진수 문자열이다. `available`인 행에서만 문자열 값을 받고 나머지는 `null`을 요구한다.

```json
[
  {"id": "shell-022", "source": "process", "state": "available", "value": "0022"},
  {"id": "shell-027", "source": "process", "state": "available", "value": "0027"},
  {"id": "shell-077", "source": "process", "state": "available", "value": "0077"},
  {"id": "service-031", "source": "process", "state": "available", "value": "0031"},
  {"id": "shell-021", "source": "process", "state": "available", "value": "0021"},
  {"id": "shell-111", "source": "process", "state": "available", "value": "0111"},
  {"id": "profile-022", "source": "config", "state": "available", "value": "0022"},
  {"id": "process-denied", "source": "process", "state": "read_error", "value": null},
  {"id": "profile-missing", "source": "config", "state": "missing", "value": null},
  {"id": "process-unsampled", "source": "process", "state": "not_collected", "value": null}
]
```

아래 전체 코드는 ZIP의 `u30_umask_review.py`와 같다. `load_rows()`가 명시한 입력 파일만 읽고 전체 목록을 검증한 뒤 출력한다. 뒤쪽 행에 오류가 있어도 앞쪽 결과만 먼저 출력하는 부분 성공은 만들지 않는다.

```python
import argparse
import json
import re
import sys
from pathlib import Path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키 중복")
        result[key] = value
    return result


def validate(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError("입력은 1~1000건의 목록이어야 함")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "source", "state", "value"}:
            raise ValueError("id, source, state, value 필드 필요")
        label = row["id"]
        if not isinstance(label, str) or not re.fullmatch(r"[a-z0-9-]{1,40}", label):
            raise ValueError("id 형식 오류")
        if label in seen:
            raise ValueError("id 중복")
        seen.add(label)
        if row["source"] not in ("config", "process"):
            raise ValueError("source는 config 또는 process")
        state = row["state"]
        if state not in ("available", "read_error", "missing", "not_collected"):
            raise ValueError("state 형식 오류")
        if state == "missing" and row["source"] != "config":
            raise ValueError("missing은 설정 파일 부재에만 사용")
        value = row["value"]
        if state == "available":
            if not isinstance(value, str) or not re.fullmatch(r"0[0-7]{3}", value):
                raise ValueError("수집값은 네 자리 8진수 문자열이어야 함")
        elif value is not None:
            raise ValueError("미확정 상태의 value는 null이어야 함")
    return rows


def load_rows(path):
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(1_000_001)
    except OSError as error:
        raise ValueError("지정한 입력 파일을 읽지 못함") from error
    if len(raw) > 1_000_000:
        raise ValueError("입력 크기 제한 초과")
    return validate(json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object))


def calculate(value):
    mask = int(value, 8)
    numeric = "이상" if mask >= 0o022 else "미만"
    missing = 0o022 & (0o777 ^ mask)
    allowed = 0o777 ^ mask
    return numeric, missing, 0o666 & allowed, 0o777 & allowed


def describe(row):
    label = row["id"]
    source = {"config": "설정", "process": "실행"}[row["source"]]
    state = row["state"]
    if state != "available":
        reason = {"read_error": "조회 오류", "missing": "설정 파일 부재",
                  "not_collected": "자료 미수집"}[state]
        return f"{label}: {reason}, 값 비교 보류"
    numeric, missing, file_mode, dir_mode = calculate(row["value"])
    return (f"{label}: {source}={row['value']}, 022 {numeric}, "
            f"쓰기 차단 누락={missing:04o}, 파일={file_mode:04o}, 디렉터리={dir_mode:04o}")


def self_test():
    expected = {
        "0000": ("미만", 0o022, 0o666, 0o777),
        "0021": ("미만", 0o002, 0o646, 0o756),
        "0022": ("이상", 0, 0o644, 0o755),
        "0027": ("이상", 0, 0o640, 0o750),
        "0031": ("이상", 0o002, 0o646, 0o746),
        "0077": ("이상", 0, 0o600, 0o700),
        "0111": ("이상", 0o022, 0o666, 0o666),
    }
    for value, result in expected.items():
        if calculate(value) != result:
            raise RuntimeError("계산 기대값 불일치")
    base = {"id": "sample", "source": "process", "state": "available", "value": "0022"}
    bad = [[], [base, base], [dict(base, extra=1)], [dict(base, id="../x")],
           [dict(base, source="unknown")], [dict(base, state="absent")],
           [dict(base, value=22)], [dict(base, value="022")],
           [dict(base, value="0088")], [dict(base, value="1022")],
           [dict(base, state="read_error")],
           [dict(base, state="missing", value=None)]]
    for rows in bad:
        try:
            validate(rows)
        except ValueError:
            continue
        raise RuntimeError("잘못된 입력을 허용함")
    print(f"계산 사례 {len(expected)}건 일치, 입력 거부 {len(bad)}건 일치")


def main():
    parser = argparse.ArgumentParser(description="가상 UMASK 수집값 비교")
    parser.add_argument("fixture", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        if args.fixture is not None:
            parser.error("--self-test에는 입력 파일을 지정하지 않음")
        self_test()
        return 0
    if args.fixture is None:
        parser.error("JSON 입력 파일 필요")
    try:
        rows = load_rows(args.fixture)
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        print(describe(row))
    print(f"가상 자료 {len(rows)}건 계산 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### service-031이 출력 한 줄이 되는 과정

위 명령은 `main()`으로 들어가 JSON 경로를 `args.fixture`에 저장한다. `load_rows()`는 최대 1,000,000바이트까지 허용하고 `unique_object()`로 중복 키를 거부한다. `validate()`는 1~1000건인지, 네 필드만 있는지, ID가 중복되지 않는지와 상태별 값 형식을 검사한다. 예를 들어 `"0031"` 대신 숫자 `31`을 넣으면 진법을 추측하지 않고 입력 오류로 끝난다.

검증 후 `for row in rows`가 `service-031`에 도달하면 `describe()`가 `source`를 ‘실행’으로 표시한다. `state`가 `available`이므로 보류 분기를 지나 `calculate("0031")`를 호출한다. 여기서 `mask = int(value, 8)`은 8진수 31을 정수 25로 읽는다. 비교 기준 `0o022`는 정수 18이므로 `numeric`은 ‘이상’이다.

`0o777 ^ mask`는 일반 권한 아홉 비트 안에서 마스크를 반전한 `0o746`이다. `missing = 0o022 & 0o746`은 `0o002`가 된다. 그룹 쓰기는 차단됐지만 기타 사용자 쓰기의 차단 비트가 빠져 있다. 일반 파일 계산은 `0o666 & 0o746 = 0o646`, 디렉터리 계산은 `0o777 & 0o746 = 0o746`이다.

`calculate()`가 네 값을 반환하면 `describe()`는 다음 한 줄을 만들고 `main()`의 `print()`가 출력한다. 아래 실제 실행 기록의 `service-031` 행과 같다. `파일=0646`은 소유자 읽기·쓰기, 그룹 읽기, 기타 사용자 읽기·쓰기라는 가상 계산값이다.

[[run:1]]

`shell-021`은 022 미만이며 기타 사용자 쓰기의 차단 비트도 빠졌다. `shell-111`은 022 이상이지만 그룹·기타 사용자 쓰기 차단이 모두 빠져 `파일=0666`이다. `profile-022`는 ‘설정’ 출처를 유지하며 출력의 파일·디렉터리 값은 해당 숫자를 대입한 계산값이다. 실제 생성 결과로 읽어서는 안 된다.

뒤의 세 행은 숫자 계산에 도달하지 않고 각각 조회 오류·설정 파일 부재·자료 미수집을 출력한다. 마지막 `가상 자료 10건 계산 완료`와 종료 0은 입력 검사와 가상 계산이 끝났다는 뜻이다. 보류 행도 정상적인 입력이며 서버 전체의 수집 완료나 U-30 양호 판정으로 세지 않는다.

### 계산 기대값과 입력 오류 시험

같은 폴더에서 다음 명령을 실행하면 JSON 파일을 읽지 않고 코드 안의 기대값과 오류 입력을 시험한다.

```bash
python -I -B -X utf8 u30_umask_review.py --self-test
```

`self_test()`는 0000·0021·0022·0027·0031·0077·0111의 네 반환값을 고정된 기대값과 비교한다. 이어서 빈 목록, 중복 ID, 추가 필드, 잘못된 ID·출처·상태, 숫자형·자릿수·8진수 범위를 어긴 값, 미확정 상태의 잔존 값, 프로세스에 지정한 `missing`을 거부하는지 시험한다.

[[run:2]]

계산 7건과 거부 12건이 모두 기대와 같으면 종료 0이다. 잘못된 입력을 거부한 시험의 성공을 실제 서버의 허용·거부 결과로 해석하지 않는다. CLI의 읽기·JSON·입력 검증 오류는 표준 오류와 종료 2로 나타난다. 자체 시험의 기대값이 어긋나면 예외로 종료하므로 마지막 성공 문구가 나오지 않는다. README에도 각 실행 단계 바로 옆에 셸별 종료 코드 조회가 있다.

운영 점검 기록에는 설정 파일의 값과 해당 생성 프로세스의 수집값을 구분해 남긴다. 둘이 다르면 실행 경로, 후속 초기화 설정, 프로세스 시작 시점을 조사한다. 자료가 없는 부분은 미수집으로 두고 실제 생성 권한을 조사할 때 요청 모드와 부모 기본 ACL까지 함께 기록한다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux man-pages: umask(2)](https://man7.org/linux/man-pages/man2/umask.2.html)
- [Python 3.12: 정수의 비트 연산](https://docs.python.org/3.12/library/stdtypes.html#bitwise-operations-on-integer-types)
- [Python 3.12: 명령줄과 환경](https://docs.python.org/3.12/using/cmdline.html)
