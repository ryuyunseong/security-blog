---
title: "U-06: 사용자 계정 su 기능 제한"
description: "su 실행 권한과 PAM 그룹 제한이 실제 사용자 전환 경로에 적용되는지 확인합니다."
date: "2026-10-11T15:59:47+09:00"
updated: "2026-10-17T00:00:00+09:00"
category: "unix"
tags: ["주통기", "U-06", "PAM"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 6
---

`wheel` 그룹을 만든 뒤 구성원을 넣었다고 `su` 제한이 끝나는 것은 아니다. 파일 실행 권한이나 PAM 규칙이 그 그룹을 검사해야 제한이 동작한다.

파일을 실행할 수 있는지와 다른 사용자로 전환할 수 있는지는 따로 확인한다. 아래 내용은 U-06 중 Linux 로컬 파일 점검에 해당하며, Solaris·AIX·HP-UX는 각각의 인증 구조에 맞춰 점검한다.

## 비밀번호 인증과 su 사용 자격은 다르다

`su`는 다른 사용자와 그룹의 식별자로 명령을 실행하는 도구다. 대상을 생략하면 일반적으로 root로 전환한다. 대상 계정의 비밀번호를 확인하는 인증(Authentication)과 요청자에게 su 사용을 허용하는 접근통제는 별개다.

| 상태 | U-06 판단 기준 |
| --- | --- |
| 특정 그룹의 사용자만 su를 사용할 수 있음 | 양호 조건. 그룹의 존재뿐 아니라 제한이 적용되는 경로와 구성원을 확인한다. |
| 모든 사용자가 su를 사용할 수 있도록 설정됨 | 취약 조건. 비밀번호 입력만으로 그룹 제한을 대신할 수는 없다. |
| 일반 사용자 계정 없이 root 계정만 사용함 | 가이드의 제한 불필요 예외. 중앙 계정과 실제 운영 방식까지 확인한 뒤 적용한다. |

비밀번호 잠금이나 nologin 셸만 보고 root 계정만 사용하는 환경이라고 판단하지 않는다. 서비스 계정과 중앙 계정, 다른 인증 경로도 확인한다. U-06 점검만으로 sudo 등 다른 관리자 전환 경로의 안전성이 검증되는 것은 아니다.

## 파일 실행 권한과 PAM 규칙을 나눠 확인한다

먼저 사용하는 su의 위치와 구현을 확인한다. 다음은 GNU stat을 사용하는 Linux의 조회 명령이며 su를 실행하지 않는다. 실제 경로가 다르면 명령의 경로도 바꾼다.

```bash
type -a su
readlink -f /usr/bin/su
stat -Lc '경로=%n UID=%u GID=%g 모드=%a' /usr/bin/su

# ACL 도구가 설치되어 있다면 추가 확인한다.
getfacl -p /usr/bin/su
```
모드 `4750`은 set-user-ID 비트를 유지하고, 소유자에게 읽기·쓰기·실행, 그룹에 읽기·실행 권한을 주며 기타 사용자에게는 권한을 주지 않는다. 파일 권한으로 제한하려면 root 소유의 su에 올바른 허용 그룹을 연결하고 불필요한 구성원을 제거해야 한다. 모드 숫자만 같아서는 충분하지 않다.

`4755`의 기타 사용자 실행 비트만 보고 취약으로 단정하지도 않는다. util-linux의 su는 PAM을 사용하므로 인증 단계의 그룹 제한도 확인한다. 반대로 실행 비트만으로 제한을 확정하지 말고 ACL, 다른 su 경로, 파일 소유권과 변경 권한을 살펴본다. set-user-ID 비트만 제거하는 조치는 허용 그룹 정책을 구성하는 것과 다르다.

## pam_wheel 규칙에 도달하는지 확인한다

PAM(Pluggable Authentication Modules)은 서비스별 인증 규칙을 조합한다. `pam_wheel.so`가 설치돼 있는 것과 실제 제한이 작동하는 것은 다르다. su의 인증 흐름에서 이 규칙이 실행되고, 비허용 사용자의 거부가 최종 실패로 이어져야 한다.

```text
# /etc/pam.d/su의 그룹 제한 규칙 예시
auth required pam_wheel.so use_uid group=wheel
```
이 줄은 그룹 제한 규칙의 예시다. 전체 PAM 파일을 대체하는 설정은 아니며, 기존 비밀번호 검증과 account·session 규칙을 함께 검토해야 한다.

| 설정·옵션 | 확인할 의미 |
| --- | --- |
| `required` | 규칙이 실행돼 실패하면 일반적인 흐름에서 최종 실패에 반영된다. 앞선 규칙이 이 줄을 건너뛰는지 확인한다. |
| `use_uid` | 호출 프로세스의 실제 UID로 요청자를 확인한다. 전환 대상 계정의 UID를 검사하는 옵션이 아니다. |
| `group=wheel` | 검사할 그룹을 명시한다. 생략하면 wheel을 사용하고, wheel이 없으면 GID 0 그룹을 사용한다. |
| `root_only` | 전환 대상 UID가 0일 때만 그룹을 검사한다. 일반 계정으로의 전환까지 제한하는 설정은 아니다. |
| `trust` | 그룹원에 대한 반환값을 성공으로 바꾼다. PAM의 다른 규칙과 결합해 비밀번호 없이 인증을 끝낼 수 있다. |
| `deny` | 허용·거부 방향을 뒤집는다. 일반적인 허용 목록 설정과 구분해 해석한다. |

앞선 required 실패가 없는 상태에서 `sufficient` 규칙이 성공하면 뒤의 규칙을 실행하지 않고 해당 스택이 끝날 수 있다. 일반 사용자도 성공할 수 있는 규칙이 앞에 있다면 pam_wheel을 건너뛰는지 확인한다. `pam_rootok.so`는 실제 UID 0인 호출자를 검사하므로 앞에 있다는 이유만으로 일반 사용자 우회라고 판단하지 않는다.

pam_wheel을 sufficient나 optional로만 사용했다면 비그룹 사용자의 실패가 최종 거부로 이어지는지 따로 살펴본다. `include`, `substack`, `@include`로 연결된 파일과 대괄호 제어식도 따라가야 한다.

util-linux는 일반 su와 로그인 방식인 `su -`에 각각 su와 su-l PAM 서비스를 사용한다. 두 경로를 확인하고, 파일이 없다면 배포판의 다른 설정 위치와 기본 규칙도 확인한다.

## 기본 그룹과 추가 그룹을 함께 확인한다

`/etc/group`의 마지막 필드는 명시된 추가 그룹 구성원이다. `/etc/passwd`의 기본 GID가 해당 그룹과 같은 계정도 구성원이므로 마지막 필드만 확인해서는 안 된다.

다음은 wheel 그룹과 admin 계정의 조회 예시다. 점검 대상의 실제 허용 그룹과 계정으로 바꿔 사용한다.

```bash
getent group wheel
id admin
grep -E '^(passwd|group|initgroups):' /etc/nsswitch.conf
```
LDAP·AD·SSSD를 연동한다면 NSS(Name Service Switch)가 반환하는 계정별 그룹 정보와 중앙 저장소의 허용 목록을 대조한다. `getent group`의 결과에 모든 구성원이 열거된다고 가정하지 않는다. 이 조회는 설정을 바꾸지 않지만 중앙 서버에 요청을 보낼 수 있다.

파일 실행 권한에는 실행 중인 프로세스의 그룹 자격 증명이 사용된다. 그룹 변경 뒤 기존 세션에 새 자격 증명이 반영됐는지도 확인한다.

## 스크립트로 계정·그룹과 su·PAM 설정을 조회한다

다음 코드를 `check_u06.py`로 저장한다. Python 3으로 passwd·group, su 파일 속성, `/etc/pam.d/su`와 `/etc/pam.d/su-l`을 확인한다. 기본 그룹과 추가 그룹을 나눠 출력하고, PAM 파일에서는 주석과 빈 줄을 제외한 원문과 줄 번호를 남긴다.

인증 시도, 계정 변경, NSS 조회, PAM 모듈 로딩은 하지 않는다. 대상 파일을 읽을 수 있으면 관리자 권한은 필요하지 않다. 실행 중 파일이 바뀌지 않는 신뢰할 수 있는 경로에서 사용한다. 출력에 계정명과 로컬 인증 구성이 포함되므로 점검 자료로 관리한다.

```python
#!/usr/bin/env python3
"""su 관련 파일을 읽는다. 인증 실행이나 양호·취약 자동 판정은 하지 않는다."""
import argparse
import pathlib
import re
import stat


def collect(root, group, binary):
    incomplete = False

    def warn(message):
        nonlocal incomplete
        incomplete = True
        print('[확인 필요] ' + message)

    def locate(name):
        path = (root / name.lstrip('/')).resolve()
        if root != path and root not in path.parents:
            raise ValueError('수집 범위 밖을 가리키는 경로')
        return path

    def read(name):
        try:
            path = locate(name)
            if not path.is_file() or path.stat().st_size > 1024 * 1024:
                raise ValueError('일반 파일이 아니거나 크기 제한 초과')
            return path.read_text(encoding='utf-8').splitlines()
        except (OSError, ValueError, RuntimeError) as error:
            warn(f'{name}: {type(error).__name__}')
            return None

    # 비밀번호 필드는 결과에 포함하지 않는다.
    users, groups = [], []
    for name, size, target in [('/etc/passwd', 7, users),
                               ('/etc/group', 4, groups)]:
        lines = read(name)
        if lines is None:
            continue
        for number, line in enumerate(lines, 1):
            parts = line.split(':')
            numeric = (2, 3) if size == 7 else (2,)
            if (len(parts) != size or not parts[0] or
                parts[0].startswith(('+', '-')) or
                any(not re.fullmatch(r'[0-9]{1,10}', parts[i]) for i in numeric)):
                warn(f'{name}:{number} 레코드 형식 확인')
                continue
            if size == 7:
                target.append((parts[0], int(parts[3])))
            else:
                target.append((parts[0], int(parts[2]), parts[3]))
    matches = [entry for entry in groups if entry[0] == group]
    if len(matches) != 1:
        warn('지정 그룹의 로컬 레코드가 정확히 하나가 아님')
    else:
        _, gid, members = matches[0]
        primary = sorted(name for name, user_gid in users if user_gid == gid)
        print(f'[그룹] {group} GID={gid}')
        print('[기본 그룹] ' + (','.join(primary) or '(로컬 기록 없음)'))
        print('[추가 그룹] ' + (members or '(명시된 구성원 없음)'))

    # su를 실행하지 않고 대상 파일의 숫자 소유권과 모드만 읽는다.
    try:
        path = locate(binary)
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('일반 파일이 아님')
        print(f'[파일] {binary} UID={info.st_uid} GID={info.st_gid} '
              f'모드={stat.S_IMODE(info.st_mode):04o}')
        print('[기타 사용자 실행 비트] ' +
              ('있음' if info.st_mode & stat.S_IXOTH else '없음'))
    except (OSError, ValueError, RuntimeError) as error:
        warn(f'{binary}: {type(error).__name__}')

    for service in ('su', 'su-l'):
        name = '/etc/pam.d/' + service
        lines = read(name)
        if lines is None:
            continue
        print(f'[PAM 파일] {name}')
        found = False
        for number, line in enumerate(lines, 1):
            text = line.strip()
            if not text or text.startswith('#'):
                continue
            # 흐름을 해석하지 않고 원문과 줄 번호를 남긴다.
            print(f'  {number}: {text}')
            found = True
        if not found:
            warn(name + ': 활성 줄 없음')
    print('[범위] 로컬 파일 수집; PAM 흐름·모듈 로딩·NSS·ACL은 별도 확인')
    print('[판정] 자동 판정하지 않음')
    return 2 if incomplete else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='/', help='수집할 파일 트리')
    parser.add_argument('--group', default='wheel', help='확인할 허용 그룹')
    parser.add_argument('--su', default='/usr/bin/su', help='확인할 su 경로')
    args = parser.parse_args()
    try:
        return collect(pathlib.Path(args.root).resolve(), args.group, args.su)
    except (OSError, ValueError, RuntimeError) as error:
        print('[확인 필요] 수집 경로 오류: ' + type(error).__name__)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
```
```bash
# 현재 환경의 로컬 파일 확인
python3 check_u06.py
result=$?
printf '종료 코드=%s\n' "$result"

# 별도로 준비한 파일 트리 확인
python3 check_u06.py --root ./sample --group wheel --su /usr/bin/su
```
`--root ./sample`을 지정하면 sample 아래의 etc/passwd, etc/group, etc/pam.d/su, etc/pam.d/su-l, usr/bin/su를 읽는다. 심볼릭 링크도 해석하지만 지정 범위 밖을 가리키면 거부한다. 복사한 파일의 소유권과 모드는 원본과 다를 수 있어 원본 서버의 권한 증거를 대신하지 못한다.

| 종료 코드 | 의미 |
| --- | --- |
| 0 | 정해진 로컬 자료를 읽었으며 스크립트가 검사하는 기본 형식 오류가 없었다. 양호 판정이나 PAM 문법 정상이라는 뜻은 아니다. |
| 2 | 인자 오류, 파일 누락·읽기 실패, 기본 형식 이상 등으로 수집이 불완전하다. 확인 필요 항목을 검토한다. |

취약 판정 코드 1은 사용하지 않는다. su-l 파일이 없어 코드 2가 나와도 그 자체로 취약한 것은 아니다. 반대로 코드 0이어도 PAM 제어 흐름, 모듈 로딩, include 대상, ACL, 중앙 계정과 실제 인증 결과는 별도 확인해야 한다.

## 수집 결과와 실제 차단 결과를 구분한다

시험용 파일에서 admin의 기본 GID를 wheel과 같게 두고, 추가 그룹 목록에는 alice만 적었다. 실행 결과 중 그룹 부분은 다음과 같다.

```text
[그룹] wheel GID=10
[기본 그룹] admin
[추가 그룹] alice
```
admin은 group 파일의 마지막 필드에 없어도 기본 그룹으로 포함됐다. 추가 그룹 목록만 보고 허용 계정이 alice 하나라고 판단하면 안 된다.

su-l 파일에 `auth include su`를 넣으면 다음과 같이 원문을 출력한다.

```text
[PAM 파일] /etc/pam.d/su-l
  1: auth include su
[범위] 로컬 파일 수집; PAM 흐름·모듈 로딩·NSS·ACL은 별도 확인
[판정] 자동 판정하지 않음
```
include 줄을 읽었다는 사실이 포함된 규칙의 실행이나 차단 성공을 뜻하지는 않는다. 파일 누락, 형식 오류, 주석 처리, PAM 옵션, 범위 밖 링크 등 19가지 수집 시험을 확인했으며, 실제 PAM 인증이나 운영 계정 전환은 실행하지 않았다.

## 허용 그룹과 복구 경로를 정한 뒤 변경한다

su가 필요한 계정만 허용 그룹에 포함한다. PAM 방식은 실제 su·su-l 흐름에서 그룹 제한을 거치도록 구성하고, 파일 권한 방식은 소유자·허용 그룹·실행 권한·ACL을 함께 정리한다. 배포판의 설정 관리 도구와 패키지 업데이트가 구성을 바꾸는지도 확인한다.

그룹을 추가할 때 기존 추가 그룹 목록을 통째로 바꾸는 옵션을 사용하면 필요한 서비스 권한을 잃을 수 있다. 변경 전 설정과 복구 경로를 확보하고, 세션과 자동화 작업에 미칠 영향을 검토한다. 새 그룹 자격 증명은 재로그인 등 적용 절차를 거쳐 확인한다.

최종 확인은 승인된 시험 환경에서 허용·비허용 사용자, root·일반 계정 대상, 일반 su·로그인 방식 su를 나눠 수행한다. 비밀번호가 틀려 실패한 결과만으로 그룹 제한이 작동했다고 판단하지 말고, 거부 지점과 로그를 확인한다.

## 참고 자료

- [KISA, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드, U-06](https://www.krcert.or.kr/kr/bbs/view.do?bbsId=B0000127&menuNo=205021&nttId=71928)
- [util-linux, su(1)](https://man7.org/linux/man-pages/man1/su.1.html)
- [Linux-PAM, pam_wheel(8)](https://man7.org/linux/man-pages/man8/pam_wheel.8.html)
- [Linux-PAM, PAM 설정 문법과 파일 위치](https://man7.org/linux/man-pages/man5/pam.conf.5.html)
- [Linux-PAM, pam_rootok(8)](https://www.man7.org/linux/man-pages/man8/pam_rootok.8.html)
- [Linux man-pages, passwd(5)](https://www.man7.org/linux/man-pages/man5/passwd.5.html)
- [shadow-utils, usermod(8)](https://man7.org/linux/man-pages/man8/usermod.8.html)
- [SSSD, Troubleshooting Basics](https://sssd.io/troubleshooting/basics.html)
