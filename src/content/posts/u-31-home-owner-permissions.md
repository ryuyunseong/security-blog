---
title: "U-31: 홈디렉토리 소유자 및 권한 설정"
description: "홈 디렉터리를 해당 계정의 UID와 대조하고 그룹·기타 사용자 쓰기 비트를 분리해 계산합니다. 0770의 그룹 쓰기, 소유자 불일치, ACL·링크·미수집을 가상 자료 열두 건으로 비교합니다."
date: "2026-11-08T18:35:42+09:00"
sourcesChecked: "2026-11-08"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "홈 디렉터리", "파일 권한", "KISA"]
draft: false
series: unix-2026
seriesOrder: 31
---

확장 접근 ACL이 없는 홈 디렉터리의 모드가 `0770`이면 소유자와 그룹에 읽기·쓰기·탐색 권한이 있고 기타 사용자 권한은 없다. 여기서 기타 사용자 쓰기만 제거하는 `o-w`를 적용해도 그룹의 쓰기는 남는다. U-31의 ‘타 사용자 쓰기 권한 제거’를 살피려면 소유자 일치 여부와 그룹·기타 사용자 비트를 각각 비교해야 한다.

## 소유자가 맞아도 그룹 쓰기가 남는 경우

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-31은 ‘홈디렉토리 소유자 및 권한 설정’이며 중요도는 ‘중’이다. 항목표 9쪽과 본문 65쪽의 코드·제목·중요도를 대조했다. 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다.

양호 기준은 홈 디렉토리 소유자가 해당 계정이고 타 사용자 쓰기 권한이 제거된 경우다. 소유자가 해당 계정이 아니거나 타 사용자 쓰기 권한이 있으면 취약 기준에 해당한다. 가이드는 `/etc/passwd`에서 홈 경로를 살피고 계정이 개별적으로 만들어 사용하는 디렉터리도 조사하도록 설명한다.

본문의 조치 예시에는 소유자 변경과 `chmod o-w`가 나온다. [GNU chmod 문서](https://man7.org/linux/man-pages/man1/chmod.1.html)에서 `g`는 소유 그룹, `o`는 소유자·그룹에 속하지 않는 기타 사용자를 가리킨다. 따라서 `0770`에 `o-w`만 적용하면 값은 `0770` 그대로다. 이 설명은 명령의 의미를 대조한 것이며 아래 실습에서 실제 권한을 변경하지는 않는다. 그룹 구성과 필요한 공유 범위를 조사하고 그룹 쓰기까지 별도로 대조한다.

디렉터리의 쓰기 권한은 그 안의 이름을 만들고 지우는 동작과 관계가 있다. 실제로 그런 작업을 하려면 디렉터리의 탐색 권한과 상위 경로 조건 등도 충족해야 한다. 파일 본문의 쓰기 권한과 디렉터리의 이름 변경·삭제 권한은 구분해 살핀다. 이 글의 비트 비교는 다른 계정의 실제 접근 시험을 대신하지 않는다.

## 홈 경로에 어떤 수집 자료를 붙일 것인가

계정 자료의 UID·홈 경로와 그 경로에서 얻은 디렉터리 메타데이터를 한 묶음으로 대조한다. [passwd(5)](https://man7.org/linux/man-pages/man5/passwd.5.html)의 계정 레코드에는 UID와 홈 디렉터리 필드가 따로 있다. 계정 이름이 비슷한 다른 디렉터리의 소유자를 섞지 않고 수집 시점과 대상 경로를 함께 남긴다.

실습의 대표 자료는 가상 계정 UID `1002`, 홈 경로 `/home/bravo`, 디렉터리 소유 UID `1002`, 모드 `0770`이다. 소유자 조건이 일치해도 그룹 쓰기 비트 `0020`은 검토 후보로 남는다.

[[diagram]]

실제 자료를 이 그림처럼 합치려면 계정이 지정한 경로와 메타데이터를 얻은 경로가 같아야 한다. 아래 JSON에서는 그 대응을 이미 마친 가상 자료라고 가정한다. 프로그램이 계정 목록이나 경로를 직접 조회해 연결하는 것은 아니다.

입력의 `state`는 수집 상황에 따라 나눈다.

- 디렉터리 종류·소유 UID·모드를 읽었다면 `directory`로 적는다. 확장 접근 ACL이 없다는 자료까지 있으면 `acl: none`, 확장 ACL이 있으면 `extended`, ACL을 받지 못했으면 `unknown`이다.
- 경로가 심볼릭 링크라면 `symlink`로 남기고 링크와 실제 대상을 별도로 조사한다. `other_type`은 디렉터리가 아닌 종류가 입증된 상태다. 두 상태의 모드를 디렉터리 모드로 비교하지 않는다.
- 경로 부재가 입증됐다면 `missing`, 조회가 실패했다면 `read_error`, 자료 자체가 없다면 `uncollected`다. 이들은 소유 UID·모드·ACL에 `null`을 넣고 비교를 보류한다. 부재는 다음 항목 U-32의 존재 관리와 구분하며 미수집을 부재로 바꾸지 않는다.

위 상황은 입력 상태를 정하는 가정이다. 링크·부재·권한 오류를 실제로 수집한 기록은 아니며 가상 `state`를 적는 행위 자체가 해당 상황의 증거가 되지는 않는다.

## 열두 가상 경로를 같은 비교기에 넣기

Python 3.9 이상과 표준 라이브러리를 사용한다. Windows Python 3.12.1의 PowerShell과 Git Bash에서 실행했다. Unix UID·모드는 정수와 문자열로만 비교하므로 관리자 권한·Linux 파일시스템·실제 계정이나 홈 폴더가 필요하지 않다. JSON의 `/home/bravo` 같은 경로는 가상 표기이며 실제 폴더를 만들지 않는다.

ZIP을 빈 폴더에 풀고 `u31_home_review.py`, `u31_home_cases.json`, `README.md`가 함께 있는 글별 폴더로 이동한다. 포함된 JSON은 다시 만들지 않는다. README에서 사용하는 셸의 실행 블록 하나를 선택하면 같은 명령과 숫자 종료 코드 확인 방법을 볼 수 있다.

[[download]]

```bash
python -I -B -X utf8 u31_home_review.py u31_home_cases.json
```

명령 직후 PowerShell에서는 `$LASTEXITCODE`, Bash에서는 `echo $?`를 읽는다. PowerShell의 `$?`는 성공 여부이므로 숫자 코드와 구분한다. 입력 경로에 공백이 있으면 전체 경로를 따옴표로 감싼다. 프로그램은 지정한 JSON만 읽고 결과를 표준 출력으로 내며 입력·결과 파일을 쓰지 않는다. 정리할 때는 자신이 ZIP을 푼 폴더만 대상으로 삼는다.

다음 목록의 `accountUid`는 계정 자료의 UID, `ownerUid`는 디렉터리 소유 UID다. UID는 음수가 아닌 정수만 받고 Python의 `True`·`False`는 거부한다. `mode`는 특수 비트를 포함할 수 있는 네 자리 8진수 문자열이다.

```json
[
  {"id": "owner-only", "accountUid": 1001, "home": "/home/alpha", "state": "directory", "ownerUid": 1001, "mode": "0750", "acl": "none"},
  {"id": "group-write", "accountUid": 1002, "home": "/home/bravo", "state": "directory", "ownerUid": 1002, "mode": "0770", "acl": "none"},
  {"id": "other-write", "accountUid": 1003, "home": "/home/charlie", "state": "directory", "ownerUid": 1003, "mode": "0707", "acl": "none"},
  {"id": "wrong-owner", "accountUid": 1004, "home": "/home/delta", "state": "directory", "ownerUid": 0, "mode": "0700", "acl": "none"},
  {"id": "both-fail", "accountUid": 1005, "home": "/home/echo", "state": "directory", "ownerUid": 1006, "mode": "0777", "acl": "none"},
  {"id": "sticky-group", "accountUid": 1007, "home": "/home/foxtrot", "state": "directory", "ownerUid": 1007, "mode": "1770", "acl": "none"},
  {"id": "extended-acl", "accountUid": 1008, "home": "/home/golf", "state": "directory", "ownerUid": 1008, "mode": "0750", "acl": "extended"},
  {"id": "acl-unsampled", "accountUid": 1009, "home": "/home/hotel", "state": "directory", "ownerUid": 1009, "mode": "0750", "acl": "unknown"},
  {"id": "home-link", "accountUid": 1010, "home": "/home/india", "state": "symlink", "ownerUid": null, "mode": null, "acl": null},
  {"id": "home-missing", "accountUid": 1011, "home": "/home/juliet", "state": "missing", "ownerUid": null, "mode": null, "acl": null},
  {"id": "home-denied", "accountUid": 1012, "home": "/home/kilo", "state": "read_error", "ownerUid": null, "mode": null, "acl": null},
  {"id": "home-unsampled", "accountUid": 1013, "home": "/home/lima", "state": "uncollected", "ownerUid": null, "mode": null, "acl": null}
]
```

`home`은 이 예제에서 정규화된 Unix 절대 경로 문자열인지 검사한다. 허용 문자는 영문자·숫자·밑줄·하이픈·슬래시로 제한했으며 실제 Unix 파일 이름 전체를 지원하는 수집기는 아니다. 경로를 운영체제에 전달해 조회하지도 않는다.

아래 전체 코드는 ZIP의 `u31_home_review.py`와 같다. `load_rows()`가 입력 크기·JSON 중복 키·전체 행의 형식을 먼저 검사하므로 뒤쪽 행이 잘못됐을 때 앞쪽 결과만 먼저 출력하지 않는다.

```python
import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키 중복")
        result[key] = value
    return result


def is_uid(value):
    return type(value) is int and value >= 0


def validate(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError("입력은 1~1000건의 목록이어야 함")
    fields = {"id", "accountUid", "home", "state", "ownerUid", "mode", "acl"}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != fields:
            raise ValueError("필드 목록 불일치")
        label = row["id"]
        if not isinstance(label, str) or not re.fullmatch(r"[a-z0-9-]{1,40}", label):
            raise ValueError("id 형식 오류")
        if label in seen:
            raise ValueError("id 중복")
        seen.add(label)
        if not is_uid(row["accountUid"]):
            raise ValueError("accountUid는 음수가 아닌 정수여야 함")
        home = row["home"]
        if not isinstance(home, str) or not re.fullmatch(r"/[A-Za-z0-9_/-]{0,239}", home):
            raise ValueError("home 경로 형식 오류")
        if str(PurePosixPath(home)) != home or ".." in PurePosixPath(home).parts:
            raise ValueError("home은 정규화된 Unix 절대 경로여야 함")
        state = row["state"]
        if state not in ("directory", "symlink", "other_type", "missing", "read_error", "uncollected"):
            raise ValueError("state 형식 오류")
        if state != "directory":
            if any(row[key] is not None for key in ("ownerUid", "mode", "acl")):
                raise ValueError("디렉터리 미확정 상태의 메타데이터는 null이어야 함")
            continue
        if not is_uid(row["ownerUid"]):
            raise ValueError("ownerUid는 음수가 아닌 정수여야 함")
        if not isinstance(row["mode"], str) or not re.fullmatch(r"[0-7]{4}", row["mode"]):
            raise ValueError("mode는 네 자리 8진수 문자열이어야 함")
        if row["acl"] not in ("none", "extended", "unknown"):
            raise ValueError("acl은 none, extended, unknown 중 하나여야 함")
    return rows


def load_rows(path):
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(1_000_001)
    except OSError as error:
        raise ValueError("지정한 입력 파일을 읽지 못함") from error
    if len(raw) > 1_000_000:
        raise ValueError("입력 크기 제한 초과")
    return validate(json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object))


def review(row):
    state = row["state"]
    if state != "directory":
        reasons = {"symlink": "링크와 대상 별도 조회", "other_type": "디렉터리 아님",
                   "missing": "경로 부재 자료, 존재 관리는 U-32와 구분",
                   "read_error": "조회 오류", "uncollected": "자료 미수집"}
        return "보류", reasons[state]
    mode = int(row["mode"], 8)
    write_bits = mode & 0o022
    issues, pending = [], []
    if row["ownerUid"] != row["accountUid"]:
        issues.append("소유 UID 불일치")
    if write_bits:
        issues.append(f"일반모드 쓰기={write_bits:04o}")
    if row["acl"] != "none":
        pending.append("확장 ACL 조사" if row["acl"] == "extended" else "ACL 미수집")
    special = mode & 0o7000
    if special:
        pending.append(f"특수 비트={special:04o} 별도 조사")
    status = "검토 후보" if issues else "보류" if pending else "입력 조건 일치"
    detail = "; ".join(issues + pending) or "소유 UID 일치, 일반모드 쓰기=0000, 확장 ACL 없음"
    return status, detail


def main():
    parser = argparse.ArgumentParser(description="가상 홈 디렉터리 수집 자료 비교")
    parser.add_argument("fixture")
    args = parser.parse_args()
    try:
        rows = load_rows(args.fixture)
    except (ValueError, UnicodeError, RecursionError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        status, detail = review(row)
        if row["state"] == "directory":
            metadata = f"UID={row['accountUid']}/소유={row['ownerUid']}, mode={row['mode']}: "
        else:
            metadata = ""
        print(f"{row['id']}: {metadata}{status} ({detail})")
    print(f"가상 자료 {len(rows)}건 분류 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

실제로 실행한 결과에서는 소유자만 다른 행과 쓰기 비트만 있는 행을 구별하고 두 조건이 함께 어긋난 행에는 두 이유를 모두 남겼다.

[[run:1]]

`owner-only` 한 건은 입력된 소유자·일반 모드·확장 ACL 조건이 일치한다. `group-write`, `other-write`, `wrong-owner`, `both-fail`, `sticky-group` 다섯 건은 검토 후보이며 나머지 여섯 건은 보류다. 종료 0과 마지막의 12건은 입력 검사와 이 분류가 완료됐다는 뜻이다. 운영 계정 열두 개의 점검을 완료했다는 뜻으로 세지 않는다.

### group-write를 읽고 반환하는 순서

ZIP의 명령이 `main()`에 진입하면 `args.fixture`에 `u31_home_cases.json`이 들어간다. `load_rows()`는 최대 1,000,000바이트의 입력을 허용하며 `unique_object()`가 중복 키를 거부한다. `validate()`는 1~1000건의 목록인지, 일곱 필드가 정확히 있는지, ID 중복·UID 형식·경로·상태별 메타데이터가 맞는지 검사한다.

`group-write`의 `state`는 `directory`이므로 소유 UID `1002`, 모드 문자열 `"0770"`, ACL 상태 `none`을 검사한 뒤 반환 목록에 남는다. `main()`의 반복문이 이 행을 `review()`에 넘기면 첫 보류 분기를 지나 `mode = int(row["mode"], 8)`로 8진수 모드를 읽는다.

`write_bits = mode & 0o022`에서 `0o022`는 그룹 쓰기 `0o020`과 기타 사용자 쓰기 `0o002`를 합친 마스크다. `0o770 & 0o022 = 0o020`이므로 `write_bits`는 0이 아니다. 소유 UID와 계정 UID는 같아 첫 조건에서 문제가 추가되지 않고 다음 쓰기 조건이 `issues`에 `일반모드 쓰기=0020`을 넣는다.

확장 ACL과 특수 비트가 없는 이 행의 `pending`은 빈 목록이다. `status`의 조건식은 `issues`를 먼저 검사해 ‘검토 후보’를 고른다. `review()`가 반환한 상태와 이유를 `main()`이 메타데이터와 합쳐 앞의 실제 출력 중 `group-write: UID=1002/소유=1002, mode=0770: 검토 후보 (일반모드 쓰기=0020)` 한 줄로 만든다.

`both-fail`은 소유 UID 불일치를 넣은 뒤에도 쓰기 비트 비교를 계속해 `0022`를 함께 출력한다. 소유자 문제를 찾았다고 다음 비교를 생략하지 않기 때문이다. `wrong-owner`의 소유 UID `0`도 계정 UID `1004`와 다르다. 이 항목의 해당 계정 소유 조건을 root 소유라는 이유로 자동 통과시키지 않는다.

## ACL과 특수 비트가 있는 행을 남기는 이유

[Linux ACL 문서](https://man7.org/linux/man-pages/man5/acl.5.html)는 접근 ACL을 해당 객체의 접근 권한, 디렉터리의 기본 ACL을 새 객체가 물려받을 ACL로 구분한다. 확장 접근 ACL에 mask 항목이 있으면 모드의 그룹 비트는 소유 그룹 항목이 아닌 ACL mask와 대응한다. 따라서 확장 ACL이 있는 행의 일반 모드 표시만으로 특정 그룹원의 실제 쓰기를 확정하지 않는다.

코드의 `extended-acl`은 확장 ACL 내용을 입력으로 받지 않으므로 보류하고 `acl-unsampled`는 ACL 자료가 없어서 보류한다. 확장 ACL과 소유자 불일치가 함께 있는 입력이라면 알려진 소유자 문제는 검토 후보로 표시하면서 ACL 조사도 이유에 남긴다. `issues`와 `pending`을 함께 보존한 목적이다.

`sticky-group`의 `1770`에는 그룹 쓰기 `0020`과 Sticky bit `1000`이 함께 있다. [inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html)의 Sticky bit 설명은 디렉터리 안 파일의 삭제·이름 변경을 특정 소유자·권한 있는 프로세스로 제한한다. 이 비트가 그룹 쓰기 자체를 없애지는 않으므로 검토 후보와 특수 비트 조사를 함께 남긴다.

읽기·JSON·입력 형식 오류는 표준 오류와 종료 2로 나타난다. 그때는 지정한 입력 경로, 필드 누락·추가, UID의 숫자형, 네 자리 8진수, 상태별 `null` 조건을 살핀다. ‘입력 조건 일치’는 이 예제의 제한된 비교이며 실제 양호·취약 판단에는 계정별 홈 경로 대응, 수집 시점, ACL과 상위 경로 등 적용되는 접근 조건을 대조한 자료가 필요하다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux man-pages: passwd(5)](https://man7.org/linux/man-pages/man5/passwd.5.html)
- [Linux man-pages: inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html)
- [Linux ACL: acl(5)](https://man7.org/linux/man-pages/man5/acl.5.html)
- [GNU Coreutils: chmod(1)](https://man7.org/linux/man-pages/man1/chmod.1.html)
