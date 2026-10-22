---
title: "Qualys Search List: 스캔 범위와 보고서 필터를 구분하기"
description: "Search List를 연결한 위치에 따라 달라지는 QID 검사 범위와 보고서 표시 필터를 비교합니다."
date: "2026-10-17T09:07:01+09:00"
updated: "2026-10-17T18:17:24+09:00"
category: "qualys"
tags: ["Qualys", "Search List", "QID", "보고서"]
draft: false
example: false
---

Search List는 Qualys의 검사 항목 번호인 QID를 묶어 사용하는 목록이다. 보고서에서 어떤 항목이 빠졌다면 이 목록이 어디에 연결됐는지부터 살펴보자.

**스캔 옵션 프로필**에 연결한 목록은 검사할 QID를 고른다. **보고서 템플릿**에 연결한 목록은 이미 수집된 결과 중 보여 줄 QID를 고른다. 같은 목록이라도 검사 범위를 바꾸는지, 표시할 결과만 거르는지에 차이가 있다.

여기서는 Qualys **VM/VMDR**의 Search List를 다룬다. 다른 Qualys 앱에서는 메뉴와 권한이 다를 수 있다.

## 먼저 목록이 붙은 위치를 찾는다

Qualys의 [Search Lists 안내](https://docs.qualys.com/en/vm/latest/search_lists/search_lists_basics.htm)는 목록을 스캔, 보고서, 조치 티켓 규칙에 쓸 수 있다고 설명한다. 예를 들어 팀이 일부 QID만 시험하려고 Search List를 만들었다고 하자. 스캔 옵션 프로필의 **Vulnerability Detection → Custom**에 넣었다면 검사할 QID 범위를 제한한다. 보고서 템플릿에만 넣었다면 보고서가 보여 주는 QID를 고른다. 티켓 규칙에 연결했다면 어떤 탐지에 티켓을 만들지도 별도로 결정한다.

| 목록이 연결된 곳 | 바뀌는 것 | 결과를 읽을 때 물어볼 질문 |
| --- | --- | --- |
| 스캔 옵션 프로필의 Custom | 검사할 QID 범위 | 선택한 목록과 제외 목록, 포트·인증 조건은 무엇인가? |
| 보고서 템플릿 | 보고서에 표시할 QID | 원래 스캔 결과와 같은 범위를 보고 있는가? |
| 조치 티켓 규칙 | 티켓 생성 대상 | 티켓이 없다는 사실을 탐지 없음으로 잘못 읽고 있지 않은가? |

보고서에서 QID가 빠졌다면 스캔 프로필, 원본 결과, 템플릿 필터를 차례로 대조한다. 이 자료가 있어야 검사에서 빠진 항목인지, 탐지되지 않은 항목인지, 조치 후 달라진 결과인지 판단할 수 있다.

[[diagram]]

## 정적 목록과 동적 목록도 사용 목적이 다르다

**정적 Search List**는 지정한 QID 목록을 저장한다. 범위가 고정된 재현 시험이나 특정 진단 QID를 확인할 때 유용하다. **동적 Search List**는 취약점 지식 베이스의 조건을 저장하고, 조건에 맞는 QID를 찾는다. 공급업체나 제품, 심각도 같은 조건을 사용하면 이후 조건에 맞는 QID가 목록에 포함될 수 있다. 지난 보고서와 범위를 비교하려면 실제 사용 시점에 어떤 QID가 포함됐는지 남겨야 한다.

자산 태그가 묶는 대상은 자산이고 Search List가 고르는 대상은 취약점 QID다. 자산 태그에 원하는 호스트가 모두 포함돼 있어도 옵션 프로필의 QID 제한 때문에 검사 범위가 좁아질 수 있다.

VM/VMDR 문서의 [Configure Search Lists](https://docs.qualys.com/en/vm/latest/search_lists/search_lists_lp.htm)는 `Reports > Search Lists > New > Dynamic List` 경로와 목록의 `Test` 기능을 안내한다. 이 단계에서 조건에 맞는 QID가 무엇인지 확인하고 저장한다. 단, 목록의 QID가 보인다는 사실이 해당 호스트에서 취약점이 탐지됐다는 뜻은 아니다. 호스트·포트·인증·탐지 조건과 실제 스캔 결과가 뒤따라야 한다.

## 옵션 프로필에서 한 번 더 범위를 좁힐 수 있다

[VM Option Profile의 Scan 설정](https://docs.qualys.com/en/vm/latest/option_profiles/op_scan_tab.htm)에서 **Complete**는 호스트에 적용 가능한 지식 베이스 QID를 검사한다. **Custom**은 Search List로 QID를 제한한다. `Select at runtime`은 일회성 사용자 지정 검사에서 목록을 고르며 예약 검사에는 사용할 수 없다. Custom을 쓴다면 기본 호스트 정보 수집도 별도로 선택해야 한다는 점을 문서가 명시한다.

제외 QID 목록을 추가해도 해당 QID와 관련된 네트워크 트래픽이 모두 차단되는 것은 아니다. 하나의 검사가 여러 QID의 자료를 수집할 수 있고, 필요한 검사를 시작 전에 완전히 분리하지 못할 수 있기 때문이다. 따라서 **Excluded QIDs를 통신 차단 장치처럼 사용하지 않는다**.

침투성 검사는 기본적으로 제외된다. 사용자 지정 목록에 포함돼 있어도 옵션 프로필에서 별도로 허용해야 검사에 들어간다. 검사 동작을 바꿀 때는 승인된 대상과 변경 영향부터 검토해야 한다.

보고서 차이를 조사할 자료는 네 가지다.

- 스캔 날짜와 대상
- Complete/Custom 설정과 당시 Search List의 QID
- 원본 탐지 결과
- 보고서 템플릿의 포함·제외 조건

동적 목록은 조회 시점에 따라 QID 구성이 달라질 수 있으므로 스캔 당시의 범위를 보관한다.

## 권한과 구독 범위를 먼저 확인한다

목록을 ‘전역’으로 공개하는 권한은 역할에 따라 다르다. 공식 Search Lists 문서는 Manager가 구독 전체에, Unit Manager가 소속 비즈니스 단위에 전역 목록을 제공할 수 있다고 설명한다. 소유자 변경은 이를 사용하는 옵션 프로필·보고서 템플릿·예약 작업의 접근 충돌을 만들 수 있으므로 연결된 작업을 먼저 확인해야 한다. 화면의 메뉴와 사용 가능한 검사 유형은 VM/VMDR 구독과 부여된 역할에 따라 대조한다.

누락된 QID가 원본 결과에 있다면 보고서 필터를 조사한다. 원본에도 없다면 당시의 QID 범위와 검사 조건을 살핀다. 동적 목록은 이후 바뀔 수 있으므로 현재 목록보다 스캔 당시 사용한 목록이 비교의 기준이다.

## 공식 참고 자료

- [Qualys VM/VMDR: Search Lists(용도, 유형, 전역 권한)](https://docs.qualys.com/en/vm/latest/search_lists/search_lists_basics.htm)
- [Qualys VM/VMDR: Configure Search Lists(동적 목록 설정과 Test)](https://docs.qualys.com/en/vm/latest/search_lists/search_lists_lp.htm)
- [Qualys VM/VMDR: VM Option Profile: Scan(Complete·Custom·제외·침투성 검사)](https://docs.qualys.com/en/vm/latest/option_profiles/op_scan_tab.htm)
