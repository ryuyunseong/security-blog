import argparse
import json
import re
import sys
from pathlib import Path


FIELDS = {"case", "serviceUse", "accountUid", "ownerUid", "mode", "text"}


def load_rows(path):
    raw = path.read_text(encoding="utf-8")
    rows = json.loads(raw)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("행 수")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("필드")
        name = row["case"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]{1,40}", name) or name in seen:
            raise ValueError("사례 이름")
        seen.add(name)
        if row["serviceUse"] not in ("used", "unused", "unknown"):
            raise ValueError("서비스 상태")
        for key in ("accountUid", "ownerUid"):
            value = row[key]
            if key == "ownerUid" and value is None:
                continue
            if type(value) is not int or not 0 <= value <= 4294967294:
                raise ValueError("UID")
        mode = row["mode"]
        if mode is not None and (not isinstance(mode, str) or not re.fullmatch(r"[0-7]{4}", mode)):
            raise ValueError("모드")
        content = row["text"]
        if content is not None and (not isinstance(content, str) or len(content) > 8192):
            raise ValueError("설정 문자열")
    return rows


def content_notes(content):
    deviations, pending = [], []
    for number, line in enumerate(content.splitlines(), 1):
        tokens = line.split()
        if not tokens:
            continue
        if len(tokens) not in (1, 2):
            pending.append(f"{number}행 필드 수")
        for column, token in enumerate(tokens, 1):
            if token == "+":
                deviations.append(f"{number}행 {column}열 단독 +")
            elif token.startswith("+"):
                deviations.append(f"{number}행 {column}열 + 접두 표기")
            elif not re.fullmatch(r"[A-Za-z0-9_.-]+", token) or token.startswith("-"):
                pending.append(f"{number}행 {column}열 추가 구문")
    return deviations, pending


def compare(row):
    if row["serviceUse"] == "unused":
        return "미사용 가정", "파일 조건 비교 생략"
    if row["serviceUse"] == "unknown":
        return "추가 조사", "서비스 사용 여부 미수집"
    deviations, pending = [], []
    owner = row["ownerUid"]
    if owner is None:
        pending.append("소유 UID 미수집")
    elif owner not in (0, row["accountUid"]):
        deviations.append(f"소유 UID {owner} 불일치")
    if row["mode"] is None:
        pending.append("모드 미수집")
    else:
        mode = int(row["mode"], 8)
        extra = mode & (0o777 & ~0o600)
        if extra:
            deviations.append(f"600 밖 비트 {extra:03o}")
        if mode & 0o7000:
            pending.append("특수 비트 별도 조사")
    if row["text"] is None:
        pending.append("설정 문자열 미수집")
    else:
        found, unresolved = content_notes(row["text"])
        deviations.extend(found)
        pending.extend(unresolved)
    if deviations:
        return "기준 이탈 후보", ", ".join(deviations + pending)
    if pending:
        return "추가 조사", ", ".join(pending)
    return "기본 조건 일치", "소유 UID·일반 권한·제한된 문자열 비교 일치"


def main():
    parser = argparse.ArgumentParser(description="가상 r-command 수집 자료 비교")
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    try:
        rows = load_rows(args.inventory)
    except (OSError, UnicodeError, ValueError, TypeError):
        print("입력 오류: JSON 파일·필드·UID·8진수 모드를 살핀다", file=sys.stderr)
        return 2
    counts = dict.fromkeys(("미사용 가정", "기본 조건 일치", "기준 이탈 후보", "추가 조사"), 0)
    for row in rows:
        state, detail = compare(row)
        counts[state] += 1
        print(f"{row['case']}: {state}; {detail}")
    print(f"가상 자료 {len(rows)}건: " + ", ".join(f"{key} {value}건" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
