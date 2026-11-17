---
title: "U-40: NFS 접근 통제"
description: "설정 파일의 0644와 NFS 공유의 ro는 서로 다른 권한이에요. 가상 exports 자료에서 호스트·옵션의 공백, 전체 대상 표기와 권한 비트를 나눠 살펴봐요."
date: "2026-11-17T18:40:32+09:00"
sourcesChecked: "2026-11-17"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["Unix", "Linux", "NFS", "exports", "KISA"]
draft: false
series: "unix-2026"
seriesOrder: 40
---

`/etc/exports`의 모드가 `0644`여도 공유 행에 `/home/example *(ro,root_squash)`가 있으면 대상 표기는 전체 클라이언트예요. 설정 파일을 누가 고칠 수 있는지와 공유에 누가 접근하도록 적었는지는 별개여서 파일 모드와 공유 행을 함께 살펴야 해요.

## 같은 ro를 붙여도 대상은 달라요

Linux의 [nfs-utils exports(5)](https://www.man7.org/linux/man-pages/man5/exports.5@@nfs-utils.html)는 클라이언트 뒤 괄호 안에 그 대상의 옵션을 적도록 설명해요. `ro`는 파일시스템을 바꾸는 요청을 제한하는 옵션이고 단독 `*`는 모든 클라이언트에 대응하는 대상 표기예요. 읽기만 허용하는 것과 특정 호스트로 범위를 좁히는 것을 구분할 수 있어요.

그림은 뒤에서 비교할 가상 입력 `bound-ro`와 `all-clients`예요. 두 사례의 공유 경로와 옵션은 같고 대상만 `host1`과 `*`로 달라요. 두 행을 한 서버에 함께 적용한 설정이나 실제 접속을 수집한 화면은 아니에요.

[[diagram]]

`root_squash`도 허용 호스트 목록을 대신하지 않아요. 같은 설명서는 클라이언트의 UID/GID 0 요청을 익명 UID/GID로 매핑하는 옵션으로 설명해요. 파일 소유자인 UID 0, 클라이언트의 UID/GID 매핑, 공유 대상 표기를 각각 읽어야 해요.

## U-40 판단표와 Linux 예시의 공백

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-40은 ‘NFS 접근 통제’, 중요도는 ‘상’이에요. 항목표 9쪽과 본문 89\~92쪽이 일치하며 대상은 SOLARIS, LINUX, AIX, HP-UX 등이에요.

89쪽 판단표는 양호를 접근 통제가 설정되고 NFS 설정 파일 권한이 644 이하인 경우로 적어요. 취약 문구는 접근 통제가 설정되지 않고 권한이 644를 초과하는 경우예요. 두 조건이 엇갈리는 사례를 이 문구의 반대만으로 양호라고 추론하지 않고 접근 통제와 파일 권한의 문제를 따로 남겨요. Linux 조치 사례에는 `/etc/exports`의 root 소유와 644 설정도 있어요.

90쪽 Linux와 92쪽 `/etc/exports` 예시에는 `host1 (ro, root_squash)`처럼 호스트와 여는 괄호 사이 공백이 있어요. [Red Hat Enterprise Linux 7의 NFS 서버 설정 문서](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/storage_administration_guide/nfs-serverconfig)와 `exports(5)`는 이 사이에 공백을 두지 않도록 설명해요. Linux 문법을 설명할 때는 `host1(ro,root_squash)`로 붙여 적되, 가이드 원문의 표기와 차이가 있다는 점을 남겨요. SOLARIS·AIX·HP-UX의 다른 명령 형식까지 Linux 문법으로 바꿔 읽지는 않아요.

가이드는 불가피한 NFS 사용 시 필요한 디렉터리와 허가된 대상만 지정하고 v4 사용을 권고해요. Linux 설명서의 `sec=sys`는 암호학적 보안이 없는 방식이며 `sec=krb5p`는 기밀성 보호를 제공해요. 버전 번호만 보고 통신이 암호화됐다고 판단하지 않고 실제 보안 방식과 전송 보호 설정을 대조해야 해요. 아래 코드는 그 협상이나 통신을 시험하지 않아요.

## 가상 설정 열 건을 읽을 준비

Python 3.12 이상과 표준 라이브러리를 사용해요. Windows Python 3.12.1의 PowerShell·Git Bash에서 실행했으며 Linux 파일시스템이나 관리자 권한, NFS 설치는 필요하지 않아요. JSON의 모드·소유자·행을 계산하는 실습이라 Windows 파일의 권한을 Linux 권한처럼 측정하지 않아요.

ZIP을 빈 폴더에 풀고 `README.md`, `u40_exports_review.py`, `u40_cases.json`, `u40_rejected.json`이 모인 글별 폴더로 이동해 주세요. 입력 두 개는 이미 들어 있어요. `/home/example`과 `/etc/exports`는 설명용 경로이며 실제 파일·폴더를 만들 필요가 없어요. 프로그램은 인수로 받은 JSON만 읽고 임시 파일·소켓 생성이나 원본 입력 변경은 하지 않아요.

[[download]]

첫 실행은 두 셸에서 다음 명령을 사용해요. 바로 뒤에 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 종료 코드를 읽어 주세요. PowerShell의 `$?`는 성공 여부예요. README의 단계별 셸 블록 중 사용하는 셸 하나를 선택하면 돼요.

```bash
python -I -B -X utf8 u40_exports_review.py u40_cases.json
```

`-I`는 Python 격리 모드, `-B`는 바이트코드 생성 방지, `-X utf8`은 UTF-8 모드예요. 파일 접근을 제한하는 옵션은 아니므로 인수에는 ZIP에 든 가상 JSON을 지정해요. 목록의 여섯 번째 `numeric-trap`은 아래 값이에요. 이 조각을 따로 저장하지 않고 전체 입력 파일로 실행해요.

```json
{
  "id": "numeric-trap",
  "collection": "collected",
  "ownerUid": 0,
  "mode": "0460",
  "line": "/home/example host1(ro,root_squash)"
}
```

`ownerUid`와 `mode`는 NFS 설정 파일의 소유자와 일반 권한을 얻었다는 가정이고 `line`은 그 파일에서 가져왔다고 가정한 공유 행이에요. 실제 파일 수집 결과가 아니에요. `collected`일 때는 세 값이 있어야 하고 부재 자료가 있는 `absent`, 조회 오류인 `query-error`, 자료가 없는 `uncollected`에서는 셋 모두 `null`로 남겨요.

아래 전체 코드는 ZIP의 Python 파일과 같아요. `ENTRY`는 `/home/example` 한 경로, `host1`·`host2`·`*` 중 한 대상, `ro` 또는 `rw`와 `root_squash`를 순서대로 붙인 형식만 다뤄요. 주석, 여러 대상, 다른 경로, 옵션 순서 변경이나 다른 옵션은 해석 보류예요. 실제 exports 문법 전체를 허용·거부하는 도구로 쓰지 않아요.

```python
import json
import re
import sys
from pathlib import Path

COLLECTIONS = {"collected", "absent", "query-error", "uncollected"}
KEYS = {"id", "collection", "ownerUid", "mode", "line"}
ENTRY = re.compile(
    r"/home/example[ \t]+(?P<client>host1|host2|\*)"
    r"\((?P<access>ro|rw),root_squash\)"
)


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
    if not isinstance(rows, list) or not 1 <= len(rows) <= 20:
        raise ValueError("사례 목록은 1~20건이어야 해요")
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
        if state == "collected":
            uid = row["ownerUid"]
            if type(uid) is not int or not 0 <= uid <= 4294967295:
                raise ValueError("ownerUid는 범위 안의 정수여야 해요")
            if not isinstance(row["mode"], str) or not re.fullmatch(r"0[0-7]{3}", row["mode"]):
                raise ValueError("mode는 0과 8진수 세 자리 문자열이어야 해요")
            if not isinstance(row["line"], str) or len(row["line"]) > 256 or "\n" in row["line"] or "\r" in row["line"]:
                raise ValueError("line은 256자 이하의 한 줄 문자열이어야 해요")
        elif any(row[key] is not None for key in ("ownerUid", "mode", "line")):
            raise ValueError("미수집 상태의 소유자·모드·행은 null이어야 해요")
    return rows


def assess(row):
    if row["collection"] != "collected":
        return "해석 보류", "수집 상태 " + row["collection"]
    findings = []
    if row["ownerUid"] != 0:
        findings.append("설정 소유자 UID=" + str(row["ownerUid"]))
    extra = int(row["mode"], 8) & ~0o644
    if extra:
        findings.append(f"644 밖 권한 비트={extra:04o}")
    match = ENTRY.fullmatch(row["line"])
    if match is None:
        detail = "; ".join(["호스트·괄호 결합 또는 지원 문법 조사"] + findings)
        return "해석 보류", detail
    client, access = match.group("client", "access")
    if client == "*":
        findings.append("전체 클라이언트 표기")
    if findings:
        return "검토 후보", "; ".join(findings)
    return "제한 표기", f"대상={client}; 요청={access}; 설정 UID=0; mode={row['mode']}"


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 JSON 파일 하나를 지정해 주세요")
        rows = load_rows(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("가상 exports 대조 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        status, detail = assess(row)
        print(f"{row['id']}: {status} | {detail}")
    print(f"대조한 가상 항목: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`load_rows()`는 최대 24,001바이트를 읽고 24,000바이트 초과를 거부해요. UTF-8·JSON, 1\~20건 범위, 정확한 키와 고유 ID를 검사한 다음 수집 상태와 값의 대응을 살펴요. `ownerUid`는 참·거짓을 제외한 0\~4,294,967,295의 정수, `mode`는 첫 자리가 0인 네 자리 8진수 문자열이에요. 특수 비트·ACL·소유 그룹·링크 여부는 입력에 없어요. `line`은 256자 이하 한 줄이며 파일 경로로 열지 않아요.

열 건에서는 제한 표기 2건, 검토 후보 4건, 해석 보류 4건이 나왔어요. 종료 0은 전체 입력 검사와 문자열·비트 대조를 마쳤다는 뜻이에요. 제한 표기는 이 코드의 형태와 속성이 맞았다는 분류라서 호스트의 업무상 허가·쓰기 필요성·실제 접근 허용이나 U-40 종합 양호 판정을 포함하지 않아요.

[[run:1]]

`bound-ro`와 `bound-rw`는 대상 이름과 `ro`·`rw`를 각각 출력해요. `all-clients`는 파일의 소유자·모드가 같고 `ro,root_squash`가 있어도 전체 대상 표기가 남아 후보예요. 호스트 이름을 DNS로 조회하거나 클라이언트에 마운트를 요청한 결과는 없어요.

## 0460에서 그룹 쓰기 0020이 남는 과정

명령의 JSON 인수는 `main()`에서 `Path(sys.argv[1])`이 되어 `load_rows()`로 들어가요. `unique_object()`는 JSON 중복 키를 거부하고 목록 전체의 형식 검사가 끝난 뒤 `main()`이 각 `row`를 `assess(row)`에 넘겨요. 여섯 번째 행에서도 `collection`이 `collected`라 첫 보류 분기를 지나가요.

`ownerUid`는 0이라 `findings`는 빈 목록으로 시작해요. 다음 식 `int(row["mode"], 8) & ~0o644`에 `0460`을 대입하면 `int("0460", 8)`은 십진수 304, `0o644`는 420이에요. AND 결과인 `extra`는 십진수 16, 네 자리 8진수로 `0020`이 돼요. 그룹 자리의 읽기 4와 쓰기 2 중 쓰기 비트가 기준 0644 밖에 남은 거예요.

이 실습은 ‘644 이하’를 숫자 대소 대신 0644에 없는 일반 권한 비트가 켜졌는지 대조하는 방식으로 정의했어요. `0460`은 숫자로는 0644보다 작아도 그룹 쓰기를 갖고 있어요. `if extra`가 참이어서 `findings`에 `644 밖 권한 비트=0020`이 들어가요.

이어 `ENTRY.fullmatch(row["line"])`는 전체 행과 맞아 `match`를 만들어요. `client, access`에는 `host1`, `ro`가 들어가고 `client == "*"`는 거짓이에요. 이미 `findings`에 권한 사유가 있으므로 `if findings`에서 `("검토 후보", "644 밖 권한 비트=0020")`를 반환해요. 마지막 제한 표기 반환에는 도달하지 않아요. `main()`은 `status, detail`로 받아 실제 기록의 `numeric-trap: 검토 후보 | 644 밖 권한 비트=0020`을 출력해요.

`group-write`의 `0664`도 같은 `0020`이 남아요. `other-owner`는 모드가 0644여도 UID 1000이 root 소유 사례와 달라 후보가 돼요. 두 결과 모두 설정 파일의 속성 차이를 가리키며 공유 안 파일들의 권한을 조사한 결과는 아니에요.

## 공백은 고치지 않고 해석 보류로 남겨요

`space-before-options`의 `line`에는 `host1` 다음 공백이 있어요. `ENTRY`는 대상 바로 뒤에 여는 괄호를 요구하므로 `fullmatch()`가 `None`을 반환해요. 이때 호스트·괄호 결합 또는 지원 문법 조사로 보류해요. 공백을 자동 삭제해서 `bound-ro`와 같은 행으로 바꾸면 입력에 있던 차이가 사라져요.

이 보류는 Linux가 그 행을 반드시 구문 오류로 거부했다는 실행 결과가 아니에요. 사용 중인 구현의 문서와 실제 적용된 공유 자료를 다시 조사할 위치예요. 구문을 해석하지 못한 행에 소유자·권한 사유도 있으면 그 사유는 함께 남기도록 `findings`를 먼저 계산해요.

입력 자료 자체가 모순된 경우에는 분류를 시작하지 않아요. `u40_rejected.json`은 `uncollected`라면서 UID·모드·행 값을 채워 둔 파일이에요. 다음 실행 직후에도 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 코드를 읽어요.

```bash
python -I -B -X utf8 u40_exports_review.py u40_rejected.json
```

`load_rows()`의 `any(row[key] is not None ...)`가 참이라 예외가 나고 `main()`이 종료 2를 반환해요. 표준 출력은 가상 exports 대조 미실행, 표준 오류는 미수집 값의 `null` 대응 안내예요.

[[run:2]]

예상한 거부의 재현과 입력 허용을 구분해 주세요. 정상 입력에서 오류가 나면 실행 위치·파일명·읽기 권한, JSON·UTF-8·크기·중복, UID와 모드 형식, 수집 상태와 값의 대응을 살펴보세요.

## 부재·조회 오류·미수집이 가리키는 자료

정상 목록의 `file-absent`는 설정 파일 부재를 뒷받침하는 자료가 있다는 가정이에요. `query-error`는 조회 과정의 오류, `uncollected`는 자료 자체가 없는 경우예요. 셋은 `assess()`의 첫 분기에서 각각의 상태로 반환돼요. `null`을 모드 0000이나 빈 공유 목록으로 채우지 않아요.

Linux `exports(5)`는 `/etc/exports`를 읽은 뒤 `/etc/exports.d`의 `.exports` 파일도 읽는다고 설명해요. 그래서 `file-absent` 하나에서 모든 NFS 공유의 부재를 추론할 수 없어요. 부재가 어느 파일과 수집 시점에 해당하는지, 추가 공유 파일과 실제 적용 자료가 조사 범위에 들어왔는지를 별도로 남겨야 해요.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [nfs-utils: exports(5)의 대상·옵션 결합, 권한 매핑과 추가 공유 파일](https://www.man7.org/linux/man-pages/man5/exports.5@@nfs-utils.html)
- [Red Hat Enterprise Linux 7: NFS 서버의 exports 설정 형식](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/storage_administration_guide/nfs-serverconfig)
