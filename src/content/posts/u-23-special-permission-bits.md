---
title: "U-23: SUID, SGID, Sticky bit 설정 파일 점검"
description: "특수 비트의 실행 파일·디렉터리 동작을 구분하고, 가상 수집 자료에서 SUID·SGID 검색 조건과 s·S 표기를 비교합니다."
date: "2026-10-28T18:45:14+09:00"
sourcesChecked: "2026-10-28"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-23", "Unix", "SUID", "SGID", "Sticky bit"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 23
---

`4755`와 `0755`는 일반 읽기·쓰기·실행 비트가 같고 맨 앞의 특수 비트가 다르다. 실행 파일에 붙은 SUID는 그 파일을 실행하는 프로세스의 유효 사용자 ID에 영향을 줄 수 있다. 반면 디렉터리의 Sticky bit는 그 안의 이름을 삭제하거나 바꾸는 권한에 관여한다. U-23을 살필 때는 파일 종류부터 나눠야 이 차이가 드러난다.

## 2026 기준에서 먼저 고르는 파일

[KISA 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-23은 중요도 ‘상’이며 SOLARIS, LINUX, AIX, HP-UX 등을 대상으로 한다. PDF 50쪽은 주요 실행 파일에 SUID·SGID 설정이 없으면 양호, 설정이 있으면 취약으로 구분한다. 점검 목적과 조치 설명은 불필요하거나 의심스러운 특수 권한을 조사하는 데 초점을 둔다.

같은 쪽의 사례에는 반드시 필요한 파일을 특정 그룹에 제한하는 방법도 있다. 따라서 발견 목록에는 패키지 기본값, 파일의 용도와 소유자, 사용할 계정, 변경 시 서비스 영향을 함께 남긴다. 필요한 시스템 실행 파일까지 일괄 변경하는 절차로 확대하지 않는다.

원문의 검색식은 `-user root`, `-type f`, SUID 또는 SGID 조건을 함께 사용하며 `-xdev`로 다른 파일시스템으로 내려가는 것을 제한한다. root 이외 소유자의 파일, 디렉터리의 특수 비트, 다른 마운트의 파일까지 모두 조사한 목록은 아니다. 아래 예제는 이 선택 조건을 가상 자료에서 비교한다.

## 같은 비트라도 파일 종류에 따라 달라지는 동작

| 비트 | 실행 파일에서 살필 내용 | 디렉터리에서 살필 내용 |
| --- | --- | --- |
| SUID `04000` | 실행 시 파일 소유자의 유효 UID 적용 조건 | 실행 파일의 SUID 설명을 그대로 적용하지 않음 |
| SGID `02000` | 실행 시 파일 소유 그룹의 유효 GID 적용 조건 | 새 파일의 그룹 상속 등 해당 OS의 동작 |
| Sticky `01000` | 현대 Linux 일반 파일의 권한 상승 근거로 삼지 않음 | 내부 항목의 삭제·이름 변경 제한 |

Linux의 세부 동작은 [inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html)과 [execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html)에 나뉘어 있다. Sticky 디렉터리에서는 파일 소유자, 디렉터리 소유자 또는 권한 있는 프로세스가 삭제·이름 변경을 할 수 있다. 파일 내용을 덮어쓰는 권한은 별도로 따지므로 Sticky가 내용 수정을 모두 막는다고 설명하면 안 된다. 가이드 참고란의 짧은 설명보다 Linux에서의 적용 대상과 예외를 구체적으로 구분한다.

[[diagram]]

실행 비트 자리의 `s`는 특수 비트와 해당 실행 비트가 함께 있음을, `S`는 특수 비트만 있음을 나타낸다. 다른 사용자의 실행 자리에서는 Sticky와 실행 비트 조합을 `t` 또는 `T`로 표시한다. 특수 비트가 보이는 것과 실제 권한 전환이 가능한 것은 구분한다. Linux에서는 `nosuid`, `no_new_privs` 같은 실행 조건도 영향을 준다.

## 가상 수집 자료 일곱 건을 분류하기

Python 3.9 이상과 표준 라이브러리를 사용한다. 실제 검증 환경은 Windows Python 3.12.1이다. 이 예제는 JSON의 문자열을 정수로 바꿀 뿐 파일 속성을 수집하거나 바꾸지 않는다. Linux 파일 모드를 Windows 파일시스템에 적용한 실습도 아니다.

ZIP을 빈 폴더에 풀고 `u23_special_bits.py`와 `u23_special_bits.json`이 함께 있는 폴더에서 실행한다. 관리자 권한·서버·추가 패키지는 필요하지 않다.

[[download]]

```bash
python -I -B -X utf8 u23_special_bits.py u23_special_bits.json
```

Linux·WSL에서는 `python3`로 실행해도 된다. PowerShell에서는 명령 직후 `$LASTEXITCODE`, Bash에서는 `echo $?`로 종료 코드를 읽는다. 입력은 이미 ZIP에 들어 있으며 다음과 같다.

```json
[
  {"case": "root-suid", "owner": "root", "kind": "file", "mode": "4755"},
  {"case": "root-sgid", "owner": "root", "kind": "file", "mode": "2750"},
  {"case": "app-suid", "owner": "app", "kind": "file", "mode": "4755"},
  {"case": "plain", "owner": "root", "kind": "file", "mode": "0755"},
  {"case": "shared-dir", "owner": "root", "kind": "dir", "mode": "1777"},
  {"case": "group-dir", "owner": "root", "kind": "dir", "mode": "2770"},
  {"case": "no-owner-exec", "owner": "root", "kind": "file", "mode": "4444"}
]
```

분류기 전체 코드는 다음과 같다. 경로를 필수 인수로 받아 지정한 JSON만 읽으며 운영 경로를 기본값으로 사용하지 않는다.

```python
import argparse
import json
from pathlib import Path
import re
import stat
import sys


def load_cases(text):
    rows = json.loads(text)
    if not isinstance(rows, list) or not rows:
        raise ValueError("비어 있지 않은 배열이 필요하다")
    names = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"case", "owner", "kind", "mode"}:
            raise ValueError("case, owner, kind, mode 필드가 필요하다")
        if any(not isinstance(row[key], str) or not row[key] for key in row):
            raise ValueError("모든 필드는 비어 있지 않은 문자열이어야 한다")
        if row["case"] in names or row["kind"] not in {"file", "dir"}:
            raise ValueError("사례 이름 중복 또는 파일 종류 오류")
        if not re.fullmatch(r"[0-7]{4}", row["mode"]):
            raise ValueError("mode는 네 자리 8진수여야 한다")
        names.add(row["case"])
    return rows


def classify(row):
    mode = int(row["mode"], 8)
    flags = [name for bit, name in [(stat.S_ISUID, "SUID"), (stat.S_ISGID, "SGID"), (stat.S_ISVTX, "Sticky")]
             if mode & bit]
    selected = row["owner"] == "root" and row["kind"] == "file" and bool(mode & 0o6000)
    file_type = stat.S_IFREG if row["kind"] == "file" else stat.S_IFDIR
    return flags, selected, stat.filemode(file_type | mode)


def main():
    parser = argparse.ArgumentParser(description="가상 수집 자료의 특수 비트만 분류한다")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        rows = load_cases(args.file.read_text(encoding="utf-8"))
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    selected_count = 0
    for row in rows:
        flags, selected, display = classify(row)
        selected_count += selected
        print(f"{row['case']}: {','.join(flags) or '없음'}; 검색 조건={'예' if selected else '아니요'}; {display}")
    print(f"가상 자료 {len(rows)}건, root 일반 파일의 SUID/SGID 검색 조건 {selected_count}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`load_cases()`는 모든 행의 필드·문자열·사례 이름·파일 종류와 네 자리 8진수 형식을 먼저 검사한다. 중간에 형식 오류가 있으면 분류 결과를 일부만 출력하지 않고 종료 코드 2로 끝난다. 파일을 읽지 못했을 때도 2다. 파일명과 JSON 필드를 먼저 살피며 원본을 지우는 정리 절차는 필요하지 않다.

`root-suid`의 `"4755"`는 `int(..., 8)`을 거쳐 정수가 된다. `classify()`의 `mode & stat.S_ISUID`가 참이어서 `flags`에 SUID가 들어간다. 소유자가 root이고 종류가 file이며 `mode & 0o6000`이 0이 아니므로 `selected`도 참이다. 이 값은 가이드의 검색 조건에 들어갔다는 뜻이다.

`stat.filemode(file_type | mode)`는 가정한 파일 종류까지 합쳐 표시 문자열을 만든다. `no-owner-exec`의 `4444`에는 SUID가 있으나 소유자 실행 비트 `0100`은 없어 대문자 `S`가 나온다. 분류기는 이를 자동으로 정상 파일이나 실행 가능한 권한 상승 경로로 판정하지 않는다.

[[run:1]]

root 일반 파일 중 세 사례가 검색 조건에 들어갔다. `app-suid`는 SUID를 출력하면서도 소유자 조건 때문에 검색 조건에서는 빠진다. `shared-dir`과 `group-dir`는 디렉터리이므로 해당 검색에서 제외된다. ‘아니요’는 특수 비트가 없다는 뜻도, 검토할 필요가 없다는 뜻도 아니다.

종료 코드 0은 일곱 가상 행을 끝까지 분류했다는 뜻이다. 실제 조사에서는 이 목록에 경로·소유자·패키지와 용도를 연결하고 수집 범위에서 빠진 파일시스템과 계정 소유 파일을 구분해 검토한다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux inode(7): 파일 종류와 모드](https://man7.org/linux/man-pages/man7/inode.7.html)
- [Linux execve(2): 실행 시 ID 변경 조건](https://man7.org/linux/man-pages/man2/execve.2.html)
