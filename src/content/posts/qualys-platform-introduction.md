---
title: "Qualys란? VMDR과 스캐너, Cloud Agent의 역할"
description: "Qualys의 클라우드 보안 플랫폼과 VMDR, 스캐너, Cloud Agent가 맡는 역할을 설명하고 자산·QID·탐지 결과의 뜻을 짚습니다."
date: "2026-10-20T06:38:21+09:00"
sourcesChecked: "2026-10-20"
category: "qualys"
tags: ["Qualys", "VMDR", "Cloud Agent", "취약점관리", "입문"]
draft: false
example: false
---

Qualys(퀄리스)는 기업의 IT 자산과 취약점, 보안 설정을 관리하는 클라우드 기반 보안 서비스를 제공하는 회사다.

취약점 관리에 사용하는 대표적인 앱은 VMDR이다. 서버와 단말에서 수집한 정보를 바탕으로 취약점을 평가하고, 어느 자산을 먼저 조치할지 검토하며, 이후 탐지 결과를 추적하는 데 쓴다. 관리 화면에 나오는 VMDR, 장비에 설치하는 Cloud Agent, 네트워크에서 검사하는 스캐너는 각각 맡은 일이 다르다.

## 플랫폼, 보안 앱, 수집 구성의 관계

Qualys의 Enterprise TruRisk Platform은 자산 정보와 보안 평가 결과를 모아 관리하는 공통 기반이다. 대상 호스트나 네트워크에 배치한 에이전트와 스캐너가 이 관리·분석 서비스에 필요한 정보를 보낸다.

여기서 클라우드라는 말은 관리 서비스를 제공하는 방식을 뜻한다. 사내 데이터센터의 서버와 업무용 단말도 관리 대상이 될 수 있다.

플랫폼 위에서는 목적에 맞는 보안 앱을 사용한다. VMDR은 취약점 관리, CSAM(CyberSecurity Asset Management)은 자산 식별과 분류, Policy Audit은 보안 정책과 기준에 따른 시스템 설정 평가를 담당한다. 같은 서버를 보더라도 어떤 앱을 사용하는지에 따라 다루는 정보와 평가 목적이 달라진다.

[[diagram]]

스캐너를 등록하거나 Cloud Agent를 설치하는 작업은 정보를 수집할 경로를 마련하는 일이다. 사용할 앱의 활성화와 자산 범위까지 맞춰야 해당 목적에 필요한 평가 결과를 볼 수 있다. 구독에 포함된 앱과 사용자에게 부여된 앱 접근·작업 권한에 따라 화면과 실행 가능한 기능도 달라진다.

## VMDR에서는 무엇을 관리하나

VMDR은 Vulnerability Management, Detection and Response의 약자다. 자산을 파악하고 취약점을 평가한 뒤, 위협 정보와 자산의 중요도를 반영해 조치 우선순위를 검토하는 기능을 제공한다. 관련 패치를 찾고 조치 대상을 추적하는 일도 이 과정에 포함된다.

예를 들어 특정 소프트웨어의 보안 업데이트가 공개됐다고 하자. 관리자는 해당 제품이 설치된 자산과 관련 탐지 항목을 조회하고, 실제 버전과 탐지 근거를 대조해 영향을 받는 대상을 검토한다. 이후 자산의 업무 중요도와 공격에 노출된 조건을 함께 살펴 조치 순서를 정한다.

이때 취약점별 설명과 해결 방법, 자산 정보, 위험도와 우선순위 자료를 한곳에서 다룰 수 있다. 다만 해결 방법이나 관련 패치가 결과에 표시됐다는 사실이 실제 서버에 적용됐다는 뜻은 아니다. 패치·설정 변경은 대상 시스템의 변경 절차로 수행하고, 이후 수집한 정보와 재평가 결과로 남아 있는 문제를 살핀다.

## 스캐너와 Cloud Agent는 정보를 얻는 위치가 다르다

Scanner Appliance는 네트워크를 통해 대상의 서비스와 응답을 검사한다. 내부망을 검사할 때는 대상까지 접근할 수 있는 위치에 물리·가상 스캐너를 두고, 외부 공개 대상을 검사할 때는 Qualys의 외부 스캐너를 선택할 수 있다. 대상에 인증하는 스캔에서는 서비스 응답 외에 로그인 후 얻을 수 있는 정보도 활용한다.

Cloud Agent는 지원되는 호스트에 설치하는 프로그램이다. 설치된 장비의 정보를 수집해 플랫폼으로 전송하며, 활성화한 앱의 평가에 활용한다. 이름에 Cloud가 들어가지만 클라우드 인스턴스에만 설치하는 프로그램은 아니다. 지원 운영체제와 에이전트 버전, 사용할 앱의 조건에 맞춰 사내 서버와 단말에도 배치할 수 있다.

센서별 결과를 비교하려면 각 대상의 수집 출처부터 살핀다. 네트워크에서 접근 가능한 정보와 호스트에서 수집한 정보가 다르고, 검사 범위·인증·수집 시점도 결과에 영향을 준다. 구체적인 수집 조건은 [Cloud Agent와 Scanner Appliance의 수집 누락을 살피는 글](../qualys-collection-coverage/)에서 다룬다.

## 화면에서 자주 만나는 네 가지 용어

처음 결과를 읽을 때는 자산, 검사 항목, 그 자산에서 얻은 탐지 근거를 구분하면 된다.

- **자산(Asset)**: 서버·단말 등 관리 대상. 취약점이 어느 대상에서 발견됐는지 연결하는 기준이다.
- **QID**: Qualys의 검사 항목을 식별하는 번호. 공개 취약점 식별자인 CVE 번호와는 구분한다.
- **탐지 결과(Results)**: 해당 자산에서 탐지한 근거. 제품·버전·설정·응답 등 항목에 맞는 내용이 표시된다.
- **태그(Tag)**: 자산을 업무·운영체제·환경 등의 기준으로 분류하는 표지. 조회·스캔·보고서의 대상을 고를 때 활용한다.

QID에 대한 설명은 검사 항목 자체를 이해하는 자료이고, 특정 서버의 Results는 그 서버에서 얻은 자료다. 항목의 제목을 읽은 뒤에는 어느 자산의 어떤 결과인지 이어서 살펴봐야 한다. 같은 QID가 여러 자산에서 탐지되면 조치할 대상도 각각 남는다.

처음에는 접근 권한이 있는 자산 하나를 고른다. 운영체제와 수집 출처, 마지막 결과 시각을 읽은 뒤 탐지 항목의 설명과 그 자산의 Results를 대조해 본다. 이후의 스캔·조치 과정은 [Qualys로 취약점 관리 시작하기](../qualys-vulnerability-management/), 실행 환경과 계정 조건은 [Qualys 실습 환경 고르기](../qualys-learning-environment/)에서 이어서 볼 수 있다.

## 참고 자료

- [Qualys: Introduction to the Enterprise TruRisk Platform](https://docs.qualys.com/en/vm/latest/onboarding_guide/platform_intro.htm)
- [Qualys: VMDR Overview](https://docs.qualys.com/en/vmdr/latest/getting_started/overview.htm)
- [Qualys VMDR: Vulnerability Details](https://docs.qualys.com/en/vm/latest/mergedProjects/search_in_vmdr/assets/vulnerability_details.htm)
- [Qualys Cloud Agent](https://www.qualys.com/cloud-agent)
- [Qualys: Scanning - The Basics](https://docs.qualys.com/en/vm/latest/scans/scanning_basics.htm)
- [Qualys: Control User Access Permissions](https://docs.qualys.com/en/vm/latest/user_accounts/admin_ui.htm)
