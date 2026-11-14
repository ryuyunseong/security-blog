---
title: "U-37: crontab 설정파일 권한 설정 미흡"
description: "0640과 0604의 읽기 비트를 비교하고 cron·at 관련 파일의 가상 UID·모드 열 건을 분류해요. 일반 권한 범위, 소유자 차이, 특수 비트와 미수집을 나누며 공식 표의 640 경계 문구도 대조해요."
date: "2026-11-14T18:35:11+09:00"
sourcesChecked: "2026-11-14"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "cron", "at", "권한", "KISA"]
draft: false
series: unix-2026
seriesOrder: 37
---

`0604`는 숫자로는 `0640`보다 작지만 기타 사용자에게 읽기 권한을 줘요. `0640`의 마지막 자리는 0이라 이 권한이 없고요. cron 관련 파일의 권한을 살필 때는 작은 숫자인지보다 누가 어떤 비트를 받았는지 비교해야 해요.

아래 그림의 두 입력은 `/etc/cron.allow`의 소유 UID를 0으로 가정하고 모드만 바꾼 독립된 사례예요. 같은 파일의 실제 변경 전후를 수집한 기록은 아니에요. UID 0은 이 실습에서 root 소유자를 나타내요.

[[diagram]]

`0640`의 그룹 읽기와 `0604`의 기타 읽기는 같은 권한이 아니에요. 기준에서 허용한 비트 밖에 켜진 것이 있는지 계산하면 숫자 대소 비교에서 빠지는 `0004`를 찾을 수 있어요.

## U-37의 대상과 표의 경계값

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-37은 ‘crontab 설정파일 권한 설정 미흡’이며 중요도는 ‘상’이에요. 항목표 9쪽과 본문 80~82쪽의 코드·항목명·중요도가 일치해요. 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이에요.

제목의 crontab만 보는 항목은 아니에요. 가이드는 crontab과 at 명령의 일반 사용자 실행 권한, cron·at 관련 파일의 소유자와 권한을 함께 다뤄요. 조치 예시는 명령 파일을 root 소유·750으로, 작업 목록과 관련 파일을 root 소유·640으로 설정하고 SUID를 제거하도록 설명해요. 바이너리와 설정 자료에 같은 모드를 일괄 적용하는 예제가 아니에요.

80쪽 판단표에는 양호의 관련 파일 권한을 ‘640 이하’, 취약의 권한을 ‘640 이상’으로 적어 640이 겹쳐요. 같은 표의 조치 방법과 81쪽 사례는 640을 제시해요. 이 글에서는 그 조치 예시를 일반 권한 비트의 비교 기준으로 사용하되 원문의 겹치는 문구를 임의로 고쳐 공식 판정 기준이 명료해졌다고 쓰지는 않아요. 실제 점검에서는 이 경계와 적용 해석을 점검 기준 담당자에게 질의할 자료로 남겨야 해요.

750에는 그룹의 읽기·실행 비트가 남아요. 따라서 그룹의 실제 구성원과 명령 사용 통제를 함께 조사해야 일반 사용자 실행 제한을 판단할 수 있어요. [Debian bookworm cron 패키지의 crontab(1)](https://manpages.debian.org/bookworm/cron/crontab.1.en.html)는 crontab 그룹에 대한 setgid 구성을 설명해요. 패키지의 동작 방식과 가이드의 SUID 제거 요구를 나눠 읽고 SUID·SGID나 실행 비트를 운영 파일에서 곧바로 바꾸는 실습은 하지 않아요.

같은 문서는 `cron.allow`가 있으면 그 목록을 우선하고 없을 때 `cron.deny`를 읽는다고 설명해요. 두 파일이 모두 없는 경우도 사이트 설정에 따라 달라질 수 있어요. 가이드 82쪽의 ‘두 파일이 없으면 root만 등록 가능’이라는 설명을 모든 구현의 공통 동작으로 넓히지 않고 해당 패키지의 문서와 실제 통제 자료를 대조해요. 실습의 `absent`는 이 때문에 자동 통과 대신 보류로 남겨요.

## 권한 수집값 열 건을 안전하게 비교하기

실습은 Python 3.12 이상과 표준 라이브러리를 사용해요. Windows Python 3.12.1의 PowerShell과 Git Bash에서 실행했어요. Linux 파일 권한을 Windows 파일에서 측정하는 실습이 아니라 JSON에 든 가상 UID·모드 문자열을 계산하는 코드라서 Linux 파일시스템·관리자 권한·cron 또는 at 설치가 필요하지 않아요.

ZIP을 빈 폴더에 풀고 `README.md`, `u37_mode_review.py`, `u37_mode_cases.json`, `u37_rejected.json`이 있는 글별 폴더로 이동해 주세요. 입력 두 개는 이미 들어 있어요. JSON의 `/etc/cron.allow` 같은 경로는 설명용 문자열이며 프로그램이 그 경로를 열지 않으므로 해당 파일·폴더를 만들지 않아요. 실제 cron·at 조회나 작업 등록, 계정·인증·권한 변경도 없어요.

[[download]]

`u37_mode_cases.json`의 열 건 중 그림의 `config-604`에 해당하는 입력은 다음과 같아요. 이 조각을 다시 저장하는 대신 ZIP의 전체 입력 파일을 명령에 넘겨 주세요.

```json
{
  "id": "config-604",
  "kind": "settings",
  "path": "/etc/cron.allow",
  "collection": "collected",
  "uid": 0,
  "mode": "0604"
}
```

`kind`가 `command`면 일반 권한 기준은 `0750`, `settings`면 `0640`이에요. 명령 파일인지 설정 자료인지 수집 자료를 보고 지정했다는 가정이며 경로 이름만으로 추론하지 않아요. 코드는 일반 파일의 메타데이터를 가정해요. 디렉터리·링크의 종류, ACL, 소유 그룹과 구성원, 파일 내용·실행 상태는 이 입력에 들어 있지 않아요.

`collection: collected`는 UID와 모드 자료를 얻었다고 가정해요. 파일 부재 자료가 있으면 `absent`, 조회 오류 자료가 있으면 `query-error`, 수집 자료 자체가 없으면 `uncollected`로 두고 `uid`·`mode`는 `null`로 남겨요. 실습의 세 상태는 실제 서버에서 수집한 오류나 부재가 아니라 미리 넣은 가정이에요. 자료를 얻지 못한 곳에 UID 0이나 0640을 대신 채우지 않아요.

첫 명령은 두 셸에서 같아요. 실행 직후 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 종료 코드를 읽어요. PowerShell의 `$?`는 성공 여부이므로 숫자 코드와 구분해 주세요. README에는 각 실행 바로 다음에 셸별 조회 명령이 있으니 사용하는 셸의 블록 하나를 고르면 돼요.

```bash
python -I -B -X utf8 u37_mode_review.py u37_mode_cases.json
```

`-I`는 Python 격리 모드, `-B`는 바이트코드 생성 방지, `-X utf8`은 UTF-8 모드예요. 파일시스템 접근을 제한하는 옵션은 아니므로 인수에는 ZIP의 가상 JSON을 지정해요. 다음 전체 코드는 ZIP의 Python 파일과 같아요.

```python
import json
from pathlib import Path
import re
import sys


LIMITS = {"command": 0o750, "settings": 0o640}
STATES = {"collected", "absent", "query-error", "uncollected"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("중복 키")
        result[key] = value
    return result


def load_rows(path):
    with path.open("rb") as stream:
        raw = stream.read(32001)
    if len(raw) > 32000:
        raise ValueError("입력 크기")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("목록 크기")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
                "id", "kind", "path", "collection", "uid", "mode"}:
            raise ValueError("행 필드")
        if (not isinstance(row["id"], str)
                or not re.fullmatch(r"[a-z0-9-]{1,24}", row["id"])
                or row["id"] in seen):
            raise ValueError("행 ID")
        seen.add(row["id"])
        if row["kind"] not in LIMITS or row["collection"] not in STATES:
            raise ValueError("종류 또는 수집 상태")
        path_text = row["path"]
        if (not isinstance(path_text, str) or not path_text.startswith("/")
                or len(path_text) > 120 or any(ord(c) < 32 for c in path_text)):
            raise ValueError("가상 경로")
        if row["collection"] == "collected":
            if (type(row["uid"]) is not int or not 0 <= row["uid"] <= 2147483647
                    or not isinstance(row["mode"], str)
                    or not re.fullmatch(r"[0-7]{4}", row["mode"])):
                raise ValueError("소유자 또는 모드")
        elif row["uid"] is not None or row["mode"] is not None:
            raise ValueError("미수집 값은 null")
    return rows


def assess(row):
    if row["collection"] != "collected":
        return "보류", row["collection"]
    mode = int(row["mode"], 8)
    limit = LIMITS[row["kind"]]
    extra = (mode & 0o777) & (~limit & 0o777)
    special = mode & 0o7000
    reasons = []
    if row["uid"] != 0:
        reasons.append(f"소유 UID {row['uid']}")
    if extra:
        reasons.append(f"범위 밖 일반 비트 {extra:04o}")
    if reasons:
        if special:
            reasons.append(f"특수 비트 {special:04o} 별도 조사")
        return "검토 후보", ", ".join(reasons)
    if special:
        return "보류", f"특수 비트 {special:04o} 별도 조사"
    return "일반 권한 범위 내", f"UID 0, 기준 {limit:04o}의 비트 부분집합"


def main():
    if len(sys.argv) != 2:
        print("사용법: python u37_mode_review.py 가상입력.json", file=sys.stderr)
        return 2
    try:
        rows = load_rows(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, TypeError):
        print("가상 권한 비교 미실행")
        print("입력 오류: 경로, UTF-8, JSON, 필드와 수집 상태를 살펴보세요", file=sys.stderr)
        return 2
    counts = {name: 0 for name in ("일반 권한 범위 내", "검토 후보", "보류")}
    for row in rows:
        status, reason = assess(row)
        counts[status] += 1
        print(f"{row['id']}: {status} | {reason}")
    print("가상 자료 " + str(len(rows)) + "건: " + ", ".join(
        f"{name} {count}" for name, count in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

프로그램은 지정한 JSON 하나만 읽고 임시 파일·소켓을 만들거나 입력을 고치지 않아요. 파일이 32,000바이트를 넘으면 읽기를 중단하고 중복 키·ID, 1~30건 범위, 필드와 수집 상태를 검사한 뒤 비교를 시작해요. `mode`는 `0`~`7`로 된 네 자리 문자열, `uid`는 음이 아닌 정수여야 해요. 참·거짓은 정수처럼 받아들이지 않아요.

[[run:1]]

‘일반 권한 범위 내 3, 검토 후보 3, 보류 4’는 열 건의 가상 자료에 대한 계산 결과예요. 종료 0은 입력 검사와 비교 완료이며 cron 사용 허용이나 U-37의 종합 양호 판정이 아니에요. 특수 비트·접근 제어·수집 범위가 남아 있으므로 ‘범위 내’를 운영 판정으로 바꿔 읽지 않아요.

## config-604의 기타 읽기 비트가 남는 과정

[GNU chmod(1)의 숫자 모드 설명](https://manpages.debian.org/bookworm/coreutils/chmod.1.en.html)에서 읽기·쓰기·실행은 각각 4·2·1이고 소유자·그룹·기타에 같은 규칙을 적용해요. 앞의 별도 자리는 SUID·SGID·sticky 비트예요. 이 코드도 일반 비트와 특수 비트를 따로 계산해요.

명령의 파일 인수는 `main()`에서 `Path(sys.argv[1])`이 되어 `load_rows()`로 들어가요. JSON 전체의 형식 검사를 마친 뒤 반복문이 `config-604` 행을 `assess()`에 전달해요. 이 행은 `collection`이 `collected`라 첫 보류 분기를 지나고 `int(row["mode"], 8)`이 문자열 `0604`를 8진수로 해석해 `mode`에 넣어요. 십진수 값은 388이에요.

`LIMITS[row["kind"]]`는 `settings`에 대응하는 `0o640`을 꺼내요. 이 `limit`은 십진수로 416이며 숫자가 작다는 이유로 388을 통과시키지는 않아요. `mode & 0o777`로 일반 권한만 남기고 `~limit & 0o777`로 기준에 없는 비트 `0137`을 만들어요. 둘을 AND 하면 `extra`는 `0004`, 곧 기타 사용자의 읽기 비트가 돼요. `special = mode & 0o7000`은 0이에요.

소유 UID는 0이어서 소유자 사유를 넣지 않지만 `if extra`는 참이에요. `reasons`에 `범위 밖 일반 비트 0004`가 추가되고 `if reasons` 분기에서 상태와 사유를 반환해요. `main()`은 검토 후보 수를 하나 늘린 뒤 실제 출력의 `config-604: 검토 후보 | 범위 밖 일반 비트 0004`를 만들어요. 이 행은 뒤의 특수 비트 보류나 범위 내 반환까지 내려가지 않아요.

`config-640`과 `config-600`은 모두 `extra`가 0이라 범위 내예요. 소유자·그룹에 허용한 비트 일부를 덜 가진 `0600`도 같은 부분집합 비교에 들어가요. `config-660`은 그룹 쓰기 `0020`이 남아 후보가 되고, `owner-1001`은 모드가 0640이어도 소유 UID가 1001이라 후보가 돼요.

`command-750`은 `kind: command`의 기준으로 비교해 범위 내예요. 같은 명령 자료의 `command-suid`는 일반 비트가 맞아도 `special`에 `4000`이 남아 보류돼요. 이 경로는 특수 비트의 필요성과 가이드 조치 요구를 추가로 조사하라는 표시이며 SUID가 제거됐다는 결과가 아니에요. 일반 비트·소유자가 이미 후보인 행에 특수 비트도 있다면 먼저 후보 분기로 가되 특수 비트 사유도 함께 남겨요.

뒤의 `no-file`, `read-error`, `no-evidence`는 각각 `absent`, `query-error`, `uncollected`예요. `assess()`의 첫 분기가 비트 계산 전에 상태를 반환하므로 미수집 값을 0으로 처리하지 않아요. 운영 자료를 모을 때는 파일 부재를 입증한 범위, 오류가 난 경로·시점, 아직 조회하지 않은 대상을 나눠 기록해야 해요.

## 모드 표기가 잘못됐으면 비교 전에 멈추기

두 번째 입력 `u37_rejected.json`은 모드를 `0680`으로 둬요. 8은 8진수 자릿값이 아니므로 `re.fullmatch(r"[0-7]{4}", row["mode"])`를 통과하지 못해요.

```bash
python -I -B -X utf8 u37_mode_review.py u37_rejected.json
```

[[run:2]]

표준 출력은 ‘가상 권한 비교 미실행’, 표준 오류는 입력 오류 안내이며 숫자 종료 코드는 2예요. 이 예상한 거부를 재현한 것과 입력이 허용됐다는 결과를 구분해 주세요. `load_rows()`가 전체 목록 검사를 끝내기 전에 예외를 내므로 앞의 정상 행만 비교한 부분 결과도 남기지 않아요. 실제 실행에서 종료 2가 나오면 파일 위치·읽기 가능 여부, UTF-8·JSON 구문·크기, 필드·중복·수집 상태와 모드 표기를 살펴보세요.

운영 점검에는 파일의 실제 종류와 수집 시점, cron·at 구현과 패키지 버전, 소유자·그룹·권한·ACL, 일반 사용자 사용 통제, 관련 작업 목록의 조사 범위를 함께 남겨요. 허용·거부 파일의 부재와 목록 내용도 별도 자료로 대조해야 해요. 이 자료가 갖춰진 범위에서 원문 경계값의 해석과 조치 적용을 결정하고 변경 후에는 서비스 기능과 접근 통제가 유지되는지 다시 검증해요.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [GNU chmod(1): 숫자 모드와 특수 비트](https://manpages.debian.org/bookworm/coreutils/chmod.1.en.html)
- [Debian bookworm cron: crontab(1)의 사용 통제와 그룹 구성](https://manpages.debian.org/bookworm/cron/crontab.1.en.html)
