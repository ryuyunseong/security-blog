---
title: "U-24: 사용자, 시스템 환경변수 파일 소유자 및 권한 설정"
description: "셸 시작 파일을 누가 바꿀 수 있는지 소유자와 쓰기 비트로 나누고, 링크·ACL 자료가 빠진 사례를 별도로 분류합니다."
date: "2026-10-29T18:46:57+09:00"
sourcesChecked: "2026-10-29"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "파일 권한", "환경변수", "KISA"]
draft: false
series: unix-2026
seriesOrder: 24
---

사용자 홈의 `.bashrc`에 명령을 추가할 수 있는 사람은 그 파일을 읽는 다음 셸의 동작에 영향을 줄 수 있다. 파일 내용이 실행 경로를 바꾸거나 다른 명령을 호출한다면 읽기 권한보다 쓰기 권한의 범위가 먼저 문제 된다. U-24는 홈 디렉터리의 환경변수 파일을 누가 소유하고 누가 바꿀 수 있는지 다룬다.

## 시작 파일의 이름과 읽히는 시점

Bash는 실행 방식에 따라 다른 파일을 읽는다. [GNU Bash의 시작 파일 설명](https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html)에서 로그인 셸은 `/etc/profile` 이후 사용자 홈의 `.bash_profile`, `.bash_login`, `.profile` 중 처음 발견한 읽을 수 있는 파일을 사용한다. 일반적인 대화형 비로그인 셸은 `.bashrc`를 읽는다. `.bash_profile` 안에서 `.bashrc`를 직접 불러오는 구성도 가능하다.

파일 이름만 모아서는 어느 경로로 적용되는지 알기 어렵다. 계정이 쓰는 셸과 로그인 방식, 파일 안에서 다른 파일을 불러오는 부분을 함께 살핀다. 이 글의 실습에서는 소유자와 모드 값을 수집했다고 가정하고 그 값만 비교한다. 시작 파일은 실행하지 않는다.

가이드의 예시 목록에는 `.profile`, `.kshrc`, `.cshrc`, `.bashrc`, `.bash_profile`, `.login`, `.exrc`, `.netrc` 등이 있다. 모두 Bash 시작 파일이라는 뜻은 아니다. `.exrc`와 `.netrc`처럼 별도 프로그램이 읽는 사용자 설정도 목록에 포함되어 있다. 시스템 공통 파일과 홈 안의 파일을 구분해 수집 범위를 적는다.

## 소유자 조건과 쓰기 조건은 각각 비교한다

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 PDF 51쪽에서 U-24의 중요도는 ‘상’이다. 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다.

양호 기준은 홈 디렉터리 환경변수 파일의 소유자가 root 또는 해당 계정이고, root와 소유자 외에는 쓰기 권한이 없는 경우다. 소유자가 다른 계정이거나 다른 사용자에게 쓰기가 허용되면 취약으로 구분한다. 일반 모드에서는 그룹 쓰기 `020`과 기타 사용자 쓰기 `002`를 따로 읽을 수 있다.

| 가정한 홈 계정 UID | 파일 소유 UID | 모드 | 비교할 차이 |
| --- | --- | --- | --- |
| 1001 | 0 | `0644` | 소유자는 root이며 그룹·기타 쓰기 없음 |
| 1001 | 1001 | `0660` | 소유자는 같지만 그룹 쓰기 존재 |
| 1001 | 1002 | `0600` | 쓰기 비트와 별개로 소유자 불일치 |

그룹에 실제로 누가 속하는지와 추가 ACL이 누구에게 쓰기를 주는지도 조사 대상이다. 모드 숫자만으로 권한의 모든 경로를 설명하지 않는다. [Linux acl(5)](https://man7.org/linux/man-pages/man5/acl.5.html)는 확장 ACL이 있을 때 그룹 모드 비트가 ACL 마스크와 대응하는 점을 설명한다. 아래 비교기는 ACL을 수집하지 않았거나 확장 ACL이 있는 행을 먼저 ‘추가 조사’로 분리한다.

[[diagram]]

원문 조치 사례의 `chmod o-w`는 기타 사용자 쓰기만 제거한다. 그룹 쓰기까지 제거하는 명령으로 읽으면 안 된다. 예를 들어 모드 정수 `0660`에서 `002`를 지워도 `0660`이 그대로 남는다. 이 글에서는 명령을 운영 파일에 실행하지 않고 `mode & 0o022`로 두 쓰기 비트의 존재를 비교한다. 변경할 때는 해당 파일의 용도와 ACL, 실제 그룹 구성까지 대조해야 한다.

## 가상 수집 자료에서 두 조건을 분리해 보기

Python 3.9 이상과 표준 라이브러리만 필요하다. Windows Python 3.12.1에서 실행했다. UID와 모드는 JSON에 직접 적은 가상 값이며 Windows 파일시스템에서 Linux 소유자·모드를 수집한 결과가 아니다. 실제 홈 파일·계정·셸 설정을 읽거나 바꾸지 않는다.

ZIP을 빈 폴더에 풀고 `u24_env_permissions.py`와 `u24_env_permissions.json`이 함께 있는 폴더에서 실행한다. JSON에는 여덟 행이 이미 들어 있어 입력을 다시 만들 필요가 없다. 관리자 권한과 별도 서버·패키지는 필요하지 않다.

[[download]]

```bash
python -I -B -X utf8 u24_env_permissions.py u24_env_permissions.json
```

Linux·WSL에서는 `python3`를 사용할 수 있다. 명령 직후 PowerShell의 `$LASTEXITCODE`, Bash의 `echo $?`로 종료 코드를 읽는다. 파일명이나 형식이 잘못됐으면 표준 오류를 살피며 기존 자료를 지우는 절차는 필요하지 않다.

가상 자료의 `homeUid`는 점검할 홈 계정의 UID, `ownerUid`는 수집했다고 가정한 파일 소유 UID다. `acl: "none"`은 추가 ACL이 없다고 조사된 조건이고 `"unknown"`은 미수집이다. 링크는 `kind: "link"`로 구별한다. 아래 전체 코드는 이 입력을 기준에 들어가는 일반 파일과 추가 자료가 필요한 행으로 나눈다.

```python
import argparse
import json
from pathlib import Path
import re
import sys


def validate(row):
    fields = {"case", "homeUid", "ownerUid", "kind", "mode", "acl"}
    if not isinstance(row, dict) or set(row) != fields:
        raise ValueError("필드가 맞지 않는다")
    if not isinstance(row["case"], str) or not row["case"].strip():
        raise ValueError("사례 이름이 필요하다")
    for key in ("homeUid", "ownerUid"):
        if type(row[key]) is not int or row[key] < 0:
            raise ValueError("UID는 0 이상의 정수여야 한다")
    if row["kind"] not in ("file", "link"):
        raise ValueError("종류는 file 또는 link여야 한다")
    if not isinstance(row["mode"], str) or not re.fullmatch(r"[0-7]{4}", row["mode"]):
        raise ValueError("모드는 네 자리 8진수 문자열이어야 한다")
    if row["acl"] not in ("none", "extended", "unknown"):
        raise ValueError("ACL 수집 상태가 맞지 않는다")


def compare(row):
    mode = int(row["mode"], 8)
    if row["kind"] != "file" or row["acl"] != "none" or mode & 0o7000:
        return "추가 조사", "링크·ACL·특수 비트 자료를 별도로 조사"
    reasons = []
    if row["ownerUid"] not in (0, row["homeUid"]):
        reasons.append("소유자 불일치")
    extra_write = mode & 0o022
    if extra_write:
        reasons.append(f"그룹·기타 쓰기 {extra_write:03o}")
    if reasons:
        return "기준 이탈", ", ".join(reasons)
    return "기본 조건 일치", "소유자와 일반 쓰기 비트가 조건에 들어감"


def main():
    parser = argparse.ArgumentParser(description="가상 환경변수 파일의 수집 자료를 비교한다")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        rows = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(rows, list) or not rows:
            raise ValueError("비어 있지 않은 배열이 필요하다")
        seen = set()
        for row in rows:
            validate(row)
            if row["case"] in seen:
                raise ValueError("사례 이름이 중복됐다")
            seen.add(row["case"])
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    counts = {"기본 조건 일치": 0, "기준 이탈": 0, "추가 조사": 0}
    for row in rows:
        state, detail = compare(row)
        counts[state] += 1
        print(f"{row['case']}: {state}; {detail}")
    print("가상 자료 " + str(len(rows)) + "건: " + ", ".join(f"{key} {value}건" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`main()`은 목록의 모든 행을 먼저 검사한다. UID에는 음수·문자열·불리언을 허용하지 않고 `mode`에는 네 자리 8진수 문자열만 받는다. 중복 사례나 잘못된 행이 있으면 결과 일부를 출력하지 않고 종료 2로 끝난다. 파일 읽기 실패도 2다.

`group-write`의 `"0660"`을 따라가 보자. `compare()`의 첫 분기는 일반 파일이고 ACL이 없으며 특수 비트도 없으므로 지나간다. 소유 UID 1001은 `homeUid`와 같아 소유자 차이는 추가되지 않는다. 이어서 `0o660 & 0o022`가 `0o020`을 남겨 `reasons`에 그룹·기타 쓰기 `020`이 들어간다. `root-profile`의 `0644`에서는 이 계산이 0이고 소유 UID도 0이므로 기본 조건에 들어간다.

[[run:1]]

‘기준 이탈’ 네 행 가운데 `two-differences`에는 소유자 불일치와 쓰기 `022`가 함께 나온다. 첫 차이를 찾았다고 나머지 비교를 멈추지 않기 때문이다. `foreign-owner`는 모드가 `0644`여도 소유 UID가 1002라서 소유자 조건에서 벗어난다.

링크와 ACL 미수집의 두 행은 앞의 분기에서 ‘추가 조사’로 끝난다. 링크 대상의 실제 경로·종류·소유자와 접근 경로를 수집하거나 ACL의 유효 권한을 조사하기 전까지 기본 조건 일치로 합치지 않는다. 소유자가 일치하는 두 행 역시 가상 입력의 제한된 비교 결과다. 종료 0은 여덟 행의 처리가 끝났다는 뜻이며 실제 홈 전체의 양호 판정은 아니다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [GNU Bash: Bash Startup Files](https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html)
- [GNU chmod(1): 기호 모드와 변경 대상](https://man7.org/linux/man-pages/man1/chmod.1.html)
- [Linux acl(5): 접근 제어 목록과 파일 모드](https://man7.org/linux/man-pages/man5/acl.5.html)
