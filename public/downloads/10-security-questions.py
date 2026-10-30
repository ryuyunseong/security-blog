import hmac
import importlib.util
from pathlib import Path


source = Path(__file__).with_name("10-security-models.py")
spec = importlib.util.spec_from_file_location("security_models", source)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)


def main():
    test_key, message = models.test_vector()
    tag = models.tag_for(test_key, message)
    repeated = [hmac.compare_digest(tag, models.tag_for(test_key, message)) for _ in range(2)]
    assert repeated == [True, True]
    print(f"q2: 같은 메시지와 태그 두 번 대조 -> {repeated}")
    document = {"id": 9, "owner": 1002}
    actor = {"id": 1002, "role": "unknown"}
    result = models.can_read(actor, document)
    assert result is False
    print(f"q3: 소유자 일치·알 수 없는 역할 -> {result}")
    plain = models.lookup_id("bob")
    injected = models.lookup_id("bob' OR 1=1 --")
    assert plain == [2] and injected == []
    print(f"q4: bob -> {plain}, 조건처럼 보이는 전체 이름 -> {injected}")
    print("문제 2~4의 가상 계산 대조 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
