---
title: "U-14: root 홈, 패스 디렉터리 권한 및 패스 설정"
description: "PATH에서 현재 디렉터리와 빈 항목의 위치를 구분하고, 같은 이름의 가상 실행 후보가 선택되는 순서를 비교합니다."
date: "2026-10-19T18:33:58+09:00"
updated: "2026-10-22"
sourcesChecked: "2026-10-19"
category: "critical-infrastructure"
tags: ["주통기","U-14","PATH","셸"]
draft: false
example: false
assessmentTarget: "unix"
series: "unix-2026"
seriesOrder: 14
---

PATH는 명령 이름을 입력했을 때 실행 파일을 찾는 디렉터리의 순서다. root가 사용하는 PATH에 현재 작업 디렉터리가 먼저 들어 있으면 같은 이름의 다른 파일을 선택할 수 있다. U-14에서는 PATH의 문자열뿐 아니라 어떤 로그인 경로에서 그 값이 만들어졌는지 함께 조사한다.

## 가이드의 판단 기준은 마침표의 위치다

2026 KISA 상세가이드의 U-14는 중요도 ‘상’이며 Solaris·Linux·AIX·HP-UX 등을 대상으로 한다. 공식 제목은 ‘root 홈, 패스 디렉터리 권한 및 패스 설정’이다. 원문 39쪽의 판단 기준은 PATH에서 현재 디렉터리를 나타내는 `.`이 맨 앞이나 중간에 포함돼 있는지다. 그 위치에 있으면 취약, 그렇지 않으면 양호로 분류한다.

가이드는 현재 디렉터리를 PATH의 마지막으로 옮기는 방법과 상대 경로를 삭제하는 사례를 제시한다. 따라서 맨 끝의 `.`을 앞·중간과 같은 공식 취약 기준으로 적어서는 안 된다. 운영 정책에서 현재 디렉터리 탐색 자체를 빼도록 정했다면 그 정책은 가이드의 위치 기준과 구분해 적용한다.

| 가상 PATH | 가이드의 위치 기준으로 읽을 부분 |
| --- | --- |
| `.:/usr/bin:/usr/sbin` | 현재 디렉터리가 첫 번째 |
| `/usr/sbin:.:/usr/bin` | 현재 디렉터리가 중간 |
| `/usr/bin:/usr/sbin:.` | 현재 디렉터리가 마지막 |

점검할 때는 대상 계정에서 수집한 PATH와 그 값을 만드는 환경 파일을 이 위치 기준에 맞춰 대조한다.

## 같은 이름을 앞에서 찾으면 뒤까지 가지 않는다

GNU Bash의 명령 탐색 설명에서는 함수·내장 명령이 아닌 외부 명령을 PATH에서 찾는다. 이름에 슬래시가 들어간 명령은 이와 구분되며, Bash에는 이미 찾은 실행 경로를 기억하는 해시 테이블도 있다.

다음은 외부 명령의 경로 탐색만 가상 목록으로 표현한 Python 코드다. `u14_path_lookup.py`로 저장해 `python -I -B -X utf8 u14_path_lookup.py`로 실행한다. 실제 root 계정이나 환경변수, 파일 권한을 바꾸지 않는다. 목록의 후보는 실행 가능하다고 가정하며 셸 함수·별칭·내장 명령·해시 캐시·심볼릭 링크는 구현하지 않았다.

[[download]]

```python
import posixpath

CWD = "/lab/work"
FILES = {
    "/usr/bin/lab-tool": "시스템 후보",
    "/lab/work/lab-tool": "작업 폴더 후보",
    "/lab/work/local-only": "작업 폴더 전용 후보",
}


def lookup(command, path):
    if "/" in command:
        candidate = posixpath.normpath(posixpath.join(CWD, command))
        return candidate if candidate in FILES else None
    for entry in path.split(":"):
        directory = posixpath.normpath(posixpath.join(CWD, entry or "."))
        candidate = posixpath.join(directory, command)
        if candidate in FILES:
            return candidate
    return None


cases = [
    ("현재 경로가 앞", ".:/usr/bin:/usr/sbin"),
    ("현재 경로가 중간", "/usr/sbin:.:/usr/bin"),
    ("현재 경로가 끝", "/usr/bin:/usr/sbin:."),
    ("앞부분이 빈 필드", ":/usr/bin"),
    ("절대 경로만 사용", "/usr/bin:/usr/sbin"),
]
assert lookup("lab-tool", cases[0][1]) == "/lab/work/lab-tool"
assert lookup("lab-tool", cases[1][1]) == "/lab/work/lab-tool"
assert lookup("lab-tool", cases[2][1]) == "/usr/bin/lab-tool"
assert lookup("lab-tool", cases[3][1]) == "/lab/work/lab-tool"
assert lookup("local-only", cases[2][1]) == "/lab/work/local-only"
assert lookup("local-only", cases[4][1]) is None
assert lookup("/usr/bin/lab-tool", cases[0][1]) == "/usr/bin/lab-tool"
assert lookup("./lab-tool", cases[4][1]) == "/lab/work/lab-tool"

for label, path in cases:
    result = lookup("lab-tool", path)
    print(f"{label}: {result}")
print("끝에 현재 경로가 있고 시스템 후보가 없을 때:",
      lookup("local-only", cases[2][1]))
print("현재 경로를 뺀 뒤 같은 이름을 찾을 때:",
      lookup("local-only", cases[4][1]))
```

ZIP의 `u14_path_lookup.py` 파일을 사용한다. 저장한 폴더에서 위 명령으로 실행한다. Linux·WSL에서는 명령 이름을 `python3`로 바꿔도 된다. `/lab/work`와 `/usr/bin/lab-tool`을 실제로 만들 필요는 없다. `FILES`의 키가 가상 파일 목록이고 `posixpath`가 Unix 형식의 경로 문자열만 계산한다.

`lookup()`은 명령에 슬래시가 있으면 지정 경로만 대조한다. 이름만 있으면 `path.split(":")`의 왼쪽부터 후보를 만들고, 처음 `FILES`에 있는 경로를 만나자마자 반환한다. `entry or "."`가 빈 항목을 현재 디렉터리로 바꾸며 끝까지 못 찾으면 `None`이다. 파일의 내용을 실행하는 함수는 아니다.

[[run:1]]

앞·중간에 현재 디렉터리를 둔 두 경우는 작업 폴더 후보를 선택했다. 끝으로 옮겼을 때는 `/usr/bin/lab-tool`이 먼저 나왔다. `local-only`처럼 시스템 경로에 없는 이름은 끝의 현재 디렉터리까지 탐색했다. 마지막 `.`도 현재 디렉터리를 탐색한다는 동작은 남는다.

[[diagram]]

마지막 `None`은 시스템 경로에서 `local-only`를 찾지 못했다는 반환값이다. 실행 오류 메시지나 명령이 차단됐다는 결과가 아니다. 코드에 있는 `assert`는 슬래시가 든 직접 경로와 빈 항목 등 기대값도 대조한다. 종료 코드 `0`은 이 비교가 통과했다는 뜻이므로 `-O`로 검사를 끄지 않는다.

이 비교에서 선택 순서를 바꾼 값은 PATH이며 파일 목록은 그대로다. 운영 점검에서는 신뢰할 수 없는 사용자가 앞쪽 디렉터리에 파일을 만들 수 있는지도 조사한다. 절대 경로를 명시한 호출, 이름만 적은 호출, 작업 디렉터리를 바꾸는 스크립트는 탐색 조건이 다르다.

## 빈 필드도 현재 디렉터리가 될 수 있다

Bash의 PATH 설명에 따르면 길이가 0인 디렉터리 항목은 현재 디렉터리다. 맨 앞이나 끝의 콜론, 연속된 콜론이 이 항목을 만든다. 예제의 `:/usr/bin`은 문자 `.`이 없어도 작업 폴더 후보를 먼저 선택했다.

점검 스크립트를 `"." in path`처럼 작성하면 이름에 마침표가 들어간 정상 디렉터리까지 잘못 분류할 수 있다. 반대로 정확히 `.`인 항목만 찾으면 빈 항목이나 다른 상대 경로를 놓칠 수 있다. PATH를 콜론 단위로 나눈 뒤 빈 항목, 정확한 마침표, 그 밖의 상대 경로를 구분한다. 빈 항목의 해석은 여기서 다룬 Bash의 동작이며 다른 셸은 해당 매뉴얼과 대조한다.

가이드가 정한 마침표 위치와 이런 추가 조사 결과는 점검 기록의 칸을 나눠 적는다. ‘문자 마침표 없음’과 ‘현재 디렉터리를 탐색하지 않음’은 서로 다른 관찰이다.

## 접속 경로별 유효값과 설정 파일을 묶어 남긴다

KISA는 root 환경 파일과 `/etc/profile` 등 시스템 환경 파일, 사용자 환경 파일을 순차적으로 살피도록 안내한다. sh·ksh·csh·bash는 읽는 파일이 다르다. Bash도 로그인·비로그인, 대화형 여부에 따라 시작 파일이 달라지므로 특정 파일 하나를 수정한 결과가 모든 접속 경로에 적용됐다고 가정하지 않는다.

대상 계정의 홈 경로와 셸을 먼저 조회하고, 승인된 새 세션에서 `printf '%s\n' "$PATH"`로 얻은 값에 접속 방식을 함께 적는다. 이 명령은 조사 방법이며 위 Python 실행 기록에 포함된 명령은 아니다. PATH를 재정의하거나 이어 붙이는 설정도 추적해 최종 항목 순서를 대조한다.

현재 경로를 삭제하거나 순서를 바꾸기 전에는 배치가 상대 경로의 도구를 기대하는지 조사한다. 변경 후에는 새 로그인 세션과 해당 배치의 실행 조건에서 명령 해석을 시험한다. 최종 기록에는 사용 셸·접속 경로·PATH 항목 순서와 함께 앞쪽 디렉터리의 소유자·쓰기 권한 조사 결과를 남긴다.

## 참고 자료

- [KISA 2026 주요정보통신기반시설 상세가이드: U-14, 39쪽](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Bash(1): PATH·명령 탐색·실행 경로 캐시](https://man7.org/linux/man-pages/man1/bash.1.html)
