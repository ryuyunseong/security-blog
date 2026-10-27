import argparse
from pathlib import Path
import re
import sys


def parse_table(text):
    entries = {}
    for number, raw in enumerate(text.splitlines(), 1):
        fields = raw.split("#", 1)[0].split()
        if not fields:
            continue
        if len(fields) < 2 or not re.fullmatch(r"[0-9]+/(tcp|udp)", fields[1]):
            raise ValueError(f"{number}행: 번호/프로토콜 형식이 필요하다")
        port_text, protocol = fields[1].split("/")
        port = int(port_text)
        if not 0 <= port <= 65535:
            raise ValueError(f"{number}행: 포트 번호 범위를 벗어났다")
        for name in [fields[0], *fields[2:]]:
            key = (name, protocol)
            if key in entries:
                raise ValueError(f"{number}행: 이름과 프로토콜이 중복됐다")
            entries[key] = port
    return entries


def main():
    parser = argparse.ArgumentParser(description="명시한 가상 서비스 이름표만 읽는다")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        entries = parse_table(args.file.read_text(encoding="utf-8"))
    except OSError:
        print("입력 파일을 읽을 수 없습니다", file=sys.stderr)
        return 2
    except (ValueError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2
    for key in [("domain", "tcp"), ("domain", "udp"), ("sample-alias", "tcp"), ("unknown", "tcp")]:
        port = entries.get(key)
        print(f"{key[0]}/{key[1]}: {port if port is not None else '등록 없음'}")
    print("이름표 조회 완료, 소켓 접속 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
