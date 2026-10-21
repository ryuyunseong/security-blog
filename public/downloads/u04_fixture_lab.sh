#!/usr/bin/env bash
# 실제 계정 파일 대신 /tmp의 가상 자료만 만든다.
set -u
export LC_ALL=C
if (( $# > 1 )); then
  printf '%s\n' '사용법: bash u04_fixture_lab.sh [수집기 경로]'
  exit 2
fi
collector=$(realpath -e -- "${1:-./check_u04_password_file.sh}") || exit 2
if [[ ! -f $collector || ! -r $collector ]]; then
  printf '%s\n' '오류: 읽을 수 있는 수집기 파일이 필요하다'
  exit 2
fi
LAB=$(mktemp -d /tmp/u04-password-file.XXXXXX) || exit 2
cleanup() {
  local status=$?
  trap - EXIT
  if [[ $LAB == /tmp/u04-password-file.* && -d $LAB && ! -L $LAB && $(realpath -- "$LAB") == "$LAB" ]]; then
    if rm -r -- "$LAB"; then
      printf '\n%s\n' '실습 파일 정리: 완료'
    else
      status=2
    fi
  else
    printf '%s\n' '정리 중단: 생성한 임시 경로인지 확인할 수 없음' >&2
    status=2
  fi
  exit "$status"
}
trap cleanup EXIT
mkdir -p "$LAB/fixture/etc" || exit 2
printf '%s\n' \
  'lab01:x:1001:1001::/home/lab01:/bin/bash' \
  'lab02:x:1002:1002::/home/lab02:/bin/bash' > "$LAB/fixture/etc/passwd"
: > "$LAB/fixture/etc/shadow"
chmod 600 "$LAB/fixture/etc/shadow" || exit 2
run_case() {
  local title=$1 expected=$2 target=$3 status
  printf '\n%s\n' "$title"
  bash "$collector" "$target"
  status=$?
  printf '수집기 종료 코드: %d\n' "$status"
  if (( status != expected )); then
    printf '오류: 기대한 종료 코드는 %d\n' "$expected" >&2
    return 2
  fi
}
run_case '[경우 1: x 두 개와 빈 shadow]' 0 "$LAB/fixture/etc" || exit 2
printf '%s\n' \
  'lab01:x:1001:1001::/home/lab01:/bin/bash' \
  'lab02:!:1002:1002::/home/lab02:/bin/bash' \
  'lab03::1003:1003::/home/lab03:/bin/bash' \
  'lab04:TEST_ONLY:1004:1004::/home/lab04:/bin/bash' > "$LAB/fixture/etc/passwd"
run_case '[경우 2: 네 가지 필드 유형]' 1 "$LAB/fixture/etc" || exit 2
run_case '[경우 3: 준비하지 않은 경로]' 2 "$LAB/not-created/etc" || exit 2
printf '\n%s\n' '세 경우의 종료 코드 비교: 통과'
