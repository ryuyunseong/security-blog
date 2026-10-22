---
title: "U-12: 세션 종료 시간 설정"
description: "600초 이하의 유휴 종료 기준을 정리하고 별도 Bash에서 TMOUT의 대기 동작을 시험합니다."
date: "2026-10-17T09:07:00+09:00"
updated: "2026-10-22"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-12", "세션", "TMOUT"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 12
---

U-12는 입력 없이 열린 셸이 얼마 뒤에 종료되는지 점검한다. 같은 설정도 로그인 경로와 셸에 따라 적용 여부가 달라질 수 있어, 파일의 시간값과 새 세션의 유효값, 실제 종료 시간을 차례로 살펴야 한다.

2026년 KISA 상세가이드의 U-12는 중요도 ‘하’다. Solaris·Linux·AIX·HP-UX 등을 대상으로, **Session Timeout이 600초(10분) 이하이면 양호**, 그렇지 않으면 취약으로 분류한다. 원문 36쪽에는 sh·ksh·bash의 `TMOUT=600`과 `export TMOUT`, csh의 `set autologout=10`이 조치 사례로 실려 있다.

## 파일에 적힌 값과 현재 셸의 값을 나눠 본다

먼저 대상 계정이 어떤 셸로 접속하는지와 로그인 방식이 무엇인지 확인한다. `/etc/profile`에 `TMOUT=600`이 있어도, 해당 셸이 그 파일을 읽지 않으면 적용 근거가 되지 않는다. 반대로 현재 셸에서 값이 보인다는 사실만으로 모든 사용자의 접속 경로가 같은 값을 사용한다고 단정할 수도 없다. 시스템 파일 외에 사용자별 시작 파일이나 다른 설정에서 값을 다시 지정하는지도 확인해야 한다.

sh·ksh·bash 계열에서는 KISA의 예처럼 `TMOUT` 값을 초 단위로 설정하고 내보내는 방법을 검토한다. csh 계열의 `autologout=10`은 분 단위 사례다. 숫자 600과 10을 그대로 비교하면 단위가 달라 잘못 판단하기 쉽다. 셸마다 시작 파일과 동작이 다르므로 bash 예제를 csh에 그대로 적용하지 않는다.

승인된 시험 계정으로 **새 로그인 세션**을 열어 시험한다. 사용 중인 셸, `TMOUT` 또는 `autologout` 값과 단위, 로그인 경로를 적고 입력 없이 기다렸을 때 종료되는 시간을 측정한다. 설정 파일의 캡처만으로 실제 동작을 대신하지 않는다.

## bash의 TMOUT이 종료하는 시점을 정확히 읽는다

[Bash 공식 매뉴얼](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html)에 따르면 양수 `TMOUT`은 대화형 셸이 기본 프롬프트를 표시한 뒤 완전한 입력 행을 기다리는 시간이다. 그 시간 동안 입력이 없으면 셸이 종료된다. `read` 명령의 기본 제한 시간에도 쓰인다. 따라서 `TMOUT=600`을 “어떤 작업이든 시작 후 10분에 강제 중지”로 설명하면 틀린다. 명령이 실행 중이거나 셸 밖의 애플리케이션에 머무는 경우까지 이 변수 하나로 보장하지 않는다.

[[diagram]]

## 입력을 기다리는 셸에서 직접 확인한다

Linux의 `bash`, `script`(util-linux), `sleep`, `tr`가 필요하다. ZIP의 `check_u12_idle.sh`가 있는 폴더에서 `bash check_u12_idle.sh`로 실행한다. 별도의 로그인 계정이나 설정 파일은 준비하지 않는다.

`script`가 가상 터미널을 만들고, `sleep`이 입력 파이프를 열어 둔 사이 새 셸이 프롬프트에서 입력을 기다린다. `env -i`로 최소 환경만 전달하고 시작 파일은 읽지 않게 했다. 실제 로그인 계정이나 `/etc/profile`은 수정하지 않는다.

[[download]]

```bash
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
```

`HOME=/nonexistent`는 생성할 디렉터리가 아니라 별도 셸에 전달하는 값이다. `script`의 기록 대상은 `/dev/null`이어서 터미널 기록 파일도 남기지 않는다.

`result=$(...)`는 가상 터미널의 출력을 모은다. `sleep 4`는 입력이 없는 채로 파이프를 열어 두는 역할이며 TMOUT 자체는 `2`초다. 출력에서 자동 로그아웃 문구를 찾지 못하면 코드 `1`, 필요한 `script`가 없으면 `2`로 끝난다. `set -euo pipefail` 때문에 그 밖의 명령·파이프 실패도 성공 출력으로 이어지지 않는다.

[[run:1]]

출력 첫 줄은 Bash가 남긴 메시지이고 마지막 ‘확인’ 줄은 그 메시지를 찾은 바깥 스크립트가 출력한 것이다. 종료 코드 `0`은 메시지 검사가 통과했다는 뜻이다. 시작·종료 시각을 재서 정확히 2.000초였다고 측정한 기록은 아니다.

이 실습은 `TMOUT=2`인 셸의 메시지를 비교했다. 운영 로그인에서 600초 제한이 적용되는지, 네트워크 연결까지 끝나는지는 별도로 시험해야 한다. `TMOUT=0`·미설정 상태와 다른 셸은 이번 실험에 포함하지 않았다.

운영 점검에는 아래 자료를 수집한다.

| 확인 지점 | 남길 자료 | 해석할 때 주의할 점 |
| --- | --- | --- |
| 계정과 접속 방식 | 계정 용도, 로그인 셸, 접속 경로 | 서비스 계정·배치 작업을 대화형 사용자와 구분 |
| 설정 파일 | 적용 대상 파일과 값, 후속 재정의 여부 | 파일 존재만으로 새 로그인 세션의 유효값을 확정하지 않음 |
| 새 세션 | 셸 종류, 실제 변수 값과 단위 | 기존 세션에 변경이 소급됐다고 가정하지 않음 |
| 유휴 종료 | 시험 계정의 대기 시작·종료 시각 | 셸 종료와 네트워크 연결 종료를 구분 |

특히 공유 터미널이나 `su`로 전환한 셸은 접속 방식에 따라 읽는 시작 파일이 다를 수 있다. 주로 쓰는 SSH 로그인 한 종류만 확인했다면 그 범위를 점검 기록에 적는다. SSH 서버의 유휴 연결 감지와 화면 잠금 정책은 셸의 `TMOUT`과 따로 조사할 설정이다. 각각이 적용된 결과를 구분해 기록한다.

## 예외가 필요한 세션을 먼저 찾는다

KISA 가이드는 모니터링 업무에서 세션 타임아웃이 업무를 막을 수 있어 예외 처리가 필요하다고 적는다. 예외는 모든 계정의 제한을 풀 이유가 아니다. 사람이 지켜봐야 하는 대화형 화면인지, 서비스가 셸 프롬프트에 의존하는지, 중단되면 어떤 영향을 받는지 먼저 확인한다. 그런 뒤 예외 대상·대체 통제·재검토 시점을 문서화한다.

변경 전에는 새 시험 세션에서 시작 파일이 읽히는 경로를 조사하고 기존 세션·배치의 영향을 검토한다. 반영 후 새로 로그인해 유효값과 유휴 종료 시간을 측정한다. 계정·셸·접속 방식별로 결과를 남기면 600초 이하 제한이 적용된 경로를 알 수 있다.

## 참고 자료

- [KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드, U-12, 36쪽](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [GNU Bash Reference Manual: TMOUT](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html)
- [GNU Bash Reference Manual: 대화형 셸 동작](https://www.gnu.org/software/bash/manual/html_node/Interactive-Shell-Behavior.html)
