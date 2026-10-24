---
title: "U-19: /etc/hosts 파일 소유자 및 권한 설정"
description: "hosts 파일을 누가 바꿀 수 있는지 소유자·권한·ACL로 나눠 살펴봅니다. 가상 JSON 자료를 읽는 Python 예제로 0644와 0624의 차이를 비교합니다."
date: "2026-10-24T18:36:50+09:00"
sourcesChecked: "2026-10-24"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-19", "Unix", "hosts", "파일권한"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 19
---

`/etc/hosts`에는 IP 주소와 호스트 이름의 대응 관계가 들어 있다. 파일을 바꿀 수 있는 사용자는 이름이 가리키는 주소도 바꿀 수 있다. U-19에서 중점적으로 볼 부분은 파일의 공개 여부보다 **변경할 수 있는 주체**다.

예를 들어 `0644`는 일반 사용자에게 읽기를 허용하지만 쓰기는 소유자에게만 허용한다. 소유자가 root라면 이 조합은 U-19의 기준에 맞는다. 비밀번호 정보를 담아 읽기까지 제한하는 [U-18의 shadow 파일](../u-18-shadow-owner-permissions/)과 보호 조건이 다르다.

## 이름 조회와 파일 변경 권한

[hosts(5)](https://man7.org/linux/man-pages/man5/hosts.5.html)의 한 행은 IP 주소, 정식 호스트 이름, 선택적인 별칭 순서다. 이 글에서는 주소 변조나 실제 접속을 실습하지 않고 파일 접근 조건을 다룬다.

Linux에서 hosts 파일과 DNS의 조회 순서는 `/etc/nsswitch.conf`의 `hosts:` 설정과 조회에 사용하는 라이브러리·애플리케이션에 영향을 받는다. [nsswitch.conf(5)](https://man7.org/linux/man-pages/man5/nsswitch.conf.5.html)는 정보의 출처와 조회 순서를 설명한다. 모든 프로그램이 항상 hosts 파일을 먼저 읽는다고 전제하지 않는다.

2026 KISA 상세가이드 45쪽에서 U-19의 중요도는 ‘상’, 대상은 Solaris·Linux·AIX·HP-UX 등이다. `/etc/hosts`의 소유자가 root이고 권한이 `644` 이하이면 양호, 소유자가 root가 아니거나 권한 조건을 벗어나면 취약으로 판단한다. 권한 숫자는 8진수 표기다.

## 0624도 그룹 쓰기를 허용한다

`0644`를 소유자·그룹·기타 사용자로 나누면 `rw- r-- r--`다. root의 쓰기는 파일을 관리하기 위해 남겨 두고 그룹·기타 쓰기와 실행 비트는 허용하지 않는다. 파일 소유자를 일반 계정으로 바꾸면 같은 `0644`에서도 그 계정이 내용을 쓸 수 있다.

[[diagram]]

권한 문자열을 정수로만 비교하면 `0624`가 `0644`보다 작아서 통과할 수 있다. 그러나 가운데 `2`는 그룹 쓰기 비트다. ‘이하’는 허용 비트의 부분집합으로 비교하고 소유자 조건을 따로 대조해야 한다.

일반 모드가 기준에 맞아도 추가 ACL이 있거나 파일이 링크라면 더 살필 자료가 있다. 링크는 대상 파일과 경로를, ACL은 실제 항목과 유효 권한을 수집한다. 상위 디렉터리에서 파일을 교체할 수 있는 사용자도 검토 대상이다. 모드 숫자만으로 이 접근 조건을 모두 설명할 수는 없다.

## 가상 수집 자료를 JSON으로 읽기

실습에는 Python 3.9 이상과 표준 라이브러리를 사용한다. ZIP을 빈 폴더에 풀면 `u19_hosts_records.py`와 `u19_hosts_samples.json`이 함께 나온다. 두 파일이 있는 폴더에서 다음 명령을 실행한다. Windows에서는 `python`, Linux·WSL에서는 `python3`를 사용할 수 있다.

입력 JSON은 준비된 가상 소유자·모드·파일 종류·ACL 상태다. 운영체제의 실제 파일 모드를 측정한 자료가 아니므로 Windows에서도 실행할 수 있다. 운영 hosts 파일을 읽거나 변경하지 않고 관리자 권한도 필요하지 않다.

[[download]]

```bash
python -I -B -X utf8 u19_hosts_records.py u19_hosts_samples.json
```

입력 파일의 전체 내용은 아래와 같다. ZIP을 사용했다면 이 파일을 다시 만들 필요가 없다. `mode`를 문자열로 둔 이유는 앞의 0과 8진수 표기를 보존하기 위해서다. `kind`와 `acl`도 실측값이 아닌 가상 상태다.

```json
[
  {"name": "기준 모드", "uid": 0, "mode": "0644", "kind": "file", "acl": "none"},
  {"name": "숫자는 작은 모드", "uid": 0, "mode": "0624", "kind": "file", "acl": "none"},
  {"name": "그룹 쓰기", "uid": 0, "mode": "0664", "kind": "file", "acl": "none"},
  {"name": "기타 쓰기", "uid": 0, "mode": "0646", "kind": "file", "acl": "none"},
  {"name": "소유자와 모드 차이", "uid": 1001, "mode": "0664", "kind": "file", "acl": "none"},
  {"name": "읽기 범위 축소", "uid": 0, "mode": "0600", "kind": "file", "acl": "none"},
  {"name": "추가 ACL", "uid": 0, "mode": "0644", "kind": "file", "acl": "present"},
  {"name": "심볼릭 링크", "uid": 0, "mode": "0644", "kind": "symlink", "acl": "unknown"}
]
```

프로그램은 입력 경로를 필수 인수로 받는다. 인수를 생략해도 실제 `/etc/hosts`로 넘어가지 않는다. 자료 전체의 형식을 검사한 다음 비교 결과를 출력한다.

```python
import argparse
import json
from pathlib import Path
import re
import sys


def validate(record):
    if not isinstance(record, dict):
        raise ValueError("각 항목은 객체여야 한다")
    if set(record) != {"name", "uid", "mode", "kind", "acl"}:
        raise ValueError("필드 이름 또는 필수 값 누락")
    if not isinstance(record["name"], str) or not record["name"].strip():
        raise ValueError("이름은 빈 문자열일 수 없다")
    if type(record["uid"]) is not int or record["uid"] < 0:
        raise ValueError("UID는 0 이상의 정수여야 한다")
    if not isinstance(record["mode"], str) or not re.fullmatch(r"[0-7]{4}", record["mode"]):
        raise ValueError("모드는 8진수 네 자리 문자열이어야 한다")
    if record["kind"] not in ("file", "symlink"):
        raise ValueError("파일 종류 오류")
    if record["acl"] not in ("none", "present", "unknown"):
        raise ValueError("ACL 상태 오류")


def review(record):
    if record["kind"] != "file":
        return None, ["링크 대상 조사"]
    mode = int(record["mode"], 8)
    if mode & 0o7000:
        return None, ["특수 비트 조사"]
    extra = mode & (~0o644 & 0o777)
    issues = []
    if record["uid"] != 0:
        issues.append("소유자 불일치")
    if extra:
        issues.append("허용 밖 권한")
    if record["acl"] != "none":
        issues.append("ACL 추가 조사")
    return extra, issues or ["소유자·일반 권한 조건 충족"]


def main():
    parser = argparse.ArgumentParser(description="가상 hosts 속성 JSON만 비교한다")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        records = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(records, list) or not records:
            raise ValueError("비어 있지 않은 배열이 필요하다")
        # 모든 입력을 검증한 뒤에 출력하므로 중간 성공 결과를 남기지 않는다.
        for record in records:
            validate(record)
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for record in records:
        extra, issues = review(record)
        bits = "비교 안 함" if extra is None else f"{extra:03o}"
        print(f"{record['name']}: UID={record['uid']}, 모드={record['mode']}, 추가 비트={bits}, {', '.join(issues)}")
    print(f"가상 자료 {len(records)}건 비교 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`validate()`는 필드 다섯 개와 값의 형식을 검사한다. UID에는 `true` 같은 불리언이 들어가지 않도록 `type(...) is int`를 사용했다. 누락된 필드를 임의의 정상 값으로 채우지 않는다. 모드는 8진수 네 자리 문자열이어야 하므로 `"0684"`는 입력 오류다.

`review()`는 링크를 만나면 대상 조사가 필요하다고 반환하고 모드 비교를 진행하지 않는다. 일반 파일이라도 `07000`의 특수 비트가 있으면 별도 조사로 남긴다. 그다음 `extra`에 `0644`에서 허용하지 않는 일반 권한만 모은다.

‘숫자는 작은 모드’ 행을 따라가 보자. `"0624"`는 `int(..., 8)`을 거쳐 8진수 값이 된다. `~0o644 & 0o777`로 만든 마스크와 AND 연산하면 그룹 쓰기 `020`이 남는다. UID는 0이므로 소유자 문제는 없고 ‘허용 밖 권한’이 `issues`에 추가된다.

`issues`를 목록으로 둔 것은 차이를 하나만 보고 끝내지 않기 위해서다. UID 1001·모드 `0664`인 행에서는 소유자 불일치와 허용 밖 권한을 함께 반환한다. ACL이 있거나 상태가 미수집이면 ‘ACL 추가 조사’를 덧붙인다.

[[run:1]]

기준 모드의 추가 비트는 `000`이고 ‘숫자는 작은 모드’와 ‘그룹 쓰기’는 모두 `020`, 기타 쓰기는 `002`다. `0600`도 추가 비트가 없지만 실제 환경에서 읽기 범위를 줄일 때는 해당 파일을 사용하는 서비스에 영향이 없는지 살펴야 한다. 기준이 허용하는 권한과 서비스에 필요한 권한을 함께 검토한다.

ACL 행은 일반 모드의 추가 비트가 `000`이어도 별도 조사가 남는다. 링크 행의 ‘비교 안 함’은 `000`과 다르다. 이 프로그램은 링크 대상을 열지 않으므로 대상을 검사한 결과로 해석하지 않는다.

마지막 줄의 8건은 형식이 맞는 가상 자료를 끝까지 비교한 건수다. 종료 코드 0은 비교 작업 완료를 뜻하며 모든 행이 양호하다는 뜻은 아니다. 파일을 읽지 못하거나 JSON·필드 형식이 잘못되면 표준 오류를 남기고 2로 끝난다. 인수 누락도 실행 오류다.

프로그램이 만드는 파일은 없다. JSON을 고쳐 다시 비교할 때도 실제 hosts 파일, 계정, 권한이나 ACL에는 영향을 주지 않는다. 운영 점검 기록에는 소유자 UID·일반 권한과 함께 ACL·링크·상위 경로를 조사한 자료를 붙인다.

## 참고 자료

- [KISA 주요정보통신기반시설 기술적 취약점 분석·평가 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1): 2026년, U-19, 45쪽
- [Linux hosts(5)](https://man7.org/linux/man-pages/man5/hosts.5.html)
- [Linux nsswitch.conf(5)](https://man7.org/linux/man-pages/man5/nsswitch.conf.5.html)
