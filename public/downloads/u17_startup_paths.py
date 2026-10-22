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
