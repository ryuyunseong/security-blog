---
title: "파일 다운로드 경로 검증: 문자열 비교만으로는 부족한 이유"
description: "임시 파일을 사용해 문자열 접두사 검사와 실제 디렉터리 포함 관계 검증을 비교합니다."
date: "2026-10-08T21:23:44+09:00"
updated: "2026-10-16T00:00:00+09:00"
category: "web"
tags: ["경로검증", "Python", "파일"]
draft: false
example: false
sourceUrl: "https://neoflux.tistory.com/31"
migrated: "2026-10-16"
---

다운로드 폴더 경로를 사용자 입력 앞에 붙이는 것만으로 파일 접근 범위가 제한되지는 않는다. `../`, 비슷한 폴더 이름, 심볼릭 링크는 문자열 검사와 실제 파일 경로의 차이를 드러낸다.

임시 파일로 세 가지 검사를 비교한 실습이다. 서버를 띄우거나 운영 파일을 읽지 않는다. 여기서 허용 범위 밖의 파일도 모두 실습용 임시 디렉터리에 만든 자료다.

## 문자열 접두사와 디렉터리 경계는 다르다

허용 폴더가 `/app/files`라면 `/app/files/../secret.txt`는 문자열상 같은 경로로 시작해도 실제로는 `/app/secret.txt`를 가리킨다. 경로를 먼저 해석하더라도 `startswith()`만 사용하면 `/app/files_backup/secret.txt`까지 내부 파일로 오인한다.

확인해야 할 것은 문자열의 시작이 아니라 해석된 경로가 허용 디렉터리 안에 있는지다. 실제 정보 유출 여부는 서비스 계정이 해당 파일을 읽을 수 있는지, 그 내용이 응답으로 반환되는지까지 확인해야 한다.

## 경로를 해석한 뒤 포함 관계 확인하기

실습의 `contained_read()`는 상대 경로만 받는다. 기준 디렉터리와 요청 경로를 `resolve(strict=True)`로 해석한 뒤, `is_relative_to()`로 포함 관계를 확인한다. 일반 파일만 읽으므로 없는 파일과 디렉터리는 제공하지 않는다.

`is_relative_to()` 자체는 파일시스템을 확인하거나 `..`를 해석하지 않는다. 먼저 `resolve()`를 호출해야 상위 이동과 심볼릭 링크의 실제 목적지를 기준으로 검사할 수 있다. 이 구현은 외부를 가리키는 링크는 거부하고 내부 파일을 가리키는 링크는 허용한다.

절대 경로는 내부 파일을 가리켜도 거부한다. 상대 경로만 받도록 정한 입력 정책이기 때문이다. 반면 `sub/../report.txt`는 해석 결과가 내부 파일이므로 허용한다. `..`의 존재만으로 취약 여부를 판단하지 않는다.

## 임시 파일로 세 가지 방식 비교하기

Linux의 Python 3.9 이상과 표준 라이브러리만 사용한다. 심볼릭 링크를 만들 수 있는 파일시스템이 필요하며 관리자 권한이나 추가 패키지는 필요 없다. 아래 코드를 `path_lab.py`로 저장하고 실행하면 종료 시 임시 디렉터리가 정리된다.

```bash
python3 path_lab.py
```
`raw_prefix()`와 `resolved_prefix()`는 비교를 위한 잘못된 구현이다. `contained_read()`는 실행 중 파일 트리가 바뀌지 않는 조건에서 검증 원리를 보여 주는 실습용 함수다.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote
import os


def raw_prefix(base, name):
    # 잘못된 예: 경로를 해석하기 전에 문자열 앞부분만 비교한다.
    candidate = base / name
    if not str(candidate).startswith(str(base)):
        raise ValueError("범위 밖 경로")
    return candidate.read_text(encoding="utf-8")


def resolved_prefix(base, name):
    # 잘못된 예: 실제 경로를 구해도 디렉터리 경계를 구분하지 않는다.
    candidate = (base / name).resolve(strict=True)
    if not str(candidate).startswith(str(base)):
        raise ValueError("범위 밖 경로")
    return candidate.read_text(encoding="utf-8")


def contained_read(base, name):
    # 이미 디코딩된 상대 경로를 받는다. 파일 트리가 고정된 실습용이다.
    if not name or "\x00" in name:
        raise ValueError("빈 경로 또는 널 문자")
    requested = Path(name)
    if requested.is_absolute():
        raise ValueError("절대 경로 금지")

    root = base.resolve(strict=True)
    candidate = (root / requested).resolve(strict=True)
    if not candidate.is_relative_to(root):
        raise ValueError("범위 밖 경로")
    if not candidate.is_file():
        raise ValueError("일반 파일 아님")

    # 검사와 읽기 사이의 파일 교체는 막지 못한다.
    return candidate.read_text(encoding="utf-8")


def outcome(reader, base, name):
    try:
        return reader(base, name)
    except (OSError, ValueError, RuntimeError):
        return "거부"


def main():
    if os.name != "posix":
        raise SystemExit("Linux 등 POSIX 환경에서 실행한다.")

    with TemporaryDirectory(prefix="path-lab-") as temporary:
        work = Path(temporary).resolve()
        base = work / "files"
        sibling = work / "files_backup"
        base.mkdir()
        sibling.mkdir()
        (base / "report.txt").write_text("공개", encoding="utf-8")
        (work / "secret.txt").write_text("외부", encoding="utf-8")
        (sibling / "secret.txt").write_text("외부", encoding="utf-8")
        (base / "sub").mkdir()
        (base / "outside-link").symlink_to(work / "secret.txt")
        (base / "inside-link").symlink_to(base / "report.txt")

        # 외부 파일도 모두 이 실습이 만든 임시 디렉터리에 있다.
        cases = [
            ("정상 파일", "report.txt", ("공개", "공개", "공개")),
            ("상위 이동", "../secret.txt", ("외부", "거부", "거부")),
            (
                "비슷한 폴더명",
                "../files_backup/secret.txt",
                ("외부", "외부", "거부"),
            ),
            (
                "절대 외부 경로",
                str(work / "secret.txt"),
                ("거부", "거부", "거부"),
            ),
            (
                "절대 내부 경로",
                str(base / "report.txt"),
                ("공개", "공개", "거부"),
            ),
            ("외부 심볼릭 링크", "outside-link", ("외부", "거부", "거부")),
            ("내부 심볼릭 링크", "inside-link", ("공개", "공개", "공개")),
            ("없는 파일", "missing.txt", ("거부", "거부", "거부")),
            ("디렉터리", "sub", ("거부", "거부", "거부")),
            (
                "내부로 돌아오는 경로",
                "sub/../report.txt",
                ("공개", "공개", "공개"),
            ),
        ]
        readers = (raw_prefix, resolved_prefix, contained_read)
        print("입력 | 원문 접두사 | 해석 후 접두사 | 경로 포함 검사")

        for label, name, expected in cases:
            observed = tuple(outcome(reader, base, name) for reader in readers)
            if observed != expected:
                raise AssertionError(f"{label}: 예상 {expected}, 실제 {observed}")
            print(label + " | " + " | ".join(observed))

        # 디코딩 횟수는 HTTP 프레임워크가 아닌 이 실습에서 명시한다.
        encoded = "%252e%252e%252fsecret.txt"
        once = unquote(encoded)
        twice = unquote(once)
        if (once, twice) != ("%2e%2e%2fsecret.txt", "../secret.txt"):
            raise AssertionError("디코딩 결과 불일치")
        if outcome(contained_read, base, twice) != "거부":
            raise AssertionError("디코딩 후 외부 경로가 허용됨")

        print(f"1회 디코딩: {once}")
        print(f"2회 디코딩: {twice}")
        print("성공: 경로 비교 30건, 디코딩 결과와 차단 확인 2건")


if __name__ == "__main__":
    main()
```
## 실행 결과에서 확인할 차이

실행 결과를 표로 정리하면 다음과 같다. ‘공개’와 ‘외부’는 파일에 미리 넣은 문자열이다. ‘거부’에는 범위 검사 실패와 파일 읽기 실패가 함께 포함돼 있으므로 모두 같은 이유로 차단된 것은 아니다.

| 입력 | 원문 접두사 | 해석 후 접두사 | 경로 포함 검사 |
| --- | --- | --- | --- |
| 정상 파일 | 공개 | 공개 | 공개 |
| 상위 이동 | 외부 | 거부 | 거부 |
| 비슷한 폴더명 | 외부 | 외부 | 거부 |
| 절대 외부 경로 | 거부 | 거부 | 거부 |
| 절대 내부 경로 | 공개 | 공개 | 거부 |
| 외부 심볼릭 링크 | 외부 | 거부 | 거부 |
| 내부 심볼릭 링크 | 공개 | 공개 | 공개 |
| 없는 파일 | 거부 | 거부 | 거부 |
| 디렉터리 | 거부 | 거부 | 거부 |
| 내부로 돌아오는 경로 | 공개 | 공개 | 공개 |

원문 접두사 비교는 상위 이동과 외부 링크를 허용했다. 해석 후 접두사 비교는 두 경우를 막았지만 이웃 폴더인 `files_backup`은 허용했다. 경로 포함 검사는 세 경우를 모두 거부했다.

절대 외부 경로는 접두사 검사에서도 거부됐다. 절대 경로 결합이 항상 검사를 우회하는 것은 아니다. 절대 내부 경로의 결과가 다른 이유는 상대 경로만 받도록 정한 정책 때문이다.

## 디코딩과 파일 교체도 확인하기

같은 입력도 디코딩 횟수에 따라 경로가 달라진다. 실습에서는 `unquote()`를 두 번 호출하고 최종 결과를 검사했다. 특정 HTTP 제품의 동작을 재현한 것은 아니다.

```text
1회 디코딩: %2e%2e%2fsecret.txt
2회 디코딩: ../secret.txt
성공: 경로 비교 30건, 디코딩 결과와 차단 확인 2건
```
실서비스에서는 프록시와 웹 프레임워크의 디코딩 시점을 확인한다. 이미 처리된 값을 무조건 다시 디코딩하지 않는다. 검증 후 추가 디코딩을 하거나 원래 입력으로 경로를 다시 조립하면 검사한 대상과 실제로 여는 대상이 달라질 수 있다.

파일 교체도 별도 문제다. `resolve()`와 `read_text()` 사이에 대상이나 상위 디렉터리가 바뀌면 다른 파일을 읽을 수 있다. 이런 검사 시점과 사용 시점의 경쟁 조건(TOCTOU)은 이번 실습에서 검증하지 않았다.

다운로드 영역의 쓰기 주체를 제한하고, 읽기 전용으로 분리하는 방안을 검토한다. Linux에서는 디렉터리 파일 디스크립터를 기준으로 파일을 여는 `openat2()`의 `RESOLVE_BENEATH` 같은 제한을 사용할 수 있다. 심볼릭 링크와 마운트 경계의 허용 여부는 별도 정책으로 정한다.

## 경로 검사와 다운로드 권한은 별개다

외부 입력은 가능하면 파일 경로 대신 파일 ID로 받고, 서버가 관리하는 저장 위치와 연결한다. 여기에 요청 사용자가 해당 파일을 받을 권한이 있는지도 확인해야 한다. 허용 폴더 안에 있는 다른 사용자의 파일도 무조건 제공해서는 안 된다.

점검은 허가된 검증 환경에서 정상 파일과 허용되지 않은 테스트 파일을 준비해 수행한다. 응답 내용, 서비스 계정의 파일 접근 권한, 디코딩 단계, 링크 생성 권한을 함께 확인하고 오류 응답에 내부 경로나 예외 내용을 그대로 노출하지 않는다.

보고서에서는 “경로 포함 검증이 없다”는 코드 관찰과 “허용 폴더 밖의 테스트 파일 내용이 반환됐다”는 재현 결과를 구분해 기록한다.

## 참고 자료

- [Python, pathlib](https://docs.python.org/3/library/pathlib.html)
- [Python, urllib.parse](https://docs.python.org/3/library/urllib.parse.html)
- [OWASP, Path Traversal](https://community.owasp.org/attacks/Path_Traversal)
- [MITRE, CWE-22](https://cwe.mitre.org/data/definitions/22.html)
- [Linux man-pages, openat2(2)](https://man7.org/linux/man-pages/man2/openat2.2.html)
