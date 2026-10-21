STATES = {None, "New", "Active", "Fixed", "Re-Opened"}


def next_state(previous, tested, detected):
    if previous not in STATES:
        raise ValueError("알 수 없는 이전 상태")
    if type(tested) is not bool:
        raise ValueError("평가 여부는 bool이어야 함")
    if not tested:
        if detected is not None:
            raise ValueError("미평가 회차에 탐지 결과를 넣을 수 없음")
        return previous
    if type(detected) is not bool:
        raise ValueError("평가한 회차에는 탐지 여부가 필요함")
    if detected:
        if previous is None:
            return "New"
        return "Re-Opened" if previous == "Fixed" else "Active"
    return "Fixed" if previous is not None else None


observations = [
    ("1차", True, True),
    ("2차", True, True),
    ("3차", False, None),
    ("4차", True, False),
    ("5차", True, True),
    ("6차", True, True),
]
assert next_state(None, True, True) == "New"
assert next_state("Active", False, None) == "Active"
assert next_state("Active", True, False) == "Fixed"
assert next_state("Fixed", True, True) == "Re-Opened"
assert next_state("Re-Opened", True, True) == "Active"
assert next_state(None, True, False) is None
try:
    next_state("Active", False, False)
except ValueError:
    pass
else:
    raise AssertionError("모순된 입력을 거부해야 함")

state = None
for label, tested, detected in observations:
    state = next_state(state, tested, detected)
    observation = "탐지" if detected is True else "미탐지" if tested else "평가 자료 없음"
    suffix = " (마지막 상태 보존)" if not tested else ""
    print(f"{label}: {observation} -> {state}{suffix}")
