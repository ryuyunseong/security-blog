---
title: "Qualys 탐지 상태: Fixed 이후 같은 QID가 다시 나오는 이유"
description: "가상 탐지 이력으로 Fixed 이후 재탐지와 평가 자료가 없는 기간을 구별합니다. 보고서를 만든 시점에 따라 상태를 어떻게 읽을지 설명합니다."
date: "2026-10-18T12:14:00+09:00"
updated: "2026-10-22"
sourcesChecked: "2026-10-18"
category: "qualys"
tags: ["Qualys","VMDR","QID","탐지 상태","보고서"]
draft: false
example: false
---

Fixed였던 항목이 다음 날 Re-Opened로 바뀌었다면, 수정됐다고 판단한 검사와 다시 탐지한 검사를 비교해야 한다. 패치 완료 시각에 더해 두 검사의 탐지 근거가 필요하다.

Qualys VM/VMDR의 탐지 상태를 가상 관찰 기록으로 따라가 본다. 검사 자료가 없는 회차를 처리하는 방법과 조치 후 재탐지를 조사할 자료도 살펴본다.

## Re-Opened 다음에도 같은 상태가 유지될까

Qualys의 Vulnerability Status Levels 문서는 새 스캔 결과가 처리되면 상태를 갱신한다고 설명한다. 첫 탐지는 New, 두 번 이상 탐지된 항목은 Active가 된다. 이전에 탐지한 항목을 최신 스캔에서 수정된 것으로 검증하면 Fixed이고, Fixed 뒤의 새 검사에서 다시 탐지하면 Re-Opened다. **Re-Opened 항목이 그다음 스캔에서도 탐지되면 Active로 바뀐다.** 따라서 현재 Active인 항목도 과거의 수정·재탐지 이력을 가질 수 있다.

아래 그림은 같은 자산의 같은 탐지 항목을 계속 추적하는 경우다. 중간에 검사 결과가 들어오지 않았다면 새 상태를 정할 근거도 없으므로, 화살표를 따라 임의로 상태를 바꾸지 않는다.

[[diagram]]

Fixed는 Qualys에 기록된 탐지 상태이며 패치 설치 완료를 보증하지 않는다. Authoritative 스캔은 해당 QID가 검사 범위에 포함돼 있으면, 이전 탐지 포트가 닫혔거나 도달할 수 없는 경우에도 기존 항목을 닫을 수 있다. 인증 스캔에서 탐지한 항목을 닫으려면 후속 검사도 인증 스캔이어야 한다. 상태를 해석할 때는 조치 이력과 함께 QID·포트 범위와 인증 방식을 대조한다.

## 한 항목의 관찰 기록으로 전이를 시험한다

다음은 가상 자산 하나의 같은 탐지 항목을 여섯 번 관찰한 예제다. 실제 Qualys 결과를 수집한 코드가 아니라 공식 상태 설명을 읽기 위한 작은 모델이다. `tested=True`는 이 예제에서 해당 항목을 충분히 평가한 관찰이 있다는 가정이며, 스캔 작업 전체가 완료됐다는 뜻으로 쓰지 않는다. `detected=None`은 판단에 쓸 관찰이 없다는 표시다. 포트·인증·접근 차단에 따른 제품의 판정 규칙은 구현하지 않았다.

ZIP의 `qualys_status_example.py`를 사용하거나 코드를 같은 이름으로 저장한다. Python 3 표준 기능만 사용하며 별도 입력 파일이나 패키지는 필요 없다. 파일이 있는 폴더에서 `python -I -B qualys_status_example.py`로 실행한다. 파일·네트워크·제품 API에 접근하지 않는다. 함수는 알 수 없는 상태와 모순된 입력을 거부하고, 평가하지 못한 회차에는 마지막 상태를 보존한다.

[[download]]

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

`next_state()`의 인수는 이전 상태, 이번 평가 여부, 탐지 여부 순서다. 함수 앞부분에서 상태명과 불리언 자료형을 검사하고, 미평가 회차는 탐지 여부가 `None`일 때만 이전 상태를 반환한다. `False`는 평가했지만 탐지하지 않았다는 값이므로 미평가와 섞어 넣을 수 없다.

평가한 회차는 탐지 여부를 따라 분기한다. 탐지했다면 이전 이력이 없을 때 `New`, 이전 상태가 `Fixed`일 때 `Re-Opened`, 나머지는 `Active`다. 미탐지라면 기존 이력이 있는 경우 `Fixed`, 처음부터 이력이 없는 경우 `None`을 반환한다. `None`은 이 모델에서 아직 상태가 없다는 표시다.

여섯 관찰을 출력하기 전에 주요 반환값을 `assert`로 검사하고, 모순된 입력 한 건이 거부되는지도 시험한다. 상태 전이의 기대값이 다르면 출력 반복문에 도달하기 전에 중단될 수 있다. 기본 실행에서 종료 코드 0은 이 검사와 여섯 관찰 처리를 마쳤다는 뜻이며, `assert`를 끄는 `-O` 옵션은 사용하지 않는다.

[[run:1]]

3차에는 평가 자료가 없어 마지막 Active를 보존했다. 4차에서 충분한 평가 후 미탐지라는 가정을 넣었을 때 Fixed로 옮겨 갔고, 5차 재탐지는 Re-Opened, 6차의 연속 탐지는 Active가 됐다. 이 모델의 입력을 실제 보고서 CSV의 ‘행 없음’으로 채우면 안 된다. 행이 없다는 사실만으로는 검사가 수행됐는지, 대상이 제외됐는지, 필터로 숨겨졌는지 알 수 없다.

이력 표에는 현재 상태와 함께 각 관찰의 시점·자료 유무를 남긴다. 예제의 3차처럼 새 자료가 없다면 마지막 탐지 상태의 날짜도 그대로 남겨야 오래된 결과를 오늘 새로 검증한 결과처럼 읽지 않는다. ‘평가 자료 없음’은 설명용 문구이며 Qualys의 다섯 번째 상태값이 아니다.

## 현재 호스트 데이터와 저장된 스캔을 나눠 읽는다

Qualys VM 최신 보고서 템플릿 문서에서 **Host Based Findings**는 계정에서 호스트별로 색인한 최신 취약점 자료를 모은다. 기본 추세 비교는 각 호스트의 취약점에 대해 마지막 두 탐지의 상태를 대조한다. **Scan Based Findings**는 실행할 때 선택한 저장 스캔 결과를 사용하므로 그 시점의 대상을 보여 준다. 이전 스캔으로 만든 PDF와 현재 호스트 화면을 바로 대조하면 숫자가 달라질 수 있다.

보고서의 기간 조건도 읽어야 한다. 같은 문서의 `Only include scan results from the specified timeframe` 옵션은 지정한 기간에 수집된 자료만 포함하도록 제한한다. 이 조건을 사용하지 않으면 기간보다 전에 마지막으로 검사된 호스트의 기존 자료가 들어갈 수 있다. 보고서 생성일을 모든 자산의 검사일로 해석하면 오래된 Active나 Fixed를 최신 관찰로 오해하게 된다.

Host Detection List API로 대조할 때는 `status` 매개변수도 확인한다. 생략하면 기본 응답에는 New·Active·Re-Opened만 포함되고 Fixed는 빠진다. 보고서나 API 응답에 행이 없다는 사실만으로 수정 여부를 판단하지 않는다.

| 대조할 자료 | 먼저 맞출 조건 |
| --- | --- |
| 현재 호스트 화면과 이전 보고서 | 자산 식별 정보, QID와 탐지 위치, 수집·처리 시점 |
| 두 번의 보고서 | Host Based/Scan Based 유형, 선택한 스캔, 기간과 상태 필터 |
| 패치 작업과 Fixed 결과 | 조치 시각, 후속 검사 시각, 해당 항목의 Results |

보고서 기능명은 2026-10-18에 확인한 Qualys VM 최신 문서 기준이다. 실제 메뉴를 사용할 때는 계정에서 활성화된 VM/VMDR 앱과 보고서 접근 권한을 대조한다. 전역 템플릿 설정은 Manager와 Unit Manager에게 허용되며 Unit Manager의 범위는 소속 비즈니스 단위다.

## 재탐지 원인은 변경 전후의 Results로 좁힌다

Re-Opened가 보이면 Fixed였던 결과와 재탐지한 결과에서 제품·버전·설정·응답 근거를 비교한다. 롤백이나 재설치, 이전 바이너리로 실행 중인 서비스, 다른 경로의 설치본 등을 조사할 수 있다.

Qualys의 Information on QIDs 문서는 레지스트리 접근 차단으로 QID가 Fixed로 바뀌고, 접근이 복구된 후 Re-Opened가 되는 사례도 설명한다. Results와 함께 IG QID 34011(방화벽 탐지), 42432(스캔 방해 가능성), 90195(Windows 레지스트리 키 접근 거부)를 살펴 이전 검사에서 탐지 근거를 수집하지 못했는지 조사한다. 상태 이름만으로 실제 수정이나 취약점 재발을 확정하지 않는다.

먼저 자산 식별 정보, 수집 방식, 포트·프로토콜을 맞춰 같은 항목의 이력인지 살핀다. QID가 같아도 자산이나 탐지 위치가 다르면 한 줄로 합쳐서는 안 된다. 이력에는 상태명과 함께 이전 수정 근거, 새 탐지 근거, 각각의 관찰 시점을 남긴다.

## 참고 자료

- [Qualys VMDR: Vulnerability Status Levels](https://docs.qualys.com/en/vmdr/latest/scans/vulnerability_status.htm)
- [Qualys VM: Authoritative Option for light port scans](https://docs.qualys.com/en/vm/latest/option_profiles/authoritative_scan_option.htm)
- [Qualys VM: Information on QIDs](https://docs.qualys.com/en/vm/latest/knowledgebase/qids_created.htm)
- [Qualys VM: Configure Report Templates](https://docs.qualys.com/en/vm/latest/reports/scan_reports/win_scan_template.htm)
- [Qualys API: Host Detection List](https://docs.qualys.com/en/vm/qweb-all-api/mergedProjects/qapi-assets/host_lists/host_detection.htm)
