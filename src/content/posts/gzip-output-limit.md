---
title: "작은 gzip 파일도 안전하지 않다: 압축 해제 출력량 제한하기"
description: "작은 gzip 입력도 해제 출력량을 기준으로 제한해야 하는 이유와 경계값 검증을 다룹니다."
date: "2026-10-12T20:52:00+09:00"
updated: "2026-10-21"
category: "application-security"
tags: ["Python", "압축", "입력검증"]
draft: false
example: false
---

예제의 544바이트 gzip 파일을 해제하자 512 KiB가 됐다. 업로드 크기는 작아도 압축을 푼 뒤에는 훨씬 많은 데이터를 처리해야 한다.

아래 코드는 압축을 풀면서 출력 바이트 수만 세고, 한도를 넘으면 중단한다. 해제한 내용은 저장하지 않는다. 파일 경로가 허용 범위 안에 있어도 해제 출력량은 따로 제한해야 한다.

## 압축 입력과 해제 출력을 따로 제한한다

압축 데이터의 과도한 확장은 메모리·디스크·CPU를 소모할 수 있다. 다만 압축률이 높다는 이유만으로 공격이라고 판단하지 않는다. 정상 로그에도 반복 문장이 많으므로 서비스가 감당할 수 있는 절대 출력량을 먼저 정한다.

gzip 끝의 `ISIZE`는 해당 멤버의 원래 크기를 2³²로 나눈 나머지다. gzip 파일은 여러 멤버를 이어 붙일 수도 있어 마지막 크기 필드 하나로 전체 해제량을 보장할 수 없다. 실제로 반환되는 출력에 한도를 적용해야 한다.

[[diagram]]

## max_length에는 항상 양수를 넣는다

Python의 `zlib.decompressobj()`로 gzip 해제기를 만들고, `decompress()`의 `max_length`로 한 번에 반환할 양을 제한한다. 이 인자에 0을 넣으면 출력 제한이 사라진다. 남은 예산이 0이어도 그대로 전달하면 안 된다.

아래 코드는 남은 예산에 1바이트를 더해 요청한다. 한도가 65,536바이트라면 65,537번째 바이트가 나왔을 때 거부한다. 추가 1바이트는 초과 여부를 확인하기 위한 것이며, 정상 결과로 반환하지 않는다. 누적 출력 전체는 저장하지 않고 길이만 센다.

| 항목 | 실습 정책 |
| --- | --- |
| 압축 입력 | 최대 1 MiB |
| 해제 출력 | 기본 64 KiB. 파일 검사에서는 --limit으로 0~1 MiB 설정 가능 |
| 허용 형식 | 단일 gzip 멤버. 두 번째 멤버나 뒤에 붙은 데이터는 거부 |
| 처리 결과 | 출력 바이트 수만 반환하며 해제 내용은 표시하거나 파일로 저장하지 않음 |

1 KiB는 1,024바이트다. 위 크기는 원리를 확인하기 위한 예시값이다. Python 3.8 이상과 표준 라이브러리의 zlib 모듈이 필요하며, 추가 패키지는 사용하지 않는다.

## 실제 출력량을 세는 전체 코드

다음 코드를 `gzip_limit.py`로 저장하거나 [같은 파일을 내려받는다](../../downloads/gzip_limit.py). 터미널에서 이 파일이 있는 폴더로 이동한 뒤 실행한다. 인자 없이 실행하면 메모리에서 만든 시험 데이터만 검사한다. 로컬 파일 경로를 지정하면 압축 입력도 한도를 확인할 수 있는 크기까지만 읽는다.

```python
import argparse
import gzip
import sys
import zlib
from pathlib import Path

INPUT_LIMIT = 1024 * 1024
OUTPUT_LIMIT = 64 * 1024
CHUNK = 8192


class PolicyError(Exception):
    pass


def inspect_gzip(data, limit=OUTPUT_LIMIT):
    """단일 gzip 멤버의 실제 출력량을 세며 검사한다. 파일은 쓰지 않는다."""
    if not 0 <= limit <= 1024 * 1024:
        raise ValueError("출력 한도는 0~1048576바이트여야 한다")
    if len(data) > INPUT_LIMIT:
        raise PolicyError("압축 입력 한도 초과")
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    total = 0
    position = 0
    pending = b""
    while True:
        if not pending and position < len(data):
            pending = data[position:position + CHUNK]
            position += len(pending)
        # 초과 여부를 확인할 1바이트를 더한다. 0은 무제한이므로 쓰지 않는다.
        piece = decoder.decompress(pending, min(CHUNK, limit - total + 1))
        total += len(piece)
        if total > limit:
            raise PolicyError("압축 해제 출력 한도 초과")
        pending = decoder.unconsumed_tail
        if decoder.eof:
            if decoder.unused_data or position < len(data):
                raise PolicyError("단일 멤버 뒤의 추가 데이터는 허용하지 않는다")
            return total
        # 내부에 남은 출력이 있을 수 있어 다음 회차의 빈 입력도 처리한다.
        if not pending and position == len(data) and not piece:
            raise ValueError("gzip 스트림이 끝나기 전에 입력이 끝났다")


def run_demo():
    normal = gzip.compress(b"A" * OUTPUT_LIMIT, mtime=0)
    large = gzip.compress(b"A" * (512 * 1024), mtime=0)
    print(f"큰 예제: 압축 {len(large)}바이트, 원문 524288바이트")
    cases = [
        ("한도와 같은 출력", normal, OUTPUT_LIMIT, None),
        ("한도보다 1바이트 큰 출력",
         gzip.compress(b"A" * (OUTPUT_LIMIT + 1), mtime=0),
         OUTPUT_LIMIT, PolicyError),
        ("작은 입력의 큰 출력", large, OUTPUT_LIMIT, PolicyError),
        ("빈 원문과 0 한도", gzip.compress(b"", mtime=0), 0, None),
        ("잘린 마지막 부분", normal[:-1], OUTPUT_LIMIT, ValueError),
        ("두 멤버 연결", normal + normal, OUTPUT_LIMIT, PolicyError),
        ("뒤에 붙은 문자열", normal + b"extra", OUTPUT_LIMIT, PolicyError),
        ("압축 입력 한도 초과",
         b"x" * (INPUT_LIMIT + 1), OUTPUT_LIMIT, PolicyError),
        ("gzip이 아닌 입력", b"not gzip", OUTPUT_LIMIT, zlib.error),
    ]
    for label, data, limit, expected in cases:
        try:
            size = inspect_gzip(data, limit)
        except (PolicyError, ValueError, zlib.error) as exc:
            if expected is None or type(exc) is not expected:
                raise AssertionError(f"예상과 다른 결과: {label}") from exc
            print(f"{label}: 성공, 예상한 거부 확인")
        else:
            if expected is not None:
                raise AssertionError(f"거부되지 않음: {label}")
            print(f"{label}: 성공, 출력 {size}바이트")


def main():
    parser = argparse.ArgumentParser(description="단일 gzip 멤버 출력 한도 검사")
    parser.add_argument("path", nargs="?", help="허가된 로컬 gzip 파일")
    parser.add_argument("--limit", type=int, default=OUTPUT_LIMIT)
    args = parser.parse_args()
    try:
        if args.path is None:
            run_demo()
        else:
            # 입력을 제한된 크기까지만 읽고 출력 내용은 보관하지 않는다.
            with Path(args.path).open("rb") as source:
                data = source.read(INPUT_LIMIT + 1)
            size = inspect_gzip(data, args.limit)
            print(f"검사 완료: 출력 {size}바이트, 설정한 정책 범위 내")
        return 0
    except PolicyError as exc:
        print(f"정책상 거부: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, zlib.error, AssertionError) as exc:
        print(f"실행 또는 데이터 오류: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```
`inspect_gzip()`는 압축 바이트와 출력 한도를 받아, 허용된 경우 해제한 바이트 수를 반환한다. `position`은 원본 압축 입력에서 읽은 위치, `pending`은 해제기에 다시 넣어야 할 입력, `total`은 지금까지 반환된 출력량이다. 한 번 반환할 조각도 `CHUNK` 이하로 제한하므로 전체 원문을 한꺼번에 만들지 않는다.

`unconsumed_tail`에는 출력 제한 때문에 아직 처리하지 못한 압축 바이트가 남는다. 이를 다음 호출에 다시 전달한다. 입력을 모두 넣은 뒤에도 내부에 출력이 남을 수 있어 빈 입력으로 진행하고, 출력도 없고 종료 표시도 없으면 잘린 스트림으로 처리한다.

`eof`가 참이 되어야 정상 종료로 인정한다. 그 뒤 `unused_data`나 아직 전달하지 않은 입력이 있으면 단일 멤버 정책에 따라 거부한다. `flush()`는 사용하지 않는다. 그 길이 인자는 출력 버퍼의 초기 크기이므로 엄격한 출력 상한을 대신하지 못한다.

## 작은 데이터로 허용과 거부를 확인한다

```bash
python3 gzip_limit.py
```
실행 결과는 다음과 같다. 압축 크기는 Python·zlib 버전과 압축 조건에 따라 달라질 수 있다.

```text
큰 예제: 압축 544바이트, 원문 524288바이트
한도와 같은 출력: 성공, 출력 65536바이트
한도보다 1바이트 큰 출력: 성공, 예상한 거부 확인
작은 입력의 큰 출력: 성공, 예상한 거부 확인
빈 원문과 0 한도: 성공, 출력 0바이트
잘린 마지막 부분: 성공, 예상한 거부 확인
두 멤버 연결: 성공, 예상한 거부 확인
뒤에 붙은 문자열: 성공, 예상한 거부 확인
압축 입력 한도 초과: 성공, 예상한 거부 확인
gzip이 아닌 입력: 성공, 예상한 거부 확인
```
544바이트로 압축된 512 KiB 원문은 입력 한도에는 들어왔지만 해제량이 64 KiB를 넘어 거부됐다. 반면 출력이 정확히 한도와 같은 사례는 스트림의 정상 종료까지 확인한 뒤 허용했다. 출력의 ‘성공’에는 이렇게 예상한 거부도 포함된다.

[[run:1:fold]]

파일 경로를 전달하는 실행에는 실제 `sample.gz`가 필요하다. 빈 실습 폴더에 `gzip_limit.py`를 둔 뒤, 다음 한 줄로 `A` 65,536바이트를 압축한 파일을 만든다. Bash 또는 PowerShell에서 `python3 -c 'import gzip; open("sample.gz", "xb").write(gzip.compress(b"A" * 65536, mtime=0))'`를 실행한다. `xb`는 같은 이름의 파일이 있으면 실패하므로 기존 파일을 덮어쓰지 않는다. Windows에서 명령 이름이 `python`이면 `python3` 대신 사용한다.

이제 같은 폴더에서 아래 명령을 실행한다. `--limit`은 파일 경로를 전달했을 때만 적용한다. 경로 없이 `--limit`만 바꾸면 `run_demo()`의 고정된 시험 사례가 실행된다. 파일 검사도 해제 내용 대신 출력 바이트 수만 표시한다.

```bash
python3 gzip_limit.py ./sample.gz --limit 65536
```
| 종료 코드 | 의미 |
| --- | --- |
| 0 | 파일이 설정한 정책을 충족했거나 기본 예제 검증이 모두 성공함 |
| 1 | 입력·출력 크기 또는 단일 멤버 정책으로 거부함 |
| 2 | 파일 읽기, 인자, gzip 형식·무결성 또는 예제 검증 오류 |

위에서 만든 파일은 해제량이 한도와 같으므로 `검사 완료: 출력 65536바이트, 설정한 정책 범위 내`와 종료 코드 0이 나와야 한다. 한도를 65,535로 낮추면 같은 파일도 정책 거부인 1로 끝난다. `sample.gz`가 없을 때의 2는 압축률 문제를 뜻하지 않으며, 파일 위치부터 살펴야 한다. 실습이 끝나면 직접 만든 `sample.gz`만 지운다.

파일 준비와 한도 65,536바이트의 검사 명령도 임시 폴더에서 실행했다. 이 기록은 위의 기본 예제 실행과 별도로 남겼다.

[[run:2]]


## 여러 멤버의 거부와 형식 오류를 구분한다

gzip 규격에서는 여러 멤버를 이어 붙일 수 있다. 이 예제가 두 번째 멤버를 거부하는 이유는 처리 범위를 단일 멤버로 정했기 때문이며, 파일 손상을 뜻하지는 않는다. 여러 멤버를 처리하려면 멤버마다 해제기를 새로 만들고 파일 전체의 누적 출력 예산을 유지해야 한다.

빈 원문으로 만든 정상 gzip과 아예 빈 입력도 다르다. 전자는 종료 정보가 있어 출력 한도 0에서도 허용할 수 있고, 후자는 정상 gzip 스트림이 아니므로 오류다. 일부 데이터가 나왔다고 처리를 완료해서도 안 된다. 마지막 무결성 검사에서 오류가 발견될 수 있으므로 정상 종료를 확인한 뒤 결과를 사용한다.

## 운영에서는 시간과 동시 작업 수도 제한한다

이 코드는 애플리케이션에 반환되는 해제 출력량을 제한한다. 해제기 내부 버퍼와 Python의 전체 메모리, CPU 시간까지 같은 숫자로 제한하는 것은 아니다. 운영 처리기에는 작업 시간, 동시 작업 수, 프로세스 메모리 한도와 격리를 함께 적용한다. 장치나 끝나지 않는 스트림을 입력으로 받는다면 읽기 시간 제한도 필요하다.

웹 서버의 업로드 제한과 해제기의 출력 제한은 각각 둔다. 파일로 저장해야 한다면 제한된 임시 영역에서 완료 여부를 확인한 뒤 서비스에 넘기고, 오류나 한도 초과 시 부분 결과를 폐기한다. 여러 파일이나 중첩 압축에는 작업 전체의 출력량, 파일 수와 중첩 깊이도 제한한다.

거부 로그에는 입력·출력 한도와 거부 사유를 남긴다. 원문 내용은 넣지 않는다. 정상 자료가 한도를 반복해서 넘으면 업무에 필요한 해제량을 조사한 뒤 자원 제한과 함께 정책을 조정한다.

## 참고 자료

- [Python zlib 문서: 출력 상한과 스트림 종료 처리](https://docs.python.org/3/library/zlib.html)
- [Python gzip 문서: 압축 예제와 버전별 동작](https://docs.python.org/3/library/gzip.html)
- [RFC 1952: gzip 멤버 구성과 ISIZE](https://www.rfc-editor.org/rfc/rfc1952.html)
- [MITRE CWE-409: 압축 데이터의 과도한 확장](https://cwe.mitre.org/data/definitions/409.html)
- [OWASP 파일 업로드 지침: 해제 이후 크기 제한](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
