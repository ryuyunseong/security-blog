---
title: "Qualys 자산 태그 읽기: 정적 분류와 동적 규칙"
description: "정적 태그와 동적 규칙에 따라 자산 목록이 달라지는 이유와 변경 후 확인할 사항을 설명합니다."
date: "2026-10-16T21:58:01+09:00"
updated: "2026-10-17T10:29:06+09:00"
sourcesChecked: "2026-10-16"
category: "qualys"
tags: ["Qualys", "자산관리", "태그", "점검범위"]
draft: false
example: false
---

‘운영 Linux’라는 태그에 Windows 자산이 들어 있다. 이름을 잘못 붙인 걸까, 운영체제 정보가 바뀐 걸까. 태그가 정적인지 동적인지에 따라 먼저 볼 곳이 달라진다.

태그는 자산을 업무 단위로 묶는 수단이다. 같은 이름을 사용해도 지정 방식과 규칙, 평가 시점이 다르면 포함되는 자산은 달라질 수 있다. VM/VMDR과 GAV에서 태그를 지정하고 재평가하는 방식을 살펴보자.

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

실제로 비교할 때는 태그 이름만 캡처하지 않고 규칙 내용, 자산 정보의 수집 시점, 재평가 완료 여부, 조회 시각을 함께 남긴다. 규칙이 최신이어도 판단에 사용한 운영체제 정보가 오래됐다면 현재 자산 상태와 다르게 분류될 수 있다. 결과가 맞지 않는 자산 몇 개를 골라 어떤 속성이 조건에 사용됐는지 확인하면 원인을 좁히기 쉽다.

스캔 대상을 정할 때도 한 단계를 더 확인한다. 태그의 자산 목록, 실제 스캔 설정의 대상·제외 조건, 사용자에게 허용된 자산 범위를 대조한다. 태그 이름이나 규칙 테스트의 성공만으로 점검 대상이 확정되거나 검사가 완료된 것은 아니다. 포함·제외 조건의 세부 의미는 사용 중인 제품과 화면의 문서를 따로 확인한다.

[[diagram]]

## 작은 가상 목록으로 차이를 확인한다

다음 Python 예제는 세 개의 가상 자산을 사용한다. 정적 목록은 `lab-01`, `lab-02`를 직접 지정했고, 별도의 비교 함수는 운영체제가 Linux이면서 환경이 `prod`인 자산을 고른다.

이 조건식은 **분류 개념을 설명하는 독립적인 Python 코드**다. Qualys의 QQL 문법, 태그 엔진, 동기화 방식이나 API 응답 형식을 재현한 것은 아니다. 자격 증명이나 네트워크 연결도 사용하지 않는다.

`compare_tags_demo.py`로 저장한 뒤 `python3 compare_tags_demo.py`로 실행한다.

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

[[run:1]]


첫 자료에서 조건에 맞는 자산은 `lab-01` 하나이며, 정적 목록에 남은 Windows 자산은 `lab-02`다. 어느 쪽이 잘못됐는지는 업무 목적에 따라 달라진다. 정적 태그가 ‘월간 점검 계약 대상’을 뜻한다면 Windows 자산을 포함하는 것이 맞을 수도 있다.

다음 실험에서는 `lab-03`의 가상 환경 값만 바꾼다. Python 함수를 다시 호출하자 조건 목록에 추가된다. 이는 함수의 재계산 결과이며 Qualys가 같은 시점에 태그를 갱신했다는 실측 결과가 아니다.

속성이 없거나 자료가 불완전하면 예제는 비교를 중단한다. 제품에서 누락 속성을 처리하는 방식은 이 코드와 같다고 가정하지 않는다. 실제 목록을 대조할 때도 정보가 빠진 자산을 단순히 ‘조건 불일치’나 ‘점검 대상 아님’으로 분류하지 말고 누락 원인을 확인한다.

## 태그의 목적과 조회 시점의 자산 목록을 보관한다

업무상 고정된 책임 범위를 표현하려면 정적 태그가 이해하기 쉬울 수 있다. 반대로 운영체제·설치 소프트웨어처럼 관찰 정보에 따라 분류할 때는 동적 규칙이 유용하다. 실제 태그를 고를 때는 변경 빈도와 담당자, 정보 수집 경로를 함께 고려한다.

태그마다 분류 목적과 적용 기준을 짧게 적고, 점검에 사용한 자산 목록은 조회 시각과 함께 별도로 보관한다. 동적 목록이 바뀌더라도 당시 어떤 대상을 확인했는지 설명할 수 있어야 한다. 태그 수정은 이후 스캔·보고서 범위에 영향을 줄 수 있으므로 대상 변화부터 검토하고 적용한다.

공유 자료에는 실제 호스트 이름과 IP, 태그에 담긴 조직·서비스 정보를 불필요하게 노출하지 않는다. 이 글처럼 분류 방식을 설명할 때는 가상 식별자만으로도 차이를 충분히 확인할 수 있다.

## 공식 참고 자료

- [VM/VMDR: Manage Tags — 정적·동적 태그, 규칙별 구독 조건](https://docs.qualys.com/en/vm/latest/mergedProjects/analyze_reports_and_dashboards/assets/manage_tags.htm)
- [GAV: Manage Asset Tags — 지정 방식과 재평가 상태](https://docs.qualys.com/en/gav/latest/Tags/manage_your_tags.htm)
