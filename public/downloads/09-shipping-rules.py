import argparse


def shipping_fee(amount):
    if type(amount) is not int:
        raise TypeError("금액은 정수여야 한다")
    if not 0 <= amount <= 100000:
        raise ValueError("금액 범위는 0~100000이다")
    return 0 if amount >= 50000 else 3000


def transition(state, event):
    edges = {
        ("DRAFT", "pay"): "PAID",
        ("DRAFT", "cancel"): "CANCELLED",
        ("PAID", "ship"): "SHIPPED",
        ("PAID", "cancel"): "CANCELLED",
    }
    if (state, event) not in edges:
        raise ValueError("허용하지 않은 상태 전이")
    return edges[state, event]


def main():
    parser = argparse.ArgumentParser(description="가상 배송비와 주문 상태를 계산한다")
    parser.add_argument("example", choices=("fees", "states"))
    args = parser.parse_args()
    if args.example == "fees":
        for amount in (-1, 0, 49999, 50000, 100000, 100001):
            try:
                print(f"금액={amount}, 배송비={shipping_fee(amount)}")
            except ValueError as error:
                print(f"금액={amount}, 예상한 거부: {error}")
    else:
        state = "DRAFT"
        for event in ("pay", "ship", "cancel"):
            try:
                after = transition(state, event)
                print(f"{state} + {event} -> {after}")
                state = after
            except ValueError as error:
                print(f"{state} + {event} -> 예상한 거부: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
