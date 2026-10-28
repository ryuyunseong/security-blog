---
title: "네트워크 기초: 계층, 다음 홉과 전송 데이터 구분하기"
description: "OSI·TCP/IP 계층과 주요 프로토콜의 역할을 정리하고, 가상 경로 선택·UDP 길이·TCP 바이트 번호를 계산합니다. 자체 문제 5개와 접힌 해설을 제공합니다."
date: "2026-10-28T18:45:14+09:00"
sourcesChecked: "2026-10-28"
category: "cs-study"
tags: ["전산", "NCS", "네트워크", "OSI", "TCP", "UDP", "경로 선택"]
draft: false
example: false
---

한 요청에도 도메인 이름, IP 주소, 포트 번호, 같은 링크에서 쓰는 MAC 주소가 함께 등장한다. 각각 이름을 찾을 대상, 네트워크의 목적지, 전송 계층의 통신 끝점, 다음 링크의 전달 대상을 가리킨다. 목적지 IP를 안다고 그 서버의 MAC 주소를 항상 직접 찾는 것은 아니다.

이번 글에서는 계층별 역할을 나눈 뒤 목적지와 다음 홉이 달라지는 계산을 따라간다. 예제와 다섯 문제는 자체 제작했으며 실제 라우팅 표나 패킷을 수집하지 않는다.

## 일곱 계층과 TCP/IP의 대응

[ITU-T X.200](https://www.itu.int/rec/T-REC-X.200-199407-I/en)의 OSI 모델은 기능을 일곱 계층으로 나눈다. [RFC 1122](https://www.rfc-editor.org/rfc/rfc1122.html)는 인터넷 호스트의 링크·IP·전송 계층과 응용 계층의 관계를 설명한다. 두 모델의 대응은 기능을 비교하는 방법이며 실제 구현을 일곱 개의 프로그램으로 나눈다는 뜻은 아니다.

| OSI 계층 | 핵심 역할 | TCP/IP와 비교 |
| --- | --- | --- |
| 7 응용 | 응용 간 서비스·메시지 | 응용 계층에서 함께 다루는 기능 |
| 6 표현 | 자료 표현·부호화·변환 | 응용 계층에서 함께 다루는 기능 |
| 5 세션 | 대화 관리와 동기화 | 응용 계층에서 함께 다루는 기능 |
| 4 전송 | 끝점 간 전송과 다중화 | TCP·UDP 등의 전송 계층 |
| 3 네트워크 | 논리 주소와 경로 선택 | IP 계층 |
| 2 데이터 링크 | 링크의 프레임 전달 | 링크 계층의 기능 |
| 1 물리 | 매체의 신호 전송 | 링크 계층과 비교할 때 포함하는 하위 기능 |

학습 자료가 TCP/IP를 다섯 계층으로 제시하면 링크를 데이터 링크와 물리로 나누었는지 살핀다. 계층 수보다 어디서 어떤 헤더와 전달 대상을 다루는지가 핵심이다. 일반적인 IP 라우터는 목적지 IP로 경로를 선택한다. 같은 링크의 프레임 전달과 라우터를 통한 다른 네트워크 전달을 구분한다.

## 이름을 찾는 과정과 다음 홉을 고르는 과정

DNS는 이름에 대응하는 레코드를 질의한다. 이름이 존재해도 A·AAAA 레코드가 모두 있는 것은 아니며 캐시된 응답을 사용할 수도 있다. [RFC 1035](https://www.rfc-editor.org/rfc/rfc1035.html)는 DNS의 UDP·TCP 사용을 모두 설명하므로 DNS를 UDP 하나에 고정하지 않는다.

IPv4 목적지가 같은 연결망에 있으면 그 호스트가 다음 홉이 된다. 원격 네트워크이면 가상 경로표에서 고른 게이트웨이가 다음 홉이다. Ethernet에서 [ARP](https://www.rfc-editor.org/rfc/rfc826.html)는 그 링크로 보낼 IPv4 다음 홉에 대응하는 하드웨어 주소를 알아내는 데 쓰인다. 원격 서버의 MAC 주소를 라우터 너머까지 그대로 쓰는 모형으로 그리지 않는다.

[[diagram]]

다음 계산은 192.0.2.0/24를 직접 연결망으로 둔 간단한 IPv4 모형이다. 같은 길이의 경로 우선순위, 인터페이스 상태, 정책 라우팅과 실제 ARP 교환은 포함하지 않는다.

## 메모리의 경로표와 헤더를 계산하기

Python 3.9 이상과 표준 라이브러리만 사용하며 Windows Python 3.12.1에서 실행했다. ZIP을 빈 폴더에 풀고 `08-network-models.py`가 있는 폴더에서 명령을 실행한다. `08-network-questions.py`는 문제를 푼 뒤 같은 폴더에서 실행할 검증 파일이다. 별도의 입력 파일·네트워크 연결·관리자 권한은 필요하지 않다.

[[download]]

```bash
python -I -B -X utf8 08-network-models.py routes
```

Linux·WSL에서는 `python3`를 사용해도 된다. PowerShell은 바로 다음 줄의 `$LASTEXITCODE`, Bash는 `echo $?`로 종료 코드를 읽는다. `-I -B`는 격리된 Python 실행과 바이트코드 생성 억제에 사용한다.

다음은 일반 예제 파일 전체다. `ROUTES`와 `packet`은 코드가 메모리에 준비하며 파일·서버·소켓을 만들지 않는다.

```python
import argparse
from ipaddress import IPv4Address, IPv4Network
import struct
import sys


ROUTES = [
    (IPv4Network("0.0.0.0/0"), IPv4Address("192.0.2.1")),
    (IPv4Network("192.0.2.0/24"), None),
    (IPv4Network("198.51.100.0/24"), IPv4Address("192.0.2.254")),
]


def route_for(destination):
    address = IPv4Address(destination)
    candidates = [(network, gateway) for network, gateway in ROUTES if address in network]
    if not candidates:
        raise ValueError("일치하는 가상 경로가 없다")
    network, gateway = max(candidates, key=lambda item: item[0].prefixlen)
    return str(network), str(gateway if gateway is not None else address)


def udp_fields(packet):
    if len(packet) < 8:
        raise ValueError("UDP 헤더보다 짧다")
    source, destination, length, checksum = struct.unpack("!HHHH", packet[:8])
    if length < 8 or length != len(packet):
        raise ValueError("UDP 길이와 받은 바이트 수가 다르다")
    return source, destination, length, packet[8:]


def main():
    parser = argparse.ArgumentParser(description="네트워크 연결 없이 경로와 헤더를 계산한다")
    parser.add_argument("example", choices=["routes", "udp"])
    args = parser.parse_args()
    try:
        if args.example == "routes":
            for address in ["192.0.2.20", "198.51.100.8", "203.0.113.9"]:
                network, next_hop = route_for(address)
                print(f"{address}: 경로={network}, 다음 홉={next_hop}")
        else:
            packet = struct.pack("!HHHH", 53000, 53, 12, 0) + b"ABCD"
            source, destination, length, payload = udp_fields(packet)
            print(f"UDP: 출발지={source}, 목적지={destination}, 전체={length}, 데이터={len(payload)}")
            print(f"데이터 바이트: {payload.hex()}")
    except ValueError as error:
        print(f"계산 오류: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`route_for()`는 `IPv4Address`로 목적지를 해석하고 `address in network`로 포함 관계를 검사해 `candidates`를 만든다. 그중 `prefixlen`이 가장 큰 경로를 선택한다. 직접 연결을 뜻하는 `gateway is None`이면 목적지 자체를, 게이트웨이가 있으면 그 주소를 다음 홉으로 반환한다. [RFC 1812의 최장 일치 규칙](https://www.rfc-editor.org/rfc/rfc1812.html#section-5.2.4.3)을 참고해 이 예제에서는 최장 접두사만 비교한다.

[[run:1]]

192.0.2.20은 직접 연결 경로에 들어가므로 목적지와 다음 홉이 같다. 198.51.100.8은 기본 경로 `/0`에도 들어가지만 더 긴 `/24`가 선택돼 192.0.2.254를 반환한다. 마지막 목적지에는 더 구체적인 경로가 없어 기본 게이트웨이 192.0.2.1이 나온다. 출력은 가상 경로의 선택값이며 실제 접속 성공을 뜻하지 않는다.

## UDP의 길이와 TCP의 바이트 번호

[RFC 768](https://www.rfc-editor.org/rfc/rfc768.html)의 UDP 헤더는 8바이트다. UDP의 Length에는 헤더와 데이터가 함께 들어간다. 앞 코드의 `udp_fields()`는 처음 8바이트를 `!HHHH`로 읽는다. `!`는 네트워크 바이트 순서이며 각 `H`는 부호 없는 2바이트 정수다.

```bash
python -I -B -X utf8 08-network-models.py udp
```

`struct.pack()`이 UDP Length를 12로 적은 8바이트 헤더와 `ABCD`의 4바이트를 결합한다. 목적지 포트 53을 사용했지만 `ABCD`는 유효한 DNS 질의가 아니다. 체크섬은 0으로 두었으며 이 함수는 길이만 비교한다. IP 헤더·체크섬 유효성·실제 전달을 검증하지 않는다.

[[run:2]]

전체 12에서 헤더 8을 빼면 데이터 4바이트다. `41424344`는 데이터의 16진수 표현으로, 길이 필드 자체나 네 개의 포트 번호가 아니다. 헤더가 너무 짧거나 선언 길이와 실제 길이가 다르면 `ValueError`가 발생한다. 일반 예제의 `main()`은 이를 표준 오류에 쓰고 2로 끝내며 정상 계산은 0이다.

[RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html)의 TCP는 순서 있는 바이트 스트림을 제공한다. 전송 중 손실을 탐지하고 재전송하는 기능과 응용 메시지의 경계는 구별한다. `send()` 한 번과 `recv()` 한 번이 같은 메시지 단위라고 가정하지 않는다. TCP 자체가 암호화를 제공하는 것도 아니다. UDP는 데이터그램 단위이며 자체적으로 순서·재전송을 보장하지 않는다.

| 프로토콜 | 먼저 구분할 역할 | 자주 생기는 혼동 |
| --- | --- | --- |
| DNS | 이름에 대한 레코드 질의 | 이름 조회와 서비스 접속 성공을 같게 봄 |
| ARP | IPv4 다음 홉과 링크 주소 대응 | 원격 서버 MAC을 직접 찾는다고 봄 |
| DHCP | 주소와 네트워크 구성 전달 | DNS 이름 조회와 섞음 |
| TCP·UDP | 포트와 전송 기능 | TCP 암호화, UDP 신뢰성 보장을 단정함 |
| HTTP | 응용 계층의 요청·응답 의미 | IP 주소나 MAC 조회 자체로 봄 |

DHCP의 구성 전달은 [RFC 2131](https://www.rfc-editor.org/rfc/rfc2131.txt)에 설명되어 있다. 이 표는 프로토콜을 실제로 실행한 결과가 아니라 역할 비교다.

## 자체 연습문제 5개

### 문제 1. 이름과 링크 주소의 차이

도메인 이름의 A 레코드를 질의하는 기능과, 같은 Ethernet 링크로 보낼 IPv4 다음 홉의 하드웨어 주소를 얻는 기능은 각각 무엇인가? 두 기능을 같은 계층의 동일한 작업으로 볼 수 있는가?

<details class="study-answer">
<summary>문제 1 정답·해설 보기</summary>

### 문제 1 해설

이름 레코드 질의는 DNS, IPv4 다음 홉의 링크 주소 대응은 ARP다. DNS는 응용 계층의 이름 체계이며 ARP는 링크 전달에 필요한 주소 대응이다. DNS 응답으로 IP를 얻어도 경로에 따라 원격 목적지 대신 로컬 게이트웨이의 링크 주소가 필요할 수 있다. 이름 조회 성공만으로 응용 연결 성공이 보장되지 않는다.

</details>

### 문제 2. 직접 연결 경로

`ROUTES`가 앞 코드와 같을 때 `route_for("192.0.2.99")`가 반환할 경로와 다음 홉은 무엇인가? `None`이 응답에 그대로 나오는지도 설명하자.

<details class="study-answer">
<summary>문제 2 정답·해설 보기</summary>

### 문제 2 해설

`('192.0.2.0/24', '192.0.2.99')`다. 목적지가 `/24`에 포함돼 기본 경로보다 먼저 선택되며 그 경로의 `gateway`는 `None`이다. 반환식은 이때 목적지 `address`를 사용하므로 `None`을 문자열로 출력하지 않는다. 직접 연결된 목적지가 다음 홉인 계산이다.

</details>

### 문제 3. 기본 경로와 더 긴 접두사

같은 경로표에서 목적지가 198.51.100.99일 때 `/0`와 `/24` 중 무엇이 선택되는가? 다음 홉도 적자.

<details class="study-answer">
<summary>문제 3 정답·해설 보기</summary>

### 문제 3 해설

198.51.100.0/24와 다음 홉 192.0.2.254다. 두 경로가 모두 `candidates`에 들어가지만 `max(..., key=prefixlen)`가 24를 고른다. 목록에서 기본 경로가 먼저 선언됐다는 이유로 그 행을 바로 반환하지 않는다. 실제 경로 정책 전체가 아니라 이 코드의 최장 접두사 모형에 대한 답이다.

</details>

### 문제 4. UDP 길이 필드가 다를 때

헤더가 길이 16을 선언했는데 실제 바이트는 8바이트 헤더와 `ABCD`의 4바이트뿐이다. `udp_fields()`는 데이터 8바이트를 반환하는가, 4바이트를 반환하는가, 예외를 발생시키는가?

<details class="study-answer">
<summary>문제 4 정답·해설 보기</summary>

### 문제 4 해설

`ValueError`가 발생한다. `length`는 16이고 `len(packet)`은 12여서 길이 비교 조건에 걸린다. 선언값만 보고 없는 데이터를 채우지도 않고, 길이가 어긋난 자료를 정상적인 4바이트 데이터로 허용하지도 않는다. 문제 검증 파일은 이 예외를 예상한 거부로 잡으며, 예외가 없으면 `AssertionError`로 실패한다.

</details>

### 문제 5. 문자 수와 TCP 데이터 바이트 수

현재 TCP 데이터의 첫 순서 번호를 1000으로 가정하자. UTF-8로 인코딩한 문자열 `가나`만 보냈다면 다음 데이터의 순서 번호는 얼마인가? SYN·FIN은 포함하지 않고 이번 구간에서 번호의 순환도 발생하지 않는다.

<details class="study-answer">
<summary>문제 5 정답·해설 보기</summary>

### 문제 5 해설

UTF-8에서 두 글자는 6바이트이므로 다음 순서 번호는 1006이다. 문제 코드는 `len("가나".encode("utf-8"))`로 바이트 수를 얻어 더한다. 문자 수 2를 더한 1002와 구별한다. 이는 순서 번호 계산이며 실제 세그먼트 수·재전송·ACK 도착 시점을 측정한 값은 아니다.

</details>

## 문제별 계산과 거부 조건의 실행

<details class="study-verification">
<summary>문제 검증 전체 코드·명령·출력 보기</summary>

문제를 푼 뒤 `08-network-questions.py`를 실행한다. 같은 폴더의 일반 예제 파일을 `__file__` 기준 경로와 `importlib`로 불러오므로 `-I`에서도 현재 폴더가 모듈 검색 경로에 들어갈 필요가 없다. 파일이 없거나 이름이 달라 모듈을 읽지 못하면 예외가 전파돼 종료 코드 1이 된다.

```bash
python -I -B -X utf8 08-network-questions.py
```

다음은 검증 파일 전체다. 문제 1은 프로토콜 역할의 개념 해설이며 나머지 네 문제의 가상 계산을 코드로 대조한다.

```python
import importlib.util
from pathlib import Path
import struct


path = Path(__file__).with_name("08-network-models.py")
spec = importlib.util.spec_from_file_location("network_models", path)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)

q2 = models.route_for("192.0.2.99")
assert q2 == ("192.0.2.0/24", "192.0.2.99")
print(f"q2: {q2}")
q3 = models.route_for("198.51.100.99")
assert q3 == ("198.51.100.0/24", "192.0.2.254")
print(f"q3: {q3}")
packet = struct.pack("!HHHH", 53000, 53, 16, 0) + b"ABCD"
try:
    models.udp_fields(packet)
except ValueError as error:
    print(f"q4: 예상한 거부, {error}")
else:
    raise AssertionError("길이가 다른 자료가 허용됐다")
data = "가나".encode("utf-8")
next_sequence = (1000 + len(data)) % (2 ** 32)
assert len(data) == 6 and next_sequence == 1006
print(f"q5: 데이터={len(data)}바이트, 다음 순서 번호={next_sequence}")
print("문제 2~5의 가상 계산 대조 완료")
```

[[run:3:fold]]

종료 코드 0은 네 문제의 값과 예상한 거부가 일치했다는 뜻이다. `q4`의 거부는 자료를 정상 처리했다는 뜻이 아니다. 표준 오류가 비어 있어도 코드와 출력·종료 코드를 함께 비교하며, 입력 파일을 새로 만들거나 과거 기록을 지우는 절차는 없다.

</details>

## 시험 직전 복습

OSI의 기능 구분과 TCP/IP의 계층 묶음을 나눠 기억한다. 도메인 이름, 목적지 IP, 다음 홉 IP, 포트, 링크 주소를 서로 바꿔 쓰지 않는다. 직접 연결에서는 목적지가 다음 홉이고 원격 경로에서는 게이트웨이가 다음 홉이다. UDP 길이는 헤더를 포함하며 TCP의 순서 번호는 데이터 바이트 수와 연결된다. DNS는 이름 레코드 질의, DHCP는 네트워크 구성 전달, ARP는 IPv4 링크 주소 대응이라는 역할을 각각 말할 수 있어야 한다.

## 참고 자료

- [RFC 1812: IPv4 라우터의 경로 선택](https://www.rfc-editor.org/rfc/rfc1812.html)
- [RFC 9110: HTTP 의미](https://www.rfc-editor.org/rfc/rfc9110.html)

- [ITU-T X.200: OSI 기본 참조 모델](https://www.itu.int/rec/T-REC-X.200-199407-I/en)
- [RFC 1122: 인터넷 호스트의 통신 계층](https://www.rfc-editor.org/rfc/rfc1122.html)
- [RFC 768: UDP](https://www.rfc-editor.org/rfc/rfc768.html)
- [RFC 9293: TCP](https://www.rfc-editor.org/rfc/rfc9293.html)
- [RFC 1035: DNS 구현과 명세](https://www.rfc-editor.org/rfc/rfc1035.html)
- [RFC 826: Ethernet 주소 해석](https://www.rfc-editor.org/rfc/rfc826.html)
- [RFC 2131: DHCP](https://www.rfc-editor.org/rfc/rfc2131.txt)
- [Python ipaddress: 주소와 네트워크 계산](https://docs.python.org/3.12/library/ipaddress.html)
