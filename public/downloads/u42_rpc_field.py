import json
import re
import sys
from pathlib import Path

SOURCES = {"excerpt", "missing-file", "read-error", "not-collected"}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 키가 중복됐어요")
        result[key] = value
    return result


def load_cases(path):
    with path.open("rb") as stream:
        raw = stream.read(12001)
    if len(raw) > 12000:
        raise ValueError("입력은 12000바이트까지 읽어요")
    cases = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys)
    if not isinstance(cases, list) or not 1 <= len(cases) <= 12:
        raise ValueError("사례 목록은 1~12건이어야 해요")
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "source", "lines"}:
            raise ValueError("각 사례에는 id, source, lines가 필요해요")
        name, source, lines = case["id"], case["source"], case["lines"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]{1,32}", name) or name in seen:
            raise ValueError("사례 ID의 형식이나 중복을 살펴보세요")
        seen.add(name)
        if not isinstance(source, str) or source not in SOURCES:
            raise ValueError("지원하지 않는 수집 상태예요")
        if source != "excerpt":
            if lines is not None:
                raise ValueError("발췌 자료가 없으면 lines는 null이어야 해요")
            continue
        if not isinstance(lines, list) or len(lines) > 8:
            raise ValueError("발췌는 여덟 줄 이하의 목록이어야 해요")
        for line in lines:
            if not isinstance(line, str) or len(line) > 120 or not line.isascii():
                raise ValueError("각 줄에는 120자 이하의 ASCII 문자열을 써 주세요")
            if any(char != "\t" and not char.isprintable() for char in line):
                raise ValueError("각 줄에 탭 이외의 제어 문자가 있어요")
    return cases


def read_setting(case):
    if case["source"] != "excerpt":
        return "자료 보류", case["source"]
    values = []
    for line in case["lines"]:
        field = line.strip()
        if not field or field.startswith("#"):
            continue
        match = re.fullmatch(r"disable\s*=\s*(yes|no)", field)
        if not match:
            return "해석 보류", "지원 범위 밖의 행"
        values.append(match[1])
    if len(values) != 1:
        return "해석 보류", f"명시값 {len(values)}개"
    return ("비활성 표기" if values[0] == "yes" else "활성 표기"), values[0]


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("가상 입력 파일 하나를 지정해 주세요")
        cases = load_cases(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print("발췌 대조 미실행")
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for case in cases:
        status, detail = read_setting(case)
        print(f"{case['id']}: {status} | {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
