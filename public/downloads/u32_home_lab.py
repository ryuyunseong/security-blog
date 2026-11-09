import argparse
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile


CASES = (
    ("existing", "/home/alpha", "collected", "디렉터리 존재"),
    ("outside-home", "/srv/worker", "collected", "디렉터리 존재"),
    ("missing", "/home/absent", "collected", "부재 후보"),
    ("ordinary-file", "/home/not-dir", "collected", "종류 확인"),
    ("empty", "", "collected", "보류"),
    ("root-home", "/", "collected", "보류"),
    ("uncollected", "/home/unsampled", "uncollected", "보류"),
    ("query-error", "/home/denied", "read_error", "보류"),
    ("relative", "home/alpha", "collected", "보류"),
    ("parent-part", "/home/../escape", "collected", "보류"),
)


def probe_home(root, home, source_state):
    if source_state == "uncollected":
        return "보류", "가상 미수집 상태: 경로 조회 안 함"
    if source_state == "read_error":
        return "보류", "가상 조회 오류 상태: 경로 조회 안 함"
    if source_state != "collected":
        raise ValueError("알 수 없는 수집 상태")
    if not home:
        return "보류", "홈 필드가 비어 있음"
    if home == "/":
        return "보류", "루트 경로: 계정 목적 별도 조사"
    if ".." in home.split("/"):
        return "보류", "상위 경로 성분 거부"
    if not re.fullmatch(r"/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", home):
        return "보류", "실습에서 허용하지 않는 경로 표기"

    candidate = root
    for part in PurePosixPath(home).parts[1:]:
        candidate = candidate / part
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            return "부재 후보", "임시 경로의 성분이 없음"
        except OSError:
            return "보류", "실제 임시 경로 조회 오류"
        reparse = getattr(info, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
        )
        if stat.S_ISLNK(info.st_mode) or reparse:
            return "보류", "링크 또는 재분석 지점: 따라가지 않음"
        if not stat.S_ISDIR(info.st_mode):
            return "종류 확인", "임시 경로의 성분이 디렉터리가 아님"
    return "디렉터리 존재", "임시 경로의 모든 성분이 디렉터리"


def run_lab(selected):
    with tempfile.TemporaryDirectory(prefix="u32-home-") as tmp:
        root = Path(tmp)
        (root / "home" / "alpha").mkdir(parents=True)
        (root / "srv" / "worker").mkdir(parents=True)
        (root / "home" / "not-dir").write_text("fixture\n", encoding="utf-8")
        for case_id, home, state, expected in selected:
            status, reason = probe_home(root, home, state)
            if status != expected:
                raise RuntimeError(f"{case_id}: 기대 상태 불일치")
            print(f"{case_id}: {status} ({reason})")
    if root.exists():
        raise RuntimeError("임시 자료가 남아 있음")
    print(f"기대 상태 {len(selected)}건 일치")
    print("임시 자료 정리 완료")


def main():
    parser = argparse.ArgumentParser(description="가상 홈 경로의 임시 파일 실습")
    parser.add_argument("--case", choices=["all"] + [row[0] for row in CASES], default="all")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        print("실행 오류: Python 3.12 이상이 필요합니다.", file=sys.stderr)
        return 2
    selected = [row for row in CASES if args.case in ("all", row[0])]
    try:
        run_lab(selected)
    except (OSError, ValueError):
        print("실행 오류: 임시 자료 준비·조회·정리를 살펴보세요.", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"실습 검증 실패: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
