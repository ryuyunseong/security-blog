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
