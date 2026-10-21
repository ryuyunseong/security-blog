---
title: "U-08: 관리자 그룹에 최소한의 계정 포함"
description: "기본 GID와 보조 그룹을 함께 조회해 관리자 그룹 구성원의 필요성을 검토합니다."
date: "2026-10-13T21:07:40+09:00"
updated: "2026-10-21T21:00:44+09:00"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-08", "그룹관리"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 8
---

`/etc/group`에 `root:x:0:`만 적혀 있어도 root 그룹 구성원이 없다고 볼 수는 없다. 기본 GID가 0인 계정은 이 그룹에 속하므로 `/etc/passwd`도 함께 읽어야 한다.

U-08의 로컬 점검 예제에서는 두 파일에서 찾은 기본·보조 구성원을 합쳐 승인 목록과 대조한다.

## 관리자 그룹에 계정을 유지할 수 있는 조건

| 구분 | 기준 |
| --- | --- |
| 항목 | U-08: 관리자 그룹에 최소한의 계정 포함 |
| 중요도 | 중 |
| 대상 | SOLARIS, LINUX, AIX, HP-UX 등 |
| 양호 | 관리자 그룹에 불필요한 계정이 등록되어 있지 않은 경우 |
| 취약 | 관리자 그룹에 불필요한 계정이 등록된 경우 |

“최소한”은 모든 서버에서 root 한 계정만 허용한다는 뜻이 아니다. 관리 업무에 승인된 계정인지, 담당자가 여전히 그 업무를 수행하는지, 부여된 권한이 필요한지를 확인한다. 퇴직자나 종료된 외주 작업 계정이 남아 있다면 그룹 명단과 함께 실제 접근 권한도 회수해야 한다.

root 그룹에 속한 계정은 해당 그룹에 허용된 파일·디렉터리 접근 권한을 얻을 수 있다. 다만 GID 0과 UID 0은 다르다. 일반 UID를 가진 계정이 root 그룹에 속했다고 해서 root의 모든 권한을 얻는 것은 아니다. 실제 영향은 그룹 권한이나 ACL로 접근할 수 있는 자원, 별도로 부여된 권한에 따라 달라진다.

## 기본 그룹과 보조 그룹을 함께 확인한다

| 확인 위치 | 의미 |
| --- | --- |
| `/etc/passwd`의 네 번째 필드 | 계정의 기본 GID |
| `/etc/group`의 세 번째 필드 | 그룹의 GID |
| `/etc/group`의 네 번째 필드 | 쉼표로 구분된 명시적 구성원 목록 |

아래는 설명용 가상 자료다. 먼저 계정 파일에 두 계정이 있다고 가정한다.

```text
root:x:0:0::/root:/bin/sh
deploy:x:1001:0::/srv/deploy:/bin/sh
```
그룹 파일의 root 항목은 다음과 같다.

```text
root:x:0:
```
`deploy`는 그룹 파일의 마지막 필드에 없지만 기본 GID가 0이므로 root 그룹 구성원으로 확인해야 한다. 마지막 필드의 이름만 조사하면 이 계정을 놓친다.

그룹 이름과 숫자 GID도 함께 본다. 서로 다른 그룹 이름이 같은 GID를 사용하면 파일 접근에서는 같은 그룹 식별자로 취급될 수 있다. 대상 그룹과 GID를 공유하는 다른 항목이 있다면 그 구성원 목록까지 조사한다.

[[diagram]]

## 로컬 파일 조회와 NSS 조회를 구분한다

Linux에서는 다음 명령으로 필요한 로컬 필드만 확인할 수 있다. 비밀번호 필드와 사용자 설명은 출력하지 않는다.

```text
# root 그룹의 GID와 명시적 구성원 확인
awk -F: '$1 == "root" {print "그룹=" $1, "GID=" $3, "구성원=" $4}' /etc/group

# 기본 GID가 0인 계정 확인
awk -F: -v gid=0 '$4 == gid {print "계정=" $1, "기본GID=" $4}' /etc/passwd
```
첫 결과에서 root 그룹의 GID를 확인한다. 값이 0이 아니라면 두 번째 명령의 `gid`에 실제 값을 넣는다. 같은 GID를 사용하는 다른 그룹 항목이 있는지도 확인해야 한다.

LDAP·AD 등 중앙 계정 관리가 연결돼 있다면 로컬 파일만으로 구성원을 확정할 수 없다. NSS(Name Service Switch) 설정과 계정별 조회 결과를 함께 살핀다. 아래는 GNU `getent`와 Bash를 사용하는 예제이며, `analyst`는 실제 조사할 계정명으로 바꾼다.

```text
# 계정·그룹 조회에 사용하는 이름 서비스 설정 확인
grep -E '^[[:space:]]*(passwd|group|initgroups)[[:space:]]*:' /etc/nsswitch.conf

(
    set -o pipefail

    getent group root |
        awk -F: '{print "그룹=" $1, "GID=" $3, "구성원=" $4}'
    printf '그룹 조회 종료 코드: %s\n' "$?"

    getent passwd analyst |
        awk -F: '{print "계정=" $1, "UID=" $3, "기본GID=" $4}'
    printf '계정 조회 종료 코드: %s\n' "$?"

    id analyst
    printf '소속 조회 종료 코드: %s\n' "$?"
)
```
`getent`는 NSS 설정에 따라 중앙 서비스나 캐시에서 정보를 조회할 수 있다. 출력이 비었다면 종료 상태와 오류를 먼저 확인한다. SSSD의 전체 목록 열거가 비활성화되거나 그룹 구성원 조회·캐시 설정 때문에 결과가 달라질 수도 있다.

중앙 관리의 승인 명단을 기준으로 계정별 `id` 결과를 대조하고, 누락이나 지연이 있으면 디렉터리 담당자와 확인한다. 계정명을 지정하지 않은 `id`는 현재 프로세스의 소속을 보여 주므로 계정별 조회와 구분한다.

## 승인 목록과 비교하는 읽기 전용 스크립트

아래 코드는 대상 그룹의 기본·보조 구성원을 합쳐 승인 목록과 비교한다. `/etc/passwd`와 `/etc/group`만 읽으며, 파일을 수정하거나 중앙 계정을 조회하지 않는다.

Linux의 Python 3 표준 라이브러리로 실행한다. 코드를 `check_u08.py`로 저장하고, 승인 목록에는 업무 담당자와 유지 필요성을 확인한 계정을 적는다. 현재 구성원을 그대로 복사하면 검토 없이도 일치 결과가 나온다.

```python
#!/usr/bin/env python3
"""로컬 관리자 그룹 구성원을 승인 목록과 읽기 전용으로 비교한다."""
import argparse
import json
import os
import re
import stat
import sys

NAME = re.compile(r"[^\s:,\x00-\x1f\x7f]+\Z")
LIMIT = 4 * 1024 * 1024
MAX_ID = 4294967294


def name(value):
    if not NAME.fullmatch(value) or value.startswith(("+", "-", "#")):
        raise ValueError("지원하지 않는 계정 또는 그룹 이름")
    return value


def number(value):
    # 숫자 길이를 먼저 제한해 과도하게 긴 정수 변환을 피한다.
    if not re.fullmatch(r"[0-9]{1,10}", value):
        raise ValueError("UID 또는 GID 형식 오류")
    parsed = int(value)
    if parsed > MAX_ID:
        raise ValueError("UID 또는 GID 범위 오류")
    return parsed


def rows(path, count):
    # FIFO를 열다가 멈추지 않도록 비차단으로 열고 일반 파일인지 확인한다.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("일반 파일만 읽을 수 있음")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("입력 파일 크기 제한 초과")

    seen, result = set(), []
    for line in data.decode("utf-8").splitlines():
        if not line:
            continue
        parts = line.split(":")
        if len(parts) != count:
            raise ValueError("입력 필드 수 오류")
        key = name(parts[0])
        if key in seen:
            raise ValueError("중복 이름: " + key)
        seen.add(key)
        result.append(parts)
    if not result:
        raise ValueError("빈 계정 또는 그룹 목록")
    return result


def inspect(passwd_path, group_path, target, allowed):
    users = {}
    for p in rows(passwd_path, 7):
        number(p[2])
        users[p[0]] = number(p[3])

    groups = {}
    for g in rows(group_path, 4):
        members = {name(x) for x in g[3].split(",")} if g[3] else set()
        groups[g[0]] = (number(g[2]), members)

    if target not in groups:
        return 1, {
            "그룹": target,
            "결과": "추가 확인",
            "사유": "대상 그룹이 입력에 없음",
        }

    gid = groups[target][0]
    aliases = sorted(k for k, v in groups.items() if v[0] == gid)
    primary = {k for k, v in users.items() if v == gid}
    supplementary = set().union(*(groups[k][1] for k in aliases))
    observed = primary | supplementary
    unknown = supplementary - users.keys()

    report = {
        "그룹": target,
        "GID": gid,
        "같은 GID의 그룹": aliases,
        "기본 그룹 구성원": sorted(primary),
        "명시된 보조 구성원": sorted(supplementary),
        "승인 목록 밖": sorted(observed - allowed),
        "승인됐지만 관찰되지 않음": sorted(allowed - observed),
        "passwd에서 찾지 못한 구성원": sorted(unknown),
    }
    review = bool(observed != allowed or unknown or len(aliases) > 1)
    report["결과"] = "추가 확인" if review else "입력 범위에서 승인 목록과 일치"
    return int(review), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passwd", default="/etc/passwd", help="로컬 계정 파일")
    parser.add_argument("--group-file", default="/etc/group", help="로컬 그룹 파일")
    parser.add_argument("--group", default="root", help="점검할 그룹 이름")
    parser.add_argument(
        "--allow", action="append", required=True, help="승인 계정명, 계정마다 반복"
    )
    args = parser.parse_args()

    try:
        allowed = {name(x) for x in args.allow}
        code, report = inspect(
            args.passwd, args.group_file, name(args.group), allowed
        )
    except (OSError, UnicodeError, ValueError) as error:
        print("실행 오류: " + str(error), file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
```
`rows()`는 일반 파일만 읽고 필드 수와 중복 이름을 검사한다. 파일별 크기는 4 MiB로 제한하며, UTF-8로 해석할 수 없는 파일이나 NIS 호환 행, 지원하지 않는 이름 형식은 오류로 중단한다. UID·GID는 10자리 이하의 십진수이며 0부터 4294967294까지 허용한다.

`inspect()`는 대상 그룹의 GID를 찾은 뒤, 기본 GID가 같은 계정과 동일 GID를 공유하는 모든 그룹의 명시적 구성원을 합친다. 같은 GID의 그룹이 여러 개이거나 그룹에 적힌 이름을 로컬 계정 파일에서 찾지 못하면 추가 확인 대상으로 표시한다.

이때 미확인 구성원이 곧 삭제 대상인 것은 아니다. 중앙 계정인지, 오래된 항목인지, 입력 범위가 잘못됐는지 확인해야 한다. 결과에는 비밀번호·사용자 설명·홈 경로가 포함되지 않지만 계정명도 운영 정보이므로 공개할 때는 필요한 부분을 가린다.

root만 승인된 서버에서 실행하는 예시는 다음과 같다.

```text
if python3 check_u08.py --allow root
then
    result=0
else
    result=$?
fi
printf '종료 코드: %s\n' "$result"
```
다른 관리 계정이 정식 승인됐다면 `--allow 계정명`을 계정마다 추가한다.

| 종료 코드 | 해석 |
| --- | --- |
| 0 | 입력 파일의 구성원이 승인 목록과 일치함. 서버 전체의 양호 판정은 아님 |
| 1 | 목록 차이, 미확인 구성원, 대상 그룹 누락 또는 GID 공유 항목이 있어 추가 확인 필요 |
| 2 | 파일 읽기·형식·인자 오류로 비교를 완료하지 못함 |

## 임시 자료로 기본 GID 누락을 확인한다

[check_u08.py 내려받기](../../downloads/check_u08.py). 실습에 필요한 파일은 아래 Bash 묶음에서 모두 만든다. `mktemp -d`가 정한 `$work` 안에 passwd와 group을 저장하므로 미리 준비할 운영 파일은 없다. Linux의 Bash와 Python 3로 실행한다.

실제 계정을 만들지 않고 가상 파일 두 개로 확인한다. root만 승인한 상태에서 기본 GID가 0인 `deploy`와 명시적 보조 구성원 `audit`을 넣으면 두 계정이 모두 승인 목록 밖으로 나와야 한다.

Bash에서 `check_u08.py`가 있는 디렉터리를 기준으로 아래 명령 전체를 실행한다.

```bash
(
    work=$(mktemp -d) || exit 2

    # 예제에서 만든 두 파일만 정리한다.
    cleanup() {
        rm -f -- "$work/passwd" "$work/group"
        rmdir -- "$work"
    }
    trap cleanup EXIT

    cat > "$work/passwd" <<'EOF'
root:x:0:0::/root:/bin/sh
deploy:x:1001:0::/srv/deploy:/bin/sh
audit:x:1002:1002::/home/audit:/bin/sh
EOF

    cat > "$work/group" <<'EOF'
root:x:0:audit
audit:x:1002:
EOF

    # 종료 코드 1도 비교를 완료한 결과이므로 값을 따로 기록한다.
    if python3 check_u08.py \
        --passwd "$work/passwd" \
        --group-file "$work/group" \
        --allow root
    then
        result=0
    else
        result=$?
    fi

    printf '종료 코드: %s\n' "$result"
    exit "$result"
)
```
다음은 위 가상 자료로 실행해 확인한 결과다.

```text
{
  "그룹": "root",
  "GID": 0,
  "같은 GID의 그룹": [
    "root"
  ],
  "기본 그룹 구성원": [
    "deploy",
    "root"
  ],
  "명시된 보조 구성원": [
    "audit"
  ],
  "승인 목록 밖": [
    "audit",
    "deploy"
  ],
  "승인됐지만 관찰되지 않음": [],
  "passwd에서 찾지 못한 구성원": [],
  "결과": "추가 확인"
}
종료 코드: 1
```

[[run:1:fold]]

`primary`는 passwd의 기본 GID로 만든 집합이고 `supplementary`는 같은 GID를 쓰는 그룹 행들의 구성원을 합친 집합이다. `observed = primary | supplementary`로 합친 뒤 `observed - allowed`를 구하므로 deploy와 audit이 함께 남는다. `--allow root`는 승인 목록을 전달하는 인자이며 실제 그룹을 바꾸지 않는다.

이 자료에서 ‘승인됐지만 관찰되지 않음’과 ‘passwd에서 찾지 못한 구성원’은 모두 비어 있다. 전자는 승인 목록 쪽의 누락, 후자는 group에만 있는 이름을 찾는 서로 다른 검사다. 마지막 `exit "$result"`가 수집기의 `1`을 바깥 Bash까지 전달하며, EXIT trap은 그 뒤에 준비한 두 파일을 정리한다.

deploy와 audit의 이름이 대조 결과에 남았으므로, 다음에는 두 계정의 관리 업무와 승인 내역을 조사한다.

## 그룹에서 제외할 때도 소속 경로를 확인한다

불필요한 계정으로 확인됐다면 승인된 변경 절차에 따라 해당 그룹에서 제외한다. Linux의 `gpasswd -d`는 그룹 파일의 명시적 구성원을 제거하는 조치다. 계정의 기본 GID가 대상 그룹의 GID와 같다면 이 목록만 정리해서는 그룹 소속이 사라지지 않는다.

기본 그룹을 변경해야 하는 경우에는 적절한 대상 그룹과 서비스 영향을 먼저 검토한다. `usermod -g`의 홈 디렉터리 내 파일 그룹 소유권 처리와 홈 밖 파일의 처리 범위도 확인해야 한다. 계정 자체를 삭제할지, 그룹 권한만 회수할지는 별개 결정이다. AIX 등 다른 Unix는 해당 OS의 계정 관리 명령과 저장 구조를 따른다.

계정 파일을 바꿔도 기존 세션과 서비스 프로세스가 이전 그룹 자격을 계속 사용할 수 있다. 필요한 세션 종료와 서비스 재시작은 담당자와 작업 시간을 정해 진행한다.

변경 후 새 세션에서 그룹 소속을 조회하고 로컬·중앙 관리 목록과 대조한다. 정상 업무에 필요한 접근은 유지되고 회수한 권한의 접근은 거부되는지 시험한 뒤, 승인 목록에 변경 사유를 반영한다.

## root 그룹 명단과 sudo 권한은 별도로 본다

root 그룹이 정리돼 있어도 개별 사용자나 다른 그룹에 `sudo` 권한이 부여될 수 있다. 반대로 `wheel`이나 `sudo`라는 그룹이 있다는 사실만으로 모든 명령 실행이 허용된다고 판단할 수는 없다. 실제 정책이 어떤 사용자·그룹에 어떤 대상 계정과 명령을 허용하는지 확인해야 한다.

U-08의 구성원 검토와 함께 관리자 권한 경로를 조사할 때는 sudo 정책, su 제한, 파일·디렉터리 접근 권한을 각각 확인한다. 이 스크립트가 비교하는 범위는 로컬 그룹 구성원이다. 다른 그룹은 `--group`으로 지정할 수 있지만, 그 그룹의 업무상 역할이나 실제 권한까지 자동으로 판단하지는 않는다.
