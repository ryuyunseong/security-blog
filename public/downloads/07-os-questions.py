from pathlib import Path
import runpy


def main():
    namespace = runpy.run_path(str(Path(__file__).resolve().with_name("07-os-examples.py")))
    translate = namespace["translate"]
    wait_cycle = namespace["wait_cycle"]
    answer2 = translate(12345, 4096, {3: 12})
    assert answer2 == (3, 57, 49209, "mapped")
    answer3 = translate(8192, 4096, {2: None})
    assert answer3 == (2, 0, None, "not_present")
    answer4 = wait_cycle({"A": "B", "B": "C", "C": None})
    assert answer4 == []
    answer5 = wait_cycle({"P": "Q", "Q": "P"})
    ordered = wait_cycle({"P": "Q", "Q": None})
    assert answer5 == ["P", "Q", "P"] and ordered == []
    print(f"q2: {answer2}")
    print(f"q3: {answer3}")
    print(f"q4: {answer4}")
    print(f"q5: {answer5}, 순서 통일 모형={ordered}")
    print("문제 2~5의 모형 값 대조 완료")


if __name__ == "__main__":
    main()
