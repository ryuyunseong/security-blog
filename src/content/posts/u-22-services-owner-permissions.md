---
title: "U-22: /etc/services 파일 소유자 및 권한 설정"
description: "서비스 이름표와 실제 포트 대기를 구분하고, /etc/services의 root·bin·sys 소유자 및 644 권한 기준을 가상 입력으로 비교합니다."
date: "2026-10-27T18:46:03+09:00"
sourcesChecked: "2026-10-27"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-22", "Unix", "services", "파일 권한"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 22
---

`/etc/services`에 `https 443/tcp`가 적혀 있어도 그 컴퓨터가 443번 포트에서 연결을 기다린다고 판단할 수는 없다. 이 파일은 서비스 이름을 포트 번호·프로토콜과 연결하는 이름표다. 실제 대기 소켓과 실행 중인 프로세스는 별도의 자료다.

이름으로 포트를 찾는 프로그램이 변경된 이름표를 사용하면 의도와 다른 번호를 선택할 수 있다. U-22는 이 이름표를 누가 바꿀 수 있는지 점검한다. 파일에 행을 추가하는 행위와 네트워크 서비스를 시작하는 행위를 구분하며 살펴보자.

## 이름표의 한 행과 실제 실행 상태

[Linux services(5)](https://man7.org/linux/man-pages/man5/services.5.html)는 서비스 이름, `번호/프로토콜`, 선택적인 별칭 순서를 설명한다. 다음은 이 글에서 준비한 가상 파일의 일부다.

```text
domain       53/tcp
domain       53/udp
sample       9999/tcp    sample-alias
```

`domain`이라는 이름과 53이라는 번호가 같아도 TCP·UDP 항목은 서로 다르다. `sample-alias`는 같은 TCP 항목을 찾는 다른 이름이다. 조회 결과가 9999라는 것은 이름표의 대응값을 얻었다는 뜻이며 해당 포트의 접속 허용이나 서비스 실행을 보여 주지는 않는다.

[[diagram]]

services를 사용하는 이름 조회 경로와 실제 서비스 상태를 조사하는 경로를 구분한다. 번호를 직접 지정하는 프로그램도 있으므로 이름표 하나가 모든 네트워크 동작을 결정한다고 확대하지 않는다.

## 가상 이름표를 읽어 보기

Python 3.9 이상과 표준 라이브러리만 필요하다. ZIP을 빈 폴더에 풀고 `u22_services_table.py`와 `u22_services_sample.txt`가 함께 있는 폴더에서 실행한다. 권한 비교에 쓸 `u22_services_modes.py`와 JSON도 같은 ZIP에 들어 있다. 입력 파일을 다시 만들 필요는 없다.

[[download]]

```bash
python -I -B -X utf8 u22_services_table.py u22_services_sample.txt
```

Linux·WSL에서는 `python`을 `python3`로 바꿔도 된다. PowerShell에서는 명령 직후 `$LASTEXITCODE`, Bash에서는 바로 다음 줄의 `echo $?`로 종료 코드를 읽는다. 관리자 권한·별도 패키지·서버는 필요하지 않다.

다음은 이름표를 읽는 전체 코드다. 실제 `/etc/services`를 기본값으로 삼지 않고 지정한 가상 파일만 연다.

```python
import argparse
from pathlib import Path
import re
import sys


def parse_table(text):
    entries = {}
    for number, raw in enumerate(text.splitlines(), 1):
        fields = raw.split("#", 1)[0].split()
        if not fields:
            continue
        if len(fields) < 2 or not re.fullmatch(r"[0-9]+/(tcp|udp)", fields[1]):
            raise ValueError(f"{number}행: 번호/프로토콜 형식이 필요하다")
        port_text, protocol = fields[1].split("/")
        port = int(port_text)
        if not 0 <= port <= 65535:
            raise ValueError(f"{number}행: 포트 번호 범위를 벗어났다")
        for name in [fields[0], *fields[2:]]:
            key = (name, protocol)
            if key in entries:
                raise ValueError(f"{number}행: 이름과 프로토콜이 중복됐다")
            entries[key] = port
    return entries


def main():
    parser = argparse.ArgumentParser(description="명시한 가상 서비스 이름표만 읽는다")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        entries = parse_table(args.file.read_text(encoding="utf-8"))
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for key in [("domain", "tcp"), ("domain", "udp"), ("sample-alias", "tcp"), ("unknown", "tcp")]:
        port = entries.get(key)
        print(f"{key[0]}/{key[1]}: {port if port is not None else '등록 없음'}")
    print("이름표 조회 완료, 소켓 접속 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`parse_table()`은 `#` 뒤의 주석과 빈 줄을 제거한 뒤 두 번째 필드를 나눈다. `53/udp`에서 `port_text`는 `"53"`, `protocol`은 `"udp"`가 된다. 키가 `("domain", "udp")`이므로 앞의 TCP 행을 덮어쓰지 않는다. 별칭 `sample-alias`도 `("sample-alias", "tcp")`라는 키로 같은 번호를 가리킨다.

이 실습 파서는 TCP·UDP만 받으며 앞쪽 공백도 허용한다. 같은 이름·프로토콜의 중복 행과 범위 밖 번호는 오류로 처리한다. 실제 C 라이브러리의 전체 파일 해석 규칙을 재현한 코드는 아니다.

[[run:1]]

처음 두 행의 53은 프로토콜이 다른 두 조회 결과다. 세 번째 9999는 별칭을 통한 조회이며 마지막 ‘등록 없음’은 `entries.get()`이 `None`을 반환한 경우다. 포트 번호 0과 조회 실패를 혼동하지 않도록 `port is not None`으로 구분했다. 입력 파일을 전부 해석한 뒤 출력하므로 뒤쪽에 잘못된 행이 있으면 일부 조회만 성공한 것처럼 표시하지 않는다.

## 644의 읽기 허용과 쓰기 제한

2026 KISA 상세가이드 49쪽의 U-22는 중요도 ‘상’이며 Solaris·Linux·AIX·HP-UX 등을 대상으로 한다. `/etc/services`의 소유자가 **root 또는 bin, sys**이고 권한이 **644 이하**이면 양호다. 허용 소유자가 아니거나 권한 조건을 벗어나면 취약이다.

`0644`는 소유자에게 읽기·쓰기, 그룹과 기타 사용자에게 읽기를 허용한다. 읽기 비트를 줄인 `0640`·`0400`도 이 일반 권한 범위에 들어간다. 그룹 쓰기가 있는 `0664`는 `020`, 기타 사용자 쓰기가 있는 `0646`은 `002`가 허용 범위 밖에 남는다. [앞 항목 U-21](../u-21-syslog-owner-permissions/)의 `0640`과는 기타 사용자 읽기 조건이 다르다.

아래 JSON의 소유자는 가정한 계정명이다. bin·sys의 UID를 고정된 숫자로 두지 않으며 실제 점검에서는 대상 OS의 UID와 계정 자료를 대조한다. 소유자를 bin이나 sys로 바꾸라는 조치 지시로 읽지 않는다.

```json
[
  {"case": "root-644", "owner": "root", "mode": "0644"},
  {"case": "bin-640", "owner": "bin", "mode": "0640"},
  {"case": "sys-400", "owner": "sys", "mode": "0400"},
  {"case": "group-write", "owner": "root", "mode": "0664"},
  {"case": "other-write", "owner": "root", "mode": "0646"},
  {"case": "other-owner", "owner": "app", "mode": "0644"}
]
```

이 목록은 **일반 파일로 수집됐다고 가정한 자료**다. 파일 누락·디렉터리·심볼릭 링크는 비교 입력으로 만들지 않았다. 그런 자료는 대상 파일과 링크의 최종 목적지를 먼저 조사하고, 상위 경로·ACL도 따로 살핀다.

```python
import argparse
import json
from pathlib import Path
import re
import sys


def validate(item):
    if not isinstance(item, dict) or set(item) != {"case", "owner", "mode"}:
        raise ValueError("필드는 case, owner, mode여야 한다")
    for field in ("case", "owner"):
        if not isinstance(item[field], str) or not item[field].strip():
            raise ValueError(f"{field} 문자열이 필요하다")
    if not isinstance(item["mode"], str) or not re.fullmatch(r"[0-7]{4}", item["mode"]):
        raise ValueError("모드는 8진수 네 자리 문자열이어야 한다")


def compare(item):
    mode = int(item["mode"], 8)
    if mode & 0o7000:
        return "추가 조사", "특수 비트가 있어 일반 권한 비교를 보류"
    extra = mode & (~0o644 & 0o777)
    differences = []
    if item["owner"] not in {"root", "bin", "sys"}:
        differences.append("허용 소유자 목록 밖")
    if extra:
        differences.append(f"허용 밖 비트 {extra:03o}")
    return ("기준 차이", ", ".join(differences)) if differences else ("조건 충족", "허용 밖 비트 000")


def main():
    parser = argparse.ArgumentParser(description="가정한 services 일반 파일의 소유자와 모드를 비교한다")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        items = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(items, list) or not items:
            raise ValueError("비어 있지 않은 배열이 필요하다")
        for item in items:
            validate(item)
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for item in items:
        state, detail = compare(item)
        print(f"{item['case']}: {state}, {detail}")
    print(f"일반 파일 가상 자료 {len(items)}건 비교 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```bash
python -I -B -X utf8 u22_services_modes.py u22_services_modes.json
```

`validate()`가 목록 전체의 필드와 네 자리 8진수 모드를 검사한 다음 `compare()`를 호출한다. 일반 모드의 `extra = mode & (~0o644 & 0o777)`는 허용되지 않은 비트만 남긴다. `0664`를 넣으면 그룹 쓰기 `020`이 남고 소유자가 `app`이면 계정명 차이도 `differences`에 들어간다. 두 조건은 각각 비교한다.

특수 비트가 있는 경우에는 이 계산보다 앞의 `mode & 0o7000` 분기가 ‘추가 조사’를 반환한다. 특별한 모드를 일반 파일의 양호 결과에 섞지 않는다.

[[run:2]]

root·bin·sys의 세 사례는 가정한 소유자와 일반 모드가 기준에 들어간 결과다. 나머지 세 행은 그룹 쓰기, 기타 사용자 쓰기, 소유자 차이를 각각 드러낸다. ‘6건 비교 완료’와 종료 0은 입력 비교를 끝냈다는 뜻이다. 입력 누락·파일 읽기 실패·형식 오류는 두 프로그램 모두 표준 오류를 남기고 2로 끝난다.

두 프로그램은 파일을 생성하거나 소유자·권한을 바꾸지 않는다. 공개한 이름표와 JSON을 읽었으며 실제 계정 조회·운영 파일 검사·소켓 연결은 수행하지 않았다. 운영 점검에는 적용 중인 파일 경로와 수집한 UID·권한·ACL 자료를 연결해 남긴다.

## 참고 자료

- [KISA 주요정보통신기반시설 기술적 취약점 분석·평가 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1): 2026년 U-22, 49쪽
- [Linux services(5)](https://man7.org/linux/man-pages/man5/services.5.html)
