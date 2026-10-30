import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description="자신이 만든 가상 파일의 쓰기 비트를 대조한다")
    parser.add_argument("collector", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        print("이 준비기는 Linux의 /tmp에서 실행한다", file=sys.stderr)
        return 2
    try:
        collector = args.collector.resolve(strict=True)
        if not collector.is_file():
            raise ValueError("수집기 파일이 필요하다")
        with tempfile.TemporaryDirectory(prefix="u25-fixture-", dir="/tmp") as temporary:
            root = Path(temporary)
            (root / ".u25-fixture").write_text("synthetic-u25\n", encoding="utf-8")
            for name, mode in (("group-only.txt", 0o664), ("open-note.txt", 0o666), ("other-only.txt", 0o602), ("private.txt", 0o600)):
                path = root / name
                path.write_text("synthetic\n", encoding="utf-8")
                path.chmod(mode)
            (root / "shared-dir").mkdir()
            (root / "shared-dir").chmod(0o777)
            (root / "shortcut").symlink_to("open-note.txt")
            run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(collector), str(root)], capture_output=True, text=True, encoding="utf-8", timeout=10)
            if run.returncode != 0 or run.stderr:
                raise ValueError("수집기가 정상 종료하지 않았다")
            found = subprocess.run(["find", "-P", str(root), "-type", "f", "-perm", "-2", "-printf", "%f\n"], capture_output=True, text=True, timeout=10)
            names = sorted(found.stdout.splitlines())
            if found.returncode != 0 or found.stderr or names != ["open-note.txt", "other-only.txt"]:
                raise ValueError("GNU find의 후보가 예상과 다르다")
            candidate_lines = [line.split(":", 1)[0] for line in run.stdout.splitlines() if line.endswith("일반 파일 후보=예")]
            if candidate_lines != names:
                raise ValueError("수집기와 GNU find의 후보가 다르다")
            print(run.stdout, end="")
            print("GNU find 후보: " + ", ".join(names))
        print("준비기 검증 완료: 후보 2건 일치, 생성한 임시 폴더 정리")
    except (OSError, ValueError, subprocess.SubprocessError):
        print("준비 오류: 수집기 경로·Linux 임시 폴더·GNU find를 살핀다", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
