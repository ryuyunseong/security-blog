#!/usr/bin/env bash
# 계정명과 비밀번호 필드 원문을 출력하지 않는다.
# shadow 내용은 읽지 않으며 파일과 인증 설정을 변경하지 않는다.
set -u
export LC_ALL=C

if (( $# > 1 )); then
  printf '%s\n' \
    '사용법: bash check_u04_password_file.sh [점검할 etc 디렉터리]'
  exit 2
fi

base=${1:-/etc}
if [[ $base != /* || $base == *[[:cntrl:]]* ||
      /${base#/}/ == */../* || /${base#/}/ == */./* ]]; then
  printf '%s\n' '오류: 점 경로가 없는 절대 경로를 지정한다'
  exit 2
fi
base=${base%/}

for tool in awk stat; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf '%s\n' '오류: awk와 GNU stat이 필요하다'
    exit 2
  fi
done

# 부모 디렉터리도 검사한다. 실행 중 파일 교체는 막지 못한다.
safe_path() {
  local part here='' path=$1
  local -a parts
  IFS=/ read -r -a parts <<< "$path"
  for part in "${parts[@]}"; do
    [[ -z $part ]] && continue
    here+=/$part
    [[ -L $here ]] && return 1
  done
  return 0
}

path=$base/passwd
if ! safe_path "$path" || [[ ! -f $path || ! -r $path ]]; then
  printf '%s\n' \
    '미수집: passwd가 일반 파일이 아니거나 읽기 불가·링크 경로임'
  exit 2
fi

printf '%s\n' '[passwd 비밀번호 필드 유형]'
awk -F: '
  /^[[:space:]]*$/ { next }
  /^[+-]/ { external++; next }
  {
    total++
    if (NF!=7 || $1=="" || $3 !~ /^[0-9]+$/ ||
        $4 !~ /^[0-9]+$/ || $0 ~ /[[:cntrl:]]/) {
      malformed++; next
    }
    if (seen[$1]++) duplicate++
    if ($2=="x") shadow++
    else if ($2=="*" || $2=="!" || $2=="!!") locked++
    else if ($2=="") empty++
    else other++
  }
  END {
    printf "일반 레코드: %d\n",total
    printf "쉐도우 참조 x: %d\n",shadow
    printf "잠금 표지 *, !, !!: %d\n",locked
    printf "빈 비밀번호 필드: %d\n",empty
    printf "기타 값: %d\n",other
    printf "형식 확인 필요: %d\n",malformed
    printf "중복 계정명: %d\n",duplicate
    printf "NIS 호환 표기: %d\n",external
    # 수집 결과와 awk 자체의 오류를 구분하기 위한 내부 코드다.
    if (total==0 || malformed) exit 11
    if (empty || other || duplicate || external) exit 10
  }
' "$path" 2>/dev/null
awk_status=$?
case $awk_status in
  0) status=0 ;;
  10) status=1 ;;
  11) status=2 ;;
  *)
    printf '%s\n' '미수집: passwd 필드 집계 실패'
    status=2
    ;;
esac

printf '\n%s\n' '[shadow 파일 메타데이터]'
path=$base/shadow
if ! safe_path "$path" || [[ ! -f $path ]]; then
  printf '%s\n' \
    '미수집: shadow 없음·일반 파일 아님·링크 경로 또는 접근 불가'
  status=2
elif ! stat --printf='소유 UID=%u, 소유 GID=%g, 모드=%a\n' \
     -- "$path" 2>/dev/null; then
  printf '%s\n' '미수집: shadow 메타데이터 조회 실패'
  status=2
fi

printf '\n%s\n' \
  '최종 판단: 수동 검토 필요' \
  'x와 shadow 파일 존재만으로 계정별 저장 상태를 확정하지 않는다' \
  '0=유형 수집 종료, 1=추가 확인 값 발견, 2=미수집·형식 오류' \
  '종료 코드는 U-04 양호·취약 판정이 아니다'
exit "$status"
