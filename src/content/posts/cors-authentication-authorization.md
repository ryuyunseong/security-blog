---
title: "CORS 설정과 서버 접근 권한의 차이"
description: "로컬 API 실습으로 CORS 허용과 서버의 인증·자료별 권한 검사를 구분합니다."
date: "2026-10-09T21:15:19+09:00"
updated: "2026-10-17T18:17:24+09:00"
category: "application-security"
tags: ["CORS", "인증", "인가"]
draft: false
example: false
---

CORS는 브라우저가 응답을 JavaScript에 공개할지 정하는 규칙이다. 서버가 비공개 문서를 반환할지 결정하는 사용자 인증·인가와는 역할이 다르다.

로컬 API에 두 경로를 만들어 차이를 비교한다. `/cors-only`는 CORS 헤더만 설정하고, `/protected`는 사용자 인증과 문서 소유자 검사까지 수행한다. Python 클라이언트로 각 경로의 상태 코드와 반환 본문을 읽는다.

## 출처를 허용하는 것과 사용자에게 권한을 주는 것은 다르다

CORS(Cross-Origin Resource Sharing)는 브라우저가 다른 출처의 응답을 JavaScript에 공개할 수 있는 조건을 정한다. 일반적인 웹 출처(Origin)는 스킴·호스트·포트로 구분한다. 반면 인증(Authentication)은 요청자가 누구인지 확인하고, 인가(Authorization)는 그 사용자가 요청한 자료를 읽거나 변경해도 되는지 판단한다.

| 구분 | 확인하는 질문 | 실습 코드의 처리 |
| --- | --- | --- |
| CORS | 어느 웹 출처에 응답을 공개할 것인가 | 허용한 Origin에만 Access-Control-Allow-Origin 반환 |
| 인증 | 누가 요청했는가 | 실습 토큰을 사용자와 연결 |
| 인가 | 이 사용자가 이 문서를 읽어도 되는가 | 인증된 사용자와 문서 소유자 비교 |

Origin 헤더는 사용자 신원을 증명하지 않는다. 브라우저 JavaScript에서는 이 헤더를 임의로 설정할 수 없지만, Python이나 curl 같은 HTTP 클라이언트는 원하는 값을 보내거나 생략할 수 있다. 비공개 자료를 반환하려면 출처 허용 여부와 별개로 인증과 권한 검사가 필요하다.

## 로컬 서버에서 두 구현 비교하기

/cors-only는 CORS 헤더만 설정하고 문서를 반환하는 잘못된 예다. /protected는 같은 CORS 설정에 인증과 문서 소유자 검사를 추가한다. 문서는 앨리스만 읽을 수 있도록 정하고, 밥에게는 읽기 권한을 주지 않는다.

Python 3 표준 라이브러리만 사용한다. 아래 코드를 cors_auth_lab.py로 저장하고 터미널에서 실행한다.

```bash
python3 cors_auth_lab.py
```
서버는 127.0.0.1의 임시 포트에서만 요청을 받고, 비교가 끝나면 자동으로 종료된다. app.example과 other.example은 Origin 헤더에 넣을 비교용 문자열이며, 해당 주소로 접속하지 않는다.

토큰과 문서는 모두 가짜 자료다. 실제 토큰으로 바꿀 필요가 없다. http.server와 고정 토큰 비교는 원리를 확인하기 위한 구성으로, 운영 서비스의 인증 구현으로 사용하지 않는다.

```python
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
```
reply()는 출처에 따라 CORS 헤더를 붙인다. 실제 문서 반환 여부는 do_GET()에서 결정한다. /protected는 토큰으로 사용자를 확인한 뒤 문서 소유자와 비교하지만, /cors-only는 두 검사를 모두 생략한다.

실행 중 각 요청의 상태 코드·CORS 허용 헤더·본문을 예상값과 대조한다. 세 값이 모두 맞아야 해당 사례를 ‘성공’으로 표시한다.

## CORS 허용 헤더가 없어도 본문은 반환된다

Python의 http.client는 브라우저의 CORS 검사를 수행하지 않는다. 따라서 서버가 CORS 허용 헤더 없이 보낸 본문도 아래처럼 읽을 수 있었다.

```text
CORS만 / 다른 출처: HTTP 200, CORS 허용 헤더=없음, 본문=앨리스의 실습 문서
CORS만 / 출처 없음: HTTP 200, CORS 허용 헤더=없음, 본문=앨리스의 실습 문서
CORS만 / 허용 출처 직접 지정: HTTP 200, CORS 허용 헤더=https://app.example, 본문=앨리스의 실습 문서
```
다른 출처를 보내거나 Origin을 생략해도 문서가 반환됐다. 허용 출처를 직접 지정하면 CORS 허용 헤더까지 붙는다. 문제는 CORS 허용 목록의 범위가 아니라, 앨리스만 읽어야 할 문서를 미인증 요청에도 반환한다는 데 있다.

서버에서 Origin을 검사해 불일치 요청에 403을 반환하도록 바꿔도 사용자 인증을 대신할 수는 없다. 일반 HTTP 클라이언트는 허용된 출처 문자열을 그대로 보낼 수 있기 때문이다.

[[diagram]]

## 인증과 소유자 검사를 추가하면 무엇이 달라질까

| 요청 조건 | HTTP 상태 | 반환 내용 |
| --- | --- | --- |
| 허용 출처, 토큰 없음 또는 잘못된 토큰 | 401 | 인증 필요 |
| 허용 출처, 밥의 토큰 | 403 | 문서 권한 없음 |
| 허용 출처, 앨리스의 토큰 | 200 | 앨리스의 실습 문서 |
| 다른 출처 또는 출처 없음, 앨리스의 토큰 | 200 | 앨리스의 실습 문서 |

허용 출처에서 요청해도 인증이 없으면 401을, 문서 권한이 없는 밥의 토큰이면 403을 반환했다. 두 오류 응답에는 문서 내용이 포함되지 않았다.

```text
권한 검사 / 다른 사용자: HTTP 403, CORS 허용 헤더=https://app.example, 본문=문서 권한 없음
권한 검사 / 소유자·다른 출처: HTTP 200, CORS 허용 헤더=없음, 본문=앨리스의 실습 문서
```
첫 번째 응답에는 CORS 허용 헤더가 있지만 문서 접근은 거부됐다. 이 헤더는 브라우저가 응답을 읽도록 허용하는 데 쓰이며, 문서에 대한 사용자 권한을 나타내지 않는다.

두 번째 요청은 다른 출처를 지정했어도 앨리스의 유효한 토큰을 사용했으므로 문서를 반환했다. 이 서버는 문서 접근을 사용자 권한으로 판단하고, 웹 출처 제한은 브라우저의 응답 공개 정책으로 적용한다. 서버 간 호출이나 명령줄 클라이언트도 허용하는 설계라면 이 결과 자체는 취약점이 아니다.

[[run:1:fold]]

## 브라우저의 동작은 별도로 확인해야 한다

위 실습에서 확인한 것은 HTTP 응답이다. 브라우저를 실행해 JavaScript의 본문 읽기 여부까지 검증한 결과는 아니다.

브라우저는 CORS 허용 조건을 만족하지 못한 교차 출처 응답을 JavaScript에 공개하지 않는다. 다만 이것이 요청 자체를 항상 차단한다는 뜻은 아니다. 사전 요청(Preflight)이 필요 없는 요청은 서버에 전송된 뒤 응답을 읽는 단계에서 차단될 수 있다.

Authorization 헤더를 직접 넣는 교차 출처 fetch() 요청은 사전 요청 허용 대상이다. 이전에 허용된 결과가 캐시되어 있지 않다면 브라우저가 OPTIONS 요청으로 허용 여부를 먼저 확인하며, 이 확인에 실패하면 본 요청을 보내지 않는다. 실습 코드는 OPTIONS 처리를 구현하지 않았으므로 브라우저에서 인증 요청을 비교하는 용도로 그대로 사용할 수 없다.

브라우저까지 점검할 때는 요청 출처, 사전 요청 결과, 본 요청의 전송 여부, JavaScript에서 응답을 읽었는지를 구분해 기록한다. 서버가 401이나 403을 반환했더라도 CORS 헤더가 맞지 않으면 JavaScript에서는 그 오류 응답을 읽지 못할 수 있다. 콘솔의 CORS 오류만으로 서버의 접근 통제가 정상인지 판단하지 않는다.

## 비공개 API를 점검할 때는 자료별 권한을 확인한다

실서비스에서는 요청마다 검증된 사용자 신원과 대상 자료의 접근 정책을 확인해야 한다. 문서 ID나 URL을 안다는 이유만으로 접근을 허용하지 않고, 소유자·조직·역할·공유 상태 등 서비스가 정한 조건을 적용한다. 보호 대상 데이터가 응답에 포함되기 전에 권한 검사가 완료되는지도 살펴본다.

권한 검사 시험에는 계정 두 개와 한 계정 소유의 테스트 문서를 사용한다. 미인증 요청, 다른 사용자의 토큰, 소유자 토큰을 각각 보내고 Origin도 따로 바꾼다. 상태 코드뿐 아니라 본문을 대조해야 403 응답에 문서가 섞여 반환되는 경우까지 찾을 수 있다.

공개 API가 누구에게나 같은 정보를 제공한다면 인증 없는 200 응답이 정상일 수 있다. 취약 여부는 보호해야 할 자료와 허용 대상을 기준으로 판단한다. 이 실습의 /cors-only는 앨리스만 읽도록 정한 문서를 미인증 요청에도 반환하므로 접근 통제 누락에 해당한다. 반대로 인증된 밥이 같은 문서를 읽을 수 있다면 자료별 인가가 빠졌는지 확인해야 한다.

CORS 허용 출처는 필요한 범위로 관리한다. 쿠키가 자동으로 전송되는 서비스의 상태 변경 요청에는 CSRF 방어도 적용해야 한다. Origin 검사는 CSRF 방어에 활용할 수 있지만, 사용자 인증과 자료별 권한 검사는 별도로 필요하다.

## 참고 자료

- [WHATWG, Fetch Standard: CORS protocol](https://fetch.spec.whatwg.org/#http-cors-protocol)
- [OWASP, Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP, Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Python, http.server](https://docs.python.org/3/library/http.server.html)
- [Python, http.client](https://docs.python.org/3/library/http.client.html)
