---
title: "U-36: r 계열 서비스 비활성화"
description: "가상 inetd 파일의 shell·login·exec 행을 명령 이름과 연결해요. 활성 행과 주석을 구분하고, rsync의 별도 조사와 자료 누락·조회 오류·입력 오류가 남기는 결과를 실제 출력으로 살펴봐요."
date: "2026-11-13T18:36:33+09:00"
sourcesChecked: "2026-11-13"
category: critical-infrastructure
assessmentTarget: "unix"
tags: ["Unix", "Linux", "inetd", "rsh", "KISA"]
draft: false
series: unix-2026
seriesOrder: 36
---

설정 파일에서 `rsh`라는 이름을 찾았는데 아무것도 나오지 않았더라도 서비스 행의 첫 이름은 `shell`일 수 있어요. U-36에서는 클라이언트 명령 이름과 서비스를 등록하는 이름을 연결해서 읽어야 빠뜨리는 행을 줄일 수 있어요. 이번 실습은 가상 `inetd` 파일의 `shell`·`login`·`exec` 행을 읽고 주석과 활성 후보를 나눠 보는 예제예요.

## U-36에서 말하는 ‘불필요한 서비스’

[KISA 2026 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 U-36은 ‘r 계열 서비스 비활성화’이며 중요도는 ‘상’이에요. 항목표 9쪽과 본문 77~79쪽의 코드·항목명·중요도가 일치하고, 적용 대상에는 SOLARIS, LINUX, AIX, HP-UX 등이 있어요.

판단 기준은 불필요한 r 계열 서비스가 비활성화되어 있으면 양호, 활성화되어 있으면 취약이에요. 여기서 ‘불필요한’을 빼면 업무상 사용 여부를 조사하는 과정이 사라져요. 가이드도 NET Backup이나 클러스터 구성처럼 사용 여부를 먼저 살필 상황을 언급해요. 등록된 서비스, 실제 실행·대기 상태, 사용하는 업무와 대체 수단을 함께 대조한 뒤 조치 범위를 정해요.

가이드는 `rsh(remsh)`, `rlogin`, `rexec`, `rsync`를 열거하지만 인증 방식을 모두 같게 설명할 수는 없어요. [IANA 서비스 이름·포트 번호 등록부](https://www.iana.org/assignments/service-names-port-numbers?search=512)는 `exec`의 인증에 사용자 이름과 비밀번호를 사용한다고 적고 있어요. 모든 항목을 ‘인증 없는 접속’으로 묶기보다 각 서비스의 인증·접근 경로를 나눠 조사해야 해요.

`rsync`도 이름만 보고 rsh 접속으로 단정하지 않아요. [rsync 공식 설명서](https://www.samba.org/ftp/rsync/generated-files/rsync.1.html)는 SSH 또는 rsh 같은 원격 셸을 이용하는 방식과 rsync 데몬에 직접 연결하는 방식을 구분해요. 이 글에서는 `rsync`를 세 서비스 행과 나누어 별도 조사 대상으로 남겨요. 가이드의 점검 대상에는 그대로 포함해요.

## 명령 이름, 서비스 이름, 실행 파일을 잇기

가이드의 예제에서는 `rsh`에 `shell`과 TCP 514, `rlogin`에 `login`과 TCP 513, `rexec`에 `exec`와 TCP 512가 대응해요. TCP라는 프로토콜까지 함께 읽어 주세요. 포트 숫자만으로 실행 중인 프로그램이나 인증 상태가 입증되지는 않아요.

[GNU Inetutils의 inetd 설정 형식](https://www.gnu.org/s/inetutils/manual/html_node/Configuration-file.html)에서 첫 필드는 서비스 이름이고 뒤에 소켓 종류·프로토콜·대기 방식·사용자·서버 프로그램·인수가 이어져요. 서비스 이름은 `/etc/services`의 이름과 대응하며 서버 프로그램은 요청을 받았을 때 실행할 경로예요. 아래 그림은 곧 실행할 가상 파일에서 세 서비스의 이름과 서버 파일을 연결한 모습이에요.

[[diagram]]

`shell`에는 활성 1행과 주석 2행이 함께 있어요. 2행을 읽었다는 이유로 1행을 비활성으로 덮어쓰지 않고, 모든 활성 행을 후보 목록에 남겨요. `login`은 주석인 3행만 있으므로 ‘이 파일에 주석 행만 있음’까지 설명할 수 있어요. 다른 설정 파일이나 서비스 관리자의 상태를 읽지 않았으니 운영체제 전체에서 중지됐다는 결론으로 넓히지는 않아요.

가이드에는 `hosts.equiv`·`.rhosts`의 부재나 빈 내용을 미사용으로 보는 설명도 있어요. 신뢰 파일에 허용 대상을 적었는지와 서비스가 대기 중인지는 다른 자료이므로 함께 조사해요. 업무상 사용하는 경우의 접근 제한·파일 권한 예시 역시 불필요한 서비스를 계속 켜 둘 근거로 바꾸지 않아요.

## ZIP에 든 가상 파일부터 읽어 보기

Python 3.12 이상과 표준 라이브러리만 사용해요. Windows Python 3.12.1의 PowerShell과 Git Bash에서 검증했으며 관리자 권한, inetd 설치, Linux 파일시스템이나 별도 패키지는 필요하지 않아요.

ZIP을 빈 폴더에 풀고 `README.md`, `u36_inetd_review.py`, `u36_sample.conf`, `u36_malformed.conf`가 있는 글별 폴더로 이동해 주세요. 두 `.conf`는 이미 포함되어 있으니 다시 만들지 않아요. 프로그램은 인수로 지정한 파일만 읽고 그 안의 서버 경로를 실행하지 않아요. 운영 설정·계정·인증·네트워크를 조회하거나 바꾸지 않고 소켓과 임시 파일도 만들지 않아요.

[[download]]

먼저 실행할 파일은 다음 다섯 줄이에요. 경로는 가상 설정 문자열이므로 해당 위치에 프로그램이나 폴더를 준비할 필요가 없어요.

```text
shell stream tcp nowait root /usr/sbin/in.rshd in.rshd
#shell stream tcp nowait root /usr/sbin/in.rshd in.rshd
#login stream tcp nowait root /usr/sbin/in.rlogind in.rlogind
exec stream tcp nowait root /usr/sbin/in.rexecd in.rexecd
rsync stream tcp nowait root /usr/bin/rsync rsync --daemon
```

아래 명령은 두 셸에서 같아요. 실행 직후 PowerShell은 `$LASTEXITCODE`, Bash는 `echo $?`로 숫자 종료 코드를 읽어요. PowerShell의 `$?`는 성공 여부이므로 숫자 코드와 구분해 주세요. README에는 각 명령 옆에 셸별 조회 방법이 있으니 사용하는 셸의 블록 하나를 고르면 돼요.

```bash
python -I -B -X utf8 u36_inetd_review.py --collection collected u36_sample.conf
```

`-I`는 Python 격리 모드, `-B`는 바이트코드 생성 방지, `-X utf8`은 UTF-8 모드예요. 파일시스템 접근을 격리하는 옵션은 아니므로 ZIP의 가상 입력을 지정해 주세요. 다음 전체 코드는 ZIP의 Python 파일과 같아요.

```python
import argparse
from pathlib import Path
import sys


TARGETS = {"shell": ("rsh", 514), "login": ("rlogin", 513),
           "exec": ("rexec", 512)}
STATES = ("collected", "absent", "query-error", "uncollected")


def read_rows(path):
    with path.open("rb") as stream:
        raw = stream.read(20001)
    if len(raw) > 20000:
        raise ValueError("입력 크기 상한")
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if len(lines) > 200:
        raise ValueError("입력 행 수 상한")
    rows = {name: [] for name in (*TARGETS, "rsync")}
    for number, line in enumerate(lines, 1):
        value = line.strip()
        if not value:
            continue
        commented = value.startswith("#")
        fields = value.removeprefix("#").strip().split()
        if commented and (not fields or fields[0] not in rows):
            continue
        if (len(fields) < 7 or fields[0] not in rows
                or fields[1] != "stream"
                or fields[2] not in ("tcp", "tcp4", "tcp6")
                or fields[3] != "nowait" or fields[4] != "root"
                or not fields[5].startswith("/")):
            raise ValueError("가상 입력 형식")
        rows[fields[0]].append((number, commented, fields[5]))
    return rows


def describe(rows):
    active_count = 0
    comment_count = 0
    output = []
    for service, (command, port) in TARGETS.items():
        active = [row for row in rows[service] if not row[1]]
        comments = [row for row in rows[service] if row[1]]
        if active:
            active_count += 1
            details = ", ".join(f"{n}행 {server}" for n, _, server in active)
            output.append(f"{service} ({command}, TCP {port}): 활성 행 후보 | {details}")
        elif comments:
            comment_count += 1
            numbers = ",".join(str(row[0]) for row in comments)
            output.append(f"{service} ({command}, TCP {port}): 주석 행만 있음 | {numbers}행")
        else:
            output.append(f"{service} ({command}, TCP {port}): 대상 행 없음, 보류")
    separate = [row for row in rows["rsync"] if not row[1]]
    if separate:
        numbers = ",".join(str(row[0]) for row in separate)
        output.append(f"rsync: 별도 조사 | {numbers}행, 전송 방식과 실제 사용 조사")
    output.append(f"파일 내 서비스 수: 활성 후보 {active_count}, 주석만 {comment_count}, "
                  f"별도 조사 {int(bool(separate))}")
    return output


def main():
    parser = argparse.ArgumentParser(description="가상 inetd 입력의 세 서비스 행 비교")
    parser.add_argument("--collection", choices=STATES, required=True)
    parser.add_argument("fixture", type=Path, nargs="?")
    args = parser.parse_args()
    if args.collection != "collected":
        if args.fixture is not None:
            parser.error("미수집 상태에는 입력 파일을 지정하지 않아요")
        print(f"보류: {args.collection}, 설정 본문 비교 미실행")
        return 0
    if args.fixture is None:
        parser.error("collected에는 가상 입력 파일이 필요해요")
    try:
        rows = read_rows(args.fixture)
        output = describe(rows)
    except (OSError, UnicodeError, ValueError):
        print("가상 설정 비교 미실행")
        print("입력 오류: UTF-8, 파일 접근, 크기 또는 지원 형식을 살펴보세요", file=sys.stderr)
        return 2
    print("\n".join(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

이 코드는 가상 입력용 작은 형식만 받아요. 서비스 이름이 `shell`, `login`, `exec`, `rsync` 중 하나이며 필드가 7개 이상이고, `stream`, `tcp`·`tcp4`·`tcp6`, `nowait`, `root`, `/`로 시작하는 서버 경로가 있어야 해요. 호스트 접두사, 다른 서비스 이름, 다른 사용자·대기 방식 등 지원하지 않는 형식은 입력 오류로 남겨요. 실제 inetd의 전체 문법을 검증하는 파서는 아니에요.

파일 전체를 읽고 형식을 검사한 다음에만 결과를 출력해요. 정상 파일에서 관찰한 ‘활성 후보 2, 주석만 1, 별도 조사 1’은 이 가상 파일 안에서 서비스 이름별로 센 값이에요. 같은 서비스의 활성 행이 여러 개여도 서비스 수는 하나이며 행 목록은 모두 남겨요.

[[run:1]]

## 1행의 shell이 최종 출력에 도달하는 순서

명령의 `--collection collected`는 본문을 얻었다고 가정하는 인수예요. `main()`이 `u36_sample.conf`를 `args.fixture`로 받아 `read_rows()`에 넘기면 파일을 최대 20,001바이트까지 읽어요. 20,000바이트를 넘거나 UTF-8로 해석되지 않거나 200행을 넘으면 결과를 만들기 전에 거부해요.

1행에서는 `value`가 `shell stream tcp nowait root /usr/sbin/in.rshd in.rshd`이고 `commented`는 거짓이에요. 공백으로 나눈 `fields[0]`은 `shell`, `fields[1]`은 `stream`, `fields[2]`는 `tcp`, `fields[3]`은 `nowait`, `fields[4]`는 `root`, `fields[5]`는 `/usr/sbin/in.rshd`예요. 필드 수와 각 조건이 맞으므로 `rows["shell"]`에 `(1, False, "/usr/sbin/in.rshd")`가 추가돼요.

2행은 맨 앞의 `#`를 떼고 같은 형식을 검사하되 `commented`가 참인 튜플로 추가해요. `describe()`의 `active`에는 1행만, `comments`에는 2행만 들어가요. `if active`가 먼저 참이 되므로 뒤의 `elif comments`로 내려가지 않고 활성 후보를 출력해요. 주석이 활성 행을 가리지 않는 분기 순서예요.

`TARGETS["shell"]`의 `("rsh", 514)`를 꺼내 `command`와 `port`에 넣고 `details`에 행 번호와 서버 경로를 붙이면 실제 실행 기록의 첫 줄이 돼요. `shell (rsh, TCP 514): 활성 행 후보 | 1행 /usr/sbin/in.rshd`가 그 결과예요. 여기서 `rsh`와 514는 정해 둔 대응값이며 실행 중인 서비스에서 조회한 값은 아니에요.

`login`은 활성 행이 없어 두 번째 분기에서 ‘주석 행만 있음’이 되고, `exec`는 활성 4행이 있어 첫 분기로 들어가요. `rsync` 활성 5행은 세 서비스의 합계에 섞지 않고 별도 조사로 표시해요. 종료 0은 파일의 입력 검사와 이 비교가 끝났다는 뜻이며 U-36의 양호 판정이나 실제 접속 허용 결과가 아니에요.

## 자료를 받지 못한 상태와 입력 오류를 구분하기

설정 본문 자체를 전달받지 못했다면 다음처럼 `uncollected`를 지정해요. 이 명령은 파일을 열지 않고 보류를 출력해요. 프로그램이 실제 운영 자료를 수집했다는 기록은 아니에요.

```bash
python -I -B -X utf8 u36_inetd_review.py --collection uncollected
```

[[run:2]]

조회 오류가 있었다고 가정하면 `query-error`를 전달해요. 이 예제에서 파일 접근을 시도해 권한 오류를 일으킨 것은 아니며 오류 자료를 받은 뒤 비교를 보류하는 분기를 실행한 거예요.

```bash
python -I -B -X utf8 u36_inetd_review.py --collection query-error
```

[[run:3]]

특정 설정 파일이 없다는 자료가 있다고 가정한 입력은 `absent`예요. 파일 하나의 부재만으로 서비스의 부재를 확정할 수 없어서 이 경우도 보류해요. 수집 상태가 이 세 값이면 파일 인수를 함께 줄 수 없으며 잘못 섞으면 인수 오류로 종료해요.

```bash
python -I -B -X utf8 u36_inetd_review.py --collection absent
```

[[run:4]]

앞의 세 실행에서 종료 0은 지정한 보류 상태를 처리했다는 뜻이에요. `collected`라고 선언했더라도 실제 파일을 읽지 못했거나 지원 형식을 벗어나면 종료 2가 돼요. ZIP의 `u36_malformed.conf`는 정상 `shell` 행 뒤에 필드가 부족한 `login stream tcp nowait` 행을 넣어 이 경로를 시험해요.

```bash
python -I -B -X utf8 u36_inetd_review.py --collection collected u36_malformed.conf
```

[[run:5]]

표준 출력은 ‘가상 설정 비교 미실행’, 표준 오류는 입력 오류 안내이고 숫자 종료 코드는 2예요. 앞의 정상 행에서 만들어질 활성 후보를 일부 출력한 뒤 성공처럼 보이게 남기지 않아요. 예상한 거부 결과를 재현한 것이지 잘못된 파일을 허용했다는 뜻은 아니에요. 정상 파일에서도 이 결과가 나오면 실행 폴더·파일 이름과 읽기 가능 여부, UTF-8, 크기·행 수, 지원 형식을 순서대로 살펴보세요.

운영 점검에는 이 파일 밖의 자료가 더 필요해요. 가이드가 구분한 inetd·xinetd·systemd·Solaris SMF 중 실제 관리 방식, 합쳐 읽는 설정 파일과 서비스 이름 매핑, 서버 프로그램과 실행·대기 상태를 먼저 대조해요. 이어서 업무상 사용 근거와 접근 제한을 조사하고 비활성화 후의 상태를 따로 남겨야 해요. 가상 파일의 주석 행이나 신뢰 파일 부재를 그 자료 대신 채우지는 않아요.

## 참고 자료

- [KISA: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드](https://www.kisa.kr/2060204/form?postSeq=22&page=1)
- [GNU Inetutils: inetd 설정 파일 형식](https://www.gnu.org/s/inetutils/manual/html_node/Configuration-file.html)
- [IANA: 서비스 이름과 포트 번호 등록부의 exec 항목](https://www.iana.org/assignments/service-names-port-numbers?search=512)
- [rsync: 공식 명령 설명서](https://www.samba.org/ftp/rsync/generated-files/rsync.1.html)
