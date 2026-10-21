---
title: "U-09: 계정이 존재하지 않는 GID 금지"
description: "기본·보조 그룹 구성원을 조회하고, 그룹이 서비스나 파일에서 사용 중인지 확인합니다."
date: "2026-10-14T20:16:39+09:00"
updated: "2026-10-22"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-09", "GID"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 9
---

`/etc/group`의 `oldapp:x:3000:`처럼 구성원 칸이 빈 그룹도 계정의 기본 그룹이나 서비스 실행 그룹으로 쓰일 수 있다. 빈 칸만으로 사용 여부를 판단하기 어려운 이유다.

U-09에서는 계정과의 연결을 먼저 찾고 서비스·파일에서 사용하는 GID까지 조사한다. 그룹을 삭제해도 파일에 기록된 숫자 GID는 남기 때문에 소유권 처리 계획도 필요하다.

## 구성원 수보다 그룹의 용도를 확인한다

| 구분 | 기준 |
| --- | --- |
| 항목 | U-09: 계정이 존재하지 않는 GID 금지 |
| 중요도 | 하 |
| 대상 | SOLARIS, LINUX, AIX, HP-UX 등 |
| 양호 | 시스템 관리나 운용에 불필요한 그룹이 제거된 경우 |
| 취약 | 시스템 관리나 운용에 불필요한 그룹이 존재하는 경우 |

먼저 `/etc/group`과 `/etc/passwd`를 대조한다. 이어 해당 GID가 파일 소유권에 쓰이는지, 앞으로 권한을 부여하려고 미리 만든 그룹인지 조사한다. 구성원 유무는 조사 자료의 하나일 뿐, 그룹의 필요성을 그대로 나타내지는 않는다.

정리 과정에서는 그룹 이름과 숫자 GID(Group ID)를 함께 추적한다. 그룹 정의를 삭제해도 파일에 기록된 소유 GID가 자동으로 바뀌지는 않는다. 같은 번호를 다른 용도로 재사용하면 기존 자료에 의도치 않은 접근 권한이 생길 수 있다.

## 기본 그룹과 보조 그룹을 함께 찾는다

| 자료 | 확인할 내용 |
| --- | --- |
| `/etc/passwd` | 네 번째 필드인 계정의 기본 GID |
| `/etc/group` | 세 번째 필드인 GID와 네 번째 필드의 명시적 구성원 |
| 서비스·업무 설정 | 실행 그룹, 접근 권한을 부여한 목적, 유지 사유 |

아래는 설명용 가상 자료다. 계정 파일에는 `alice`가 등록돼 있다.

```text
alice:x:1000:1000::/home/alice:/bin/sh
```
그룹 파일에는 두 항목이 있다.

```text
alice:x:1000:
share:x:2000:alice
```
`alice` 그룹의 마지막 칸은 비어 있지만 계정의 기본 GID가 1000이므로 사용 중인 그룹이다. `share`에는 같은 계정이 보조 구성원으로 등록돼 있다. 기본 GID와 명시적 구성원 목록 중 한쪽만 보면 사용 관계를 놓친다.

서로 다른 그룹 이름이 같은 GID를 사용하는 경우에도 숫자를 기준으로 연결한다. 이름이 여러 개라는 사실만으로 U-09 취약으로 확정하지 않고, 별칭의 필요성과 실제 조회 결과를 확인한다.

## 로컬 파일과 이름 서비스 조회를 구분한다

다음은 Linux에서 `oldapp`과 GID 3000을 조사하는 읽기 전용 예제다. 두 값은 실제 점검 대상으로 바꾼다. 비밀번호 필드와 사용자 설명은 출력하지 않는다.

```text
# 대상 그룹의 GID와 명시적 구성원 확인
awk -F: -v g=oldapp '$1 == g {print "그룹=" $1, "GID=" $3, "명시구성원=" $4}' /etc/group

# 해당 GID를 기본 그룹으로 사용하는 계정 확인
awk -F: -v gid=3000 '$4 == gid {print "계정=" $1, "기본GID=" $4}' /etc/passwd

# 계정·그룹 조회에 사용하는 이름 서비스 설정 확인
grep -E '^[[:space:]]*(passwd|group|initgroups)[[:space:]]*:' /etc/nsswitch.conf
```
중앙 계정 관리가 연결돼 있다면 로컬 파일에 없는 이름도 실제로 존재할 수 있다. GNU `getent`는 NSS(Name Service Switch) 설정에 따라 계정과 그룹을 조회한다. 아래는 Bash 예제이며, `analyst`는 승인 명단이나 그룹 목록에서 확인한 실제 계정명으로 바꾼다.

```bash
(
    set -o pipefail

    getent group oldapp |
        awk -F: '{print "그룹=" $1, "GID=" $3, "명시구성원=" $4}'
    printf '그룹 조회 종료 코드: %s\n' "$?"

    getent passwd analyst |
        awk -F: '{print "계정=" $1, "UID=" $3, "기본GID=" $4}'
    printf '계정 조회 종료 코드: %s\n' "$?"

    id analyst
    printf '소속 조회 종료 코드: %s\n' "$?"
)
```
`pipefail`은 조회 실패가 뒤의 `awk` 성공에 가려지는 것을 막는다. 출력이 비었다면 표준 오류와 종료 상태부터 확인한다. 전체 목록 열거가 지원되지 않거나 중앙 조회·캐시에 문제가 있으면 빈 출력만으로 계정 부재를 입증할 수 없다. 중앙 승인 명단과 계정별 조회 결과를 대조해야 한다.

계정명 없이 실행한 `id`는 현재 프로세스의 소속을 보여 준다. 지정한 계정의 조회 결과와 혼동하지 않는다.

Linux의 shadow-utils 환경에서는 `/etc/gshadow`의 그룹 관리자·구성원 정보도 확인한다. 해당 파일을 읽을 권한이 있는 관리자가 필요한 필드만 조회하고 `/etc/group`과의 불일치를 조사한다.

```text
# 그룹 비밀번호 필드를 제외하고 관리자·구성원 확인
awk -F: -v g=oldapp '$1 == g {print "그룹=" $1, "관리자=" $3, "구성원=" $4}' /etc/gshadow
```
파일 전체나 두 번째 필드의 그룹 비밀번호 정보를 보고서에 복사하지 않는다. 다른 Unix는 해당 OS의 그룹 관리 방식에 맞춰 확인한다.

[[diagram]]

## 읽기 전용 스크립트로 검토 대상을 추린다

아래 코드를 `check_u09.py`로 저장한다. Linux에서 Python 3 표준 라이브러리만 사용하며, 로컬 계정·그룹 파일을 읽어 GID별 기본·보조 구성원을 연결한다.

이 코드는 `/etc/gshadow`, 중앙 디렉터리, 서비스 설정, 파일 권한을 자동으로 조사하지 않는다. 결과는 후속 검토 대상을 추리는 데 사용한다.

```python
#!/usr/bin/env python3
"""로컬 passwd/group 자료에서 그룹 검토 대상을 수집한다."""
import argparse
import json
import os
import re
import stat
import sys

LIMIT = 4 * 1024 * 1024
NAME = re.compile(r"[^\s:,\x00-\x1f\x7f]+\Z")


def name(value):
    if not NAME.fullmatch(value) or value.startswith(("+", "-", "#")):
        raise ValueError("지원하지 않는 이름 형식")
    return value


def number(value):
    if not re.fullmatch(r"[0-9]{1,10}", value) or int(value) > 4294967294:
        raise ValueError("UID 또는 GID 형식 오류")
    return int(value)


def rows(path, count):
    # 일반 파일만 읽고 FIFO에서 대기하지 않는다.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("일반 파일만 지원함")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("입력 파일이 4 MiB를 초과함")
    result, seen = [], set()
    for line in data.decode("utf-8").splitlines():
        if not line:
            continue
        fields = line.split(":")
        if len(fields) != count:
            raise ValueError("입력 필드 수 오류")
        key = name(fields[0])
        if key in seen:
            raise ValueError("중복 이름 또는 분할 그룹은 수동 확인 필요")
        seen.add(key)
        result.append(fields)
    if not result:
        raise ValueError("빈 계정 또는 그룹 목록")
    return result


def inspect(passwd_path, group_path):
    users, primary, groups = {}, {}, {}
    for row in rows(passwd_path, 7):
        number(row[2])
        gid = number(row[3])
        users[row[0]] = gid
        primary.setdefault(gid, set()).add(row[0])
    for row in rows(group_path, 4):
        gid = number(row[2])
        members = {name(x) for x in row[3].split(",")} if row[3] else set()
        entry = groups.setdefault(gid, {"names": [], "members": set()})
        entry["names"].append(row[0])
        entry["members"].update(members)
    findings = []
    for gid, entry in sorted(groups.items()):
        known = entry["members"] & users.keys()
        unknown = entry["members"] - users.keys()
        reasons = []
        if not primary.get(gid) and not known:
            reasons.append("로컬 구성원 미관찰")
        if unknown:
            reasons.append("명시 구성원의 로컬 계정 미관찰")
        if len(entry["names"]) > 1:
            reasons.append("같은 GID를 사용하는 여러 그룹 이름")
        if reasons:
            findings.append({
                "GID": gid,
                "그룹": sorted(entry["names"]),
                "기본 구성원": sorted(primary.get(gid, set())),
                "보조 구성원": sorted(known),
                "로컬 미관찰 이름": sorted(unknown),
                "사유": reasons,
            })
    missing = [
        {"계정": user, "기본GID": gid}
        for user, gid in sorted(users.items())
        if gid not in groups
    ]
    result = {"그룹 검토 대상": findings, "그룹 정의 없는 기본GID": missing}
    return (1 if findings or missing else 0), result


def main():
    parser = argparse.ArgumentParser(description="로컬 그룹 검토 자료 수집")
    parser.add_argument("--passwd", default="/etc/passwd", help="계정 파일 경로")
    parser.add_argument("--group", default="/etc/group", help="그룹 파일 경로")
    args = parser.parse_args()
    try:
        status, result = inspect(args.passwd, args.group)
    except (OSError, ValueError) as exc:
        print("실행 오류: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("추가 확인 필요" if status else "기계적 검토 대상 없음: 보안 양호 판정은 아님")
    return status


if __name__ == "__main__":
    sys.exit(main())
```
`rows()`는 일반 파일만 읽고 크기·필드 수·이름 중복을 검사한다. 입력은 UTF-8이며 파일당 최대 4 MiB다. NIS 지시 행이나 같은 이름을 여러 행으로 나눈 분할 그룹 등 지원하지 않는 형식은 오류로 중단한다. 이런 오류를 취약 판정으로 집계해서는 안 된다.

`inspect()`는 계정의 기본 GID와 그룹의 명시적 구성원을 연결한다. 로컬에 존재하는 보조 구성원과 이름만 남은 구성원을 구분하고, 같은 GID의 여러 그룹 이름도 함께 표시한다.

`그룹 정의 없는 기본GID`는 반대 방향의 참조를 확인하는 보조 결과다. 계정이 지정한 GID가 입력한 그룹 목록에 없다는 뜻이며, 아무 계정도 사용하지 않는 그룹과는 다르다. 중앙 그룹이 입력에서 빠졌을 가능성도 확인한다.

두 파일을 동시에 고정해 읽는 방식은 아니다. 수집 중 계정·그룹 변경이 있었다면 변경이 끝난 뒤 다시 확인한다.

```text
if python3 check_u09.py
then
    result=0
else
    result=$?
fi
printf '종료 코드: %s\n' "$result"
```
| 종료 코드 | 의미 |
| --- | --- |
| 0 | 코드가 찾는 자동 검토 항목이 없음. 모든 그룹의 필요성이나 서버 전체 양호를 뜻하지 않음 |
| 1 | 그룹 또는 계정 연결 관계에 추가 확인 대상이 있음 |
| 2 | 입력·형식·읽기·실행 인자 오류로 점검을 완료하지 못함 |

## 임시 파일로 결과를 확인한다

ZIP의 `check_u09.py` 파일을 사용한다. 준비 명령 안의 `mktemp -d`가 `$work`를 만들고 passwd와 group을 채운다. 실행 기록의 `$LAB`을 실제 경로로 입력할 필요는 없다. Linux의 Bash와 Python 3가 필요하다.

다음 예제는 가상 계정·그룹 파일만 생성한다. 실제 계정을 만들거나 변경하지 않는다. Bash에서 `check_u09.py`가 있는 디렉터리를 기준으로 명령 전체를 실행한다.

```bash
(
    work=$(mktemp -d) || exit 2

    # 이 예제에서 만든 가상 파일만 정리한다.
    cleanup() {
        rm -f -- "$work/passwd" "$work/group"
        rmdir -- "$work"
    }
    trap cleanup EXIT

    cat > "$work/passwd" <<'EOF'
root:x:0:0::/root:/bin/sh
alice:x:1000:1000::/home/alice:/bin/sh
EOF

    cat > "$work/group" <<'EOF'
root:x:0:
alice:x:1000:
share:x:2000:alice
oldapp:x:3000:
EOF

    # 종료 코드 1도 비교를 완료한 결과이므로 값을 따로 기록한다.
    if python3 check_u09.py --passwd "$work/passwd" --group "$work/group"
    then
        result=0
    else
        result=$?
    fi

    printf '종료 코드: %s\n' "$result"
    exit "$result"
)
```
아래는 위 자료로 실행해 확인한 결과다.

```text
{
  "그룹 검토 대상": [
    {
      "GID": 3000,
      "그룹": [
        "oldapp"
      ],
      "기본 구성원": [],
      "보조 구성원": [],
      "로컬 미관찰 이름": [],
      "사유": [
        "로컬 구성원 미관찰"
      ]
    }
  ],
  "그룹 정의 없는 기본GID": []
}
추가 확인 필요
종료 코드: 1
```

[[run:1:fold]]

`primary`는 GID별 기본 구성원 집합이다. 그룹 파일의 명시 이름은 로컬 계정표와 교집합을 구해 `known`, 차집합을 구해 `unknown`으로 나눈다. oldapp의 GID 3000에는 기본 구성원도 `known`도 없어 ‘로컬 구성원 미관찰’이 붙었다. 반면 share는 alice를 보조 구성원으로 참조하므로 후보에서 빠진다.

`그룹 정의 없는 기본GID`가 빈 것은 root와 alice의 기본 GID가 모두 group 입력에 있기 때문이다. 이 항목은 oldapp의 필요성을 승인하지도, 파일·서비스의 GID 사용 여부를 조회하지도 않는다. `exit "$result"`가 후보 발견 코드 `1`을 바깥 Bash에 전달하고 trap이 가상 파일을 정리한다.

추가 조사 대상은 `oldapp`이다. 계정 파일에서 구성원이 발견되지 않았으므로 다음에는 GID 3000으로 실행되는 서비스와 그 GID가 소유한 파일을 찾는다.

구성원 이름을 계정 자료에 없는 `ghost`로 바꾸면 `로컬 미관찰 이름`에 표시된다. 삭제된 계정의 흔적일 수도 있고 중앙 계정일 수도 있으므로 로컬 결과만으로 제거하지 않는다.

## 그룹을 사용하는 서비스와 파일까지 확인한다

systemd 서비스는 `Group=`과 `SupplementaryGroups=`로 실행 그룹을 지정할 수 있다. `DynamicUser=`로 동적 할당된 계정·그룹은 실행 중 관리되며 `/etc/passwd`와 `/etc/group`에 추가되지 않는다. 서비스 설정과 실행 중인 프로세스의 그룹 정보를 함께 확인해야 한다.

파일 조사는 담당자와 합의한 파일시스템·경로부터 진행한다. 아래는 GNU `find` 예제이며, `/srv/app`과 3000은 실제 점검 경로와 GID로 바꾼다.

```text
# 숫자 GID가 3000인 파일·디렉터리 확인
find /srv/app -xdev -gid 3000 -ls

# 소유 GID에 대응하는 그룹을 조회할 수 없는 파일·디렉터리 확인
find /srv/app -xdev -nogroup -ls
```
첫 명령은 특정 GID가 소유한 자원을 찾는다. 두 번째는 그룹 정의를 조회할 수 없는 자원을 찾는다. 그룹이 존재하지만 구성원만 없는 경우에는 `-nogroup`으로 찾을 수 없다.

`-xdev`는 다른 파일시스템 내부로 내려가지 않으므로 별도 마운트는 따로 조사한다. 접근 거부와 조회 오류를 숨기지 말고 확인 범위와 누락 범위를 기록한다. 중앙 그룹 조회에 장애가 있다면 `-nogroup` 결과도 그 영향을 구분해 해석한다.

파일의 소유 그룹 외에 ACL(Access Control List)의 그룹 권한, 애플리케이션 설정, 배치 작업과 패키지 요구 사항도 확인한다. 사용자 네임스페이스를 사용하는 컨테이너라면 내부 GID와 호스트 GID의 매핑을 확인한 뒤 숫자를 비교한다.

## 불필요함이 확인된 뒤 조치한다

그룹의 유지 사유는 연결된 계정·서비스·소유 파일과 담당자에게서 찾는다. 예정된 업무를 위해 미리 만든 그룹은 사용 예정일과 재검토 시점을 적어 둔다. 이름이 시스템 기본 그룹처럼 보인다는 이유만으로 조사를 끝내지 않는다.

불필요함이 확인되면 변경 승인과 복구 계획을 마련하고 필요한 자료의 소유권·ACL을 정리한다. Linux의 `groupdel 그룹명`은 그룹 정의를 제거하며 소유 파일을 대신 정리하지 않는다. 기본 그룹으로 사용하는 계정이 있다면 그 사용 관계부터 해결하고 강제 삭제로 검사를 건너뛰지 않는다.

조치 후에는 그룹 조회 결과, 기존 GID로 남은 파일, 관련 서비스의 실행과 접근 결과를 다시 확인한다. 기존 프로세스의 그룹 권한이 그룹 파일 수정만으로 모두 즉시 사라지지는 않으므로 필요한 세션 갱신과 서비스 재시작은 영향 검토 후 진행한다.
