---
title: "U-01: root 계정 원격 접속 제한"
description: "OpenSSH 설정과 접속 조건에 따라 root 원격 로그인이 허용되는지 살펴봅니다. 설정 파일에 적힌 값과 실제 적용 값의 차이를 짚습니다."
date: "2026-10-06T21:54:44+09:00"
updated: "2026-10-22"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-01", "SSH"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 1
---

`PermitRootLogin no`가 있어도 접속 조건과 일치하는 `Match` 블록에서 root 로그인을 허용할 수 있습니다. Linux OpenSSH의 U-01 점검에서는 파일의 한 줄과 함께 실제 접속 조건에서 해석되는 값을 봐야 합니다.

클라이언트 주소만 바꿔 유효 설정이 어떻게 달라지는지 비교합니다. 설정 해석 결과가 서비스 반영이나 실제 로그인 시험과 어떤 차이가 있는지도 살펴봅니다.

## 비밀번호를 막는 것과 root 접속을 막는 것

`PermitRootLogin`의 값은 다음처럼 구분합니다.

| 값 | 의미 |
| --- | --- |
| `no` | SSH를 통한 root 로그인 차단 |
| `yes` | 다른 인증·접근통제 조건을 충족하면 root 로그인 허용 |
| `prohibit-password` / `without-password` | root의 비밀번호·keyboard-interactive 인증 차단. 공개키 등 다른 인증은 가능 |
| `forced-commands-only` | `authorized_keys`의 `command` 옵션으로 실행 명령을 제한한 root 공개키 인증 허용 |

기본값은 `prohibit-password`입니다. 설정이 없거나 주석 처리돼 있어도 root 접속이 완전히 차단된 상태로 볼 수는 없습니다.

예를 들어 아래 설정에서는 기본값이 `no`지만 root에 적용되는 값은 `yes`입니다.

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

[[download]]

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
ZIP의 `check_u01_ssh.sh`가 있는 폴더에서 아래 명령을 실행합니다. 이 수집기는 `/etc/ssh/sshd_config`를 읽으므로, 뒤의 가상 설정 실습과 구분합니다.

```bash
sudo bash check_u01_ssh.sh
```
`no`가 나오면 입력한 조건에서는 root 로그인이 차단됩니다. 그 외 값은 `AllowUsers`, `DenyUsers`, 인증 방식 등 다른 제한까지 검토해야 합니다. 명령 실행 실패는 취약 판정이 아니라 점검 불가로 남깁니다.

`set -u`는 정의하지 않은 변수 사용을, `pipefail`은 파이프라인 앞쪽 명령의 실패를 잡습니다. `if ! output=...` 분기에서는 `sshd`가 실패한 이유를 출력하고 종료 코드 `2`를 반환합니다. 설정 해석에 성공한 경우에만 `awk`로 `permitrootlogin`을 골라 `no`는 `0`, 추가 검토가 필요한 값은 `1`로 구분합니다.

이 결과는 설정 파일을 새로 읽어 계산한 값입니다. 실행 중인 서비스에 변경 사항이 반영됐는지, 다른 설정 파일이나 명령행 옵션을 사용하는지는 별도로 확인해야 합니다. 관리망·VPN 등 접속 경로가 여러 개라면 조건을 바꿔 다시 점검합니다. SSH 외에 Telnet 등 원격 접속 경로도 살펴본 뒤 U-01 전체를 판단합니다.

## 설정값 대신 오류가 나올 때

`./sshd_config: No such file or directory`는 현재 작업 폴더에 예제 설정 파일이 없다는 뜻입니다. 아래 실행 기록의 `./sshd_config`는 수집기에 지정한 `/etc/ssh/sshd_config`와 다른 파일입니다. 임시 파일 실습의 준비 코드부터 실행하면 해당 폴더와 설정이 함께 만들어집니다.

`Missing privilege separation directory: /run/sshd`는 해당 OpenSSH가 권한 분리에 사용하는 디렉터리를 찾지 못했다는 뜻입니다. root로 실행하는 검사도 이 디렉터리를 요구할 수 있으므로 존재 여부와 소유자·권한을 살핍니다.

OpenSSH 9.6p1의 `sshd -T`와 `sshd -t`는 설정 검사 중에도 권한 분리용 디렉터리를 검사합니다. 일반적인 서비스 시작 과정 없이 `sshd`를 직접 실행하는 WSL·컨테이너에서는 `/run/sshd`가 준비되지 않았을 수 있습니다. 오류가 나온 상태에서는 `PermitRootLogin`의 값을 얻지 못했으므로 양호·취약으로 분류하지 않습니다.

학습용 Ubuntu·WSL에서 `/run/sshd`가 없는 것을 확인했다면 다음 명령으로 준비할 수 있습니다. 이미 있는 디렉터리의 권한을 덮어쓰는 용도로 사용하지 않습니다.

```bash
sudo install -d -o root -g root -m 0755 /run/sshd
```

이 명령은 디렉터리만 만들며 SSH 서비스를 시작하지 않습니다. `/run`은 재부팅 때 비워질 수 있으므로, 운영 서버에서 문제가 반복되면 배포판의 서비스·런타임 디렉터리 생성 절차를 조사합니다. 권한 분리 기능을 끄거나 쓰기 권한을 넓혀 해결하지 않습니다.

## 임시 파일로 Match 재현하기

아래 코드를 한 번에 Bash에서 실행합니다. OpenSSH 서버 프로그램과 `ssh-keygen`이 설치된 Linux 환경이 필요합니다. 별도의 일회용 호스트 키와 설정을 만들고, `/etc/ssh/sshd_config`를 바꾸거나 데몬을 시작하지 않은 채 두 주소를 차례로 대입합니다. `Match`에서 root 접속을 허용하는 설정은 이 비교 실습에만 사용합니다.

```bash
(
set -euo pipefail
umask 077
LAB=$(mktemp -d)
trap 'rm -rf -- "$LAB"' EXIT

ssh-keygen -q -t ed25519 -N '' -f "$LAB/host_key"
cat > "$LAB/sshd_config" <<EOF
HostKey $LAB/host_key
UsePAM no
PermitRootLogin no
Match Address 192.0.2.10
    PermitRootLogin yes
EOF

cd "$LAB"
for address in 192.0.2.11 192.0.2.10; do
    /usr/sbin/sshd -T -f ./sshd_config \
        -C "user=root,addr=$address,host=admin.example.invalid,laddr=192.0.2.20,lport=22" \
        | awk '$1 == "permitrootlogin"'
done
)
```

ZIP의 `u01_match_lab.sh`에는 위 준비 코드가 들어 있습니다. 저장한 폴더에서 `bash u01_match_lab.sh`로 실행하며, 두 주소의 결과가 위에서 아래 순서로 나옵니다. `/run/sshd` 오류가 발생하면 앞 절의 원인과 준비 조건을 먼저 살펴봅니다.

`mktemp -d`로 만든 폴더 안에서 명령을 실행하므로 `./sshd_config`가 가리키는 파일이 분명해집니다. `HostKey`도 그 폴더의 키를 가리키며 소괄호로 묶은 실습이 끝나면 `trap`이 임시 파일과 키를 지웁니다. 예제의 IP와 호스트명은 조건 비교에 쓰는 문자열이며 해당 주소로 접속하지 않습니다.

| 코드에서 바뀌는 부분 | 역할 |
| --- | --- |
| `ssh-keygen`과 `HostKey` | 임시 폴더에 새 키를 만들고 이 설정 검사에만 사용 |
| `-f ./sshd_config` | `cd "$LAB"` 이후 생성한 파일을 읽음 |
| 반복문의 `address`와 `-C addr=...` | 설정 파일은 유지하고 접속 주소 조건만 바꿈 |
| `awk`의 필드 선택 | 전체 유효 설정 중 `permitrootlogin` 한 줄만 표시 |

두 실행 기록의 종료 코드가 모두 `0`인 것은 `sshd`의 설정 해석과 결과 추출에 성공했다는 뜻입니다. 두 번째 출력의 `yes`는 root 접속을 허용하는 설정값이므로 차단 성공으로 읽으면 안 됩니다.

앞의 수집기는 같은 값을 만나면 추가 검토를 뜻하는 `1`을 반환하지만, 여기서는 그 수집기 대신 설정 해석 명령을 직접 실행했습니다.

첫 번째 주소인 `192.0.2.11`에서는 `Match Address 192.0.2.10`에 일치하지 않아 `permitrootlogin no`가 나왔습니다.

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
문법 검사를 통과하면 변경 절차에 따라 설정을 반영하고, 기존 관리 세션을 유지한 채 새 세션으로 접속을 시험합니다. 로그인에 한 번 실패했다는 사실만으로 root 차단이 적용됐다고 판단하지 않습니다. 잘못된 인증정보나 네트워크 차단 때문일 수도 있습니다.

## 참고 자료

- [KISA 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.krcert.or.kr/kr/bbs/view.do?bbsId=B0000127&menuNo=205021&nttId=71928)
- [OpenSSH 서버 설정 매뉴얼: sshd_config(5)](https://man.openbsd.org/sshd_config)
- [OpenSSH 서버 실행 옵션: sshd(8)](https://man.openbsd.org/sshd)
- [OpenSSH Portable 9.6p1: 권한 분리 디렉터리 검사 구현](https://github.com/openssh/openssh-portable/blob/V_9_6_P1/sshd.c#L1875-L1898)
