from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote
import os


def raw_prefix(base, name):
    # 잘못된 예: 경로를 해석하기 전에 문자열 앞부분만 비교한다.
    candidate = base / name
    if not str(candidate).startswith(str(base)):
        raise ValueError("범위 밖 경로")
    return candidate.read_text(encoding="utf-8")


def resolved_prefix(base, name):
    # 잘못된 예: 실제 경로를 구해도 디렉터리 경계를 구분하지 않는다.
    candidate = (base / name).resolve(strict=True)
    if not str(candidate).startswith(str(base)):
        raise ValueError("범위 밖 경로")
    return candidate.read_text(encoding="utf-8")


def contained_read(base, name):
    # 이미 디코딩된 상대 경로를 받는다. 파일 트리가 고정된 실습용이다.
    if not name or "\x00" in name:
        raise ValueError("빈 경로 또는 널 문자")
    requested = Path(name)
    if requested.is_absolute():
        raise ValueError("절대 경로 금지")

    root = base.resolve(strict=True)
    candidate = (root / requested).resolve(strict=True)
    if not candidate.is_relative_to(root):
        raise ValueError("범위 밖 경로")
    if not candidate.is_file():
        raise ValueError("일반 파일 아님")

    # 검사와 읽기 사이의 파일 교체는 막지 못한다.
    return candidate.read_text(encoding="utf-8")


def outcome(reader, base, name):
    try:
        return reader(base, name)
    except (OSError, ValueError, RuntimeError):
        return "거부"


def main():
    if os.name != "posix":
        raise SystemExit("Linux 등 POSIX 환경에서 실행한다.")

    with TemporaryDirectory(prefix="path-lab-") as temporary:
        work = Path(temporary).resolve()
        base = work / "files"
        sibling = work / "files_backup"
        base.mkdir()
        sibling.mkdir()
        (base / "report.txt").write_text("공개", encoding="utf-8")
        (work / "secret.txt").write_text("외부", encoding="utf-8")
        (sibling / "secret.txt").write_text("외부", encoding="utf-8")
        (base / "sub").mkdir()
        (base / "outside-link").symlink_to(work / "secret.txt")
        (base / "inside-link").symlink_to(base / "report.txt")

        # 외부 파일도 모두 이 실습이 만든 임시 디렉터리에 있다.
        cases = [
            ("정상 파일", "report.txt", ("공개", "공개", "공개")),
            ("상위 이동", "../secret.txt", ("외부", "거부", "거부")),
            (
                "비슷한 폴더명",
                "../files_backup/secret.txt",
                ("외부", "외부", "거부"),
            ),
            (
                "절대 외부 경로",
                str(work / "secret.txt"),
                ("거부", "거부", "거부"),
            ),
            (
                "절대 내부 경로",
                str(base / "report.txt"),
                ("공개", "공개", "거부"),
            ),
            ("외부 심볼릭 링크", "outside-link", ("외부", "거부", "거부")),
            ("내부 심볼릭 링크", "inside-link", ("공개", "공개", "공개")),
            ("없는 파일", "missing.txt", ("거부", "거부", "거부")),
            ("디렉터리", "sub", ("거부", "거부", "거부")),
            (
                "내부로 돌아오는 경로",
                "sub/../report.txt",
                ("공개", "공개", "공개"),
            ),
        ]
        readers = (raw_prefix, resolved_prefix, contained_read)
        print("입력 | 원문 접두사 | 해석 후 접두사 | 경로 포함 검사")

        for label, name, expected in cases:
            observed = tuple(outcome(reader, base, name) for reader in readers)
            if observed != expected:
                raise AssertionError(f"{label}: 예상 {expected}, 실제 {observed}")
            print(label + " | " + " | ".join(observed))

        # 디코딩 횟수는 HTTP 프레임워크가 아닌 이 실습에서 명시한다.
        encoded = "%252e%252e%252fsecret.txt"
        once = unquote(encoded)
        twice = unquote(once)
        if (once, twice) != ("%2e%2e%2fsecret.txt", "../secret.txt"):
            raise AssertionError("디코딩 결과 불일치")
        if outcome(contained_read, base, twice) != "거부":
            raise AssertionError("디코딩 후 외부 경로가 허용됨")

        print(f"1회 디코딩: {once}")
        print(f"2회 디코딩: {twice}")
        print("성공: 경로 비교 30건, 디코딩 결과와 차단 확인 2건")


if __name__ == "__main__":
    main()
