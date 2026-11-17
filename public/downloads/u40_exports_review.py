import json
import re
import sys
from pathlib import Path

COLLECTIONS = {"collected", "absent", "query-error", "uncollected"}
KEYS = {"id", "collection", "ownerUid", "mode", "line"}
ENTRY = re.compile(
    r"/home/example[ \t]+(?P<client>host1|host2|\*)"
    r"\((?P<access>ro|rw),root_squash\)"
)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키가 중복됐어요")
        result[key] = value
    return result


def load_rows(path):
    with path.open("rb") as source:
        raw = source.read(24001)
    if len(raw) > 24000:
        raise ValueError("입력은 24000바이트 이하여야 해요")
    rows = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 20:
        raise ValueError("사례 목록은 1~20건이어야 해요")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != KEYS:
            raise ValueError("입력 행의 키가 맞지 않아요")
        case_id = row["id"]
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9-]{1,32}", case_id):
            raise ValueError("id 형식이 잘못됐어요")
        if case_id in ids:
            raise ValueError("id가 중복됐어요")
        ids.add(case_id)
        state = row["collection"]
        if not isinstance(state, str) or state not in COLLECTIONS:
            raise ValueError("collection 지원 값이 아니에요")
        if state == "collected":
            uid = row["ownerUid"]
            if type(uid) is not int or not 0 <= uid <= 4294967295:
                raise ValueError("ownerUid는 범위 안의 정수여야 해요")
            if not isinstance(row["mode"], str) or not re.fullmatch(r"0[0-7]{3}", row["mode"]):
                raise ValueError("mode는 0과 8진수 세 자리 문자열이어야 해요")
            if not isinstance(row["line"], str) or len(row["line"]) > 256 or "\n" in row["line"] or "\r" in row["line"]:
                raise ValueError("line은 256자 이하의 한 줄 문자열이어야 해요")
        elif any(row[key] is not None for key in ("ownerUid", "mode", "line")):
            raise ValueError("미수집 상태의 소유자·모드·행은 null이어야 해요")
    return rows


def assess(row):
    if row["collection"] != "collected":
        return "해석 보류", "수집 상태 " + row["collection"]
    findings = []
    if row["ownerUid"] != 0:
        findings.append("설정 소유자 UID=" + str(row["ownerUid"]))
    extra = int(row["mode"], 8) & ~0o644
    if extra:
        findings.append(f"644 밖 권한 비트={extra:04o}")
    match = ENTRY.fullmatch(row["line"])
    if match is None:
        detail = "; ".join(["호스트·괄호 결합 또는 지원 문법 조사"] + findings)
        return "해석 보류", detail
    client, access = match.group("client", "access")
    if client == "*":
        findings.append("전체 클라이언트 표기")
    if findings:
        return "검토 후보", "; ".join(findings)
    return "제한 표기", f"대상={client}; 요청={access}; 설정 UID=0; mode={row['mode']}"


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 JSON 파일 하나를 지정해 주세요")
        rows = load_rows(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("가상 exports 대조 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for row in rows:
        status, detail = assess(row)
        print(f"{row['id']}: {status} | {detail}")
    print(f"대조한 가상 항목: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
