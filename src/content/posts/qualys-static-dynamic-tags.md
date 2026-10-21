---
title: "Qualys 자산 태그 읽기: 정적 분류와 동적 규칙"
description: "정적 목록과 동적 규칙의 차이를 가상 자산 세 개로 비교하고 태그 재평가 시점을 짚습니다."
date: "2026-10-16T21:58:01+09:00"
updated: "2026-10-21"
sourcesChecked: "2026-10-16"
category: "qualys"
tags: ["Qualys", "자산관리", "태그", "점검범위"]
draft: false
example: false
---

‘운영 Linux’ 태그에 Windows 자산이 들어 있다면 이름보다 태그 종류를 먼저 살펴본다. 정적 태그는 누가 어떤 목적으로 자산을 넣었는지, 동적 태그는 어떤 규칙과 자산 정보로 분류했는지가 조사 대상이다.

VM/VMDR과 GAV의 태그 지정·재평가 방식을 정리하고, 작은 Python 예제로 고정 목록과 조건 목록이 달라지는 경우를 비교한다.

## 이름보다 태그 종류와 규칙을 확인한다

| 종류 | 분류 근거 | 목록이 예상과 다를 때 확인할 것 |
| --- | --- | --- |
| 정적 태그 | 자산에 직접 지정한 내역 | 지정 대상, 담당자, 이후 자산 용도 변경 |
| 동적 태그 | 저장된 자산 정보와 태그 규칙 | 규칙 조건, 입력 정보, 평가 상태와 시점 |
| 시스템 생성 태그 | Asset Group 등 연결된 제품 객체 | 원래 객체와 연결 관계, 제품별 동작 |

정적 태그에는 자산을 자동 분류하는 규칙이 없다. 담당자가 수동으로 묶은 업무 목록처럼 사용할 수 있지만, 이름에 ‘Linux’가 들어 있다고 운영체제 조건을 검사하는 것은 아니다.

동적 태그는 자산 정보가 규칙에 맞는지 평가해 적용한다. Qualys의 `Manage Tags` 문서는 자산 이름, IP 범위, 열린 포트, 자산 검색 등 여러 규칙을 설명한다. 다만 규칙별로 구독 조건이 있다. 이 문서에서는 `Vulnerability Detection Searches`를 제외한 규칙에 VMDR와 GAV/CSAM 또는 VM과 CSAM의 구독 조합을 명시한다. 실제 사용할 앱과 계약의 지원 범위를 확인해야 한다.

여기서 취약점 탐지에 붙이는 태그와 자산에 붙이는 태그를 구분한다. 같은 태그 화면에서 보이더라도 분류하는 대상이 다르면 ‘태그에 포함된 자산 수’로 바로 해석할 수 없다.

## 수정 직후의 목록을 최종 결과로 보지 않는다

규칙을 바꾼 직후 자산 목록이 그대로라고 해서 곧바로 규칙 오류라고 판단하기는 어렵다. GAV 문서는 재평가에 시간이 걸릴 수 있고 `REEVAL STATUS`에서 진행 여부를 확인할 수 있다고 설명한다. 생성·수정 시의 평가 옵션과 이후 수집 데이터에 의한 평가도 함께 확인한다.

태그를 비교할 때는 규칙, 자산 정보의 수집 시점, 재평가 완료 여부와 조회 시각을 함께 남긴다. 규칙이 최신이어도 운영체제 정보가 오래됐다면 현재 상태와 다르게 분류될 수 있다. 예상과 다른 자산 몇 개에서 조건에 쓰인 속성을 살펴보면 원인을 좁힐 수 있다.

스캔에 태그를 쓸 때는 평가된 자산 목록을 스캔의 대상·제외 조건, 사용자의 자산 접근 범위와 대조한다. 규칙 테스트는 분류 결과를 보여 줄 뿐 실제 검사를 수행하지 않는다. 포함·제외 조건의 의미는 사용 중인 제품과 화면의 문서를 따른다.

[[diagram]]

## 작은 가상 목록으로 차이를 확인한다

다음 Python 예제는 세 개의 가상 자산을 사용한다. 정적 목록은 `lab-01`, `lab-02`를 직접 지정했고, 별도의 비교 함수는 운영체제가 Linux이면서 환경이 `prod`인 자산을 고른다.

이 조건식은 **분류 개념을 설명하는 독립적인 Python 코드**다. Qualys의 QQL 문법, 태그 엔진, 동기화 방식이나 API 응답 형식을 재현한 것은 아니다. 자격 증명이나 네트워크 연결도 사용하지 않는다.

[compare_tags_demo.py](../../downloads/compare_tags_demo.py)를 내려받거나 아래 코드로 저장한 뒤, 같은 폴더에서 `python3 compare_tags_demo.py`로 실행한다. Python 3의 `json`·`re` 표준 라이브러리만 사용한다. 자산 파일을 따로 만들거나 실제 호스트 이름으로 값을 바꿀 필요는 없다.

```python
import json
import re


def compare(assets, assigned):
    by_id = {}
    for asset in assets:
        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not re.fullmatch(r"lab-[0-9]{2}", asset_id):
            raise ValueError("가상 자산 ID 형식 오류")
        if asset_id in by_id:
            raise ValueError("중복 자산 ID")
        if asset.get("os") not in {"Linux", "Windows"}:
            raise ValueError("운영체제 정보 확인 필요")
        if asset.get("environment") not in {"prod", "dev"}:
            raise ValueError("환경 정보 확인 필요")
        by_id[asset_id] = asset
    static_ids = set(assigned)
    if static_ids - by_id.keys():
        raise ValueError("정적 목록에 자료가 없는 자산 포함")
    dynamic_ids = {
        asset_id for asset_id, asset in by_id.items()
        if asset["os"] == "Linux" and asset["environment"] == "prod"
    }
    return {
        "직접 지정한 목록": sorted(static_ids),
        "Linux와 prod 조건에 맞는 목록": sorted(dynamic_ids),
        "직접 지정했지만 조건과 다른 자산": sorted(static_ids - dynamic_ids),
        "조건에 맞지만 직접 지정하지 않은 자산": sorted(dynamic_ids - static_ids),
    }


if __name__ == "__main__":
    assets = [
        {"id": "lab-01", "os": "Linux", "environment": "prod"},
        {"id": "lab-02", "os": "Windows", "environment": "prod"},
        {"id": "lab-03", "os": "Linux", "environment": "dev"},
    ]
    assigned = {"lab-01", "lab-02"}
    result = compare(assets, assigned)
    assert result["직접 지정했지만 조건과 다른 자산"] == ["lab-02"]
    print(json.dumps(result, ensure_ascii=False, indent=2))

    changed = [dict(asset) for asset in assets]
    changed[2]["environment"] = "prod"
    assert compare(changed, assigned)["조건에 맞지만 직접 지정하지 않은 자산"] == ["lab-03"]
    print("lab-03의 가상 환경 값을 prod로 변경: 조건 목록에 추가")

    missing_os = [dict(asset) for asset in assets]
    missing_os[0].pop("os")
    for label, data, selected in [
        ("속성 누락", missing_os, assigned),
        ("중복 ID", assets + [dict(assets[0])], assigned),
        ("자산 자료 누락", assets, {"lab-99"}),
    ]:
        try:
            compare(data, selected)
        except ValueError:
            print(f"{label}: 비교 중단")
        else:
            raise AssertionError(f"{label} 검증 실패")
```

`compare()`는 먼저 자산을 ID로 찾는 `by_id` 딕셔너리를 만든다. ID 형식·중복·운영체제·환경을 검사한 뒤, 직접 지정한 ID가 모두 자료에 있는지도 대조한다. 이 검사가 끝나야 Linux·prod 조건의 집합을 계산한다.

반환하는 네 목록은 두 집합과 양방향 차집합이다. `static_ids - dynamic_ids`는 직접 지정했지만 조건 밖인 자산이고, 반대 방향의 뺄셈은 조건에 맞지만 직접 지정하지 않은 자산이다. 출력 순서가 매번 같도록 집합을 정렬한 뒤 JSON으로 표시한다.

[[run:1]]


첫 자료에서 조건에 맞는 자산은 `lab-01` 하나이며, 정적 목록에 남은 Windows 자산은 `lab-02`다. 어느 쪽이 잘못됐는지는 업무 목적에 따라 달라진다. 정적 태그가 ‘월간 점검 계약 대상’을 뜻한다면 Windows 자산을 포함하는 것이 맞을 수도 있다.

`lab-03`의 환경을 `prod`로 바꿔 함수를 다시 호출하면 조건 목록에 이 자산이 추가된다. 직접 지정한 정적 목록은 그대로 남는다. 재계산은 이 Python 함수의 동작이며 Qualys의 평가 시점과는 관계없다.

아래의 `비교 중단` 세 줄은 프로그램 전체의 비정상 종료가 아니다. 일부러 준비한 속성 누락·중복 ID·존재하지 않는 지정 ID가 각각 `ValueError`를 일으켜야 하는 시험이다. 오류가 나지 않으면 오히려 `AssertionError`로 실패한다. 정상 비교와 오류 거부가 모두 기대값과 같으면 종료 코드 0이 된다.

`changed`와 `missing_os`는 각 자산 딕셔너리를 복사한 목록이다. 변경용 목록에서 값을 바꾸거나 속성을 지워도 처음 JSON에 쓴 원본 자료는 그대로 둔다.

속성이 없거나 자료가 불완전하면 예제는 비교를 중단한다. 제품에서 누락 속성을 처리하는 방식은 이 코드와 같다고 가정하지 않는다. 실제 목록을 대조할 때도 정보가 빠진 자산을 단순히 ‘조건 불일치’나 ‘점검 대상 아님’으로 분류하지 말고 누락 원인을 확인한다.

## 태그의 목적과 조회 시점의 자산 목록을 보관한다

업무상 고정된 책임 범위를 표현하려면 정적 태그가 이해하기 쉬울 수 있다. 반대로 운영체제·설치 소프트웨어처럼 관찰 정보에 따라 분류할 때는 동적 규칙이 유용하다. 실제 태그를 고를 때는 변경 빈도와 담당자, 정보 수집 경로를 함께 고려한다.

태그에는 분류 목적과 기준을 적고, 점검에 사용한 자산 목록은 조회 시각과 함께 보관한다. 목록이 바뀐 뒤에도 당시의 점검 대상을 알 수 있어야 한다. 태그 수정 전에는 이후 스캔·보고서에 포함될 자산이 어떻게 달라지는지 검토한다.

분류 규칙을 공유할 때는 예제처럼 가상 자산 이름을 사용한다. 실제 호스트 이름·IP와 태그에 들어 있는 조직·서비스 정보는 공개할 자료에서 제외한다.

## 공식 참고 자료

- [VM/VMDR: Manage Tags(정적·동적 태그, 규칙별 구독 조건)](https://docs.qualys.com/en/vm/latest/mergedProjects/analyze_reports_and_dashboards/assets/manage_tags.htm)
- [GAV: Manage Asset Tags(지정 방식과 재평가 상태)](https://docs.qualys.com/en/gav/latest/Tags/manage_your_tags.htm)
