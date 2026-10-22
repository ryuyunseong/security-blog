---
title: "TLS 1.3이면 안전할까? 버전과 인증서 검증의 차이"
description: "로컬 TLS 실습으로 프로토콜 버전, 인증서 신뢰 경로, 서버 이름 검증을 비교합니다."
date: "2026-10-06T22:56:53+09:00"
updated: "2026-10-22"
category: "infrastructure"
tags: ["TLS", "인증서", "Python"]
draft: false
example: false
---

TLS 1.3으로 연결됐다는 사실만으로 접속한 서버가 의도한 상대인지 알 수는 없습니다. 클라이언트에서 인증서의 이름과 신뢰 경로도 검증해야 합니다.

같은 로컬 서버에 허용 TLS 버전, 신뢰 CA, 검증할 이름을 바꿔 접속해 봅니다. 네 조건에서 연결이 허용되거나 거절되는 결과를 비교합니다.

## 같은 서버에 네 가지 조건으로 접속하기

실습 서버는 127.0.0.1의 임의 포트에서만 연결을 받습니다. 인증서에는 lab.example.invalid를 넣고, 클라이언트가 허용하는 TLS 버전과 검증할 이름, 신뢰하는 CA를 바꿔 비교합니다.

실험용 CA는 클라이언트에서만 사용합니다. 운영체제나 브라우저의 신뢰 저장소에는 등록하지 않으며, 인증서 검증도 끄지 않습니다.

Python 3.10 이상과 OpenSSL 3.x 명령줄 도구가 필요합니다. Python에 연결된 TLS 라이브러리도 TLS 1.3을 지원해야 합니다. 별도 Python 패키지는 사용하지 않습니다.

실습 ZIP의 `tls_identity_lab.py`를 사용하거나 아래 코드를 같은 이름으로 저장합니다. 터미널에서 파일을 저장한 폴더로 이동합니다. 먼저 `openssl version`으로 명령줄 도구를 조회하고, `python3 -c 'import ssl; print(ssl.OPENSSL_VERSION, ssl.HAS_TLSv1_3)'`로 Python 쪽 라이브러리와 TLS 1.3 지원을 따로 살펴봅니다. OpenSSL 명령줄 도구와 Python의 TLS 라이브러리는 서로 다른 OpenSSL 버전을 사용할 수 있습니다.

인증서나 비밀키를 미리 만들 필요는 없습니다. 코드는 쓰기 가능한 임시 경로에 전용 폴더를 만들고 `req.cnf`·`server.ext`와 CA 두 쌍, 서버 키·CSR·인증서를 생성합니다. `trusted.pem`은 서버 인증서의 발급 CA이고 `unrelated.pem`은 신뢰 불일치를 비교할 CA입니다. 파일들은 종료할 때 삭제되며, 별도 CA 설치나 hosts 파일 수정은 하지 않습니다.

[[download]]

```python
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
```
저장한 뒤 실행합니다.

```bash
python3 -I -B tls_identity_lab.py
```

## 인증서 생성에서 응답 비교까지

`run()`은 임시 폴더를 작업 경로로 삼아 OpenSSL을 실행합니다. 명령이 실패하거나 제한 시간을 넘기면 이후 연결 비교로 넘어가지 않습니다. 생성한 인증서·키는 서버의 `load_cert_chain()`에, 신뢰할 CA는 클라이언트의 `load_verify_locations()`에 각각 전달합니다.

`check()`는 TCP 연결 주소를 `127.0.0.1`로 고정하고, `server_hostname`으로 인증서에서 검증할 이름을 별도로 전달합니다. `lab.example.invalid`를 DNS에서 찾는 작업은 없습니다. 클라이언트 컨텍스트의 인증서·이름 검증을 유지한 채 최소·최대 TLS 버전을 같은 값으로 정해 한 버전씩 비교합니다.

TLS 연결이 성립한 경우에만 HTTP 요청을 보내고, 협상 버전·HTTP 200·ALPN `http/1.1`을 모두 대조합니다. 인증서가 거절돼야 하는 사례에서는 예외 종류와 검증 오류 코드를 기대값과 비교합니다. 마지막에는 각 반환값을 모아 성공 수를 계산하고 로컬 서버와 임시 폴더를 정리합니다.

[[diagram]]

## 이름과 CA가 달라지면 연결도 거절된다

발급 CA와 이름이 모두 맞으면 HTTP 200을 받았고, 둘 중 하나가 다르면 인증서 검증에서 연결이 거절됐습니다.

| 클라이언트 허용 버전 | 이름 | 신뢰 CA | 실행 결과 |
| --- | --- | --- | --- |
| TLS 1.3만 허용 | 일치 | 발급 CA | TLS 1.3 연결, HTTP 200 |
| TLS 1.3만 허용 | 불일치 | 발급 CA | 이름 검증 실패 |
| TLS 1.3만 허용 | 일치 | 관계없는 CA | 신뢰 경로 검증 실패 |
| TLS 1.2만 허용 | 일치 | 발급 CA | TLS 1.2 연결, HTTP 200 |

코드에서 세는 ‘성공’에는 예상대로 연결을 거절한 사례도 포함됩니다. 네 조건의 기대 결과가 모두 맞는지 검사합니다.

TLS 1.2 테스트의 암호 스위트(cipher suite)는 ECDHE-RSA-AES256-GCM-SHA384로 제한했습니다. Python의 set_ciphers()는 TLS 1.3 암호 스위트를 제어하지 않으므로, TLS 1.3에도 같은 설정이 적용됐다고 해석하면 안 됩니다.

거절된 두 줄의 `요청 버전=TLSv1.3`은 클라이언트에 지정한 조건입니다. HTTP 응답을 받은 줄의 `실제 협상=TLSv1.3`과 구분해야 합니다. 네 사례가 기대대로 동작하고 임시 폴더가 사라졌을 때 종료 코드 0이 됩니다.

OpenSSL이 없거나 TLS 1.3을 지원하지 않으면 비교 전에 중단되고, 예상과 다른 응답이나 검증 오류도 실패로 처리됩니다. 오류 코드가 다른 환경에서는 Python이 사용하는 OpenSSL 버전과 실제 오류를 함께 살펴봅니다. 문제를 통과시키려고 인증서 검증을 끄면 이 실습의 비교 조건이 달라집니다.

[[run:1:fold]]

## OpenSSL에서도 연결 성공과 검증 성공을 구분해야 한다

OpenSSL s_client는 기본적으로 인증서 검증 오류가 발생해도 연결을 계속할 수 있습니다. CONNECTED나 TLSv1.3이 표시됐다는 이유만으로 서버 인증까지 성공했다고 판단하면 안 됩니다.

아래 명령은 별도의 서버 점검 예시이며 위 로컬 실행 기록에 포함하지 않았습니다. 앞 실습은 서버를 종료하고 임시 인증서를 지우므로 그 포트나 CA 파일을 그대로 재사용할 수 없습니다. 점검할 권한이 있는 서버를 대상으로 다음처럼 확인합니다. example.com은 실제 점검 대상 이름으로 바꿉니다.

```bash
openssl s_client \
  -connect example.com:443 \
  -servername example.com \
  -verify_hostname example.com \
  -verify_return_error
```
| 옵션 | 역할 |
| --- | --- |
| -servername | SNI로 서버 이름 전달 |
| -verify_hostname | 인증서가 해당 이름에 유효한지 확인 |
| -verify_return_error | 인증서 검증 오류가 발생하면 연결 중단 |

SNI는 서버가 제시할 인증서를 선택하는 데 쓰이며, 호스트명 검증을 대신하지 않습니다. 사설 CA를 사용하는 환경에서는 승인된 CA 파일을 -CAfile로 지정합니다.

## 운영 환경에서는 점검 구간도 확인하기

외부에서 확인한 TLS 결과는 CDN이나 로드밸런서까지의 연결일 수 있습니다. 그 뒤의 원본 서버 구간은 다른 TLS 버전을 사용하거나 HTTP로 연결될 수도 있습니다.

점검 결과에는 접속 주소·포트와 점검 구간, 검증한 이름, 신뢰 CA, 협상된 TLS 버전·암호 스위트, 인증서 검증 결과를 적습니다. 인증서 폐기 상태와 웹 애플리케이션 보안은 이번 실습의 범위에 포함하지 않았습니다.

## 참고 자료

- [RFC 9525: Service Identity in TLS](https://www.rfc-editor.org/rfc/rfc9525.html)
- [Python ssl 모듈](https://docs.python.org/3.12/library/ssl.html)
- [OpenSSL s_client](https://docs.openssl.org/3.5/man1/openssl-s_client/)
