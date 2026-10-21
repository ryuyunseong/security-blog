---
title: "U-10: 동일한 UID 금지"
description: "중복 UID를 찾는 Python 예제와 UID 분리 전에 조사할 파일 소유권·서비스 영향을 다룹니다."
date: "2026-10-15T20:23:44+09:00"
updated: "2026-10-22"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-10", "UID"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 10
---

아래 가상 계정 자료의 `deploy`와 `backup`은 이름과 기본 그룹이 다르지만 UID 1500을 공유한다. 파일의 사용자 소유권으로는 두 이름을 구분할 수 없다.

U-10 스크립트로 중복 UID를 찾고, UID를 나누기 전에 조사할 서비스와 파일 소유권을 살펴본다.

## 이름이 아니라 숫자 UID를 비교한다

| 구분 | 기준 |
| --- | --- |
| 항목 | U-10: 동일한 UID 금지 |
| 중요도 | 중 |
| 대상 | SOLARIS, LINUX, AIX, HP-UX 등 |
| 양호 | 동일한 UID로 설정된 사용자 계정이 없는 경우 |
| 취약 | 동일한 UID로 설정된 사용자 계정이 있는 경우 |

점검에서는 `/etc/passwd`의 세 번째 필드인 UID(User ID)를 비교한다. 첫 번째 필드는 계정 이름, 네 번째는 기본 GID다. 여러 계정이 같은 GID를 공유하는 경우는 UID 중복으로 집계하지 않는다.

운영상 필요해 같은 UID를 부여했다는 설명만으로 양호가 되지는 않는다. 다만 UID를 분리하면 서비스 실행이나 파일 접근에 영향을 줄 수 있으므로, 사용 중인 자원과 조치 영향을 먼저 확인한다.

Linux의 파일 접근 검사는 프로세스의 파일시스템 UID 등 숫자 자격을 사용한다. 같은 UID의 두 로그인 이름은 같은 파일 소유자 권한으로 처리될 수 있다. UID만 남긴 기록에서는 어느 이름으로 작업했는지 구분하기도 어렵다. 다만 그룹·ACL·보안 모듈을 포함한 모든 권한이나 모든 로그가 같아진다는 뜻은 아니다.

## 읽기 전용 명령으로 필요한 필드만 확인한다

다음 Linux 명령은 로컬 계정 파일의 이름과 UID, 계정 조회 설정을 보여 준다. 파일을 읽을 권한이 있다면 관리자 권한 없이 확인할 수 있다. 비밀번호 필드와 사용자 설명은 출력하지 않는다.

```text
# 로컬 계정 이름과 UID 확인
awk -F: '{print "계정=" $1, "UID=" $3}' /etc/passwd

# 계정 조회에 사용하는 이름 서비스 설정 확인
grep -E '^[[:space:]]*passwd[[:space:]]*:' /etc/nsswitch.conf
```
이 명령은 내용을 살펴보는 용도다. 입력 형식 검증과 UID별 중복 집계는 아래 스크립트가 담당한다.

LDAP·AD 같은 중앙 디렉터리를 사용하는 서버라면 로컬 파일 밖의 계정도 확인한다. GNU `getent`는 NSS(Name Service Switch) 설정에 따라 계정을 조회한다. 아래 Bash 예제의 `deploy`는 실제 조사할 계정명으로 바꾼다.

```bash
(
    set -o pipefail

    if getent passwd deploy |
        awk -F: '{print "계정=" $1, "UID=" $3}'
    then
        result=0
    else
        result=$?
    fi

    printf '조회 종료 코드: %s\n' "$result"
    exit "$result"
)
```
`pipefail`은 조회 실패가 뒤의 `awk` 성공에 가려지는 것을 막는다. 출력이 비었다면 표준 오류와 종료 상태도 확인한다. 조회 실패와 계정 부재를 같은 결과로 처리하지 않는다.

`getent passwd 1500`으로 이름 하나를 얻었다고 해서 같은 UID의 다른 이름이 없다는 뜻은 아니다. 숫자 키 조회는 해당 UID에 대한 항목을 얻는 동작이다. 중앙 계정 명단을 이름별로 조회하고 UID 배정 내역과 대조한다. 로컬 계정과 중앙 계정이 서로 가려지는 조회 설정도 함께 확인한다.

중앙 계정 서비스가 전체 목록 열거를 지원하지 않거나 일부 계정만 반환할 수 있다. 명령의 성공 여부와 함께 조회 범위가 충분한지도 살펴야 한다.

[[diagram]]

## 스크립트는 중복과 실행 오류를 나눠 보고한다

다음 코드를 `check_u10.py`로 저장한다. Linux에서 Python 3.9 이상과 표준 라이브러리를 사용하는 읽기 전용 예제다. 기본 입력은 `/etc/passwd`이며, `--passwd`로 임시 파일을 지정할 수 있다. 계정·설정·권한을 변경하지 않는다.

입력은 UTF-8 일반 파일만 지원하며 파일 크기는 4 MiB로 제한한다. 빈 자료, 잘못된 필드 수, 중복 계정 이름, NIS 지시 행처럼 지원하지 않는 형식은 오류로 중단한다. UID와 GID는 0~4294967294 범위의 ASCII 십진수만 받는다. 이 제한은 예제의 입력 규칙이며 모든 Unix에 공통으로 적용되는 계정 규칙은 아니다.

[[download]]

```python
#!/usr/bin/env python3
"""passwd 자료에서 같은 숫자 UID를 사용하는 계정을 찾는다."""
import argparse
import json
import os
import re
import stat
import sys

LIMIT = 4 * 1024 * 1024


def number(value):
    if not re.fullmatch(r"[0-9]{1,10}", value):
        raise ValueError("UID 또는 GID 형식 오류")
    result = int(value)
    if result > 4294967294:
        raise ValueError("이 예제의 UID 또는 GID 범위 초과")
    return result


def inspect(path):
    # FIFO 등에서 대기하지 않고 일반 파일만 읽는다.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("일반 파일만 입력할 수 있음")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("입력 파일은 4 MiB 이하여야 함")

    names, by_uid = set(), {}
    for line_no, line in enumerate(data.decode("utf-8").split("\n"), 1):
        line = line.removesuffix("\r")
        if not line:
            continue
        if any(ord(c) < 32 or ord(c) == 127 for c in line):
            raise ValueError(f"{line_no}행: 제어 문자 포함")
        fields = line.split(":")
        if len(fields) != 7:
            raise ValueError(f"{line_no}행: 필드 수 오류")
        name = fields[0]
        if (
            not name
            or name.startswith(("+", "-", "#"))
            or any(c.isspace() or c == "," for c in name)
        ):
            raise ValueError(f"{line_no}행: 지원하지 않는 계정 이름")
        if name in names:
            raise ValueError(f"{line_no}행: 계정 이름 중복")
        names.add(name)
        uid = number(fields[2])
        number(fields[3])
        by_uid.setdefault(uid, []).append(name)

    if not names:
        raise ValueError("계정 자료가 비어 있음")
    duplicates = [
        {"UID": uid, "계정": sorted(users)}
        for uid, users in sorted(by_uid.items())
        if len(users) > 1
    ]
    return {"확인한 계정 수": len(names), "중복 UID": duplicates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passwd", default="/etc/passwd", help="읽을 passwd 파일")
    args = parser.parse_args()
    try:
        report = inspect(args.passwd)
    except (OSError, UnicodeError, ValueError) as error:
        print("실행 오류: " + str(error), file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    found = bool(report["중복 UID"])
    print(
        "중복 발견: 해당 계정과 영향 범위 확인 필요"
        if found else "입력 범위에서 중복 UID 미발견"
    )
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
```
`number()`는 숫자를 검증한 뒤 정수로 변환한다. 따라서 `1500`과 `01500`은 같은 UID로 묶인다. `inspect()`는 입력을 검증하고 UID별 계정 목록을 만든다. 읽기나 형식 오류가 있으면 부분 결과를 정상 결과처럼 출력하지 않는다.

출력에는 확인한 계정 수와 중복 UID·계정 이름만 담는다. 셸이 `nologin`이거나 비밀번호가 잠긴 계정도 비교에서 제외하지 않는다. 로그인 제한은 숫자 UID의 중복을 없애는 조치가 아니기 때문이다.

다음과 같이 실행하고 종료 코드를 확인한다. 실제 운영 계정 이름도 내부 정보이므로 결과를 외부 게시물에 그대로 복사하지 않는다.

```text
if python3 check_u10.py
then
    result=0
else
    result=$?
fi
printf '종료 코드: %s\n' "$result"
```
| 종료 코드 | 의미 |
| --- | --- |
| 0 | 입력 범위에서 중복 UID를 찾지 못함. 서버 전체 양호 판정은 아님 |
| 1 | 중복 UID가 있음. 해당 계정과 영향 범위 확인 필요 |
| 2 | 읽기·형식·실행 인자 오류로 점검을 완료하지 못함 |

## 임시 계정 자료로 결과를 확인한다

ZIP의 `check_u10.py` 파일을 사용한다. Linux의 Bash와 Python 3를 사용한다. 아래 묶음을 실행하면 `mktemp -d`로 배정한 `$work` 아래에 passwd가 생성되므로, 기록의 `$LAB` 경로를 직접 준비할 필요는 없다.

다음 Bash 예제는 가상 계정 파일만 만든다. `check_u10.py`를 저장한 디렉터리에서 명령 전체를 실행한다. `deploy`와 `backup`의 UID는 1500으로 같고 기본 GID는 다르게 설정했다.

```bash
(
    work=$(mktemp -d) || exit 2

    # 이 예제에서 만든 가상 파일만 정리한다.
    cleanup() {
        rm -f -- "$work/passwd"
        rmdir -- "$work"
    }
    trap cleanup EXIT

    cat > "$work/passwd" <<'EOF'
root:x:0:0::/root:/bin/sh
deploy:x:1500:1500::/srv/deploy:/bin/sh
backup:x:1500:1600::/srv/backup:/usr/sbin/nologin
EOF

    # 중복 발견에 따른 종료 코드 1도 기록한다.
    if python3 check_u10.py --passwd "$work/passwd"
    then
        result=0
    else
        result=$?
    fi

    printf '종료 코드: %s\n' "$result"
    exit "$result"
)
```
위 자료로 실행해 확인한 결과는 다음과 같다.

```text
{
  "확인한 계정 수": 3,
  "중복 UID": [
    {
      "UID": 1500,
      "계정": [
        "backup",
        "deploy"
      ]
    }
  ]
}
중복 발견: 해당 계정과 영향 범위 확인 필요
종료 코드: 1
```

[[run:1:fold]]

코드는 각 행을 검증한 뒤 `by_uid.setdefault(uid, []).append(name)`로 UID별 이름을 모은다. 그 목록 길이가 2 이상인 항목만 `duplicates`에 남긴다. GID가 1500과 1600으로 달라도 이 묶음에는 영향을 주지 않으며 nologin인 backup도 제외하지 않는다.

출력의 ‘확인한 계정 수’ 3은 root를 포함해 읽은 전체 이름 수다. 중복 묶음은 UID 1500 한 개, 그 묶음의 계정은 두 개다. Bash의 `exit "$result"`가 수집기의 발견 코드 `1`을 그대로 반환하며 trap이 준비 파일을 지운다. 입력 오류로 코드 `2`가 나왔다면 중복 개수가 0인 결과로 바꿔 기록하지 않는다.

두 이름이 UID 1500에 묶였고 종료 코드 `1`이 나왔다. `backup`의 셸이 `nologin`이어도 UID 비교 결과는 달라지지 않는다.

가상 자료에서 `backup`의 UID를 1600으로 바꾸자 중복 목록이 비고 종료 코드 0이 나왔다. 입력 숫자를 바꿔 비교한 결과이며, 실제 파일 소유권과 서비스 권한을 변경해 시험한 것은 아니다.

## 로컬 중복이 없어도 점검 범위를 확인한다

이 스크립트는 입력한 파일 안의 중복만 찾는다. 중앙 계정과 로컬 계정의 UID 충돌까지 모두 확인하려면 중앙 디렉터리의 배정 정책과 실제 조회 결과가 필요하다. 결과에는 대상 호스트와 계정 자료의 범위를 기록하고, 수집 중 계정 변경이 있었다면 변경 완료 후 다시 확인한다.

컨테이너나 사용자 네임스페이스에서는 내부 UID와 호스트 UID의 대응 관계가 다를 수 있다. 서로 다른 컨테이너에 UID 1000이 있다는 이유만으로 하나의 계정 파일에서 발생한 중복처럼 합산하지 않는다. 계정 관리 범위를 정해 중복을 확인하고, 호스트 자원 접근은 UID 매핑까지 따로 검토한다.

UID 0은 우선 확인한다. 두 계정이 UID 0을 공유하면 이 코드도 찾지만, `root`가 아닌 계정 하나만 UID 0을 사용하는 입력에서는 중복이 없다고 나온다. U-05의 root 이외 UID 0 제한은 별도로 점검해야 한다.

## 기존 파일의 소유자를 정한 뒤 UID를 바꾼다

중복이 확인되면 각 계정의 담당자·사용 목적·실행 서비스를 확인하고 기존 파일을 조사한다. 다음은 GNU `find`로 숫자 UID 1500이 소유한 파일과 디렉터리를 찾는 읽기 전용 예제다. `/srv/app`은 승인된 조사 경로로 바꾸고 표준 오류와 종료 상태도 확인한다.

```bash
find /srv/app -xdev -uid 1500 -ls
```
`-xdev`는 다른 파일시스템 내부로 내려가지 않으므로 별도 마운트는 따로 조사한다. 접근하지 못한 경로는 누락 범위로 기록한다. 파일의 소유 UID가 1500이라는 사실만으로 그 자료가 원래 `deploy`와 `backup` 중 어느 계정의 것인지 복원할 수는 없다. 화면에 표시된 계정 이름도 그 구분의 근거가 되지 않는다.

기존 UID의 파일을 전부 새 계정 소유로 넘기는 일괄 조치는 피한다. 업무 자료·설정·담당자 확인으로 귀속을 정하고, 홈 디렉터리 밖의 파일, ACL, 예약 작업, 서비스 설정을 포함한 변경 목록과 복구 계획을 준비한다.

Linux의 `usermod -u 새UID 계정명`은 승인된 변경 시간에 사용하는 조치 명령이다. 새 UID가 로컬·중앙 계정과 충돌하지 않는지 먼저 확인한다. 중복을 허용하는 `-o` 옵션은 해결책이 아니다. AIX 등 다른 Unix는 해당 운영체제의 계정 관리 명령과 절차를 따른다.

shadow-utils의 `usermod`는 조건에 따라 홈 디렉터리와 메일함의 소유 UID를 바꾸지만, 홈 밖의 파일과 예약 작업까지 모두 정리하지는 않는다. 홈 디렉터리를 공유하는 구성이라면 자동 변경 범위도 먼저 검토한다.

UID를 변경하기 전에는 해당 UID로 실행 중인 프로세스와 세션을 정리할 절차가 필요하다. 중복 UID를 공유하는 다른 계정의 서비스까지 영향을 받을 수 있으므로 중지·재시작 범위를 담당자와 확인한다. 점검 스크립트에는 이런 변경 작업을 넣지 않는다.

변경 후에는 새 UID가 조회되고 중복이 해소됐는지 검사한다. 파일은 기존 UID에 남길 자료와 새 UID로 옮길 자료를 대조해 누락을 찾는다. 서비스 계정으로 필요한 자료에 접근할 수 있는지, 다른 계정의 자료에 과도한 권한이 남지 않았는지도 시험한다.
