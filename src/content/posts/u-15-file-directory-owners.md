---
title: "U-15: 파일 및 디렉터리 소유자 설정"
description: "가상 자료의 UID·GID를 계정·그룹 목록과 대조하며, 이름이 조회되지 않는 소유자와 UID 재사용의 영향을 살펴봅니다."
date: "2026-10-20T18:38:46+09:00"
updated: "2026-10-22"
sourcesChecked: "2026-10-20"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-15", "UID", "GID", "파일권한"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 15
---

계정을 삭제해도 그 계정이 소유하던 파일의 숫자 UID는 남을 수 있어요. 나중에 다른 계정에 같은 UID를 부여하면 파일 속성을 바꾸지 않았는데도 새 계정이 소유자로 조회돼요. U-15는 이렇게 소유자를 찾을 수 없는 파일과 디렉터리를 조사하는 항목이에요.

## 가이드의 소유자 기준과 그룹 조회

2026 KISA 상세가이드에서 U-15의 중요도는 ‘상’이며 Solaris·Linux·AIX·HP-UX 등을 대상으로 해요. 원문 40쪽은 소유자가 존재하지 않는 파일·디렉터리가 없으면 양호, 있으면 취약으로 판단해요. 조치 방법으로는 불필요한 자료의 제거 또는 소유자 변경을 제시해요.

같은 쪽의 점검 사례에서는 소유자와 그룹을 함께 찾도록 안내해요. GNU find에서 `-nouser`는 파일의 숫자 UID에 대응하는 사용자가 없는 경우이고 `-nogroup`은 숫자 GID에 대응하는 그룹이 없는 경우예요. 두 조건을 OR로 묶으면 어느 한쪽이라도 조회되지 않는 항목을 선택해요.

결과에는 소유자 조회 실패와 그룹 조회 실패를 따로 표시하는 편이 좋아요. UID는 정상적으로 조회되고 GID만 없는 파일을 ‘소유자가 없는 파일’로 적으면 가이드의 판단 기준과 수집한 현상이 뒤섞여요. 그룹이 존재하지만 구성원 칸만 빈 경우도 `-nogroup`과는 달라요. 그룹의 필요성과 구성원 관계는 [U-09의 GID 점검](../u-09-unused-gid/)에서 다뤄요.

## 숫자 표시와 이름 조회 실패를 구분한다

파일에 기록된 UID·GID는 계정·그룹 이름으로 해석해 표시할 수 있어요. `ls -n`은 이름 대신 숫자를 출력하는 옵션이라 이 출력에서 숫자가 보이는 것은 정상이에요. 이름을 표시하는 명령에서 이름이 나오지 않을 때는 해당 ID를 조회할 수 있는지 조사해요.

Linux의 `getent`는 NSS(Name Service Switch)에 설정된 데이터베이스를 조회해요. 예를 들어 `getent passwd 41001`은 UID 41001의 사용자, `getent group 42001`은 GID 42001의 그룹을 조회하는 방식이에요. 중앙 계정 서비스를 사용하는 시스템에서는 로컬 파일뿐 아니라 설정된 조회 경로와 서비스 상태도 함께 살펴봐요.

계정 조회 장애 중에 나온 결과와 계정을 정리한 뒤 남은 소유권은 원인이 달라요. 당시의 조회 상태를 기록하고 중앙 서비스가 복구된 뒤 같은 ID를 다시 대조해야 해요. `/etc/passwd`에 이름이 없다는 이유만으로 중앙 계정까지 없다고 결론 내리지 않아요.

## 가상 파일 속성과 계정표를 대조하기

아래 코드는 파일 네 개의 속성 목록을 가상 계정·그룹 표와 비교해요. 실제 파일이나 계정 데이터베이스를 읽거나 소유권을 변경하지는 않아요. `u15_owner_mapping.py`로 저장해 `python -I -B -X utf8 u15_owner_mapping.py`를 실행하면 돼요.

[[download]]

```python
USERS = {1000: "alice"}
GROUPS = {1000: "app"}
FILES = (
    ("/lab/live.conf", "file", 1000, 1000),
    ("/lab/archive", "directory", 41001, 1000),
    ("/lab/report.txt", "file", 1000, 42001),
    ("/lab/old.log", "file", 41001, 42001),
)


def unmapped(files, users, groups):
    result = []
    for path, kind, uid, gid in files:
        no_user = uid not in users
        no_group = gid not in groups
        if no_user or no_group:
            result.append((path, kind, no_user, no_group))
    return result


snapshot = tuple(FILES)
before = unmapped(FILES, USERS, GROUPS)
assert before == [
    ("/lab/archive", "directory", True, False),
    ("/lab/report.txt", "file", False, True),
    ("/lab/old.log", "file", True, True),
]
assert all(path != "/lab/live.conf" for path, *_ in before)

for path, kind, no_user, no_group in before:
    missing = []
    if no_user:
        missing.append("UID")
    if no_group:
        missing.append("GID")
    print(f"{path} ({kind}): {'·'.join(missing)} 정의 없음")

print(f"UID 조회 실패: {sum(row[2] for row in before)}개")
print(f"GID 조회 실패: {sum(row[3] for row in before)}개")

reused_users = {**USERS, 41001: "newapp"}
after = unmapped(FILES, reused_users, GROUPS)
assert after == [
    ("/lab/report.txt", "file", False, True),
    ("/lab/old.log", "file", False, True),
]
assert FILES == snapshot
assert FILES[1][2] == 41001
assert 41001 not in USERS and reused_users[41001] == "newapp"
print(f"UID 41001의 이름: {USERS.get(41001, '없음')} -> {reused_users[41001]}")
print(f"archive의 UID: {snapshot[1][2]} -> {FILES[1][2]}")
print("재사용 뒤 남은 후보: " + ", ".join(row[0] for row in after))
```

Python 3 표준 기능으로 실행해요. ZIP을 푼 폴더에서 위 명령을 사용하고 Linux·WSL에서는 명령 이름을 `python3`로 바꿀 수 있어요. `/lab` 아래 파일은 만들지 않아요. `FILES`의 각 튜플이 경로·종류·UID·GID를 제공하고 `USERS`와 `GROUPS`가 이 실습의 조회 표예요.

`unmapped()`는 각 ID가 표의 키에 없는지 따로 계산해요. 예를 들어 `old.log`의 UID 41001과 GID 42001은 두 표에 모두 없으므로 `no_user`·`no_group`이 둘 다 참이에요. `if no_user or no_group`을 통과하면 이 파일이 결과에 한 번 들어가요. `kind`는 표시용 값이라 조건을 바꾸지 않아요.

결과 튜플의 세 번째·네 번째 값은 두 조건이 각각 참인지 거짓인지 나타내요. `sum(row[2] ...)`와 `sum(row[3] ...)`는 각 열에서 참인 수를 따로 세므로 같은 파일이 양쪽 건수에 포함될 수 있어요.

입력의 `archive`는 소유자만, `report.txt`는 그룹만, `old.log`는 둘 다 가상 표에 없는 경우예요. 조회되는 `live.conf`와 함께 비교해요.

[[run:1]]

UID 조회 실패 두 개와 GID 조회 실패 두 개는 old.log에서 한 번 겹쳐요. 그래서 후보 경로는 `2 + 2 - 1 = 3`개예요.

계정표에 `newapp`을 추가한 뒤에는 `archive`가 후보에서 빠졌어요. 파일 속성 목록의 UID 41001은 그대로지만 대응하는 이름이 생겼기 때문이에요. 이 실습은 이름 매핑의 변화만 비교해요. 실제 읽기·쓰기 허용 여부는 파일 모드와 ACL 등 접근 제어 조건도 함께 평가해야 해요.

[[diagram]]

조회 실패 건수가 줄어든 이유도 구분해서 기록해야 해요. 담당자를 조사해 소유권을 이관한 결과와 다른 용도로 같은 UID를 재사용한 결과는 서로 다른 변경이거든요. UID를 다른 용도로 재사용했다면 이름이 표시되더라도 새 계정이 해당 자료를 소유해야 하는지 추가로 검토해야 해요.

`reused_users = {**USERS, 41001: "newapp"}`는 원래 계정표를 고치지 않고 비교용 표를 새로 만들어요. 재사용 뒤에도 GID 42001은 없어서 report.txt와 old.log는 남아요. `assert FILES == snapshot`은 파일 속성 입력이 바뀌지 않았음을 대조해요. 이 코드의 `0`은 가상 비교가 기대값과 같았다는 뜻이며 `find`가 실제 디스크를 조사한 종료 상태와 달라요. Python의 `-O` 옵션 없이 실행해요.

## 조사 범위와 소유권 이관을 기록한다

원문의 find 사례에는 `-xdev`가 포함돼 있어요. 이 옵션은 다른 파일시스템의 디렉터리 내부로 내려가지 않으니 별도 마운트된 업무·데이터 영역은 조사 대상 목록에 따로 포함해요. 승인된 경로를 대상으로 읽기 전용 조사를 수행하고 접근 거부와 계정 조회 오류도 결과와 함께 보관해요. 오류가 발생한 구간을 조사 완료로 처리하지 않아요.

후속 조치는 파일의 사용 목적에 따라 정해요. 백업 보관 자료, 배포 산출물, 서비스가 계속 사용하는 디렉터리는 담당자와 현재 사용 여부부터 조사해요. 보존할 자료라면 이관받을 계정·그룹과 필요한 접근 권한을 정하고 불필요한 자료의 삭제는 보존 기간과 업무 영향 검토를 거쳐요.

변경 기록에는 경로, 이전 UID·GID, 새 소유자·그룹, 이관 또는 제거 사유를 남겨요. 이후 같은 파일시스템 범위에서 미조회 ID를 다시 찾고 서비스를 사용하는 계정으로 필요한 동작이 유지되는지도 시험해요. 숫자 ID를 다른 용도로 재사용할 계획이 있다면 기존 소유 자료의 처리 결과까지 함께 검토해요.

## 참고 자료

- [KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드, U-15, 40쪽](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [GNU find 매뉴얼: -nouser·-nogroup·-xdev와 종료 상태](https://man7.org/linux/man-pages/man1/find.1.html)
- [GNU C Library getent 매뉴얼: NSS 데이터베이스 조회](https://man7.org/linux/man-pages/man1/getent.1.html)
- [GNU ls 매뉴얼: 숫자 UID·GID 표시 옵션](https://man7.org/linux/man-pages/man1/ls.1.html)
