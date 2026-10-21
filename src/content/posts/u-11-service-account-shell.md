---
title: "U-11: 사용자 shell 점검"
description: "로그인 불필요 계정의 셸을 분류하고 nologin으로 바꾸기 전 서비스 실행 방식을 조사합니다."
date: "2026-10-16T21:58:00+09:00"
updated: "2026-10-22"
sourcesChecked: "2026-10-16"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-11", "계정", "Shell"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 11
---

서비스 계정에 `/bin/bash`가 지정돼 있다면 직접 로그인할 업무가 있는지부터 조사한다. UID나 계정 이름만으로 그 필요성을 정하지 않는다. 가상 계정 `svc_report`의 셸을 바꾸며 검토 목록이 어떻게 달라지는지 비교해 본다.

U-11은 **로그인이 필요하지 않은 계정에 로그인용 셸이 남아 있는지** 확인하는 항목이다. 계정을 지워야 하는지 살피는 U-07과는 조치가 다르다. 서비스 실행에 필요한 계정은 유지하면서 직접 로그인할 통로를 제한할 수 있다.

## 계정의 용도를 먼저 정한다

2026 KISA 상세가이드의 U-11은 중요도 ‘하’이며 SOLARIS, LINUX, AIX, HP-UX 등을 대상으로 한다. 로그인 불필요 계정에 `/bin/false` 또는 `/sbin/nologin` 셸을 설정했는지를 판단 기준으로 삼는다. 원문은 [KISA 공식 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 35쪽에서 확인할 수 있다.

`daemon`, `bin`, `sys`, `adm` 계정도 용도를 확인해야 한다. 이름이 같아도 운영체제와 서비스 구성에 따라 쓰임이 다르므로 목록을 그대로 변경 명령에 넣지 않는다. 별도로 만든 서비스 계정도 조사 대상에 포함한다. UID가 작다는 이유로 로그인 불필요 계정이라고 단정하거나, UID가 크다는 이유로 제외하지 않는다.

| 확인할 자료 | 판단에 쓰는 이유 |
| --- | --- |
| 계정 담당자와 사용 목적 | 직접 로그인할 업무가 있는지 확인 |
| 서비스 실행 사용자와 예약 작업 | 셸 변경으로 영향을 받는 작업 확인 |
| 로컬 계정 및 중앙 계정 조회 결과 | 조사에서 빠진 계정 확인 |
| 로그인 셸과 해당 파일의 실제 위치 | 제한용 셸인지, 실행 가능한 파일인지 확인 |

`/etc/passwd`의 마지막 필드가 로그인 셸이다. Linux에서 이 필드가 비어 있으면 기본적으로 `/bin/sh`를 사용하므로, 빈 값을 로그인 차단으로 읽으면 안 된다. `/etc/shells` 역시 사용할 수 있는 셸의 목록이지, 해당 계정에 로그인할 업무가 있다는 근거는 아니다.

## nologin과 false의 역할을 구분한다

`nologin`은 계정 이용 불가 메시지를 표시하고 실패 상태로 종료하는 로그인 셸 대체 프로그램이다. `false`도 실패 상태를 반환하지만 안내 메시지는 표시하지 않는다. 배포판에 따라 `/usr/sbin/nologin`이나 `/usr/bin/false` 경로를 사용할 수 있으므로 실제 경로와 파일을 확인한다.

이 설정은 계정 자체를 삭제하거나 모든 프로세스 실행을 막는 기능이 아니다. 이미 실행 중인 서비스, 예약 작업, 로그인 셸을 사용하지 않는 실행 경로의 동작은 별도로 확인해야 한다. FTP 등 다른 서비스의 접근 가능 여부도 각 서비스의 인증·PAM·셸 검사 설정에 따라 달라진다.

조치 기록에는 제한한 로그인 경로와 셸 변경 후 시험한 서비스 동작을 적는다. 셸을 바꿨다는 이유로 해당 계정의 모든 명령 실행을 막았다고 쓰지는 않는다.

[[diagram]]

## 가상 passwd 자료에서 검토할 계정을 찾는다

다음 코드를 `check_u11_demo.py`로 저장해 Python 3.9 이상에서 실행한다. 운영 계정을 읽거나 변경하지 않고, 코드 안의 가상 자료만 처리한다. `targets`에는 담당자 확인을 거쳐 **로그인이 불필요하다고 정한 계정**만 넣는다.

이 예제는 계정 이름과 셸만 결과에 남긴다. 비밀번호 필드·사용자 설명·홈 경로는 출력하지 않는다. 빈 자료, 잘못된 필드, 중복 이름, 누락 계정을 오류로 처리해 조사 실패가 ‘문제 없음’에 섞이지 않게 했다. 계정명·숫자·셸 경로의 허용 형식은 이 작은 예제의 입력 규칙이며 모든 Unix 형식을 지원하지는 않는다.

[[download]]

```python
import json
import re

RESTRICTED = {
    "/bin/false", "/usr/bin/false",
    "/sbin/nologin", "/usr/sbin/nologin",
}
NAME = re.compile(r"[a-z_][a-z0-9_-]{0,31}\$?")
SHELL = re.compile(r"/[A-Za-z0-9_./+-]+")


def inspect(text, targets):
    if not text.strip() or len(text.encode("utf-8")) > 4 * 1024 * 1024:
        raise ValueError("빈 자료 또는 입력 크기 초과")
    if not targets or any(not NAME.fullmatch(x) for x in targets):
        raise ValueError("조사 대상 계정 이름 확인 필요")
    accounts = {}
    for line in text.splitlines():
        if not line:
            continue
        fields = line.split(":")
        if len(fields) != 7 or not NAME.fullmatch(fields[0]):
            raise ValueError("계정 자료 형식 오류")
        name, _, uid, gid, _, _, shell = fields
        if name in accounts:
            raise ValueError("중복 계정 이름")
        for value in (uid, gid):
            if not re.fullmatch(r"[0-9]{1,10}", value) or int(value) > 4294967294:
                raise ValueError("UID 또는 GID 형식 오류")
        if shell and not SHELL.fullmatch(shell):
            raise ValueError("이 예제가 지원하지 않는 셸 경로")
        accounts[name] = shell
    if set(targets) - accounts.keys():
        raise ValueError("조사 대상 계정 누락")
    return [
        {"계정": name, "셸": accounts[name] or "(빈 값: 기본 셸 확인)",
         "검토 필요": accounts[name] not in RESTRICTED}
        for name in sorted(set(targets))
    ]


if __name__ == "__main__":
    fixture = (
        "root:x:0:0::/root:/bin/bash\n"
        "daemon:x:1:1::/usr/sbin:/usr/sbin/nologin\n"
        "svc_report:x:1500:1500::/srv/report:/bin/bash\n"
    )
    targets = {"daemon", "svc_report"}
    result = inspect(fixture, targets)
    assert [x["계정"] for x in result if x["검토 필요"]] == ["svc_report"]
    print(json.dumps(result, ensure_ascii=False, indent=2))

    restricted = fixture.replace("/srv/report:/bin/bash", "/srv/report:/bin/false")
    assert not any(x["검토 필요"] for x in inspect(restricted, targets))
    print("제한용 셸로 바꾼 가상 자료: 검토 후보 0개")

    empty_shell = fixture.replace("/srv/report:/bin/bash", "/srv/report:")
    assert any(x["검토 필요"] for x in inspect(empty_shell, targets))
    print("빈 셸: 검토 후보로 유지")

    error_cases = [
        ("필드 오류", "daemon:x:1:1", {"daemon"}),
        ("중복 이름", fixture + fixture.splitlines()[1] + "\n", targets),
        ("대상 누락", fixture, {"missing_service"}),
    ]
    for label, data, selected in error_cases:
        try:
            inspect(data, selected)
        except ValueError:
            print(f"{label}: 오류로 구분")
        else:
            raise AssertionError(f"{label} 검증 실패")
```

ZIP에 들어 있는 `check_u11_demo.py` 파일을 사용한다. 파일을 저장한 폴더에서 `python3 -I -B check_u11_demo.py`로 실행한다. Windows에서는 같은 Python 옵션과 함께 명령 이름을 `python`으로 바꾼다. passwd 파일이나 `/srv/report` 디렉터리를 만들 필요는 없다. `fixture` 안의 각 행이 입력 데이터이며 홈 경로는 문자열로만 사용한다. 코드는 가상 자료의 셸 문자열을 분류하므로 제한용 셸 파일의 존재 여부나 실제 로그인 차단은 검사하지 않는다. 출력에는 후보 계정과 제한용 셸·빈 셸·입력 오류를 비교한 결과가 남는다.

`inspect()`는 입력 전체를 먼저 검증한 뒤 조사 대상 이름이 빠졌는지 검사한다. 반환 목록에서는 `accounts[name] not in RESTRICTED`의 참·거짓이 ‘검토 필요’ 값이 된다. 빈 셸은 안내 문구로 표시하면서도 제한용 셸 집합에는 없으므로 후보로 남는다.

첫 자료에서는 `svc_report`만 검토 후보가 된다. `root`는 조사 대상으로 지정하지 않았기 때문에 결과에 포함되지 않는다. 가상 자료의 셸 문자열을 바꾼 뒤 후보가 사라지는 것은 비교 로직의 결과이며, 서버의 U-11 양호 판정이 아니다.

[[run:1]]

JSON 뒤의 ‘검토 후보 0개’는 가상 문자열을 `/bin/false`로 바꾼 두 번째 대조다. 이어지는 세 오류 안내는 각 잘못된 입력에서 `ValueError`가 발생해 예외 처리 분기에 들어갔다는 뜻이다. 코드가 오류를 놓치면 `AssertionError`로 중단한다. 기록의 종료 코드 `0`은 이 검증들이 끝났다는 뜻이며 모든 계정의 셸이 적합하다는 판정이 아니다. `-O`는 assert 검사를 없애므로 이 예제를 재현할 때는 사용하지 않는다.

## 조치 전에는 서비스 실행 방식을 확인한다

운영 자료에서는 로컬 파일에 있는 계정뿐 아니라 LDAP·AD 등 중앙 계정의 조회 범위도 확인한다. 전체 계정 열거가 지원되지 않는 환경에서는 승인된 명단을 이름별로 조회하고, 조회 실패와 계정 부재를 구분해 남긴다. 원본 계정 자료를 공개 게시물이나 외부 보고서에 그대로 붙이지 않는다.

로그인이 불필요한 계정이라고 확인되면 현재 셸과 서비스 설정을 기록하고 변경 영향을 검토한다. 예를 들어 `su - 계정 -c 명령`처럼 로그인 셸을 통해 시작하는 작업은 셸 변경으로 실패할 수 있다. 서비스가 다른 실행 방식을 쓰더라도 재시작·배치·백업까지 확인해야 한다.

Linux의 `usermod -s /usr/sbin/nologin 계정명` 같은 변경은 경로를 확인한 뒤 승인된 시간에 수행한다. 이 글의 실습에서는 실행하지 않았다. 다른 Unix는 해당 운영체제의 계정 관리 절차를 따른다. 실패할 때 복구할 기존 셸 값과 작업 담당자를 함께 남긴다.

변경한 셸이 계정 조회에 나타나는지 살피고, 제한하려던 경로로 로그인을 시험한다. 서비스 재시작과 예약 작업도 실행해 업무 영향을 확인한다. 결과에는 계정 용도, 변경 전후의 셸과 남은 예외를 함께 적는다.

## 참고 자료

- [KISA 2026 상세가이드, U-11, 35쪽](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [passwd(5): 계정 필드와 빈 로그인 셸](https://man7.org/linux/man-pages/man5/passwd.5.html)
- [nologin(8): 동작과 적용 범위](https://man7.org/linux/man-pages/man8/nologin.8.html)
