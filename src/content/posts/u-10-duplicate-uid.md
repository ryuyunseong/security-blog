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

아래 가상 계정 자료에서 `deploy`와 `backup`은 이름과 기본 그룹이 다른데도 UID 1500을 공유해요. 파일의 사용자 소유권으로는 두 이름을 구분할 수 없어요.

U-10 스크립트로 중복 UID를 찾아보고 UID를 나누기 전에 조사할 서비스와 파일 소유권까지 살펴볼게요.

## 이름이 아니라 숫자 UID를 비교한다

| 구분 | 기준 |
| --- | --- |
| 항목 | U-10: 동일한 UID 금지 |
| 중요도 | 중 |
| 대상 | SOLARIS, LINUX, AIX, HP-UX 등 |
| 양호 | 동일한 UID로 설정된 사용자 계정이 없는 경우 |
| 취약 | 동일한 UID로 설정된 사용자 계정이 있는 경우 |

점검할 값은 `/etc/passwd`의 세 번째 필드인 UID(User ID)예요. 첫 번째 필드는 계정 이름, 네 번째는 기본 GID이고요. 여러 계정이 같은 GID를 공유하는 경우는 UID 중복으로 집계하지 않아요.

운영상 필요해서 같은 UID를 부여했다는 설명만으로 양호가 되지는 않아요. 다만 UID를 분리하면 서비스 실행이나 파일 접근에 영향을 줄 수 있으니 사용 중인 자원과 조치 영향을 먼저 살펴야 해요.

Linux의 파일 접근 검사는 프로세스의 파일시스템 UID 등 숫자 자격을 사용해요. 그래서 같은 UID의 두 로그인 이름은 같은 파일 소유자 권한으로 처리될 수 있고 UID만 남긴 기록에서는 어느 이름으로 작업했는지 구분하기도 어려워요. 그렇다고 그룹·ACL·보안 모듈을 포함한 모든 권한이나 모든 로그가 같아진다는 뜻은 아니에요.

## 읽기 전용 명령으로 필요한 필드만 확인한다

다음 Linux 명령으로 로컬 계정 파일의 이름과 UID, 계정 조회 설정을 살펴볼 수 있어요. 파일을 읽을 권한이 있다면 관리자 권한은 필요하지 않고 비밀번호 필드와 사용자 설명도 출력하지 않아요.

```text
# 로컬 계정 이름과 UID 확인
awk -F: '{print "계정=" $1, "UID=" $3}' /etc/passwd

# 계정 조회에 사용하는 이름 서비스 설정 확인
grep -E '^[[:space:]]*passwd[[:space:]]*:' /etc/nsswitch.conf
```
이 명령은 내용을 살펴보는 용도예요. 입력 형식 검증과 UID별 중복 집계는 아래 스크립트에서 처리해요.

LDAP·AD 같은 중앙 디렉터리를 사용하는 서버라면 로컬 파일 밖의 계정도 살펴야 해요. GNU `getent`는 NSS(Name Service Switch) 설정에 따라 계정을 조회해요. 아래 Bash 예제의 `deploy`는 실제 조사할 계정명으로 바꿔 주세요.

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
`pipefail`은 조회 실패가 뒤의 `awk` 성공에 가려지는 것을 막아 줘요. 출력이 비었을 때는 표준 오류와 종료 상태도 함께 읽어야 조회 실패와 계정 부재를 구분할 수 있어요.

`getent passwd 1500`으로 이름 하나를 얻었다고 해서 같은 UID의 다른 이름이 없다고 볼 수는 없어요. 숫자 키 조회는 해당 UID에 대한 항목을 얻는 동작이므로 중앙 계정 명단을 이름별로 조회해 UID 배정 내역과 대조해야 해요. 로컬 계정과 중앙 계정이 서로 가려지는 조회 설정도 함께 살펴보고요.

중앙 계정 서비스는 전체 목록 열거를 지원하지 않거나 일부 계정만 반환할 수 있어요. 명령의 성공 여부에 더해 조회 범위가 충분한지도 살펴야 해요.

[[diagram]]

## 스크립트는 중복과 실행 오류를 나눠 보고한다

다음 코드를 `check_u10.py`로 저장해요. Linux에서 Python 3.9 이상과 표준 라이브러리를 사용하는 읽기 전용 예제예요. 기본 입력은 `/etc/passwd`이고 `--passwd`로 임시 파일을 지정할 수 있어요. 계정·설정·권한은 변경하지 않아요.

입력은 UTF-8 일반 파일만 지원하고 파일 크기는 4 MiB로 제한해요. 빈 자료, 잘못된 필드 수, 중복 계정 이름, NIS 지시 행처럼 지원하지 않는 형식은 오류로 중단해요. UID와 GID는 0~4294967294 범위의 ASCII 십진수만 받아요. 이는 작은 예제의 입력 규칙이며 모든 Unix에 공통으로 적용되는 계정 규칙은 아니에요.

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
`number()`는 숫자를 검증한 뒤 정수로 변환하므로 `1500`과 `01500`은 같은 UID로 묶여요. `inspect()`는 입력을 검증하고 UID별 계정 목록을 만들어요. 읽기나 형식 오류가 생겼을 때는 부분 결과를 정상 결과처럼 출력하지 않아요.

출력에는 확인한 계정 수와 중복 UID·계정 이름만 담아요. 셸이 `nologin`이거나 비밀번호가 잠긴 계정도 비교에서 제외하지 않아요. 로그인 제한으로는 숫자 UID의 중복이 없어지지 않기 때문이에요.

다음과 같이 실행한 뒤 종료 코드를 살펴보세요. 실제 운영 계정 이름도 내부 정보이므로 결과를 외부 게시물에 그대로 복사하지 않아야 해요.

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

ZIP의 `check_u10.py` 파일을 준비한 뒤 Linux의 Bash와 Python 3로 실행해요. 아래 묶음을 실행하면 `mktemp -d`로 배정한 `$work` 아래에 passwd가 생성돼요. 기록의 `$LAB` 경로를 직접 준비할 필요는 없어요.

다음 Bash 예제는 가상 계정 파일만 만들어요. `check_u10.py`를 저장한 디렉터리에서 명령 전체를 실행하면 돼요. `deploy`와 `backup`의 UID는 1500으로 같게 두고 기본 GID는 다르게 설정했어요.

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
위 자료로 실행해서 얻은 결과예요.

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

코드는 각 행을 검증한 뒤 `by_uid.setdefault(uid, []).append(name)`로 UID별 이름을 모아요. 그 목록 길이가 2 이상인 항목만 `duplicates`에 남겨요. GID가 1500과 1600으로 달라도 이 묶음에는 영향을 주지 않고 nologin인 backup도 제외하지 않아요.

출력의 ‘확인한 계정 수’ 3은 root를 포함해 읽은 전체 이름 수예요. 중복 묶음은 UID 1500 한 개이고 그 묶음의 계정은 두 개예요. Bash의 `exit "$result"`는 수집기의 발견 코드 `1`을 그대로 반환하고 trap은 준비 파일을 지워요. 입력 오류로 코드 `2`가 나왔다면 중복 개수가 0인 결과로 바꿔 기록하면 안 돼요.

이 비교는 입력 파일의 숫자 UID를 묶는 작업이에요. `backup`에 별도 UID 1600을 배정해 중복을 없애더라도 수집기가 그 계정이 사용하던 파일의 소유권과 서비스 설정까지 바꾸지는 않아요. UID를 분리한 뒤의 실제 접근 영향은 별도의 변경 작업에서 시험해야 해요.

## 로컬 중복이 없어도 점검 범위를 확인한다

이 스크립트가 찾는 중복은 입력한 파일 안으로 한정돼요. 중앙 계정과 로컬 계정의 UID 충돌까지 모두 조사하려면 중앙 디렉터리의 배정 정책과 실제 조회 결과가 필요해요. 결과에는 대상 호스트와 계정 자료의 범위를 기록하고 수집 중 계정 변경이 있었다면 변경 완료 후 다시 살펴봐야 해요.

컨테이너나 사용자 네임스페이스에서는 내부 UID와 호스트 UID의 대응 관계가 다를 수 있어요. 서로 다른 컨테이너에 UID 1000이 있다는 이유만으로 하나의 계정 파일에서 발생한 중복처럼 합산하면 안 돼요. 계정 관리 범위를 정해 중복을 찾고 호스트 자원 접근은 UID 매핑까지 따로 검토해요.

UID 0은 우선 살펴야 해요. 두 계정이 UID 0을 공유하면 이 코드도 찾지만 `root`가 아닌 계정 하나만 UID 0을 사용하는 입력에서는 중복이 없다고 나와요. 그래서 U-05의 root 이외 UID 0 제한은 별도로 점검해야 해요.

## 기존 파일의 소유자를 정한 뒤 UID를 바꾼다

중복이 발견되면 각 계정의 담당자·사용 목적·실행 서비스와 기존 파일을 조사해요. 다음은 GNU `find`로 숫자 UID 1500이 소유한 파일과 디렉터리를 찾는 읽기 전용 예제예요. `/srv/app`은 승인된 조사 경로로 바꾸고 표준 오류와 종료 상태도 함께 읽어야 해요.

```bash
find /srv/app -xdev -uid 1500 -ls
```
`-xdev`는 다른 파일시스템 내부로 내려가지 않으니 별도 마운트는 따로 조사해야 해요. 접근하지 못한 경로는 누락 범위로 기록해요. 파일의 소유 UID가 1500이라는 사실만으로 그 자료가 원래 `deploy`와 `backup` 중 어느 계정의 것이었는지 복원할 수는 없어요. 화면에 표시된 계정 이름도 두 계정을 구분하는 근거가 되지 않아요.

기존 UID의 파일을 전부 새 계정 소유로 넘기는 일괄 조치는 피해야 해요. 업무 자료·설정·담당자 확인으로 귀속을 정하고 홈 디렉터리 밖의 파일, ACL, 예약 작업, 서비스 설정을 포함한 변경 목록과 복구 계획을 준비해요.

Linux의 `usermod -u 새UID 계정명`은 승인된 변경 시간에 사용하는 조치 명령이에요. 새 UID가 로컬·중앙 계정과 충돌하지 않는지 먼저 조사해야 해요. 중복을 허용하는 `-o` 옵션은 해결책이 아니에요. AIX 등 다른 Unix에서는 해당 운영체제의 계정 관리 명령과 절차를 따라요.

shadow-utils의 `usermod`는 조건에 따라 홈 디렉터리와 메일함의 소유 UID를 바꿔요. 다만 홈 밖의 파일과 예약 작업까지 모두 정리하지는 않으므로 홈 디렉터리를 공유하는 구성이라면 자동 변경 범위도 먼저 검토해야 해요.

UID를 바꾸기 전에는 해당 UID로 실행 중인 프로세스와 세션을 정리할 절차가 필요해요. 중복 UID를 공유하는 다른 계정의 서비스까지 영향을 받을 수 있으니 중지·재시작 범위를 담당자와 확인해야 해요. 점검 스크립트에는 이런 변경 작업을 넣지 않아요.

변경 후에는 새 UID가 조회되고 중복이 해소됐는지 검사해요. 파일은 기존 UID에 남길 자료와 새 UID로 옮길 자료를 대조해 누락을 찾아요. 서비스 계정으로 필요한 자료에 접근할 수 있는지, 다른 계정의 자료에 과도한 권한이 남지는 않았는지도 시험해야 해요.
