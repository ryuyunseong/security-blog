from pathlib import Path
import os
import subprocess
import sys
import tempfile


def main():
    if sys.platform != "linux" or len(sys.argv) != 2:
        raise SystemExit("Linux에서 python3 실습파일.py 수집기파일로 실행한다")
    collector = Path(sys.argv[1]).resolve(strict=True)
    if not collector.is_file():
        raise SystemExit("수집기는 읽을 수 있는 일반 파일이어야 한다")
    with tempfile.TemporaryDirectory(prefix="u06-fixture-", dir="/tmp") as directory:
        root = Path(directory)

        def write(relative, text):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return path

        def run(label, expected, markers, *arguments, environment=None):
            print(f"[사례] {label}", flush=True)
            result = subprocess.run(
                [sys.executable, str(collector), *arguments],
                env={**os.environ, **(environment or {})},
                capture_output=True, text=True, encoding="utf-8", timeout=15,
            )
            print(result.stdout, end="", flush=True)
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr, flush=True)
            print(f"수집기 종료 코드: {result.returncode}", flush=True)
            if result.returncode != expected or result.stderr or any(
                marker not in result.stdout for marker in markers
            ):
                raise RuntimeError("가상 자료의 출력 또는 종료 코드가 예상과 다름")
        write("etc/passwd", "root:x:0:0::/root:/bin/sh\n"
              "admin:x:1001:10::/home/admin:/bin/sh\n"
              "alice:x:1000:1000::/home/alice:/bin/sh\n")
        write("etc/group", "wheel:x:10:alice\n")
        write("etc/pam.d/su", "auth required pam_wheel.so use_uid\n")
        login_pam = write("etc/pam.d/su-l", "auth include su\n")
        # 속성 조회용 텍스트다. su 프로그램은 실행하지 않는다.
        binary = write("usr/bin/su", "fixture only; never executed\n")
        binary.chmod(0o750)
        run("기본 그룹 admin과 추가 그룹 alice", 0,
            ("[기본 그룹] admin", "[추가 그룹] alice", "모드=0750"),
            "--root", str(root))
        login_pam.unlink()
        run("가상 su-l 파일 누락", 2,
            ("/etc/pam.d/su-l: ValueError", "자동 판정하지 않음"),
            "--root", str(root))
    if root.exists():
        raise RuntimeError("실습 폴더가 남아 있음")
    print("실습 파일 정리: 완료")


if __name__ == "__main__":
    main()
