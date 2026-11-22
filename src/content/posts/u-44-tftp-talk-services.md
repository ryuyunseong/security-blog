---
title: "U-44: tftp, talk 서비스 비활성화"
description: "점검표에 talk 행이 없고 ntalk 행에 조회 오류가 남았다면 두 칸을 어떻게 읽을까요? 가상 자료를 세 서비스 이름에 맞춰 놓고 비활성 기록, 빠진 행, 조회 오류를 구별해요."
date: "2026-11-22T18:38:43+09:00"
sourcesChecked: "2026-11-22"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "TFTP", "서비스 관리", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 44
---

가상 점검표에서 `talk`를 찾으면 `ntalk` 한 줄만 눈에 띄어요. 철자가 겹쳐도 점검표에서는 서로 다른 서비스예요. U-44의 제목은 ‘tftp, talk 서비스 비활성화’지만 판단 기준에는 `ntalk`도 들어가므로 이름을 하나씩 맞춰 봐야 해요.

## 점검표에는 세 칸이 필요해요

KISA의 2026년 가이드 102\~104쪽에서 U-44는 중요도 **상**이고 대상은 Solaris, Linux, AIX, HP-UX 등이에요. tftp, talk, ntalk 서비스가 비활성화된 경우를 양호로, 활성화된 경우를 취약으로 판단해요. 예를 들어 앞의 두 서비스가 꺼져 있어도 ntalk가 켜져 있으면 세 서비스가 모두 비활성이라는 조건을 충족하지 못해요.

tftp는 인증 절차 없이 파일을 전송하는 프로토콜로, 가이드에는 부팅이나 설치에 쓸 초기 파일을 전달하는 용도가 나와요. talk와 ntalk는 서로 다른 시스템의 사용자가 대화할 때 쓰는 서비스예요. 어떤 자료에서 상태를 읽을지는 운영체제와 서비스 관리자에 따라 달라져요. 가이드의 Linux 사례만 보더라도 `inetd`, `xinetd`, `systemd`를 나눠 설명해요.

아래 그림의 왼쪽 표는 가상 자료 `short`에 들어 있는 두 행이에요. 작은 화면에서는 이 표가 위에 놓여요. `tftp`는 비활성으로 관찰했다고 가정했고 `ntalk`는 조회 중에 오류가 났다고 적었어요. 이 두 행을 점검 대상 전체에 맞춰 놓으면 빠진 이름이 보여요.

[[diagram]]

`ntalk`의 조회 오류를 살필 때는 조회 당시의 오류 메시지가 실마리가 돼요. 반면 `talk`에는 조회 결과 자체가 없으므로 어느 범위의 자료를 받았는지부터 살펴야 해요. 두 칸을 모두 비활성으로 채워 넣으면 이 차이가 사라져요.

## 받은 순서가 달라도 같은 이름끼리 대조하기

실습 ZIP을 빈 폴더에 풀면 `u44_service_rows.py`, 기본 입력 `u44_samples.json`, 중복 사례 `u44_duplicate.json`과 `README.md`가 나와요. 파일들이 들어 있는 폴더에서 Python 3.12로 실행하세요. 표준 라이브러리만 쓰며 서비스 설치나 관리자 권한은 필요 없어요. 프로그램은 지정한 UTF-8 JSON을 열어 이미 적힌 가상 관찰값을 읽어요.

[[download]]

PowerShell에서는 아래 명령을 실행한 뒤 바로 다음 줄의 `$LASTEXITCODE`로 숫자 종료 코드를 읽어요. PowerShell의 `$?`에는 성공 여부가 담겨요.

```powershell
python -I -B -X utf8 u44_service_rows.py u44_samples.json
$LASTEXITCODE
```

Bash를 쓴다면 이 블록 하나를 실행하면 돼요. `echo $?`는 바로 앞 명령의 종료 코드를 보여 줘요.

```bash
python -I -B -X utf8 u44_service_rows.py u44_samples.json
echo $?
```

기본 입력에서 `short`의 값은 `[["tftp", "inactive"], ["ntalk", "query-error"]]`예요. 입력에 쓸 수 있는 상태는 `active`, `inactive`, `query-error`이고, 행이 빠졌을 때 표시하는 `no-row`는 프로그램이 출력할 때 붙여요.

```python
import json
import sys
from pathlib import Path

SERVICES = ("tftp", "talk", "ntalk")
STATES = ("active", "inactive", "query-error")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def summarize(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    observed = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError("expected [service, state]")
        service, state = row
        if service not in SERVICES or state not in STATES:
            raise ValueError("unknown service or state")
        if service in observed:
            raise ValueError(f"duplicate service: {service}")
        observed[service] = state
    fields = [f"{name}={observed.get(name, 'no-row')}" for name in SERVICES]
    return " ".join(fields)


def main(args):
    if len(args) != 1:
        print("usage: u44_service_rows.py FILE", file=sys.stderr)
        return 2
    try:
        with Path(args[0]).open("rb") as stream:
            raw = stream.read(8193)
        if len(raw) > 8192:
            raise ValueError("input exceeds 8192 bytes")
        samples = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys)
        if not isinstance(samples, dict) or not samples:
            raise ValueError("expected named samples")
        lines = []
        for label, rows in samples.items():
            if not label.isascii() or not label.isalpha() or len(label) > 20:
                raise ValueError("invalid sample name")
            lines.append(f"{label}: {summarize(rows)}")
    except (OSError, ValueError, RecursionError) as error:
        print("samples-emitted=0")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

명령 끝의 `u44_samples.json`이 `main(sys.argv[1:])`의 유일한 인수가 돼요. `stream.read(8193)`는 8,193바이트까지만 읽고 길이가 8,192바이트를 넘으면 입력을 거절해요. JSON을 해석할 때 같은 키가 두 번 나오면 `unique_keys`에서 멈춰요. 크기와 형식에 맞으면 `samples.items()`에서 첫 묶음의 이름 `short`와 두 행을 꺼내 `summarize(rows)`에 넘겨요.

첫 행의 `service`는 `"tftp"`, `state`는 `"inactive"`예요. 둘 다 허용된 값이고 빈 딕셔너리 `observed`에 `"tftp"`가 없으므로 `observed["tftp"] = "inactive"`가 돼요. 둘째 행도 같은 검사를 거쳐 `"ntalk"`에 `"query-error"`를 저장해요. 이제 `observed`에는 두 이름만 있어요.

출력 순서를 정하는 `SERVICES`는 `("tftp", "talk", "ntalk")`예요. 가운데 이름을 넣은 `observed.get("talk", 'no-row')`는 키가 없어 기본값을 돌려줘요. 바로 뒤의 `ntalk`에는 이미 저장한 오류값이 들어가요. `summarize`가 세 필드를 공백으로 이으면 `main`이 이름을 붙여 `lines`에 보관해요. 모든 묶음을 다 읽은 뒤 출력한 첫 줄은 `short: tftp=inactive talk=no-row ntalk=query-error`예요.

[[run:1]]

`full`의 원래 순서는 ntalk, talk, tftp예요. 출력에서는 기준 순서대로 정렬돼 마지막 칸에 `ntalk=active`가 남아요. `quiet`에서는 세 칸 모두 비활성으로 기록돼 있어요. 이 명령이 돌려준 0은 세 가상 묶음을 끝까지 읽었다는 뜻이에요. 실제 호스트의 U-44 판정에는 그 호스트에서 얻은 서비스 상태 자료가 필요해요.

## talk 행이 두 번 들어온 경우

다른 입력에는 `repeat` 묶음에 `["talk", "inactive"]`와 `["talk", "active"]`가 이어져요. 이 자료에는 관찰 시각이 없어서 뒤에 적힌 값을 최신 상태로 고를 근거가 없어요. 같은 폴더에서 다음 명령을 실행한 직후 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 2를 읽을 수 있어요.

```text
python -I -B -X utf8 u44_service_rows.py u44_duplicate.json
```

둘째 행에서도 `service`는 `"talk"`예요. `service in observed`가 참이 되는 순간 예외가 발생해서 첫 값을 덮어쓰지 않아요.

[[run:2]]

표준 오류의 `duplicate service: talk`는 어느 이름에서 입력을 거절했는지 알려 줘요. 앞선 `short`는 이미 읽었지만 `main`은 정상 행을 한꺼번에 출력하기 때문에 표준 출력에는 `samples-emitted=0`만 남아요. 이 경우에는 두 행이 각각 어느 시스템과 시각의 관찰인지 알아낸 뒤 같은 묶음에 놓아도 되는지 정할 수 있어요.

## 참고 자료

- [한국인터넷진흥원, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
