#!/usr/bin/env bash
# U-02 증거 수집 전용. 설정 변경·비밀번호/해시 조회·자동 양호 판정 없음.
# 실행: bash check_u02_policy.sh  (시험용 루트: U02_ROOT=/absolute/fixture)
set -u
export LC_ALL=C
shopt -s nullglob dotglob
status=0
if ! command -v awk >/dev/null 2>&1; then
  printf '%s\n' '오류: awk 명령이 필요합니다' '수동 검토 필요'
  exit 2
fi
root=${U02_ROOT:-/}
if [[ $root != /* || $root == *[[:cntrl:]]* || /${root#/}/ == */../* || /${root#/}/ == */./* ]]; then
  printf '%s\n' '오류: U02_ROOT는 점 경로가 없는 절대 경로여야 합니다' '수동 검토 필요'
  exit 2
fi
root=${root%/}
# 모든 경로 구성요소의 링크를 거부. 실행 중 경로가 바뀌는 경쟁 상태는 방어하지 않음.
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
collect() {
  local rel=$1 mode=$2 path=$root$1
  printf '\n[파일] %q\n' "$rel"
  if ! safe_path "$path"; then printf '%s\n' '건너뜀: 심볼릭 링크 포함'; return; fi
  if [[ ! -f $path || ! -r $path ]]; then printf '%s\n' '건너뜀: 없음/일반 파일 아님/읽기 불가'; return; fi
  awk -v mode="$mode" '
  function numeric(k) {
    return k ~ /^(minlen|dcredit|ucredit|lcredit|ocredit|minclass|difok|maxrepeat|maxclassrepeat|dictcheck|usercheck|gecoscheck|usersubstr|enforcing|retry|remember)$/
  }
  function flag(k) { return k ~ /^(enforce_for_root|local_users_only|use_authtok|try_first_pass|use_first_pass|nullok|obscure|yescrypt|sha512)$/ }
  function emit(k,v,n) {
    if (numeric(k) || k ~ /^PASS_(MIN|MAX)_DAYS$/) {
      if (n == 2 && v ~ /^-?[0-9]+$/) printf " %s=%s", k,v
      else printf " %s=[값 형식 수동 검토]", k
    } else if (flag(k)) {
      if (n == 1) printf " %s", k
      else printf " %s=[값 포함: 수동 검토]", k
    } else if (k ~ /^(conf|file|dictpath)$/) printf " %s=[지정 경로: 미추적, 수동 검토]", k
    else return 0
    return 1
  }
  {
    sub(/#.*/, ""); sub(/^[ \t]+/, ""); sub(/[ \t]+$/, "")
    if ($0 == "") next
    if (mode != "pam") {
      n=split($0,a,/[ \t=]+/); k=a[1]
      if (mode == "age" && k !~ /^PASS_(MIN|MAX)_DAYS$/) next
      if (mode == "quality" && !((numeric(k) && k != "remember") || k ~ /^(enforce_for_root|local_users_only|dictpath)$/)) next
      if (mode == "history" && k !~ /^(remember|retry|enforce_for_root|file)$/) next
      printf "%d:", NR; emit(k,a[2],n); print ""; seen++; next
    }
    n=split($0,a,/[ \t]+/)
    if (a[1] == "@include") {
      printf "%d: @include [대상 미추적: 수동 검토]\n", NR; seen++; next
    }
    if (a[1] !~ /^-?password$/) next
    seen++; printf "%d: %s", NR,a[1]
    if ($0 ~ /\\$/) printf " [줄 연결: 수동 검토]"
    i=2; control=a[i]
    if (control ~ /^\[/) while (i<n && a[i] !~ /\]$/) control=control " " a[++i]
    if (control ~ /^(required|requisite|sufficient|optional|include|substack)$/ || control ~ /^\[[a-zA-Z0-9_= !-]+\]$/)
      printf " %s", control
    else printf " [제어문 수동 검토]"
    if (control ~ /^(include|substack)$/) { print " [대상 미추적: 수동 검토]"; next }
    mod=a[++i]; if (mod ~ /\//) printf " [모듈 경로 지정: 수동 검토]"
    sub(/^.*\//,"",mod)
    if (mod ~ /^pam_(pwquality|pwhistory|unix|cracklib|sss|ldap|winbind|deny|permit|exec)\.so$/) printf " %s",mod
    else printf " [기타/누락 모듈: 수동 검토]"
    omitted=0
    while (++i<=n) {
      m=split(a[i],b,"=")
      if (!emit(b[1],b[2],m)) omitted++
    }
    if (omitted) printf " [기타 옵션 %d개 생략: 수동 검토]",omitted
    print ""
  }
  END { if (!seen) print "해당 항목 없음: 기본값·다른 경로 수동 확인" }
  ' "$path" || { printf '%s\n' '읽기/파싱 오류: 수동 검토'; status=2; }
}
printf '%s\n' 'U-02 읽기 전용 증거 수집 (파일 표시 순서는 적용 우선순위가 아님)'
collect /etc/login.defs age
collect /etc/security/pwquality.conf quality
dir=$root/etc/security/pwquality.conf.d
if ! safe_path "$dir"; then
  printf '\n%s\n' '[pwquality.conf.d] 심볼릭 링크 포함: 건너뜀'
elif [[ -d $dir && -r $dir && -x $dir ]]; then
  files=("$dir"/*.conf)
  ((${#files[@]})) || printf '\n%s\n' '[pwquality.conf.d] .conf 파일 없음'
  for f in "${files[@]}"; do collect "${f#"$root"}" quality; done
else
  printf '\n%s\n' '[pwquality.conf.d] 없음/디렉터리 아님/접근 불가'
fi
collect /etc/security/pwhistory.conf history
for service in passwd common-password system-auth password-auth; do collect "/etc/pam.d/$service" pam; done
printf '\n%s\n' \
  '이 출력은 설정 후보이며 실제 유효값·모듈 설치·PAM 실행 경로를 판정하지 않습니다' \
  '기본값/우선순위/include/사용자 지정 경로/외부 인증/기존 계정 만료 정책을 별도 확인하세요' \
  '수동 검토 필요'
exit "$status"
