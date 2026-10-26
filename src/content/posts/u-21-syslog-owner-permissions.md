---
title: "U-21: /etc/(r)syslog.conf 파일 소유자 및 권한 설정"
description: "로그 설정 파일의 소유자로 root 외에 bin·sys도 허용하는 공식 기준을 살펴봅니다. 0640 허용 비트와 파일 종류를 가상 자료 여덟 건으로 비교합니다."
date: "2026-10-26T18:47:53+09:00"
sourcesChecked: "2026-10-26"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-21", "Unix", "syslog", "rsyslog", "파일 권한"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 21
---

`bin` 소유의 로그 설정 파일이 `0600`이라면 U-21의 소유자·모드 조건에 들어간다. [앞 항목 U-20](../u-20-inetd-owner-permissions/)처럼 소유자를 root 하나로만 비교하면 이 차이를 놓친다. U-21은 root뿐 아니라 bin과 sys도 허용 소유자로 적고 있다.

로그 설정에는 어떤 메시지를 어느 대상으로 보낼지 정하는 내용이 들어간다. 이 파일을 바꿀 수 있는 주체는 로그 저장을 중단하거나 대량 기록을 유발하는 설정을 넣을 수도 있다. 이 글에서는 설정의 내용 대신 수집한 소유자와 모드가 항목의 조건에 맞는지 비교한다.

## 공식 기준의 소유자 목록부터 맞추기

2026 KISA 상세가이드 48쪽의 U-21은 중요도 ‘상’이며 Solaris·Linux·AIX·HP-UX 등을 대상으로 한다. `/etc/(r)syslog.conf`의 소유자가 **root 또는 bin, sys**이고 권한이 **640 이하**이면 양호다. 소유자 목록이나 권한 조건을 벗어나면 취약이다. 모드 `640`은 8진수 표기다.

괄호의 `(r)`은 syslog와 rsyslog를 함께 나타낸다. 괄호가 들어간 파일 하나를 만들라는 뜻이 아니다. 해당 운영체제의 로그 데몬과 실제 설정 경로를 먼저 정한다.

계정 이름을 수집할 때는 그 운영체제의 UID와 계정 자료가 서로 맞는지도 살핀다. 아래 예제는 소유자 이름을 가정한 JSON을 읽으며 bin·sys의 UID를 특정 숫자로 고정하거나 실제 계정 데이터베이스를 조회하지 않는다. 공식 허용 목록을 설명한다고 해서 운영 파일의 소유자를 bin이나 sys로 바꾸도록 권하는 것도 아니다.

[[diagram]]

현재 소유자와 서비스 실행 계정은 다른 자료다. rsyslog가 어떤 권한으로 메시지를 처리하는지와 설정 파일을 누가 바꿀 수 있는지를 나눠 조사한다.

## 0640에 들어 있는 권한과 빠져야 할 권한

`0640`은 소유자에게 읽기·쓰기, 그룹에게 읽기를 허용한다. 기타 사용자에게는 권한이 없다. 허용 비트의 일부를 줄인 `0600`과 `0440`도 이 비트 범위 안에 들어간다.

| 가상 모드 | 0640에 없는 비트 | 해석 |
| --- | --- | --- |
| `0640` | `000` | 허용 비트 안 |
| `0600` | `000` | 그룹 읽기를 제거한 상태 |
| `0440` | `000` | 소유자 쓰기를 제거한 상태 |
| `0620` | `020` | 그룹 쓰기가 추가됨 |
| `0644` | `004` | 기타 사용자 읽기가 추가됨 |

코드의 `extra = mode & (~0o640 & 0o777)`는 일반 권한 아홉 비트에서 허용 범위 밖에 켜진 비트를 남긴다. `0620`을 대입하면 `020`이 남는다. 모드 문자열을 10진수 크기로 비교하지 않는다. 특수 비트는 별도 분기에서 추가 조사로 남긴다.

설정 파일의 모드와 디렉터리의 탐색 권한, 링크 대상의 속성은 각각 다룬다. ACL이나 상위 경로의 접근 권한이 있으면 그 자료도 필요하다. 이번 비교기는 일반 파일에 기록된 소유자와 모드만 계산한다.

## 가상 로그 설정 자료 여덟 건 비교하기

Python 3.9 이상과 표준 라이브러리만 사용한다. ZIP을 빈 폴더에 풀고 `u21_syslog_records.py`와 `u21_syslog_samples.json`이 있는 폴더에서 실행한다. 관리자 권한이나 실제 로그 서비스는 필요하지 않다.

경로 문자열은 출력에 표시할 이름이다. 프로그램은 `/etc/rsyslog.conf` 같은 경로를 열지 않고 지정한 JSON 파일 하나만 읽으므로 Windows에서도 실습할 수 있다.

[[download]]

Linux·WSL에서는 `python` 대신 `python3`를 사용해도 된다.

```bash
python -I -B -X utf8 u21_syslog_records.py u21_syslog_samples.json
```

ZIP에 포함된 입력은 다음과 같다. 별도로 준비하는 방법을 택했다면 해당 파일이 없는 다른 빈 폴더에 이 내용을 저장한다.

```json
[
  {"path": "/etc/rsyslog.conf", "kind": "file", "owner": "root", "mode": "0640"},
  {"path": "/sample/bin-syslog.conf", "kind": "file", "owner": "bin", "mode": "0600"},
  {"path": "/sample/sys-syslog.conf", "kind": "file", "owner": "sys", "mode": "0440"},
  {"path": "/sample/group-write.conf", "kind": "file", "owner": "root", "mode": "0620"},
  {"path": "/sample/app-owned.conf", "kind": "file", "owner": "app", "mode": "0644"},
  {"path": "/etc/syslog.conf", "kind": "missing", "owner": null, "mode": null},
  {"path": "/etc/rsyslog.d", "kind": "directory", "owner": "root", "mode": "0750"},
  {"path": "/sample/linked.conf", "kind": "symlink", "owner": "root", "mode": "0777"}
]
```

비교기의 전체 코드다.

```python
import argparse
import json
from pathlib import Path
import re
import sys


def validate(item):
    if not isinstance(item, dict) or set(item) != {"path", "kind", "owner", "mode"}:
        raise ValueError("필드는 path, kind, owner, mode여야 한다")
    if not isinstance(item["path"], str) or not item["path"].startswith("/"):
        raise ValueError("경로 표시는 /로 시작하는 문자열이어야 한다")
    if item["kind"] not in ("file", "directory", "missing", "symlink"):
        raise ValueError("파일 종류가 올바르지 않다")
    if item["kind"] == "missing":
        if item["owner"] is not None or item["mode"] is not None:
            raise ValueError("미수집 항목의 소유자와 모드는 null이어야 한다")
        return
    if not isinstance(item["owner"], str) or not item["owner"].strip():
        raise ValueError("수집한 소유자 계정명이 필요하다")
    if not isinstance(item["mode"], str) or not re.fullmatch(r"[0-7]{4}", item["mode"]):
        raise ValueError("모드는 8진수 네 자리 문자열이어야 한다")


def compare(item):
    if item["kind"] == "missing":
        return "미수집", "로그 데몬과 실제 설정 경로 조사"
    if item["kind"] == "directory":
        return "대상 구분", "디렉터리에는 파일의 0640 기준을 적용하지 않음"
    if item["kind"] == "symlink":
        return "대상 조사", "링크 대상 파일의 소유자와 모드 필요"
    mode = int(item["mode"], 8)
    if mode & 0o7000:
        return "추가 조사", "특수 비트가 있어 일반 권한 비교를 보류"
    extra = mode & (~0o640 & 0o777)
    reasons = []
    if item["owner"] not in {"root", "bin", "sys"}:
        reasons.append("허용 소유자 목록 밖")
    if extra:
        reasons.append(f"허용 밖 비트 {extra:03o}")
    if reasons:
        return "기준 차이", ", ".join(reasons)
    return "조건 충족", f"소유자 {item['owner']}, 허용 밖 비트 000"


def main():
    parser = argparse.ArgumentParser(description="명시한 가상 로그 설정 자료만 비교한다")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        items = json.loads(args.input.read_text(encoding="utf-8"))
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
        status, detail = compare(item)
        print(f"{item['path']}: {status}, {detail}")
    print(f"가상 자료 {len(items)}건 비교 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`validate()`는 모든 항목을 출력 전에 검사한다. `missing`이면 소유자와 모드가 `null`이어야 하고 수집한 항목에는 비어 있지 않은 계정명과 네 자리 8진수 문자열이 필요하다. 뒤쪽 항목의 형식이 잘못되면 앞쪽의 비교 결과도 출력하지 않는다.

`compare()`는 미수집·디렉터리·링크를 먼저 분리한다. 예를 들어 `0750`인 `/etc/rsyslog.d`는 파일의 `0640` 기준으로 계산하지 않고 ‘대상 구분’으로 반환한다. 일반 파일이면 특수 비트를 살핀 뒤 소유자 목록과 `extra`를 각각 비교한다.

`/sample/app-owned.conf`는 `owner="app"`, `mode="0644"`다. 소유자 조건과 권한 조건이 모두 어긋나므로 `reasons`에 두 이유가 들어간다. 첫 번째 차이를 발견했다고 뒤의 모드 계산을 건너뛰지 않는다.

[[run:1]]

출력의 처음 세 행은 가정한 root·bin·sys 소유자와 일반 모드가 공식 목록·허용 비트에 들어간 사례다. `group-write.conf`의 `020`은 그룹 쓰기, `app-owned.conf`의 `004`는 기타 사용자 읽기다. 두 번째 파일에는 소유자 차이도 함께 표시된다.

마지막 세 행은 모드 비교로 끝내지 못한 항목이다. `/etc/syslog.conf` 미수집은 서비스 미사용을 입증하지 않는다. 디렉터리 행에는 파일 기준을 적용하지 않았고 링크 행에는 대상 파일의 자료가 더 필요하다. 종료 코드 0과 ‘8건 비교 완료’는 입력 처리를 끝냈다는 뜻이다. 입력 누락·읽기 실패·형식 오류는 2로 끝난다.

생성하는 파일은 없다. 운영 설정을 읽거나 `chown`, `chmod`를 실행하지 않았으며 로그의 실제 생성·저장·전송도 시험하지 않았다. 실제 rsyslog 환경에서는 [설정의 기본 구조](https://docs.rsyslog.com/doc/configuration/basic_structure.html)와 [포함 설정 지시자](https://docs.rsyslog.com/doc/configuration/global/options/rsconf1_includeconfig.html)를 참고해 적용 중인 주 설정과 포함 파일을 함께 조사한다.

## 참고 자료

- [KISA 주요정보통신기반시설 기술적 취약점 분석·평가 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1): 2026년 U-21, 48쪽
- [rsyslog Basic Structure](https://docs.rsyslog.com/doc/configuration/basic_structure.html)
- [rsyslog IncludeConfig](https://docs.rsyslog.com/doc/configuration/global/options/rsconf1_includeconfig.html)
