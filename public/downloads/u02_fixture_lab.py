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
    with tempfile.TemporaryDirectory(prefix="u02-fixture-", dir="/tmp") as directory:
        root = Path(directory)

        def write(relative, text):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return path

        def run(label, expected, markers, *arguments, environment=None):
            print(f"[사례] {label}", flush=True)
            result = subprocess.run(
                ["bash", str(collector), *arguments],
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
        # 모든 경로는 /tmp의 가상 루트 아래에 만든다.
        write("etc/login.defs", "PASS_MIN_DAYS 1\nPASS_MAX_DAYS 90\n")
        write("etc/security/pwquality.conf", "minlen = 14\nenforce_for_root\n")
        write("etc/security/pwhistory.conf", "remember = 4\nenforce_for_root\n")
        write("etc/pam.d/passwd", "@include common-password\n")
        write("etc/pam.d/common-password",
              "password requisite pam_pwquality.so minlen=8 enforcing=0 enforce_for_root\n"
              "password required pam_pwhistory.so remember=4 enforce_for_root\n"
              "password required pam_unix.so use_authtok\n")
        run("기본 길이 14와 PAM 인수 8", 0,
            ("minlen=14", "minlen=8 enforcing=0", "대상 미추적", "수동 검토 필요"),
            environment={"U02_ROOT": str(root)})
        # 경로 검증은 파일을 읽기 전에 수행한다.
        run("상대 경로 입력 거부", 2, ("절대 경로",),
            environment={"U02_ROOT": "relative-fixture"})
    if root.exists():
        raise RuntimeError("실습 폴더가 남아 있음")
    print("실습 파일 정리: 완료")


if __name__ == "__main__":
    main()
