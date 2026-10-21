import argparse
import gzip
import sys
import zlib
from pathlib import Path

INPUT_LIMIT = 1024 * 1024
OUTPUT_LIMIT = 64 * 1024
CHUNK = 8192


class PolicyError(Exception):
    pass


def inspect_gzip(data, limit=OUTPUT_LIMIT):
    """단일 gzip 멤버의 실제 출력량을 세며 검사한다. 파일은 쓰지 않는다."""
    if not 0 <= limit <= 1024 * 1024:
        raise ValueError("출력 한도는 0~1048576바이트여야 한다")
    if len(data) > INPUT_LIMIT:
        raise PolicyError("압축 입력 한도 초과")
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    total = 0
    position = 0
    pending = b""
    while True:
        if not pending and position < len(data):
            pending = data[position:position + CHUNK]
            position += len(pending)
        # 초과 여부를 확인할 1바이트를 더한다. 0은 무제한이므로 쓰지 않는다.
        piece = decoder.decompress(pending, min(CHUNK, limit - total + 1))
        total += len(piece)
        if total > limit:
            raise PolicyError("압축 해제 출력 한도 초과")
        pending = decoder.unconsumed_tail
        if decoder.eof:
            if decoder.unused_data or position < len(data):
                raise PolicyError("단일 멤버 뒤의 추가 데이터는 허용하지 않는다")
            return total
        # 내부에 남은 출력이 있을 수 있어 다음 회차의 빈 입력도 처리한다.
        if not pending and position == len(data) and not piece:
            raise ValueError("gzip 스트림이 끝나기 전에 입력이 끝났다")


def run_demo():
    normal = gzip.compress(b"A" * OUTPUT_LIMIT, mtime=0)
    large = gzip.compress(b"A" * (512 * 1024), mtime=0)
    print(f"큰 예제: 압축 {len(large)}바이트, 원문 524288바이트")
    cases = [
        ("한도와 같은 출력", normal, OUTPUT_LIMIT, None),
        ("한도보다 1바이트 큰 출력",
         gzip.compress(b"A" * (OUTPUT_LIMIT + 1), mtime=0),
         OUTPUT_LIMIT, PolicyError),
        ("작은 입력의 큰 출력", large, OUTPUT_LIMIT, PolicyError),
        ("빈 원문과 0 한도", gzip.compress(b"", mtime=0), 0, None),
        ("잘린 마지막 부분", normal[:-1], OUTPUT_LIMIT, ValueError),
        ("두 멤버 연결", normal + normal, OUTPUT_LIMIT, PolicyError),
        ("뒤에 붙은 문자열", normal + b"extra", OUTPUT_LIMIT, PolicyError),
        ("압축 입력 한도 초과",
         b"x" * (INPUT_LIMIT + 1), OUTPUT_LIMIT, PolicyError),
        ("gzip이 아닌 입력", b"not gzip", OUTPUT_LIMIT, zlib.error),
    ]
    for label, data, limit, expected in cases:
        try:
            size = inspect_gzip(data, limit)
        except (PolicyError, ValueError, zlib.error) as exc:
            if expected is None or type(exc) is not expected:
                raise AssertionError(f"예상과 다른 결과: {label}") from exc
            print(f"{label}: 성공, 예상한 거부 확인")
        else:
            if expected is not None:
                raise AssertionError(f"거부되지 않음: {label}")
            print(f"{label}: 성공, 출력 {size}바이트")


def main():
    parser = argparse.ArgumentParser(description="단일 gzip 멤버 출력 한도 검사")
    parser.add_argument("path", nargs="?", help="허가된 로컬 gzip 파일")
    parser.add_argument("--limit", type=int, default=OUTPUT_LIMIT)
    args = parser.parse_args()
    try:
        if args.path is None:
            run_demo()
        else:
            # 입력을 제한된 크기까지만 읽고 출력 내용은 보관하지 않는다.
            with Path(args.path).open("rb") as source:
                data = source.read(INPUT_LIMIT + 1)
            size = inspect_gzip(data, args.limit)
            print(f"검사 완료: 출력 {size}바이트, 설정한 정책 범위 내")
        return 0
    except PolicyError as exc:
        print(f"정책상 거부: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, zlib.error, AssertionError) as exc:
        print(f"실행 또는 데이터 오류: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
