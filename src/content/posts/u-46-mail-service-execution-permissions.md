---
title: "U-46: 일반 사용자의 메일 서비스 실행 방지"
description: "Postfix 관리 도구의 가상 권한 기록에서 0755와 0754의 마지막 비트를 비교해요. 실행 비트가 꺼진 경우와 권한을 읽지 못한 경우가 출력에서 어떻게 갈리는지 살펴봐요."
date: "2026-11-25T18:34:14+09:00"
sourcesChecked: "2026-11-25"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "메일", "Postfix", "파일 권한", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 46
---

권한 문자열 `rwxr-xr-x`에서 맨 끝의 `x` 하나를 지우면 누구의 실행 권한이 달라질까요? Postfix의 메일 큐 관리 도구인 `postsuper`를 예로 들어 볼게요. 가상 기록 두 줄에 같은 도구의 권한을 각각 `0755`와 `0754`로 적었어요. 두 줄 모두 소유자와 그룹의 실행 비트는 켜져 있어요.

## 맨 오른쪽 칸의 주인

전통적인 Unix 파일 모드에서 권한을 읽는 순서는 소유자, 그룹, 기타 사용자예요. 여기서 ‘기타 사용자’는 파일의 소유자가 아니고 그 파일의 그룹에도 속하지 않는 사용자를 가리켜요. 마지막 숫자 `5`에는 읽기(4)와 실행(1)이 들어 있고, `4`에는 읽기만 남아요.

[[diagram]]

두 줄은 별개의 가상 사례예요. 그림의 `other-x=clear`는 둘째 기록에서 기타 사용자의 실행 비트가 꺼져 있다는 뜻이에요. 특정 계정이 이 도구를 쓸 수 있는지 살피려면 파일의 소유자, 계정의 그룹, 별도로 적용되는 접근 제어와 프로그램 자체의 권한 검사도 함께 봐야 해요.

## 메일 서비스마다 살필 곳이 달라요

KISA의 2026년 가이드 111\~112쪽은 U-46의 중요도를 **상**으로 분류하고 Solaris, Linux, AIX, HP-UX 등을 대상으로 들어요. 메일 큐는 전송을 기다리는 메시지를 보관하는 곳이에요. 이 항목은 SMTP 서비스를 쓸 때 일반 사용자가 큐 처리를 실행하는 `q` 옵션을 제한하는지 다뤄요. 가이드는 일반 사용자의 메일 서비스 실행을 막는 설정이 있으면 양호, 그 설정이 없으면 취약으로 판단해요.

서비스를 쓰지 않는 경우 가이드는 중지와 비활성화를 안내해요. 메일 서비스를 사용한다면 제품에 따라 확인할 설정이나 파일이 달라요. Sendmail 사례는 `/etc/mail/sendmail.cf`의 `PrivacyOptions`에 `restrictqrun`이 있는지 살펴봐요. Postfix 사례는 `/usr/sbin/postsuper`, Exim 사례는 `/usr/sbin/exiqgrep`의 기타 사용자 실행 권한을 다뤄요. 아래 실습에서는 Postfix 사례에서 쓰인 **파일 모드 한 자리**를 가상 자료로 읽어요.

## 권한을 읽은 경우와 읽지 못한 경우

ZIP을 빈 폴더에 풀면 `u46_mode_record.py`, `u46_modes.txt`, `u46_invalid.txt`, `README.md`가 나와요. 그 폴더에서 Python 3.12와 표준 라이브러리로 실행하세요. 입력은 UTF-8 텍스트이고 한 줄에 수집 상태와 모드를 세로줄로 구분해 적어요. 코드가 읽는 대상은 인수로 준 텍스트 파일 한 개예요. 메일 서버 설치, Unix 파일시스템, 관리자 권한은 필요 없어요.

[[download]]

사용하는 셸의 블록 하나를 골라 실행하세요. PowerShell에서 `$LASTEXITCODE`는 방금 끝난 외부 프로그램의 숫자 종료 코드예요. `$?`에는 성공 여부가 담겨요.

```powershell
python -I -B -X utf8 u46_mode_record.py u46_modes.txt
$LASTEXITCODE
```

Bash에서는 같은 명령 바로 다음에 `echo $?`로 숫자를 읽어요.

```bash
python -I -B -X utf8 u46_mode_record.py u46_modes.txt
echo $?
```

어느 셸에서 실행해도 `main(sys.argv[1:])`이 받는 인수는 `u46_modes.txt` 하나예요. `source.read(4097)`은 최대 4,097바이트를 읽고 크기가 4,096바이트를 넘으면 해석을 멈춰요. 크기와 UTF-8 인코딩을 검사한 뒤 `enumerate(lines, 1)`로 첫 줄부터 번호를 붙여요.

```python
import re
import stat
import sys
from pathlib import Path


def describe(line, number):
    fields = line.split("|")
    if len(fields) != 2:
        raise ValueError(f"line {number}: expected state|mode")
    state, value = fields
    if state == "observed":
        if not re.fullmatch(r"0[0-7]{3}", value):
            raise ValueError(f"line {number}: expected four octal digits starting with 0")
        mode = int(value, 8)
        other_x = "set" if mode & stat.S_IXOTH else "clear"
    elif state in ("read-error", "not-collected"):
        if value != "-":
            raise ValueError(f"line {number}: mode must be - for {state}")
        other_x = "unknown"
    else:
        raise ValueError(f"line {number}: unknown collection state")
    return f"{number} state={state} mode={value} other-x={other_x}"


def main(args):
    if len(args) != 1:
        print("usage: u46_mode_record.py FILE", file=sys.stderr)
        return 2
    try:
        with Path(args[0]).open("rb") as source:
            data = source.read(4097)
        if len(data) > 4096:
            raise ValueError("input exceeds 4096 bytes")
        lines = data.decode("utf-8").splitlines()
        if not lines:
            raise ValueError("empty input")
        results = [describe(line, n) for n, line in enumerate(lines, 1)]
    except (OSError, ValueError) as error:
        print("records-emitted=0")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for result in results:
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

둘째 줄 `observed|0754`가 `describe(line, number)`에 들어가면 `number`는 2예요. 세로줄에서 나눈 `state`가 `observed`이므로 `value`에 담긴 문자열 `0754`를 검사해요. 이 실습은 특수 권한을 제외한 일반 권한만 다뤄서 첫 자리는 0, 나머지 세 자리는 0부터 7까지의 숫자를 받아요.

`int(value, 8)`은 문자열을 8진수로 읽어 `mode`에 정수 492를 담아요. Python의 `stat.S_IXOTH`는 기타 사용자 실행 비트에 해당하는 1이에요. `mode & stat.S_IXOTH`에 값을 넣으면 `492 & 1`은 0이어서 `other_x`에는 `clear`가 들어가요. 함수가 돌려준 `2 state=observed mode=0754 other-x=clear`가 `results`의 둘째 항목이자 다음 출력의 둘째 줄이에요.

[[run:1]]

첫째 줄은 같은 계산에 8진수 `0755`가 들어가요. 정수 493의 마지막 비트는 1이라 `set`이 나왔어요. 셋째 줄의 `read-error`는 권한을 조회하다 오류가 났다고 가정한 사례예요. 넷째 줄의 `not-collected`는 조회 자료를 아직 받지 못한 사례예요. 두 경우 모두 `-`가 적힌 모드 칸을 숫자로 바꾸지 않고 `unknown`으로 남겨요. 조회 오류라면 당시 오류 내용을, 미수집이라면 해당 도구의 권한 기록을 확보해야 두 번째 줄처럼 비트를 읽을 수 있어요. 종료 코드 0은 네 입력 줄을 형식에 맞게 처리했다는 뜻이에요.

## 8진수 자리에 8이 들어가면

`u46_invalid.txt`의 둘째 줄은 `observed|0758`이에요. 같은 폴더에서 아래 명령을 실행한 직후 PowerShell에서는 `$LASTEXITCODE`, Bash에서는 `echo $?`로 종료 코드를 읽을 수 있어요.

```text
python -I -B -X utf8 u46_mode_record.py u46_invalid.txt
```

끝자리 8이 허용 범위를 벗어나 정규식 검사를 통과하지 못해요. `int(value, 8)`에 도달하기 전에 예외가 발생하고 `main`이 표준 오류에 줄 번호와 형식 오류를 출력해요.

[[run:2]]

표준 출력의 `records-emitted=0`은 내보낸 권한 기록이 0건이라는 뜻이에요. 종료 코드 2는 입력 오류를 가리켜요. 코드는 모든 줄을 해석해 `results`를 완성한 뒤에 권한 기록을 출력해요. 그래서 유효했던 첫째 줄도 결과로 나오지 않아요. 여기서 다시 살펴볼 곳은 입력 파일 둘째 줄의 표기예요. 유효한 모드를 다시 수집해야 해당 비트가 켜졌는지 읽을 수 있어요.

## 참고 자료

- [한국인터넷진흥원, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Python 3.12 문서, stat 모듈의 기타 사용자 실행 권한](https://docs.python.org/3.12/library/stat.html#stat.S_IXOTH)
