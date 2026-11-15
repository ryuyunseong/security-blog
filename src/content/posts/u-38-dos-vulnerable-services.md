---
title: "U-38: DoS 공격에 취약한 서비스 비활성화"
description: "같은 echo라도 TCP 주석 행과 UDP 활성 설정 행을 따로 읽어요. 가상 inetd 문자열 여덟 건에서 프로토콜별 행, 중복과 자료 부재를 나누고 공식 가이드의 주석 안내 차이도 짚어요."
date: "2026-11-15T18:35:38+09:00"
sourcesChecked: "2026-11-15"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "Linux", "inetd", "TCP", "UDP", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 38
---

TCP 7번과 UDP 7번은 같은 숫자를 쓰지만 서로 다른 전송 방식의 echo 서비스예요. [RFC 862: Echo Protocol](https://www.rfc-editor.org/rfc/rfc862.html)은 두 방식을 각각 설명해요. TCP 설정 한 줄에 주석을 달았다는 자료만으로 UDP 쪽 설정까지 설명할 수는 없어요.

U-38에서 서비스 이름을 찾을 때도 이 차이가 남아요. 이번에는 한 가상 설정 안의 TCP 행은 주석이고 UDP 행은 활성 형식인 경우를 읽어 볼게요. 패킷을 보내거나 echo 서버를 띄우는 대신 문자열의 필드와 줄 번호를 비교해요.

## U-38의 서비스 범위와 주석 안내의 차이

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-38은 ‘DoS 공격에 취약한 서비스 비활성화’이며 중요도는 ‘상’이에요. 항목표 9쪽과 본문 83\~85쪽의 코드·항목명·중요도가 일치하고 대상은 SOLARIS, LINUX, AIX, HP-UX 등이에요.

판단표는 해당 서비스가 비활성화된 경우를 양호, 활성화된 경우를 취약으로 구분해요. 개요는 사용하지 않는 서비스의 실행 여부를 점검한다고 설명하며 본문 표에는 echo, discard, daytime, chargen뿐 아니라 NTP, DNS, SNMP, SMTP도 나와요. 이 실습은 그중 inetd 예시의 네 이름만 다뤄요. 업무에 쓰는 서비스는 사용 근거와 영향, 실제 구현의 보안 설정을 함께 조사해야 하며 이 문자열 결과로 일괄 중지 대상을 정하지 않아요.

83쪽 Linux inetd의 수정 안내에는 ‘주석 제거’가 적혀 있고 다음 쪽의 예시도 주석 없는 echo 행이에요. 반면 같은 항목의 AIX·HP-UX 사례는 84\~85쪽에서 TCP와 UDP 행을 각각 주석 처리해요. 비활성화라는 항목 목적과 Linux의 그 문구가 맞지 않는 점을 원문 차이로 남겨요. 아래 코드는 주석 없는 형식을 활성 설정 후보로 분류하며 가이드의 재시작·중지 명령을 실행하지 않아요.

## 가상 설정의 두 행을 나란히 읽기

Python 3.12 이상과 표준 라이브러리를 사용해요. Windows Python 3.12.1의 PowerShell과 Git Bash에서 같은 명령을 실행했어요. inetd 설치, 관리자 권한이나 Linux 파일시스템은 필요하지 않아요.

ZIP을 빈 폴더에 풀고 `README.md`, `u38_inetd_pairs.py`, `u38_cases.json`, `u38_rejected.json`이 있는 글별 폴더로 이동해 주세요. 두 JSON은 이미 들어 있어요. 설정은 JSON의 `text`에 담긴 문자열이므로 `/etc/inetd.conf`나 `/example/echohelper`를 만들지 않아요. 프로그램은 인수로 지정한 JSON만 읽고 임시 파일·소켓·운영 설정을 만들거나 바꾸지 않아요.

[[download]]

`u38_cases.json`의 `split-echo`는 `collection: collected`이고 `text`는 다음 두 줄이에요. 이 조각을 별도 파일로 저장하지 않고 ZIP의 JSON 전체를 입력으로 사용해요.

```text
# echo stream tcp nowait root internal
echo dgram udp wait root internal
```

각 행에서 서비스 이름 뒤의 소켓 형식과 프로토콜을 같이 읽어요. 첫 줄의 `#`는 `echo/tcp` 행에만 붙어 있고 두 번째 `echo/udp` 행에는 없어요. 그림은 이 가상 문자열의 필드를 나눈 모습이에요.

[[diagram]]

그림의 ‘활성 설정 후보’는 문자열을 읽은 결과예요. 해당 서비스의 실행·대기 상태나 실제 도달 가능 여부를 수집한 결과는 따로 필요해요.

코드는 가이드 예시를 좁혀 `echo`, `discard`, `daytime`, `chargen`의 여섯 필드 형식만 해석해요. `tcp`에는 `stream`, `udp`에는 `dgram`이 대응하고 대기 방식은 `wait` 또는 `nowait`, 마지막 두 필드는 `root internal`이어야 해요. 다른 사용자·외부 서버 프로그램·확장 형식이 있는 대상 행은 지원 범위 밖으로 보류해요. inetd 전체 문법이나 배포판별 설정 우선순위를 구현한 파서는 아니에요.

## 여덟 사례를 실행하고 후보와 보류를 나누기

첫 명령은 두 셸에서 같아요. 실행 직후 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 종료 코드를 읽어요. PowerShell의 `$?`는 성공 여부예요. README에서 사용하는 셸의 블록 하나를 선택하면 각 명령 바로 다음에 숫자 코드 조회가 있어요.

```bash
python -I -B -X utf8 u38_inetd_pairs.py u38_cases.json
```

`-I`는 Python 격리 모드, `-B`는 바이트코드 생성 방지, `-X utf8`은 UTF-8 모드예요. 파일시스템 접근을 막는 옵션은 아니므로 인수에는 ZIP의 가상 입력을 지정해요. 다음 전체 코드는 ZIP의 Python 파일과 같아요.

```python
import json
import re
import sys
from pathlib import Path

TARGETS = {"echo", "discard", "daytime", "chargen"}
SOCKETS = {"tcp": "stream", "udp": "dgram"}
STATES = {"collected", "absent", "query-error", "uncollected"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키가 중복됐어요")
        result[key] = value
    return result


def load_cases(path):
    with path.open("rb") as source:
        raw = source.read(20001)
    if len(raw) > 20000:
        raise ValueError("입력은 20000바이트 이하여야 해요")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("사례 목록은 1~30건이어야 해요")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "collection", "text"}:
            raise ValueError("각 행에는 id, collection, text만 필요해요")
        case_id, state, text = row["id"], row["collection"], row["text"]
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9-]{1,32}", case_id):
            raise ValueError("id 형식이 잘못됐어요")
        if case_id in ids:
            raise ValueError("id가 중복됐어요")
        ids.add(case_id)
        if not isinstance(state, str) or state not in STATES:
            raise ValueError("지원하지 않는 수집 상태예요")
        if state == "collected":
            if not isinstance(text, str) or len(text) > 2000 or "\0" in text:
                raise ValueError("collected의 text는 NUL 없는 2000자 이하 문자열이어야 해요")
        elif text is not None:
            raise ValueError("수집하지 않은 text는 null이어야 해요")
    return rows


def inspect_text(text):
    active, comments, issues, seen = [], [], [], set()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        commented = line.startswith("#")
        fields = (line[1:].strip() if commented else line).split()
        if not fields or fields[0] not in TARGETS:
            continue
        if (len(fields) != 6 or fields[2] not in SOCKETS
                or fields[1] != SOCKETS.get(fields[2])
                or fields[3] not in {"wait", "nowait"}
                or fields[4:] != ["root", "internal"]):
            issues.append(f"행 {number}: 지원 범위 밖 대상 행")
            continue
        pair = f"{fields[0]}/{fields[2]}"
        if commented:
            comments.append(f"{pair}@{number}")
        else:
            if pair in seen:
                issues.append(f"행 {number}: 활성 {pair} 중복")
            seen.add(pair)
            active.append(f"{pair}@{number}")
    if issues:
        return "해석 보류", "; ".join(issues)
    detail = f"활성 {', '.join(active) or '없음'}; 주석 {', '.join(comments) or '없음'}"
    return ("활성 설정 후보" if active else "활성 행 없음"), detail


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 JSON 파일 하나를 지정해 주세요")
        rows = load_cases(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("가상 설정 비교 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    counts = {"활성 설정 후보": 0, "활성 행 없음": 0, "해석 보류": 0}
    for row in rows:
        if row["collection"] == "collected":
            status, detail = inspect_text(row["text"])
        else:
            status, detail = "해석 보류", f"수집 상태 {row['collection']}"
        counts[status] += 1
        print(f"{row['id']}: {status} | {detail}")
    print("사례 합계: " + ", ".join(f"{name} {count}" for name, count in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`load_cases()`는 최대 20,001바이트를 읽어 20,000바이트 초과를 거부하고 UTF-8과 JSON을 해석해요. 목록은 1\~30건이며 키·ID 중복, 수집 상태, `text`의 길이와 NUL을 검사해요. 수집된 본문은 `collected`와 2,000자 이하 문자열로 표현해요. 파일 부재를 뒷받침하는 자료가 있으면 `absent`, 조회 오류면 `query-error`, 자료 자체가 없으면 `uncollected`로 두고 `text`는 `null`로 남겨요. 실습의 수집 상태는 미리 넣은 가정이에요.

다음 실제 실행에서는 활성 설정 후보 1건, 활성 행 없음 2건, 해석 보류 5건이 나왔어요. 종료 0은 여덟 건의 입력 검사와 분류가 끝났다는 뜻이며 U-38의 종합 양호 판정이나 실제 접속 허용을 뜻하지 않아요.

[[run:1]]

`both-commented`는 TCP·UDP 두 행이 모두 주석이라 활성 목록이 비어 있어요. `other-name`의 첫 필드는 `echohelper`이므로 `TARGETS`의 `echo`와 일치하지 않아 대상 행에서 빠져요. 둘 다 ‘활성 행 없음’이지만 앞의 결과에는 주석 행 두 개가 남고 뒤의 결과에는 주석 행도 없어요. 이 표시는 제공된 문자열 범위에 한정돼요.

`duplicate-udp`는 같은 서비스·프로토콜의 활성 행이 두 개여서 해석을 보류해요. `mismatched-socket`은 `udp`인데 소켓 형식이 `stream`이어서 지원 형식 검사에서 걸려요. 어느 행이 실제로 적용될지 추측해 하나를 골라내지 않아요.

나머지 세 건은 본문을 얻었다는 가정이 없어요. `no-file`, `read-error`, `no-evidence`는 각각 부재·조회 오류·미수집을 나타내며 `inspect_text()`를 호출하기 전에 해석 보류로 나뉘어요. 파일이 없다는 자료와 조회하지 못했다는 자료를 같은 ‘서비스 없음’으로 바꾸지 않아요.

## split-echo가 echo/udp@2로 출력되는 과정

명령의 `u38_cases.json`은 `main()`에서 `Path(sys.argv[1])`로 전달돼요. `load_cases()`가 모든 행의 형식을 먼저 검사한 뒤 반환하므로 뒤쪽에 잘못된 입력이 있으면 앞부분의 분류도 출력하지 않아요. 첫 사례의 `collection`은 `collected`여서 `inspect_text(row["text"])`로 들어가요.

시작할 때 `active`, `comments`, `issues`는 빈 목록이고 `seen`은 빈 집합이에요. `enumerate(text.splitlines(), 1)`이 첫 줄에 번호 1을 붙여요. `line.startswith("#")`가 참이므로 `commented`는 `True`, `fields`는 `#`를 벗긴 여섯 토큰이 돼요. `fields[0]`의 `echo`는 대상 집합에 있고 `fields[2]`의 `tcp`에 대응하는 `SOCKETS["tcp"]`는 `stream`이므로 소켓 형식도 맞아요.

대기 방식과 `fields[4:]`의 `root`, `internal`까지 맞으면 `pair`는 `echo/tcp`예요. 주석 분기로 들어가 `comments`에 `echo/tcp@1`을 넣고 `active`와 `seen`은 비워 둬요. `@1`은 이 문자열의 첫 번째 줄이라는 표시예요.

두 번째 줄에는 `#`가 없어서 `commented`가 `False`예요. `fields[2]`는 `udp`, 대응 소켓은 `dgram`이고 `pair`는 `echo/udp`가 돼요. `seen`에 아직 같은 쌍이 없으므로 중복 사유 없이 집합과 `active`에 추가해요. 반복문이 끝나면 `active = ["echo/udp@2"]`, `comments = ["echo/tcp@1"]`, `issues = []`예요.

`if issues`를 지나 `detail`을 만들고 비어 있지 않은 `active` 때문에 상태를 ‘활성 설정 후보’로 반환해요. `main()`은 `counts[status]`를 1 늘린 뒤 실제 기록의 `split-echo: 활성 설정 후보 | 활성 echo/udp@2; 주석 echo/tcp@1`을 출력해요. TCP의 주석 상태가 UDP 쪽 집합에 섞이지 않는 과정이에요.

중복이나 지원 범위 밖 행이 있으면 `issues` 분기가 이 반환보다 먼저 실행돼요. 이미 앞에서 활성 행을 읽었더라도 결과를 해석 보류로 남기는 순서예요. 주석 행은 `seen`에 넣지 않으므로 같은 쌍의 과거 주석과 현재 활성 행이 하나씩 있는 형식은 활성 행 중복으로 세지 않아요.

## 수집 상태와 본문이 충돌하는 입력

`u38_rejected.json`은 `uncollected` 상태인데 `text`에 주석 행을 넣어 둔 가상 오류 입력이에요. 다음 명령 뒤에도 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`를 실행해 숫자 종료 코드를 읽어요.

```bash
python -I -B -X utf8 u38_inetd_pairs.py u38_rejected.json
```

`load_cases()`의 `elif text is not None`이 참이 되어 `ValueError`가 나고 `main()`이 이를 받아 2를 반환해요. 표준 출력은 비교 미실행, 표준 오류는 수집 상태와 `text`의 충돌을 알리는 다음 기록과 같아요.

[[run:2]]

종료 2는 입력을 분류 전에 거부한 결과예요. 기대한 거부를 재현한 시험 성공을 입력 허용으로 읽지 않아요. 정상 입력에서도 오류가 나면 실행 폴더·파일명·읽기 권한, UTF-8과 JSON 구문·크기, 키와 ID 중복, 수집 상태와 `text`의 대응을 순서대로 살펴보세요.

실제 점검 자료에는 TCP·UDP별 설정 행뿐 아니라 사용 중인 관리 방식과 포함 파일, 설정 반영 시점, 서비스의 실행·대기 상태와 사용 근거를 함께 남겨요. 이 입력 밖의 xinetd·systemd·Solaris SMF, 그리고 NTP·DNS·SNMP·SMTP의 자료까지 조사 범위에 맞춰 대조해야 U-38의 비활성화 상태를 판단할 수 있어요.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [RFC 862: Echo Protocol의 TCP·UDP 서비스](https://www.rfc-editor.org/rfc/rfc862.html)
