---
title: "U-29: hosts.lpd 파일 소유자 및 권한 설정"
description: "hosts.lpd의 부재와 미수집을 구분하고 불가피한 사용·root 소유·600 이하 권한을 가상 자료로 비교합니다. 일반 권한 512개를 열거해 숫자 크기 비교와 비트 포함 관계의 차이를 재현합니다."
date: "2026-11-04T18:45:17+09:00"
sourcesChecked: "2026-11-04"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "파일 권한", "프린트 서비스", "KISA"]
draft: false
series: unix-2026
seriesOrder: 29
---

`hosts.lpd`가 없다는 수집 결과와 해당 파일의 자료를 받지 못한 상태는 다르다. U-29에는 파일이 존재하지 않는 경우의 양호 기준이 있으므로 이 둘을 같은 빈칸으로 처리하면 미수집 자료가 양호 쪽으로 섞인다. 아래 비교기는 처음부터 `absent`, `uncollected`, `present`를 별도 입력으로 받는다.

## 부재 자료에서 소유자 비교를 생략하는 이유

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-29는 ‘hosts.lpd 파일 소유자 및 권한 설정’이며 중요도는 ‘하’다. 항목표와 본문 61쪽의 제목·중요도가 같고 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다.

가이드는 `/etc/hosts.lpd`를 로컬 프린트 서비스를 사용할 수 있는 허가된 호스트·사용자 정보를 담는 파일로 설명한다. 양호 기준은 파일이 존재하지 않거나 불가피하게 사용할 때 소유자가 root이고 권한이 600 이하인 경우다. 파일이 존재하면서 root 소유가 아니거나 권한이 600 이하가 아니면 취약으로 구분한다. 조치 사례에는 파일 제거 또는 소유자·권한 변경이 나온다.

이 기준을 수집 자료에 대입할 때 파일 부재의 근거가 먼저 필요하다. 조회 오류나 누락된 자료를 부재로 변환하지 않고 파일이 있다면 사용 필요성과 소유자·권한을 이어서 조사한다.

[[diagram]]

그림의 분기는 수집 자료를 나누는 순서다. 실제 프린트 서비스의 파일 해석·인증 동작을 재현한 그림은 아니다. 사용하는 구현과 설정 경로를 조사한 뒤 그 경로에 대한 수집 시점·결과를 남긴다.

수집 상황을 다음처럼 가정하면 입력의 `state`를 나누는 기준이 드러난다.

- 부재 보고 자료가 있는 경우: 대상 `/etc/hosts.lpd`의 부재를 보고한 조회 자료가 있고 대상 경로와 수집 시점을 함께 알고 있다. `absent`로 입력하고 소유자·모드 비교를 생략한다.
- 조회가 권한 오류로 끝난 경우: 파일의 존재 여부를 알 수 없으므로 `uncollected`로 입력한다. 부재로 바꾸지 않고 보류한다.
- 수집 자료를 전달받지 못한 경우: 해당 경로의 자료가 없는 상태를 `uncollected`로 입력한다. 부재로 바꾸지 않고 보류한다.

`absent`에는 대상 경로와 수집 시점을 대조할 수 있는 부재 자료가 있다는 가정을 둔다. 아래 실습은 조회나 권한 오류를 직접 만들지 않고 이렇게 정리된 상태를 읽는다.

## 가상 자료 열 건을 비교하는 파일

실습에는 Python 3.9 이상과 표준 라이브러리만 필요하다. Windows Python 3.12.1에서 실행했으며 관리자 권한이나 별도 패키지는 사용하지 않았다. Unix의 UID·모드는 JSON에 적힌 가상 값으로만 계산하므로 Linux 파일시스템이나 실제 `/etc/hosts.lpd`를 준비할 필요가 없다. 계정·권한·프린트 서비스의 조회와 변경도 수행하지 않는다.

ZIP을 빈 폴더에 풀고 `u29_lpd_evidence.py`와 `u29_lpd_cases.json`이 함께 있는 글별 폴더에서 아래 명령을 실행한다. 포함된 JSON을 다시 만들지 않는다. 프로그램은 지정한 입력을 읽고 표준 출력으로 결과를 내며 결과 파일을 쓰지 않는다.

[[download]]

```bash
python -I -B -X utf8 u29_lpd_evidence.py cases u29_lpd_cases.json
```

명령 직후 PowerShell에서는 `$LASTEXITCODE`, Linux·WSL에서는 `echo $?`로 종료 코드를 읽는다. Linux·WSL에서 실행 파일 이름이 `python3`이면 그 이름을 사용한다. 직접 지정하는 입력 경로에 공백이 있으면 따옴표로 감싼다. 정리할 때는 자신이 압축을 푼 실습 폴더만 대상으로 삼는다.

ZIP README의 각 단계에는 PowerShell과 Bash용 코드 블록이 나란히 있다. 사용하는 셸의 블록 하나를 골라 실행한다. Python 명령은 같지만 PowerShell의 `$?`는 성공 여부를 뜻하므로 숫자 종료 코드는 `$LASTEXITCODE`로 읽는다.

`state`가 `present`일 때만 파일 종류 `kind`, 소유 UID `uid`, 네 자리 8진수 문자열 `mode`, 사용 필요성을 뜻하는 `required`를 받는다. `required: true`는 불가피한 사용을 뒷받침하는 자료가 있다는 가정이다. `false`는 불필요한 파일, `null`은 필요성 미수집을 나타낸다. 코드가 이 필요성을 직접 조사하지는 않는다.

```json
[
  {"id": "absent", "state": "absent"},
  {"id": "not-collected", "state": "uncollected"},
  {"id": "root-600", "state": "present", "kind": "regular", "uid": 0, "mode": "0600", "required": true},
  {"id": "root-400", "state": "present", "kind": "regular", "uid": 0, "mode": "0400", "required": true},
  {"id": "other-owner", "state": "present", "kind": "regular", "uid": 1001, "mode": "0600", "required": true},
  {"id": "numeric-trap", "state": "present", "kind": "regular", "uid": 0, "mode": "0477", "required": true},
  {"id": "special-bit", "state": "present", "kind": "regular", "uid": 0, "mode": "4600", "required": true},
  {"id": "need-unknown", "state": "present", "kind": "regular", "uid": 0, "mode": "0600", "required": null},
  {"id": "unneeded", "state": "present", "kind": "regular", "uid": 0, "mode": "0600", "required": false},
  {"id": "link", "state": "present", "kind": "symlink", "uid": 0, "mode": "0777", "required": true}
]
```

`absent`와 `uncollected`에는 소유자·모드를 넣지 않는다. 없는 파일에 임의의 UID 0이나 모드 0000을 채워 넣어 기본 조건을 통과시키는 입력을 막기 위해서다. 전체 코드는 다음과 같다.

```python
import argparse
import json
import re
import sys
from pathlib import Path


def load_cases(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("비어 있지 않은 사례 목록이 필요하다")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("각 사례는 객체여야 한다")
        name = row.get("id")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]+", name):
            raise ValueError("사례 이름은 영문 소문자·숫자·하이픈만 받는다")
        if name in seen:
            raise ValueError("사례 이름이 중복됐다")
        seen.add(name)
        state = row.get("state")
        fields = {"id", "state"}
        if state == "present":
            fields |= {"kind", "uid", "mode", "required"}
            if row.get("kind") not in ("regular", "symlink"):
                raise ValueError("kind는 regular 또는 symlink여야 한다")
            if type(row.get("uid")) is not int or row["uid"] < 0:
                raise ValueError("uid는 0 이상의 정수여야 한다")
            if not isinstance(row.get("mode"), str) or not re.fullmatch(r"[0-7]{4}", row["mode"]):
                raise ValueError("mode는 네 자리 8진수 문자열이어야 한다")
            if row.get("required") is not None and type(row["required"]) is not bool:
                raise ValueError("required는 true·false·null만 받는다")
        elif state not in ("absent", "uncollected"):
            raise ValueError("state는 absent·uncollected·present만 받는다")
        if set(row) != fields:
            raise ValueError("상태에 필요한 필드만 정확히 지정한다")
    return rows


def compare(row):
    if row["state"] == "uncollected":
        return "보류: 부재로 바꾸지 않음"
    if row["state"] == "absent":
        return "부재 자료: 소유자·모드 비교 생략"
    if row["kind"] != "regular":
        return "보류: 링크와 대상 별도 조사"
    mode = int(row["mode"], 8)
    extra = mode & (0o777 & ~0o600)
    special = mode & 0o7000
    notes = []
    if row["required"] is None:
        notes.append("사용 필요성 미수집")
    elif row["required"] is False:
        notes.append("불필요한 파일의 제거 검토")
    if row["uid"] != 0:
        notes.append("root 소유 아님")
    if extra:
        notes.append(f"600 밖의 일반 권한={extra:03o}")
    if special:
        notes.append(f"특수 비트={special:04o}, 별도 조사")
    result = "; ".join(notes) if notes else "입력된 기본 조건 일치"
    return f"UID={row['uid']}, mode={mode:04o}: {result}"


def enumerate_modes():
    modes = range(0o1000)
    numeric = {m for m in modes if m <= 0o600}
    subset = {m for m in modes if m & (0o777 & ~0o600) == 0}
    print(f"일반 권한 0000~0777: {len(modes)}개")
    print(f"숫자 크기 0600 이하: {len(numeric)}개")
    print(f"600 밖의 일반 권한 없음: {len(subset)}개")
    print("비트 조건 목록: " + ", ".join(f"{m:04o}" for m in sorted(subset)))
    print(f"숫자 비교만 통과한 모드: {len(numeric - subset)}개")
    print(f"0477의 초과 비트: {0o477 & (0o777 & ~0o600):03o}")


def main():
    parser = argparse.ArgumentParser(description="가상 hosts.lpd 수집 자료 비교")
    parser.add_argument("task", choices=("cases", "modes"))
    parser.add_argument("fixture", nargs="?")
    args = parser.parse_args()
    try:
        if args.task == "modes":
            if args.fixture is not None:
                raise ValueError("modes에는 입력 파일을 주지 않는다")
            enumerate_modes()
        else:
            if args.fixture is None:
                raise ValueError("cases에는 JSON 파일 경로가 필요하다")
            rows = load_cases(args.fixture)
            for row in rows:
                print(f"{row['id']}: {compare(row)}")
            print(f"가상 자료 {len(rows)}건 비교 완료")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"입력 오류: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`load_cases()`는 모든 행을 검사한 뒤 `rows`를 반환한다. UID에서 불리언을 배제하려고 `type(...) is int`를 쓰고 `mode`는 0~7로 된 네 글자만 받는다. 필요한 필드 집합 `fields`와 실제 키가 다르면 입력 오류가 된다. 뒤쪽 행이 잘못됐어도 앞쪽 행의 결과를 먼저 출력하지 않는다.

`compare()`는 `uncollected`를 보류로 반환하고 `absent`에서는 소유자·모드 비교를 생략한다. 존재하는 자료 중 `symlink`는 링크와 대상의 별도 조사로 돌려보낸다. 일반 파일에 대해서만 사용 필요성·UID·모드를 비교하며 발견한 차이는 `notes`에 계속 쌓아 한 줄로 출력한다.

첫 명령에서 `cases`는 `args.task`, `u29_lpd_cases.json`은 `args.fixture`에 들어간다. `main()`은 `else`에서 `load_cases(args.fixture)`를 호출한다. 열 행의 검사가 끝나면 반환된 `rows`를 `for row in rows`로 순회한다. 두 번째 명령의 `modes`는 앞의 `if`에서 `enumerate_modes()`를 호출하므로 JSON 파일을 읽지 않는다.

첫 명령의 `numeric-trap` 행을 따라가면 `state`가 `present`이고 `kind`가 `regular`라 앞의 세 반환 분기를 지난다. `"0477"`은 `int(row["mode"], 8)`에서 `mode = 0o477`로 바뀌고 마스크 계산 뒤 `extra`는 `0o077`, `special`은 `0`이 된다. `required`가 `true`이고 UID가 `0`이라 필요성·소유자 차이는 추가되지 않는다. `notes`에는 초과 일반 권한 한 항목만 남고 `result`가 그 문구를 받는다.

`compare()`는 UID·모드·비교 문구를 반환한다. 바깥 `print()`가 그 앞에 사례 이름을 붙이면 `numeric-trap: UID=0, mode=0477: 600 밖의 일반 권한=077`이 된다. 아래 실제 출력의 같은 행과 대응하며 초과 비트를 만드는 산식은 다음 절에서 풀어 쓴다.

[[run:1]]

`root-600`과 `root-400`은 입력된 기본 조건이 일치했다. `other-owner`는 같은 `0600`이어도 UID 1001이 0이 아니어서 소유자 차이를 표시한다. `need-unknown`은 UID·모드가 같지만 `required`가 `null`이라 사용 필요성 미수집으로 남는다. `unneeded`의 제거 검토는 가상 자료의 분류이며 프로그램이 파일을 지우는 동작은 없다.

`special-bit`의 `4600`은 일반 권한 부분이 `0600`이고 특수 비트가 `4000`이다. 코드는 이 값을 `special`로 분리해 별도 조사로 표시한다. 링크 행도 모드 비교 전에 반환하므로 링크의 모드를 대상 파일의 권한으로 간주하지 않는다. 이 예제는 실제 링크를 만들거나 따라가지 않는다.

## 0477이 숫자 비교를 통과하는 이유

`numeric-trap`의 `"0477"`은 `int(..., 8)`을 거쳐 8진수 `0o477`이 된다. 이 수는 `0o600`보다 작지만 그룹·기타 사용자의 권한이 들어 있다. 일반 권한에서 소유자의 읽기·쓰기만 남긴 `0o600` 밖의 비트를 계산해야 차이가 드러난다.

`0o777 & ~0o600`은 `0o177`이다. 여기에 `0o477`을 AND 하면 `extra = 0o077`이 남는다. 소유자 읽기 `0o400`은 허용 범위에 있어 제거되고 그룹의 `0o070`과 기타 사용자의 `0o007`이 출력에 남는 과정이다. [Python 정수의 비트 연산 설명](https://docs.python.org/3.12/library/stdtypes.html#bitwise-operations-on-integer-types)은 `&`를 AND, `~`를 비트 반전으로 정의한다.

일반 권한 `0000`부터 `0777`까지 양 끝을 포함한 512개를 같은 코드의 `modes` 작업으로 열거한다. 이 작업에는 JSON 경로를 주지 않는다.

```bash
python -I -B -X utf8 u29_lpd_evidence.py modes
```

`enumerate_modes()`의 `numeric`은 숫자 크기 조건을 통과한 모드 집합, `subset`은 600 밖의 일반 권한이 없는 집합이다. `numeric - subset`은 첫 조건만 통과한 모드이며 정렬한 `subset`도 함께 출력한다.

[[run:2]]

숫자 크기로는 385개가 통과하지만 비트 조건에 맞는 값은 `0000`, `0200`, `0400`, `0600` 네 개다. 차이인 381개에는 앞서 본 `0477`도 들어간다. 이 네 값은 일반 권한만 비교한 결과다. `0000`의 파일을 서비스가 읽을 수 있는지 같은 동작 조건이나 소유자·사용 필요성까지 합쳐 양호 네 건으로 세지는 않는다.

[Python stat 문서](https://docs.python.org/3.12/library/stat.html)는 소유자·그룹·기타 사용자의 읽기·쓰기·실행 비트와 특수 비트를 나눠 설명한다. 실제 수집에서 파일 종류까지 들어 있는 모드 전체를 일반 권한 정수와 섞지 않고 종류·일반 권한·특수 비트를 구분해 기록한다. ACL 등 이 입력에 없는 접근 조건은 별도로 조사한다.

두 명령의 종료 0은 각각 가상 자료 비교와 모드 열거가 끝났다는 뜻이다. 미수집 보류나 차이 발견도 정상적인 계산 결과이며 U-29의 양호 판정 코드가 아니다. 읽기·JSON·필드 오류는 표준 오류와 종료 2로 알린다. 오류가 나면 지정한 경로, `cases`의 JSON 인수, 상태별 필드와 모드 표기를 살핀다.

운영 자료에는 실제 경로의 부재 근거 또는 사용 필요성 자료, 소유자, 파일 종류, 권한을 남긴다. 링크나 조회 오류가 있으면 그 사실도 유지한다. 가상 입력의 `required: true`와 `UID=0`은 이러한 운영 근거를 대신하지 않는다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Python 3.12 stat: 일반 권한과 특수 비트](https://docs.python.org/3.12/library/stat.html)
- [Python 3.12 내장형: 정수의 비트 연산](https://docs.python.org/3.12/library/stdtypes.html#bitwise-operations-on-integer-types)
