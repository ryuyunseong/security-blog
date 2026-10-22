---
title: "U-16: /etc/passwd 파일 소유자 및 권한 설정"
description: "root 소유 여부와 0644 권한 비트를 대조합니다. 가상 UID·모드 다섯 가지로 숫자 대소 비교가 놓치는 쓰기 권한을 실행해 봅니다."
date: "2026-10-21T18:52:52+09:00"
updated: "2026-10-22"
sourcesChecked: "2026-10-21"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-16", "파일권한", "Linux"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 16
---

`/etc/passwd`의 권한이 `0606`이라면 `0644`보다 안전할까? 숫자로만 비교하면 더 작지만, 마지막 자리의 `6`에는 기타 사용자의 쓰기 권한이 들어 있다. U-16은 파일 소유자와 허용한 권한 비트를 각각 대조해야 한다.

## 가이드가 요구하는 소유자와 권한

2026 KISA 상세가이드 41쪽의 U-16은 중요도 ‘상’이며 Solaris·Linux·AIX·HP-UX 등을 대상으로 한다. 양호 조건은 `/etc/passwd`의 소유자가 root이고 권한이 `644` 이하인 경우다. 소유자가 다르거나 권한 조건을 벗어나면 취약으로 판단한다.

이 파일에는 계정 이름, UID·GID, 홈 디렉터리와 로그인 셸 같은 정보가 담긴다. 내용을 바꿀 수 있는 사용자는 계정의 속성을 변조할 수 있으므로, 읽을 수 있는 범위와 쓸 수 있는 범위를 구별한다. 비밀번호 해시를 별도 파일로 옮기는 [U-04의 비밀번호 파일 보호](../u-04-password-file/)와는 점검 대상이 다르다.

root 소유 여부는 표시된 이름과 숫자 UID를 함께 수집한다. Linux에서 root의 UID는 0이다. 소유 그룹 이름은 수집 자료에 남길 수 있지만, 원문의 U-16 양호 조건에 특정 그룹 이름이 별도로 지정되어 있지는 않다.

## ‘644 이하’를 비트로 비교하기

`0644`를 나누면 소유자 `rw-`, 그룹 `r--`, 기타 사용자 `r--`다. `0640`이나 `0600`은 이 비트의 일부를 제거한 형태다. 반면 `0606`은 숫자는 작아도 원래 허용하지 않은 기타 쓰기 비트를 추가한 값이다.

일반 권한 9비트에서 허용 범위 밖의 비트는 `mode & (~0o644 & 0o777)`로 구할 수 있다. 결과가 0인지와 소유자 UID가 0인지를 별도로 판단한다. 읽기 권한을 더 제한하면 일반 계정의 사용자 정보 조회에 영향을 줄 수 있으므로, 기준 대조와 서비스 동작 시험도 구분한다.

[[diagram]]

아래 실습은 이 비교를 가상 UID와 모드 목록에 적용한다. 실제 `/etc/passwd`를 읽거나 `chmod`·`chown`을 실행하지 않는다. ACL과 특수 권한 비트는 이 9비트 모델에 포함하지 않고 별도 조사 대상으로 둔다.

## 가상 속성 다섯 가지를 실행해 비교하기

Python 3 표준 기능만 사용한다. ZIP을 풀고 `u16_passwd_mode.py`가 있는 폴더에서 `python -I -B -X utf8 u16_passwd_mode.py`로 실행한다. Linux·WSL에서는 명령 이름을 `python3`로 바꿀 수 있다.

[[download]]

```python
ALLOWED = 0o644
CASES = (
    ("기준 설정", 0, 0o644),
    ("그룹 쓰기 추가", 0, 0o664),
    ("소유자 다름", 1001, 0o644),
    ("숫자 비교 함정", 0, 0o606),
    ("소유자만 읽기·쓰기", 0, 0o600),
)


def inspect(uid, mode):
    # 가상 자료의 일반 권한 9비트만 비교한다.
    if not isinstance(uid, int) or isinstance(uid, bool) or uid < 0:
        raise ValueError("UID는 0 이상의 정수여야 한다")
    if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o777:
        raise ValueError("이 예제는 일반 권한 0000~0777만 받는다")
    extra = mode & (~ALLOWED & 0o777)
    return uid == 0 and extra == 0, extra


expected = (True, False, False, False, True)
for (label, uid, mode), allowed in zip(CASES, expected):
    matches, extra = inspect(uid, mode)
    assert matches == allowed
    state = "충족" if matches else "불일치"
    print(f"{label}: UID={uid}, 모드={mode:04o}, 허용 밖 비트={extra:03o}, 기준 {state}")

assert 0o606 <= 0o644
assert inspect(0, 0o606) == (False, 0o002)
assert inspect(0, 0o640) == (True, 0)
assert inspect(0, 0o644) == (True, 0)
assert inspect(1, 0o600) == (False, 0)
try:
    inspect(0, 0o4644)
except ValueError:
    print("특수 비트가 있는 모드: 일반 권한 예제 범위 밖")
else:
    raise AssertionError("범위 밖 모드를 거부하지 않음")
print(f"0606 <= 0644 숫자 비교: {0o606 <= 0o644}")
print("0606에서 추가된 기타 쓰기 비트: 002")
```

`/etc/passwd`의 복사본이나 별도 파일 권한 준비는 필요하지 않다. `CASES`에 적힌 가상 UID·모드 숫자만 함수에 전달한다.

`inspect()`는 UID·모드가 정수인지 검사하면서 Python에서 정수의 하위 유형인 참·거짓 값은 제외한다. `~ALLOWED`를 `0o777`로 한정한 뒤 AND 연산을 하므로 일반 권한 9비트에서 허용하지 않은 비트만 남는다. 반환값은 ‘UID가 0이고 추가 비트가 없음’과 ‘추가된 비트 값’ 두 개다. `:04o`와 `:03o`는 결과를 8진수 자릿수에 맞춰 출력한다.

이 예제에서 `~ALLOWED & 0o777`은 `0o133`이다. `0606`을 대입하면 `0o606 & 0o133`이 `0o002`가 되어 기타 쓰기 비트가 남는다. UID가 0이어도 추가 비트가 0이 아니므로 최종 참·거짓 값은 거짓이다. 숫자 대소 비교 대신 허용하지 않은 비트가 무엇인지 찾는 계산이다.

`그룹 쓰기 추가`는 `020`, `숫자 비교 함정`은 `002`가 허용 범위 밖에 남는다. `소유자 다름`은 모드가 기준과 같아도 UID 조건을 충족하지 못한다.

[[run:1]]

`기준 설정`과 `소유자만 읽기·쓰기`는 둘 다 허용 밖 비트가 0이고 UID도 0이다. 별도로 넣은 `04644`는 허용 범위 `0000~0777`을 벗어나 `ValueError`가 나며, 이를 잡은 분기가 ‘일반 권한 예제 범위 밖’을 출력한다. 이 예외를 잡고 다른 assert 비교도 통과했기 때문에 프로그램의 종료 코드는 `0`이다. 특수 비트가 적합하다는 판정은 하지 않는다. `-O`로 assert 검사를 끄지 않고 실행한다.

마지막 숫자 비교는 True지만, 비트 비교에서는 `0606`이 불일치로 나왔다. 이 출력은 예제의 가상 속성을 비교한 결과이며 실행한 컴퓨터의 `/etc/passwd` 상태를 뜻하지 않는다.

## 실제 점검 자료와 조치 범위

운영체제에 맞는 파일 속성 조회 명령으로 실제 소유자, 숫자 UID, 모드를 수집한다. Linux에서는 `stat -c '%U %u %a %n' -- /etc/passwd`처럼 함께 표시할 수 있다. 경로가 심볼릭 링크라면 링크 자체와 실제 대상 파일을 구별해 조사하고, 확장 ACL이 있다면 모드 숫자 외에 허용된 사용자·그룹도 살핀다.

원문 조치 사례는 root로 소유자를 맞추고 `644` 권한을 설정하는 방식이다. 실제 변경 전에 현재 소유자·권한과 파일 관리 주체를 기록하고, 구성 관리나 배포 절차가 값을 다시 바꾸는지도 조사한다. 파일 내용의 정상 여부와 쓰기 권한 문제는 별도로 검토해야 한다.

변경 후에는 소유자와 권한을 다시 수집하고, 일반 계정의 사용자 이름 조회와 필요한 서비스 동작을 시험한다. 권한을 좁혔다는 이유만으로 접근 오류를 조사 대상에서 제외하지 않는다.

## 참고 자료

- [KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드, U-16, 41쪽](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux passwd(5): 계정 정보 파일과 읽기·쓰기 권한](https://man7.org/linux/man-pages/man5/passwd.5.html)
- [Linux stat(2): 파일의 UID와 모드 속성](https://man7.org/linux/man-pages/man2/stat.2.html)
