import argparse
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
from threading import Barrier, Lock


def sharing():
    value = [1]
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-X", "utf8", "-c", "value = 1; value += 100; print(value)"],
        capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    if result.returncode != 0 or result.stderr:
        raise RuntimeError("자식 프로세스가 정상적으로 끝나지 않았다")
    child = int(result.stdout.strip())
    parent = value[0]
    lock = Lock()
    ready = Barrier(2)

    def increase():
        ready.wait(timeout=10)
        for _ in range(2):
            with lock:
                value[0] += 1

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(increase) for _ in range(2)]
        for job in jobs:
            job.result()
    assert (parent, child, value[0]) == (1, 101, 5)
    print(f"별도 프로세스: parent={parent} child={child}")
    print(f"같은 프로세스의 스레드: shared={value[0]}")


def translate(address, page_size, table):
    if type(address) is not int or address < 0 or type(page_size) is not int or page_size <= 0:
        raise ValueError("주소는 음이 아닌 정수, 페이지 크기는 양의 정수여야 한다")
    page, offset = divmod(address, page_size)
    if page not in table:
        return page, offset, None, "unmapped"
    frame = table[page]
    if frame is None:
        return page, offset, None, "not_present"
    if type(frame) is not int or frame < 0:
        raise ValueError("프레임 번호는 음이 아닌 정수여야 한다")
    return page, offset, frame * page_size + offset, "mapped"


def paging():
    table = {2: 9, 3: None}
    for address in (8195, 12288, 16384):
        page, offset, physical, state = translate(address, 4096, table)
        print(f"{state}: page={page} offset={offset} physical={physical}")


def wait_cycle(wait_for):
    for start in sorted(wait_for):
        seen, path = {}, []
        current = start
        while current is not None:
            if current in seen:
                return path[seen[current]:] + [current]
            seen[current] = len(path)
            path.append(current)
            current = wait_for.get(current)
    return []


def waiting():
    before = wait_cycle({"A": "B", "B": "A"})
    after = wait_cycle({"A": "B", "B": None})
    assert before == ["A", "B", "A"] and after == []
    print("대기 순환: " + " -> ".join(before))
    print("순환 해제 모형: " + (" -> ".join(after) if after else "없음"))


def main():
    parser = argparse.ArgumentParser(description="작은 프로세스·스레드 실험과 메모리·대기 관계 모형")
    parser.add_argument("example", choices=("sharing", "paging", "waiting"))
    args = parser.parse_args()
    try:
        {"sharing": sharing, "paging": paging, "waiting": waiting}[args.example]()
    except (OSError, ValueError, RuntimeError, AssertionError, subprocess.TimeoutExpired) as error:
        print(f"실행 오류: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
