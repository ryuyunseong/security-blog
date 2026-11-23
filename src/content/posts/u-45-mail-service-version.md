---
title: "U-45: 메일 서비스 버전 점검"
description: "같은 설치 버전도 패키지 공급 경로에 따라 비교할 기준이 달라져요. 가상 설치 기록에서 버전 불일치, 기준 자료 누락, 조회 오류가 어떻게 다른 출력으로 남는지 살펴봐요."
date: "2026-11-23T18:35:54+09:00"
sourcesChecked: "2026-11-23"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "메일", "Postfix", "패키지", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 45
---

메일 서비스의 설치 버전 칸에 `1.0-2`가 적혀 있다고 해 볼게요. 이 숫자 옆에 **어디서 받은 패키지인지**를 적으면 비교할 대상이 정해져요. 아래 실습에서는 설치 버전을 그대로 두고 공급 경로만 바꿔 두 기록을 각각 어떤 기준값과 비교하는지 살펴봐요.

## 제품 버전에서 패키지 기록으로

KISA의 2026년 가이드 105\~110쪽에서 U-45 ‘메일 서비스 버전 점검’은 중요도 **상**이고 대상은 Solaris, Linux, AIX, HP-UX 등이에요. 메일 서비스 버전이 최신이면 양호, 최신이 아니면 취약으로 판단해요. 사용 중인 서비스는 패치 관리 정책에 따라 주기적으로 갱신하고 사용하지 않을 때는 중지와 비활성화를 검토하도록 안내해요. 실제 패치를 적용하기 전에는 시스템과 메일 서비스에 미칠 영향도 살펴야 해요.

가이드의 Linux용 Postfix 사례는 `postconf mail_version`으로 제품 버전을 조회한 뒤 해당 운영체제의 패키지 공급처로 안내해요. 두 자료는 쓰임이 달라요. 예를 들어 Debian은 안정판에 포함된 버전을 유지하면서 보안 수정 사항을 반영하기도 해요. 그래서 Debian 패키지를 쓰는 경우에는 설치한 패키지의 전체 버전을 해당 배포판 보안 공지의 버전과 대조하거나 패키지 변경 기록을 살펴봐요.

## 같은 설치값에 기준이 둘인 이유

그림의 `lab-a`와 `lab-b`는 한 메일 프로그램을 서로 다른 경로에서 공급한다고 가정한 예예요. 각 경로의 기준값을 미리 적어 두고 설치 기록과 글자 단위로 대조했어요. 경로 이름과 버전은 모두 실습용이에요.

[[diagram]]

그림에서 `different`는 두 값이 다르다는 뜻이에요. 어느 버전이 더 최근인지 알아보려면 그 공급처의 버전 비교 규칙과 해당 시점의 배포 기록이 필요해요. 한편 보안 공지에 특정 수정이 포함됐다는 기록과 그날 최신 패키지를 쓰는지는 서로 다른 질문이에요.

## 두 번째 입력 줄을 따라가요

빈 폴더에 ZIP을 풀면 `u45_package_record.py`, `u45_inventory.txt`, `u45_invalid.txt`와 `README.md`가 나와요. 그 폴더에서 Python 3.12와 표준 라이브러리로 실행해요. 메일 서버나 관리자 권한은 필요 없어요. 입력은 UTF-8 텍스트로, 각 줄에 공급 경로, 수집 상태, 설치 버전을 세로줄 하나씩으로 구분해 적었어요.

[[download]]

사용 중인 셸의 블록 하나를 골라 실행하세요. PowerShell에서 외부 프로그램의 숫자 종료 코드는 `$LASTEXITCODE`로 읽어요. `$?`에는 성공 여부가 담겨요.

```powershell
python -I -B -X utf8 u45_package_record.py u45_inventory.txt
$LASTEXITCODE
```

Bash에서는 같은 명령이 끝난 자리에서 `echo $?`로 숫자를 읽을 수 있어요.

```bash
python -I -B -X utf8 u45_package_record.py u45_inventory.txt
echo $?
```

`main(sys.argv[1:])`에는 파일명 `u45_inventory.txt`가 유일한 인수로 들어가요. `stream.read(8193)`은 최대 8,193바이트를 읽고 길이가 8,192바이트를 넘으면 입력을 거절해요. 크기에 맞는 파일을 UTF-8로 해석하고 나면 `enumerate(lines, 1)`이 첫 줄부터 번호를 붙여요.

```python
import re
import sys
from pathlib import Path

REFERENCE = {"lab-a": "1.0-2", "lab-b": "1.0-3"}


def compare_record(line, number):
    parts = line.split("|")
    if len(parts) != 3:
        raise ValueError(f"line {number}: expected channel|state|installed")
    channel, state, installed = parts
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,23}", channel):
        raise ValueError(f"line {number}: invalid channel")
    reference = REFERENCE.get(channel)
    if state == "observed":
        if not re.fullmatch(r"[0-9][A-Za-z0-9.+:~-]{0,47}", installed):
            raise ValueError(f"line {number}: invalid version token")
        if reference is None:
            result = "no-reference"
        elif installed == reference:
            result = "match"
        else:
            result = "different"
    elif state in ("read-error", "not-collected"):
        if installed != "-":
            raise ValueError(f"line {number}: missing value must be -")
        result = state
    else:
        raise ValueError(f"line {number}: invalid collection state")
    return f"{number} {channel} installed={installed} reference={reference or '-'} {result}"


def main(args):
    if len(args) != 1:
        print("usage: u45_package_record.py FILE", file=sys.stderr)
        return 2
    try:
        with Path(args[0]).open("rb") as stream:
            data = stream.read(8193)
        if len(data) > 8192:
            raise ValueError("input exceeds 8192 bytes")
        lines = data.decode("utf-8").splitlines()
        if not lines:
            raise ValueError("empty input")
        output = [compare_record(line, i) for i, line in enumerate(lines, 1)]
    except (OSError, ValueError) as error:
        print("records-emitted=0")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for item in output:
        print(item)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

두 번째 줄 `lab-b|observed|1.0-2`를 `compare_record`가 나누면 `channel`은 `lab-b`, `state`는 `observed`, `installed`는 `1.0-2`예요. 경로 이름이 형식에 맞아 `REFERENCE.get(channel)`에서 `1.0-3`을 꺼내요. 설치값도 실습에서 허용한 표기에 맞으므로 이제 두 값을 비교할 수 있어요.

기준값이 있으니 `reference is None`은 거짓이에요. 다음 조건 `installed == reference`에 실제 값을 넣으면 `"1.0-2" == "1.0-3"`도 거짓이어서 `result`에는 `different`가 남아요. 함수가 돌려준 문자열은 `output`의 두 번째 항목이 돼요. 아래 기록의 둘째 줄 `2 lab-b installed=1.0-2 reference=1.0-3 different`가 그 값이에요.

[[run:1]]

첫 줄의 `lab-a`는 기준값도 `1.0-2`라서 `match`가 나왔어요. 셋째 줄에서 설치값은 똑같지만 `lab-c`에 해당하는 기준이 없어 `no-reference`가 나와요. 이때 필요한 건 설치값을 다시 읽는 일보다 비교할 공급 경로와 기준 자료를 확보하는 일이에요.

마지막 두 줄은 설치값 쪽 사정이 달라요. `read-error`는 조회를 시도했으나 실패했다고 가정한 기록이고 `not-collected`는 조회 자료를 아직 수집하지 않았다는 기록이에요. 둘 다 설치값 칸을 `-`로 비워 두고 사유를 출력해요. 종료 코드 0은 이렇게 다섯 줄의 대조를 마쳤다는 뜻이에요. 이 코드가 읽은 범위는 지정한 파일과 가상 기준표까지예요.

## 수집 오류 옆에 버전이 남아 있다면

`u45_invalid.txt`는 둘째 줄에 `lab-b|read-error|1.0-2`를 담고 있어요. 조회 실패로 표시한 칸에 설치값도 들어간 경우예요. 같은 폴더에서 다음 명령을 실행한 직후 PowerShell에서는 `$LASTEXITCODE`, Bash에서는 `echo $?`로 종료 코드 2를 읽을 수 있어요.

```text
python -I -B -X utf8 u45_package_record.py u45_invalid.txt
```

`read-error` 분기에서 `installed != "-"`가 참이므로 입력 오류가 발생해요. `output`을 모두 완성한 뒤에만 결과 줄을 내보내는 코드라 앞서 읽은 첫 줄까지 보류해요.

[[run:2]]

표준 출력의 `records-emitted=0`은 내보낸 비교 결과가 없다는 뜻이에요. 표준 오류의 `line 2: missing value must be -`는 둘째 줄에서 수집 상태와 설치값이 충돌한 자리를 짚어요. 실제 기록에 이런 조합이 보이면 그 값이 이전 수집분인지부터 살펴야 해요. 같은 시점에 얻은 설치 기록과 해당 공급 경로의 기준 자료가 모여야 버전을 대조할 수 있어요.

## 참고 자료

- [한국인터넷진흥원, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Debian Security FAQ](https://www.debian.org/security/faq)
