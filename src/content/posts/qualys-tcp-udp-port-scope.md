---
title: "Qualys 포트 범위 대조: TCP·UDP와 호스트 탐색 나눠 보기"
description: "옵션 프로필의 서비스 포트와 Host Discovery 설정을 구분하고 가상 목록에서 TCP·UDP별 빠진 조합을 찾습니다."
date: "2026-10-19T18:33:58+09:00"
updated: "2026-10-22"
sourcesChecked: "2026-10-19"
category: "qualys"
tags: ["Qualys","VMDR","Option Profile","TCP","UDP"]
draft: false
example: false
---

서비스 목록에 TCP 8443이 있는데 Qualys 검사 결과에는 해당 서비스가 보이지 않는다면, 옵션 프로필의 포트 목록과 목록을 수집한 시점을 대조할 수 있다. 호스트가 응답했다는 정보만으로 TCP 8443까지 검사했다고 판단할 수는 없다.

VM/VMDR의 옵션 프로필은 호스트를 찾는 설정과 서비스 포트 검사 설정을 나눠 제공한다. 여기서는 두 설정의 역할과 TCP·UDP 범위를 구분해 읽고, 작은 가상 서비스 목록으로 빠진 조합을 찾아본다.

## Scan 탭의 TCP와 UDP를 따로 읽는다

VM 옵션 프로필의 Scan 문서는 TCP와 UDP의 포트 선택을 각각 설명한다. Standard가 기본이며 Full, 더 적은 포트를 쓰는 Light Scan, Additional 목록 등을 선택할 수 있다. 목록에 서비스가 들어 있는지는 해당 프로필과 실제 사용 시점의 구성을 기준으로 대조한다.

TCP 53과 UDP 53은 같은 숫자를 쓰더라도 서로 다른 검사 대상이다. 포트 번호만 모아 비교하면 UDP 53을 선택했다는 사실 때문에 TCP 53도 포함됐다고 오해할 수 있다. 자료를 `(프로토콜, 포트)` 쌍으로 유지하면 이 차이가 드러난다.

| 대조할 자료 | 구분할 값 |
| --- | --- |
| 서비스 명단 | 프로토콜과 포트, 그 정보를 얻은 시점 |
| Scan 탭 | TCP 선택 방식·목록과 UDP 선택 방식·목록 |
| Additional 탭 | 호스트 탐색에 사용하는 응답·포트 조건 |
| 실제 작업 | 사용한 프로필, 검사 대상, 결과와 미검사 사유 |

‘서비스 목록에 포함됨’, ‘옵션 목록에 포함됨’, ‘열린 포트로 관찰됨’은 각각 다른 사실이다. 아래 실습은 그중 앞의 두 목록만 비교한다.

## 가상 서비스 네 개를 선택 목록과 대조한다

ZIP의 `qualys_port_scope.py`를 사용하거나 아래 코드를 같은 이름으로 저장한다. Python 3만 있으면 되며 별도 입력 파일·패키지·제품 계정은 필요 없다. 저장한 폴더에서 `python -I -B -X utf8 qualys_port_scope.py`로 실행한다.

비교할 가상 서비스는 TCP 443·8443·53, UDP 53이다. 선택 목록에는 TCP 22·443, UDP 53을 넣었다고 가정했다. 이 값은 설명용 사용자 지정 목록이며 Qualys의 Standard 또는 Light 기본 목록을 복제한 것이 아니다.

코드는 메모리의 집합을 비교한다. 실제 호스트, 포트, 제품 API에 요청을 보내지 않으며 열린 포트나 취약점 탐지를 재현하지 않는다. 입력 형식이 잘못됐을 때도 번호만 남기고 처리하지 않도록 검사를 넣었다.

[[download]]

```python
def endpoints(rows):
    result = set()
    for protocol, port in rows:
        if protocol not in {"tcp", "udp"}:
            raise ValueError("프로토콜은 tcp 또는 udp여야 함")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("포트는 1~65535 정수여야 함")
        result.add((protocol, port))
    return result


services = endpoints([("tcp", 443), ("tcp", 8443), ("tcp", 53), ("udp", 53)])
selected = endpoints([("tcp", 22), ("tcp", 443), ("udp", 53)])
missing = services - selected
assert missing == {("tcp", 53), ("tcp", 8443)}
assert ("udp", 53) in selected
assert ("tcp", 53) not in selected
assert endpoints([("tcp", 443), ("tcp", 443)]) == {("tcp", 443)}
for invalid in [[("icmp", 53)], [("tcp", 0)], [("udp", 65536)], [("tcp", True)]]:
    try:
        endpoints(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("잘못된 프로토콜·포트를 거부해야 함")

for protocol, port in sorted(services):
    scope = "선택 목록에 포함" if (protocol, port) in selected else "선택 목록 밖"
    print(f"{protocol}/{port}: {scope}")
print("목록에 빠진 조합:", ", ".join(f"{p}/{n}" for p, n in sorted(missing)))
revised = selected | missing
assert services <= revised
assert selected == endpoints([("tcp", 22), ("tcp", 443), ("udp", 53)])
print("가상 목록 보완 후 빠진 조합 수:", len(services - revised))
```

`endpoints()`는 각 행을 프로토콜과 포트 쌍으로 읽어 집합에 넣는다. 프로토콜은 소문자 `tcp`·`udp`, 포트는 1~65,535의 정수만 받는다. `type(port) is int`로 검사하므로 Python에서 정수처럼 쓰일 수 있는 `True`도 거부한다. 같은 쌍이 반복되면 집합에 하나만 남는다.

`missing = services - selected`는 기대 서비스 중 선택 목록에 없는 쌍을 구한다. 출력은 `services`를 순회하므로 선택 목록에만 있는 TCP 22는 네 서비스의 결과 줄에 나오지 않는다. 정렬은 출력 순서를 고정할 뿐 비교 기준을 바꾸지 않는다.

`revised = selected | missing`은 새 집합을 만들어 빠진 쌍을 더한다. 기존 TCP 22도 남기므로 `services <= revised`는 기대 서비스가 모두 들어 있다는 부분집합 검사다. 두 집합이 완전히 같다는 검사가 아니다. 마지막 `assert`는 원래 `selected`를 바꾸지 않았는지도 대조한다.

[[run:1]]

출력에서 TCP 53·8443이 선택 목록 밖으로 나왔고 UDP 53은 포함됐다. 가상 목록을 보완한 뒤 누락 수는 0이지만, 이는 입력한 네 조합을 모두 포함했다는 의미다. 패킷 전송·서비스 응답·인증·QID 실행에 대한 결과는 이 계산에 없다.

잘못된 프로토콜, 범위 밖 포트 두 개, 불리언 포트는 출력 전에 일부러 넣은 거부 시험이다. 이 입력들이 `ValueError`를 일으키고 집합·차집합 검사가 통과하면 종료 코드 0이 된다. 예상한 오류를 잡아 처리하므로 정상 실행에서 오류 메시지가 따로 나오지는 않는다. 검사를 유지하려면 `-O` 없이 실행한다.

실제 조사에서는 검사해야 할 서비스 목록도 최신인지 살핀다. 폐기된 포트가 명단에 남거나 최근 추가한 서비스가 빠졌다면, 두 목록의 차이를 곧바로 검사 누락으로 해석하기 어렵다. 변경 전후 목록의 조회 시점과 대상 자산을 맞춰 비교한다.

## 호스트 탐색에 쓴 포트와 서비스 검사 포트는 역할이 다르다

Additional 탭의 Host Discovery는 ICMP·TCP·UDP 탐색 응답으로 호스트의 살아 있음을 판단하는 설정이다. 공식 문서는 이 설정을 바꾸면 살아 있는 호스트를 놓칠 수 있고, 탐색에서 빠진 호스트는 취약점 검사까지 진행되지 않을 수 있다고 설명한다.

[[diagram]]

TCP 탐색 응답을 받았다는 사실이 Scan 탭의 모든 TCP·UDP 서비스를 시험했다는 뜻은 아니다. 결과를 조사할 때는 먼저 대상이 발견됐는지, 그다음 필요한 프로토콜·포트가 선택됐는지와 실제로 무엇을 검사했는지 나눠 읽는다.

Scan 문서는 선택 목록에 없는 포트로도 OS 탐색 등 다른 목적의 트래픽이 생길 수 있다고 설명한다. 포트 목록을 방화벽의 허용 목록처럼 취급하지 않는다. 어떤 통신이 허용되는지를 결정하는 네트워크 정책과 검사 옵션을 별도로 검토해야 한다.

## 포트를 넓히기 전에 작업의 조건을 맞춘다

실제 스캔 범위를 늘리는 조치는 허가된 대상과 점검 시간, 서비스 영향을 검토한 뒤 정한다. 이 예제에서 `revised`를 계산한 동작은 실제 프로필을 변경하거나 재스캔을 시작한 작업이 아니다. 프로필을 공유하는 예약 작업이 있다면 어느 작업의 TCP·UDP 목록까지 바뀌는지 먼저 조사한다.

프로필 변경 전에는 사용하는 VM/VMDR 앱과 계정에 부여된 편집 권한을 대조한다. 여기서 다룬 것은 네트워크 스캐너의 VM 옵션이며 Cloud Agent의 모든 평가에 같은 포트 선택이 적용된다고 가정하지 않는다.

Full UDP도 무조건 모든 포트를 끝까지 검사한다는 뜻으로 읽지 않는다. 공식 Scan 문서는 방화벽의 UDP 차단·드롭이나 ICMP 응답 속도 제한 때문에 전체 검사가 비현실적인 경우 기본 UDP 포트의 Standard 검사로 전환한다고 설명한다. 원하는 설정값과 처리된 실제 결과를 함께 남겨야 이 차이가 보인다.

변경 전후 비교에는 대상 자산, 프로필 이름과 TCP·UDP 목록, Host Discovery 조건, 검사 시각과 미검사 사유를 묶는다. 포트를 포함한 뒤에도 결과가 없다면 인증 결과와 해당 QID의 적용 조건으로 조사를 이어 간다.

## 참고 자료

- [Qualys VM: Option Profile Scan의 TCP·UDP 포트 설정](https://docs.qualys.com/en/vm/latest/option_profiles/op_scan_tab.htm)
- [Qualys VM: Additional Settings와 Host Discovery](https://docs.qualys.com/en/vm/latest/option_profiles/op_additional_tab.htm)
