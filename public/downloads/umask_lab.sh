#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import ctypes
import ctypes.util
import errno
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
    detail = os.strerror(code)
    if code in {errno.ENOTSUP, errno.EOPNOTSUPP}:
        detail += (
            ". 이 실습 경로에서 POSIX ACL 작업을 지원하지 않는다. "
            "findmnt로 경로의 파일시스템을 확인하고, ACL을 지원하는 "
            "경로를 UMASK_LAB_TMPDIR로 지정해 다시 실행한다."
        )
    raise OSError(code, f"{label}: {detail}")


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
lab_base = os.environ.get("UMASK_LAB_TMPDIR", "/tmp")
original_umask = os.umask(0o077)
try:
    # 현재 경로나 TMPDIR 대신 지정한 실습 경로 아래에만 폴더를 만든다.
    with tempfile.TemporaryDirectory(prefix="neoflux-umask-", dir=lab_base) as folder:
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
