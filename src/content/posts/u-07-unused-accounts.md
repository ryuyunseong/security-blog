---
title: "U-07: 불필요한 계정 제거"
description: "미사용 계정 후보를 승인 목록·업무 의존성과 대조하고 제거 전에 확인할 범위를 정리합니다."
date: "2026-10-12T20:48:05+09:00"
updated: "2026-10-16T00:00:00+09:00"
category: "unix"
tags: ["주통기", "U-07", "계정관리"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 7
---

오랫동안 로그인하지 않은 계정을 지웠더니 배치 작업이 멈출 수도 있다. 서비스 계정이라면 대화형 로그인 기록이 없는 편이 오히려 자연스럽다.

U-07에서는 계정 목록만 보고 삭제를 결정하지 않는다. 인사·업무 변경 내역과 승인 목록을 대조해 검토 대상을 찾고, 서비스와 파일의 사용 관계를 확인한 뒤 처리한다.

## 사용하지 않는 계정과 불필요한 계정을 구분한다

2026년 주요정보통신기반시설 가이드의 U-07은 불필요한 계정이 남아 있는지 확인하는 항목이다.

| 구분 | 기준 |
| --- | --- |
| 항목 | U-07: 불필요한 계정 제거 |
| 중요도 | 하 |
| 대상 | SOLARIS, LINUX, AIX, HP-UX |
| 양호 | 불필요한 계정이 없는 경우 |
| 취약 | 불필요한 계정이 존재하는 경우 |

퇴직·전직·휴직이나 장기 미사용으로 관리에서 빠진 계정이 주요 확인 대상이다. 다만 가이드가 모든 서버에 적용할 “미사용 90일” 같은 공통 기간을 정한 것은 아니다. 조직의 계정 관리 기준과 인사·업무 변경 내역을 대조해야 한다.

휴직 중 유지가 필요한 계정이나 승인된 비상용 계정이라면 유지 사유와 접근 제한을 확인한다. 기본 계정도 이름만 보고 삭제하지 않는다. lp, uucp 등이 필요한지는 설치된 패키지와 서비스에 따라 달라지므로 먼저 업무 영향을 살펴야 한다.

## 계정 목록은 사용 근거와 함께 읽는다

로컬 계정은 /etc/passwd에서 확인한다. 아래 예제는 비밀번호 필드와 사용자 설명을 제외하고 계정명·UID·홈 디렉터리·셸만 출력한다. 파일 읽기 권한이 있다면 첫 명령에는 관리자 권한이 필요하지 않다.

```text
# 로컬 계정의 기본 정보 확인
awk -F: '{printf "계정=%s UID=%s 홈=%s 셸=%s\n", $1, $3, $6, $7}' /etc/passwd

# analyst는 실제 확인할 계정명으로 바꾼다.
# NSS 조회 결과도 비밀번호 필드와 사용자 설명을 제외한다.
getent passwd analyst |
    awk -F: '{printf "계정=%s UID=%s 홈=%s 셸=%s\n", $1, $3, $6, $7}'

id analyst
last analyst
```
getent는 이름 서비스 전환(Name Service Switch, NSS) 설정을 따라 조회한다. LDAP·AD 등 중앙 계정 서비스나 관련 캐시에 접근할 수 있어 로컬 파일만 읽는 명령과는 범위가 다르다. getent passwd로 전체 목록을 요청하더라도 SSSD의 열거 설정에 따라 중앙 계정이 빠질 수 있다. 중앙 관리 목록을 대조하고, 필요한 계정은 이름을 지정해 조회한다.

last는 보관된 로그인 기록을 보여준다. 기록 파일의 시작 시점과 교체·보관 정책, 접속 방식에 따라 과거 사용이 보이지 않을 수 있다. 출력이 비었다는 이유만으로 미사용 계정이라고 판단하지 않는다. 프로세스 실행이나 예약 작업도 별도로 확인해야 한다.

계정 관리대장에는 계정명과 함께 다음 근거를 남긴다.

| 확인할 근거 | 판단에 연결할 내용 |
| --- | --- |
| 사용 목적·책임자 | 현재 업무나 서비스에 필요한지, 책임자가 변경됐는지 |
| 인사·계약·승인 내역 | 퇴직·이동·휴직·계약 종료 후 회수할 접근 권한이 남았는지 |
| 프로세스·서비스·예약 작업 | 해당 UID로 실행되거나 계정명을 참조하는 업무가 있는지 |
| 파일 소유권·보관 의무 | 삭제 전에 이관하거나 보관할 자료가 있는지 |
| 접속 수단·개별 권한 | 비밀번호 외 공개키, 중앙 인증, 추가 그룹과 별도 권한이 남았는지 |

## 승인 목록과 다른 계정을 찾는 스크립트

아래 코드는 유지 필요성을 검토한 로컬 계정 목록과 passwd 파일을 비교한다. 승인 목록에 없는 계정과, 승인 목록에는 있지만 로컬 파일에는 없는 이름을 출력한다. 이 차이는 추가 확인 대상이며 자동 삭제 목록이 아니다.

approved.txt에는 한 줄에 계정명 하나를 적는다. 시스템·서비스 계정도 필요성을 검토한 뒤 포함한다. 유지 사유와 담당자, 검토 이력은 별도 관리대장에 연결한다.

```text
root
svc
analyst
```
현재 /etc/passwd의 이름을 그대로 복사하면 필요성을 검토하지 않아도 일치 결과가 나온다. 승인 목록은 실제 계정 목록과 독립된 승인 근거로 작성해야 한다.

코드를 check_u07.py로 저장한다. Linux에서 Python 3 표준 라이브러리만 사용하며, 두 입력 파일을 읽고 결과를 표준 출력으로 내보낸다. /etc/shadow 조회나 계정 잠금·삭제는 수행하지 않는다.

```python
#!/usr/bin/env python3
import argparse
import json
import os
import re
import stat
import sys

LIMIT = 2 * 1024 * 1024
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*\$?", re.ASCII)


def read_text(path):
    # 일반 파일만 읽고 입력 크기를 제한한다. 설정은 변경하지 않는다.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("일반 파일이 아닌 입력")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("입력 파일이 2 MiB를 초과함")
    return data.decode("utf-8")


def parse_passwd(text):
    accounts = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line:
            continue
        fields = line.split(":")
        if len(fields) != 7 or not NAME.fullmatch(fields[0]):
            raise ValueError(f"passwd {number}행: 지원하지 않는 계정 형식")
        name, _, uid, gid, _, home, shell = fields
        if not all(re.fullmatch(r"[0-9]{1,10}", value) for value in (uid, gid)):
            raise ValueError(f"passwd {number}행: UID/GID 형식 확인 필요")
        if name in accounts:
            raise ValueError(f"passwd {number}행: 계정 이름 중복")
        accounts[name] = {
            "계정": name,
            "UID": int(uid),
            "홈": home,
            "셸": shell or "(빈 값)",
        }
    if not accounts:
        raise ValueError("passwd에서 계정을 읽지 못함")
    return accounts


def parse_approved(text):
    approved = set()
    for number, line in enumerate(text.splitlines(), 1):
        name = line.strip()
        # 승인 목록에서만 빈 줄과 #으로 시작하는 설명을 허용한다.
        if not name or name.startswith("#"):
            continue
        if not NAME.fullmatch(name) or name in approved:
            raise ValueError(f"승인 목록 {number}행: 이름 형식 또는 중복 확인 필요")
        approved.add(name)
    if not approved:
        raise ValueError("승인 목록이 비어 있음")
    return approved


def main():
    parser = argparse.ArgumentParser(
        description="로컬 계정과 승인 목록을 읽기 전용으로 비교"
    )
    parser.add_argument(
        "--passwd", default="/etc/passwd", help="점검할 passwd 파일"
    )
    parser.add_argument(
        "--approved", required=True, help="유지 필요성이 검토된 로컬 계정 목록"
    )
    args = parser.parse_args()

    try:
        accounts = parse_passwd(read_text(args.passwd))
        approved = parse_approved(read_text(args.approved))
    except (OSError, UnicodeError, ValueError) as error:
        print("오류: " + str(error), file=sys.stderr)
        return 2

    extra = sorted(set(accounts) - approved)
    missing = sorted(approved - set(accounts))
    result = {
        "수집한 로컬 계정 수": len(accounts),
        "승인 목록에 없는 계정": [accounts[name] for name in extra],
        "로컬 파일에 없는 승인 계정": missing,
        "결과": "추가 확인 필요" if extra or missing else "목록 대조 완료",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if extra or missing else 0


if __name__ == "__main__":
    sys.exit(main())
```
read_text()는 일반 파일인지 확인하고 입력 크기를 제한한다. parse_passwd()는 일곱 필드와 계정명·UID/GID 형식, 이름 중복을 검사하고 대조에 필요한 값만 남긴다. parse_approved()가 읽은 이름 집합과 비교해 양쪽 차이를 구한다.

UID가 작거나 셸이 nologin이어도 비교에서 제외하지 않는다. 시스템 계정인지, 대화형 로그인이 제한됐는지와 업무상 필요한지는 각각 다른 문제이기 때문이다.

## 실제 계정을 만들지 않고 결과를 확인한다

다음 예제는 임시 디렉터리에 가상 계정 파일과 승인 목록을 만든다. oldvendor가 승인 목록에서 빠진 상황이며 실제 시스템 계정은 변경하지 않는다. Bash에서 check_u07.py가 있는 디렉터리를 기준으로 실행한다.

```bash
(
    # 임시 디렉터리를 만들지 못하면 바로 중단한다.
    work=$(mktemp -d) || exit 2

    cat > "$work/passwd" <<'EOF'
root:x:0:0:관리자:/root:/bin/bash
svc:x:990:990:서비스:/srv/svc:/usr/sbin/nologin
oldvendor:x:1201:1201:외부인력:/home/oldvendor:/bin/bash
EOF

    cat > "$work/approved.txt" <<'EOF'
root
svc
EOF

    # 종료 코드 1도 정상적인 비교 결과이므로 값을 따로 기록한다.
    if python3 check_u07.py \
        --passwd "$work/passwd" \
        --approved "$work/approved.txt"
    then
        status=0
    else
        status=$?
    fi
    printf '종료 코드: %s\n' "$status"

    # 이 예제에서 만든 가상 파일만 삭제한다.
    rm -- "$work/passwd" "$work/approved.txt"
    rmdir -- "$work"
)
```
아래는 이 가상 자료로 실행해 확인한 출력이다.

```text
{
  "수집한 로컬 계정 수": 3,
  "승인 목록에 없는 계정": [
    {
      "계정": "oldvendor",
      "UID": 1201,
      "홈": "/home/oldvendor",
      "셸": "/bin/bash"
    }
  ],
  "로컬 파일에 없는 승인 계정": [],
  "결과": "추가 확인 필요"
}
종료 코드: 1
```
예제에서는 의도한 차이가 표시돼 검증이 성공했다. 하지만 oldvendor가 실제로 불필요한지는 이 결과로 알 수 없다. 계약이 끝났는지, 다른 업무로 재승인됐는지, 승인 목록이 갱신되지 않았는지를 확인해야 한다.

| 종료 코드 | 의미 |
| --- | --- |
| 0 | 두 계정 목록이 일치함. 이것만으로 U-07 양호 판정은 할 수 없음 |
| 1 | 비교를 완료했으며 추가 확인할 이름 차이가 있음 |
| 2 | 파일 읽기·입력 형식·실행 인자 오류로 비교를 완료하지 못함 |

실제 점검에서는 검토한 승인 목록을 지정한다. 기본 비교 대상은 /etc/passwd다.

```bash
python3 check_u07.py --approved approved.txt
```
승인 목록에만 남은 이름은 계정 삭제 후 목록이 갱신되지 않았거나 중앙 계정을 잘못 포함한 경우일 수 있다. 로컬 계정용 목록인지부터 확인한다.

## 자동 대조로 확인할 수 없는 부분

이 코드는 중앙 계정, 컨테이너 내부 계정, 애플리케이션 자체 계정을 수집하지 않는다. 이름이 같아도 소유자나 사용 목적이 바뀌었는지, 권한이 적절한지는 확인하지 못한다. UID 중복도 별도 점검 대상이다. 최종 판단에는 승인 목록의 정확성과 시스템별 조사 범위를 함께 기록한다.

입력 계정명은 영문자·밑줄로 시작하고, 이후 영문자·숫자·밑줄·점·하이픈과 끝의 $를 허용한다. 이 범위 밖의 계정명, NIS 호환 행, UTF-8이 아닌 파일은 오류로 중단한다. 이는 계정이 불필요하다는 뜻이 아니라 해당 입력을 이 코드로 해석하지 못했다는 뜻이다. 파일 크기는 각각 최대 2 MiB다.

/etc/passwd의 계정 행 앞에 #을 붙이는 방식은 정상적인 계정 비활성화 조치로 사용하지 않는다. 위 코드가 설명용 # 행을 허용하는 곳은 별도로 만든 승인 목록뿐이다.

출력에는 비밀번호 필드와 사용자 설명이 포함되지 않는다. 다만 계정명과 홈 경로도 운영 정보이므로 실제 결과를 공개할 때는 필요한 부분을 가린다.

## 삭제 전 의존성을 확인하고 조치 후 다시 대조한다

불필요한 계정으로 확인됐다면 변경 승인과 보관 기준에 따라 제거한다. 실행 중인 업무, 서비스 설정, 예약 작업, 소유 파일과 공유 자원 접근을 먼저 확인한다. 로그인 기록이 없더라도 자동화 작업의 실행 주체일 수 있으므로 업무 담당자와 함께 검토해야 한다.

Linux의 userdel은 계정 제거에 사용한다. -r을 붙이면 홈 디렉터리와 그 안의 파일, 메일 스풀도 삭제 대상이 된다. 홈 밖의 소유 파일까지 모두 정리하는 옵션은 아니다. 백업·보존·소유권 이관 범위를 정한 뒤 조치하고, 실행 중인 프로세스 때문에 제거가 거부됐다면 의존성을 확인한다. 강제 삭제로 먼저 해결하려 해서는 안 된다.

AIX의 계정 제거에는 가이드에서 rmuser를 안내한다. 실제 조치는 해당 OS와 설치된 버전의 관리 절차를 따른다.

즉시 제거하기 어려워 usermod -L로 비밀번호를 잠갔다면 임시 제한으로 기록한다. 이 옵션은 비밀번호 잠금이며, 공개키·중앙 인증·기존 세션·서비스 실행까지 모두 차단하거나 종료했다는 근거가 아니다. 불필요한 계정 자체도 남아 있으므로 제거 기한을 별도로 관리한다.

조치 후에는 로컬·중앙 계정 목록과 승인 목록을 다시 대조한다. 관련 서비스의 정상 동작, 남은 파일의 소유권, 별도 접근 권한도 확인한다. 최종 결과에는 어떤 계정을 어떤 근거로 유지하거나 제거했는지 남긴다.

## 참고 자료

- [2026년 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.krcert.or.kr/kr/bbs/view.do?bbsId=B0000127&menuNo=205021&nttId=71928)
- [shadow-utils: passwd 파일 형식](https://github.com/shadow-maint/shadow/blob/master/man/passwd.5.xml)
- [SSSD: 계정 조회와 목록 열거](https://sssd.io/troubleshooting/basics.html)
- [GNU C Library: getent의 계정 조회 구현](https://github.com/bminor/glibc/blob/master/nss/getent.c)
- [util-linux: last의 로그인 기록 조회](https://github.com/util-linux/util-linux/blob/master/login-utils/last.1.adoc)
- [shadow-utils: userdel의 제거 범위](https://github.com/shadow-maint/shadow/blob/master/man/userdel.8.xml)
- [shadow-utils: usermod의 비밀번호 잠금](https://github.com/shadow-maint/shadow/blob/master/man/usermod.8.xml)
