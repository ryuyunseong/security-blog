import argparse
import os
from pathlib import Path
import stat
import sys
import tempfile


EXPECTED_ROWS = [
    (".cache", "디렉터리", "이름 숨김"),
    (".cache/session.txt", "파일", "숨김 경로 내부"),
    (".profile", "파일", "이름 숨김"),
    ("docs/.draft.txt", "파일", "이름 숨김"),
]


def collect(root, unreadable=()):
    rows, issues = [], []

    def visit(folder, hidden_parent=False):
        relative = folder.relative_to(root).as_posix()
        if relative in unreadable:
            issues.append((relative, "가상 조회 오류"))
            return
        try:
            with os.scandir(folder) as stream:
                entries = sorted(stream, key=lambda entry: entry.name)
        except OSError:
            issues.append((relative, "디렉터리 조회 오류"))
            return
        for entry in entries:
            path = folder / entry.name
            name = path.relative_to(root).as_posix()
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                issues.append((name, "종류 조회 오류"))
                continue
            reparse = getattr(info, "st_file_attributes", 0) & getattr(
                stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
            )
            if stat.S_ISLNK(info.st_mode) or reparse:
                kind = "링크"
                issues.append((name, "링크 또는 재분석 지점 보류"))
            elif stat.S_ISDIR(info.st_mode):
                kind = "디렉터리"
            elif stat.S_ISREG(info.st_mode):
                kind = "파일"
            else:
                kind = "기타"
            named = entry.name.startswith(".")
            if named or hidden_parent:
                reason = "이름 숨김" if named else "숨김 경로 내부"
                rows.append((name, kind, reason))
            if kind == "디렉터리":
                visit(path, hidden_parent or named)

    visit(root)
    return rows, issues


def run_lab(scenarios):
    with tempfile.TemporaryDirectory(prefix="u33-hidden-") as tmp:
        root = Path(tmp)
        for name in [".cache", "docs"]:
            (root / name).mkdir()
        for name in [".profile", ".cache/session.txt", "docs/.draft.txt", "docs/readme.txt", "public.txt"]:
            (root / name).write_text("synthetic fixture\n", encoding="utf-8")
        for scenario in scenarios:
            if scenario == "uncollected":
                print("[uncollected] 검색 미실행")
                continue
            blocked = (".cache",) if scenario == "read-error" else ()
            rows, issues = collect(root, blocked)
            expected = EXPECTED_ROWS if not blocked else [row for row in EXPECTED_ROWS if row[0] != ".cache/session.txt"]
            expected_issues = [(".cache", "가상 조회 오류")] if blocked else []
            if rows != expected or issues != expected_issues:
                raise RuntimeError(f"{scenario}: 기대 결과 불일치")
            print(f"[{scenario}] 조사 후보 {len(rows)}건, 보류 {len(issues)}건")
            for row in rows:
                print(" | ".join(row))
            for name, reason in issues:
                print(f"보류: {name} ({reason})")
            print("검색 상태: " + ("일부 범위 보류" if issues else "지정한 가상 범위 순회 완료"))
    if root.exists():
        raise RuntimeError("임시 자료가 남아 있음")
    print(f"기대 결과 {len(scenarios)}개 시나리오 일치")
    print("임시 자료 정리 완료")


def main():
    parser = argparse.ArgumentParser(description="자체 임시 폴더의 점 이름 검색 실습")
    parser.add_argument("--scenario", choices=["all", "complete", "read-error", "uncollected"], default="all")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        print("실행 오류: Python 3.12 이상이 필요합니다.", file=sys.stderr)
        return 2
    scenarios = ["complete", "read-error", "uncollected"] if args.scenario == "all" else [args.scenario]
    try:
        run_lab(scenarios)
    except OSError:
        print("실행 오류: 임시 자료 준비·정리를 살펴보세요.", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"실습 검증 실패: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
