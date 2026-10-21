import json
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# 출처 비교용 문자열이며, 이 주소로 접속하지 않는다.
ALLOWED_ORIGIN = "https://app.example"
OTHER_ORIGIN = "https://other.example"

# 실제 자격 증명이 아닌 실습 전용 고정 문자열이다.
USERS = {"demo-alice": "alice", "demo-bob": "bob"}
DOCUMENT = {"owner": "alice", "text": "앨리스의 실습 문서"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def reply(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Vary", "Origin")
        if self.headers.get("Origin") == ALLOWED_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        if status == 401:
            self.send_header("WWW-Authenticate", 'Bearer realm="local-lab"')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/cors-only":
            # 잘못된 예: CORS 헤더만 정하고 인증과 권한은 검사하지 않는다.
            self.reply(200, DOCUMENT)
            return
        if self.path != "/protected":
            self.reply(404, {"error": "없는 경로"})
            return

        value = self.headers.get("Authorization", "")
        token = value[7:] if value.startswith("Bearer ") else ""
        user = USERS.get(token)
        if user is None:
            self.reply(401, {"error": "인증 필요"})
        elif user != DOCUMENT["owner"]:
            self.reply(403, {"error": "문서 권한 없음"})
        else:
            self.reply(200, DOCUMENT)


def request(port, path, origin, token):
    headers = {}
    if origin is not None:
        headers["Origin"] = origin
    if token is not None:
        headers["Authorization"] = "Bearer " + token

    # 프록시 환경 변수를 사용하지 않고 루프백에 직접 연결한다.
    conn = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        result = (
            response.status,
            response.getheader("Access-Control-Allow-Origin"),
            json.loads(response.read().decode("utf-8")),
        )
        if response.getheader("Vary") != "Origin":
            raise AssertionError("Vary 헤더 불일치")
        if response.getheader("Cache-Control") != "no-store":
            raise AssertionError("캐시 제어 헤더 불일치")
        return result
    finally:
        conn.close()


def main():
    cases = [
        ("CORS만 / 다른 출처", "/cors-only", OTHER_ORIGIN, None,
         200, DOCUMENT),
        ("CORS만 / 출처 없음", "/cors-only", None, None,
         200, DOCUMENT),
        ("CORS만 / 허용 출처 직접 지정", "/cors-only", ALLOWED_ORIGIN, None,
         200, DOCUMENT),
        ("권한 검사 / 인증 없음", "/protected", ALLOWED_ORIGIN, None,
         401, {"error": "인증 필요"}),
        ("권한 검사 / 잘못된 토큰", "/protected", ALLOWED_ORIGIN, "invalid",
         401, {"error": "인증 필요"}),
        ("권한 검사 / 다른 사용자", "/protected", ALLOWED_ORIGIN, "demo-bob",
         403, {"error": "문서 권한 없음"}),
        ("권한 검사 / 소유자", "/protected", ALLOWED_ORIGIN, "demo-alice",
         200, DOCUMENT),
        ("권한 검사 / 소유자·다른 출처", "/protected", OTHER_ORIGIN, "demo-alice",
         200, DOCUMENT),
        ("권한 검사 / 소유자·출처 없음", "/protected", None, "demo-alice",
         200, DOCUMENT),
        ("없는 경로", "/missing", ALLOWED_ORIGIN, "demo-alice",
         404, {"error": "없는 경로"}),
    ]

    # 운영체제가 빈 포트를 선택한다. 외부 인터페이스에는 열지 않는다.
    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            for label, path, origin, token, status, body in cases:
                actual = request(server.server_port, path, origin, token)
                cors = ALLOWED_ORIGIN if origin == ALLOWED_ORIGIN else None
                expected = (status, cors, body)
                if actual != expected:
                    raise AssertionError(f"{label}: 예상 {expected!r}, 실제 {actual!r}")
                content = actual[2].get("text", actual[2].get("error"))
                print(
                    f"{label}: HTTP {actual[0]}, "
                    f"CORS 허용 헤더={actual[1] or '없음'}, 본문={content}"
                )
        finally:
            server.shutdown()
            worker.join()
    print("성공: 서버 응답이 예상과 일치하며 실습 서버를 종료했다.")


if __name__ == "__main__":
    main()
