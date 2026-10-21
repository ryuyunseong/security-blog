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
