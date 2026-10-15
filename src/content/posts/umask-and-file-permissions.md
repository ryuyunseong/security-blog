---
title: "umask 설정과 실제 파일 권한"
description: "요청 모드·umask·기본 ACL이 새 파일의 실제 권한에 미치는 영향을 비교합니다."
date: "2026-10-08T21:26:23+09:00"
updated: "2026-10-16T00:00:00+09:00"
category: "unix"
tags: ["umask", "권한", "ACL"]
draft: false
example: false
---

`umask 077`이면 새 파일은 늘 `0600`일까? 부모 디렉터리에 기본 ACL이 있다면 같은 요청에서도 `0640`이 나올 수 있다.

전용 임시 폴더에 파일과 디렉터리를 만들면서 요청 모드·umask·기본 ACL을 하나씩 바꿔 본다. 기존 파일을 다시 열 때와 새로 만들 때의 차이도 함께 확인한다.

## 권한은 요청 모드에서 줄어든다

umask는 새 파일이나 디렉터리를 만들 때 제외할 권한 비트를 지정한다. 부모 디렉터리에 기본 ACL이 없다면 일반 권한 비트는 다음과 같이 계산한다.

```text
생성 권한 = 요청 모드 & ~umask & 0777
```
`&`는 비트 AND, `~`는 비트 반전이다. 요청한 권한 중 umask가 막지 않은 비트만 남는다. `0640`은 소유자에게 읽기·쓰기, 그룹에 읽기, 기타 사용자에게는 권한을 주지 않는 모드다. 디렉터리의 실행 비트는 경로를 탐색하는 권한에 해당한다.

일반 파일은 흔히 `0666`, 디렉터리는 `0777`을 요청하지만 프로그램에 따라 다르다. 파일을 `0600`으로 요청하면 umask가 `022`여도 `0600`이다. 실행 비트를 포함한 `0777`을 요청하면 같은 umask에서 `0755`가 될 수 있다.

이 계산은 뺄셈이 아니다. `0666`에는 실행 비트가 없으므로 실행 비트만 막는 umask `0111`을 적용해도 `0666`이다. Python 코드에서는 8진수를 `0o666`처럼 쓰고, 출력에서는 `0666`처럼 표시한다.

## 전용 임시 폴더에서 비교하기

Linux, Python 3.7 이상, `libacl` 공유 라이브러리와 POSIX ACL을 지원하는 쓰기 가능한 로컬 경로가 필요하다. 자식 프로세스의 umask를 조회하려면 `/proc/self/status`에 `Umask` 항목이 있어야 한다. 이 항목은 Linux 4.7부터 제공된다. 별도 Python 패키지는 사용하지 않는다.

일반 사용자로 본인 소유의 실습 경로에서 아래 코드 전체를 셸에 붙여넣는다. 현재 경로에 무작위 이름의 임시 폴더를 만들고 권한을 `0700`으로 제한한다. 변경 대상은 그 폴더와 내부 파일뿐이며, 생성한 파일을 실행하지 않는다. umask는 별도 Python 프로세스 안에서만 바꾸고 종료 전에 복원한다.

상위 경로의 기본 ACL이 상속됐을 수 있으므로 새 실습 폴더의 기본 ACL만 지워 비교 조건을 맞춘다. ACL 실험은 별도 하위 폴더에서 진행한다.

```bash
python3 - <<'PY'
import ctypes
import ctypes.util
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

# Linux의 libacl과 POSIX ACL을 지원하는 로컬 파일시스템에서 실행한다.
if sys.platform != "linux":
    raise SystemExit("중단: 이 실습은 Linux용이다.")
name = ctypes.util.find_library("acl")
if not name:
    raise SystemExit("중단: libacl이 없어 기본 ACL 실습을 실행할 수 없다.")
lib = ctypes.CDLL(name, use_errno=True)
ACCESS, DEFAULT = 0x8000, 0x4000  # Linux ACL API의 형식 상수

# 포인터가 잘리지 않도록 C 함수의 인수와 반환 형식을 명시한다.
signatures = {
    "acl_from_text": ([ctypes.c_char_p], ctypes.c_void_p),
    "acl_set_file": ([ctypes.c_char_p, ctypes.c_uint, ctypes.c_void_p], ctypes.c_int),
    "acl_get_file": ([ctypes.c_char_p, ctypes.c_uint], ctypes.c_void_p),
    "acl_to_text": ([ctypes.c_void_p, ctypes.POINTER(ctypes.c_ssize_t)], ctypes.c_void_p),
    "acl_delete_def_file": ([ctypes.c_char_p], ctypes.c_int),
    "acl_free": ([ctypes.c_void_p], ctypes.c_int),
}
for key, (args, result) in signatures.items():
    fn = getattr(lib, key)
    fn.argtypes, fn.restype = args, result


def acl_error(label):
    code = ctypes.get_errno()
    raise OSError(code, f"{label}: {os.strerror(code)}")


def set_default(path, text):
    acl = lib.acl_from_text(text.encode("ascii"))
    if not acl:
        acl_error("ACL 문자열 해석 실패")
    try:
        if lib.acl_set_file(os.fsencode(path), DEFAULT, acl) != 0:
            acl_error("기본 ACL 설정 실패")
    finally:
        lib.acl_free(acl)


def read_acl(path, kind):
    acl = lib.acl_get_file(os.fsencode(path), kind)
    if not acl:
        acl_error("ACL 조회 실패")
    text = None
    try:
        length = ctypes.c_ssize_t()
        text = lib.acl_to_text(acl, ctypes.byref(length))
        if not text:
            acl_error("ACL 출력 변환 실패")
        return ctypes.string_at(text, length.value).decode("ascii").strip()
    finally:
        if text:
            lib.acl_free(text)
        lib.acl_free(acl)


def permission(path):
    # 파일 종류 비트와 특수 비트를 제외한 rwx 권한만 읽는다.
    return stat.S_IMODE(path.stat().st_mode) & 0o777


def check(label, actual, expected):
    if actual != expected:
        raise RuntimeError(f"실패: {label}, 실제={actual!r}, 예상={expected!r}")


def create_file(path, requested):
    # 이름이 이미 있으면 실패하여 기존 파일을 덮어쓰지 않는다.
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, requested)
    os.close(fd)


# 독립된 단일 스레드 실습 프로세스 안에서만 umask를 바꾼다.
original_umask = os.umask(0o077)
try:
    # 현재 작업 경로 아래에 무작위 이름의 임시 폴더를 만든다.
    with tempfile.TemporaryDirectory(prefix="neoflux-umask-", dir=".") as folder:
        root = Path(folder)
        os.chmod(root, 0o700)
        # 상위 임시 경로에서 상속됐을 수 있는 기본 ACL을 실습 폴더에서만 지운다.
        if lib.acl_delete_def_file(os.fsencode(root)) != 0:
            acl_error("실습 폴더 기본 ACL 초기화 실패")
        check("실습 폴더 권한", permission(root), 0o700)
        check("기본 ACL 없는 기준 환경", read_acl(root, DEFAULT), "")
        print("[준비 성공] 전용 임시 폴더 0700, 기준 환경의 기본 ACL 없음")

        # 요청 모드를 고정하고 umask만 바꾼다.
        for mask, expected_file, expected_dir in [
            (0o022, 0o644, 0o755),
            (0o027, 0o640, 0o750),
            (0o077, 0o600, 0o700),
        ]:
            os.umask(mask)
            file = root / f"file-{mask:03o}"
            directory = root / f"dir-{mask:03o}"
            create_file(file, 0o666)
            directory.mkdir(mode=0o777)
            check("일반 파일", permission(file), expected_file)
            check("디렉터리", permission(directory), expected_dir)
            print(f"[성공] umask {mask:04o}: 파일 요청 0666 → {permission(file):04o}, "
                  f"디렉터리 요청 0777 → {permission(directory):04o}")

        # 요청하지 않은 권한은 생기지 않으며, 계산은 산술 뺄셈이 아니다.
        for label, mask, requested, expected in [
            ("제한된 요청", 0o022, 0o600, 0o600),
            ("실행 비트만 차단", 0o111, 0o666, 0o666),
            ("실행 비트도 요청", 0o022, 0o777, 0o755),
        ]:
            os.umask(mask)
            file = root / label
            create_file(file, requested)
            check(label, permission(file), expected)
            print(f"[성공] {label}: 요청 {requested:04o}, umask {mask:04o} "
                  f"→ 파일 {permission(file):04o}")

        # 이미 존재하는 파일을 다시 열어도 생성 권한이 재계산되지 않는다.
        os.umask(0o077)
        old_file = root / "file-022"
        old_inode = old_file.stat().st_ino
        fd = os.open(old_file, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        os.close(fd)
        check("동일한 기존 파일", old_file.stat().st_ino, old_inode)
        check("기존 파일 권한 유지", permission(old_file), 0o644)
        check("기존 디렉터리 권한 유지", permission(root / "dir-022"), 0o755)
        print("[성공] umask 0077로 변경 후 기존 파일 재열기: 파일 0644, 디렉터리 0755 유지")
        os.chmod(old_file, 0o640)
        check("명시적 chmod", permission(old_file), 0o640)
        print("[성공] 같은 umask에서 chmod 0640 실행: 파일 0640")

        # 자식 프로세스는 부모의 umask를 상속한다. 조회 중 값을 바꾸지 않는다.
        os.umask(0o027)
        child = subprocess.check_output(
            [sys.executable, "-c",
             "from pathlib import Path; "
             "print(next(x.split()[1] for x in "
             "Path('/proc/self/status').read_text().splitlines() "
             "if x.startswith('Umask:')))"],
            text=True,
        ).strip()
        check("자식 프로세스 상속", child, "0027")
        print(f"[성공] 자식 프로세스에서 읽은 umask: {child}")

        # 기본 ACL은 이 실습 전용 하위 폴더에만 설정한다.
        acl_dir = root / "with-acl"
        acl_dir.mkdir(mode=0o700)
        set_default(acl_dir, "u::rwx,g::r-x,o::---")
        default_text = read_acl(acl_dir, DEFAULT)
        check("설정한 기본 ACL", default_text,
              "user::rwx\ngroup::r-x\nother::---")
        print("[설정 확인] 기본 ACL: " + default_text.replace("\n", ", "))
        os.umask(0o077)
        acl_file = acl_dir / "file"
        acl_child_dir = acl_dir / "directory"
        private_file = acl_dir / "private"
        create_file(acl_file, 0o666)
        acl_child_dir.mkdir(mode=0o777)
        create_file(private_file, 0o600)
        check("기본 ACL 아래 파일", permission(acl_file), 0o640)
        check("기본 ACL 아래 디렉터리", permission(acl_child_dir), 0o750)
        check("기본 ACL 아래 제한된 요청", permission(private_file), 0o600)
        check("파일 접근 ACL", read_acl(acl_file, ACCESS),
              "user::rw-\ngroup::r--\nother::---")
        print("[성공] 기본 ACL + umask 0077: 파일 요청 0666 → 0640, 디렉터리 요청 0777 → 0750")
        print("[성공] 기본 ACL + umask 0077: 파일 요청 0600 → 0600")
        print("[ACL 확인] 생성 파일: " + read_acl(acl_file, ACCESS).replace("\n", ", "))
    check("임시 폴더 정리", root.exists(), False)
    print("[정리 성공] 실습 임시 폴더와 생성 파일 삭제")
finally:
    os.umask(original_umask)
PY
```
`Operation not supported`가 나오면 해당 경로에서 ACL 조건을 재현하지 못한 것이다. ACL을 지원하는 실습 경로로 옮겨 실행한다. 오류나 예상값 불일치가 나오면 결과를 성공으로 취급하지 않는다.

## 실행 결과 확인하기

파일과 디렉터리를 실제로 만들고 권한과 ACL을 다시 읽어 예상값과 비교했다. 파일 요청 모드 `0666`, 디렉터리 요청 모드 `0777`의 결과는 다음과 같다.

| 부모 디렉터리의 기본 ACL | umask | 파일 권한 | 디렉터리 권한 |
| --- | --- | --- | --- |
| 없음 | 0022 | 0644 | 0755 |
| 없음 | 0027 | 0640 | 0750 |
| 없음 | 0077 | 0600 | 0700 |
| 소유자 rwx / 그룹 r-x / 기타 --- | 0077 | 0640 | 0750 |

요청 모드를 바꾸거나 기존 파일을 다시 여는 경우도 확인했다. 아래는 출력의 일부다.

```text
[성공] 제한된 요청: 요청 0600, umask 0022 → 파일 0600
[성공] 실행 비트만 차단: 요청 0666, umask 0111 → 파일 0666
[성공] 실행 비트도 요청: 요청 0777, umask 0022 → 파일 0755
[성공] umask 0077로 변경 후 기존 파일 재열기: 파일 0644, 디렉터리 0755 유지
[성공] 같은 umask에서 chmod 0640 실행: 파일 0640
[성공] 자식 프로세스에서 읽은 umask: 0027
[성공] 기본 ACL + umask 0077: 파일 요청 0600 → 0600
[정리 성공] 실습 임시 폴더와 생성 파일 삭제
```
umask는 요청하지 않은 권한을 추가하지 않는다. 실행 비트가 설정됐더라도 파일 형식이나 마운트 조건까지 충족해 실제로 실행할 수 있다는 뜻은 아니다.

## 기존 파일의 권한은 그대로 남는다

umask를 `077`로 바꾼 뒤 기존 파일을 `0600` 모드로 다시 열어도 원래 권한인 `0644`가 유지됐다. 코드에서는 inode도 비교해 같은 파일임을 확인했다. 기존 디렉터리의 `0755` 권한 역시 바뀌지 않았다.

반면 명시적으로 `chmod 0640`을 적용하면 기존 파일의 권한이 바뀐다. umask는 생성 시 적용되는 마스크이며 이후의 권한 변경까지 계속 제한하지 않는다. 기존 파일의 권한을 정리할 때는 필요한 공유 범위와 서비스 동작을 따로 확인한다.

## 기본 ACL이 있으면 결과가 달라진다

접근 ACL은 해당 파일이나 디렉터리의 접근 권한을 정한다. 디렉터리의 기본 ACL은 새로 생성되는 객체가 물려받을 접근 ACL을 정한다. 기본 ACL이 있으면 생성 시 umask 대신 상속 ACL과 프로그램의 요청 모드로 권한이 결정된다.

실습의 기본 ACL은 소유자 `rwx`, 그룹 `r-x`, 기타 사용자 `---`이다. 파일을 `0666`으로 요청하면 실행 비트가 제외돼 `0640`, 디렉터리를 `0777`로 요청하면 `0750`이 된다. umask가 `077`이어도 기본 ACL이 없는 경우의 `0600`·`0700`과 다르다. 같은 ACL 아래에서 파일을 `0600`으로 요청하면 결과도 `0600`이다.

특정 사용자나 그룹을 추가한 확장 ACL에서는 ACL mask 항목도 확인한다. mask가 있으면 일반 모드의 그룹 비트는 소유 그룹 항목이 아니라 mask에 대응한다. 모드 숫자만으로 각 사용자의 실제 권한을 설명할 수는 없다.

이번 실습은 권한 비트와 ACL을 확인한 것이며 다른 계정으로 접근을 시도한 시험은 아니다. 최상위 실습 폴더가 `0700`이므로 내부 파일에 그룹 읽기 권한이 있어도 다른 일반 계정은 그 폴더를 경유할 수 없다. 실제 접근 가능 여부는 상위 경로의 탐색 권한, 소유자·그룹, 추가 접근 통제까지 확인한다.

## 운영 점검은 생성 주체부터 확인한다

umask는 프로세스의 속성이며 자식 프로세스에 상속된다. 로그인한 셸의 값만으로 이미 실행 중인 서비스의 값을 판단해서는 안 된다. 조회 권한이 있다면 대상 프로세스의 `/proc/<PID>/status`에서 `Umask` 항목을 확인한다.

점검 순서는 생성 주체, 프로그램의 요청 모드, 부모 디렉터리의 기본 ACL, 생성 직후 권한이다. 생성 후 `chmod`를 하거나 다른 파일로 교체하는 처리도 함께 살펴본다. 배포나 실행 방식이 바뀌면 같은 경로에서 같은 작업이 만든 파일을 다시 확인한다.

점검 기록에는 조건과 결과를 함께 남긴다. 예를 들어 “기본 ACL이 없는 실습 경로에서 요청 모드 0666·0777에 umask 027을 적용해 파일 0640, 디렉터리 0750 생성을 확인했다. 기존 객체의 권한은 변경되지 않았다”처럼 적는다. 기본 ACL이 있는 경우는 별도 결과로 기록한다.

## 참고 자료

- [Linux man-pages, umask(2)](https://man7.org/linux/man-pages/man2/umask.2.html)
- [Linux man-pages, open(2)](https://man7.org/linux/man-pages/man2/open.2.html)
- [Linux man-pages, mkdir(2)](https://man7.org/linux/man-pages/man2/mkdir.2.html)
- [Linux man-pages, chmod(2)](https://man7.org/linux/man-pages/man2/chmod.2.html)
- [Linux ACL, acl(5)](https://man7.org/linux/man-pages/man5/acl.5.html)
- [Linux ACL, acl_set_file(3)](https://man7.org/linux/man-pages/man3/acl_set_file.3.html)
- [Linux ACL, acl_delete_def_file(3)](https://man7.org/linux/man-pages/man3/acl_delete_def_file.3.html)
- [Python, os](https://docs.python.org/3/library/os.html)
- [Python, tempfile](https://docs.python.org/3/library/tempfile.html)
- [Python, ctypes](https://docs.python.org/3/library/ctypes.html)
