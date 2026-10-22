---
title: "U-17: 시스템 시작 스크립트 권한 설정"
description: "시작 스크립트의 링크와 실제 대상 파일을 나눠 살피고, 가상 경로 여섯 개에서 소유자·쓰기 권한·끊어진 링크를 비교합니다."
date: "2026-10-22T18:46:15+09:00"
sourcesChecked: "2026-10-22"
category: "critical-infrastructure"
assessmentTarget: "unix"
tags: ["주통기", "U-17", "Linux", "systemd", "파일권한"]
draft: false
example: false
series: "unix-2026"
seriesOrder: 17
---

시작 디렉터리에 있는 링크는 root 소유인데, 그 링크가 가리키는 스크립트에는 다른 사용자의 쓰기 권한이 남아 있을 수 있다. 링크 이름 옆의 소유자만 보고 점검을 마치면 실제로 실행될 파일의 변경 권한을 놓친다.

## 시작할 때 읽는 파일의 변경 권한

2026 KISA 상세가이드 42~43쪽의 U-17은 중요도 ‘상’이며 Solaris·Linux·AIX·HP-UX 등을 대상으로 한다. 시스템 시작 스크립트가 root 소유이고 일반 사용자의 쓰기 권한이 제거돼 있으면 양호로, 소유자가 다르거나 일반 사용자에게 쓰기가 허용돼 있으면 취약으로 판단한다.

시작 스크립트는 부팅 과정에서 초기화와 서비스 시작에 사용된다. 일반 계정이 이 파일의 내용을 바꿀 수 있다면 다음 시작 때 다른 명령이 실행될 여지가 생긴다. [U-16의 passwd 파일](../u-16-passwd-owner-permissions/)과 소유자 조회 방법은 비슷하지만, 이번 항목에서는 시작 경로와 연결된 대상 파일을 함께 추적한다.

원문은 init 계열의 시작 디렉터리와 Linux systemd의 `/etc/systemd/system/` 예시를 구분한다. 조치 예시의 `chmod o-w`는 **기타 사용자의 쓰기 비트만** 제거한다. 그룹에 일반 계정이 포함돼 있다면 그룹 쓰기 권한으로도 수정할 수 있으므로, 이 명령 하나로 모든 일반 사용자의 쓰기가 차단됐다고 결론 내리지 않는다.

## init 링크와 systemd 설정을 나눠 살피기

init 방식에서는 시작 순서에 놓인 링크와 그 목적지 스크립트를 구분해 목록을 만든다. Linux의 [일반 심볼릭 링크](https://man7.org/linux/man-pages/man7/symlink.7.html)에 보이는 `0777`을 일반 파일의 쓰기 권한처럼 해석하지 않고, [경로 해석 과정](https://man7.org/linux/man-pages/man7/path_resolution.7.html)에서 실제로 도달하는 파일을 살핀다. 링크가 끊어졌거나 순환하면 정상 파일을 수집한 것으로 세지 않는다.

systemd에서는 유닛 파일, 덮어쓰는 drop-in 설정, `ExecStart=` 등이 지정하는 실행 파일을 함께 읽는다. 공급업체 유닛이 `/usr/lib/systemd/system/`에 있고 `/etc/systemd/system/`에서 이를 보완하는 경우도 있다. 파일 이름이 같은 후보를 전부 같은 우선순위로 처리하지 말고, 해당 시스템이 적용하는 파일을 먼저 찾는다. 검색 경로와 drop-in의 병합 방식은 [systemd.unit 공식 문서](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html)에 정리돼 있다.

[[diagram]]

실제 수집 자료에는 시작 항목의 경로, 링크 목적지, 최종 파일의 UID·GID·모드, 파일을 교체할 수 있는 상위 디렉터리와 ACL을 묶어 둔다. root 소유 파일이라도 상위 디렉터리를 통해 다른 파일로 교체할 수 있으면 그 경로까지 검토한다.

## 가상 링크를 따라가며 속성을 비교하기

다음 실습은 Python 3.9 이상과 표준 라이브러리만 사용한다. ZIP을 풀어 `u17_startup_paths.py`가 있는 폴더에서 `python -I -B -X utf8 u17_startup_paths.py`로 실행한다. Linux·WSL에서는 명령 이름을 `python3`로 바꿀 수 있다. 입력 파일이나 `/lab` 디렉터리를 따로 만들 필요는 없다.

`FILES`는 파일시스템 대신 사용하는 사전이다. 각 값은 종류·UID·일반 권한 모드·링크 목적지 순서다. 실제 파일·계정·서비스에는 접근하지 않는다. 가상 경로의 마지막 링크만 따라가며 중간 디렉터리 링크, ACL, 특수 권한과 systemd 설정 해석은 구현하지 않았다.

[[download]]

```python
import posixpath

# 경로와 속성은 모두 가상 자료다. 실제 파일을 열거나 실행하지 않는다.
FILES = {
    "/lab/rc3.d/S20app": ("link", 0, 0o777, "../init.d/app"),
    "/lab/init.d/app": ("file", 0, 0o755, None),
    "/lab/rc3.d/S21job": ("link", 0, 0o777, "../init.d/job"),
    "/lab/init.d/job": ("file", 0, 0o756, None),
    "/lab/custom.service": ("file", 1001, 0o644, None),
    "/lab/override.conf": ("file", 0, 0o664, None),
    "/lab/broken": ("link", 0, 0o777, "missing"),
    "/lab/loop-a": ("link", 0, 0o777, "loop-b"),
    "/lab/loop-b": ("link", 0, 0o777, "loop-a"),
}
CASES = (
    ("정상 대상", "/lab/rc3.d/S20app", "기본 조건 충족"),
    ("기타 쓰기", "/lab/rc3.d/S21job", "조건 불일치"),
    ("소유자 다름", "/lab/custom.service", "조건 불일치"),
    ("그룹 쓰기", "/lab/override.conf", "그룹 구성원 추가 검토"),
    ("끊어진 링크", "/lab/broken", "미수집"),
    ("링크 순환", "/lab/loop-a", "미수집"),
)


def resolve_node(path):
    # 가상 사전에서 최종 파일을 찾는다. 중간 디렉터리 링크는 구현하지 않는다.
    seen = set()
    while True:
        path = posixpath.normpath(path)
        if path in seen:
            raise ValueError("링크 순환")
        seen.add(path)
        if path not in FILES:
            raise ValueError("대상 자료 없음")
        kind, uid, mode, target = FILES[path]
        if kind == "file":
            return path, uid, mode
        if kind != "link" or not target:
            raise ValueError("지원하지 않는 자료")
        path = posixpath.join(posixpath.dirname(path), target)


def inspect(path):
    try:
        target, uid, mode = resolve_node(path)
    except ValueError as error:
        return "미수집", str(error)
    if uid != 0 or mode & 0o002:
        state = "조건 불일치"
    elif mode & 0o020:
        state = "그룹 구성원 추가 검토"
    else:
        state = "기본 조건 충족"
    return state, f"대상={target}, UID={uid}, 모드={mode:04o}"


for label, path, expected in CASES:
    state, detail = inspect(path)
    if state != expected:
        raise AssertionError(f"{label}: 기대={expected}, 실제={state}")
    print(f"{label}: {state}; {detail}")
print(f"가상 경로 {len(CASES)}건 비교 통과")
```

`resolve_node()`는 경로를 정규화한 뒤 `FILES`에서 항목을 가져온다. 링크면 그 링크의 디렉터리를 기준으로 상대 목적지를 연결한다. `S20app`의 `../init.d/app`이 `/lab/init.d/app`으로 바뀌는 지점이다. 이미 거친 경로는 `seen`에 넣어 순환을 끝내고, 사전에 목적지가 없으면 `ValueError`를 발생시킨다.

`inspect()`는 최종 파일의 UID와 모드를 받는다. UID가 0이 아니거나 `mode & 0o002`가 남으면 조건 불일치다. 기타 쓰기는 없지만 `mode & 0o020`이 남으면 그룹 구성원을 조사할 대상으로 분리한다. 그룹 명단을 입력받지 않았기 때문에 이 분기에서 일반 계정의 실제 쓰기 가능 여부까지 결정하지 않는다.

`CASES`의 마지막 값은 기대 상태다. 계산한 상태와 다르면 `AssertionError`로 중단한다. 모든 기대값이 맞으면 마지막에 비교한 사례 수를 출력하고 종료 코드 0으로 끝난다. 미수집 사례가 들어 있어도 그것이 의도한 관찰값이면 실습 검사는 통과한다.

[[run:1]]

첫 사례에서는 링크의 `0777` 대신 최종 파일의 `0755`가 출력된다. 두 번째는 목적지의 모드가 `0756`이어서 기타 쓰기 비트 `002`가 남는다. 세 번째는 모드가 `0644`여도 소유자 UID가 1001이라 조건 불일치다.

`override.conf`의 `0664`는 그룹 쓰기 `020`을 따로 검토하는 경로로 들어간다. 끊어진 링크와 순환 링크에는 UID·모드가 출력되지 않고, 각각 자료 없음과 순환 사유가 남는다. 이 두 줄을 ‘쓰기 권한 없음’으로 바꿔 집계하면 수집하지 못한 대상을 안전한 파일로 잘못 처리하게 된다.

## 권한을 바꾸기 전에 적용 경로부터 남기기

운영 환경에서는 적용 중인 유닛과 시작 스크립트 목록을 먼저 보존한 뒤 소유자·기타 쓰기·그룹 구성원·ACL·상위 디렉터리를 대조한다. 패키지 관리 파일과 배포 도구가 관리하는 파일도 구분한다. 디렉터리 전체에 재귀적으로 같은 모드를 적용하면 필요한 탐색·실행 권한까지 바뀔 수 있다.

권한을 조정했다면 같은 경로를 다시 수집하고, 변경 절차에서 정한 서비스 시작 시험으로 영향을 살핀다. 위 실습은 가상 속성 비교만 했으므로 서비스 재시작이나 재부팅 결과는 포함하지 않는다.

## 참고 자료

- [KISA 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1): 2026판 U-17, PDF 42~43쪽
- [systemd.unit: Unit configuration](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html)
- [Linux path_resolution(7)](https://man7.org/linux/man-pages/man7/path_resolution.7.html)

- [Linux symlink(7)](https://man7.org/linux/man-pages/man7/symlink.7.html)
