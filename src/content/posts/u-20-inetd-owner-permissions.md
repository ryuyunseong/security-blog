---
title: "U-20: /etc/(x)inetd.conf 파일 소유자 및 권한 설정"
description: "주 설정이 0600이어도 포함된 서비스 파일에는 다른 권한이 남을 수 있습니다. inetd·xinetd·systemd의 조사 경로와 파일·디렉터리 구분을 가상 자료로 살펴봅니다."
date: "2026-10-25T18:37:56+09:00"
sourcesChecked: "2026-10-25"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-20", "Unix", "inetd", "xinetd", "systemd"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 20
---

xinetd의 주 설정 파일을 `0600`으로 관리해도 그 설정에서 불러오는 서비스 파일이 `0644`로 남아 있을 수 있다. 설정을 읽는 경로가 여러 개라면 주 파일 하나의 소유자·권한으로 전체 점검을 끝낼 수 없다.

U-20은 서비스 설정 파일을 관리자만 제어하도록 보호하는 항목이다. 오늘은 **어느 설정을 조사할지 정하는 일**과 **수집한 파일 속성을 비교하는 일**을 나눠 살펴본다.

## 실행 방식에 따라 달라지는 조사 경로

2026 KISA 상세가이드 46~47쪽의 U-20은 중요도 ‘상’이다. 대상은 Solaris·Linux·AIX·HP-UX 등이며 판단 기준은 `/etc/(x)inetd.conf`의 소유자가 root이고 권한이 `600` 이하인 경우 양호다. root가 아니거나 권한 조건을 벗어나면 취약이다. 여기서 `600`은 8진수 권한 표기다.

`(x)inetd`는 inetd와 xinetd를 함께 나타낸 표현이다. 이름에 괄호가 들어간 실제 파일 하나를 찾는다는 뜻이 아니다. 가이드의 조치 사례도 실행 방식별로 경로를 나눈다.

| 실행 방식 | 가이드가 제시한 조사 경로 | 함께 살필 내용 |
| --- | --- | --- |
| inetd | `/etc/inetd.conf` | 실제 사용 중인 inetd와 설정 위치 |
| xinetd | `/etc/xinetd.conf`, `/etc/xinetd.d/` 안의 파일 | 주 설정의 include·includedir 관계 |
| systemd | `/etc/systemd/system.conf`, `/etc/systemd/` 안의 파일 | 관리자 설정과 유닛·드롭인, 파일 종류 구분 |

[xinetd.conf(5)](https://manpages.debian.org/trixie/xinetd/xinetd.conf.5.en.html)의 `includedir`는 지정한 디렉터리의 파일을 읽는다. 파일명에 점이 있거나 끝이 `~`인 파일은 제외하고 C 로캘의 알파벳순으로 읽는 조건도 있다. 실제 포함 경로와 파일 목록을 수집해야 주 설정과 서비스별 설정의 관계를 알 수 있다.

[[diagram]]

그림의 주 설정과 서비스 파일은 서로 다른 파일이다. 같은 디렉터리에 있다는 이유로 소유자와 모드가 함께 바뀌지는 않는다.

파일이 없다는 결과는 서비스 미사용의 증거와 구분한다. 설치 상태·실행 방식·설정 경로를 대조한 뒤 해당 여부를 남긴다. [systemd의 관리자 설정 문서](https://www.freedesktop.org/software/systemd/man/latest/systemd-system.conf.html)는 `system.conf`와 `system.conf.d` 드롭인을 설명한다. `system.conf`를 개별 서비스의 `.service` 유닛 파일과 같은 역할로 보지 않는다. 이 링크의 최신 문서는 systemd 262 기준이며 실제 대상 버전의 설정 위치도 대조해야 한다.

## 파일의 0600과 디렉터리의 탐색 권한

`0600`은 소유자의 읽기·쓰기만 허용한다. `0400`은 이 허용 비트 안에 들어가고 `0644`에는 그룹·기타 사용자의 읽기 비트 `044`가 더 있다. U-20에서는 다른 사용자의 쓰기뿐 아니라 공식 기준의 전체 허용 비트와 비교한다.

가이드 47쪽에는 `chmod -R 600` 형태의 재귀 조치 예시가 있다. 이 명령을 디렉터리 전체에 그대로 적용하는 실습은 하지 않는다. 디렉터리에 탐색 권한이 없으면 그 안의 파일 경로를 해석하지 못할 수 있다. [path_resolution(7)](https://man7.org/linux/man-pages/man7/path_resolution.7.html)은 경로 중간 디렉터리의 검색 권한을 설명한다. 파일 목록과 종류, 서비스가 읽는 경로를 정한 뒤 파일별 변경 영향과 배포판 관리 방식을 검토한다.

링크는 실제 대상 파일과 상위 경로를 조사한다. 추가 ACL이 있다면 그 항목과 유효 권한도 필요하다. 아래 코드는 가상 자료의 일반 모드만 비교하며 이런 접근 조건을 수집하지 않는다.

## 일곱 개의 가상 수집 항목 읽기

Python 3.9 이상과 표준 라이브러리만 필요하다. ZIP을 빈 폴더에 풀면 `u20_superdaemon_records.py`와 `u20_superdaemon_samples.json`이 나온다. 두 파일이 있는 폴더에서 실행하며 관리자 권한은 필요하지 않다.

JSON의 경로는 화면에 표시할 문자열이다. 프로그램은 그 경로를 열거나 서비스를 실행하지 않는다. 운영체제 속성을 측정하는 코드가 아니어서 Windows에서도 실행할 수 있다.

[[download]]

기본 명령은 다음과 같다. Linux·WSL에서는 `python` 대신 `python3`를 사용해도 된다.

```bash
python -I -B -X utf8 u20_superdaemon_records.py u20_superdaemon_samples.json
```

ZIP에 들어 있는 입력은 아래와 같다. 직접 만드는 대안은 이 파일이 없는 별도 폴더에서만 사용한다.

```json
[
  {
    "path": "/etc/xinetd.conf",
    "kind": "file",
    "uid": 0,
    "mode": "0600"
  },
  {
    "path": "/etc/xinetd.d/example",
    "kind": "file",
    "uid": 0,
    "mode": "0644"
  },
  {
    "path": "/etc/inetd.conf",
    "kind": "missing",
    "uid": null,
    "mode": null
  },
  {
    "path": "/etc/systemd/system.conf",
    "kind": "file",
    "uid": 0,
    "mode": "0400"
  },
  {
    "path": "/etc/xinetd.d",
    "kind": "directory",
    "uid": 0,
    "mode": "0700"
  },
  {
    "path": "/etc/xinetd.d/other",
    "kind": "file",
    "uid": 1001,
    "mode": "0660"
  },
  {
    "path": "/etc/xinetd.d/linked",
    "kind": "symlink",
    "uid": 0,
    "mode": "0777"
  }
]
```

주 설정과 포함 파일의 모드를 다르게 두었다. `missing`은 경로가 없다고 가정한 사례이며 UID·모드에 `null`을 넣어 미수집을 나타낸다. 실제 서비스가 사용하지 않는다는 뜻으로 바꾸지 않는다.

다음은 실행 파일 전체다.

```python
import argparse
import json
from pathlib import Path
import re
import sys


def validate(item):
    if not isinstance(item, dict) or set(item) != {"path", "kind", "uid", "mode"}:
        raise ValueError("필드는 path, kind, uid, mode여야 한다")
    if not isinstance(item["path"], str) or not item["path"].startswith("/"):
        raise ValueError("경로 표시는 /로 시작하는 문자열이어야 한다")
    if item["kind"] not in ("file", "directory", "missing", "symlink"):
        raise ValueError("종류가 올바르지 않다")
    if item["kind"] == "missing":
        if item["uid"] is not None or item["mode"] is not None:
            raise ValueError("미수집 항목의 UID와 모드는 null이어야 한다")
        return
    if type(item["uid"]) is not int or item["uid"] < 0:
        raise ValueError("UID는 0 이상의 정수여야 한다")
    if not isinstance(item["mode"], str) or not re.fullmatch(r"[0-7]{4}", item["mode"]):
        raise ValueError("모드는 8진수 네 자리 문자열이어야 한다")


def inspect(item):
    if item["kind"] == "missing":
        return "미수집", "설치·사용 여부와 실제 적용 경로 조사"
    if item["kind"] == "directory":
        return "대상 구분", "디렉터리는 파일의 0600 기준으로 판정하지 않음"
    if item["kind"] == "symlink":
        return "대상 조사", "링크가 가리키는 실제 파일 자료 필요"
    mode = int(item["mode"], 8)
    if mode & 0o7000:
        return "추가 조사", "특수 비트가 있어 일반 권한 비교를 보류"
    extra = mode & (~0o600 & 0o777)
    differences = []
    if item["uid"] != 0:
        differences.append("root 소유가 아님")
    if extra:
        differences.append(f"허용 밖 비트 {extra:03o}")
    return ("기준 차이", ", ".join(differences)) if differences else ("조건 충족", "UID 0, 허용 밖 비트 000")


def main():
    parser = argparse.ArgumentParser(description="명시한 가상 수집 자료만 읽는다")
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
        status, detail = inspect(item)
        print(f"{item['path']}: {status}, {detail}")
    print(f"가상 자료 {len(items)}건 비교 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`main()`은 입력 파일을 필수 인수로 받는다. 인수가 빠져도 운영 설정 경로로 넘어가지 않는다. `validate()`가 일곱 항목의 형식을 모두 검사한 뒤에야 결과를 출력하므로 뒤쪽 자료가 잘못됐을 때 앞쪽 항목만 성공처럼 출력하지 않는다.

`inspect()`의 첫 분기는 `missing`, 다음은 디렉터리와 링크다. 이 경우 일반 파일의 권한 비교까지 진행하지 않는다. 예를 들어 `/etc/xinetd.d`의 `0700`은 파일의 `0600` 초과로 분류하지 않고 ‘대상 구분’으로 돌려준다. 디렉터리가 안전하다고 판정한 결과도 아니다.

일반 파일은 특수 비트를 먼저 걸러 낸 뒤 `extra = mode & (~0o600 & 0o777)`로 허용 밖 비트를 구한다. `/etc/xinetd.d/example`의 `0644`를 대입하면 `044`가 남는다. `other` 항목은 UID 1001과 `0660`이므로 소유자 차이와 `060`의 권한 차이를 함께 `differences`에 넣는다.

[[run:1]]

주 파일 `/etc/xinetd.conf`는 조건 충족이지만 서비스 파일 `example`은 기준 차이가 나온다. 출력은 두 파일을 개별적으로 비교한 결과다. 이 가상 목록만으로 실제 includedir가 읽는 전체 파일을 조사했다고 볼 수는 없다.

`system.conf`의 `0400`도 허용 밖 비트는 `000`이다. 읽기 전용 모드가 현재 운영에 적합한지는 설정 관리·갱신 절차와 함께 판단한다. 링크의 ‘대상 조사’와 미수집의 ‘설치·사용 여부 조사’는 비교를 끝낸 `000`과 다른 상태다.

마지막 7건과 종료 코드 0은 입력 항목을 끝까지 비교했다는 뜻이다. JSON 오류·필드 누락·읽기 실패·인수 누락은 2로 끝난다. 생성하는 파일은 없으며 운영 설정의 내용·소유자·권한에는 손대지 않는다.

## 참고 자료

- [KISA 주요정보통신기반시설 기술적 취약점 분석·평가 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1): 2026년, U-20, 46~47쪽
- [Debian xinetd.conf(5)](https://manpages.debian.org/trixie/xinetd/xinetd.conf.5.en.html)
- [systemd-system.conf](https://www.freedesktop.org/software/systemd/man/latest/systemd-system.conf.html)
- [Linux path_resolution(7)](https://man7.org/linux/man-pages/man7/path_resolution.7.html)
