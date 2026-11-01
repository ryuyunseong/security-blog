import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description="자신이 만든 가상 dev 자료만 비교한다")
    parser.add_argument("collector", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        print("이 준비기는 Linux의 /tmp에서 실행한다", file=sys.stderr)
        return 2
    try:
        collector = args.collector.resolve(strict=True)
        if not collector.is_file():
            raise ValueError("수집기 파일이 필요하다")
        with tempfile.TemporaryDirectory(prefix="u26-fixture-", dir="/tmp") as temporary:
            root = Path(temporary)
            (root / ".u26-fixture").write_text("synthetic-u26\n", encoding="utf-8")
            for name in ("shm", "mqueue"):
                (root / name).mkdir()
            for name in ("console", "notes.txt", "shm/cache.bin", "mqueue/notice"):
                (root / name).write_text("synthetic\n", encoding="utf-8")
            (root / "device-link").symlink_to("console")
            os.mkfifo(root / "pipe", 0o600)
            run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(collector), str(root)], capture_output=True, text=True, encoding="utf-8", timeout=10)
            if run.returncode != 0 or run.stderr:
                raise ValueError("수집기가 정상 종료하지 않았다")
            found = subprocess.run(["find", "-P", str(root), "-type", "f", "!", "-name", ".u26-fixture", "-printf", "%P\n"], capture_output=True, text=True, encoding="utf-8", timeout=10)
            names = sorted(found.stdout.splitlines())
            expected = ["console", "mqueue/notice", "notes.txt", "shm/cache.bin"]
            if found.returncode != 0 or found.stderr or names != expected:
                raise ValueError("GNU find의 일반 파일이 예상과 다르다")
            collected = [line.split(":", 1)[0] for line in run.stdout.splitlines() if ": file, " in line]
            if collected != names:
                raise ValueError("수집기와 GNU find의 일반 파일이 다르다")
            print(run.stdout, end="")
            print("GNU find 일반 파일: " + ", ".join(names))
        print("대조 완료: 일반 파일 4건 일치, 생성한 임시 폴더 정리")
    except (OSError, ValueError, subprocess.SubprocessError):
        print("준비 오류: 수집기 경로·Linux 임시 폴더·GNU find를 살핀다", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
