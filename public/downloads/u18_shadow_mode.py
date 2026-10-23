CASES = (
    ("기준 권한", 0, 0o400, "조건 충족"),
    ("소유자 쓰기", 0, 0o600, "권한 초과"),
    ("그룹 읽기", 0, 0o440, "권한 초과"),
    ("기타 읽기", 0, 0o404, "권한 초과"),
    ("숫자가 작은 모드", 0, 0o004, "권한 초과"),
    ("일반 권한 없음", 0, 0o000, "조건 충족"),
    ("다른 소유자", 1001, 0o400, "소유자 불일치"),
    ("특수 비트", 0, 0o4400, "범위 밖"),
    ("소유자 미수집", None, 0o400, "미수집"),
)


def compare(uid, mode):
    # 실제 파일을 조회하지 않고 전달받은 가상 속성만 비교한다.
    if uid is None or mode is None:
        return "미수집", None
    if type(uid) is not int or uid < 0:
        raise ValueError("UID는 0 이상의 정수여야 한다")
    if type(mode) is not int or not 0 <= mode <= 0o7777:
        raise ValueError("모드 범위 오류")
    if mode & 0o7000:
        return "범위 밖", None
    extra = mode & (~0o400 & 0o777)
    if uid != 0:
        return "소유자 불일치", extra
    return ("권한 초과" if extra else "조건 충족"), extra


def main():
    for label, uid, mode, expected in CASES:
        state, extra = compare(uid, mode)
        if state != expected:
            raise AssertionError(f"{label}: {state!r} != {expected!r}")
        bits = "비교 안 함" if extra is None else f"{extra:03o}"
        print(f"{label}: UID={uid}, 모드={mode:04o}, 추가 비트={bits}, {state}")
    print(f"가상 속성 {len(CASES)}건의 기대 상태 일치")


if __name__ == "__main__":
    main()
