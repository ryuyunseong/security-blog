---
title: "U-42: 불필요한 RPC 서비스 비활성화"
description: "rpc-statd 설정에 yes와 no가 함께 보이면 어느 값을 읽을까요? 가상 xinetd 발췌에서 주석을 건너뛰고 남은 disable 값과 수집 자료가 없는 경우를 비교해요."
date: "2026-11-20T18:38:44+09:00"
sourcesChecked: "2026-11-20"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "RPC", "xinetd", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 42
---

`disable = no`에서 `no`가 가리키는 건 서비스의 실행 여부일까요, 비활성화 여부일까요? 설정 이름을 먼저 읽으면 뜻이 분명해져요. `disable`은 비활성화를 뜻하므로 `no`는 그 서비스에 비활성화를 지정하지 않았다는 표기예요. 프로세스가 지금 실행 중인지는 이 한 줄에 담겨 있지 않아요.

## RPC를 쓰는 곳과 판단 기준

RPC(Remote Procedure Call)는 다른 프로세스가 제공하는 기능을 호출하는 방식이에요. KISA의 2026년 가이드 96\~98쪽에서 U-42의 중요도는 **상**, 대상은 Solaris, Linux, AIX, HP-UX 등이에요. 업무에 **불필요한** RPC 서비스가 비활성화된 경우를 양호, 활성화된 경우를 취약으로 판단해요. 어느 기능에서 해당 서비스를 쓰는지 먼저 알아야 이 기준을 적용할 수 있어요.

가이드는 Solaris에서는 서비스 관리 상태를, AIX와 HP-UX에서는 `inetd` 설정을 살펴봐요. Linux 예시는 `inetd`, `xinetd`, `systemd`로 나뉘어요. 여기서는 97쪽의 `xinetd` 서비스 블록 `rpc-statd`에 집중할게요. 96쪽 참고 목록의 데몬 표기는 `rpc.statd`이고 97쪽 예시의 블록 이름은 `rpc-statd`예요. 실제 시스템의 어느 서비스가 이 설정을 읽는지는 그 시스템의 자료로 대조해야 해요.

## 주석에 남은 yes와 다음 줄의 no

가상의 `rpc-statd` 블록에서 두 줄을 발췌했어요. 첫 줄 맨 앞에는 `#`가 있어요. 두 줄을 한꺼번에 검색하면 `yes`와 `no`가 모두 보여요. 주석을 건너뛰면 명시값은 하나만 남아요.

[[diagram]]

둘째 줄이 `disable = yes`였다면 같은 자리에 비활성 표기가 남아요. 반대로 주석만 남았을 때는 명시값이 없어요. 이때 실습은 기본값을 추정하지 않고 해석을 보류해요. 전체 설정에서 상속되는 값과 실제 적용 상태를 알려면 발췌 밖의 자료가 필요하거든요.

## 가상 발췌 여덟 건 읽기

ZIP을 빈 폴더에 푼 뒤 `README.md`, `u42_rpc_field.py`, `u42_cases.json`, `u42_rejected.json`이 함께 있는 폴더로 이동하세요. Python 3.12와 표준 라이브러리를 사용해요. 실제 설정 파일이나 관리 권한, 별도 서비스가 필요하지 않아요.

[[download]]

Windows PowerShell 또는 Bash에서 다음 명령을 실행하세요. 숫자 종료 코드는 실행 직후 PowerShell에서 `$LASTEXITCODE`, Bash에서 `echo $?`로 읽을 수 있어요. PowerShell의 `$?`에는 성공 여부가 참·거짓으로 들어가요.

```bash
python -I -B -X utf8 u42_rpc_field.py u42_cases.json
```

`u42_cases.json`의 첫 원소는 아래와 같아요. `lines`에는 가상 서비스 블록 하나에서 가져온 것으로 가정한 속성 행만 넣었어요. 블록 전체나 파일 경로를 넘기는 형식은 지원하지 않아요.

```json
{"id": "comment-first", "source": "excerpt", "lines": ["# disable = yes", "disable = no"]}
```

`main()`은 명령 끝의 파일명을 `Path(sys.argv[1])`로 받아 `load_cases()`에 넘겨요. 이 함수는 최대 12,001바이트를 읽고 12,000바이트를 넘으면 거부해요. 사례 수는 1\~12건, 한 발췌의 행 수는 0\~8개로 제한했어요. `unique_keys()`는 각 JSON 객체 안에서 같은 키가 다시 나오는지 살피고 `seen`은 사례 ID가 서로 겹치는지 검사해요. 모든 사례가 형식에 맞아야 첫 줄의 대조를 시작해요.

```python
import json
import re
import sys
from pathlib import Path

SOURCES = {"excerpt", "missing-file", "read-error", "not-collected"}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키가 중복됐어요")
        result[key] = value
    return result


def load_cases(path):
    with path.open("rb") as stream:
        raw = stream.read(12001)
    if len(raw) > 12000:
        raise ValueError("입력은 12000바이트까지 읽어요")
    cases = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys)
    if not isinstance(cases, list) or not 1 <= len(cases) <= 12:
        raise ValueError("사례 목록은 1~12건이어야 해요")
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "source", "lines"}:
            raise ValueError("각 사례에는 id, source, lines가 필요해요")
        name, source, lines = case["id"], case["source"], case["lines"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]{1,32}", name) or name in seen:
            raise ValueError("사례 ID의 형식이나 중복을 살펴보세요")
        seen.add(name)
        if not isinstance(source, str) or source not in SOURCES:
            raise ValueError("지원하지 않는 수집 상태예요")
        if source != "excerpt":
            if lines is not None:
                raise ValueError("발췌 자료가 없으면 lines는 null이어야 해요")
            continue
        if not isinstance(lines, list) or len(lines) > 8:
            raise ValueError("발췌는 여덟 줄 이하의 목록이어야 해요")
        for line in lines:
            if not isinstance(line, str) or len(line) > 120 or not line.isascii():
                raise ValueError("각 줄에는 120자 이하의 ASCII 문자열을 써 주세요")
            if any(char != "\t" and not char.isprintable() for char in line):
                raise ValueError("각 줄에 탭 이외의 제어 문자가 있어요")
    return cases


def read_setting(case):
    if case["source"] != "excerpt":
        return "자료 보류", case["source"]
    values = []
    for line in case["lines"]:
        field = line.strip()
        if not field or field.startswith("#"):
            continue
        match = re.fullmatch(r"disable\s*=\s*(yes|no)", field)
        if not match:
            return "해석 보류", "지원 범위 밖의 행"
        values.append(match[1])
    if len(values) != 1:
        return "해석 보류", f"명시값 {len(values)}개"
    return ("비활성 표기" if values[0] == "yes" else "활성 표기"), values[0]


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 입력 파일 하나를 지정해 주세요")
        cases = load_cases(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("발췌 대조 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for case in cases:
        status, detail = read_setting(case)
        print(f"{case['id']}: {status} | {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

첫 사례를 따라가 볼게요. `source`가 `excerpt`라서 `read_setting()`은 빈 목록 `values`를 만들어요. 첫 줄에서 앞뒤 공백을 제거한 `field`는 `# disable = yes`예요. `field.startswith("#")`가 참이어서 `continue`로 둘째 줄로 넘어가요. 목록은 아직 비어 있어요.

둘째 줄 `disable = no`는 `re.fullmatch()`의 패턴과 줄 전체가 일치해요. 괄호로 묶은 부분 `match[1]`이 `no`이므로 `values`는 `["no"]`가 돼요. 길이가 1이고 첫 값이 `yes`가 아니어서 반환값은 `("활성 표기", "no")`예요. `main()`이 사례 ID를 붙인 `comment-first: 활성 표기 | no`를 실제 출력 첫 줄에서 볼 수 있어요.

[[run:1]]

`disabled`에서는 유일한 값 `yes`를 비활성 표기로 읽었어요. `only-comment`는 주석을 건너뛴 뒤 명시값이 0개이고 `two-values`에서는 2개가 남아요. 실습은 두 값 중 마지막 값을 임의로 고르지 않아요. `unsupported`의 `maybe`는 패턴과 맞지 않아 그 행에서 해석을 멈춰요. 이 파서는 소문자 `yes`·`no`를 지정한 한 줄, 빈 줄, 줄 전체 주석만 다뤄요.

출력 끝의 세 건은 행을 읽기 전부터 사정이 달라요. `missing-file`은 가정한 수집 파일이 없던 경우, `read-error`는 자료를 읽는 중에 오류가 난 경우, `not-collected`는 수집을 시도하지 않은 경우예요. 세 경우 모두 `lines`에 `null`을 넣고 사유를 그대로 돌려줘요. 종료 코드 0은 여덟 사례의 처리가 끝났다는 뜻이에요. 가상 파일의 부재만으로 해당 서비스까지 꺼져 있다고 볼 근거는 없어요.

## 빈 목록과 자료 없음이 갈리는 지점

발췌했는데 행이 하나도 없으면 `lines`에 빈 배열 `[]`을 넣을 수 있어요. 반면 다음 명령의 파일은 `source`를 `missing-file`로 적고도 `lines`에 `[]`을 넣었어요. 두 필드의 의미가 서로 어긋나는 경우예요.

```bash
python -I -B -X utf8 u42_rpc_field.py u42_rejected.json
```

`load_cases()`에서 `source != "excerpt"`가 참이면 `lines is not None`을 살펴요. 빈 배열도 `None`과는 다른 값이라 예외가 발생해요. `main()`은 표준 출력에 미실행을 알리고 표준 오류에 이유를 적은 뒤 종료 코드 2를 반환해요.

[[run:2]]

첫 번째 명령에서 종료 코드 2가 나오면 표준 오류에 따라 실행 폴더와 파일명, JSON 키, `source`와 `lines`의 조합을 살펴보세요. 반대로 비교가 끝났는데 ‘해석 보류’가 나왔다면 원래 발췌에 명시값이 몇 개였는지부터 돌아보면 돼요. U-42 판정에는 그 서비스의 업무상 필요 여부와 실제 적용 상태까지 함께 남겨야 해요.

## 참고 자료

- [한국인터넷진흥원, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
