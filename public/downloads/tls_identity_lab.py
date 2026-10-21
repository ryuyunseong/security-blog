import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler
from socketserver import TCPServer
from pathlib import Path


NAME = "lab.example.invalid"
CIPHER = "ECDHE-RSA-AES256-GCM-SHA384"

OPENSSL = shutil.which("openssl")

if not OPENSSL or not ssl.HAS_TLSv1_3:
    raise SystemExit(
        "OpenSSL 명령과 Python의 TLS 1.3 지원이 필요합니다"
    )


def run(directory, *args):
    # 비밀키를 출력하지 않고 임시 폴더에서만 인증서를 만듭니다.
    result = subprocess.run(
        [OPENSSL, *args],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode:
        raise RuntimeError(
            "인증서 준비 실패: " + result.stderr.strip()
        )


class Reply(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def log_message(self, *args):
        # 기본 HTTP 서버 로그 대신 아래의 테스트 결과만 출력합니다.
        pass


class LocalServer(TCPServer):
    def get_request(self):
        raw, address = super().get_request()
        raw.settimeout(5)

        try:
            return (
                self.tls.wrap_socket(raw, server_side=True),
                address,
            )
        except BaseException:
            raw.close()
            raise


def check(
    directory,
    port,
    number,
    label,
    version,
    ca,
    hostname,
    expected,
):
    # 서버 인증서 검증과 호스트명 확인이 기본으로 활성화됩니다.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # 이 테스트에서 사용할 CA만 직접 읽어 들입니다.
    context.load_verify_locations(str(directory / ca))

    # 비교 조건을 고정하기 위해 하나의 TLS 버전만 허용합니다.
    context.minimum_version = version
    context.maximum_version = version

    # set_ciphers()는 TLS 1.3 cipher suite를 제어하지 않습니다.
    # 따라서 TLS 1.2 테스트에서만 사용할 cipher suite를 제한합니다.
    if version == ssl.TLSVersion.TLSv1_2:
        context.set_ciphers(CIPHER)

    context.set_alpn_protocols(["http/1.1"])

    requested = (
        "TLSv1.3"
        if version == ssl.TLSVersion.TLSv1_3
        else "TLSv1.2"
    )

    success = False

    try:
        # DNS 조회 없이 루프백 주소에 TCP 연결합니다.
        # 인증서 이름 검증에는 hostname 값이 사용됩니다.
        with socket.create_connection(
            ("127.0.0.1", port),
            timeout=5,
        ) as raw:
            with context.wrap_socket(
                raw,
                server_hostname=hostname,
            ) as tls:
                request = (
                    "GET / HTTP/1.1\r\n"
                    f"Host: {hostname}\r\n"
                    "Connection: close\r\n\r\n"
                )

                tls.sendall(request.encode("ascii"))

                with tls.makefile("rb") as response:
                    status = response.readline(1024).strip()

                success = (
                    expected == "응답"
                    and tls.version() == requested
                    and status == b"HTTP/1.1 200 OK"
                    and tls.selected_alpn_protocol() == "http/1.1"
                )

                http = (
                    "200"
                    if status == b"HTTP/1.1 200 OK"
                    else "예상과 다름"
                )

                detail = (
                    f"실제 협상={tls.version()} | HTTP={http}"
                )

    except ssl.SSLCertVerificationError as error:
        codes = {
            "이름 불일치": {62},
            "신뢰 경로 확인 실패": {20, 21},
        }

        success = (
            error.verify_code
            in codes.get(expected, set())
        )

        reason = (
            expected
            if success
            else "예상과 다른 오류"
        )

        detail = (
            f"요청 버전={requested} | "
            f"인증서 거절={reason}"
        )

        if not success:
            detail += (
                f" | 오류 코드={error.verify_code}"
            )

    except Exception as error:
        detail = "실행 오류=" + str(error)

    print(
        ("성공" if success else "실패")
        + f" | {number}. {label} | {detail}"
    )

    return success


# 생성 파일은 이 임시 폴더에서만 사용하고 종료할 때 정리합니다.
with tempfile.TemporaryDirectory(
    prefix="tls-identity-lab-"
) as temporary:
    directory = Path(temporary)

    (directory / "req.cnf").write_text(
        "[req]\n"
        "distinguished_name=dn\n"
        "prompt=no\n"
        "[dn]\n"
        "CN=TLS Lab\n"
    )

    for ca in ("trusted", "unrelated"):
        run(
            directory,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-noenc",
            "-sha256",
            "-days",
            "1",
            "-config",
            "req.cnf",
            "-subj",
            "/CN=TLS Lab " + ca,
            "-addext",
            "basicConstraints=critical,CA:TRUE,pathlen:0",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
            "-addext",
            "subjectKeyIdentifier=hash",
            "-keyout",
            ca + ".key",
            "-out",
            ca + ".pem",
        )

    run(
        directory,
        "req",
        "-new",
        "-newkey",
        "rsa:2048",
        "-noenc",
        "-sha256",
        "-config",
        "req.cnf",
        "-subj",
        "/CN=" + NAME,
        "-keyout",
        "server.key",
        "-out",
        "server.csr",
    )

    (directory / "server.ext").write_text(
        "basicConstraints=critical,CA:FALSE\n"
        "keyUsage=critical,digitalSignature,keyEncipherment\n"
        "extendedKeyUsage=serverAuth\n"
        "subjectKeyIdentifier=hash\n"
        "authorityKeyIdentifier=keyid,issuer\n"
        "subjectAltName=DNS:" + NAME + "\n"
    )

    run(
        directory,
        "x509",
        "-req",
        "-in",
        "server.csr",
        "-CA",
        "trusted.pem",
        "-CAkey",
        "trusted.key",
        "-set_serial",
        "2",
        "-sha256",
        "-days",
        "1",
        "-extfile",
        "server.ext",
        "-out",
        "server.pem",
    )

    server_context = ssl.SSLContext(
        ssl.PROTOCOL_TLS_SERVER
    )

    server_context.minimum_version = (
        ssl.TLSVersion.TLSv1_2
    )
    server_context.maximum_version = (
        ssl.TLSVersion.TLSv1_3
    )

    # TLS 1.2에서 사용할 cipher suite를 제한합니다.
    # 이 메서드는 TLS 1.3 cipher suite에는 영향을 주지 않습니다.
    server_context.set_ciphers(CIPHER)

    server_context.set_alpn_protocols(
        ["http/1.1"]
    )

    server_context.load_cert_chain(
        directory / "server.pem",
        directory / "server.key",
    )

    with LocalServer(
        ("127.0.0.1", 0),
        Reply,
    ) as server:
        server.tls = server_context

        worker = threading.Thread(
            target=server.serve_forever,
            daemon=True,
        )
        worker.start()

        v13 = ssl.TLSVersion.TLSv1_3
        v12 = ssl.TLSVersion.TLSv1_2

        cases = [
            (
                "TLS 1.3, 이름·신뢰 일치",
                v13,
                "trusted.pem",
                NAME,
                "응답",
            ),
            (
                "TLS 1.3, 다른 이름",
                v13,
                "trusted.pem",
                "other.example.invalid",
                "이름 불일치",
            ),
            (
                "TLS 1.3, 다른 CA",
                v13,
                "unrelated.pem",
                NAME,
                "신뢰 경로 확인 실패",
            ),
            (
                "TLS 1.2, 이름·신뢰 일치",
                v12,
                "trusted.pem",
                NAME,
                "응답",
            ),
        ]

        try:
            results = [
                check(
                    directory,
                    server.server_address[1],
                    n,
                    *case,
                )
                for n, case in enumerate(
                    cases,
                    1,
                )
            ]
        finally:
            server.shutdown()
            worker.join()

print(
    "동작 확인 결과: "
    f"성공={sum(results)} "
    f"실패={4 - sum(results)} "
    "전체=4"
)

print(
    "임시 인증서·비밀키 정리: "
    + (
        "성공"
        if not directory.exists()
        else "실패"
    )
)

raise SystemExit(
    0
    if all(results) and not directory.exists()
    else 1
)
