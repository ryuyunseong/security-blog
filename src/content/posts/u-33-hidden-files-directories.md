---
title: "U-33: 숨겨진 파일 및 디렉토리 검색 및 제거"
description: "점으로 시작하는 이름과 숨김 디렉터리 안의 일반 이름 파일을 구분합니다. 임시 트리 검색과 가상 조회 오류를 비교하고 검색 후보를 삭제 대상으로 판단하기 전에 필요한 자료를 설명합니다."
date: "2026-11-10T18:41:34+09:00"
sourcesChecked: "2026-11-10"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "숨김 파일", "디렉터리 검색", "KISA"]
draft: false
series: unix-2026
seriesOrder: 33
---

`.cache/session.txt`에서 점으로 시작하는 이름은 `.cache`다. 마지막 이름 `session.txt`에는 점이 앞에 붙지 않았지만 이 파일도 숨김 디렉터리의 내용을 조사할 때 살펴볼 대상이다. 반대로 `docs/.draft.txt`는 상위 디렉터리가 보통 이름이어도 마지막 이름 자체가 점으로 시작한다.

[GNU find 문서](https://man7.org/linux/man-pages/man1/find.1.html)의 `-name`은 상위 디렉터리를 뺀 마지막 이름을 패턴과 비교한다. 따라서 `-name '.*'`만으로 `.cache/session.txt`라는 파일 행까지 출력되는 것은 아니다. 숨김 디렉터리를 발견했다면 그 내부에 보통 이름으로 저장된 파일도 별도로 조사할 수 있어야 한다.

[[diagram]]

그림은 Unix의 점 이름 규칙을 설명한다. Windows의 숨김 속성과는 별개이며, 두 경로 모두 아래 임시 자료에 넣어 실제 검색한다.

## 숨김 이름과 U-33의 제거 기준

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-33은 ‘숨겨진 파일 및 디렉토리 검색 및 제거’이며 중요도는 ‘하’다. 항목표 9쪽과 본문 67쪽의 코드·항목명·중요도가 일치하고 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다.

양호 기준은 불필요하거나 의심스러운 숨겨진 파일 및 디렉토리를 제거한 경우, 취약 기준은 이를 제거하지 않은 경우다. 가이드는 숨김 영역에 비인가자가 만든 악성 파일이나 백도어가 남아도 탐지하지 못할 위험을 설명한다. 이름의 첫 글자만으로 불필요성이나 악성 여부까지 결정하는 기준은 아니다. 예를 들어 `.profile`처럼 설정에 쓰이는 이름도 있으므로 사용 목적과 내용·출처를 함께 조사한다.

가이드의 조치 사례에는 `ls -al`, 파일·디렉터리를 나눠 찾는 `find`, 제거 명령이 나온다. [GNU ls 문서](https://man7.org/linux/man-pages/man1/ls.1.html)의 `-a`는 점으로 시작하는 항목을 숨기지 않는 옵션이고 `-l`은 자세한 목록 형식이다. 목록에서 이름을 찾은 뒤 파일 종류와 용도를 조사하는 절차로 읽는다.

PDF의 파일 검색 줄에는 옵션 대시가 `–name`, 패턴 따옴표가 곡선 형태로 표시돼 있다. 여기서 구문을 설명할 때는 ASCII `-name '.*'`를 사용한다. 아래 실행 절차는 PDF의 시스템 전체 검색이나 제거 명령을 실행하지 않고 별도로 만든 작은 임시 트리만 검색한다.

수집 범위와 결과의 상태도 남겨야 한다. 특정 경로의 목록을 끝까지 읽은 자료가 있으면 그 범위에서 얻은 후보를 조사한다. 조회 오류가 있다면 읽은 경로의 후보는 남기되 오류 경로의 내부 결과는 미확정이다. 검색 자료 자체가 없으면 후보 수를 0으로 채우지 않고 미수집으로 둔다. 아래의 `complete`, `read-error`, `uncollected`는 이 차이를 비교하는 시나리오 이름이다. `read-error`는 코드가 넣은 가상 오류이며 실제 권한 거부를 수집한 기록이 아니다.

## 이름 검색을 재현할 임시 트리

Python 3.12 이상과 표준 라이브러리만 필요하다. Windows Python 3.12.1의 PowerShell·Git Bash에서 검증했으며 관리자 권한이나 별도 패키지는 사용하지 않았다. 점 이름과 상위 경로의 관계를 검사하므로 Linux 파일시스템이나 실제 사용자 홈을 준비할 필요는 없다. Unix 권한·악성 파일 탐지 기능을 검증하는 예제는 아니다.

ZIP을 빈 폴더에 풀고 `README.md`와 `u33_hidden_lab.py`가 있는 글별 폴더에서 실행한다. 입력 파일을 따로 만들지 않는다. 프로그램이 운영체제의 임시 폴더 아래에 자신만의 `u33-hidden-` 폴더를 만들고 `.cache`, `docs` 디렉터리와 다음 다섯 파일을 준비한다.

- `.profile`
- `.cache/session.txt`
- `docs/.draft.txt`
- `docs/readme.txt`
- `public.txt`

파일 내용은 모두 코드가 넣은 짧은 가상 문자열이다. Linux의 기본 임시 위치는 보통 `/tmp`이며 실제 위치는 환경 설정에 따른다. Windows에서는 Python이 고른 쓰기 가능한 임시 위치를 사용한다. 이 이름들은 모두 새 임시 폴더 안에만 만들며 실제 `.profile`이나 `.cache`를 읽지 않는다.

[[download]]

```bash
python -I -B -X utf8 u33_hidden_lab.py --scenario all
```

`main()`은 `--scenario all`을 세 시나리오로 펼쳐 `run_lab()`에 전달한다. 하나씩 실행하려면 `all` 대신 `complete`, `read-error`, `uncollected` 중 하나를 고른다. `-I`는 Python 격리 모드, `-B`는 바이트코드 생성 방지, `-X utf8`은 UTF-8 모드다. 이 옵션이 파일시스템을 격리하지는 않으며 대상 범위는 코드의 자체 임시 폴더로 제한한다.

명령 바로 뒤에서 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 Python의 숫자 종료 코드를 읽는다. PowerShell의 `$?`는 성공 여부다. README에는 각 셸의 명령과 종료 코드 조회를 나란히 제공하므로 사용하는 셸의 블록 하나를 선택한다.

다음은 ZIP과 같은 전체 코드다. `collect()`는 이름과 종류만 읽으며 파일 본문을 열거나 후보를 지우지 않는다. `os.scandir()`가 주는 항목에는 `.`과 `..`가 포함되지 않는다. 링크·Windows 재분석 지점은 보류로 남기고 그 아래로 재귀 호출하지 않는다. 이번 트리에는 링크를 만들지 않았다. 이 코드는 다른 사용자가 동시에 바꾸는 임의 경로를 안전하게 수집하는 도구로 쓰지 않는다.

```python
import argparse
import os
from pathlib import Path
import stat
import sys
import tempfile


EXPECTED_ROWS = [
    (".cache", "디렉터리", "이름 숨김"),
    (".cache/session.txt", "파일", "숨김 경로 내부"),
    (".profile", "파일", "이름 숨김"),
    ("docs/.draft.txt", "파일", "이름 숨김"),
]


def collect(root, unreadable=()):
    rows, issues = [], []

    def visit(folder, hidden_parent=False):
        relative = folder.relative_to(root).as_posix()
        if relative in unreadable:
            issues.append((relative, "가상 조회 오류"))
            return
        try:
            with os.scandir(folder) as stream:
                entries = sorted(stream, key=lambda entry: entry.name)
        except OSError:
            issues.append((relative, "디렉터리 조회 오류"))
            return
        for entry in entries:
            path = folder / entry.name
            name = path.relative_to(root).as_posix()
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                issues.append((name, "종류 조회 오류"))
                continue
            reparse = getattr(info, "st_file_attributes", 0) & getattr(
                stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
            )
            if stat.S_ISLNK(info.st_mode) or reparse:
                kind = "링크"
                issues.append((name, "링크 또는 재분석 지점 보류"))
            elif stat.S_ISDIR(info.st_mode):
                kind = "디렉터리"
            elif stat.S_ISREG(info.st_mode):
                kind = "파일"
            else:
                kind = "기타"
            named = entry.name.startswith(".")
            if named or hidden_parent:
                reason = "이름 숨김" if named else "숨김 경로 내부"
                rows.append((name, kind, reason))
            if kind == "디렉터리":
                visit(path, hidden_parent or named)

    visit(root)
    return rows, issues


def run_lab(scenarios):
    with tempfile.TemporaryDirectory(prefix="u33-hidden-") as tmp:
        root = Path(tmp)
        for name in [".cache", "docs"]:
            (root / name).mkdir()
        for name in [".profile", ".cache/session.txt", "docs/.draft.txt", "docs/readme.txt", "public.txt"]:
            (root / name).write_text("synthetic fixture\n", encoding="utf-8")
        for scenario in scenarios:
            if scenario == "uncollected":
                print("[uncollected] 검색 미실행")
                continue
            blocked = (".cache",) if scenario == "read-error" else ()
            rows, issues = collect(root, blocked)
            expected = EXPECTED_ROWS if not blocked else [row for row in EXPECTED_ROWS if row[0] != ".cache/session.txt"]
            expected_issues = [(".cache", "가상 조회 오류")] if blocked else []
            if rows != expected or issues != expected_issues:
                raise RuntimeError(f"{scenario}: 기대 결과 불일치")
            print(f"[{scenario}] 조사 후보 {len(rows)}건, 보류 {len(issues)}건")
            for row in rows:
                print(" | ".join(row))
            for name, reason in issues:
                print(f"보류: {name} ({reason})")
            print("검색 상태: " + ("일부 범위 보류" if issues else "지정한 가상 범위 순회 완료"))
    if root.exists():
        raise RuntimeError("임시 자료가 남아 있음")
    print(f"기대 결과 {len(scenarios)}개 시나리오 일치")
    print("임시 자료 정리 완료")


def main():
    parser = argparse.ArgumentParser(description="자체 임시 폴더의 점 이름 검색 실습")
    parser.add_argument("--scenario", choices=["all", "complete", "read-error", "uncollected"], default="all")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        print("실행 오류: Python 3.12 이상이 필요합니다.", file=sys.stderr)
        return 2
    scenarios = ["complete", "read-error", "uncollected"] if args.scenario == "all" else [args.scenario]
    try:
        run_lab(scenarios)
    except OSError:
        print("실행 오류: 임시 자료 준비·정리를 살펴보세요.", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"실습 검증 실패: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

다음 실제 출력은 한 번의 `all` 실행 결과다. 상대 경로는 프로그램이 만든 임시 폴더를 기준으로 표시한다. `complete`와 `read-error`는 같은 준비 자료를 사용하지만 `.cache` 안으로 들어가는지에 차이가 있다.

[[run:1]]

`complete`의 후보 4건은 점 이름 3건과 숨김 경로 내부 파일 1건이다. 보통 이름의 `docs`, `docs/readme.txt`, `public.txt`는 후보 목록에서 빠진다. `.profile`을 포함한 네 후보의 내용이 의심스럽다는 판정을 내린 결과는 아니다.

`read-error`에서는 `.cache`라는 디렉터리 이름까지 읽은 뒤 내부 조회를 가상으로 보류한다. 그래서 `.cache/session.txt`가 목록에 없고 후보가 3건으로 줄어든다. 해당 파일이 없거나 제거됐다는 뜻으로 읽어서는 안 된다. `issues`에는 `.cache`와 ‘가상 조회 오류’가 남아 ‘일부 범위 보류’를 출력한다. `uncollected`는 `collect()`를 호출하지 않고 ‘검색 미실행’만 출력한다.

## session.txt를 후보에 넣는 재귀 호출

대표 입력은 `--scenario all` 중 먼저 실행되는 `complete`다. `blocked`는 빈 튜플 `()`이고 `collect(root, blocked)`에서 `rows`, `issues`는 각각 빈 목록으로 시작한다. `visit(root)`의 `hidden_parent` 기본값은 `False`다.

루트 항목을 이름순으로 정렬하면 `.cache`를 먼저 처리한다. `entry.stat(follow_symlinks=False)`로 얻은 종류는 디렉터리이고, `entry.name.startswith(".")`가 참이어서 `named = True`다. `rows`에 `(".cache", "디렉터리", "이름 숨김")`을 넣은 뒤 `visit(path, hidden_parent or named)`를 호출한다. 이때 `False or True`의 결과인 `True`가 다음 호출로 전달된다.

그 안의 `session.txt`는 일반 파일이다. 마지막 이름의 첫 글자가 점이 아니어서 `named = False`이지만 전달받은 `hidden_parent = True`가 남아 있다. 따라서 `named or hidden_parent`는 참이고 `reason` 조건식은 ‘숨김 경로 내부’를 고른다. `rows`의 두 번째 항목은 `(".cache/session.txt", "파일", "숨김 경로 내부")`가 된다. 일반 파일이므로 다음 디렉터리 재귀 호출은 하지 않는다.

나머지 항목까지 처리한 `collect()`는 네 `rows`와 빈 `issues`를 반환한다. `run_lab()`이 고정한 `EXPECTED_ROWS`와 비교한 뒤 각 튜플을 `" | ".join(row)`로 합쳐 출력한다. 앞의 실제 기록에 있는 `.cache/session.txt | 파일 | 숨김 경로 내부` 한 줄이 이 과정의 결과다. `docs/.draft.txt`는 부모의 숨김 상태가 거짓이어도 자기 이름의 `named`가 참이어서 후보가 된다.

`read-error`에서는 `blocked = (".cache",)`이므로 `visit()`의 첫 분기가 디렉터리 내부 조회 전에 반환한다. 실제 `os.scandir()`나 종류 조회에서 `OSError`가 나면 별도의 ‘디렉터리 조회 오류’ 또는 ‘종류 조회 오류’로 남긴다. 이 예제에서는 고정 기대값과 결과가 다르면 실습 검증 실패로 종료하므로 실제 실행 오류가 났는데 마지막 성공 문구만 보고 통과로 처리하지 않는다.

끝의 ‘기대 결과 3개 시나리오 일치’와 종료 0은 준비한 가상 사례가 기대한 목록·보류 상태와 같았다는 뜻이다. 미수집·가상 오류 사례의 시험 성공을 운영 검색의 완료나 U-33 양호 판정으로 세지 않는다. 기대 결과·정리 검증 불일치는 종료 1, 잘못된 `--scenario`나 Python 버전 조건·바깥으로 전달된 임시 준비·정리 오류는 종료 2다. 표준 오류도 함께 읽고 준비 오류라면 Python 버전과 임시 폴더 쓰기 가능 여부를 살핀다.

`TemporaryDirectory`는 정상·예외 경로에서 자신이 만든 트리의 정리를 시도한다. 마지막 ‘임시 자료 정리 완료’는 이 정리 이후의 확인이며 후보를 조사해 불필요한 것만 제거했다는 U-33 조치 결과가 아니다. ZIP을 푼 폴더와 원본 코드는 남긴다.

실제 점검의 후보에는 대상 경로·수집 시점·조회 오류, 파일 종류·소유자·권한, 생성 주체와 사용 목적, 내용과 배포 출처를 대조할 자료를 붙인다. 불필요하거나 의심스러운 대상으로 판단한 근거와 조치 이후의 재검색 결과도 구분해 남긴다. 이름 검색 결과만 삭제 목록으로 넘기면 정상 설정 파일과 필요한 캐시까지 섞일 수 있으므로 삭제 대상은 그 판단을 마친 개별 경로로 정한다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [GNU findutils: find(1)의 이름 패턴과 순회](https://man7.org/linux/man-pages/man1/find.1.html)
- [GNU Coreutils: ls(1)의 숨김 항목 표시](https://man7.org/linux/man-pages/man1/ls.1.html)
- [Python 3.12: os.scandir와 DirEntry](https://docs.python.org/3.12/library/os.html#os.scandir)
