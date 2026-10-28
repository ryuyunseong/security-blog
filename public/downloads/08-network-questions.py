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
