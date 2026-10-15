"""Linux에서 글의 코드를 임시 파일·루프백만 사용해 재현한다.

실행: python3 scripts/run-article-examples.py
결과: src/data/executions.json. 운영 계정·PAM·SSH 설정은 변경하지 않는다.
"""
from pathlib import Path
import ast
import hashlib
import json
import os
import platform
import re
import ssl
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "src/content/posts"
records = {}


def blocks(slug):
    source = (POSTS / f"{slug}.md").read_text(encoding="utf-8")
    return [(m[2], m[3]) for m in re.finditer(
        r"^(`{3,4})([\w+-]*)\n(.*?)\n\1\s*$", source, re.M | re.S)]


def write(folder, name, text):
    target = folder / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def run(slug, folder, label, command, display, expected=0, contains=(), env=None):
    result = subprocess.run(command, cwd=folder, capture_output=True,
                            text=True, encoding="utf-8", timeout=60,
                            env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})})
    assert result.returncode == expected, (slug, label, result.returncode, result.stderr)
    for text in contains:
        assert text in result.stdout, (slug, label, text, result.stdout)
    # 무작위 임시 경로만 통일한다. 출력 내용과 종료 코드는 그대로 기록한다.
    clean = lambda text: text.replace(str(folder), "$LAB")
    records.setdefault(slug, {"runs": []})["runs"].append({
        "label": label, "command": display, "exitCode": result.returncode,
        "stdout": clean(result.stdout), "stderr": clean(result.stderr),
    })
    print(f"PASS {slug}: {label} (exit={result.returncode})")


def main():
    if sys.platform != "linux":
        raise SystemExit("Linux에서 실행한다. Windows에서는 WSL Ubuntu를 사용한다.")
    with tempfile.TemporaryDirectory(prefix="security-blog-examples-") as temporary:
        lab = Path(temporary).resolve()
        # 각 글의 Python 코드와 heredoc의 문법도 확인한다.
        syntax_count = 0
        for post in POSTS.glob("*.md"):
            for language, code in blocks(post.stem):
                if language == "python":
                    ast.parse(code)
                    syntax_count += 1
        for slug, filename, marker in [
            ("gzip-output-limit", "gzip_limit.py", "gzip이 아닌 입력: 성공"),
            ("download-path-validation", "path_lab.py", "성공: 경로 비교 30건"),
            ("cors-authentication-authorization", "cors_auth_lab.py", "성공: 서버 응답이 예상과 일치"),
            ("tls-version-and-identity", "tls_identity_lab.py", "성공=4 실패=0 전체=4"),
        ]:
            folder = lab / slug
            folder.mkdir()
            code = next(code for language, code in blocks(slug) if language == "python")
            write(folder, filename, code)
            run(slug, folder, "본문 전체 코드", [sys.executable, "-I", "-B", filename],
                f"python3 -I -B {filename}", contains=(marker,))

        for slug in ["login-failure-sliding-window", "cidr-interval-binary-search"]:
            folder = lab / slug
            folder.mkdir()
            code = [code for language, code in blocks(slug) if language == "python"]
            write(folder, "solution.py", code[0])
            write(folder, "test_solution.py", code[1])
            # 글에 적힌 실행 명령을 그대로 사용한다. 테스트가 실제 수행됐는지 출력도 확인한다.
            marker = "무작위 입력과 전수 탐색 비교: 성공" if slug.startswith("login") else "기준 풀이 비교: 성공"
            run(slug, folder, "본문 테스트 코드", [sys.executable, "-B", "test_solution.py"],
                "python3 -B test_solution.py", contains=(marker,))

        slug = "umask-and-file-permissions"
        folder = lab / slug
        folder.mkdir()
        code = next(code for language, code in blocks(slug) if code.startswith("python3 - <<'PY'"))
        write(folder, "umask_lab.sh", code)
        run(slug, folder, "본문 임시 폴더·ACL 실습", ["bash", "umask_lab.sh"],
            "bash umask_lab.sh", contains=("[정리 성공]", "파일 요청 0666 → 0640"))

        for n in range(2, 11):
            slug = next(POSTS.glob(f"u-{n:02d}-*.md")).stem
            folder = lab / slug
            folder.mkdir()
            language, code = next((language, code) for language, code in blocks(slug) if code.startswith("#!/"))
            name = {2: "check_u02_policy.sh", 3: "check_u03_lockout.sh", 4: "check_u04_password_file.sh",
                    5: "check_u05.sh"}.get(n, f"check_u{n:02d}.py")
            write(folder, name, code)
            if n >= 7:
                fixture_index = {7: 3, 8: 6, 9: 7, 10: 4}[n]
                write(folder, "fixture.sh", blocks(slug)[fixture_index][1])
                expected = 0 if n == 7 else 1
                marker = {7: "oldvendor", 8: "deploy", 9: "oldapp", 10: "1500"}[n]
                run(slug, folder, "본문 가상 계정 파일 예제", ["bash", "fixture.sh"],
                    "bash fixture.sh", expected, contains=(marker, "종료 코드: 1"))
                continue
            fixture = folder / "fixture"
            write(fixture, "etc/passwd", "root:x:0:0::/root:/bin/sh\nalice:x:1000:10::/home/alice:/bin/sh\n")
            if n == 2:
                write(fixture, "etc/login.defs", "PASS_MIN_DAYS 1\nPASS_MAX_DAYS 90\n")
                write(fixture, "etc/security/pwquality.conf", "minlen = 12\nenforce_for_root\n")
                write(fixture, "etc/security/pwhistory.conf", "remember = 4\n")
                write(fixture, "etc/pam.d/common-password", "password requisite pam_pwquality.so retry=3\npassword required pam_pwhistory.so remember=4\n")
                run(slug, folder, "정책 후보가 있는 가상 설정", ["bash", name],
                    f"U02_ROOT=$LAB/fixture bash {name}", contains=("minlen=12", "수동 검토 필요"), env={"U02_ROOT": str(fixture)})
            elif n == 3:
                write(fixture, "etc/security/faillock.conf", "deny = 10\nfail_interval = 900\nunlock_time = 120\n")
                write(fixture, "etc/pam.d/sshd", "auth required pam_faillock.so preauth\naccount required pam_faillock.so\n")
                run(slug, folder, "임계값 10의 가상 설정", ["bash", name],
                    f"U03_ROOT=$LAB/fixture bash {name}", contains=("deny=10", "최종 판단: 수동 검토 필요"), env={"U03_ROOT": str(fixture)})
            elif n == 4:
                # 비밀값이 없는 빈 가상 shadow 파일. 내용은 스크립트가 읽지 않는다.
                shadow = write(fixture, "etc/shadow", "")
                shadow.chmod(0o600)
                run(slug, folder, "x 표지 2개와 빈 가상 shadow", ["bash", name, str(fixture / "etc")],
                    f"bash {name} $LAB/fixture/etc", contains=("쉐도우 참조 x: 2", "빈 비밀번호 필드: 0"))
            elif n == 5:
                passwd = fixture / "etc/passwd"
                args = ["bash", name, "--file", str(passwd)]
                display = f"bash {name} --file $LAB/fixture/etc/passwd"
                run(slug, folder, "root만 UID 0", args, display, contains=("[양호]",))
                with passwd.open("a") as output:
                    output.write("backup:!:0:0::/srv/backup:/usr/sbin/nologin\n")
                run(slug, folder, "잠금·nologin인 backup도 UID 0", args, display, 1, contains=("[취약] 계정=backup UID=0",))
                passwd.write_text("malformed\n", encoding="utf-8")
                run(slug, folder, "형식이 깨진 계정 파일", args, display, 2, contains=("[확인 필요]",))
            elif n == 6:
                write(fixture, "etc/group", "wheel:x:10:alice\n")
                write(fixture, "etc/pam.d/su", "auth required pam_wheel.so use_uid\n")
                write(fixture, "etc/pam.d/su-l", "auth include su\n")
                binary = write(fixture, "usr/bin/su", "fixture only; never executed\n")
                binary.chmod(0o750)
                run(slug, folder, "wheel·PAM·su 모형 파일", [sys.executable, name, "--root", str(fixture)],
                    f"python3 {name} --root $LAB/fixture", contains=("wheel GID=10", "[판정] 자동 판정하지 않음"))

        # U-01 본문 수집기는 /etc 경로가 고정되어 있어 실행하지 않는다.
        # 동일한 sshd 해석 명령을 별도 설정·일회용 키에 적용한다. 데몬은 시작하지 않는다.
        slug = "u-01-root-remote-login"
        folder = lab / slug
        folder.mkdir()
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(folder / "host_key")], check=True)
        config = write(folder, "sshd_config", f"HostKey {folder}/host_key\nUsePAM no\nPermitRootLogin no\nMatch Address 192.0.2.10\n    PermitRootLogin yes\n")
        for address, value in [("192.0.2.11", "no"), ("192.0.2.10", "yes")]:
            # OpenSSH 출력 중 주제에 해당하는 필드만 골라 기록한다.
            command = ["/usr/sbin/sshd", "-T", "-f", str(config), "-C", f"user=root,addr={address},host=admin.example.invalid,laddr=192.0.2.20,lport=22"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            assert result.returncode == 0, result.stderr
            selected = [line for line in result.stdout.splitlines() if line.startswith("permitrootlogin ")]
            assert selected == [f"permitrootlogin {value}"], selected
            records.setdefault(slug, {"runs": []})["runs"].append({
                "label": f"Match 비교: 접속 주소 {address}",
                "command": f"sshd -T -f ./sshd_config -C 'user=root,addr={address},host=admin.example.invalid,laddr=192.0.2.20,lport=22' | awk '$1 == \"permitrootlogin\"'",
                "exitCode": result.returncode, "stdout": "\n".join(selected) + "\n", "stderr": "",
            })
            print(f"PASS {slug}: {address} → {value}")

        assert len(records) == 17
        for slug, record in records.items():
            code = [code for language, code in blocks(slug)]
            record["sourceCodeSha256"] = hashlib.sha256("\0".join(code).encode()).hexdigest()
        os_release = platform.freedesktop_os_release().get("PRETTY_NAME", "Linux")
        if "microsoft" in platform.release().lower():
            os_release += " / WSL 2" if "wsl2" in platform.release().lower() else " / WSL"
        report = {
            "recordedAt": datetime.now(timezone.utc).isoformat(),
            "environment": {"os": os_release, "python": platform.python_version(),
                            "pythonSsl": ssl.OPENSSL_VERSION,
                            "openssl": subprocess.check_output(["openssl", "version"], text=True).strip()},
            "pythonSyntaxCount": syntax_count, "posts": records,
        }
        (ROOT / "src/data/executions.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert not lab.exists()
    print(f"17편, {sum(len(p['runs']) for p in records.values())}개 실행 기록 저장. 임시 작업 폴더 정리 완료.")


if __name__ == "__main__":
    main()
