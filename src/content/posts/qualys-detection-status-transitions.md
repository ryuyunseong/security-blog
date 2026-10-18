---
title: "Fixed였던 QID가 다시 나올 때: Qualys 탐지 상태 읽기"
description: "평가 자료가 없는 구간과 Fixed 이후 재탐지를 가상 이력으로 구분하고, 보고서 시점과 상태 변화를 대조합니다."
date: "2026-10-18T12:14:00+09:00"
sourcesChecked: "2026-10-18"
category: "qualys"
tags: ["Qualys","VMDR","QID","탐지 상태","보고서"]
draft: false
example: false
---

어제 Fixed로 보였던 항목이 오늘 Re-Opened로 나타났다면 두 가지 결과를 비교해야 한다. 어떤 검사에서 수정됐다고 확인했는지, 그 뒤 어느 검사에서 같은 취약점을 다시 탐지했는지다. 패치 작업의 완료 시각만으로는 이 상태 변화를 설명하기 어렵다.

이 글은 Qualys VM/VMDR의 탐지 상태를 시간 순서로 읽는 예제다. 기본 상태 이름을 소개하는 데서 더 나아가, 결과가 없는 구간을 어떻게 남길지와 조치 후 재탐지를 어떤 자료로 조사할지 다룬다.

## Re-Opened 다음에도 같은 상태가 유지될까

Qualys의 Vulnerability Status Levels 문서는 새 스캔 결과가 처리되면 상태를 갱신한다고 설명한다. 첫 탐지는 New, 두 번 이상 탐지된 항목은 Active가 된다. 이전에 탐지한 항목을 최신 스캔에서 수정된 것으로 검증하면 Fixed이고, Fixed 뒤의 새 검사에서 다시 탐지하면 Re-Opened다. **Re-Opened 항목이 그다음 스캔에서도 탐지되면 Active로 바뀐다.** 따라서 현재 Active인 항목도 과거의 수정·재탐지 이력을 가질 수 있다.

같은 자산과 탐지 항목을 추적한다는 조건에서 다음 흐름을 읽는다. 중간에 검사 결과가 들어오지 않은 구간은 그림의 화살표를 따라 상태를 옮길 근거가 없다.

[[diagram]]

Fixed는 패치 관리 시스템의 ‘설치 완료’와 같은 필드가 아니다. 패치가 설치돼도 재부팅이나 서비스 재시작이 남아 있을 수 있고, 검사 결과가 처리되기 전에는 화면이 예전 상태를 보여 줄 수 있다. 반대로 보고서에서 행이 빠진 이유가 대상 제외나 필터라면 이를 Fixed로 해석해서는 안 된다.

## 한 항목의 관찰 기록으로 전이를 시험한다

다음은 가상 자산 하나의 같은 탐지 항목을 여섯 번 관찰한 예제다. 실제 Qualys 결과를 수집한 코드가 아니라 공식 상태 설명을 읽기 위한 작은 모델이다. `tested=True`는 이 예제에서 해당 항목을 충분히 평가한 관찰이 있다는 가정이며, 스캔 작업 전체가 완료됐다는 뜻으로 쓰지 않는다. `detected=None`은 판단에 쓸 관찰이 없다는 표시다.

코드를 `qualys_status_example.py`로 저장하고 `python -I -B qualys_status_example.py`로 실행한다. 파일·네트워크·제품 API에 접근하지 않는다. 함수는 알 수 없는 상태와 모순된 입력을 거부하고, 평가하지 못한 회차에는 마지막 상태를 보존한다.

```python
STATES = {None, "New", "Active", "Fixed", "Re-Opened"}


def next_state(previous, tested, detected):
    if previous not in STATES:
        raise ValueError("알 수 없는 이전 상태")
    if type(tested) is not bool:
        raise ValueError("평가 여부는 bool이어야 함")
    if not tested:
        if detected is not None:
            raise ValueError("미평가 회차에 탐지 결과를 넣을 수 없음")
        return previous
    if type(detected) is not bool:
        raise ValueError("평가한 회차에는 탐지 여부가 필요함")
    if detected:
        if previous is None:
            return "New"
        return "Re-Opened" if previous == "Fixed" else "Active"
    return "Fixed" if previous is not None else None


observations = [
    ("1차", True, True),
    ("2차", True, True),
    ("3차", False, None),
    ("4차", True, False),
    ("5차", True, True),
    ("6차", True, True),
]
assert next_state(None, True, True) == "New"
assert next_state("Active", False, None) == "Active"
assert next_state("Active", True, False) == "Fixed"
assert next_state("Fixed", True, True) == "Re-Opened"
assert next_state("Re-Opened", True, True) == "Active"
assert next_state(None, True, False) is None
try:
    next_state("Active", False, False)
except ValueError:
    pass
else:
    raise AssertionError("모순된 입력을 거부해야 함")

state = None
for label, tested, detected in observations:
    state = next_state(state, tested, detected)
    observation = "탐지" if detected is True else "미탐지" if tested else "평가 자료 없음"
    suffix = " (마지막 상태 보존)" if not tested else ""
    print(f"{label}: {observation} -> {state}{suffix}")
```

[[run:1]]

3차에는 평가 자료가 없어 마지막 Active를 보존했다. 4차에서 충분한 평가 후 미탐지라는 가정을 넣었을 때 Fixed로 옮겨 갔고, 5차 재탐지는 Re-Opened, 6차의 연속 탐지는 Active가 됐다. 이 모델의 입력을 실제 보고서 CSV의 ‘행 없음’으로 채우면 안 된다. 행이 없다는 사실에는 해당 검사가 수행됐는지, 대상이 제외됐는지, 필터로 숨겨졌는지가 들어 있지 않다.

이력 표에는 현재 상태와 함께 각 관찰의 시점·자료 유무를 남긴다. 예제의 3차처럼 새 자료가 없다면 마지막 탐지 상태의 날짜도 그대로 남겨야 오래된 결과를 오늘 새로 검증한 결과처럼 읽지 않는다. ‘평가 자료 없음’은 설명용 문구이며 Qualys의 다섯 번째 상태값이 아니다.

## 현재 호스트 데이터와 저장된 스캔을 나눠 읽는다

VM 10.32의 보고서 템플릿 문서에서 **Host Based Findings**는 계정에서 호스트별로 색인한 최신 취약점 자료를 모은다. 기본 추세 비교는 각 호스트의 취약점에 대해 마지막 두 탐지의 상태를 대조한다. **Scan Based Findings**는 실행할 때 선택한 저장 스캔 결과를 사용하므로 그 시점의 대상을 보여 준다. 이전 스캔으로 만든 PDF와 현재 호스트 화면을 바로 대조하면 숫자가 달라질 수 있다.

보고서의 기간 조건도 읽어야 한다. 같은 문서의 `Only include scan results from the specified timeframe` 옵션은 지정한 기간에 수집된 자료만 포함하도록 제한한다. 이 조건을 사용하지 않으면 기간보다 전에 마지막으로 검사된 호스트의 기존 자료가 들어갈 수 있다. 보고서 생성일을 모든 자산의 검사일로 해석하면 오래된 Active나 Fixed를 최신 관찰로 오해하게 된다.

| 대조할 자료 | 먼저 맞출 조건 |
| --- | --- |
| 현재 호스트 화면과 이전 보고서 | 자산 식별 정보, QID와 탐지 위치, 수집·처리 시점 |
| 두 번의 보고서 | Host Based/Scan Based 유형, 선택한 스캔, 기간과 상태 필터 |
| 패치 작업과 Fixed 결과 | 조치 시각, 후속 검사 시각, 해당 항목의 Results |

보고서 예시는 VM 10.32 문서의 기능명에 맞췄다. 실제 메뉴를 사용할 때는 계정에서 활성화된 VM/VMDR 앱과 보고서 접근 권한을 대조한다. 템플릿을 전역으로 배포하는 경우에는 별도 역할 조건도 있다. 해당 문서는 Manager와 Unit Manager에게 전역 설정을 허용하며 Unit Manager의 범위는 소속 비즈니스 단위다. 상태 이력을 읽는 일과 구독 전체의 템플릿을 바꾸는 일을 같은 권한으로 취급하지 않는다.

## 재탐지 원인은 변경 전후의 Results로 좁힌다

Re-Opened가 보이면 Fixed였던 결과와 재탐지한 결과에서 제품·버전·설정·응답 근거를 비교한다. 롤백이나 재설치로 취약한 버전이 돌아왔는지, 서비스가 이전 바이너리로 실행 중인지, 다른 경로의 설치본이 잡힌 것인지 등을 조사할 수 있다. 이들은 조사 후보이며 상태 이름만으로 원인을 확정할 수는 없다.

같은 QID라는 이유로 서로 다른 자산이나 탐지 위치를 한 줄로 합치지 않는다. 자산 식별 정보와 수집 방식, 결과에 있는 포트·프로토콜을 맞춘 뒤 같은 항목의 이력인지 결정한다. 실제로 새로운 관찰이 들어온 것인지도 살핀다. 마지막으로 남길 기록은 ‘다시 열림’이라는 상태명만이 아니라, 이전 수정 근거와 새 탐지 근거가 어느 시점에 달라졌는지 보여 주는 비교다.

## 참고 자료

- [Qualys VMDR: Vulnerability Status Levels](https://docs.qualys.com/en/vmdr/latest/scans/vulnerability_status.htm)
- [Qualys VM 10.32: Configure Report Templates](https://docs.qualys.com/en/vm/10.32.0.0/reports/scan_reports/win_scan_template.htm)
