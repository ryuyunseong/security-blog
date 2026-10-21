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
    with tempfile.TemporaryDirectory(prefix="u03-fixture-", dir="/tmp") as directory:
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
        write("etc/security/faillock.conf", "deny = 5\nfail_interval = 900\nunlock_time = 600\n")
        # 줄을 수집할 뿐 PAM을 호출하지 않는다.
        write("etc/pam.d/sshd", "auth required pam_faillock.so preauth deny=20\n")
        run("파일 임계값 5와 PAM 인수 20", 0,
            ("deny=5", "deny=20", "최종 판단: 수동 검토 필요"),
            environment={"U03_ROOT": str(root)})
        write("etc/security/faillock.conf", "deny = 0\n")
        run("deny 0의 후보 안내", 0,
            ("deny=0", "잠금 비활성 여부 확인"),
            environment={"U03_ROOT": str(root)})
    if root.exists():
        raise RuntimeError("실습 폴더가 남아 있음")
    print("실습 파일 정리: 완료")


if __name__ == "__main__":
    main()
