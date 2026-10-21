import json
import re

RESTRICTED = {
    "/bin/false", "/usr/bin/false",
    "/sbin/nologin", "/usr/sbin/nologin",
}
NAME = re.compile(r"[a-z_][a-z0-9_-]{0,31}\$?")
SHELL = re.compile(r"/[A-Za-z0-9_./+-]+")


def inspect(text, targets):
    if not text.strip() or len(text.encode("utf-8")) > 4 * 1024 * 1024:
        raise ValueError("빈 자료 또는 입력 크기 초과")
    if not targets or any(not NAME.fullmatch(x) for x in targets):
        raise ValueError("조사 대상 계정 이름 확인 필요")
    accounts = {}
    for line in text.splitlines():
        if not line:
            continue
        fields = line.split(":")
        if len(fields) != 7 or not NAME.fullmatch(fields[0]):
            raise ValueError("계정 자료 형식 오류")
        name, _, uid, gid, _, _, shell = fields
        if name in accounts:
            raise ValueError("중복 계정 이름")
        for value in (uid, gid):
            if not re.fullmatch(r"[0-9]{1,10}", value) or int(value) > 4294967294:
                raise ValueError("UID 또는 GID 형식 오류")
        if shell and not SHELL.fullmatch(shell):
            raise ValueError("이 예제가 지원하지 않는 셸 경로")
        accounts[name] = shell
    if set(targets) - accounts.keys():
        raise ValueError("조사 대상 계정 누락")
    return [
        {"계정": name, "셸": accounts[name] or "(빈 값: 기본 셸 확인)",
         "검토 필요": accounts[name] not in RESTRICTED}
        for name in sorted(set(targets))
    ]


if __name__ == "__main__":
    fixture = (
        "root:x:0:0::/root:/bin/bash\n"
        "daemon:x:1:1::/usr/sbin:/usr/sbin/nologin\n"
        "svc_report:x:1500:1500::/srv/report:/bin/bash\n"
    )
    targets = {"daemon", "svc_report"}
    result = inspect(fixture, targets)
    assert [x["계정"] for x in result if x["검토 필요"]] == ["svc_report"]
    print(json.dumps(result, ensure_ascii=False, indent=2))

    restricted = fixture.replace("/srv/report:/bin/bash", "/srv/report:/bin/false")
    assert not any(x["검토 필요"] for x in inspect(restricted, targets))
    print("제한용 셸로 바꾼 가상 자료: 검토 후보 0개")

    empty_shell = fixture.replace("/srv/report:/bin/bash", "/srv/report:")
    assert any(x["검토 필요"] for x in inspect(empty_shell, targets))
    print("빈 셸: 검토 후보로 유지")

    error_cases = [
        ("필드 오류", "daemon:x:1:1", {"daemon"}),
        ("중복 이름", fixture + fixture.splitlines()[1] + "\n", targets),
        ("대상 누락", fixture, {"missing_service"}),
    ]
    for label, data, selected in error_cases:
        try:
            inspect(data, selected)
        except ValueError:
            print(f"{label}: 오류로 구분")
        else:
            raise AssertionError(f"{label} 검증 실패")
