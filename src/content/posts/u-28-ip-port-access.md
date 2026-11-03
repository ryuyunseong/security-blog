---
title: "U-28: 접속 IP 및 포트 제한"
description: "출발지 IP·프로토콜·목적지 포트를 함께 비교하고 규칙 순서에 따른 차이를 재현합니다. 가상 접근표와 실제 방화벽의 적용 범위, TCP Wrapper 지원 여부와 규칙 내보내기를 구분합니다."
date: "2026-11-03T18:33:16+09:00"
sourcesChecked: "2026-11-03"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "접근 제어", "CIDR", "KISA"]
draft: false
series: unix-2026
seriesOrder: 28
---

허용 목록에 IP주소가 있어도 어느 서비스까지 허용했는지는 별도로 읽어야 한다. 출발지 `192.0.2.14`, 프로토콜 `tcp`, 목적지 포트 `22`를 한 조합으로 보면 같은 IP의 다른 포트나 같은 포트 번호의 UDP 요청과 구별할 수 있다. 이 글에서는 그 조합과 규칙의 순서를 가상 접근표로 계산한다.

## 허용할 호스트와 서비스의 범위

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-28은 ‘접속 IP 및 포트 제한’이며 중요도는 ‘상’이다. 항목표와 본문 56~60쪽에서 제목·중요도를 대조했으며 적용 대상은 SOLARIS, LINUX, AIX, HP-UX 등이다.

양호 기준은 접속을 허용할 특정 호스트의 IP주소 및 포트 제한을 설정한 경우다. 해당 제한을 설정하지 않으면 취약으로 구분한다. 조치 사례에는 호스트별 서비스 제한 도구와 운영체제의 방화벽을 사용한 접근 허용 IP 등록이 나온다. 원문은 허용되지 않은 IP에서 서비스를 사용할 수 없다는 영향도 명시한다.

실제 정책을 조사할 때는 허용 대상과 서비스, 프로토콜·목적지 포트, 규칙의 적용 위치와 순서를 함께 남긴다. 아래 예제의 포트 번호는 가상 정책의 비교값이며 운영 서버의 허용 목록을 제안하는 값이 아니다.

## 여덟 요청을 같은 접근표에 넣기

Python 3.9 이상과 표준 라이브러리만 사용한다. 실제 실행 환경은 Windows Python 3.12.1이다. 주소는 문자열과 정수로만 해석하므로 관리자 권한·실제 계정·서버·방화벽 도구가 필요하지 않다. 소켓을 만들거나 DNS 조회를 하지 않고 운영 방화벽도 읽거나 바꾸지 않는다.

ZIP을 빈 폴더에 풀고 `u28_access_model.py`와 `u28_access_cases.json`이 함께 있는 글별 폴더에서 실행한다. 입력은 ZIP에 포함되어 있으므로 다시 만들지 않는다. 코드가 결과 파일을 쓰거나 입력을 수정하지 않으며 정리할 때는 자신이 압축을 푼 실습 폴더만 대상으로 삼는다.

[[download]]

```bash
python -I -B -X utf8 u28_access_model.py u28_access_cases.json
```

명령 직후 PowerShell에서는 `$LASTEXITCODE`, Linux·WSL에서는 `echo $?`로 종료 코드를 읽는다. Linux·WSL의 Python 명령이 `python3`이면 그 이름으로 실행한다. 직접 지정하는 입력 경로에 공백이 있으면 전체 경로를 따옴표로 감싼다.

JSON의 `rules`는 위에서 아래로 검사할 규칙 목록이다. `source`는 규칙에서 CIDR, 요청에서 단일 주소를 뜻한다. `port`는 목적지 포트이며 이 예제는 `tcp`와 `udp`만 받는다. 일치하는 첫 규칙의 `allow` 또는 `deny`에서 계산을 끝내고 끝까지 일치하지 않으면 예제에 고정한 기본 거부를 반환한다.

```json
{
  "rules": [
    {"id": "block-one", "source": "192.0.2.13/32", "protocol": "tcp", "port": 22, "action": "deny"},
    {"id": "admin-net", "source": "192.0.2.0/25", "protocol": "tcp", "port": 22, "action": "allow"},
    {"id": "web-net", "source": "198.51.100.0/24", "protocol": "tcp", "port": 443, "action": "allow"},
    {"id": "admin-v6", "source": "2001:db8:1::/64", "protocol": "tcp", "port": 22, "action": "allow"}
  ],
  "requests": [
    {"id": "blocked-host", "source": "192.0.2.13", "protocol": "tcp", "port": 22},
    {"id": "admin-host", "source": "192.0.2.14", "protocol": "tcp", "port": 22},
    {"id": "same-ip-other-port", "source": "192.0.2.14", "protocol": "tcp", "port": 443},
    {"id": "outside-half", "source": "192.0.2.130", "protocol": "tcp", "port": 22},
    {"id": "udp-same-port", "source": "192.0.2.14", "protocol": "udp", "port": 22},
    {"id": "web-client", "source": "198.51.100.8", "protocol": "tcp", "port": 443},
    {"id": "v6-admin", "source": "2001:db8:1::8", "protocol": "tcp", "port": 22},
    {"id": "v6-other", "source": "2001:db8:2::8", "protocol": "tcp", "port": 22}
  ]
}
```

`192.0.2.0/25`는 주소의 앞 25비트를 비교한다. 이 범위에 속하는 `192.0.2.13/32`는 단일 주소다. 가상 목록은 그 단일 주소의 거부를 더 넓은 범위의 허용보다 먼저 둔다. IPv6용 `2001:db8:1::/64`도 별도 규칙으로 두며 IPv4 범위와 섞어 비교하지 않는다.

```python
import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path


def checked_endpoint(row, fields):
    if not isinstance(row, dict) or set(row) != fields:
        raise ValueError("필드")
    if not isinstance(row["id"], str) or not re.fullmatch(r"[a-z0-9-]{1,40}", row["id"]):
        raise ValueError("이름")
    if row["protocol"] not in ("tcp", "udp"):
        raise ValueError("프로토콜")
    if type(row["port"]) is not int or not 1 <= row["port"] <= 65535:
        raise ValueError("포트")
    source = row["source"]
    if not isinstance(source, str) or "%" in source:
        raise ValueError("주소")


def load_model(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"rules", "requests"}:
        raise ValueError("최상위 필드")
    rules, requests = [], []
    for key, limit in (("rules", 100), ("requests", 1000)):
        rows = data[key]
        if not isinstance(rows, list) or not 1 <= len(rows) <= limit:
            raise ValueError("목록 크기")
        seen = set()
        for row in rows:
            fields = {"id", "source", "protocol", "port"}
            if key == "rules":
                fields.add("action")
            checked_endpoint(row, fields)
            if row["id"] in seen:
                raise ValueError("중복 이름")
            seen.add(row["id"])
            if key == "rules":
                if row["action"] not in ("allow", "deny") or "/" not in row["source"]:
                    raise ValueError("규칙")
                network = ipaddress.ip_network(row["source"], strict=True)
                rules.append(dict(row, network=network))
            else:
                address = ipaddress.ip_address(row["source"])
                requests.append(dict(row, address=address))
    return rules, requests


def decide(rules, request):
    address = request["address"]
    for number, rule in enumerate(rules, 1):
        if address.version != rule["network"].version:
            continue
        if (address not in rule["network"]
                or request["protocol"] != rule["protocol"]
                or request["port"] != rule["port"]):
            continue
        return rule["action"], f"규칙 {number}={rule['id']}"
    return "deny", "기본 정책"


def main():
    parser = argparse.ArgumentParser(description="가상 IP·프로토콜·포트 접근표 비교")
    parser.add_argument("input", type=Path)
    parser.add_argument("--swap-first-two", action="store_true")
    args = parser.parse_args()
    try:
        rules, requests = load_model(args.input)
        if args.swap_first_two:
            if len(rules) < 2:
                raise ValueError("교환할 규칙 부족")
            rules = [rules[1], rules[0], *rules[2:]]
    except (OSError, UnicodeError, ValueError, TypeError):
        print("입력 오류: JSON·필드·CIDR·프로토콜·포트·규칙 수를 살핀다", file=sys.stderr)
        return 2
    print("규칙 순서: " + ", ".join(rule["id"] for rule in rules))
    allowed = 0
    for request in requests:
        action, reason = decide(rules, request)
        allowed += action == "allow"
        label = "허용" if action == "allow" else "거부"
        print(f"{request['id']}: 가상 {label}; {reason}")
    print(f"가상 요청 {len(requests)}건: 허용 {allowed}건, 거부 {len(requests) - allowed}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`load_model()`은 규칙과 요청의 필드·이름 중복·프로토콜·포트를 모두 검사한 뒤 반환한다. 포트에 불리언을 받지 않도록 `type(row["port"]) is int`를 사용한다. 주소는 문자열만 받으며 IPv6 영역 식별자가 붙은 `%` 표기는 이 모형에서 거부한다. 형식이 틀린 행이 있으면 일부 요청만 처리한 결과를 먼저 출력하지 않는다.

[Python ipaddress](https://docs.python.org/3.12/library/ipaddress.html)의 `ip_network(..., strict=True)`는 네트워크 주소에 호스트 비트가 남아 있으면 오류를 낸다. 예를 들어 `192.0.2.13/25`를 규칙에 넣으면 `192.0.2.0/25`로 조용히 바꾸지 않고 입력 오류로 끝난다. `ip_address()`는 요청의 단일 주소를 `address`에 저장한다.

`admin-host`를 따라가면 `address`는 `192.0.2.14`다. `decide()`의 첫 규칙은 `/32`의 `192.0.2.13`과 달라 다음 규칙으로 넘어간다. 두 번째에서는 IPv4 계열이 같고 주소가 `192.0.2.0/25`에 속하며 `tcp`와 `22`가 모두 일치한다. 함수는 `allow`와 `규칙 2=admin-net`을 반환해 뒤의 규칙을 더 검사하지 않는다.

[[run:1]]

`same-ip-other-port`는 같은 출발지여도 목적지 `443`이 규칙의 `22`와 달라 기본 거부다. `udp-same-port`는 숫자 `22`가 같아도 프로토콜이 달라 기본 거부로 남는다. 이 UDP 요청을 SSH 접속의 관찰값으로 해석하지 않는다.

`outside-half`의 `192.0.2.130`은 `/25` 범위 밖이다. IPv6 요청 두 건도 `v6-admin`은 해당 IPv6 범위에서 허용되고 `v6-other`는 기본 거부됐다. `allowed`는 반환값이 `allow`일 때만 1씩 늘고 전체 요청 수에서 그 값을 빼 거부 건수를 만든다. 마지막의 허용 3건·거부 5건은 가상 요청 여덟 개의 분류이며 거부 다섯 개 중 하나는 명시 규칙, 나머지 네 개는 기본 정책에서 나왔다.

## 앞선 허용 규칙이 거부를 가릴 때

다음 명령은 원본 JSON을 다시 읽은 뒤 메모리의 첫 두 규칙만 교환한다. 파일을 편집하거나 앞의 실행 상태를 이어받지 않는다. 그 밖의 규칙 세부값과 요청 여덟 개는 같다.

```bash
python -I -B -X utf8 u28_access_model.py u28_access_cases.json --swap-first-two
```

`--swap-first-two`가 있으면 `main()`은 `rules[1]`, `rules[0]`, 나머지 규칙의 순서로 새 목록을 만든다. 교환할 규칙이 두 개보다 적으면 입력 오류로 끝난다.

[[run:2]]

`blocked-host`가 이제 `규칙 1=admin-net`에서 가상 허용으로 바뀌었다. `192.0.2.13`은 넓은 `/25` 범위에도 들어가기 때문에 첫 허용에서 반환하고 뒤로 밀린 `block-one`까지 도달하지 않는다. 나머지 일곱 요청의 허용·거부는 같아 허용 4건·거부 4건이 됐다. `admin-host`가 고른 규칙도 계속 `admin-net`이지만 목록의 위치가 바뀌어 출력 번호는 2에서 1로 달라졌다.

[[diagram]]

이 모형은 일치하면 계산을 끝내는 허용·거부만 다룬다. [iptables(8)](https://man7.org/linux/man-pages/man8/iptables.8.html)의 실제 체인에는 사용자 정의 체인으로 이동하는 동작이나 `RETURN` 등도 있다. 실제 방화벽의 인터페이스·방향·연결 추적·NAT·다른 체인과 훅은 이 입력에 없으며 운영 정책의 효과는 해당 구성까지 대조해 판단한다.

두 명령의 종료 0은 입력 검사와 가상 요청 계산이 끝났다는 뜻이다. 가상 거부도 정상적인 계산 결과다. 파일 읽기 실패, 잘못된 JSON·CIDR·필드·프로토콜·포트는 표준 오류와 종료 2로 알린다. 오류가 나면 지정한 JSON 경로와 해당 입력 조건을 살핀다.

## 가이드의 도구와 현재 적용 환경 대조하기

가이드에는 TCP Wrapper의 `hosts.allow`, `hosts.deny`와 SSH 예시가 있다. 다만 [OpenSSH 6.7 릴리스 기록](https://www.openssh.org/txt/release-6.7)은 `sshd`의 tcpwrappers/libwrap 지원 제거를 명시한다. 파일이 존재한다는 사실만으로 설치된 SSH가 그 파일을 읽는다고 가정하지 않고 해당 구현·버전·배포판의 지원 여부를 조사한다.

58쪽의 iptables 사례는 ‘설정한 접근제한 정책 적용’ 아래에 `iptables-save`를 적고 있다. [iptables-save(8)](https://man7.org/linux/man-pages/man8/iptables-save.8.html)에 따르면 이 명령은 현재 규칙을 내보내며 파일을 지정하지 않으면 표준 출력으로 보낸다. 규칙 내보내기와 재부팅 뒤의 영구 적용 절차는 구분해야 한다. 운영체제가 사용하는 규칙 관리 도구, 실행 중인 규칙과 저장된 구성의 대응을 함께 남긴다.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [Python 3.12 ipaddress: 주소·네트워크와 엄격한 CIDR 해석](https://docs.python.org/3.12/library/ipaddress.html)
- [Netfilter iptables(8): 규칙·체인·동작](https://man7.org/linux/man-pages/man8/iptables.8.html)
- [Netfilter iptables-save(8): 규칙 내보내기](https://man7.org/linux/man-pages/man8/iptables-save.8.html)
- [OpenSSH 6.7: tcpwrappers/libwrap 지원 제거](https://www.openssh.org/txt/release-6.7)
