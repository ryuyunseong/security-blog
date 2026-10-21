---
title: "U-05: root 이외의 UID가 ‘0’ 금지"
description: "root 이외의 UID 0 계정을 찾고 로컬·중앙 계정의 확인 범위를 구분합니다."
date: "2026-10-10T21:19:36+09:00"
updated: "2026-10-22"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-05", "UID"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 5
---

비밀번호가 잠기고 셸이 `nologin`인 `backup` 계정도 UID가 0이면 U-05 조사 대상이다. 가상 passwd 파일을 사용해 로그인 제한과 숫자 UID를 따로 점검하는 이유를 살펴본다.

먼저 로컬 passwd 파일에서 root 이외의 UID 0 계정을 찾는다. LDAP·AD 같은 중앙 계정을 사용한다면 로컬 결과에서 멈추지 않고 NSS 조회와 원래 계정 저장소를 대조해야 한다.

## 로그인 제한과 UID 설정은 따로 판단한다

root 이외에 UID가 0인 계정이 없으면 양호, 있으면 취약으로 판단한다. 여러 이름이 같은 UID를 공유하면 파일 소유권이나 UID만 남은 기록에서 어느 계정의 행위인지 구분하기도 어려워진다.

| 확인한 설정 | U-05에서의 해석 |
| --- | --- |
| root 이외의 계정에 UID 0 부여 | 취약 조건에 해당한다. |
| 해당 계정의 비밀번호 잠금 또는 nologin 설정 | 일부 로그인 경로를 제한할 수 있지만 UID 0 중복은 해소되지 않는다. |
| 일반 계정의 GID가 0 | 그룹 권한을 별도로 확인한다. UID 0과 같은 조건은 아니다. |
| 일반 계정에 sudo 권한 부여 | 권한 위임 정책을 점검할 대상이다. 계정 UID가 0이라는 뜻은 아니다. |

/etc/passwd의 각 계정 레코드는 콜론으로 구분된 일곱 필드이며, 세 번째 필드가 UID다. /etc/shadow에는 UID 필드가 없으므로 U-05 점검을 위해 비밀번호 해시를 수집할 필요는 없다.

[[diagram]]

## 로컬 파일에서 확인한 결과는 로컬 계정 범위다

다음 명령은 /etc/passwd에서 UID가 0인 레코드의 계정 이름과 UID만 출력한다. 파일을 읽을 권한이 필요하며, 일반적인 Linux 환경에서는 관리자 권한 없이 실행할 수 있다.

```bash
awk -F: 'NF == 7 && $3 ~ /^0+$/ {printf "계정=%s UID=%s\n", $1, $3}' /etc/passwd
```
출력이 root 한 줄이어도 조사 범위는 더 살펴야 한다. 형식이 깨진 레코드는 조건에 걸리지 않을 수 있고, 중앙 계정이 로컬 파일에 모두 들어 있지도 않다. 아래 스크립트에서는 형식 경고와 수집 범위를 함께 읽는다.

LDAP·AD·SSSD 등을 사용하는 서버에서는 /etc/nsswitch.conf의 passwd 조회 구성을 확인한다. NSS(Name Service Switch)는 프로그램이 계정 정보를 어느 출처에서 어떤 순서로 조회할지 결정하는 체계다.

getent passwd는 NSS를 통해 계정 목록의 열거를 요청한다. 하지만 백엔드 설정이나 조회 오류에 따라 일부 계정이 보이지 않을 수 있다. SSSD처럼 전체 열거를 비활성화할 수 있는 구성도 있으므로, 중앙 계정 저장소에서 UID 매핑을 확인하고 서버의 조회 결과와 대조한다.

getent passwd 0도 전체 중복 계정을 찾는 명령은 아니다. UID 하나로 계정 정보를 조회하므로, UID 0을 공유하는 모든 이름을 반환한다고 가정하면 안 된다.

## 계정 정보를 읽어 확인하는 스크립트

아래 코드를 check_u05.sh로 저장한다. 기본 실행은 현재 환경의 /etc/passwd를 읽고, --file은 지정한 파일을 분석한다. --nss는 NSS 계정 목록을 추가로 조회한다.

Bash와 awk가 필요하며, NSS 모드에서는 getent와 GNU timeout도 사용한다. 계정 설정을 변경하거나 로그인 시도를 하지는 않는다. 다만 NSS 조회는 설정된 중앙 계정 서버에 요청을 보낼 수 있다.

[[download]]

```bash
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
```
```text
# 현재 환경의 로컬 계정 파일 확인
bash check_u05.sh

# 점검 대상으로 받은 passwd 파일 확인
bash check_u05.sh --file ./passwd.sample

# 중앙 계정 연동 환경에서 추가 확인
bash check_u05.sh --nss
result=$?
printf '종료 코드=%s\n' "$result"
```
## 양호·취약·확인 필요를 구분하는 방식

check_records()는 필드 수, 계정 이름, UID·GID의 기본 형식을 확인한 뒤 root 이외의 UID 0 계정을 찾는다. /^0+$/는 0과 000처럼 0으로만 구성된 값을 함께 검출한다. 비밀번호 필드, 홈 디렉터리, 셸은 결과에 출력하지 않는다.

형식이 깨진 줄이나 NIS 호환 지시문은 일반 계정처럼 분석하지 않고 '확인 필요'로 남긴다. root 레코드가 없거나 반복되는 경우도 양호로 처리하지 않는다. 이 검사는 UID 0 점검에 필요한 기본 확인이며, 계정 데이터베이스 전체의 무결성 검사를 대신하지 않는다.

NSS 모드에서는 조회 명령의 종료 코드를 먼저 확인한다. 실패나 시간 초과를 빈 목록으로 오인하지 않기 위해서다. 조회가 성공해도 목록의 완전성이 보장되지 않으므로, 취약 계정이 발견되지 않은 NSS 결과는 '확인 필요'로 반환한다.

| 종료 코드 | 의미 | 후속 확인 |
| --- | --- | --- |
| 0 | 검사한 파일에 다른 UID 0 계정이 없고 형식 경고도 없음 | 해당 파일 범위의 양호다. 중앙 계정 연동 여부와 파일의 출처를 확인한다. |
| 1 | 검사한 레코드에서 root 이외의 UID 0 계정 발견 | 해당 계정의 출처와 서버에서 실제로 조회되는 UID를 확인한다. |
| 2 | 판정을 완료할 수 없거나 추가 확인이 필요함 | 인자·파일·도구 오류, 레코드 이상, root 레코드 이상, NSS 조회 범위를 확인한다. |

취약 계정과 형식 경고가 함께 발견되면 종료 코드 1을 반환한다. 이미 확인한 UID 0 계정을 경고 때문에 놓치지 않도록 한 것이다. 경고가 사라진 것은 아니므로 출력된 항목도 별도로 검토한다.

## 테스트 파일에서 확인한 출력

ZIP을 풀면 `check_u05.sh`와 `u05_fixture_lab.py`가 같은 폴더에 있다. Linux의 Python 3, Bash, awk가 있는 터미널에서 `python3 -I -B u05_fixture_lab.py ./check_u05.sh`로 실행하면 아래 세 사례를 차례로 재현한다. 수집기에 `--file`을 항상 전달하므로 운영 계정 파일이나 NSS를 조회하지 않는다.

준비 파일은 `/tmp`의 새 폴더에 `etc/passwd`를 만든다. 처음에는 root와 alice 두 줄, 다음에는 UID 0인 backup 한 줄을 추가하고, 마지막에는 `malformed` 한 줄로 교체한다. 따라서 본문 실행 예시의 `./passwd.sample`이나 기록에 표시된 `$LAB/fixture/etc/passwd`를 별도로 갖고 있을 필요는 없다. 준비 파일 안의 `TemporaryDirectory`가 종료 시 자신이 만든 폴더를 정리한다.

root와 UID 1000인 일반 사용자만 있는 테스트용 파일에서는 다음과 같이 출력됐으며, 종료 코드는 0이었다.

```text
[범위] 지정한 passwd 파일의 현재 내용
[양호] 검사한 파일에서 root 이외의 UID=0 계정 없음
```

[[run:1:fold]]

같은 파일에 UID 0인 backup 레코드를 추가하면 종료 코드 1을 반환하고 계정 이름을 표시했다. 비밀번호를 잠그고 셸을 nologin으로 지정한 레코드에서도 동일하게 검출됐다.

```text
[취약] 계정=backup UID=0
[범위] 지정한 passwd 파일의 현재 내용
```

[[run:2:fold]]

위 비교에는 테스트 파일만 사용했다. 운영 계정을 조사할 때는 로컬 레코드와 NSS가 같은 이름에 반환하는 UID도 대조해야 한다. 테스트 파일에서의 검출 결과로 실제 계정의 조회·로그인 상태까지 설명할 수는 없다.

마지막 자료의 `malformed`는 일곱 필드가 아니므로 awk의 `review()`가 경고를 남기고 해당 줄을 건너뛴다. 정상 root 레코드 수도 0이 되어 두 번째 경고가 더해진다. 내부 상태 `20`은 Bash의 마지막 `case`에서 외부 코드 `2`로 바뀐다. 계정 파일의 형식을 깨뜨리자 종료 코드 `2`와 추가 확인 안내가 나왔다. 읽을 수 없는 자료가 ‘UID 0 계정 없음’으로 처리되지 않는지도 이 사례로 확인했다.

[[run:3]]

위 기록은 개별 수집기의 코드 `0`·`1`·`2`다. 준비 파일은 세 값이 각각 예상과 같으면 마지막에 코드 `0`과 ‘실습 파일 정리: 완료’를 남긴다. 실제 결과와 다른 코드나 표준 오류가 나오면 예외로 끝나므로 마지막 코드만 보고 개별 판정을 생략하지 않는다.

## 컨테이너에서 실행했다면 점검 범위를 기록한다

컨테이너 안에서 스크립트를 실행하면 그 환경에서 보이는 계정 파일을 읽는다. 사용자 네임스페이스(User Namespace)를 사용하면 내부 UID 0이 호스트의 일반 UID로 매핑될 수 있다. 컨테이너 안에서 UID 0을 확인했다는 이유만으로 호스트 관리자 권한까지 있다고 판단하지 않는다.

계정 파일은 이름과 UID의 대응 정보를 제공한다. 실행 중인 프로세스의 권한은 유효 UID(Effective UID), capabilities, 네임스페이스 등의 영향을 받는다. 호스트와 컨테이너는 각각 점검하고, 실행 위치·UID 매핑·수집한 파일의 출처를 결과에 함께 기록한다.

## UID 변경 전에는 소유권과 실행 중인 작업부터 확인한다

불필요한 UID 0 계정은 제거하고, 계속 사용할 계정에는 시스템의 UID 할당 정책에 맞는 중복되지 않는 일반 UID를 배정한다. 관리자 작업은 개인별 계정과 필요한 범위의 권한 위임으로 분리한다. 중앙 계정이라면 로컬 파일만 고치는 대신 원래 계정 저장소에서 변경해야 한다.

변경 전에 해당 계정의 세션·서비스·예약 작업과 소유 파일을 조사한다. 계정 데이터베이스를 고쳐도 실행 중인 프로세스의 자격 증명이 즉시 바뀌지는 않는다. usermod가 시스템 전체의 파일 소유권을 정리하는 것도 아니므로 변경 대상을 미리 정해야 한다.

특히 기존 UID가 0이면 UID로 찾은 파일에 정상적인 root 소유 파일도 함께 포함된다. 이 목록을 모두 새 UID로 바꾸면 시스템 파일의 소유권까지 변경될 수 있다. 공유된 UID만으로 어느 계정의 파일인지 구분하기 어려우므로, 서비스 설정과 실제 사용 경로를 기준으로 소유권 변경 대상을 정한다.

기존 계정에 의존하지 않는 관리자 복구 경로를 확보한 뒤 변경하고, 필요한 재시작·재로그인을 거쳐 계정 조회 결과와 업무 동작을 다시 확인한다.

## 참고 자료

- KISA, [주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드, U-05](https://www.kisa.kr/2060204/form?lang_type=KO&page=1&postSeq=22)
- Linux man-pages, [passwd(5)](https://man7.org/linux/man-pages/man5/passwd.5.html)
- Linux man-pages, [getent(1)](https://man7.org/linux/man-pages/man1/getent.1.html)
- Linux man-pages, [nsswitch.conf(5)](https://man7.org/linux/man-pages/man5/nsswitch.conf.5.html)
- SSSD, [Troubleshooting Basics](https://sssd.io/troubleshooting/basics.html)
- Linux man-pages, [credentials(7)](https://man7.org/linux/man-pages/man7/credentials.7.html)
- Linux man-pages, [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html)
- shadow-utils, [usermod(8)](https://man7.org/linux/man-pages/man8/usermod.8.html)
