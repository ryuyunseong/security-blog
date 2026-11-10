---
title: "U-32: 홈 디렉토리로 지정한 디렉토리의 존재 관리"
description: "계정의 홈 필드와 실제 경로의 존재 여부를 연결합니다. 임시 폴더에서 디렉터리·부재·일반 파일을 구분하고 미수집·조회 오류를 부재로 처리하지 않는 분기를 따라갑니다."
date: "2026-11-09T18:42:10+09:00"
sourcesChecked: "2026-11-09"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "홈 디렉터리", "경로", "KISA"]
draft: false
series: unix-2026
seriesOrder: 32
---

계정 자료에 홈 경로가 `/srv/worker`로 적혀 있다면 `/home` 목록만 살펴서는 그 계정의 홈이 있는지 알 수 없어요. 계정이 지정한 경로를 조회해 디렉터리인지까지 살펴야 해요. 같은 이름의 일반 파일이 있어도 사용자의 작업 디렉터리로 들어갈 수는 없으니까요.

## 계정에 적힌 경로를 점검 대상으로 삼기

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-32는 ‘홈 디렉토리로 지정한 디렉토리의 존재 관리’이며 중요도는 ‘중’이에요. 항목표 9쪽과 본문 66쪽의 코드·제목·중요도가 일치하고 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이에요.

양호 기준은 홈 디렉토리가 존재하지 않는 계정이 발견되지 않는 경우이고 취약 기준은 그런 계정이 발견된 경우예요. 조치 사례에는 사용 중인 계정의 홈 설정과 불필요한 계정의 제거가 나와요. 실제 조치 전에는 계정의 사용 목적과 필요한 경로를 조사해요. 아래 실습에서는 계정이나 홈 설정을 변경하지 않아요.

[passwd(5)](https://man7.org/linux/man-pages/man5/passwd.5.html)의 레코드는 콜론으로 나뉘며 여섯 번째 `directory` 필드가 홈 경로예요. 예를 들어 가상 레코드 `worker:x:1001:1001::/srv/worker:/bin/sh`에서 조회할 경로는 `/srv/worker`예요. 이 글의 코드는 레코드를 수집·파싱하지 않고 홈 문자열을 코드 안에 준비해요. 실제 점검에서는 계정 자료의 출처·대상·시점과 경로 조회 자료를 함께 남겨야 해요.

가이드는 홈이 없을 때 로그인 작업 위치가 `/`가 되는 위험을 설명해요. 이것이 root 계정의 권한을 얻는다는 뜻은 아니고 실제 로그인 처리는 구현과 설정에 따라 달라져요. 예를 들어 [shadow-utils의 login.defs(5)](https://man7.org/linux/man-pages/man5/login.defs.5.html)는 `DEFAULT_HOME`이 `yes`이면 홈으로 이동할 수 없을 때 `/`에서 로그인을 허용하며 기본값은 `no`라고 설명해요. 실습에서는 로그인이나 이 설정을 시험하지 않아요.

경로를 조사한 자료가 없다면 ‘없음’으로 채우지는 않아요. 조회 성공 여부를 먼저 나눠야 부재와 보류가 뒤섞이지 않아요.

[[diagram]]

디렉터리 존재와 경로 부재는 모두 조회에서 얻은 결과예요. 반면 조회 오류나 자료 미수집은 존재 여부를 판단할 근거가 부족한 상태이므로 보류해요. 이 구분을 거친 뒤에야 경로의 존재와 종류를 비교할 수 있어요.

실제 수집 상황이 아래 입력과 어떻게 이어지는지 살펴볼게요.

- 해당 경로를 조회할 자료가 준비됐다면 `collected`로 둬요. 실습은 이 상태에서 자신이 만든 임시 경로를 직접 조회하며 디렉터리, 없는 경로, 일반 파일의 차이를 실제로 관찰해요.
- 조회가 실패한 상황은 `read_error`, 자료 자체를 전달받지 못한 상황은 `uncollected`로 둬요. 이 두 입력은 실제 접근 거부를 일으켜 수집한 결과가 아니라 가상 상황이므로, 코드는 경로 조회 전에 보류를 반환해요.
- 빈 홈 필드, `/`, 상대 경로, `..`가 든 경로는 각각 이유를 남기고 보류해요. 특히 `/`가 적혀 있다고 없는 홈으로 바꾸지 않고 계정 목적과 설정을 따로 조사할 대상으로 둬요.

## 빈 폴더에서 열 가지 상황 실행하기

Python 3.12 이상과 표준 라이브러리만 사용해요. 아래 기록은 Windows Python 3.12.1에서 얻었으며 PowerShell과 Git Bash의 같은 명령을 검증했어요. 관리자 권한과 별도 패키지는 필요하지 않아요. Windows에서 관찰한 것은 임시 파일의 존재·종류이며 Unix 권한이나 로그인 동작은 아니에요.

ZIP을 빈 폴더에 풀고 `README.md`와 `u32_home_lab.py`가 함께 있는 글별 폴더에서 실행해요. 별도 입력 파일을 만들 필요는 없어요. 프로그램이 운영체제의 임시 폴더 아래에 자신만의 `u32-home-` 폴더를 만들고 그 안에 `home/alpha`, `srv/worker` 디렉터리와 `home/not-dir` 일반 파일을 준비해요. Linux에서 실행하면 기본 임시 위치는 보통 `/tmp`이며 실제 위치는 환경 설정에 따라 달라져요. `/home/absent` 같은 홈 문자열도 이 임시 폴더 안으로만 대응시켜요.

[[download]]

```bash
python -I -B -X utf8 u32_home_lab.py --case all
```

`-I`는 Python의 격리 실행, `-B`는 바이트코드 파일 생성 방지, `-X utf8`은 UTF-8 모드예요. 파일시스템 격리는 이 옵션이 아니라 프로그램의 임시 경로 사용과 고정 입력으로 제한해요. `--case all`은 코드의 열 가지 입력을 모두 골라요. 명령 직후 PowerShell에서는 `$LASTEXITCODE`, Bash에서는 `echo $?`로 숫자 종료 코드를 읽어요. PowerShell의 `$?`는 성공 여부이므로 숫자 코드와 구분해요. README에서 사용하는 셸의 블록 하나를 선택하면 돼요.

다음은 ZIP과 같은 전체 코드예요. `TemporaryDirectory`의 범위를 벗어나면 정상·예외 경로 모두 자신이 만든 임시 자료의 정리를 시도해요. 운영 계정·인증 설정이나 실제 홈 폴더를 읽고 바꾸는 기본 경로는 없어요. 아래 함수는 고정된 가상 자료를 위한 실습 코드이며 다른 사용자가 동시에 바꾸는 임의 경로를 안전하게 수집하는 도구로 사용하지 않아요.

```python
import argparse
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile


CASES = (
    ("existing", "/home/alpha", "collected", "디렉터리 존재"),
    ("outside-home", "/srv/worker", "collected", "디렉터리 존재"),
    ("missing", "/home/absent", "collected", "부재 후보"),
    ("ordinary-file", "/home/not-dir", "collected", "종류 확인"),
    ("empty", "", "collected", "보류"),
    ("root-home", "/", "collected", "보류"),
    ("uncollected", "/home/unsampled", "uncollected", "보류"),
    ("query-error", "/home/denied", "read_error", "보류"),
    ("relative", "home/alpha", "collected", "보류"),
    ("parent-part", "/home/../escape", "collected", "보류"),
)


def probe_home(root, home, source_state):
    if source_state == "uncollected":
        return "보류", "가상 미수집 상태: 경로 조회 안 함"
    if source_state == "read_error":
        return "보류", "가상 조회 오류 상태: 경로 조회 안 함"
    if source_state != "collected":
        raise ValueError("알 수 없는 수집 상태")
    if not home:
        return "보류", "홈 필드가 비어 있음"
    if home == "/":
        return "보류", "루트 경로: 계정 목적 별도 조사"
    if ".." in home.split("/"):
        return "보류", "상위 경로 성분 거부"
    if not re.fullmatch(r"/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", home):
        return "보류", "실습에서 허용하지 않는 경로 표기"

    candidate = root
    for part in PurePosixPath(home).parts[1:]:
        candidate = candidate / part
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            return "부재 후보", "임시 경로의 성분이 없음"
        except OSError:
            return "보류", "실제 임시 경로 조회 오류"
        reparse = getattr(info, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
        )
        if stat.S_ISLNK(info.st_mode) or reparse:
            return "보류", "링크 또는 재분석 지점: 따라가지 않음"
        if not stat.S_ISDIR(info.st_mode):
            return "종류 확인", "임시 경로의 성분이 디렉터리가 아님"
    return "디렉터리 존재", "임시 경로의 모든 성분이 디렉터리"


def run_lab(selected):
    with tempfile.TemporaryDirectory(prefix="u32-home-") as tmp:
        root = Path(tmp)
        (root / "home" / "alpha").mkdir(parents=True)
        (root / "srv" / "worker").mkdir(parents=True)
        (root / "home" / "not-dir").write_text("fixture\n", encoding="utf-8")
        for case_id, home, state, expected in selected:
            status, reason = probe_home(root, home, state)
            if status != expected:
                raise RuntimeError(f"{case_id}: 기대 상태 불일치")
            print(f"{case_id}: {status} ({reason})")
    if root.exists():
        raise RuntimeError("임시 자료가 남아 있음")
    print(f"기대 상태 {len(selected)}건 일치")
    print("임시 자료 정리 완료")


def main():
    parser = argparse.ArgumentParser(description="가상 홈 경로의 임시 파일 실습")
    parser.add_argument("--case", choices=["all"] + [row[0] for row in CASES], default="all")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        print("실행 오류: Python 3.12 이상이 필요합니다.", file=sys.stderr)
        return 2
    selected = [row for row in CASES if args.case in ("all", row[0])]
    try:
        run_lab(selected)
    except (OSError, ValueError):
        print("실행 오류: 임시 자료 준비·조회·정리를 살펴보세요.", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"실습 검증 실패: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`probe_home()`은 경로 성분마다 `lstat()`으로 종류를 읽어요. [Python pathlib 문서](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.lstat)는 이 메서드가 심볼릭 링크 자체의 정보를 돌려준다고 설명해요. 코드에서는 링크 또는 Windows 재분석 지점 표시를 발견하면 그 아래로 진행하지 않아요. 이번 열 가지 입력에는 링크를 만들지 않았으므로 링크 접근을 실제로 관찰한 결과로 읽지는 않아요.

## missing이 부재 후보가 되는 순서

위 명령은 `main()`에서 `args.case`를 `all`로 읽고 `selected`에 `CASES`의 열 행을 담아요. `run_lab(selected)`가 임시 자료를 만든 뒤 세 번째 행인 `("missing", "/home/absent", "collected", "부재 후보")`를 꺼내요. 여기서 `expected`는 실습의 고정된 기대값이며 운영 점검의 판정값을 입력받는 필드는 아니에요.

`probe_home(root, "/home/absent", "collected")`에서는 미수집·가상 오류 분기를 지나가요. 홈 문자열은 비어 있지 않고 `/`도 아니며 `..`도 없어요. `re.fullmatch()`의 허용 표기에 맞으므로 `PurePosixPath(home).parts[1:]`는 `("home", "absent")`가 돼요. 첫 `/`를 실제 운영체제의 루트로 결합하지 않고 성분 이름만 사용해요.

처음의 `candidate = root`에서 `home`을 붙인 경로는 준비 과정에서 만든 디렉터리예요. `lstat()`이 반환한 `info.st_mode`에 대해 `stat.S_ISDIR()`가 참이므로 반복을 계속해요. 두 번째 성분 `absent`를 붙이면 그 임시 경로는 만들지 않았기 때문에 `FileNotFoundError`가 나요. 이 예외를 먼저 잡아 `("부재 후보", "임시 경로의 성분이 없음")`을 반환해요. 다른 `OSError`는 뒤의 분기에서 보류하므로 조회 오류를 부재로 합치지 않아요.

반환한 `status`가 이 행의 `expected`와 같으면 `run_lab()`이 ID·상태·이유를 합쳐 출력해요. 아래 실제 실행 기록의 `missing: 부재 후보 (임시 경로의 성분이 없음)` 행이 그 결과예요.

[[run:1]]

`outside-home`은 임시 폴더의 `srv/worker`까지 두 성분이 모두 디렉터리여서 ‘디렉터리 존재’예요. `/home` 밖이라는 문자열만으로 부재로 분류하지 않아요. `ordinary-file`은 마지막 성분의 조회에는 성공하지만 `stat.S_ISDIR(info.st_mode)`가 거짓이어서 ‘종류 확인’이 돼요. 홈으로 지정된 위치의 종류를 다시 조사하라는 뜻이에요.

`uncollected`와 `query-error`는 임시 경로를 조회하기 전에 반환해요. 그러므로 이 출력은 해당 경로가 실제로 없거나 권한 오류를 냈다는 증거가 아니에요. `relative`와 `parent-part`도 입력 표기 단계에서 멈추며 운영 경로로 이동하지 않아요. 경로의 허용 문자는 이 실습을 위한 제한이므로 공백·한글이 든 모든 Unix 홈 경로가 잘못됐다는 일반 기준으로 확대하지 않아요.

마지막 ‘기대 상태 10건 일치’는 디렉터리 존재 2건, 부재 후보 1건, 종류 확인 1건, 보류 6건이 각 고정 기대값과 같다는 뜻이에요. 보류가 포함된 시험의 종료 0을 양호 계정 열 개로 세지는 않아요. ‘임시 자료 정리 완료’는 임시 폴더를 정리한 뒤 출력하며 ZIP을 푼 폴더의 원본은 그대로 남아요.

종료 1은 기대 상태나 정리 후 검증의 불일치를 나타내요. 종료 2는 잘못된 `--case`, Python 버전 조건 또는 임시 자료 준비·정리 과정에서 바깥으로 전달된 실행 오류예요. 오류는 표준 오류로 나오며 중간까지 출력됐다면 일부 행만 성공한 결과일 수 있으므로 종료 코드도 함께 읽어요. 경로 조회 중 잡은 `OSError`는 행의 보류가 되고 고정 기대값과 어긋나면 실습 검증 실패로 이어져요. 각 행의 보류와 프로그램 전체의 실행 오류를 구분해요. 바깥 셸을 실행하는 도구의 성공 여부보다 바로 앞 Python의 숫자 종료 코드를 기준으로 삼아요.

운영 자료에서 부재 후보를 발견하면 계정이 지정한 경로와 조회 시점이 같은지, 필요한 마운트가 제공됐는지, 링크의 실제 대상은 무엇인지 조사해요. 존재하는 홈의 소유자·쓰기 권한은 [U-31](/security-blog/posts/u-31-home-owner-permissions/)의 별도 비교 대상이에요. 경로가 있다는 관찰에 권한·실제 로그인까지 성공했다는 의미를 덧붙이지 않아요.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Linux man-pages: passwd(5)](https://man7.org/linux/man-pages/man5/passwd.5.html)
- [shadow-utils: login.defs(5)](https://man7.org/linux/man-pages/man5/login.defs.5.html)
- [Python 3.12: pathlib와 lstat](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.lstat)
- [Python 3.12: stat의 파일 종류와 Windows 속성](https://docs.python.org/3.12/library/stat.html)
