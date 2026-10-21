---
title: "U-04: 비밀번호 파일 보호"
description: "passwd 필드 집계와 shadow 메타데이터의 수집 범위를 설명하고, 가상 파일로 종료 코드 0·1·2와 미수집 경로를 비교합니다."
date: "2026-10-09T21:11:54+09:00"
updated: "2026-10-22"
sourcesChecked: "2026-10-21"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-04", "계정관리"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 4
---

Linux의 `/etc/passwd`에서 두 번째 필드가 `x`라면 비밀번호 정보는 쉐도우 저장소를 참조한다. `/etc/passwd`를 읽은 것과 비밀번호·해시를 얻은 것은 다르다.

U-04는 비밀번호를 어디에 어떤 방식으로 저장하는지 점검한다. 예제 스크립트는 passwd의 비밀번호 필드 유형별 건수와 shadow 파일의 UID·GID·모드를 수집한다. passwd 자체의 파일 권한이나 shadow 안의 계정별 저장값을 검사하는 코드는 아니다. 해시 원문은 수집하지 않는다.

## 저장 방식과 파일 권한은 별도로 점검한다

2026 KISA 상세가이드 25~26쪽의 U-04는 중요도 ‘상’이며 Solaris·Linux·AIX·HP-UX 등을 대상으로 한다. 양호 기준은 쉐도우 비밀번호를 사용하거나 비밀번호를 암호화해 저장하는 것이다. 둘 다 사용하지 않으면 취약으로 본다. 따라서 비밀번호 필드가 `x`가 아니라는 이유만으로 취약하다고 단정하지 않는다.

Linux의 일반적인 비밀번호 저장에는 해시를 사용한다. 해시는 원래 비밀번호를 복호화하는 값이 아니라 입력한 비밀번호를 검증하는 값이다. 다만 유출되면 후보 비밀번호를 대입해 비교할 수 있으므로 접근을 제한해야 한다.

| 점검 항목 | 확인할 내용 |
| --- | --- |
| U-04 비밀번호 파일 보호 | 쉐도우 사용 또는 암호화 저장 여부 |
| U-13 안전한 비밀번호 암호화 알고리즘 사용 | 비밀번호 저장에 사용하는 알고리즘 |
| U-16 /etc/passwd 파일 소유자 및 권한 설정 | 계정 정보 파일의 소유자와 접근 권한 |
| U-18 /etc/shadow 파일 소유자 및 권한 설정 | 쉐도우 파일의 소유자와 접근 권한 |

U-18은 별도로 소유자 root와 `400` 이하 권한을 요구한다(상세가이드 44쪽). 예를 들어 출력이 `소유 UID=0, 소유 GID=42, 모드=640`이라면 소유자는 root지만 모드는 그 기준과 다르다. `640`은 소유자 읽기·쓰기, 그룹 읽기, 기타 사용자 권한 없음으로 나뉜다.

GID 42가 어떤 그룹인지는 해당 시스템에서 `getent group 42`로 조회해야 한다. 숫자만 보고 그룹 이름이나 비인가자의 접근 여부를 확정하지 않는다. `stat -c '%n %U:%G %a %A' /etc/passwd /etc/shadow`로 두 파일의 속성을 별도로 수집하고, 확장 ACL과 그룹 구성원이 허용 범위를 넓히는지도 살핀다. 이 메타데이터 조회 명령은 파일 내용이나 해시를 출력하지 않는다.

권한을 변경하기 전에는 배포판의 파일 관리 방식과 인증 서비스의 의존성을 조사한다. 가이드 기준과 현재 값을 구별해 기록하고, 필요한 변경은 검증 환경에서 인증 동작과 복구 경로를 시험한 뒤 적용한다.

`/etc/shadow`가 존재한다는 사실만으로 모든 계정이 정상적으로 분리돼 있다고 볼 수는 없다. 쉐도우를 쓰지 않아도 암호화 저장 근거가 있다면 U-04의 양호 조건에 해당할 수 있지만, 일반 사용자가 읽을 수 있는 파일에 해시가 남아 있다면 노출 위험과 관련 점검 항목을 함께 검토한다.

[[diagram]]

## 비밀번호 필드는 원문 대신 유형으로 확인한다

`/etc/passwd`는 계정명, 비밀번호 필드, UID, GID, 설명, 홈 디렉터리, 로그인 셸의 일곱 필드로 구성된다. 보고서에는 계정명이나 해시 원문을 복사하기보다 유형별 건수를 남기고, 예외는 권한 있는 관리자가 서버에서 확인한다.

| 두 번째 필드 | 해석과 후속 확인 |
| --- | --- |
| `x` | 쉐도우 참조 표지. 실제 저장소에 해당 계정의 레코드가 있는지 확인한다. |
| `*`, `!`, `!!` | 비밀번호 로그인을 막는 표지. SSH 키 등 다른 로그인 방식까지 차단한 것은 아니다. |
| 빈 값 | 비밀번호 없는 인증 가능성을 확인한다. 실제 허용 여부는 PAM 등 인증 구성에 따라 달라진다. |
| 그 밖의 값 | 저장 방식과 형식을 확인한다. 문자열 모양만으로 유효한 해시나 평문이라고 단정하지 않는다. |

표와 아래 출력의 잠금 표지 건수는 **passwd의 두 번째 필드**만 집계한 값이다. 0개여도 shadow 안의 계정이 잠겨 있지 않다는 뜻은 아니다.

`!` 뒤에 문자열이 붙은 값에는 잠금 이전 비밀번호 정보가 남아 있을 수 있다. 아래 스크립트는 이런 값과 구형 해시, 알 수 없는 값을 모두 “기타 값”으로 집계한다.

## 읽기 전용 스크립트로 유형을 수집한다

ZIP의 `check_u04_password_file.sh`를 사용하거나 다음 코드를 같은 이름으로 저장한다. Bash, awk, GNU stat이 있는 Linux에서 사용하며 기본 대상은 `/etc`다. 일반 사용자 권한으로 읽을 수 있는 범위부터 실행한다.

스크립트는 passwd의 필드 유형과 shadow의 UID·GID·모드만 출력한다. shadow 내용은 읽지 않으며, 메타데이터를 조회할 수 없는 경우는 미수집으로 남긴다. 파일 변경이나 로그인 시도는 하지 않으며, 실행 중 파일이 교체되지 않는 신뢰할 수 있는 경로에서 사용한다.

```bash
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
```
```bash
bash check_u04_password_file.sh

# 시험용 디렉터리 바로 아래에 passwd와 shadow를 준비한다.
bash check_u04_password_file.sh /absolute/test-etc
```
심볼릭 링크가 포함된 경로와 일반 파일이 아닌 대상은 수집하지 않는다. 종료 코드의 의미는 다음과 같다. 이 값은 U-04의 양호·취약 판정이 아니다.

| 종료 코드 | 의미 |
| --- | --- |
| 0 | 추가 확인 표시 없이 유형 수집 종료 |
| 1 | 빈 필드·기타 값·중복 계정명·NIS 호환 표기 발견 |
| 2 | 파일 없음·접근 불가·링크 경로·형식 오류 또는 수집 실패 |

## 코드에서 집계와 파일 조회가 나뉘는 지점

| 구간 | 실제로 처리하는 내용 |
| --- | --- |
| 인수·경로 검사 | 인수를 하나까지 받고 점 경로가 없는 절대 경로인지 검사한다. `safe_path()`는 부모를 포함한 링크 경로를 거부하지만 실행 도중 파일이 바뀌는 경쟁 조건까지 막지는 못한다. |
| awk의 형식 검사 | 콜론으로 나눈 필드 7개, 계정명, 숫자 UID·GID와 제어 문자를 검사한다. 중복 계정명과 NIS 호환 표기는 별도 건수로 남긴다. |
| 비밀번호 필드 분류 | 정확히 `x`, `*`, `!`, `!!`인 값과 빈 값을 구별한다. `!` 뒤에 문자열이 붙은 값은 기타 값으로 집계한다. |
| awk 종료 코드 변환 | 내부 코드 10을 스크립트의 1로, 11 또는 집계 오류를 2로 바꾼다. 이후 shadow 조회에 실패해도 최종 값은 2가 된다. |
| stat 조회 | shadow의 `%u`는 숫자 UID, `%g`는 숫자 GID, `%a`는 8진수 모드다. 파일의 계정별 내용이나 passwd 자체의 권한은 조회하지 않는다. |

`일반 레코드`는 빈 줄과 NIS 호환 줄을 뺀 집계 대상 수다. `total++`가 형식 검사보다 앞에 있으므로 잘못된 레코드도 이 수에 포함될 수 있다. 형식 오류가 있으면 이 숫자만 분모로 삼아 저장 상태를 판정하지 않는다.

## 준비하지 않은 경로는 미수집으로 끝난다

앞의 `/absolute/test-etc`는 예시 경로다. 명령을 입력한다고 디렉터리와 파일이 생기지는 않는다. 그 디렉터리 바로 아래에 읽을 수 있는 일반 파일 `passwd`와 메타데이터를 조회할 `shadow`가 있어야 한다. 경로가 존재해도 링크·접근 권한 문제로 수집이 중단될 수 있다.

`$LAB/fixture/etc`도 자동 생성되는 경로가 아니다. 호출하는 셸에서 LAB 변수를 먼저 지정해야 한다. `printf 'LAB=[%s]\n' "${LAB:-}"`로 비어 있는지 살펴볼 수 있다. LAB이 미설정이고 호출 셸의 nounset 옵션이 꺼져 있으면 `$LAB/fixture/etc`는 `/fixture/etc`로 확장된다. 수집기 안의 `set -u`는 명령을 호출하기 전에 끝난 이 확장을 검사하지 못한다. 호출 셸에서 nounset을 켰다면 수집기 실행 전에 변수 오류로 멈출 수 있다.

다음 실습기는 LAB을 직접 만들고 모든 호출에 `"$LAB/fixture/etc"`처럼 따옴표로 감싼 경로를 넘긴다. 임시 폴더를 수동으로 준비하지 않아도 같은 입력을 재현할 수 있다.

## 출력에서 추가 확인 대상을 찾는다

추가 실습의 두 번째 경우는 `x`, `!`, 빈 값, `TEST_ONLY`라는 시험 문자열을 하나씩 넣는다. 실제 비밀번호나 해시를 쓰지 않은 이 입력에서 집계한 결과는 다음과 같다.

```text
[passwd 비밀번호 필드 유형]
일반 레코드: 4
쉐도우 참조 x: 1
잠금 표지 *, !, !!: 1
빈 비밀번호 필드: 1
기타 값: 1
형식 확인 필요: 0
중복 계정명: 0
NIS 호환 표기: 0
```
빈 필드가 있으면 해당 인증 경로에서 빈 비밀번호를 허용하는지 조사한다. 기타 값은 저장 형식을 더 살펴야 하며, 집계 결과만으로 평문이라고 단정할 수 없다.

아래의 기존 실행 기록은 이 네 행과 다른 자료다. `x`가 있는 두 계정과 내용이 빈 가상 shadow를 사용했고 종료 코드는 0이었다. 파일이 비어 있어도 메타데이터를 수집할 수 있기 때문이다. 이 결과가 계정별 shadow 대응 관계를 검증한 것은 아니다.

[[run:1:fold]]


## 가상 파일을 준비해 종료 코드 0·1·2 비교하기

ZIP의 `u04_fixture_lab.sh`와 위 수집기를 같은 폴더에 두고 `bash u04_fixture_lab.sh ./check_u04_password_file.sh`로 실행한다. Bash·awk·GNU stat과 일반 Coreutils가 있는 Linux 또는 WSL 환경을 사용한다.

실습기는 `/tmp`에 새 디렉터리를 만들고 그 안에서만 가상 파일을 생성·변경한다. shadow는 내용이 없는 파일로 만들고 모드를 `600`으로 지정한다. 이 값은 비교용 파일의 설정이며 U-18의 운영 권장값을 뜻하지 않는다. 끝나면 자신이 생성한 임시 경로인지 대조한 뒤 정리한다.

| 가상 입력 | 수집기 종료 코드 | 관찰 |
| --- | --- | --- |
| `x` 두 개와 빈 shadow | 0 | 필드 유형과 파일 메타데이터를 수집했다. shadow 안의 대응 레코드는 없는데도 0으로 끝난다. |
| 네 가지 비밀번호 필드 | 1 | 빈 값과 기타 값이 각각 한 개 집계된다. 잠금 표지 역시 passwd 기준으로 한 개다. |
| 만들지 않은 임시 하위 경로 | 2 | passwd를 읽지 못해 미수집으로 끝난다. 비밀번호 저장 방식은 이 결과로 판정할 수 없다. |

새 실행 기록에는 세 호출의 출력과 종료 코드가 함께 들어 있다. 처음의 두 계정 자료를 네 가지 필드로 바꾼 뒤, 마지막에는 준비하지 않은 경로를 넘겼다.

[[run:2:fold]]

실습기 전체의 종료 코드 0은 세 호출이 예상한 0·1·2로 끝났다는 뜻이다. 출력의 소유 UID·GID는 임시 파일을 만든 사용자의 값이다. 실제 계정 파일과 인증 설정은 읽거나 변경하지 않았다.

## 중앙 인증과 다른 운영체제는 범위를 나눠 본다

AD·LDAP 같은 중앙 인증 계정은 로컬 `/etc/passwd`만으로 파악할 수 없다. `/etc/nsswitch.conf`의 passwd·shadow 조회 경로와 PAM 구성을 확인하고, 중앙 저장소의 보호 정책은 해당 관리 범위에서 점검한다. 조회 경로를 확인한 것과 비밀번호 저장 방식을 확인한 것은 구분한다.

컨테이너 안의 결과는 그 컨테이너의 상태만 보여 준다. 호스트나 다른 컨테이너로 확대하지 않는다. NIS 호환 표기나 별도 인증 모듈이 있다면 외부 계정 점검도 필요하다.

AIX의 `/etc/security/passwd`나 HP-UX 등 다른 Unix에는 이 스크립트를 경로만 바꿔 적용하지 않는다. 해당 운영체제의 저장 방식과 지원 절차를 확인한다.

## 조치는 백업과 복구 경로를 확보한 뒤 진행한다

쉐도우 분리가 필요하다면 배포판이 지원하는 계정 관리 절차를 따른다. `pwconv`는 조회 명령이 아니라 passwd와 shadow를 변경하는 도구다. 기존 레코드와 비밀번호 사용 기간 설정에 영향을 줄 수 있어 진단 스크립트에는 포함하지 않았다.

계정 파일의 구조와 passwd·shadow 대응 관계에는 읽기 전용 옵션인 `pwck -r`을 검토할 수 있다. 권한 있는 관리 세션에서 사용하며, 이 도구의 검사는 해시 알고리즘 강도나 실제 인증 성공을 검증하는 것과 다르다.

변경 전에는 계정 파일의 일관성을 확인하고 보호된 백업과 콘솔 등 복구 경로를 확보한다. 검증 환경에서 전환 후 레코드 대응 관계와 필요한 인증 동작을 확인한 뒤 운영에 반영한다. 평문 저장이나 해시 노출이 확인됐다면 노출 범위와 비밀번호 재설정 필요성도 검토한다.

보고서에는 조사한 저장소와 저장 방식, 전환 후 인증 결과를 적는다. 비밀번호나 해시 원문은 첨부하지 않는다.

## 참고 자료

- [KISA 2026 상세가이드: U-04 25~26쪽, U-18 44쪽](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux man-pages, passwd(5)](https://man7.org/linux/man-pages/man5/passwd.5.html)
- [shadow-utils, shadow(5)](https://man7.org/linux/man-pages/man5/shadow.5.html)
- [Linux man-pages, crypt(3)](https://man7.org/linux/man-pages/man3/crypt.3.html)
- [shadow-utils, pwconv(8)](https://man7.org/linux/man-pages/man8/pwconv.8.html)
- [Linux man-pages, nsswitch.conf(5)](https://man7.org/linux/man-pages/man5/nsswitch.conf.5.html)
- [GNU Coreutils, stat invocation](https://www.gnu.org/software/coreutils/manual/coreutils.html#stat-invocation)
- [shadow-utils, pwck(8): 읽기 전용 검사와 대응 관계](https://man7.org/linux/man-pages/man8/pwck.8.html)
