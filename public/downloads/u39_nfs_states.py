import json
import re
import sys
from pathlib import Path

COLLECTIONS = {"collected", "absent", "query-error", "uncollected"}
USAGES = {"unused", "required", "unknown"}
ACTIVE_STATES = {"active", "inactive", "failed"}
FILE_STATES = {"enabled", "disabled", "static", "masked"}
KEYS = {"id", "unit", "usage", "collection", "ActiveState", "UnitFileState"}


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
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("사례 목록은 1~30건이어야 해요")
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
        if row["unit"] != "nfs-server.service":
            raise ValueError("실습 대상은 가상 nfs-server.service 하나예요")
        for field, allowed in [("usage", USAGES), ("collection", COLLECTIONS)]:
            if not isinstance(row[field], str) or row[field] not in allowed:
                raise ValueError(f"{field} 지원 값이 아니에요")
        if row["collection"] == "collected":
            for field, allowed in [("ActiveState", ACTIVE_STATES), ("UnitFileState", FILE_STATES)]:
                if not isinstance(row[field], str) or row[field] not in allowed:
                    raise ValueError(f"{field} 지원 값이 아니에요")
        elif row["ActiveState"] is not None or row["UnitFileState"] is not None:
            raise ValueError("미수집 상태의 두 속성은 null이어야 해요")
    return rows


def assess(row):
    if row["collection"] != "collected":
        return "보류", f"수집 상태 {row['collection']}"
    if row["usage"] == "unknown":
        return "보류", "사용 필요성 자료 없음"
    if row["usage"] == "required":
        return "보류", "필요 서비스의 접근 통제 검토"
    active, file_state = row["ActiveState"], row["UnitFileState"]
    if active == "active":
        return "검토 후보", f"현재 active; 기동 설정 {file_state}"
    if active != "inactive":
        return "보류", f"현재 상태 {active}의 원인 조사"
    if file_state == "enabled":
        return "검토 후보", "현재 inactive; 기동 설정 enabled"
    if file_state != "disabled":
        return "보류", f"기동 설정 {file_state}의 방식 조사"
    return "두 값 일치", "현재 inactive; 기동 설정 disabled"


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 JSON 파일 하나를 지정해 주세요")
        rows = load_rows(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("가상 상태 대조 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    counts = {"검토 후보": 0, "두 값 일치": 0, "보류": 0}
    for row in rows:
        status, reason = assess(row)
        counts[status] += 1
        print(f"{row['id']}: {status} | {reason}")
    print("사례 합계: " + ", ".join(f"{key} {value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
