ALGORITHMS = {"1": "MD5-crypt", "5": "SHA256-crypt", "6": "SHA512-crypt"}


def classify(field):
    locked = field.startswith("!")
    value = field.lstrip("!")
    if not field:
        return locked, "빈 필드"
    if not value or value == "*":
        return locked, "사용할 해시 없음"
    parts = value.split("$")
    if value.startswith("$") and len(parts) >= 4:
        return locked, ALGORITHMS.get(parts[1], "대상별 해석 필요")
    return locked, "대상별 해석 필요"


samples = {
    "old": "$1$salt$DEMO",
    "locked_old": "!$1$salt$DEMO",
    "new": "$6$salt$DEMO",
    "sha256": "$5$salt$DEMO",
    "platform": "{OTHER}DEMO",
    "empty": "",
    "disabled": "*",
}
before = samples.copy()
new_password_policy = "SHA512"
assert classify(samples["locked_old"]) == (True, "MD5-crypt")
assert classify(samples["new"]) == (False, "SHA512-crypt")
assert classify(samples["platform"])[1] == "대상별 해석 필요"
assert classify(samples["empty"])[1] == "빈 필드"
assert classify("!!") == (True, "사용할 해시 없음")
assert samples == before

print(f"새 비밀번호 정책(가정): {new_password_policy}")
for name, field in samples.items():
    locked, algorithm = classify(field)
    lock_text = "있음" if locked else "없음"
    print(f"{name}: 잠금 접두부={lock_text}, 형식={algorithm}")
print("정책 변수 지정 후 기존 필드: 변경 없음")
