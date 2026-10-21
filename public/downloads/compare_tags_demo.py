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
