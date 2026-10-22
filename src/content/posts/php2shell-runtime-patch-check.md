---
title: "PHP2Shell 대응: 수정 버전과 웹 서버의 PHP 실행 환경 점검"
description: "CVE-2026-109618·109619의 원인과 수정 버전을 살피고, 업스트림·배포판 패키지·CLI 기록을 구분하는 가상 목록 실습을 진행합니다."
date: "2026-10-22T19:25:52+09:00"
sourcesChecked: "2026-10-22"
category: "cve"
tags: ["PHP", "PHP2Shell", "CVE-2026-109618", "CVE-2026-109619", "PHP-FPM"]
draft: false
example: false
---

터미널에서 PHP 버전을 조회했는데, 그 값으로 웹 서비스의 업데이트 여부까지 판단해도 될까? 같은 서버에서도 터미널의 PHP와 웹 서버에 연결된 PHP가 다를 수 있다. 배포판 패키지는 원래 버전 번호를 유지하면서 보안 패치를 적용하기도 하므로 서비스가 사용하는 PHP와 공급 경로부터 찾아야 한다.

PHP2Shell은 PHP의 **CVE-2026-109618과 CVE-2026-109619**를 함께 부르는 이름이다. [네덜란드 NCSC의 대응 자료](https://github.com/NCSC-NL/php2shell)도 이 두 식별자로 안내한다. PHP 프로젝트는 2026년 10월 21일 수정 릴리스를 공개했다.

## 요청 종료와 다음 요청 사이에서 생기는 문제

두 취약점은 인증 없이 웹 워커 권한의 코드 실행으로 이어질 수 있다. 다만 취약한 메모리 상태가 만들어지고 사용되는 과정은 서로 다르다.

| 식별자 | 원인 | 공식 권고에서 구분한 실행 조건 |
| --- | --- | --- |
| CVE-2026-109618 | 메모리 부족 처리 중 조기 탈출로 내부 자료가 불완전한 상태에 남음 | mod_php에서 애플리케이션 코드 실행 전 HTTP 공격이 검증됨. FPM의 영향은 해당 권고에서 소스 분석으로 설명 |
| CVE-2026-109619 | 요청 메모리가 해제된 뒤에도 워커가 이전 상태를 참조 | mod_php 및 FPM의 세션 생명주기 경로가 검증됨. FPM은 적절한 애플리케이션 동작 등 조건이 필요 |

[OOM corruption 권고](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w)에서 OOM은 메모리 부족을 뜻한다. PHP가 `longjmp()`로 현재 처리를 빠져나간 뒤, 요청 종료 과정이 아직 초기화되지 않은 자료를 정상 자료처럼 사용할 수 있다는 설명이다. mod_php에서 검증된 공격은 애플리케이션의 로그인 검사보다 앞에서 발생한다.

[Stale global state 권고](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp)는 요청에 쓰던 메모리를 해제한 뒤에도 워커가 그 메모리를 가리키는 참조를 보관하는 문제다. 같은 워커가 다음 요청의 초기화 전에 남은 참조를 사용하면, 이미 해제한 메모리에 다시 접근하는 use-after-free로 이어진다.

아래는 두 번째 취약점의 요청 간 관계다. 앞 요청과 뒤 요청이 같은 워커에서 처리되는 조건을 함께 읽어야 한다.

[[diagram]]

PHP 프로젝트의 [보안 공지](https://www.php.net/archive/2026.php)는 PHP-FPM, Apache mod_php, php-cgi, FrankenPHP, LiteSpeed 등 웹 요청을 처리하는 PHP 설치를 점검 대상으로 안내한다. 개별 공격 경로가 검증된 범위와 전체 업데이트 권고 범위를 구별하자.

## 어느 버전으로 올려야 하나

다음은 두 CVE의 패치가 처음 포함된 PHP 프로젝트의 정식 릴리스다. 해당 계열에서 이 버전 이상을 사용하되, 이후 보안 릴리스가 있다면 그 내용도 함께 살핀다.

| PHP 계열 | 수정 릴리스 |
| --- | --- |
| 8.2 | 8.2.35 |
| 8.3 | 8.3.36 |
| 8.4 | 8.4.27 |
| 8.5 | 8.5.12 |

배포판이나 LTS 업체 패키지는 공급업체의 두 CVE 공지와 **패키지 릴리스 번호**로 대조한다. 화면에 `8.2.30`이 보인다는 이유만으로 백포트 적용 여부를 결정할 수는 없다. 반대로 업체 공지를 읽지 않은 상태에서 ‘백포트됐을 것’이라고 넘기지도 않는다.

PHP 8.1 이하는 PHP 프로젝트의 정기 지원이 끝난 계열이다. 이번 대응을 위한 일부 구형 계열의 최소 소스 백포트가 제공됐어도 정기 지원이 재개됐다는 뜻은 아니다. 공급업체 지원과 수정 패키지를 확인하거나 지원되는 계열로 이전해야 한다. 버전 표와 구형 계열 안내는 [PHP 공식 보안 공지](https://www.php.net/archive/2026.php)에 근거한다.

## 가상 목록에서 업데이트 대상을 분류하기

실습은 Python 3.9 이상과 표준 라이브러리만 사용한다. ZIP을 빈 폴더에 풀고 `php2shell_inventory.py`가 있는 폴더에서 `python -I -B -X utf8 php2shell_inventory.py`로 실행한다. Linux·WSL에서는 `python3`를 사용할 수 있다. PHP, 웹 서버, 외부 URL이나 별도 입력 파일은 필요하지 않다.

`SAMPLES`에는 이름·공급 경로·버전·기대 분류 순서로 가상 기록 여섯 개가 들어 있다. `upstream-web`은 웹 실행 환경에서 수집한 정식 업스트림 버전이라고 **가정한 입력**이다. `vendor`는 공급업체 패키지, `cli-only`는 CLI만 조사한 기록이다. 코드가 실제 설치 경로나 패치 적용을 수집하는 것은 아니다.

[[download]]

```python
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
```

`classify()`는 버전 숫자보다 공급 경로를 먼저 본다. `cli-only`는 웹 실행 환경이 빠져 있고, `vendor`는 업체별 패키지 판정이 필요하므로 숫자 비교에 넣지 않는다. 알 수 없는 공급 경로도 별도로 남긴다.

정식 업스트림 입력만 정규식으로 세 숫자를 나누고 `int`로 변환한다. 문자열의 사전 순서로 비교하면 `8.3.9`와 `8.3.36`의 순서를 틀릴 수 있다. 여기서는 `(8, 3)` 계열의 수정 기준 36과 패치 숫자 9를 비교한다. 표에 없는 새 계열이나 RC·업체 접미사가 붙은 값은 수정됐다고 추정하지 않는다.

`main()`은 각 분류가 기대값과 같은지 대조한 뒤 출력한다. 다르면 `AssertionError`로 중단한다. 파일을 쓰거나 프로세스를 시작하지 않으므로 실행 뒤 삭제할 임시 자료도 없다.

[[run:1]]

`web-a`의 8.3.35는 기준 36보다 낮아 업데이트 대상으로, `web-b`의 8.3.36은 버전 조건 충족으로 나왔다. 후자는 새 바이너리가 실제 웹 워커에 반영됐는지 조사하는 단계가 남는다. `web-c`의 업체 접미사는 임의로 잘라 버리지 않았고, `cli-a`는 새 버전이 적혀 있어도 웹 실행 환경 미수집으로 분류했다.

`legacy`는 구형 계열의 지원 경로를 살필 대상으로 남겼다. `preview`의 RC 문자열도 정식 버전 비교에 통과시키지 않았다. 마지막 ‘6건 분류 통과’와 종료 코드 0은 가상 입력의 분기 검사가 맞았다는 뜻이며 실제 서버의 안전 판정이 아니다. 표준 오류는 비어 있었다.

## 업데이트 작업에서 남길 정보

서비스별로 웹 서버 연결 방식, PHP 바이너리나 모듈 경로, 패키지 릴리스 또는 컨테이너 이미지 식별자, 적용한 보안 공지를 함께 적는다. CLI의 `php -v`는 그 명령이 실행한 바이너리를 보여 주므로 웹 요청을 맡는 FPM 풀이나 Apache 모듈과 대응시켜야 한다.

설정 파일도 실행 방식에 따라 달라질 수 있다. [PHP 설정 파일 문서](https://www.php.net/manual/en/configuration.file.php)는 SAPI별 설정 파일과 검색 경로를 설명한다. 갱신한 패키지가 어느 서비스에 연결되는지 파악한 뒤 해당 서비스의 절차로 기존 워커를 교체하고, 실행 중인 버전과 애플리케이션의 정상 요청을 다시 점검한다. 여러 풀·컨테이너가 있다면 각각 대조한다. 환경 정보 전체를 노출하는 `phpinfo()` 페이지를 공개 경로에 두는 방식은 피한다.

패치 전 임시 설정은 각 경로에만 효과가 있다. 두 번째 권고의 `session.upload_progress.enabled=0`은 검증된 세션 경로를 줄이지만 다른 상태의 생명주기 문제까지 해결하지 않는다. 설정은 요청 파싱 전에 적용돼야 하며 모든 워커 재시작이 필요하다. 오류 표시만 끄는 방식도 보호 수단이 아니다. [해당 권고의 완화 조건](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp)을 함께 읽어야 한다.

첫 번째 권고의 `memory_limit=-1` 역시 완전한 해결책이 아니고 메모리 사용 제한을 없애므로 가용성 대책이 함께 필요하다. 요청 크기 제한도 업데이트를 대신하지 않는다. [OOM 권고의 한계](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w)를 검토하고, 변경 가능한 설정만 골라 일괄 적용하기보다 수정 릴리스를 실제 웹 실행 환경에 반영하는 작업을 우선한다.
