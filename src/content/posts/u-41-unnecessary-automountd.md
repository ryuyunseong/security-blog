---
title: "U-41: 불필요한 automountd 제거"
description: "프로세스 목록에 automountd가 보일 때 이름과 검색 인수를 어떻게 구별할까요? 가상 PID 세 줄에서 이름 후보 하나가 남는 과정을 따라가며 서비스 활성화 판단에 필요한 자료를 살펴봐요."
date: "2026-11-19T18:37:57+09:00"
sourcesChecked: "2026-11-19"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "Linux", "autofs", "automountd", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 41
---

자동 마운트는 디렉터리가 필요해지는 순간에 파일시스템을 연결해 주는 기능이에요. 이 일을 맡은 데몬을 찾으려고 프로세스 목록에서 `automountd`를 검색하면 뜻밖에도 두 줄이 보일 수 있어요. 한 줄에는 데몬의 이름이, 다른 줄에는 방금 검색할 때 입력한 **검색어**가 적혀 있기 때문이에요. 두 줄을 어떻게 구별할지 가상 자료로 살펴볼게요.

## U-41에서 판정하는 대상

KISA의 2026년 가이드 93\~95쪽에서 U-41의 중요도는 **상**이에요. Solaris, Linux, AIX, HP-UX 등을 대상으로 automountd 서비스가 비활성화돼 있으면 양호, 활성화돼 있으면 취약으로 판단해요. 가이드는 불필요한 데몬을 켜 두었을 때 로컬 사용자의 RPC 요청으로 마운트 옵션이나 데몬 권한이 악용될 위험을 설명해요.

서비스를 끄면 자동으로 연결하던 경로에도 영향이 가요. 가이드는 NFS·Samba의 사용 여부와 `/etc/auto.*`, `/etc/auto_*`에 해당하는 설정을 먼저 살피도록 안내해요. CD-ROM 자동 마운트도 영향 범위에 들어가요. Linux 예시에서 현재 서비스의 중지와 이후 기동 설정의 비활성화를 따로 다루는 이유도 여기에 있어요. 지금 멈춰 있다는 관찰과 다음 부팅 때 어떤 서비스가 시작될지는 서로 다른 자료로 설명해야 해요.

## 검색한 단어가 어느 자리에 있을까요?

AIX와 HP-UX의 가이드 예시에는 프로세스 목록에서 이름을 찾는 단계가 있어요. 아래 실습에서는 그때 보일 법한 줄을 PID와 인수 배열로 나눠 JSON에 넣었어요. PID는 한 프로세스의 번호이고 `argv[0]`은 프로그램을 시작할 때 넘긴 첫 문자열이에요. 뒤에 붙는 검색어나 옵션과 구별할 수 있도록 인수를 미리 나눴어요. 실제 `ps` 출력에서 공백을 잘라 이 배열을 복원하는 실습은 아니에요.

Python 3.12와 표준 라이브러리를 사용해요. ZIP을 빈 폴더에 풀고 `README.md`, `u41_process_names.py`, `u41_cases.json`, `u41_rejected.json`이 함께 있는 폴더로 이동하세요. 입력에 적힌 Unix 경로는 문자열이어서 그 경로나 프로세스를 만들 필요가 없어요. 일반 사용자 권한으로 실행하며 프로그램은 인수로 지정한 JSON만 읽어요.

[[download]]

PowerShell이나 Bash에서 다음 명령으로 아홉 사례를 한 번에 읽을 수 있어요. 실행 직후 숫자 종료 코드는 PowerShell에서 `$LASTEXITCODE`, Bash에서는 `echo $?`로 읽어요. PowerShell의 `$?`는 성공 여부를 나타내는 참·거짓 값이에요.

```bash
python -I -B -X utf8 u41_process_names.py u41_cases.json
```

입력 목록에서 첫 사례인 `mixed`만 꺼내 보면 세 줄에 같은 철자가 들어 있어요. 특히 PID 101과 102에서는 단어가 놓인 자리를 눈여겨보세요.

```json
{
  "id": "mixed",
  "collection": "collected",
  "processes": [
    {
      "pid": 101,
      "argv": [
        "/usr/sbin/automountd"
      ]
    },
    {
      "pid": 102,
      "argv": [
        "grep",
        "automountd"
      ]
    },
    {
      "pid": 103,
      "argv": [
        "/opt/bin/automountd-check"
      ]
    }
  ]
}
```

그림에는 첫 두 행만 나란히 담았어요. 각 행의 첫 칸에서 시작하면 어느 PID가 이름 후보로 남는지 따라갈 수 있어요.

[[diagram]]

PID 101에서는 경로 맨 끝의 이름이 `automountd`예요. PID 102의 첫 문자열은 `grep`이고 `automountd`는 그 프로그램에 건넨 검색어예요. PID 103은 첫 문자열에 검색어를 포함하지만 끝 이름 전체가 `automountd-check`여서 다른 이름으로 읽어요.

## 세 줄을 비교한 결과가 한 줄이 되는 과정

명령을 실행하면 맨 아래의 `main()`에서 `Path(sys.argv[1])`이 `u41_cases.json`을 가리켜요. `load_rows()`는 최대 16,001바이트를 읽어서 16,000바이트를 넘는 파일을 거부해요. 사례는 1\~12건, PID는 이 실습에서 1\~999999로 제한해요. 같은 사례 안에서 PID가 겹치는지와 `argv`가 문자열 목록인지도 이때 검사해요. `unique_object()`에서 JSON 키 중복까지 거른 뒤 모든 사례가 형식에 맞아야 첫 결과를 출력해요.

```python
import json
import re
import sys
from pathlib import Path, PurePosixPath

COLLECTIONS = {"collected", "absent", "query-error", "uncollected"}
TARGET_NAMES = {"automountd", "automount", "autofs"}
KEYS = {"id", "collection", "processes"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키가 중복됐어요")
        result[key] = value
    return result


def load_rows(path):
    with path.open("rb") as source:
        raw = source.read(16001)
    if len(raw) > 16000:
        raise ValueError("입력은 16000바이트 이하여야 해요")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 12:
        raise ValueError("사례 목록은 1~12건이어야 해요")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != KEYS:
            raise ValueError("입력 행의 키가 맞지 않아요")
        case_id = row["id"]
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9-]{1,32}", case_id):
            raise ValueError("id 형식이 잘못됐어요")
        if case_id in ids:
            raise ValueError("id가 중복됐어요")
        ids.add(case_id)
        state = row["collection"]
        if not isinstance(state, str) or state not in COLLECTIONS:
            raise ValueError("collection 지원 값이 아니에요")
        items = row["processes"]
        if state != "collected":
            if items is not None:
                raise ValueError("미수집 상태의 processes는 null이어야 해요")
            continue
        if not isinstance(items, list) or len(items) > 16:
            raise ValueError("processes는 16행 이하 목록이어야 해요")
        pids = set()
        for item in items:
            if not isinstance(item, dict) or set(item) != {"pid", "argv"}:
                raise ValueError("프로세스 행의 키가 맞지 않아요")
            pid, argv = item["pid"], item["argv"]
            if type(pid) is not int or not 1 <= pid <= 999999 or pid in pids:
                raise ValueError("PID 범위 또는 중복 오류예요")
            pids.add(pid)
            if not isinstance(argv, list) or not 1 <= len(argv) <= 8:
                raise ValueError("argv는 1~8개 문자열 목록이어야 해요")
            if any(not isinstance(arg, str) or not 1 <= len(arg) <= 160 or any(c in arg for c in "\x00\r\n") for arg in argv):
                raise ValueError("인수는 제어 문자 없는 160자 이하 문자열이어야 해요")
            if "\\" in argv[0] or not PurePosixPath(argv[0]).name:
                raise ValueError("argv[0]에 POSIX 끝 이름이 필요해요")
    return rows


def assess(row):
    if row["collection"] != "collected":
        return "해석 보류", "수집 상태 " + row["collection"]
    items = row["processes"]
    if not items:
        return "해석 보류", "가상 목록이 비었어요"
    matches = []
    for item in items:
        name = PurePosixPath(item["argv"][0]).name
        if name in TARGET_NAMES:
            matches.append(f"{name}@{item['pid']}")
    count = len(items)
    if matches:
        return "이름 후보", ", ".join(matches) + f"; 비교 행={count}"
    return "대상 이름 없음", f"비교 행={count}"


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 JSON 파일 하나를 지정해 주세요")
        rows = load_rows(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("가상 프로세스 이름 대조 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        status, detail = assess(row)
        print(f"{row['id']}: {status} | {detail}")
    print(f"가상 사례: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`assess()`에 `mixed`가 들어오면 `collection`이 `collected`이고 `items`에 세 줄이 있으므로 빈 목록 분기를 지나가요. `matches`는 처음에 비어 있어요. 첫 줄에서 `PurePosixPath(item["argv"][0]).name`은 `/usr/sbin/automountd`의 끝 이름인 `automountd`를 돌려줘요. 이 값이 `TARGET_NAMES`에 있어서 `matches`에 `automountd@101`을 넣어요. 나머지 두 줄에서 비교하는 값은 각각 `grep`과 `automountd-check`라서 후보 목록에 더하지 않아요.

비교한 줄 수 `count = len(items)`는 여전히 3이에요. 함수가 반환한 상태와 세부 내용을 `main()`이 사례 ID 뒤에 붙이면 아래 출력의 첫 줄인 `mixed: 이름 후보 | automountd@101; 비교 행=3`이 돼요.

[[run:1]]

`grep-only`에는 검색 명령밖에 없어 ‘대상 이름 없음’이 나왔어요. `linux-name`과 `autofs-name`은 첫 문자열의 끝 이름이 각각 `automount`, `autofs`여서 이름 후보에 들어갔어요. `--timeout`과 `60`은 가상 입력의 두 번째·세 번째 문자열이라 비교에서 빠져요. `other-path`의 경로는 `/opt/tools/automountd`예요. 디렉터리가 달라도 끝 이름은 같아서 후보로 남아요. 실제로 어느 실행 파일이 구동됐는지 판단하려면 서비스 관리자가 가리키는 실행 경로와 상태 자료를 함께 봐야 해요.

빈 목록을 받은 `empty-list`에서는 비교할 줄이 없어 해석을 보류했어요. 뒤의 세 사례는 보류한 이유가 달라요. `absent`는 가정한 수집 파일 자체가 없던 경우, `query-error`는 조회가 실패한 경우, `uncollected`는 아직 조사하지 않은 경우예요. 이때 `processes`에는 모두 `null`을 넣어 수집한 빈 배열과 구별해요. 프로그램은 이름 후보 네 건과 대상 이름 없음 한 건, 보류 네 건을 출력해요. 종료 코드 0은 가상 입력 대조가 끝났다는 뜻이에요.

## 같은 PID가 두 번 나오면

두 번째 파일에는 PID 801을 같은 목록에 두 번 넣었어요. 첫 줄에서 `pids.add(pid)`로 801을 저장했으므로 다음 줄의 `pid in pids`가 참이 돼요. `load_rows()`의 예외가 `main()`으로 돌아와 `assess()`로 넘어가기 전에 처리를 끝내요.

```bash
python -I -B -X utf8 u41_process_names.py u41_rejected.json
```

이번에는 표준 출력에 대조를 실행하지 않았다는 한 줄이, 표준 오류에 입력을 거부한 이유가 남아요. 위와 같은 셸별 명령으로 읽은 종료 코드는 2예요.

[[run:2]]

정상 입력에서도 종료 코드 2가 나오면 표준 오류 메시지에 맞춰 실행 폴더와 파일명, JSON의 키나 PID 중복을 살펴보세요. 이 예제에서 얻은 후보로 조사할 이름을 좁힐 수 있어요. 가이드가 묻는 서비스 활성화 여부를 판단하려면 해당 시스템의 서비스 상태와 기동 설정을 확인해야 해요. 비활성화의 영향을 살피려면 자동 연결에 의존하는 경로와 그 사용처까지 알아야 해요.

## 참고 자료

- [한국인터넷진흥원, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Python 3 문서, pathlib의 PurePath.name](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.name)
