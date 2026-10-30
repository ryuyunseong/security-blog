---
title: "U-25: world writable 파일 점검"
description: "일반 파일의 other 쓰기 비트를 Linux 가상 자료에서 수집하고 GNU find 결과와 비교합니다. 발견 목록과 설정 이유에 따른 판정을 구분합니다."
date: "2026-10-30T18:46:04+09:00"
sourcesChecked: "2026-10-30"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "파일 권한", "KISA"]
draft: false
series: unix-2026
seriesOrder: 25
---

`0602`인 일반 파일에는 기타 사용자(other)의 쓰기 비트가 있다. 읽기 비트가 없더라도 쓰기 비트 자체는 켜져 있다. 반대로 `0664`는 그룹 쓰기를 허용하지만 other 쓰기는 허용하지 않는다. U-25의 검색 조건을 읽을 때 이 두 모드를 구분해야 한다.

## 발견한 파일의 설정 이유까지 판단에 포함된다

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-25는 ‘world writable 파일 점검’이며 중요도는 ‘상’이다. PDF 52쪽의 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다.

원문은 world writable 파일이 없거나, 있더라도 설정 이유를 인지하고 있으면 양호로 구분한다. 파일이 있는데 설정 이유를 인지하지 못하면 취약이다. 따라서 검색 결과의 개수를 곧바로 최종 판정으로 바꾸지 않는다. 파일의 용도, 생성·수정 주체, 해당 권한이 필요한 이유와 변경 영향을 각각 조사할 자료가 된다.

조치 사례에는 other 쓰기 제거와 불필요한 파일 제거가 나온다. 검색됐다는 이유만으로 일괄 삭제하거나 권한을 바꾸는 절차로 확대하지 않는다. 아래 실습에서는 자신이 만든 임시 파일만 조회하고 실습 폴더를 정리한다.

## `-perm -2`가 고르는 비트

원문의 검색은 일반 파일인 `-type f`와 `-perm -2`를 함께 사용한다. [GNU find(1)](https://man7.org/linux/man-pages/man1/find.1.html)의 `-perm -mode`는 지정한 비트가 모두 켜졌는지 검사한다. `-2`에서 요구한 비트는 `0002` 하나이므로 나머지 읽기·쓰기·실행 비트가 어떤 조합이어도 other 쓰기가 켜졌으면 맞는다.

| 일반 파일의 모드 | `mode & 0o002` | `-perm -2` 선택 |
| --- | --- | --- |
| `0666` | `0002` | 예 |
| `0602` | `0002` | 예 |
| `0664` | `0000` | 아니요 |
| `0600` | `0000` | 아니요 |

앞에 하이픈이 없는 `-perm 2`는 권한 비트의 정확한 일치를 찾는 다른 식이다. `-perm -2`를 ‘모드가 정확히 0002인 파일’로 읽으면 위의 후보를 놓친다.

[[diagram]]

디렉터리와 링크는 종류를 따로 표시한다. 아래 코드의 `stat(follow_symlinks=False)`는 링크 대상 대신 링크 자체의 종류를 읽고 GNU find에도 링크를 따라가지 않는 `-P`를 준다. 링크의 `0777` 표시를 대상 일반 파일의 쓰기 허용 결과로 합치지 않는다.

## Linux 임시 폴더의 여섯 항목을 대조하기

Linux 또는 WSL의 Ubuntu 셸에서 Python 3.9 이상과 GNU find를 사용한다. 실제 검증 환경은 WSL Ubuntu 24.04, Python 3.12.3이다. POSIX 모드·심볼릭 링크를 사용하므로 Windows Python으로 실행하지 않는다. 관리자 권한·별도 패키지·네트워크 연결은 필요하지 않다.

ZIP을 빈 폴더에 풀고 `u25_fixture_lab.py`, `u25_world_writable.py`가 함께 있는 글별 폴더에서 실행한다. 준비기가 `/tmp`에 가상 파일 네 개, 디렉터리 한 개, 링크 한 개를 만든다. 독자가 운영 파일이나 입력 자료를 따로 준비할 필요는 없다.

[[download]]

```bash
python3 -I -B -X utf8 u25_fixture_lab.py ./u25_world_writable.py
```

명령 직후 `echo $?`로 종료 코드를 읽는다. 아래 수집기는 준비기가 만든 폴더 경로를 필수 인수로 받으며, 기본 경로로 `/`나 실제 홈을 탐색하지 않는다. 디렉터리 안으로 재귀적으로 내려가지 않고 표지를 제외한 바로 아래 항목만 수집한다.

```python
import argparse
import os
from pathlib import Path
import stat
import sys


def collect(root):
    root = root.resolve(strict=True)
    if root.parent != Path("/tmp") or not root.name.startswith("u25-fixture-"):
        raise ValueError("준비기가 만든 /tmp 실습 폴더만 지정한다")
    if (root / ".u25-fixture").read_text(encoding="utf-8") != "synthetic-u25\n":
        raise ValueError("실습 폴더 표지가 맞지 않는다")
    rows = []
    with os.scandir(root) as entries:
        for entry in sorted(entries, key=lambda item: item.name):
            if entry.name == ".u25-fixture":
                continue
            info = entry.stat(follow_symlinks=False)
            kind = "file" if stat.S_ISREG(info.st_mode) else "dir" if stat.S_ISDIR(info.st_mode) else "link" if stat.S_ISLNK(info.st_mode) else "other"
            mode = stat.S_IMODE(info.st_mode)
            other_write = bool(mode & stat.S_IWOTH)
            candidate = kind == "file" and other_write
            rows.append((entry.name, kind, mode, other_write, candidate))
    return rows


def main():
    parser = argparse.ArgumentParser(description="격리 실습 폴더의 일반 파일 쓰기 비트를 수집한다")
    parser.add_argument("lab", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        print("이 실습은 Linux의 /tmp에서 실행한다", file=sys.stderr)
        return 2
    try:
        rows = collect(args.lab)
    except (OSError, ValueError, UnicodeError):
        print("수집 오류: 준비기가 만든 폴더와 표지를 살핀다", file=sys.stderr)
        return 2
    for name, kind, mode, other_write, candidate in rows:
        print(f"{name}: {kind}, {mode:04o}, other 쓰기={'있음' if other_write else '없음'}, 일반 파일 후보={'예' if candidate else '아니요'}")
    count = sum(row[4] for row in rows)
    print(f"항목 {len(rows)}건, 일반 파일 후보 {count}건 수집 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`collect()`는 `/tmp/u25-fixture-`로 시작하는 폴더 이름과 준비기가 남긴 표지를 먼저 읽는다. `root`의 바로 아래 항목마다 `entry.stat(follow_symlinks=False)`로 얻은 `st_mode`를 해석한다. 파일 내용이나 계정 정보는 수집하지 않는다.

`other-only.txt`를 따라가면 `stat.S_ISREG()`가 참이어서 `kind`는 `file`이 된다. `stat.S_IMODE()`가 얻은 `0602`와 `stat.S_IWOTH`의 `0002`를 AND하면 0이 아닌 값이 남으므로 `other_write`는 참이다. `candidate`에는 일반 파일이라는 조건까지 함께 들어간다. `shared-dir`의 `0777`도 쓰기 비트는 있지만 `kind`가 `dir`라서 후보는 거짓이다.

이 수집기와 GNU find를 같은 가상 파일에 적용하는 준비기 전체 코드다.

```python
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description="자신이 만든 가상 파일의 쓰기 비트를 대조한다")
    parser.add_argument("collector", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        print("이 준비기는 Linux의 /tmp에서 실행한다", file=sys.stderr)
        return 2
    try:
        collector = args.collector.resolve(strict=True)
        if not collector.is_file():
            raise ValueError("수집기 파일이 필요하다")
        with tempfile.TemporaryDirectory(prefix="u25-fixture-", dir="/tmp") as temporary:
            root = Path(temporary)
            (root / ".u25-fixture").write_text("synthetic-u25\n", encoding="utf-8")
            for name, mode in (("group-only.txt", 0o664), ("open-note.txt", 0o666), ("other-only.txt", 0o602), ("private.txt", 0o600)):
                path = root / name
                path.write_text("synthetic\n", encoding="utf-8")
                path.chmod(mode)
            (root / "shared-dir").mkdir()
            (root / "shared-dir").chmod(0o777)
            (root / "shortcut").symlink_to("open-note.txt")
            run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(collector), str(root)], capture_output=True, text=True, encoding="utf-8", timeout=10)
            if run.returncode != 0 or run.stderr:
                raise ValueError("수집기가 정상 종료하지 않았다")
            found = subprocess.run(["find", "-P", str(root), "-type", "f", "-perm", "-2", "-printf", "%f\n"], capture_output=True, text=True, timeout=10)
            names = sorted(found.stdout.splitlines())
            if found.returncode != 0 or found.stderr or names != ["open-note.txt", "other-only.txt"]:
                raise ValueError("GNU find의 후보가 예상과 다르다")
            candidate_lines = [line.split(":", 1)[0] for line in run.stdout.splitlines() if line.endswith("일반 파일 후보=예")]
            if candidate_lines != names:
                raise ValueError("수집기와 GNU find의 후보가 다르다")
            print(run.stdout, end="")
            print("GNU find 후보: " + ", ".join(names))
        print("준비기 검증 완료: 후보 2건 일치, 생성한 임시 폴더 정리")
    except (OSError, ValueError, subprocess.SubprocessError):
        print("준비 오류: 수집기 경로·Linux 임시 폴더·GNU find를 살핀다", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`TemporaryDirectory`가 만든 상위 폴더는 기본적으로 해당 사용자만 접근할 수 있다. 그 안의 파일에 other 쓰기 비트를 설정해도 다른 계정의 실제 접근을 시험한 것은 아니다. 이 실습은 파일 비트와 종류에 따른 선택을 대조하며 상위 경로 권한·ACL·마운트 정책에 따른 최종 접근 가능 여부는 조사하지 않는다.

준비기는 `path.chmod(mode)`로 자신이 만든 네 파일의 모드를 지정한다. 파일을 만든 시점의 umask에 기대지 않고 비교할 값을 직접 맞춘다. `collector`의 절대 경로와 임시 `root`를 수집기 인수로 전달한 뒤 반환 코드와 표준 오류를 살핀다. 이어 GNU find의 결과 이름을 정렬해 `open-note.txt`, `other-only.txt`와 비교하고 수집기의 후보 이름도 같은 목록인지 대조한다.

[[run:1]]

`group-only.txt`는 그룹 쓰기 `0020`이 있어도 other 쓰기 `0002`가 없어 후보에서 빠졌다. `shortcut`은 대상이 후보 파일이어도 링크 자체로 분류했다. 두 프로그램이 같은 일반 파일 두 개를 고른 것은 가상 자료에서 선택 조건이 일치한 결과다. 파일마다 권한을 설정한 업무상 이유까지 수집한 결과는 아니다.

안쪽 수집기의 종료 0은 항목 여섯 개를 읽어 결과를 만들었다는 뜻이다. 바깥 준비기의 종료 0은 수집기·GNU find의 후보 비교와 임시 폴더 정리가 끝났다는 뜻이다. 준비나 수집·비교에 오류가 있으면 2로 끝나며 표준 오류에서 수집기 경로, `/tmp`, GNU find를 살핀다. 준비기가 만든 임시 폴더는 예외로 빠져나올 때도 문맥 관리자에서 정리한다.

실제 점검 목록에는 경로·종류·권한과 설정 이유를 함께 남긴다. 일반 파일 검색에서 제외된 디렉터리·링크와 접근할 수 없었던 경로는 조사 범위의 차이로 구분한다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [GNU find(1): 파일 종류와 권한 비트 검색](https://man7.org/linux/man-pages/man1/find.1.html)
- [Python 3.12 stat: 파일 종류와 모드 해석](https://docs.python.org/3.12/library/stat.html)
- [Python 3.12 tempfile: 임시 디렉터리의 생성과 정리](https://docs.python.org/3.12/library/tempfile.html)
