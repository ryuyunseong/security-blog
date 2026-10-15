---
title: HTTP 응답 헤더 기록하기
description: 응답 헤더를 근거로 남기고 적용 범위를 구분합니다.
date: 2026-10-15
category: web
tags: [HTTP, 헤더]
draft: true
example: true
---

## 관찰과 판단 구분하기

응답 헤더를 기록할 때는 ‘헤더가 있었다’는 관찰과 ‘보안 정책이 충분하다’는 판단을 구분합니다. 하나의 응답만으로 서비스 전체의 설정을 단정하지 않습니다.

## 기록 형식

아래는 실제 사이트에서 수집한 결과가 아닌 가상 예시입니다. `example.invalid`는 문서용 이름이며 외부 요청을 보내지 않습니다.

```text
대상: https://example.invalid/
방법: 로컬 실습 자료의 응답 확인
Content-Type: text/html; charset=utf-8
X-Content-Type-Options: nosniff
판단: 해당 응답에서 헤더를 관찰함
추가 확인: 다른 경로와 오류 응답의 정책
```

## 공개 전 점검

쿠키, 인증 헤더, 내부 호스트명, 요청 식별자는 원문을 게시하지 않습니다. 재현에 필요한 최소한의 필드와 확인 범위를 남깁니다.

추가 정책은 애플리케이션의 자원과 동작을 확인한 뒤 별도로 검토합니다. 이 예시는 운영 설정 변경을 제안하는 보안 판정 문서가 아닙니다.

공식 참고: [MDN — HTTP 헤더](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers).
