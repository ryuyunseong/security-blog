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
