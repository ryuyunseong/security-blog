#!/usr/bin/env bash
set -euo pipefail

command -v script >/dev/null || { echo 'script 명령이 필요합니다' >&2; exit 2; }
result=$(sleep 4 | script -q -e -c \
  'env -i HOME=/nonexistent HISTFILE=/dev/null TERM=dumb TMOUT=2 bash --noprofile --norc -i' /dev/null)
case "$result" in
  *'timed out waiting for input: auto-logout'*) ;;
  *) echo '예상한 유휴 종료 메시지를 찾지 못했습니다' >&2; exit 1 ;;
esac
printf '%s\n' "$result" | tr -d '\a\r'
printf '%s\n' '확인: 입력 없는 프롬프트에서 셸 자동 종료'
