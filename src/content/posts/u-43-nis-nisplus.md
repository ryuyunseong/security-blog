---
title: "U-43: NIS, NIS+ 점검"
description: "NIS+가 켜진 두 가상 기록에서 기존 NIS의 상태만 바꿔 봐요. 두 서비스를 함께 쓰는 경우와 NIS 자료가 빠진 경우를 구별해 U-43의 판단 기준을 읽어요."
date: "2026-11-21T18:38:26+09:00"
sourcesChecked: "2026-11-21"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "NIS", "서비스 관리", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 43
---

점검표의 NIS+ 칸에 ‘활성’이라고 적혀 있어도 기존 NIS가 함께 켜져 있을 수 있어요. 두 이름이 비슷해서 한 칸으로 합치기 쉽지만 서비스를 하나씩 나눠 적으면 어느 쪽이 여전히 동작하는지 드러나요.

## 같은 NIS+ 기록에서 갈라지는 두 경우

NIS는 여러 Unix 시스템이 계정 등 공통 정보를 공유하는 서비스예요. KISA의 2026년 가이드 99\~101쪽은 U-43의 중요도를 **상**으로 분류하고 Solaris, Linux, AIX, HP-UX 등을 대상으로 들어요. 기준은 NIS가 비활성화돼 있거나 불가피하게 사용해야 할 때 NIS+를 쓰면 양호, NIS가 활성화돼 있으면 취약이에요. 가이드는 NIS 활성화로 다른 시스템의 관리자 권한까지 위협받을 수 있다고 설명해요.

아래 가상 사례의 `both`와 `plus`는 NIS+ 상태가 같아요. 첫 번째 사례에는 기존 NIS도 활성으로 기록돼 있어요. 두 번째에서는 기존 NIS의 비활성 상태가 별도로 기록돼 있어요.

[[diagram]]

운영 자료를 읽을 때도 어느 서비스의 상태인지, 그 값을 언제 어떻게 얻었는지가 필요해요. 가이드는 Linux 예시에서 `ypserv`와 `ypbind` 등 NIS 관련 서비스를 살펴봐요. 101쪽 설명에서 `ypserv`는 서버 쪽 요청에 응답하고 `ypbind`는 클라이언트와 서버를 연결해요. 한 데몬에 관한 발췌를 시스템 전체의 상태로 옮겨 적으면 다른 역할의 자료가 빠질 수 있어요.

## 가상 기록의 네 가지 값

실습에서는 한 사례에 `nis`와 `nisplus`를 각각 적어요. `on`과 `off`는 활성·비활성이라는 자료를 확보했다고 가정한 값이에요. 조회 도중 오류가 났다면 `error`, 수집한 자료 자체가 없다면 `missing`을 넣어요. 실제 호스트에서 자료를 모으는 단계는 실습 범위 밖이에요.

빈 폴더에 ZIP을 풀면 `u43_nis_status.py`, `u43_cases.json`, `u43_rejected.json`과 `README.md`가 나와요. 이 파일들이 있는 폴더에서 Python 3.12와 표준 라이브러리로 실행해요. 별도 서비스나 관리자 권한은 필요 없어요.

[[download]]

아래 두 블록 중 사용하는 셸에 맞는 하나를 고르세요. PowerShell에서는 외부 프로그램의 숫자 종료 코드를 `$LASTEXITCODE`로 읽어요. `$?`는 성공 여부를 담아요.

```powershell
python -I -B -X utf8 u43_nis_status.py u43_cases.json
$LASTEXITCODE
```

Bash에서는 같은 명령 바로 다음에 `echo $?`를 실행해요. 정상 입력의 숫자 종료 코드는 0이에요.

```bash
python -I -B -X utf8 u43_nis_status.py u43_cases.json
echo $?
```

## plus 한 행이 출력되기까지

`main(sys.argv[1:])`이 받는 인수는 이번에 지정한 `u43_cases.json` 하나예요. `read_rows`는 파일을 최대 8,193바이트까지 읽고 8,192바이트를 넘으면 거절해요. UTF-8 JSON을 읽은 뒤에는 목록이 비어 있는지, 각 행에 정해진 키 세 개가 있는지 살펴요.

```python
import json
import re
import sys
from pathlib import Path

STATES = {"on", "off", "error", "missing"}


def compare(nis, nisplus):
    if nis == "on":
        return "nis-active"
    if nis == "off":
        if nisplus == "on":
            return "plus-only"
        return "nis-inactive"
    return "need-nis-status"


def read_rows(path):
    with path.open("rb") as source:
        data = source.read(8193)
    if len(data) > 8192:
        raise ValueError("file exceeds 8192 bytes")
    records = json.loads(data.decode("utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("expected a nonempty list")

    seen = set()
    output = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {"case", "nis", "nisplus"}:
            raise ValueError("expected case, nis and nisplus")
        name, nis, nisplus = (record[k] for k in ("case", "nis", "nisplus"))
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z-]{0,29}", name):
            raise ValueError("invalid case name")
        if name in seen:
            raise ValueError("duplicate case name")
        if not all(isinstance(v, str) and v in STATES for v in (nis, nisplus)):
            raise ValueError(f"{name}: unexpected state")
        seen.add(name)
        output.append(f"{name} nis={nis} nisplus={nisplus} result={compare(nis, nisplus)}")
    return output


def main(args):
    if len(args) != 1:
        print("rows-emitted=0")
        print("입력 오류: JSON 파일 하나를 지정하세요.", file=sys.stderr)
        return 2
    try:
        rows = read_rows(Path(args[0]))
    except (OSError, ValueError, RecursionError) as error:
        print("rows-emitted=0")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

두 번째 행의 값은 `name="plus"`, `nis="off"`, `nisplus="on"`이에요. 첫 번째 행을 처리했으므로 `seen`에는 `"both"`가 들어 있어요. `"plus"`는 이름 형식에 맞고 아직 등장하지 않았으며 두 상태도 `STATES`에 있으므로 `seen.add(name)`까지 진행해요.

이제 `compare("off", "on")`에서 첫 조건 `nis == "on"`은 거짓이고 그다음 `nis == "off"`는 참이에요. 안쪽의 `nisplus == "on"`까지 참이어서 `"plus-only"`를 돌려줘요. 이 값이 `output`의 두 번째 문자열에 들어가고 전체 입력이 검증된 뒤 `main`이 그 줄을 출력해요. 아래 두 번째 행이 바로 `plus nis=off nisplus=on result=plus-only`예요.

[[run:1]]

첫 행 `both`는 두 서비스가 모두 `on`이라 맨 앞 조건에서 `nis-active`로 끝나요. 기존 NIS가 켜져 있다는 관찰이 그대로 남아요. `idle`과 `partial`은 기존 NIS가 `off`여서 둘 다 `nis-inactive`인데, NIS+ 칸을 보면 `idle`은 비활성이고 `partial`은 조회 오류예요.

`unread`와 `no-record`에서는 기존 NIS가 활성인지 비활성인지 알 수 없어 `need-nis-status`가 나와요. 전자는 NIS 조회가 실패한 원인을 살필 차례이고 후자는 누락된 수집 자료를 확보해야 해요. 종료 코드 0은 여섯 행의 입력값을 대조해 출력했다는 뜻이에요. NIS+ 사용이 업무상 불가피한 사정은 이 파일에 담겨 있지 않아요.

## 끝 행에 오타가 있을 때

다른 입력 파일은 첫 행이 정상이지만 다음 행의 `nis`가 `off`에서 한 글자 빠진 `of`예요. 같은 폴더에서 두 셸 모두 아래 명령을 실행할 수 있어요. 숫자 종료 코드는 명령 직후 PowerShell에서 `$LASTEXITCODE`, Bash에서 `echo $?`로 읽어요.

```text
python -I -B -X utf8 u43_nis_status.py u43_rejected.json
```

`of`가 `STATES`에 없어 `read_rows`가 예외를 내면 앞서 모은 첫 행도 반환하지 않아요. 표준 출력의 `rows-emitted=0`은 내보낸 **사례 행**이 없다는 뜻이고 표준 오류에는 `typo: unexpected state`라는 원인이 남아요.

[[run:2]]

이때 종료 코드 2가 가리키는 건 입력 오류예요. `typo` 행에는 허용된 상태를 적어야 하고 실제 조회에 실패한 기록이라면 그 사실을 `error`로 남겨야 해요. `off`는 비활성이라는 관찰이 있을 때 쓰는 값이에요.

## 참고 자료

- [한국인터넷진흥원, 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
