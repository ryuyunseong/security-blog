import argparse
import json
import re
import sys
from pathlib import Path


def load_cases(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("비어 있지 않은 사례 목록이 필요하다")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("각 사례는 객체여야 한다")
        name = row.get("id")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]+", name):
            raise ValueError("사례 이름은 영문 소문자·숫자·하이픈만 받는다")
        if name in seen:
            raise ValueError("사례 이름이 중복됐다")
        seen.add(name)
        state = row.get("state")
        fields = {"id", "state"}
        if state == "present":
            fields |= {"kind", "uid", "mode", "required"}
            if row.get("kind") not in ("regular", "symlink"):
                raise ValueError("kind는 regular 또는 symlink여야 한다")
            if type(row.get("uid")) is not int or row["uid"] < 0:
                raise ValueError("uid는 0 이상의 정수여야 한다")
            if not isinstance(row.get("mode"), str) or not re.fullmatch(r"[0-7]{4}", row["mode"]):
                raise ValueError("mode는 네 자리 8진수 문자열이어야 한다")
            if row.get("required") is not None and type(row["required"]) is not bool:
                raise ValueError("required는 true·false·null만 받는다")
        elif state not in ("absent", "uncollected"):
            raise ValueError("state는 absent·uncollected·present만 받는다")
        if set(row) != fields:
            raise ValueError("상태에 필요한 필드만 정확히 지정한다")
    return rows


def compare(row):
    if row["state"] == "uncollected":
        return "보류: 부재로 바꾸지 않음"
    if row["state"] == "absent":
        return "부재 자료: 소유자·모드 비교 생략"
    if row["kind"] != "regular":
        return "보류: 링크와 대상 별도 조사"
    mode = int(row["mode"], 8)
    extra = mode & (0o777 & ~0o600)
    special = mode & 0o7000
    notes = []
    if row["required"] is None:
        notes.append("사용 필요성 미수집")
    elif row["required"] is False:
        notes.append("불필요한 파일의 제거 검토")
    if row["uid"] != 0:
        notes.append("root 소유 아님")
    if extra:
        notes.append(f"600 밖의 일반 권한={extra:03o}")
    if special:
        notes.append(f"특수 비트={special:04o}, 별도 조사")
    result = "; ".join(notes) if notes else "입력된 기본 조건 일치"
    return f"UID={row['uid']}, mode={mode:04o}: {result}"


def enumerate_modes():
    modes = range(0o1000)
    numeric = {m for m in modes if m <= 0o600}
    subset = {m for m in modes if m & (0o777 & ~0o600) == 0}
    print(f"일반 권한 0000~0777: {len(modes)}개")
    print(f"숫자 크기 0600 이하: {len(numeric)}개")
    print(f"600 밖의 일반 권한 없음: {len(subset)}개")
    print("비트 조건 목록: " + ", ".join(f"{m:04o}" for m in sorted(subset)))
    print(f"숫자 비교만 통과한 모드: {len(numeric - subset)}개")
    print(f"0477의 초과 비트: {0o477 & (0o777 & ~0o600):03o}")


def main():
    parser = argparse.ArgumentParser(description="가상 hosts.lpd 수집 자료 비교")
    parser.add_argument("task", choices=("cases", "modes"))
    parser.add_argument("fixture", nargs="?")
    args = parser.parse_args()
    try:
        if args.task == "modes":
            if args.fixture is not None:
                raise ValueError("modes에는 입력 파일을 주지 않는다")
            enumerate_modes()
        else:
            if args.fixture is None:
                raise ValueError("cases에는 JSON 파일 경로가 필요하다")
            rows = load_cases(args.fixture)
            for row in rows:
                print(f"{row['id']}: {compare(row)}")
            print(f"가상 자료 {len(rows)}건 비교 완료")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"입력 오류: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
