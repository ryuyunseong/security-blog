import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def require(name):
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"필요한 도구를 찾을 수 없습니다: {name}")
    return executable


def execute(command):
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode != 0 or result.stderr:
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"실행 실패 또는 표준 오류 발생: {Path(command[0]).name}, 종료 {result.returncode}")
    return result.stdout


def run_one(language, source):
    # 컴파일 결과는 이번 실행이 만든 임시 폴더에만 저장한다.
    with tempfile.TemporaryDirectory(prefix="cs06-") as folder:
        work = Path(folder)
        if language == "c":
            binary = work / ("program.exe" if sys.platform == "win32" else "program")
            execute([require("gcc"), "-std=c11", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)])
            return execute([str(binary)])
        if language == "java":
            execute([require("javac"), "-encoding", "UTF-8", "-d", str(work), str(source)])
            return execute([require("java"), "-cp", str(work), source.stem])
        return execute([sys.executable, "-I", "-B", "-X", "utf8", str(source)])


def main():
    parser = argparse.ArgumentParser(description="묶음에 포함된 작은 예제를 실행하고 기대값과 대조한다")
    parser.add_argument("language", choices=("c", "java", "python"))
    parser.add_argument("--questions", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    demos = {
        "c": [("06-programming-basics.c", "division: -2 -1\nguard: 0\nvalue: 5 6\ntotal: 4\n")],
        "java": [("ProgrammingBasics.java", "division: -2 -1\nguard: false\nvalue: 5 6\ntotal: 4\n")],
        "python": [("06-programming-basics.py", "division: -3 2\nguard: False\nvalue: 5 6\ntotal: 4\n")],
    }
    questions = {
        "c": [("06-question1.c", "4 5\n"), ("06-question4.c", "9 0\n")],
        "java": [("Question2.java", "7\n")],
        "python": [("06-question3.py", "[1, 2, 5]\n[9, 2]\n")],
    }
    completed = []
    try:
        for name, expected in (questions if args.questions else demos)[args.language]:
            actual = run_one(args.language, root / name)
            if actual != expected:
                raise RuntimeError(f"기대 출력과 다릅니다: {name}")
            completed.append((name, actual))
    except (OSError, RuntimeError, subprocess.TimeoutExpired, UnicodeError) as error:
        print(f"실행 오류: {error}", file=sys.stderr)
        return 2
    for name, output in completed:
        print(f"파일: {name}")
        print(output, end="")
    print(f"예제 {len(completed)}건 기대값 대조 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
