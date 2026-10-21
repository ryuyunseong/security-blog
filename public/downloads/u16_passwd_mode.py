ALLOWED = 0o644
CASES = (
    ("기준 설정", 0, 0o644),
    ("그룹 쓰기 추가", 0, 0o664),
    ("소유자 다름", 1001, 0o644),
    ("숫자 비교 함정", 0, 0o606),
    ("소유자만 읽기·쓰기", 0, 0o600),
)


def inspect(uid, mode):
    # 가상 자료의 일반 권한 9비트만 비교한다.
    if not isinstance(uid, int) or isinstance(uid, bool) or uid < 0:
        raise ValueError("UID는 0 이상의 정수여야 한다")
    if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o777:
        raise ValueError("이 예제는 일반 권한 0000~0777만 받는다")
    extra = mode & (~ALLOWED & 0o777)
    return uid == 0 and extra == 0, extra


expected = (True, False, False, False, True)
for (label, uid, mode), allowed in zip(CASES, expected):
    matches, extra = inspect(uid, mode)
    assert matches == allowed
    state = "충족" if matches else "불일치"
    print(f"{label}: UID={uid}, 모드={mode:04o}, 허용 밖 비트={extra:03o}, 기준 {state}")

assert 0o606 <= 0o644
assert inspect(0, 0o606) == (False, 0o002)
assert inspect(0, 0o640) == (True, 0)
assert inspect(0, 0o644) == (True, 0)
assert inspect(1, 0o600) == (False, 0)
try:
    inspect(0, 0o4644)
except ValueError:
    print("특수 비트가 있는 모드: 일반 권한 예제 범위 밖")
else:
    raise AssertionError("범위 밖 모드를 거부하지 않음")
print(f"0606 <= 0644 숫자 비교: {0o606 <= 0o644}")
print("0606에서 추가된 기타 쓰기 비트: 002")
