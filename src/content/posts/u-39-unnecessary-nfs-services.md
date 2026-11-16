---
title: "U-39: 불필요한 NFS 서비스 비활성화"
description: "NFS의 사용 필요성과 현재 활성 상태, 기동 설정을 나눠 살펴봐요. 가상 유닛 자료 열한 건에서 active·disabled의 공존, inactive·enabled의 차이와 수집 보류를 직접 비교해요."
date: "2026-11-16T18:44:46+09:00"
sourcesChecked: "2026-11-16"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "Linux", "NFS", "systemd", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 39
---

NFS는 서버의 파일시스템을 다른 컴퓨터에서 마운트해 공유하는 데 쓰여요. U-39의 중지 대상은 그중 업무에 필요하지 않은 NFS 서비스예요. 파일 공유를 쓰는 곳과 쓰지 않는 곳의 판단을 나누려면 서비스 상태와 함께 사용 근거도 있어야 해요.

## 어떤 NFS를 중지 대상으로 보는가

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-39는 ‘불필요한 NFS 서비스 비활성화’이며 중요도는 ‘상’이에요. 항목표 9쪽과 본문 86\~88쪽의 코드·항목명·중요도가 일치하고 대상은 SOLARIS, LINUX, AIX, HP-UX 등이에요.

판단표는 불필요한 NFS 관련 데몬이 비활성화된 경우를 양호, 활성화된 경우를 취약으로 구분해요. 가이드는 NFS 사용을 원칙적으로 금지하되 불가피하게 필요한 경우 U-40을 참조해 통제하도록 설명해요. 사용이 필요한 서비스의 접근 통제 검토와 불필요한 서비스의 중지 판단을 한 값으로 합치지 않아요.

86쪽 조치 안내에는 마운트된 디렉터리와 공유 디렉터리를 정리한 후 서비스를 중지할 수 있다는 조건도 있어요. NFS를 사용하는 클라이언트와 공유·마운트의 의존 관계를 먼저 조사해야 하는 대목이에요. 아래 실습에는 그 운영 자료가 들어 있지 않아서 서비스 중지, 공유 해제나 마운트 변경은 수행하지 않아요.

## 현재 상태와 기동 설정은 서로 다른 값이에요

Linux 사례의 `stop`과 `disable`은 가이드에서도 별도 단계예요. [systemd 262의 systemctl 설명서](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)는 `disable`이 해당 유닛을 암묵적으로 중지하지 않는다고 설명해요. 현재 상태를 나타내는 `ActiveState`와 기동 설정을 나타내는 `UnitFileState`를 따로 읽으면 이 차이가 드러나요.

그림은 `nfs-server.service`라는 가상 대상 한 개에 `ActiveState=active`, `UnitFileState=disabled`가 함께 들어 있는 입력이에요. `usage=unused`도 업무상 불필요하다고 검토했다는 가정이에요. 실제 명령 출력이나 특정 서버의 NFS 상태를 수집한 화면은 아니에요.

[[diagram]]

현재 활성으로 표시된 유닛을 `disabled` 한 단어만 보고 중지 상태로 분류하면 현재 상태를 놓쳐요. 반대로 `inactive`이더라도 `enabled`가 남아 있으면 기동 설정을 별도로 살펴야 해요. `enabled`를 다음 기동의 성공 보장으로 읽지는 않아요.

같은 설명서에서 `static`은 활성화용 설치 설정이 없는 경우, `masked`는 시작을 막는 방식으로 구분돼요. 이 실습은 두 값을 `disabled`로 바꿔 채우지 않고 설정 방식 조사로 보류해요. `ActiveState`도 유닛의 상위 상태이므로 NFS 프로세스·공유·클라이언트 접근의 세부 결과를 모두 담지는 않아요.

## 두 속성을 담은 JSON으로 대조하기

Python 3.12 이상과 표준 라이브러리를 사용해요. Windows Python 3.12.1의 PowerShell과 Git Bash에서 검증했어요. 실제 systemd나 NFS를 호출하지 않으므로 Linux 파일시스템·관리자 권한·NFS 설치는 필요하지 않아요.

ZIP을 빈 폴더에 풀고 `README.md`, `u39_nfs_states.py`, `u39_cases.json`, `u39_rejected.json`이 모인 글별 폴더로 이동해 주세요. 두 JSON은 이미 들어 있어요. 프로그램은 지정한 JSON만 읽고 임시 파일·소켓을 만들거나 원본 입력을 고치지 않아요. 실제 유닛 파일·공유 디렉터리·마운트를 준비할 필요도 없어요.

[[download]]

두 셸에서 첫 실행 명령은 같아요. 실행 직후 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 종료 코드를 읽어요. PowerShell의 `$?`는 성공 여부예요. README에는 각 실행 바로 다음에 숫자 코드 조회가 있으니 사용하는 셸의 블록 하나를 고르면 돼요.

```bash
python -I -B -X utf8 u39_nfs_states.py u39_cases.json
```

`-I`는 Python 격리 모드, `-B`는 바이트코드 생성 방지, `-X utf8`은 UTF-8 모드예요. 파일 접근을 가상 폴더에 가두는 옵션은 아니므로 인수에는 ZIP의 가상 JSON을 지정해요. 첫 번째 `disabled-active` 사례는 다음 값으로 준비돼 있어요. 이 조각을 다시 저장하지 않고 ZIP의 전체 입력 파일을 사용해요.

```json
{
  "id": "disabled-active",
  "unit": "nfs-server.service",
  "usage": "unused",
  "collection": "collected",
  "ActiveState": "active",
  "UnitFileState": "disabled"
}
```

`ActiveState`와 `UnitFileState`는 문서의 속성명을 사용하지만 이 JSON은 실제 `systemctl show` 출력을 옮긴 것이 아니에요. 유닛 이름도 실습 대상 식별자로 고정했으며 모든 배포판의 NFS 유닛 이름이 같다고 가정하지 않아요.

`usage`는 `unused`(불필요하다는 가정), `required`(필요하다는 가정), `unknown`(사용 근거 미확인)을 받아요. `collection: collected`는 두 속성값을 얻었다는 가정이에요. 유닛 부재를 뒷받침하는 자료가 있으면 `absent`, 조회 오류가 있으면 `query-error`, 자료 자체가 없으면 `uncollected`로 두고 두 속성은 모두 `null`로 남겨요. 사용 필요성 판단과 속성 수집 여부는 별개예요.

전체 코드는 ZIP의 `u39_nfs_states.py`와 같아요. 지원 범위는 `ACTIVE_STATES`의 `active`, `inactive`, `failed`와 `FILE_STATES`의 `enabled`, `disabled`, `static`, `masked`로 제한했어요. 실제 구현의 다른 상태값을 받으면 입력 오류로 거부하므로 전체 systemd 상태 해석기를 대신하지 않아요.

```python
import json
import re
import sys
from pathlib import Path

COLLECTIONS = {"collected", "absent", "query-error", "uncollected"}
USAGES = {"unused", "required", "unknown"}
ACTIVE_STATES = {"active", "inactive", "failed"}
FILE_STATES = {"enabled", "disabled", "static", "masked"}
KEYS = {"id", "unit", "usage", "collection", "ActiveState", "UnitFileState"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키가 중복됐어요")
        result[key] = value
    return result


def load_rows(path):
    with path.open("rb") as source:
        raw = source.read(24001)
    if len(raw) > 24000:
        raise ValueError("입력은 24000바이트 이하여야 해요")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("사례 목록은 1~30건이어야 해요")
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
        if row["unit"] != "nfs-server.service":
            raise ValueError("실습 대상은 가상 nfs-server.service 하나예요")
        for field, allowed in [("usage", USAGES), ("collection", COLLECTIONS)]:
            if not isinstance(row[field], str) or row[field] not in allowed:
                raise ValueError(f"{field} 지원 값이 아니에요")
        if row["collection"] == "collected":
            for field, allowed in [("ActiveState", ACTIVE_STATES), ("UnitFileState", FILE_STATES)]:
                if not isinstance(row[field], str) or row[field] not in allowed:
                    raise ValueError(f"{field} 지원 값이 아니에요")
        elif row["ActiveState"] is not None or row["UnitFileState"] is not None:
            raise ValueError("미수집 상태의 두 속성은 null이어야 해요")
    return rows


def assess(row):
    if row["collection"] != "collected":
        return "보류", f"수집 상태 {row['collection']}"
    if row["usage"] == "unknown":
        return "보류", "사용 필요성 자료 없음"
    if row["usage"] == "required":
        return "보류", "필요 서비스의 접근 통제 검토"
    active, file_state = row["ActiveState"], row["UnitFileState"]
    if active == "active":
        return "검토 후보", f"현재 active; 기동 설정 {file_state}"
    if active != "inactive":
        return "보류", f"현재 상태 {active}의 원인 조사"
    if file_state == "enabled":
        return "검토 후보", "현재 inactive; 기동 설정 enabled"
    if file_state != "disabled":
        return "보류", f"기동 설정 {file_state}의 방식 조사"
    return "두 값 일치", "현재 inactive; 기동 설정 disabled"


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 JSON 파일 하나를 지정해 주세요")
        rows = load_rows(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("가상 상태 대조 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    counts = {"검토 후보": 0, "두 값 일치": 0, "보류": 0}
    for row in rows:
        status, reason = assess(row)
        counts[status] += 1
        print(f"{row['id']}: {status} | {reason}")
    print("사례 합계: " + ", ".join(f"{key} {value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`load_rows()`는 최대 24,001바이트를 읽어 24,000바이트 초과를 거부해요. UTF-8과 JSON, 1\~30건의 목록, 정확한 키·고유 ID·고정 유닛 이름, 사용 판단과 수집 상태를 검사한 뒤 속성값의 허용 집합과 `null` 조건을 대조해요. 뒤쪽 행이 잘못됐을 때 앞부분만 분류해 출력하지 않도록 목록 전체를 먼저 검증해요.

첫 명령에서는 열한 건 중 검토 후보 2건, 두 값 일치 1건, 보류 8건이 나왔어요. 종료 0은 이 가상 자료의 입력 검사와 대조를 끝냈다는 뜻이에요. 서비스 중지 성공, 접속 거부나 U-39의 종합 양호 판정으로 세지 않아요.

[[run:1]]

`disabled-active`는 현재 활성 상태 때문에 후보이고 `enabled-inactive`는 현재 비활성 상태여도 기동 설정이 남아 있어 후보예요. `inactive-disabled`만 이 실습에서 정한 두 상태값 조합과 일치해요. 같은 시점·같은 유닛의 두 속성이라는 가정 안에서만 일치하며 다른 관련 데몬·공유·마운트까지 조사했다는 결과는 없어요.

## 첫 행은 disabled 검사까지 내려가지 않아요

명령의 파일 인수는 `main()`의 `Path(sys.argv[1])`를 통해 `load_rows()`로 들어가요. JSON 객체의 중복 키는 `unique_object()`가 거부하고, 모든 행의 형식 검증이 끝나면 `main()`의 반복문이 첫 행을 `assess(row)`에 전달해요.

첫 조건 `row["collection"] != "collected"`는 거짓이에요. `usage`는 `unused`여서 `unknown`과 `required`의 두 보류 분기도 지나가요. 이어서 `active`에는 `active`, `file_state`에는 `disabled`가 들어가요.

다음 조건 `active == "active"`가 참이므로 함수는 `("검토 후보", "현재 active; 기동 설정 disabled")`를 바로 반환해요. 아래쪽의 `file_state != "disabled"` 검사와 마지막 ‘두 값 일치’ 반환에는 도달하지 않아요. `main()`은 이 반환값을 `status, reason`에 받고 `counts[status]`를 0에서 1로 늘려 실제 출력의 `disabled-active: 검토 후보 | 현재 active; 기동 설정 disabled`를 만들어요.

두 번째 `enabled-inactive`는 `active == "active"`를 지나 `active != "inactive"`도 거짓이라 다음 조건으로 내려가요. 여기서 `file_state == "enabled"`가 참이어서 기동 설정 후보로 반환돼요. 세 번째는 `inactive`와 `disabled`가 각각의 조건을 지나 마지막 반환에 도달해요. 값 하나만 먼저 보고 같은 상태로 합치지 않는 분기 순서예요.

`static-unit`과 `masked-unit`은 현재 비활성이더라도 `file_state != "disabled"`가 참이어서 방식 조사를 남겨요. `failed-unit`은 그보다 앞의 현재 상태 분기에서 원인 조사를 남기므로 실패 상태를 의도한 중지 상태로 바꿔 읽지 않아요.

## 사용 판단이 없는 곳과 수집값이 없는 곳

`needed-service`는 속성값보다 먼저 `usage == "required"`에 걸려 보류돼요. 이 행의 `active`를 불필요한 NFS의 활성으로 단정하지 않고 가이드가 안내한 필요 서비스의 접근 통제 검토로 넘겨요. `need-unreviewed`도 두 속성값이 기대한 조합이어도 사용 근거가 없어 보류돼요.

`missing-unit`, `query-error`, `uncollected`는 `assess()`의 첫 조건에서 반환해요. 부재·오류·미수집이 각각 출력에 남고 두 속성의 `null`은 상태 비교에 쓰이지 않아요. 유닛 하나의 부재를 NFS 전체의 미설치나 미사용으로 확장하지 않아요.

운영 자료에서는 사용 근거와 수집 시점, 대상 유닛 및 관련 데몬의 범위, 현재 상태와 기동 설정을 같은 대상끼리 맞춰 대조해요. 공유를 이용하는 클라이언트와 마운트 의존 관계도 조사해야 중지 영향과 필요 서비스의 통제를 판단할 수 있어요. 이 예제의 두 상태 속성만으로 공유 해제나 마운트 변경을 지시하지 않아요.

## 명령 이름을 상태값에 넣은 파일은 거부해요

`u39_rejected.json`은 `UnitFileState`에 상태값 `disabled` 대신 명령 이름 `disable`을 넣은 가상 오류 입력이에요. 다음 명령 직후에도 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`를 실행해 숫자 종료 코드를 읽어요.

```bash
python -I -B -X utf8 u39_nfs_states.py u39_rejected.json
```

표준 출력에는 가상 상태 대조 미실행, 표준 오류에는 `UnitFileState`의 지원 값 오류가 나와요. 이 거부를 예상한 시험과 입력이 허용된 결과를 구분해 주세요. 정상 파일에서 입력 오류가 나면 실행 위치·파일명·읽기 권한, UTF-8·JSON·크기·키·ID, 속성명과 원본 수집값, 수집 상태와 `null`의 대응을 살펴보세요.

[[run:2]]

`load_rows()`에서 `row["UnitFileState"] not in FILE_STATES`가 참이 되어 `ValueError`가 나고 `main()`이 이를 받아 2를 반환해요. 아직 목록의 형식을 검사하는 단계여서 `assess()`와 상태 합계 출력에는 도달하지 않아요.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [systemd: systemctl의 현재 상태와 유닛 파일 활성화 설정](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
