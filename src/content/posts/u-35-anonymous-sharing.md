---
title: "U-35: 공유 서비스에 대한 익명 접근 제한 설정"
description: "vsftpd 설정의 주석과 활성 항목을 구분해요. 가상 설정 아홉 건에서 명시적인 NO, YES, 중복과 수집 자료 부재를 나누고 익명 접근의 운영 판정에 필요한 범위를 설명해요."
date: "2026-11-12T18:38:57+09:00"
sourcesChecked: "2026-11-12"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "익명 접근", "vsftpd", "KISA"]
draft: false
series: unix-2026
seriesOrder: 35
---

`#anonymous_enable=NO`에는 익명 로그인을 막는 값처럼 보이는 `NO`가 들어 있어요. 하지만 맨 앞의 `#` 때문에 이 줄은 주석이에요. 설정 파일에서 문자열을 찾았다는 결과와 실제로 적용할 항목을 읽었다는 결과를 나눠야 하는 이유죠.

## 익명 접근을 제한한다는 U-35의 범위

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-35는 ‘공유 서비스에 대한 익명 접근 제한 설정’이며 중요도는 ‘상’이에요. 항목표 9쪽과 본문 70~76쪽의 코드·항목명·중요도가 일치해요. 대상은 SOLARIS, LINUX, AIX, HP-UX 등이에요.

가이드는 공유 서비스의 익명 접근을 제한한 경우를 양호, 허용한 경우를 취약으로 구분해요. 공유 서비스를 사용하지 않는 경우에는 양호 또는 N/A로 처리할 수 있다고 설명해요. 다만 설정 파일 하나가 없다는 자료로 공유 서비스 전체의 미사용을 확정할 수는 없어요. 익명 사용자가 쓰기까지 할 수 있다면 파일 변조 위험도 함께 조사해야 해요.

제품에 따라 읽을 자료가 달라져요. 가이드의 vsFTP 사례는 `anonymous_enable=NO`, ProFTP 사례는 익명 로그인 구간, Samba 사례는 공유별 `guest ok`를 다뤄요. [Samba smb.conf 설명서](https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html#GUESTOK)는 `guest ok=yes`인 공유에서 비밀번호 없이 게스트 계정 권한으로 접근할 수 있다고 설명해요. 이 글의 실행 코드는 그중 vsftpd의 한 설정 이름만 추출해요.

NFS의 값을 FTP와 같은 스위치로 해석하지는 않아요. 가이드 73쪽의 Linux 사례에는 `anonuid`·`anongid` 조회와 anon 옵션 삭제가 나오지만 [Linux exports(5)](https://manpages.debian.org/bookworm/nfs-kernel-server/exports.5.en.html)의 두 옵션은 익명 계정에 대응시킬 UID·GID를 정하는 값이에요. 삭제만으로 익명 접근이 차단됐다고 판단하지 않고 허용 클라이언트, 보안 방식과 UID 매핑을 함께 조사해요. Solaris·AIX·HP-UX 사례의 `anon=-1`을 Linux에 그대로 옮기지 않아요.

## 주석 속 NO와 활성 행의 NO

[Debian bookworm의 vsftpd.conf(5)](https://manpages.debian.org/bookworm/vsftpd/vsftpd.conf.5.en.html)는 줄을 주석 또는 `option=value` 형식의 지시자로 구분하며 옵션·등호·값 사이의 공백을 오류로 설명해요. `anonymous_enable`은 익명 로그인의 허용 여부이고 `YES`일 때 `ftp`와 `anonymous`라는 사용자 이름을 익명 로그인으로 인식해요.

아래 그림은 가상 JSON의 `commented`와 `explicit-off`에 든 설정 문자열이에요. 왼쪽은 주석 한 줄만 있고 오른쪽은 두 번째 줄에 활성 항목이 있어요. 두 입력의 `NO`가 같은 위치에 있는지 살펴보세요.

[[diagram]]

이 추출기는 활성 항목이 정확히 하나이며 값이 `NO`일 때 ‘명시적 제한값’으로 표시해요. 해당 문서에 적힌 기본값도 `NO`이지만 생략된 항목을 이 결과로 채우지는 않아요. 실제 프로그램의 버전·빌드 기본값, 실행 인수로 선택한 설정 파일이 아직 입증되지 않았기 때문이에요. 기본값과 배포판의 예제 파일에 적힌 값도 따로 읽어야 해요.

설정 본문을 얻었다고 가정한 행은 `collection: collected`와 문자열 `text`를 함께 가져요. 파일이 없다는 자료가 있으면 `absent`, 조회가 실패했다면 `query-error`, 자료 자체를 받지 못했다면 `uncollected`로 두고 `text`는 `null`로 남겨요. 이 세 상태는 모두 설정값 추출 전에 보류해요. 실습의 부재·오류 상태는 실제 운영 파일 조회가 아니라 JSON에 준비한 가정이에요.

## JSON의 문자열을 그대로 전달해 실행하기

Python 3.12 이상과 표준 라이브러리를 사용해요. Windows Python 3.12.1의 PowerShell과 Git Bash에서 같은 명령을 실행했어요. 관리자 권한, vsftpd 설치, Linux 파일시스템이나 별도 패키지는 필요하지 않아요.

ZIP을 빈 폴더에 풀고 `README.md`, `u35_anonymous_review.py`, `u35_anonymous_cases.json`, `u35_rejected.json`이 있는 글별 폴더로 이동해 주세요. 설정 예시는 JSON 안의 문자열이므로 `.conf` 파일이나 `/etc` 아래 경로를 만들지 않아요. 프로그램은 지정한 JSON만 읽고 다른 파일·계정·운영 설정을 조회하거나 바꾸지 않으며 소켓과 임시 파일도 만들지 않아요.

[[download]]

```bash
python -I -B -X utf8 u35_anonymous_review.py u35_anonymous_cases.json
```

명령 직후 PowerShell에서는 `$LASTEXITCODE`, Bash에서는 `echo $?`로 숫자 종료 코드를 읽어요. PowerShell의 `$?`는 성공 여부이므로 숫자 코드와 구분해 주세요. README에서 사용하는 셸의 블록 하나를 고르면 각 실행 바로 다음에 종료 코드 조회가 있어요.

`-I`는 Python 격리 모드, `-B`는 바이트코드 생성 방지, `-X utf8`은 UTF-8 모드예요. 파일시스템을 격리하는 옵션은 아니므로 인수에는 ZIP에 포함된 가상 JSON을 지정해요.

다음 전체 코드는 ZIP의 Python 파일과 같아요. `load_cases()`는 JSON의 크기·키·ID·수집 상태를 검사하고 `inspect_text()`는 대상 이름이 있는 행만 읽어요. 다른 옵션의 문법, 실제 vsftpd의 중복 처리나 실행 결과를 재현하는 전체 설정 파서는 아니에요. 대상 항목의 공백·여분 문자·중복을 발견하면 어느 값을 채택할지 추측하지 않고 보류해요.

```python
import argparse
import json
from pathlib import Path
import re
import sys


STATES = {"collected", "absent", "query-error", "uncollected"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키 중복")
        result[key] = value
    return result


def load_cases(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(20001)
    if len(raw) > 20000:
        raise ValueError("입력 크기 제한 초과")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("입력은 1~30건의 목록이어야 합니다")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "collection", "text"}:
            raise ValueError("입력 필드 불일치")
        name = row["id"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name) or name in seen:
            raise ValueError("ID 형식 오류 또는 중복")
        seen.add(name)
        if not isinstance(row["collection"], str) or row["collection"] not in STATES:
            raise ValueError("수집 상태 오류")
        if row["collection"] == "collected":
            if not isinstance(row["text"], str) or len(row["text"]) > 2000:
                raise ValueError("수집한 설정 본문 오류")
        elif row["text"] is not None:
            raise ValueError("설정 자료가 없으면 text는 null이어야 합니다")
    return rows


def inspect_text(text):
    values, malformed = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        if not re.match(r"anonymous_enable\b", line.lstrip()):
            continue
        match = re.fullmatch(r"anonymous_enable=(YES|NO)", line)
        if match is None:
            malformed.append(number)
        else:
            values.append((number, match[1]))
    if malformed:
        return "보류", "대상 항목 형식 재검토: 행 " + ",".join(map(str, malformed))
    if len(values) != 1:
        return "보류", f"활성 대상 항목 {len(values)}개; 생략·중복 조사"
    number, value = values[0]
    status = "명시적 제한값" if value == "NO" else "검토 후보"
    return status, f"anonymous_enable={value}; 행 {number}"


def main():
    parser = argparse.ArgumentParser(description="가상 vsftpd 설정의 익명 로그인 항목 추출")
    parser.add_argument("fixture")
    args = parser.parse_args()
    try:
        rows = load_cases(args.fixture)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print("가상 설정 비교 미실행")
        if isinstance(exc, (json.JSONDecodeError, UnicodeError, RecursionError)):
            message = "JSON 구문·UTF-8 인코딩·중첩 깊이를 살펴보세요"
        elif isinstance(exc, OSError):
            message = "입력 파일의 경로·읽기 권한을 살펴보세요"
        else:
            message = str(exc)
        print("입력 오류: " + message, file=sys.stderr)
        return 2
    counts = {"명시적 제한값": 0, "검토 후보": 0, "보류": 0}
    for row in rows:
        if row["collection"] == "collected":
            status, reason = inspect_text(row["text"])
        else:
            status, reason = "보류", "설정 자료 " + row["collection"]
        counts[status] += 1
        print(f"{row['id']}: {status} ({reason})")
    print(f"가상 설정 {len(rows)}건: 명시적 제한값 {counts['명시적 제한값']}, 검토 후보 {counts['검토 후보']}, 보류 {counts['보류']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## 아홉 건의 결과에서 남겨 둘 차이

첫 명령의 실제 결과는 ‘명시적 제한값’ 한 건, ‘검토 후보’ 한 건, ‘보류’ 일곱 건이에요. 출력의 상태는 설정 문자열을 추출한 범위에서 해석해요. 공유 서비스 전체의 양호·취약이나 실제 익명 접속 허용을 판정한 결과로 세지는 않아요.

[[run:1]]

`explicit-on`은 활성 행에서 `YES`를 읽었으므로 검토 후보예요. 네트워크 연결이나 인증을 시도한 결과는 없어요. `commented`는 활성 항목이 0개, `duplicate`는 2개여서 선택할 값이 정해지지 않아요. 두 입력을 같은 ‘NO 없음’으로 묶어 버리면 생략과 중복이라는 조사 이유를 잃어요.

`spaces`의 `anonymous_enable =NO`와 `inline`의 `anonymous_enable=NO # sample`은 이 예제가 허용한 정확한 한 행 형식과 달라요. 코드는 공백이나 뒤쪽 문구를 잘라 `NO`로 통과시키지 않고 행 번호를 남겨요. `missing`, `read-error`, `uncollected`의 보류는 문자열 안에 항목이 없다는 뜻이 아니라 설정 본문을 읽을 자료가 부족하다는 뜻이에요.

## explicit-off가 두 번째 줄을 고르는 과정

첫 명령의 인수는 `main()`의 `args.fixture`를 거쳐 `load_cases()`로 전달돼요. 최대 20,000바이트를 읽는지 검사한 뒤 `unique_object()`로 중복 JSON 키를 거부해요. 목록은 1~30건, 행의 키는 `id`, `collection`, `text` 세 개여야 하고 ID는 중복 없는 소문자·숫자·하이픈 형식이어야 해요. 수집된 `text`는 2,000자 이내 문자열, 미수집 등 다른 상태의 `text`는 `null`만 허용해요.

첫 행 `explicit-off`는 `collected`이므로 `inspect_text(row["text"])`를 호출해요. 시작할 때 `values`와 `malformed`는 빈 목록이에요. `enumerate(text.splitlines(), 1)`이 첫 줄 `#anonymous_enable=YES`에 번호 1을 붙이지만 `line.startswith("#")`가 참이어서 바로 다음 줄로 넘어가요. 주석의 `YES`는 `values`에 들어가지 않아요.

두 번째 줄은 `anonymous_enable=NO`예요. 대상 이름을 찾는 정규식에 이어 `re.fullmatch(r"anonymous_enable=(YES|NO)", line)`이 행 전체와 일치해요. `match[1]`은 `NO`이고 `values`는 `[(2, "NO")]`가 돼요. 형식 오류가 없으므로 `malformed` 분기를 지나고 `len(values) != 1`도 거짓이에요.

남은 한 쌍을 `number, value`에 풀면 각각 2와 `NO`예요. `value == "NO"`가 참이어서 `status`는 ‘명시적 제한값’이 되고 그 상태와 `anonymous_enable=NO; 행 2`를 반환해요. `main()`이 `counts[status]`를 하나 늘리고 ID·상태·이유를 합쳐 출력한 한 줄이 실제 기록의 `explicit-off: 명시적 제한값 (anonymous_enable=NO; 행 2)`예요.

반면 `commented`는 첫 주석을 건너뛴 뒤 `values`가 빈 목록으로 남아 길이 검사에서 반환해요. `duplicate`는 `[(1, "NO"), (2, "YES")]`가 되어 같은 길이 검사에서 보류하고 `spaces`는 `malformed = [1]`이어서 길이 검사보다 앞에서 반환해요. 뒤쪽에 올바른 값이 하나 더 있더라도 형식 오류 행을 숨기지 않는 순서예요.

## 수집하지 않은 본문이 들어오면

`u35_rejected.json`은 `collection: uncollected`인데 `text`에 `anonymous_enable=NO`를 넣은 가상 오류 입력이에요. 설정을 얻지 못한 상태를 명시적 제한값으로 바꾸는 실수를 입력 단계에서 막아요.

```bash
python -I -B -X utf8 u35_anonymous_review.py u35_rejected.json
```

이 명령 뒤에서도 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 코드를 읽어요. 다음 실제 기록의 표준 출력은 비교 미실행을 알리고 표준 오류는 `text`와 수집 상태의 충돌을 설명해요.

[[run:2]]

`load_cases()`의 `elif row["text"] is not None`이 참이어서 `ValueError`가 나고 `main()`이 오류를 출력한 뒤 2를 반환해요. 정상 입력의 종료 0은 아홉 건의 입력 검사·추출이 끝났다는 뜻이고 여기서 종료 2는 비교 전 거부예요. 예상한 거부를 재현한 시험 성공을 입력 허용이나 운영 양호 판정으로 읽지 않아요.

실행 오류가 나면 입력 경로와 읽기 권한, UTF-8·JSON 구문·크기, 중복 키·ID, 수집 상태와 `text`의 대응을 살펴보세요. 원본 JSON과 ZIP은 그대로 남기고 자료가 없는 행을 통과시키려고 `collected`로 바꾸지 않아요.

실제 점검 자료에는 서비스의 사용 여부, 실행 인수가 고른 설정 파일과 수집 시점, 해당 버전의 기본값과 설정 반영 자료를 함께 남겨요. FTP의 익명 로그인, Samba 공유의 게스트 접근, NFS 클라이언트와 UID 매핑을 각각 대조해야 U-35의 공유 서비스 범위를 판단할 수 있어요.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Debian bookworm: vsftpd.conf(5)의 형식과 익명 로그인 옵션](https://manpages.debian.org/bookworm/vsftpd/vsftpd.conf.5.en.html)
- [Samba: smb.conf의 guest ok](https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html#GUESTOK)
- [Linux NFS: exports(5)의 클라이언트 지정과 UID 매핑](https://manpages.debian.org/bookworm/nfs-kernel-server/exports.5.en.html)
