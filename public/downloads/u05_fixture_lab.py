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
    with tempfile.TemporaryDirectory(prefix="u05-fixture-", dir="/tmp") as directory:
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
        passwd = write("etc/passwd",
                       "root:x:0:0::/root:/bin/sh\n"
                       "alice:x:1000:10::/home/alice:/bin/sh\n")
        run("root만 UID 0", 0, ("[양호]",), "--file", str(passwd))
        with passwd.open("a", encoding="utf-8") as stream:
            stream.write("backup:!:0:0::/srv/backup:/usr/sbin/nologin\n")
        run("잠금·nologin인 backup도 UID 0", 1,
            ("[취약] 계정=backup UID=0",), "--file", str(passwd))
        passwd.write_text("malformed\n", encoding="utf-8")
        run("형식이 깨진 계정 파일", 2,
            ("계정 레코드 형식 이상", "root 레코드가 정확히 하나"),
            "--file", str(passwd))
    if root.exists():
        raise RuntimeError("실습 폴더가 남아 있음")
    print("실습 파일 정리: 완료")


if __name__ == "__main__":
    main()
