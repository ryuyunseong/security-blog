---
title: "U-03: 계정 잠금 임계값 설정"
description: "pam_faillock의 잠금 횟수·시간 설정과 서비스별 PAM 구성을 점검합니다."
date: "2026-10-08T21:45:21+09:00"
updated: "2026-10-17T18:17:24+09:00"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-03", "PAM"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 3
---

`pam_faillock`의 `deny`, `fail_interval`, `unlock_time`은 각각 잠금 횟수, 실패 집계 구간, 잠금 해제 시간을 정한다. U-03을 점검할 때는 이 값들이 어느 서비스의 인증 경로에 적용되는지부터 찾는다.

파일에 `deny=10`이 있어도 해당 PAM 호출에 다른 인수가 지정됐거나 잠금 모듈을 건너뛰면 동작이 달라진다. 아래 수집기로 기본 설정과 서비스별 호출을 나란히 읽어 본다.

## 판단 기준과 점검 범위

U-03의 기준은 계정 잠금 임계값 10회 이하이다. 실제 인증 경로에 적용되는 임계값이 없거나 10회를 초과하면 취약으로 본다. 다만 `pam_faillock`의 `deny=0`은 임계값에 따른 잠금을 비활성화하므로, 숫자가 10 이하라는 이유로 양호하게 처리해서는 안 된다.

| 확인 항목 | 확인할 내용 |
| --- | --- |
| 임계값 | 유효한 양의 정수이며 10 이하인지 확인한다. 파일과 PAM 인수의 값이 다르면 적용값을 추적한다. |
| 적용 서비스 | SSH, 콘솔 로그인, su, sudo 등의 PAM 연결과 인증 분기를 확인한다. |
| 계정 범위 | 일반 계정, root, 중앙 인증 계정의 적용 정책과 예외를 확인한다. |
| 잠금과 복구 | 실패 집계 구간, 잠금 해제 시간, 비상 접근 경로를 확인한다. |

아래 스크립트는 Linux 설정 수집용이다. U-03에 포함된 다른 Unix 운영체제나 중앙 인증 서버의 정책은 별도로 점검한다.

## 임계값과 잠금 시간을 구분하기

`deny`는 잠금 임계값, `fail_interval`은 실패 집계 구간, `unlock_time`은 잠금 해제까지의 시간이다. 다음은 각 설정의 역할을 설명하기 위한 예시다.

```text
# /etc/security/faillock.conf의 정책 예시
deny = 5
fail_interval = 900
unlock_time = 600
```
실패를 집계하는 구간은 900초, 잠금 후 해제 시간은 600초다. `unlock_time=0`은 시간 경과에 따른 자동 해제를 하지 않는 설정이며 `deny=0`과 의미가 다르다. 실패 기록의 집계와 성공 후 초기화는 PAM 구성도 확인해야 한다.

`pam_faillock`는 기본적으로 root를 잠그지 않는다. `even_deny_root`와 `root_unlock_time`, `admin_group`이 있으면 관리자 적용 범위를 확인한다. `root_unlock_time` 지정은 root 잠금도 활성화하므로 복구 경로를 먼저 확보한다.

[[diagram]]

## 설정 파일에서 인증 경로까지 확인하기

먼저 `/etc/security/faillock.conf`와 서비스별 PAM 설정을 확인한다. PAM 모듈 인수는 설정 파일보다 우선하며 `conf=`가 있으면 지정된 파일도 확인한다. 일부 Linux-PAM 버전은 기본 파일이 없을 때 `/usr/share/pam/security/faillock.conf`를 사용한다. 설치된 버전의 문서와 함께 확인한다.

`preauth`는 인증 전 잠금 여부를 확인하고, `authfail`은 실패를 기록하며, `authsucc`는 성공 후 실패 기록을 정리한다. `account` 단계와 조합하는 구성도 있다. 세 옵션의 존재만 확인하기보다 성공·실패 분기에서 실제로 어떤 모듈이 실행되는지 따라가야 한다.

`include`, `substack`, `@include`의 참조 대상과 `sufficient`, 대괄호 제어문의 분기를 살핀다. 앞선 모듈에서 인증이 종료되거나 실패 기록 단계가 건너뛰어질 수 있다. 구형 `pam_tally`·`pam_tally2`의 설정을 `pam_faillock`에 그대로 옮겨서는 안 된다.

SSH는 실제 적용 중인 `UsePAM`과 인증 방식도 확인한다. AD·LDAP·IdM 계정은 중앙 잠금 정책과 로컬 PAM의 범위를 함께 본다. `local_users_only`가 있으면 중앙 계정은 로컬 실패 집계에서 제외된다.

## 읽기 전용 스크립트로 설정 수집하기

아래 코드를 `check_u03_lockout.sh`로 저장한다. Bash와 `awk`, 대상 파일을 읽을 권한이 필요하다. 지정된 경로에서 잠금 정책과 인증·계정 단계의 설정 후보만 수집하며 로그인 시도, 잠금 해제, 설정 변경은 하지 않는다.

```bash
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
```
현재 시스템과 별도로 준비한 설정 복사본은 다음과 같이 확인한다. 복사본은 `U03_ROOT` 아래에 `etc/security`, `etc/pam.d` 등의 디렉터리 구조를 유지한다.

```bash
# 현재 시스템의 설정 후보 조회
bash check_u03_lockout.sh

# 별도로 준비한 설정 복사본 조회
U03_ROOT=/absolute/config-copy bash check_u03_lockout.sh
```
참조 파일을 재귀적으로 따라가지 않으며 심볼릭 링크도 건너뛴다. `authselect`의 생성 파일은 별도로 제시하지만 서비스 연결 여부까지 판정하지 않는다. `/etc/pam.conf`, 사용자 지정 서비스·설정 파일, 다른 벤더 경로는 직접 확인한다. 실행 중 경로가 바뀌는 상황까지 막는 도구는 아니다.

종료 코드 `0`은 수집 절차가 끝났다는 뜻이며 누락된 파일이 있어도 반환될 수 있다. 잘못된 시험 경로, `awk` 누락, 읽기·파싱 오류는 `2`로 표시한다. 출력의 미수집·생략 안내와 수동 검토 항목을 함께 확인한다.

[[run:1:fold]]

## 출력에서 실제 적용값 확인하기

시험용 기본 설정에는 `deny=5`, SSH PAM 줄에는 `deny=20`을 넣었다. 수집 결과의 관련 부분은 다음과 같다.

```text
[파일] /etc/security/faillock.conf
1: deny=5
임계값 후보: 1~10, 실제 적용 경로 확인

[파일] /etc/pam.d/sshd
1: auth required pam_faillock.so preauth deny=20

최종 판단: 수동 검토 필요
```
이 호출에는 기본 파일의 5가 아닌 PAM 인수의 20이 우선한다. 잠금이 실제로 작동하려면 이 호출이 인증 경로에 연결되고 실패 기록과 성공 후 처리가 이어져야 하므로, 관련 분기까지 따라간다.

임계값 0·10 초과·중복·잘못된 값, PAM 인수와 참조 구문, 링크, 오류 처리 등 시험용 설정 23가지에서 예상 결과를 확인했다. 입력 파일의 내용과 권한, 링크도 유지됐다. 검증 범위는 파일 수집과 출력이며 실제 PAM 인증이나 계정 잠금 동작은 시험하지 않았다.

## PAM 변경 전 복구 수단과 테스트 계정 준비하기

설정이 없는 항목에는 설치된 모듈의 기본값을 대조한다. 모듈 설치 여부와 서비스 연결도 조사해, 각 서비스·계정에 어느 값이 적용되는지 기록한다. 연결을 추적하지 못한 경로는 미확인 범위로 남긴다.

변경할 때는 배포판이 지원하는 PAM 관리 방식으로 양의 임계값을 적용한다. RHEL에서 `authselect`를 사용한다면 선택된 프로필을 먼저 확인한다. 생성 파일만 직접 수정하거나 인증 스택 전체를 덮어쓰면 설정의 일관성이 깨지고 정상 로그인도 막힐 수 있다.

운영 반영 전에는 설정 백업과 콘솔 등 비상 접근 경로를 확보한다. 격리된 검증 환경과 전용 시험 계정에서 임계값 도달, 정상 비밀번호 차단, 해제 시간 후 복구, 성공 후 기록 초기화, 관리자·중앙 계정 예외를 확인한다. 운영 관리자 계정으로 실패 로그인을 반복하지 않는다.

계정 잠금만으로 여러 계정을 천천히 시도하는 공격이나 잠금을 악용한 서비스 방해까지 막을 수는 없다. 인증 로그 탐지, 접근 경로 제한, 다중 인증을 함께 운영한다.

## 참고 자료

- [KISA, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.krcert.or.kr/kr/bbs/view.do?bbsId=B0000127&menuNo=205021&nttId=71928)
- [Linux-PAM, pam_faillock(8)](https://man7.org/linux/man-pages/man8/pam_faillock.8.html)
- [Linux-PAM, faillock.conf(5)](https://man7.org/linux/man-pages/man5/faillock.conf.5.html)
- [Linux-PAM, pam_faillock 구현](https://github.com/linux-pam/linux-pam/blob/master/modules/pam_faillock/pam_faillock.c)
- [OpenSSH, sshd_config(5)](https://manpages.debian.org/trixie/openssh-server/sshd_config.5.en.html)
- [Red Hat Enterprise Linux 9, authselect 설정](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_authentication_and_authorization_in_rhel/configuring-user-authentication-using-authselect_configuring-authentication-and-authorization-in-rhel)
