---
title: "U-26: /dev에 존재하지 않는 device 파일 점검"
description: "장치처럼 보이는 이름과 실제 파일 종류를 구분합니다. Linux 임시 폴더에서 일반 파일·링크·FIFO를 분류하고 GNU find 결과와 예외 영역을 대조합니다."
date: "2026-11-01T18:37:03+09:00"
sourcesChecked: "2026-11-01"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "파일 종류", "KISA"]
draft: false
series: unix-2026
seriesOrder: 26
---

아래 실습에서 만든 `console`은 일반 파일로 분류됐다. 장치처럼 보이는 이름을 붙여도 텍스트를 저장한 일반 파일의 종류가 바뀌지는 않는다. U-26의 `/dev` 점검을 이해하려면 이름, 파일 종류, 그 파일이 필요한 이유를 나눠 살펴야 한다.

## 문자·블록 장치와 일반 파일

[Linux inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html)은 `st_mode`에 파일 종류와 모드가 들어간다고 설명한다. Python에서는 [stat 모듈의 종류 검사 함수](https://docs.python.org/3.12/library/stat.html)로 같은 값을 해석할 수 있다.

| 종류 | Python 검사 | 이 글의 비교 방식 |
| --- | --- | --- |
| 일반 파일 | `stat.S_ISREG(mode)` | 임시 폴더에서 직접 생성·조회 |
| 문자 장치 | `stat.S_ISCHR(mode)` | 메모리의 가상 모드 정수만 해석 |
| 블록 장치 | `stat.S_ISBLK(mode)` | 메모리의 가상 모드 정수만 해석 |
| 심볼릭 링크 | `stat.S_ISLNK(mode)` | 링크 자체의 종류를 조회 |
| FIFO | `stat.S_ISFIFO(mode)` | 임시 폴더에서 생성하고 열지 않음 |

장치 파일이 나타내는 장치의 major·minor 번호는 `st_rdev`와 연결된다. `st_dev`는 파일이 놓인 파일시스템의 장치를 나타내므로 `st_rdev`와 구분한다. 종류는 `st_mode`로 먼저 나누고 장치를 나타내는 파일에서 해당 장치 정보를 해석한다. 파일 이름이나 숫자 하나만으로 장치 파일 여부를 대신 판정하지 않는다.

## 공식 기준과 53쪽의 다른 문구

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-26은 ‘/dev에 존재하지 않는 device 파일 점검’이며 중요도는 ‘상’이다. 항목표와 본문 53쪽에서 제목·중요도가 같고, 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다.

판단 기준은 `/dev`의 파일을 점검한 뒤 존재하지 않는 device 파일을 제거한 경우를 양호로, 파일을 점검하지 않았거나 해당 파일을 방치한 경우를 취약으로 구분한다. 보안 위협에는 rootkit 설정 파일이 장치 파일처럼 위장될 가능성이 적혀 있다. 검색 결과에는 생성 주체·용도·불필요한 파일인지 조사한 내용이 더해져야 한다.

같은 쪽 개요의 ‘점검 내용’과 ‘점검 목적’에는 접속 IP주소·포트 제한 문구가 들어 있다. 항목명과 보안 위협, 판단 기준, 조치 사례의 파일 점검 설명과 맞지 않는 부분이다. 이 글은 그 차이를 남기고 파일 종류를 조회하는 사례를 설명한다.

원문의 검색 명령은 `/dev` 아래에서 `-type f`인 일반 파일을 찾는다. [GNU find(1)](https://man7.org/linux/man-pages/man1/find.1.html)에서 `f`는 일반 파일이며 문자 장치 `c`, 블록 장치 `b`, 링크 `l`, FIFO `p`와 다르다. 이 글의 실행 코드는 검색 대상을 준비기가 만든 임시 폴더로 한정한다.

[[diagram]]

가이드는 `mqueue`, `shm`을 시스템에서 생성·제거가 일어나는 예외로 적고 있다. 아래 분류기는 그 이름의 영역을 따로 표시하면서도 일반 파일 목록에는 남긴다. 이름이 같다는 이유로 양호 처리하거나 파일 삭제를 지시하는 기능은 넣지 않았다.

## 빈 폴더에서 가상 dev 자료 실행하기

Linux 또는 WSL Ubuntu에서 Python 3.9 이상과 GNU find를 사용한다. 실제 실행 환경은 WSL Ubuntu 24.04, Python 3.12.3이다. FIFO·심볼릭 링크와 Linux 파일 종류를 다루므로 Windows Python으로 실행하지 않는다. 관리자 권한·별도 패키지·네트워크 연결은 필요하지 않다.

ZIP을 빈 폴더에 풀고 `u26_fixture_lab.py`, `u26_file_types.py`가 함께 있는 글별 폴더로 이동한다. 준비기가 `/tmp`에 일반 파일 네 개, 디렉터리 두 개, 링크와 FIFO를 각각 한 개 만든다. 입력을 따로 만들거나 운영 `/dev`를 지정할 필요는 없다.

[[download]]

```bash
python3 -I -B -X utf8 u26_fixture_lab.py ./u26_file_types.py
```

명령 직후 `echo $?`로 종료 코드를 읽는다. `shm`, `mqueue`는 이 실습의 보통 디렉터리 이름이며 실제 공유 메모리·메시지 큐 파일시스템을 마운트한 것이 아니다. 문자·블록 장치도 만들지 않는다.

다음은 파일 종류와 조사 구분을 만드는 수집기 전체 코드다.

```python
import argparse
import os
from pathlib import Path
import stat
import sys


def file_kind(mode):
    for test, name in ((stat.S_ISREG, "file"), (stat.S_ISDIR, "dir"),
                       (stat.S_ISLNK, "link"), (stat.S_ISFIFO, "fifo"),
                       (stat.S_ISCHR, "char"), (stat.S_ISBLK, "block"),
                       (stat.S_ISSOCK, "socket")):
        if test(mode):
            return name
    return "other"


def collect(root):
    root = root.resolve(strict=True)
    if root.parent != Path("/tmp") or not root.name.startswith("u26-fixture-"):
        raise ValueError("준비기가 만든 /tmp 실습 폴더만 지정한다")
    if (root / ".u26-fixture").read_text(encoding="utf-8") != "synthetic-u26\n":
        raise ValueError("실습 폴더 표지가 맞지 않는다")
    rows = []

    def visit(folder):
        with os.scandir(folder) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                path = Path(entry.path)
                if path == root / ".u26-fixture":
                    continue
                relative = path.relative_to(root)
                kind = file_kind(entry.stat(follow_symlinks=False).st_mode)
                review = "검색 대상 아님"
                if kind == "file":
                    review = "예외 영역 검토" if relative.parts[0] in {"shm", "mqueue"} else "일반 파일 조사"
                rows.append((relative.as_posix(), kind, review))
                if kind == "dir":
                    visit(path)

    visit(root)
    return sorted(rows)


def main():
    parser = argparse.ArgumentParser(description="가상 dev 자료의 파일 종류를 분류한다")
    parser.add_argument("lab", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        print("이 실습은 Linux의 /tmp에서 실행한다", file=sys.stderr)
        return 2
    try:
        rows = collect(args.lab)
    except (OSError, ValueError, UnicodeError):
        print("수집 오류: 실습 경로·표지·읽기 권한을 살핀다", file=sys.stderr)
        return 2
    for name, kind, review in rows:
        print(f"{name}: {kind}, {review}")
    regular = sum(kind == "file" for _, kind, _ in rows)
    exceptions = sum(review == "예외 영역 검토" for _, _, review in rows)
    print(f"항목 {len(rows)}건, 일반 파일 {regular}건, 예외 영역 {exceptions}건")
    for label, mode in (("문자", stat.S_IFCHR | 0o600), ("블록", stat.S_IFBLK | 0o600)):
        print(f"메모리 모드 예시 {label}: {file_kind(mode)}, {stat.filemode(mode)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`collect()`는 `/tmp/u26-fixture-`로 시작하는 폴더와 `.u26-fixture` 표지를 읽는다. `visit()`는 폴더마다 `os.scandir()`로 항목을 열거하고 `entry.stat(follow_symlinks=False).st_mode`를 `file_kind()`에 넘긴다. 표지 외의 파일 내용은 읽지 않으며 FIFO도 열지 않는다. 디렉터리일 때만 재귀 호출하므로 링크가 가리키는 폴더로 따라가지 않는다.

`mqueue/notice`에서는 `relative.parts`가 `("mqueue", "notice")`이고 `kind`는 `file`이다. 일반 파일 조건이 참이므로 첫 경로 성분 `mqueue`를 비교해 `review`에 ‘예외 영역 검토’를 넣는다. 반면 `mqueue` 디렉터리 자체는 `dir`이므로 일반 파일 분기에 들어가지 않는다. `console`은 같은 일반 파일이어도 첫 성분이 예외 이름이 아니어서 ‘일반 파일 조사’로 남는다.

`device-link`에는 링크의 모드가 들어가 `link`가 반환된다. 링크 대상 `console`의 일반 파일 속성을 링크 행에 복사하지 않는다. `main()` 마지막의 `stat.S_IFCHR | 0o600`, `stat.S_IFBLK | 0o600`은 메모리에만 있는 정수다. 출력의 `char`, `block`과 `crw-------`, `brw-------`는 그 정수를 해석한 결과이며 실제 장치를 조회한 기록이 아니다.

## GNU find와 같은 네 파일이 선택됐는지

준비기는 같은 가상 자료에 수집기와 GNU find를 차례로 적용한다. 다음 전체 코드를 ZIP에도 함께 제공한다.

```python
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description="자신이 만든 가상 dev 자료만 비교한다")
    parser.add_argument("collector", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        print("이 준비기는 Linux의 /tmp에서 실행한다", file=sys.stderr)
        return 2
    try:
        collector = args.collector.resolve(strict=True)
        if not collector.is_file():
            raise ValueError("수집기 파일이 필요하다")
        with tempfile.TemporaryDirectory(prefix="u26-fixture-", dir="/tmp") as temporary:
            root = Path(temporary)
            (root / ".u26-fixture").write_text("synthetic-u26\n", encoding="utf-8")
            for name in ("shm", "mqueue"):
                (root / name).mkdir()
            for name in ("console", "notes.txt", "shm/cache.bin", "mqueue/notice"):
                (root / name).write_text("synthetic\n", encoding="utf-8")
            (root / "device-link").symlink_to("console")
            os.mkfifo(root / "pipe", 0o600)
            run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(collector), str(root)], capture_output=True, text=True, encoding="utf-8", timeout=10)
            if run.returncode != 0 or run.stderr:
                raise ValueError("수집기가 정상 종료하지 않았다")
            found = subprocess.run(["find", "-P", str(root), "-type", "f", "!", "-name", ".u26-fixture", "-printf", "%P\n"], capture_output=True, text=True, encoding="utf-8", timeout=10)
            names = sorted(found.stdout.splitlines())
            expected = ["console", "mqueue/notice", "notes.txt", "shm/cache.bin"]
            if found.returncode != 0 or found.stderr or names != expected:
                raise ValueError("GNU find의 일반 파일이 예상과 다르다")
            collected = [line.split(":", 1)[0] for line in run.stdout.splitlines() if ": file, " in line]
            if collected != names:
                raise ValueError("수집기와 GNU find의 일반 파일이 다르다")
            print(run.stdout, end="")
            print("GNU find 일반 파일: " + ", ".join(names))
        print("대조 완료: 일반 파일 4건 일치, 생성한 임시 폴더 정리")
    except (OSError, ValueError, subprocess.SubprocessError):
        print("준비 오류: 수집기 경로·Linux 임시 폴더·GNU find를 살핀다", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`TemporaryDirectory`는 `/tmp` 안에 자신만 접근할 수 있는 임시 상위 폴더를 만든다. `os.mkfifo()`는 FIFO를 생성할 뿐 열지 않는 함수다. 준비기와 수집기 모두 FIFO의 입출력을 시도하지 않으므로 읽기 상대를 기다리는 동작이 없다. [Python os의 mkfifo 설명](https://docs.python.org/3.12/library/os.html#os.mkfifo)과 같은 범위다.

`collector`와 `root`의 절대 경로를 안쪽 Python에 전달하고 종료 코드·표준 오류를 먼저 비교한다. GNU find에는 링크를 따라가지 않는 `-P`와 `-type f`를 준다. `.u26-fixture`는 실습 표지라 검색에서 빼고 `%P`로 임시 루트 아래의 상대 경로만 출력한다. 정렬한 네 이름을 `expected`와 대조한 뒤 수집기의 `: file, ` 행에서도 같은 이름이 나왔는지 비교한다.

[[run:1]]

일반 파일 네 개에는 `mqueue/notice`, `shm/cache.bin`도 포함됐다. 수집기는 그 둘을 예외 영역으로 표시했지만 검색에서 지우지는 않았다. 따라서 ‘일반 파일 4건’과 ‘예외 영역 2건’은 서로 독립된 여섯 파일을 센 값이 아니라 네 파일 중 두 파일의 조사 구분이다. 파일시스템 항목 여덟 개에는 메모리 모드 예시 두 건이 포함되지 않는다.

안쪽 수집기의 종료 0은 항목 분류를 마쳤다는 뜻이다. 바깥 준비기의 종료 0은 두 도구의 일반 파일 네 경로가 같고 임시 폴더 정리가 끝났다는 뜻이다. 경로·표지·수집 실패나 비교 오류는 2로 끝난다. 표준 오류가 나오면 같은 폴더의 두 Python 파일, Linux `/tmp`, GNU find를 살핀다. 정상·실패 모두 준비기가 만든 임시 폴더만 문맥 관리자에서 정리한다.

운영 점검에서는 검색된 경로의 생성 주체와 용도, 예외 영역 여부, 패키지·시스템 구성과의 대응을 남긴다. 장치처럼 보이는 이름과 일반 파일 검색 결과를 곧바로 삭제 목록으로 바꾸지 않고, 원문의 제거 대상에 해당하는지 조사한 자료로 구분한다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux inode(7): 파일 종류와 장치 식별 정보](https://man7.org/linux/man-pages/man7/inode.7.html)
- [GNU find(1): 파일 종류와 링크 처리](https://man7.org/linux/man-pages/man1/find.1.html)
- [Python 3.12 stat: 파일 종류 해석](https://docs.python.org/3.12/library/stat.html)
- [Python 3.12 os: FIFO 생성](https://docs.python.org/3.12/library/os.html#os.mkfifo)
- [Python 3.12 tempfile: 임시 디렉터리 생성과 정리](https://docs.python.org/3.12/library/tempfile.html)
