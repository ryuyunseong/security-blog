---
title: "U-01: root 계정 원격 접속 제한"
description: "OpenSSH의 유효 설정과 접속 조건을 확인해 root 원격 로그인 제한을 점검합니다."
date: "2026-10-06T21:54:44+09:00"
updated: "2026-10-17T18:17:24+09:00"
category: "unix"
tags: ["주통기", "U-01", "SSH"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 1
---

`PermitRootLogin no`가 적혀 있어도 `Match` 조건에 따라 root 접속이 허용될 수 있습니다. U-01의 Linux OpenSSH 점검에는 설정 파일에서 찾은 값보다 해당 접속 조건에서 해석된 값이 필요합니다.

아래 예제에서는 클라이언트 주소만 바꿔 유효 설정을 비교합니다. 설정을 해석하는 명령과 서비스 반영 여부, 실제 로그인 시험이 각각 어디까지 보여 주는지도 짚습니다.

## 비밀번호를 막는 것과 root 접속을 막는 것

`PermitRootLogin`의 값은 다음처럼 구분합니다.

| 값 | 의미 |
| --- | --- |
| `no` | SSH를 통한 root 로그인 차단 |
| `yes` | 다른 인증·접근통제 조건을 충족하면 root 로그인 허용 |
| `prohibit-password` / `without-password` | root의 비밀번호·keyboard-interactive 인증 차단. 공개키 등 다른 인증은 가능 |
| `forced-commands-only` | `authorized_keys`의 `command` 옵션으로 실행 명령을 제한한 root 공개키 인증 허용 |

기본값은 `prohibit-password`입니다. 설정이 없거나 주석 처리돼 있어도 root 접속이 완전히 차단된 상태로 볼 수는 없습니다.

예를 들어 아래 설정에서는 기본값이 `no`지만, root에 적용되는 값은 `yes`입니다.

```text
PermitRootLogin no

Match User root
    PermitRootLogin yes
```
`Include`의 설정 순서도 확인해야 합니다. 같은 항목은 일반적으로 먼저 읽은 값이 사용되고, 해당 연결에 일치하는 `Match` 설정은 전역 설정을 덮어쓸 수 있습니다.

[[diagram]]

## 접속 조건을 넣어 확인하기

스크립트는 지정한 접속 조건 하나를 `sshd -T -C`로 해석합니다. Linux의 Bash·`awk`와 이 옵션을 지원하는 OpenSSH가 필요하며, 설정과 호스트 키를 읽을 root 또는 `sudo` 권한으로 실행합니다. 서비스 재시작이나 원격 로그인 없이 설정값만 수집합니다.

`addr`는 클라이언트 IP, `host`는 서버가 판단하는 클라이언트 호스트명, `laddr`와 `lport`는 서버가 연결을 받는 IP와 포트입니다. 예제 주소와 이름을 실제 점검할 경로에 맞게 바꾸고, `user=root`는 유지합니다. `Match RDomain`을 사용하는 환경은 `rdomain`도 지정해야 합니다.

```bash
#!/usr/bin/env bash
set -uo pipefail

sshd=/usr/sbin/sshd
config=/etc/ssh/sshd_config
context='user=root,addr=192.0.2.10,host=admin.example.invalid,laddr=192.0.2.20,lport=22'

printf '설정 파일: %s\n접속 조건: %s\n' "$config" "$context"

if ! output=$("$sshd" -T -f "$config" -C "$context" 2>&1); then
    printf '[점검 불가] 설정 검사 실패\n%s\n' "$output" >&2
    exit 2
fi

value=$(awk '$1 == "permitrootlogin" && NF == 2 {print $2}' <<< "$output")

case "$value" in
    no)
        printf '[SSH 차단 확인] 지정한 조건에서 PermitRootLogin=no\n'
        exit 0
        ;;
    yes|prohibit-password|without-password|forced-commands-only)
        printf '[추가 검토 필요] PermitRootLogin=%s\n' "$value"
        exit 1
        ;;
    *)
        printf '[점검 불가] PermitRootLogin 결과를 해석할 수 없습니다\n' >&2
        exit 2
        ;;
esac
```
`check_u01_ssh.sh`로 저장한 뒤 실행합니다.

```bash
sudo bash check_u01_ssh.sh
```
`no`가 나오면 입력한 조건에서는 root 로그인이 차단됩니다. 그 외 값은 `AllowUsers`, `DenyUsers`, 인증 방식 등 다른 제한까지 검토해야 합니다. 명령 실행 실패는 취약 판정이 아니라 점검 불가로 남깁니다.

이 결과는 설정 파일을 새로 읽어 계산한 값입니다. 실행 중인 서비스에 변경 사항이 반영됐는지, 다른 설정 파일이나 명령행 옵션을 사용하는지는 별도로 확인해야 합니다. 관리망·VPN 등 접속 경로가 여러 개라면 조건을 바꿔 다시 점검합니다. SSH 외에 Telnet 등 원격 접속 경로도 살펴본 뒤 U-01 전체를 판단합니다.

임시 설정에서 `192.0.2.11`을 클라이언트 주소로 넣자 `permitrootlogin no`가 나왔습니다.

[[run:1]]

주소를 `192.0.2.10`으로 바꾸자 `Match` 조건이 적용돼 값이 `yes`로 바뀌었습니다.

[[run:2]]

임시 설정을 해석한 결과이며 실제 원격 로그인을 시도한 기록은 아닙니다.

## 설정을 바꾸기 전에

root 직접 접속을 차단하려면 적용 대상 설정과 `Match` 예외를 정리해 `PermitRootLogin no`가 적용되도록 합니다. 먼저 일반 관리 계정의 로그인과 필요한 `sudo` 권한을 확인하고, root 접속을 사용하는 백업·배포 작업의 영향도 살펴봅니다.

기본 설정 파일을 사용하는 환경에서는 다음 명령으로 문법과 호스트 키를 검사합니다.

```bash
sudo /usr/sbin/sshd -t -f /etc/ssh/sshd_config
```
검사가 성공하면 변경 절차에 따라 설정을 반영합니다. 기존 관리 세션은 유지한 채 새 세션으로 정상 접속을 확인하는 편이 안전합니다. 로그인 실패 한 번만으로 root 차단을 판단하면 잘못된 인증정보나 네트워크 차단을 설정의 효과로 오인할 수 있습니다.

## 참고 자료

- [KISA 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.krcert.or.kr/kr/bbs/view.do?bbsId=B0000127&menuNo=205021&nttId=71928)
- [OpenSSH 서버 설정 매뉴얼: sshd_config(5)](https://man.openbsd.org/sshd_config)
- [OpenSSH 서버 실행 옵션: sshd(8)](https://man.openbsd.org/sshd)
