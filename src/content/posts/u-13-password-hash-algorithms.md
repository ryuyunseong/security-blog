---
title: "U-13: 안전한 비밀번호 암호화 알고리즘 사용"
description: "새 비밀번호의 해시 정책과 기존 계정의 저장 형식을 나눠 점검하고, 가상 필드에서 잠금과 알고리즘을 분류합니다."
date: "2026-10-18T12:14:00+09:00"
updated: "2026-10-22"
sourcesChecked: "2026-10-18"
category: "critical-infrastructure"
tags: ["주통기","U-13","비밀번호","PAM","해시"]
draft: false
example: false
assessmentTarget: "unix"
series: "unix-2026"
seriesOrder: 13
---

`ENCRYPT_METHOD SHA512`로 설정을 바꿔도 기존 계정의 해시가 한꺼번에 SHA-512로 바뀌지는 않는다. U-13에서는 새 비밀번호를 저장할 때의 정책과 이미 저장된 계정별 해시 형식을 함께 점검한다.

2026 KISA 상세가이드의 U-13은 중요도 ‘중’이며 Solaris·Linux·AIX·HP-UX 등을 대상으로 한다. SHA-2 이상의 안전한 비밀번호 암호화 알고리즘을 사용하면 양호, 취약한 알고리즘을 사용하면 취약으로 판단한다. 원문 37~38쪽은 설정 변경 후에도 해당 계정의 비밀번호를 재설정해야 새 방식이 적용된다고 설명한다.

## 저장된 형식과 새 비밀번호의 정책을 대조한다

Linux의 로컬 계정에서는 저장된 비밀번호 필드의 접두부로 알고리즘을 분류할 수 있다. 가이드는 `$1$`을 MD5, `$5$`를 SHA-256, `$6$`을 SHA-512로 설명한다. 여기서 SHA-512는 비밀번호 저장에 쓰이는 crypt 형식을 가리킨다. 애플리케이션에서 비밀번호에 `hashlib.sha512()`를 한 번 적용하는 구현으로 대체하라는 뜻이 아니다.

비밀번호 변경 설정과 기존 계정의 저장 형식을 대조한다. 정책이 SHA512여도 오래된 `$1$` 값이 남아 있다면 전환 대상이다. `$6$` 값이 있는 계정도 설정의 적용 경로, 지원 방식과 계정 상태를 함께 살펴야 한다.

잠금 표시는 해시 형식과 구분해 읽는다. Linux shadow 필드에서 `!` 앞머리는 비밀번호 잠금과 관련된 값이고, 그 뒤에 기존 해시가 남을 수 있다. 잠겼다는 이유로 뒤의 MD5 저장값을 분류에서 누락하면 추후 계정을 다시 사용할 때 전환 대상을 놓친다. 빈 필드와 `*`처럼 사용할 수 있는 해시가 없는 값도 SHA-2로 계산해서는 안 된다. 로그인 가능 여부는 이 필드 외의 인증 설정에도 영향을 받는다.

[[diagram]]

## 배포판이 읽는 설정을 먼저 찾는다

가이드의 Red Hat 계열 사례는 `/etc/login.defs`의 `ENCRYPT_METHOD`와 `/etc/pam.d/system-auth`의 `pam_unix.so`를 함께 다룬다. Debian 계열은 `/etc/pam.d/common-password`를 제시하며 SHA-256·SHA-512 외에 yescrypt도 안내한다. 서로 다른 배포판의 파일 경로를 그대로 섞어 적용하지 않는다.

Linux-PAM의 `pam_unix(8)` 매뉴얼은 비밀번호 변경 시 해시를 만들며 `sha512`·`yescrypt` 옵션은 시스템의 `crypt` 구현이 지원해야 한다고 설명한다. `login.defs` 한 줄을 읽는 데서 멈추지 말고 비밀번호 변경에 쓰이는 PAM 스택, 모듈 옵션, 배포판의 설정 관리 방식을 조사한다. 중앙 인증을 쓰는 계정은 로컬 shadow에 해시가 없을 수 있으므로 로컬 계정 결과와 따로 기록한다.

아래 표는 가이드의 운영체제별 조사 위치를 정리한 것이다. 실제 점검에서는 대상 OS의 버전과 저장 구성에 맞춰 경로를 정한다.

| 대상 | 저장값·설정을 조사할 위치 | 구분할 부분 |
| --- | --- | --- |
| Solaris | 계정의 암호화 필드, `/etc/security/policy.conf` | 가이드의 `CRYPT_DEFAULT=5` 또는 `6` 사례 |
| Linux | `/etc/shadow` 등의 계정 필드, `login.defs`, 사용 중인 PAM 파일 | 새 비밀번호 정책과 기존 계정의 형식 |
| AIX | `/etc/security/passwd`, `/etc/security/login.cfg` | `{알고리즘}` 형식과 `pwd_algorithm`; 지원 이름은 `pwdalg.cfg`에서 조회 |
| HP-UX | `/etc/shadow`, `/etc/default/security` | OS 버전·비밀번호 저장 구성과 `CRYPT_DEFAULT` 적용 조건 |

표는 공통 명령 하나로 모든 OS를 판정할 수 있다는 뜻이 아니다. 특히 AIX의 `{알고리즘}` 표기를 Linux의 `$번호$` 규칙으로 해석하면 형식을 잘못 읽게 된다. HP-UX 역시 11i v2 이상 여부와 shadow 등 저장 구성을 원문 사례 및 해당 버전 문서와 대조한다.

## 가상 필드에서 잠금과 알고리즘을 따로 추출한다

다음 코드를 `u13_hash_format.py`로 저장하고 `python -I -B u13_hash_format.py`로 실행한다. 실제 계정 파일을 열지 않고 문자열만 분류한다. `DEMO`와 `salt`는 형식 설명용 글자이며 유효한 비밀번호 해시가 아니다. 비밀번호 검증이나 복호화, 계정의 양호·취약 자동 판정을 수행하지 않는다.

[[download]]

```python
ALGORITHMS = {"1": "MD5-crypt", "5": "SHA256-crypt", "6": "SHA512-crypt"}


def classify(field):
    locked = field.startswith("!")
    value = field.lstrip("!")
    if not field:
        return locked, "빈 필드"
    if not value or value == "*":
        return locked, "사용할 해시 없음"
    parts = value.split("$")
    if value.startswith("$") and len(parts) >= 4:
        return locked, ALGORITHMS.get(parts[1], "대상별 해석 필요")
    return locked, "대상별 해석 필요"


samples = {
    "old": "$1$salt$DEMO",
    "locked_old": "!$1$salt$DEMO",
    "new": "$6$salt$DEMO",
    "sha256": "$5$salt$DEMO",
    "platform": "{OTHER}DEMO",
    "empty": "",
    "disabled": "*",
}
before = samples.copy()
new_password_policy = "SHA512"
assert classify(samples["locked_old"]) == (True, "MD5-crypt")
assert classify(samples["new"]) == (False, "SHA512-crypt")
assert classify(samples["platform"])[1] == "대상별 해석 필요"
assert classify(samples["empty"])[1] == "빈 필드"
assert classify("!!") == (True, "사용할 해시 없음")
assert samples == before

print(f"새 비밀번호 정책(가정): {new_password_policy}")
for name, field in samples.items():
    locked, algorithm = classify(field)
    lock_text = "있음" if locked else "없음"
    print(f"{name}: 잠금 접두부={lock_text}, 형식={algorithm}")
print("정책 변수 지정 후 기존 필드: 변경 없음")
```

Python 3 표준 기능만 사용한다. ZIP을 푼 폴더에서 위 명령을 실행하고, Linux·WSL에서는 `python` 대신 `python3`를 사용할 수 있다. `/etc/shadow`나 별도 salt 파일은 준비하지 않는다. 입력은 `samples`의 가상 문자열에 모두 들어 있다.

`classify()`는 원본이 `!`로 시작하는지를 `locked`에 보관한 뒤 `lstrip("!")`로 잠금 접두부를 제거한다. `!$1$salt$DEMO`는 이 단계에서 `$1$salt$DEMO`가 된다. 이어 `$`로 나눈 `parts[1]`의 `1`을 `ALGORITHMS`에서 찾아 MD5-crypt로 분류한다. 잠금 여부를 먼저 보관했으므로 형식을 읽고 나서도 두 정보를 함께 출력할 수 있다.

빈 필드·`*`·`!!`는 빈 값 또는 사용할 해시가 없는 경우로 구분한다. `{OTHER}DEMO`는 이 접두부 표로 해석하지 않고 ‘대상별 해석 필요’로 남긴다. salt와 뒤의 본문이 유효한 해시인지까지 검사하는 함수는 아니다.

[[run:1]]

실행 결과의 `locked_old`에는 잠금과 MD5-crypt가 함께 표시되고, `new`와 `sha256`에는 각각 SHA512-crypt와 SHA256-crypt가 나온다. `new`는 가상 입력의 이름이며 이 코드가 새 비밀번호를 생성한 것은 아니다.

첫 줄의 `new_password_policy`는 출력용 변수다. `samples`를 수정하는 코드가 없고 `before`와의 비교도 통과했으므로 마지막 줄이 ‘변경 없음’이다. 다른 `assert`도 통과해 종료 코드 `0`으로 끝났다. 검사를 유지하려면 Python의 `-O` 옵션을 붙이지 않는다. PAM의 알고리즘 선택과 새 비밀번호 저장은 해당 OS의 시험 계정에서 별도로 검증해야 한다.

## 전환 후에는 새 저장값을 다시 수집한다

취약한 형식의 계정이 발견되면 비밀번호 변경 시점과 서비스 의존성을 먼저 정리한다. 배치나 서비스에 연결된 계정은 인증 정보 교체가 업무에 영향을 줄 수 있다. 시스템 전체 설정과 계정별 재설정을 같은 작업으로 취급하지 말고 적용 순서와 시험 방법을 정한다.

승인된 시험 계정에서 비밀번호를 변경한 뒤 새 해시 형식과 정상 인증을 대조한다. 기존 계정은 재설정이 끝난 대상과 아직 옛 형식이 남은 대상을 구분한다. 점검 기록에는 OS·버전, 설정 경로와 유효값, 계정 용도별 형식 분포를 남기고 비밀번호 필드 전체나 해시 원문을 붙이지 않는다. 전환이 끝났다는 근거는 설정 파일의 한 줄보다 재설정 뒤 수집한 계정별 형식에 있다.

## 참고 자료

- [KISA 2026 주요정보통신기반시설 상세가이드: U-13, 37~38쪽](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux-PAM pam_unix(8): 비밀번호 변경과 해시 옵션](https://man7.org/linux/man-pages/man8/pam_unix.8.html)
- [shadow(5): 비밀번호 필드의 잠금 표시와 빈값](https://man7.org/linux/man-pages/man5/shadow.5.html)
