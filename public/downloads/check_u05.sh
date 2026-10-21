#!/usr/bin/env bash
# 계정 정보만 읽는다. 비밀번호 필드와 전체 레코드는 출력하지 않는다.
set -u
export LC_ALL=C

mode=file
file=/etc/passwd
case $# in
  0) ;;
  1) [[ $1 == --nss ]] && mode=nss || mode=usage ;;
  2) [[ $1 == --file ]] && file=$2 || mode=usage ;;
  *) mode=usage ;;
esac

if [[ $mode == usage ]]; then
  printf '%s\n' '사용법: bash check_u05.sh [--file passwd파일 | --nss]'
  exit 2
fi
if ! command -v awk >/dev/null 2>&1; then
  printf '%s\n' '[확인 필요] awk를 사용할 수 없음'
  exit 2
fi

check_records() {
  awk -F: -v source="$mode" '
  function review(reason) {
    printf "[확인 필요] %d행: %s\n", NR, reason
    uncertain=1
  }
  {
    # 빈 줄이나 NIS 호환 지시문은 일반 계정 레코드로 판단하지 않는다.
    if ($0 == "") { review("빈 레코드"); next }
    if ($1 ~ /^[+-]/) { review("NIS 호환 지시문"); next }
    if (NF != 7 || $1 == "" || $1 ~ /[[:cntrl:][:space:]]/ ||
        $3 !~ /^[0-9]+$/ || $4 !~ /^[0-9]+$/) {
      review("계정 레코드 형식 이상"); next
    }
    if (++seen[$1] > 1) review("동일한 계정 이름이 반복됨")
    if ($1 == "root") {
      roots++
      if ($3 !~ /^0+$/) review("root 계정의 UID가 0이 아님")
    }
    # 숫자 변환 대신 0으로만 구성됐는지 검사한다.
    if ($3 ~ /^0+$/ && $1 != "root") {
      printf "[취약] 계정=%s UID=0\n", $1
      found=1
    }
  }
  END {
    if (roots != 1) {
      print "[확인 필요] root 레코드가 정확히 하나인지 확인"
      uncertain=1
    }
    if (source == "nss") {
      print "[범위] NSS 열거 응답; 중앙 계정 전체 목록과 대조 필요"
      uncertain=1
    } else {
      print "[범위] 지정한 passwd 파일의 현재 내용"
    }
    if (found) exit 10
    if (uncertain) exit 20
    print "[양호] 검사한 파일에서 root 이외의 UID=0 계정 없음"
  }' 2>/dev/null
}

if [[ $mode == file ]]; then
  if [[ ! -f $file || ! -r $file ]]; then
    printf '%s\n' '[확인 필요] 읽을 수 있는 일반 파일이 아님'
    exit 2
  fi
  check_records < "$file"
  rc=$?
else
  # NSS 조회 실패를 빈 목록이나 양호 결과로 바꾸지 않는다.
  if ! command -v getent >/dev/null 2>&1 ||
     ! command -v timeout >/dev/null 2>&1; then
    printf '%s\n' '[확인 필요] getent와 GNU timeout이 필요함'
    exit 2
  fi
  records=$(timeout -k 2s 15s getent passwd 2>/dev/null)
  rc=$?
  if [[ $rc != 0 ]]; then
    printf '[확인 필요] NSS 조회 실패 또는 시간 초과 (종료 코드=%s)\n' "$rc"
    exit 2
  fi
  check_records <<< "$records"
  rc=$?
  unset records
fi

# 판정용 내부 코드와 실행 오류를 구분한다.
case $rc in
  0) exit 0 ;;
  10) exit 1 ;;
  20) exit 2 ;;
  *) printf '%s\n' '[확인 필요] 파일 읽기 또는 분석 도구 실행 오류'; exit 2 ;;
esac
