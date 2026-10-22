import re

# PHP 8.2~8.5 정식 업스트림 릴리스의 두 CVE 수정 기준이다.
MINIMUM = {(8, 2): 35, (8, 3): 36, (8, 4): 27, (8, 5): 12}


def classify(source, version):
    if source == "cli-only":
        return "웹 실행 환경 미수집"
    if source == "vendor":
        return "공급업체 보안 공지 대조"
    if source != "upstream-web":
        return "공급 경로 미확인"
    match = re.fullmatch(r"([0-9]+)\.([0-9]+)\.([0-9]+)", version)
    if not match:
        return "정식 버전 형식 재검토"
    major, minor, patch = map(int, match.groups())
    branch = (major, minor)
    if branch < (8, 2):
        return "구형 계열 지원 경로 검토"
    minimum = MINIMUM.get(branch)
    if minimum is None:
        return "비교표 밖의 계열"
    if patch < minimum:
        return "업데이트 대상"
    return "수정 버전 조건 충족; 워커 반영 검토"


# 모두 가상 목록이다. 실제 PHP나 네트워크를 조회하지 않는다.
SAMPLES = (
    ("web-a", "upstream-web", "8.3.35", "업데이트 대상"),
    ("web-b", "upstream-web", "8.3.36", "수정 버전 조건 충족; 워커 반영 검토"),
    ("web-c", "vendor", "8.2.30-1.vendor1", "공급업체 보안 공지 대조"),
    ("cli-a", "cli-only", "8.5.12", "웹 실행 환경 미수집"),
    ("legacy", "upstream-web", "8.1.33", "구형 계열 지원 경로 검토"),
    ("preview", "upstream-web", "8.6.0RC4", "정식 버전 형식 재검토"),
)


def main():
    for name, source, version, expected in SAMPLES:
        result = classify(source, version)
        if result != expected:
            raise AssertionError(f"{name}: 기대={expected}, 실제={result}")
        print(f"{name} | {version} | {result}")
    print(f"가상 목록 {len(SAMPLES)}건 분류 통과")


if __name__ == "__main__":
    main()
