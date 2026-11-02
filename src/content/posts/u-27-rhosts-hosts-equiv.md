---
title: "U-27: $HOME/.rhosts, hosts.equiv 사용 금지"
description: "r-command 사용 여부와 신뢰 파일의 소유자·권한·플러스 표기를 분리합니다. 가상 JSON 자료에서 600 밖의 권한 비트와 단독 플러스, 넷그룹 표기를 비교합니다."
date: "2026-11-02T18:37:07+09:00"
sourcesChecked: "2026-11-02"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "접근 제어", "KISA"]
draft: false
series: unix-2026
seriesOrder: 27
---

`backup.example.test analyst`와 `+ +`는 같은 두 칸짜리 설정이라도 신뢰 범위가 다르다. 여기에 파일 소유자와 권한이 더해진다. 내용의 한 줄을 읽는 일과 그 내용을 바꿀 수 있는 계정을 살피는 일은 U-27에서 각각 필요한 비교다.

## 서비스 사용 여부가 먼저 나뉘는 기준

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-27은 ‘$HOME/.rhosts, hosts.equiv 사용 금지’이며 중요도는 ‘상’이다. 항목표와 본문 54~55쪽을 대조했으며 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다.

원문은 rlogin·rsh·rexec 서비스를 사용하지 않으면 양호로 구분한다. 사용하는 경우에는 `/etc/hosts.equiv`와 `$HOME/.rhosts`의 다음 조건을 모두 요구한다.

- 소유자가 root 또는 해당 계정이다.
- 파일 권한이 600 이하이다.
- 파일 설정에 `+` 설정이 없다.

서비스를 사용하면서 이 조건이 적용되지 않으면 취약 기준에 해당한다. `/etc/hosts.equiv`는 서버 설정 파일, `$HOME/.rhosts`는 개별 사용자의 설정 파일로 구분해 조사한다. 실제 운영체제와 서비스가 어떤 파일을 읽는지도 함께 살펴야 한다.

가이드의 서비스 목록을 모든 구현이 같은 방식으로 인증한다는 뜻으로 읽지는 않는다. [Linux rexec(3)](https://man7.org/linux/man-pages/man3/rexec.3.html)는 사용자 이름과 암호를 인증에 사용하는 인터페이스를 설명한다. 아래 코드는 서비스의 사용 여부를 입력값으로 받을 뿐 서비스 조회나 인증을 실행하지 않는다.

[[diagram]]

실제 미사용을 뒷받침하려면 서비스 설정·실행 상태를 조사한 자료가 필요하다. 수집 시점과 적용되는 인증 구성도 함께 남긴다.

## 플러스의 위치와 권한 비트 읽기

[Linux hosts.equiv(5)](https://man7.org/linux/man-pages/man5/hosts.equiv.5.html)는 단독 `+`를 모든 호스트에 대한 와일드카드로 설명하고, `+@netgroup`을 넷그룹 표기로 구분한다. PAM의 적용 설정에 따라서도 단독 플러스의 해석 조건이 달라진다. 두 표기에 모두 플러스가 있다고 해서 같은 접속 범위를 허용한다고 단정하지 않는다.

가이드가 예시로 든 `+ +`는 모든 호스트의 계정, `+ 사용자`는 모든 호스트의 해당 사용자, `호스트 +`는 해당 호스트의 모든 계정에 대한 신뢰를 나타낸다. 실습은 이 중 `+ +`와 `+@operators analyst`를 서로 다른 이유로 표시한다. 넷그룹의 실제 구성원이나 PAM 규칙은 계산하지 않는다.

권한 ‘600 이하’는 권한 비트의 포함 관계로 비교한다. 일반 권한에서 소유자 읽기·쓰기인 `0600` 밖에 비트가 남는지를 계산한다. [Python stat의 권한 비트 설명](https://docs.python.org/3.12/library/stat.html)은 소유자·그룹·기타 사용자의 읽기·쓰기·실행 비트를 구분한다.

| 가상 모드 | `mode & (0o777 & ~0o600)` | 해석 |
| --- | --- | --- |
| `0600` | `000` | 600 밖의 일반 권한 없음 |
| `0660` | `060` | 그룹 읽기·쓰기 존재 |
| `0477` | `077` | 그룹·기타 사용자의 모든 권한 존재 |

`0477`은 8진수 정수로 `0600`보다 작지만 그룹과 기타 사용자에게 권한을 준다. 단순히 `mode <= 0o600`으로 비교하면 이 차이를 놓친다. 특수 비트가 있는 값은 일반 권한 비교와 별도로 조사 대상으로 남긴다.

## JSON의 아홉 사례를 실행하기

Python 3.9 이상과 표준 라이브러리만 사용한다. 실제 실행 환경은 Windows Python 3.12.1이다. Linux 권한을 Windows 파일에 적용하는 실습이 아니라 JSON의 가상 정수·문자열을 비교하는 실습이므로 관리자 권한, 실제 계정, 서버, 별도 패키지가 필요하지 않다.

ZIP을 빈 폴더에 풀고 `u27_trust_inventory.py`와 `u27_trust_inventory.json`이 함께 있는 글별 폴더에서 실행한다. 두 파일은 ZIP에 들어 있다. `.rhosts` 파일이나 홈 디렉터리를 따로 만들지 않는다. 결과 파일을 쓰거나 입력을 수정하지 않으므로 정리할 때는 자신이 압축을 푼 실습 폴더만 대상으로 삼는다.

[[download]]

```bash
python -I -B -X utf8 u27_trust_inventory.py u27_trust_inventory.json
```

PowerShell에서는 명령 직후 `$LASTEXITCODE`로 종료 코드를 읽는다. Linux·WSL에서는 `python3`를 사용하고 직후 `echo $?`로 읽을 수 있다. 파일 이름에 공백이 있는 경로를 직접 인수로 주면 경로 전체를 따옴표로 감싼다. 입력 오류는 표준 오류와 종료 2로 알리며 같은 폴더의 JSON 파일·필드·UID·8진수 표기를 살핀다.

입력의 `serviceUse`는 세 서비스의 사용 여부를 조사했다고 가정한 `used`, `unused`, `unknown`이다. `accountUid`는 해당 계정, `ownerUid`는 파일 소유자의 가상 UID다. `null`은 미수집이며 숫자 0인 root와 다르다. 호스트 이름도 예시 문자열로만 읽고 DNS 조회를 하지 않는다.

```json
[
  {"case": "unused", "serviceUse": "unused", "accountUid": 1001, "ownerUid": null, "mode": null, "text": null},
  {"case": "bounded", "serviceUse": "used", "accountUid": 1001, "ownerUid": 1001, "mode": "0600", "text": "backup.example.test analyst"},
  {"case": "wildcards", "serviceUse": "used", "accountUid": 1001, "ownerUid": 0, "mode": "0600", "text": "+ +"},
  {"case": "netgroup", "serviceUse": "used", "accountUid": 1001, "ownerUid": 0, "mode": "0600", "text": "+@operators analyst"},
  {"case": "group-write", "serviceUse": "used", "accountUid": 1001, "ownerUid": 1001, "mode": "0660", "text": "backup.example.test analyst"},
  {"case": "numeric-trap", "serviceUse": "used", "accountUid": 1001, "ownerUid": 1001, "mode": "0477", "text": "backup.example.test analyst"},
  {"case": "foreign-owner", "serviceUse": "used", "accountUid": 1001, "ownerUid": 1002, "mode": "0600", "text": "backup.example.test analyst"},
  {"case": "negative-rule", "serviceUse": "used", "accountUid": 1001, "ownerUid": 1001, "mode": "0600", "text": "-blocked.example.test analyst"},
  {"case": "unknown-service", "serviceUse": "unknown", "accountUid": 1001, "ownerUid": null, "mode": null, "text": null}
]
```

이 자료의 한 행은 하나의 독립된 비교 사례다. 실제 서버 전체나 두 신뢰 파일을 빠짐없이 수집한 목록은 아니다. 파일 종류·ACL·상위 경로·링크·서비스별 적용 순서도 이 JSON에는 들어 있지 않다.

```python
import argparse
import json
import re
import sys
from pathlib import Path


FIELDS = {"case", "serviceUse", "accountUid", "ownerUid", "mode", "text"}


def load_rows(path):
    raw = path.read_text(encoding="utf-8")
    rows = json.loads(raw)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("행 수")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("필드")
        name = row["case"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]{1,40}", name) or name in seen:
            raise ValueError("사례 이름")
        seen.add(name)
        if row["serviceUse"] not in ("used", "unused", "unknown"):
            raise ValueError("서비스 상태")
        for key in ("accountUid", "ownerUid"):
            value = row[key]
            if key == "ownerUid" and value is None:
                continue
            if type(value) is not int or not 0 <= value <= 4294967294:
                raise ValueError("UID")
        mode = row["mode"]
        if mode is not None and (not isinstance(mode, str) or not re.fullmatch(r"[0-7]{4}", mode)):
            raise ValueError("모드")
        content = row["text"]
        if content is not None and (not isinstance(content, str) or len(content) > 8192):
            raise ValueError("설정 문자열")
    return rows


def content_notes(content):
    deviations, pending = [], []
    for number, line in enumerate(content.splitlines(), 1):
        tokens = line.split()
        if not tokens:
            continue
        if len(tokens) not in (1, 2):
            pending.append(f"{number}행 필드 수")
        for column, token in enumerate(tokens, 1):
            if token == "+":
                deviations.append(f"{number}행 {column}열 단독 +")
            elif token.startswith("+"):
                deviations.append(f"{number}행 {column}열 + 접두 표기")
            elif not re.fullmatch(r"[A-Za-z0-9_.-]+", token) or token.startswith("-"):
                pending.append(f"{number}행 {column}열 추가 구문")
    return deviations, pending


def compare(row):
    if row["serviceUse"] == "unused":
        return "미사용 가정", "파일 조건 비교 생략"
    if row["serviceUse"] == "unknown":
        return "추가 조사", "서비스 사용 여부 미수집"
    deviations, pending = [], []
    owner = row["ownerUid"]
    if owner is None:
        pending.append("소유 UID 미수집")
    elif owner not in (0, row["accountUid"]):
        deviations.append(f"소유 UID {owner} 불일치")
    if row["mode"] is None:
        pending.append("모드 미수집")
    else:
        mode = int(row["mode"], 8)
        extra = mode & (0o777 & ~0o600)
        if extra:
            deviations.append(f"600 밖 비트 {extra:03o}")
        if mode & 0o7000:
            pending.append("특수 비트 별도 조사")
    if row["text"] is None:
        pending.append("설정 문자열 미수집")
    else:
        found, unresolved = content_notes(row["text"])
        deviations.extend(found)
        pending.extend(unresolved)
    if deviations:
        return "기준 이탈 후보", ", ".join(deviations + pending)
    if pending:
        return "추가 조사", ", ".join(pending)
    return "기본 조건 일치", "소유 UID·일반 권한·제한된 문자열 비교 일치"


def main():
    parser = argparse.ArgumentParser(description="가상 r-command 수집 자료 비교")
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    try:
        rows = load_rows(args.inventory)
    except (OSError, UnicodeError, ValueError, TypeError):
        print("입력 오류: JSON 파일·필드·UID·8진수 모드를 살핀다", file=sys.stderr)
        return 2
    counts = dict.fromkeys(("미사용 가정", "기본 조건 일치", "기준 이탈 후보", "추가 조사"), 0)
    for row in rows:
        state, detail = compare(row)
        counts[state] += 1
        print(f"{row['case']}: {state}; {detail}")
    print(f"가상 자료 {len(rows)}건: " + ", ".join(f"{key} {value}건" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`load_rows()`는 모든 행의 필드를 먼저 검사한 뒤 목록을 반환한다. UID에 `True` 같은 불리언을 받지 않으려고 `type(value) is int`를 사용한다. 모드는 네 자리 8진수 문자열만 받고 사례 이름의 중복도 거부한다. 검사가 끝나기 전에는 일부 행의 비교 결과를 출력하지 않는다.

`compare()`에서 `unused`는 첫 분기에 걸려 파일 비교를 생략한다. `unknown`은 다음 분기에서 추가 조사로 남는다. `used`인 `group-write`는 소유 UID 1001이 `accountUid`와 같아 소유자 조건을 지나고 `"0660"`을 8진수로 바꾼 `mode`에서 `extra`가 `0o060`이 된다. 소유자가 맞아도 그룹 읽기·쓰기 비트가 `deviations`에 들어간다.

`content_notes()`는 비어 있지 않은 줄의 공백 구분 칸을 센다. 단독 `+`를 먼저 비교하고 그 뒤 플러스 접두 표기를 나누므로 `+@operators`는 단독 플러스로 기록되지 않는다. 마이너스·넷그룹·주석 등 이 비교기가 완전히 해석하지 않는 구문은 별도 조사할 대상으로 다룬다. 특히 플러스가 들어 있는 복잡한 줄은 후보로 표시할 수 있으며 이것이 실제 인증 규칙의 해석 결과는 아니다.

[[run:1]]

`wildcards`의 출력은 1행의 두 칸에 단독 플러스가 있음을 보여 준다. `netgroup`에는 첫 칸의 플러스 접두 표기만 나온다. 둘 다 가이드의 플러스 설정을 살필 후보지만 두 행이 같은 범위의 접속을 허용했다는 관찰은 아니다.

`numeric-trap`의 `077`은 앞의 표와 일치한다. `foreign-owner`는 권한 `0600`과 별개로 소유 UID 1002가 root도 해당 계정 1001도 아니라 후보가 된다. 후보를 찾은 뒤에도 다른 비교를 계속해 `deviations`와 미해석 항목인 `pending`을 함께 출력한다.

`negative-rule`은 플러스가 없어도 ‘추가 조사’다. 거부 규칙의 순서와 실제 구현을 해석하지 않았기 때문이다. `unknown-service` 역시 사용 여부를 알 수 없어 남겨 둔 행이며 `unused`처럼 비교 생략으로 합치지 않는다.

마지막의 아홉 건은 입력 행 수이고 종료 0은 그 자료의 형식 검사와 분류가 끝났다는 뜻이다. ‘기본 조건 일치’ 한 건도 입력된 세 조건의 제한된 비교다. 운영 점검의 양호·취약 판정에는 실제 서비스 사용 자료와 각 신뢰 파일의 소유자·권한·내용, 적용되는 인증 구성의 대조가 더해진다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux hosts.equiv(5): 호스트·사용자 신뢰 설정](https://man7.org/linux/man-pages/man5/hosts.equiv.5.html)
- [Linux rexec(3): 사용자 이름과 암호를 사용하는 인터페이스](https://man7.org/linux/man-pages/man3/rexec.3.html)
- [Python 3.12 stat: 일반 권한과 특수 비트](https://docs.python.org/3.12/library/stat.html)
