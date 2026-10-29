import importlib.util
from pathlib import Path


source = Path(__file__).with_name("09-shipping-rules.py")
spec = importlib.util.spec_from_file_location("shipping_rules", source)
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)


def main():
    values = [49999, 50000, 50001]
    result = [rules.shipping_fee(value) for value in values]
    assert result == [3000, 0, 0]
    print(f"q3: {values} -> {result}")
    assert rules.transition("DRAFT", "cancel") == "CANCELLED"
    try:
        rules.transition("CANCELLED", "pay")
    except ValueError as error:
        print(f"q4: CANCELLED + pay, 예상한 거부: {error}")
    else:
        raise AssertionError("잘못된 전이를 허용했다")
    normal = [rules.shipping_fee(10000), rules.shipping_fee(60000)]
    assert normal == [3000, 0]
    print(f"q5: 정상 금액 두 건 -> {normal}")
    try:
        rules.shipping_fee(-1)
    except ValueError as error:
        print(f"q5: -1, 예상한 거부: {error}")
    else:
        raise AssertionError("잘못된 금액을 허용했다")
    print("문제 3~5의 가상 계산 대조 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
