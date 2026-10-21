#!/usr/bin/env bash
# 설정 후보만 수집한다. 인증 시도, 계정 잠금·해제, 설정 변경은 하지 않는다.
# 실행: bash check_u03_lockout.sh
# 복사본: U03_ROOT=/절대경로 bash check_u03_lockout.sh
set -u
export LC_ALL=C
status=0
root=${U03_ROOT:-/}

if [[ $root != /* || $root == *[[:cntrl:]]* ||
      /${root#/}/ == */../* || /${root#/}/ == */./* ]]; then
  printf '%s\n' '오류: U03_ROOT에는 점 경로가 없는 절대 경로를 지정한다'
  exit 2
fi
root=${root%/}
if ! command -v awk >/dev/null 2>&1; then
  printf '%s\n' '오류: awk가 필요하다'
  exit 2
fi

# 부모 디렉터리의 링크도 건너뛴다. 실행 중 경로 교체까지 막지는 못한다.
safe_path() {
  local path=$1 part here=''
  local -a parts
  IFS=/ read -r -a parts <<< "$path"
  for part in "${parts[@]}"; do
    [[ -z $part ]] && continue
    here+=/$part
    [[ -L $here ]] && return 1
  done
  return 0
}

collect() {
  local rel=$1 mode=$2 path=$root$1
  printf '\n[파일] %s\n' "$rel"
  if ! safe_path "$path"; then
    printf '%s\n' '미수집: 심볼릭 링크 대상 수동 확인'
    return
  fi
  if [[ ! -f $path || ! -r $path ]]; then
    printf '%s\n' '미수집: 없음·일반 파일 아님·읽기 불가'
    return
  fi

  awk -v mode="$mode" '
  function numeric(k) {
    return k ~ /^(deny|fail_interval|unlock_time|root_unlock_time)$/
  }
  function flag(k) {
    return k ~ /^(preauth|authfail|authsucc|silent|audit|even_deny_root|local_users_only|no_log_info|nodelay|no_magic_root|reset)$/
  }
  function emit(k,v,n) {
    if (numeric(k)) {
      if (n==2 && v ~ /^[0-9]+$/) printf " %s=%s",k,v
      else if (k=="unlock_time" && n==2 && v=="never")
        printf " %s=never",k
      else printf " %s=[값 형식 확인]",k
    } else if (flag(k)) {
      if (n==1) printf " %s",k
      else printf " %s=[값 형식 확인]",k
    } else if (k ~ /^(conf|dir|admin_group)$/) {
      printf " %s=[지정값 수동 확인]",k
    } else return 0
    return 1
  }
  {
    sub(/#.*/, "")
    sub(/^[ \t]+/, "")
    sub(/[ \t\r]+$/, "")
    if ($0=="") next

    if (mode=="conf") {
      n=split($0,a,/[ \t=]+/)
      k=a[1]
      if (k !~ /^(deny|fail_interval|unlock_time|root_unlock_time|silent|audit|even_deny_root|local_users_only|no_log_info|nodelay|dir|admin_group)$/) next
      raw=$0
      equals=gsub(/=/,"=",raw)
      printf "%d:",NR
      if (equals>1) printf " %s=[값 형식 확인]",k
      else emit(k,a[2],n)
      print ""
      seen++
      if (k=="deny") {
        count++
        value=(n==2 && equals<=1 ? a[2] : "형식오류")
      }
      next
    }

    n=split($0,a,/[ \t]+/)
    if (a[1]=="@include") {
      printf "%d: @include [참조 대상 수동 확인]\n",NR
      seen++
      next
    }
    if (a[1] !~ /^-?(auth|account)$/) next
    seen++
    printf "%d: %s",NR,a[1]
    if ($0 ~ /\\$/) printf " [줄 연결: 수동 확인]"
    i=2
    control=a[i]
    if (control ~ /^\[/) {
      while (i<n && a[i] !~ /\]$/) control=control " " a[++i]
    }
    if (control ~ /^(required|requisite|sufficient|optional|include|substack)$/ ||
        control ~ /^\[[a-zA-Z0-9_= !-]+\]$/) {
      printf " %s",control
    } else printf " [제어문 확인]"
    if (control ~ /^(include|substack)$/) {
      print " [참조 대상 수동 확인]"
      next
    }

    mod=a[++i]
    if (mod ~ /\//) printf " [모듈 경로 지정: 수동 확인]"
    sub(/^.*\//,"",mod)
    if (mod ~ /^pam_(faillock|tally2?|unix|sss|ldap|winbind|deny|permit)\.so$/) {
      printf " %s",mod
    } else printf " [기타/누락 모듈]"

    # 잠금 모듈의 허용한 인수만 표시한다. 다른 모듈의 인수는 출력하지 않는다.
    if (mod ~ /^pam_(faillock|tally2?)\.so$/) {
      omitted=0
      while (++i<=n) {
        m=split(a[i],b,"=")
        if (!emit(b[1],b[2],m)) omitted++
      }
      if (omitted) printf " [기타 옵션 생략: 수동 확인]"
    }
    print ""
  }
  END {
    if (!seen) print "관련 활성 설정 없음: 미설정으로 단정하지 않는다"
    if (mode=="conf") {
      if (count==0) print "임계값 후보: 명시값 없음, 기본값·다른 설정 확인"
      else if (count>1) print "임계값 후보: 중복 설정, 적용값 확인"
      else if (value !~ /^[0-9]+$/) print "임계값 후보: 값 형식 확인"
      else if (value+0==0) print "임계값 후보: 0, 잠금 비활성 여부 확인"
      else if (value+0<=10) print "임계값 후보: 1~10, 실제 적용 경로 확인"
      else print "임계값 후보: 10 초과, 실제 적용값 확인"
    }
  }
  ' "$path" || {
    printf '%s\n' '수집 오류: 해당 파일 수동 확인'
    status=2
  }
}

printf '%s\n' 'U-03 읽기 전용 점검 자료' '파일 표시 순서는 적용 우선순위가 아니다'
collect /etc/security/faillock.conf conf
collect /usr/share/pam/security/faillock.conf conf
for service in sshd login sudo su system-auth password-auth common-auth common-account; do
  collect "/etc/pam.d/$service" pam
done
# 생성 파일을 별도로 제시할 뿐 서비스 연결 여부를 판정하지는 않는다.
for service in system-auth password-auth; do
  collect "/etc/authselect/$service" pam
done
printf '\n%s\n' \
  '최종 판단: 수동 검토 필요' \
  '서비스 연결·분기·모듈 설치·인수 우선값·외부 인증·root 예외를 확인한다' \
  '종료 코드 0은 절차 종료이며 양호 판정이나 완전한 수집을 뜻하지 않는다'
exit "$status"
