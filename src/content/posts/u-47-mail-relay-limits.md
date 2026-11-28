---
title: "U-47: 스팸 메일 릴레이 제한"
description: "메일 중계를 맡겨도 되는 주소 대역과 가상 설정 기록을 나란히 놓고 범위가 넓어진 경우와 기록을 읽지 못한 경우를 구별해요."
date: "2026-11-28T18:37:43+09:00"
sourcesChecked: "2026-11-28"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "메일", "Postfix", "CIDR", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 47
---

메일 서버는 자기 도메인으로 온 편지를 받을 수도 있고 다른 도메인으로 가는 편지를 대신 전달할 수도 있어요. 뒤의 동작을 **릴레이(중계)**라고 해요. 누구나 이 서버에 중계를 맡길 수 있다면 스팸 메일도 서버를 거쳐 나갈 수 있어요. 그래서 U-47을 점검할 때는 서버가 어떤 발신 시스템의 중계 요청을 받아들이는지 살펴봐요.

## 같은 시작 주소, 서로 다른 끝 주소

가상의 승인 대장에는 중계를 맡길 수 있는 네트워크가 `192.0.2.0/28`로 적혀 있어요. 이 값과 설정에서 옮겨 적은 `192.0.2.0/27`을 비교해 볼게요. 슬래시 뒤 숫자는 IPv4 주소의 앞쪽 몇 비트가 고정되는지를 나타내요. 32비트 가운데 28비트가 고정되면 뒤의 4비트로 주소 16개를 나타내고 27비트만 고정되면 5비트가 남아서 주소 32개를 나타내요.

[[diagram]]

두 대역 모두 `192.0.2.0`에서 시작해요. 승인 대역은 `192.0.2.15`에서 끝나지만 수집 기록에는 `192.0.2.31`까지 들어 있어요. 이 차이를 발견하면 먼저 어느 대역이 현재 승인된 범위인지, 메일 서버에서 그 목록을 어떤 규칙에 쓰는지 살펴봐요. 주소 16개가 더 적혀 있다는 사실만으로 그 주소에서 보낸 메일이 실제로 전달됐다고 볼 수는 없어요.

## 가이드에서 말하는 릴레이 제한

KISA의 2026년 가이드 113\~115쪽은 U-47의 중요도를 **상**으로 분류하고 Solaris, Linux, AIX, HP-UX 등을 대상으로 들어요. 메일 서비스에 릴레이 제한이 설정돼 있으면 양호, 설정돼 있지 않으면 취약이에요. 메일 서비스를 사용하지 않는 것으로 확인된 경우에는 양호 또는 해당 없음(N/A)으로 볼 수 있어요. 설정 파일을 읽지 못했다면 서비스 사용 여부와 제한 설정은 둘 다 조사할 사항으로 남아요.

가이드의 Postfix 사례는 신뢰하는 네트워크를 적는 `mynetworks`와 수신자 제한 설정을 함께 살펴봐요. Sendmail은 8.9 이상과 그 이전 버전의 사례가 나뉘고 Exim에서는 허용 호스트 목록과 그 목록을 참조하는 접근 제어 규칙을 짝지어 봐요. 아래에서는 이 가운데 주소 목록 한 줄이 승인 대역과 얼마나 겹치는지만 계산해요.

## 주소 목록을 손에 들고 있을 때와 없을 때

실습 ZIP을 빈 폴더에 풀면 `u47_relay_ranges.py` 옆에 두 입력 파일과 `README.md`가 있어요. 그 폴더에서 Python 3.12와 표준 라이브러리만 사용해요. 예제 주소는 RFC 5737의 문서용 대역에서 골랐고 메일 서버나 관리자 권한은 필요 없어요.

`u47_ranges.txt`의 각 줄은 서로 독립된 가상 수집 사례예요. 대역을 읽은 경우에는 `observed|192.0.2.0/28`처럼 세로줄 뒤에 값을 써요. 조회를 시도했지만 실패한 사례는 `read-error|-`, 자료를 수집하지 않은 사례는 `not-collected|-`예요. 실제 점검에서 이 둘을 가르려면 조회 오류 기록이나 수집 대상 목록이 필요해요. 하이픈은 대역을 알 수 없다는 표시예요.

[[download]]

사용하는 셸에 맞춰 한 블록만 실행하세요. PowerShell에서 외부 프로그램의 숫자 종료 코드는 `$LASTEXITCODE`로 읽어요. `$?`에는 성공 여부가 담겨요.

```powershell
python -I -B -X utf8 u47_relay_ranges.py u47_ranges.txt
$LASTEXITCODE
```

Bash에서는 같은 명령을 실행한 직후 `echo $?`로 숫자를 읽을 수 있어요.

```bash
python -I -B -X utf8 u47_relay_ranges.py u47_ranges.txt
echo $?
```

## 둘째 줄에서 주소 16개가 남는 이유

`main(sys.argv[1:])`이 받는 인수는 `u47_ranges.txt` 하나예요. 파일을 열어 최대 4097바이트를 읽고 4096바이트를 넘으면 중단해요. 크기 제한을 통과하면 내용을 UTF-8로 읽어 각 줄을 번호와 함께 `describe`에 넘겨요. 둘째 줄 `observed|192.0.2.0/27`에서는 `state`가 `observed`라서 누락 상태를 처리하는 분기를 지나가요. 이어서 `IPv4Network`가 값을 해석하고 다시 문자열로 바꾼 값이 입력과 같은지 비교해요.

```python
from ipaddress import IPv4Network
from pathlib import Path
import sys


APPROVED = IPv4Network("192.0.2.0/28")


def describe(row, number):
    fields = row.split("|")
    if len(fields) != 2:
        raise ValueError(f"line {number}: expected two fields")
    state, value = fields
    if state in ("read-error", "not-collected") and value == "-":
        return f"{number} state={state} outside=unknown"
    if state != "observed":
        raise ValueError(f"line {number}: invalid state or value")
    try:
        network = IPv4Network(value, strict=True)
        if str(network) != value:
            raise ValueError
    except ValueError:
        raise ValueError(f"line {number}: expected canonical IPv4 CIDR") from None

    first = max(network.network_address, APPROVED.network_address)
    last = min(network.broadcast_address, APPROVED.broadcast_address)
    overlap = max(0, int(last) - int(first) + 1)
    outside = network.num_addresses - overlap
    return f"{number} network={network} listed={network.num_addresses} outside={outside}"


def main(args):
    try:
        if len(args) != 1:
            raise ValueError("expected one input file")
        with Path(args[0]).open("rb") as stream:
            data = stream.read(4097)
        if len(data) > 4096:
            raise ValueError("input exceeds 4096 bytes")
        rows = data.decode("utf-8").splitlines()
        if not rows:
            raise ValueError("empty input")
        results = [describe(row, n) for n, row in enumerate(rows, start=1)]
    except (OSError, UnicodeError):
        print("입력 오류: cannot read UTF-8 file", file=sys.stderr)
    except ValueError as error:
        print(f"입력 오류: {error}", file=sys.stderr)
    else:
        print(*results, sep="\n")
        return 0
    print("records-emitted=0")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

`first`에는 두 시작 주소 중 더 큰 값인 `192.0.2.0`이, `last`에는 두 끝 주소 중 더 작은 값인 `192.0.2.15`가 들어가요. 양 끝을 포함하므로 마지막 숫자로 계산하면 `15 - 0 + 1 = 16`이에요. 겹치는 주소 수인 `overlap`을 전체 32에서 빼면 `outside`가 16이 돼요. 두 대역이 떨어져 있다면 `max(0, ...)`가 겹치는 개수를 0으로 잡아요.

[[run:1]]

실행 기록의 둘째 줄은 `2 network=192.0.2.0/27 listed=32 outside=16`이에요. 첫째 줄은 대역이 승인 대장과 일치해 `outside=0`이고 셋째와 넷째 줄은 모두 `outside=unknown`이에요. 뒤의 두 줄은 `state`를 보면 조회 오류와 미수집을 구별할 수 있어요. 종료 코드 0은 네 줄 모두 입력 형식에 맞아 결과를 출력했다는 뜻이에요.

## 잘못 적은 대역은 결과에서 어떻게 보일까요?

두 번째 입력 파일 `u47_invalid.txt`에는 첫 줄 다음에 `observed|192.0.2.1/28`이 들어 있어요. 대역의 시작 주소 자리에 그 안의 개별 주소를 적은 경우예요. 앞서 사용한 폴더에서 다음 명령을 실행하세요. 바로 이어서 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 종료 코드를 읽어요.

```text
python -I -B -X utf8 u47_relay_ranges.py u47_invalid.txt
```

`strict=True`로 읽으면 둘째 줄에서 오류가 나요. 프로그램은 모든 줄을 해석한 다음에야 `results`를 출력하므로 앞에서 읽은 정상 행도 개별 결과로 내보내지 않아요.

[[run:2]]

표준 오류의 `line 2`는 입력 파일에서 살필 위치예요. 표준 출력의 `records-emitted=0`과 종료 코드 2가 함께 나오면 대역 비교가 끝나기 전에 멈춘 거예요. 이런 경우 원래 수집한 값이 네트워크 대역이었는지 개별 주소였는지부터 살피면 돼요.

## 참고 자료

- [KISA, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Python 3.12 표준 라이브러리, ipaddress](https://docs.python.org/3.12/library/ipaddress.html)
- [RFC 5737, IPv4 Address Blocks Reserved for Documentation](https://datatracker.ietf.org/doc/html/rfc5737)
