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
