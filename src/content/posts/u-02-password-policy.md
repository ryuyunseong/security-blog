---
title: "U-02: 비밀번호 관리정책 설정"
description: "비밀번호 복잡성·사용 기간·재사용 제한을 PAM 적용 경로와 함께 확인합니다."
date: "2026-10-07T21:27:23+09:00"
updated: "2026-10-22"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-02", "PAM"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 2
---

설정한 최소 길이보다 짧은 비밀번호가 통과한다면 비밀번호 변경에 사용되는 PAM 경로를 살펴본다. 복잡성 검사를 건너뛰거나 설정 파일보다 우선하는 모듈 인수가 적용됐을 수 있다.

U-02의 점검 대상은 복잡성, 사용 기간, 재사용 제한이다. 파일과 PAM 인수를 수집해 적용 경로를 추적하고, 기존 계정의 만료 정보는 `chage`로 조회한다.

## 비밀번호 정책에서 확인할 값

KISA 가이드의 Linux 설정 예시는 다음과 같다. 기관에서 더 엄격한 정책을 정했다면 그 기준도 함께 확인한다.

| 항목 | 설정 예시 | 확인할 내용 |
| --- | --- | --- |
| 최소 길이 | `minlen = 8` | 8자 이상 |
| 문자 조합 | 네 가지 `credit`을 각각 `-1`로 설정 | 대문자·소문자·숫자·기타 문자 각각 1자 이상 |
| 최소 사용 기간 | `PASS_MIN_DAYS 1` | 변경 후 다시 바꾸기까지 최소 1일 |
| 최대 사용 기간 | `PASS_MAX_DAYS 90` | 최대 90일 |
| 재사용 제한 | `remember = 4` | 최근 비밀번호 4개 기억 |
| root 적용 | `enforce_for_root` | 복잡성·이력 모듈 각각 확인 |

각 값은 서로 다른 파일에서 관리한다. 아래는 파일별 비교 예시이며, 복잡성과 이력 설정은 해당 PAM 모듈이 호출돼야 적용된다.

```text
# /etc/login.defs: 신규 계정의 기본값
PASS_MIN_DAYS 1
PASS_MAX_DAYS 90

# /etc/security/pwquality.conf: 복잡성
minlen = 8
dcredit = -1
ucredit = -1
lcredit = -1
ocredit = -1
enforce_for_root

# /etc/security/pwhistory.conf: 재사용 제한
remember = 4
enforce_for_root
```
`dcredit = -1`은 숫자를 최소 1자 요구한다는 뜻이다. `ucredit`, `lcredit`, `ocredit`은 각각 대문자, 소문자, 기타 문자에 해당한다. 양수는 길이 계산에 더하는 점수이므로 최소 개수와 구분해야 한다.

## 설정값과 PAM 적용 경로 함께 보기

복잡성은 보통 `pam_pwquality.so`, 재사용 제한은 `pam_pwhistory.so`가 처리한다. 먼저 비밀번호 변경 서비스의 PAM 파일인 `/etc/pam.d/passwd`에서 시작해 `include`, `substack`, `@include`가 불러오는 파일을 따라간다. Debian 계열의 `common-password`, Red Hat 계열의 `system-auth`와 `password-auth`가 대표적이다.

두 검사 모듈이 `pam_unix.so`보다 앞에 있는지, 실패를 무시하거나 검사를 건너뛰는 제어 조건이 없는지 확인한다. 뒤따르는 모듈의 `use_authtok`은 앞서 받은 새 비밀번호를 이어서 사용하게 한다. 모듈 순서와 함께 검사한 비밀번호가 그대로 저장되는지도 봐야 한다.

libpwquality는 `pwquality.conf.d/*.conf`를 ASCII 정렬 순서로 읽은 뒤 `pwquality.conf`를 읽는다. 뒤에 읽은 설정이 앞의 값을 덮어쓰며, PAM 모듈 인수는 설정 파일보다 우선한다. 예를 들어 파일에 `minlen = 14`가 있어도 PAM에 `minlen=8`이 지정됐다면 해당 호출에는 8이 적용된다.

`enforcing=0`이면 복잡성 검사 실패가 경고로 끝날 수 있다. root에 대한 `enforce_for_root`도 복잡성과 이력 모듈 각각 확인한다. 옵션이 없으면 설치된 버전의 기본값을 확인하고, `conf=`로 별도 파일을 지정했다면 그 파일도 점검한다.

[[diagram]]

## 기존 계정의 변경 주기 확인하기

`login.defs`의 사용 기간은 계정 생성 시 사용하는 기본값이다. 파일을 수정해도 기존 계정에는 자동으로 반영되지 않는다. 기존 로컬 계정은 조회 권한이 있는 세션에서 다음과 같이 확인한다.

```bash
# 소문자 -l은 조회 옵션이다.
chage -l root
```
root 대신 점검 대상 계정명을 넣고 최소·최대 변경 간격과 비밀번호 만료 정보를 확인한다. 계정 자체의 만료일과 비밀번호 만료일은 서로 다른 항목이다.

`chage`는 로컬 shadow 정보를 보여준다. LDAP나 Active Directory 계정은 중앙 인증 시스템의 정책을 따로 확인한다. 점검 기록에 비밀번호나 해시, 비밀번호 이력 파일의 내용은 담지 않는다.

## 읽기 전용 스크립트로 설정 수집하기

아래 코드를 `check_u02_policy.sh`로 저장한다. Bash와 `awk`를 사용하며, 정책 설정과 주요 PAM 파일에서 확인할 항목을 줄 번호와 함께 출력한다. 비밀번호나 설정을 변경하지 않는다.

허용한 항목만 표시하고, 비밀번호·해시·이력 파일은 읽지 않는다. 포함 파일과 사용자 지정 경로는 자동으로 따라가지 않으며, 파일이나 상위 디렉터리에 심볼릭 링크가 있으면 건너뛴다. `authselect`가 만든 정상 링크, 다른 PAM 서비스와 공급업체 기본 경로는 별도로 확인해야 한다. 실행 중 파일 교체까지 막지는 못하므로 설정 배포가 진행 중이지 않을 때 실행한다.

[[download]]

```bash
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
```
저장한 파일은 다음 명령으로 실행한다.

```bash
bash check_u02_policy.sh
```
종료 코드는 정책의 적합 여부가 아니라 수집 상태를 나타낸다. 건너뛴 파일이 있어도 절차를 마치면 `0`이며, `awk` 누락·읽기·파싱 오류나 잘못된 시험 경로는 `2`다. 따라서 `0`을 받았더라도 출력에 누락된 파일이 있는지 읽어야 한다.

가상 자료로 실행하려면 ZIP을 풀어 `check_u02_policy.sh`와 `u02_fixture_lab.py`를 같은 폴더에 두고 `python3 -I -B u02_fixture_lab.py ./check_u02_policy.sh`로 실행한다. Linux의 Python 3, Bash, awk가 필요하며 관리자 권한은 쓰지 않는다.

준비 파일은 `/tmp` 아래에 새 폴더를 만든다. 그 안에 `etc/login.defs`, `etc/security/pwquality.conf`, `etc/security/pwhistory.conf`, `etc/pam.d/passwd`와 `common-password`를 작성하고, 그 폴더의 절대 경로를 `U02_ROOT`로 전달한다. 직접 만드는 경우에도 `/absolute/fixture`라는 이름의 폴더가 미리 있다고 가정하지 말고 이 구조를 먼저 준비한다. 실행이 끝나거나 Python 예외가 발생하면 `TemporaryDirectory`가 만든 자료를 정리한다.

수집기의 `safe_path()`는 경로를 구성하는 각 디렉터리의 링크를 검사한다. 가상 실습에서는 `root`에 `U02_ROOT`를 받은 뒤 `/etc/security/pwquality.conf` 같은 조사 경로를 붙이므로 운영 파일 대신 임시 트리 안의 파일을 읽는다. `collect()`가 넘기는 `quality`·`history`·`pam` 모드에 따라 awk에서 남길 항목도 달라진다.

예를 들어 `quality` 모드의 `minlen = 14`는 공백과 등호로 나뉘어 키 `minlen`과 값 `14`가 된다. `emit()`은 이 키가 허용된 숫자 항목이고 값도 정수 형식일 때 `minlen=14`로 출력한다. PAM 모드에서는 모듈 뒤의 `minlen=8`을 따로 읽어 표시한다. 대괄호 제어문은 닫는 괄호까지 모으지만 그 분기를 실행하거나 두 값을 합쳐 유효 정책을 계산하지는 않는다. 출력의 줄 번호는 각 원본 파일의 행 번호다.

## 출력은 이렇게 읽는다

먼저 보관된 실행 기록은 `minlen=12`, `remember=4`가 들어 있는 가상 파일의 수집 결과다. `passwd`, `system-auth`, `password-auth` 등의 파일은 준비하지 않아 건너뜀으로 표시됐다. 이때 종료 코드 `0`은 읽은 파일의 수집 절차가 끝났다는 뜻이고, 비밀번호 정책 전체가 적용됐다는 뜻은 아니다.

[[run:1:fold]]

위 준비 파일은 값이 충돌하는 경우를 별도로 재현한다. 기본 파일에는 길이 14, PAM 호출에는 길이 8과 `enforcing=0`을 넣었다. 새 실행 출력의 관련 부분은 다음과 같다.

```text
[파일] /etc/security/pwquality.conf
1: minlen=14

[파일] /etc/pam.d/common-password
1: password requisite pam_pwquality.so minlen=8 enforcing=0 enforce_for_root

수동 검토 필요
```
이 PAM 호출이 실제 변경 경로에 있다면 길이 기준은 8이며, 복잡성 실패가 거절로 이어지지 않을 수 있다. 스크립트는 두 설정을 보여줄 뿐, 실행 경로나 최종 적용값까지 계산하지 않는다.

출력에 `include`나 `conf=`가 보이면 원본 줄에서 참조 파일을 따라간다. 수집 과정에서 일부 경로·옵션이 생략될 수 있으며 출력 순서는 적용 우선순위가 아니다. 보이지 않는 설정은 모듈 기본값과 사용자 지정 경로에서 찾고, 수집된 설정은 실제 비밀번호 변경 경로에서 호출되는지 대조한다.

첫 사례의 `@include`는 대상 미추적으로 표시된다. 이 줄에서 다음 PAM 파일까지 자동으로 따라간 결과는 없으므로 원본 참조를 별도로 읽어야 한다. 두 번째 사례는 `U02_ROOT`에 상대 경로를 넣어 파일 조회 전에 코드 `2`로 거부되는지 시험한다.

[[run:2:fold]]

준비 파일 자체의 종료 코드 `0`은 두 사례의 출력과 수집기 코드가 예상대로 나왔고 임시 자료도 정리됐다는 뜻이다. 비밀번호를 실제로 바꾸거나 PAM을 호출한 시험은 아니다.

## 운영 설정을 바꾸기 전에

PAM 변경 전에는 적용 경로와 계정 범위를 정리하고, 기존 관리 세션과 복구 수단을 확보한다. `authselect`를 사용하는 환경에서는 생성 파일을 직접 고치기보다 선택된 프로필과 변경 방법을 먼저 확인한다.

사용 기간을 바꿀 때는 기존 비밀번호 변경일과 서비스 연동도 확인한다. 비밀번호 만료가 배치 작업, 백업, 애플리케이션 접속에 영향을 줄 수 있다. 서비스 계정의 예외와 승인 근거도 함께 기록한다.

반영 후에는 검증 환경과 테스트 계정에서 길이·복잡성·재사용 제한이 실제로 동작하는지 확인한다. root가 수행하는 변경 경로도 포함한다. 점검 기록에는 설정 파일, PAM 적용 경로, 기존 계정의 사용 기간, 확인하지 못한 범위를 남긴다.

## 참고 자료

- [KISA, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.krcert.or.kr/kr/bbs/view.do?bbsId=B0000127&menuNo=205021&nttId=71928)
- [pwquality.conf(5)](https://manpages.debian.org/trixie/libpwquality-common/pwquality.conf.5.en.html)
- [pam_pwquality(8)](https://manpages.debian.org/trixie/libpam-pwquality/pam_pwquality.8.en.html)
- [pam_pwhistory(8)](https://manpages.debian.org/trixie/libpam-runtime/pam_pwhistory.8.en.html)
- [pam.conf(5)](https://manpages.debian.org/trixie/libpam-runtime/pam.conf.5.en.html)
- [login.defs(5)](https://manpages.debian.org/trixie/login.defs/login.defs.5.en.html)
- [chage(1)](https://manpages.debian.org/trixie/passwd/chage.1.en.html)
- [Red Hat Enterprise Linux 9, authselect 설정](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_authentication_and_authorization_in_rhel/configuring-user-authentication-using-authselect_configuring-authentication-and-authorization-in-rhel)
