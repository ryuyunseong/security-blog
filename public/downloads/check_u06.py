#!/usr/bin/env python3
"""su 관련 파일을 읽는다. 인증 실행이나 양호·취약 자동 판정은 하지 않는다."""
import argparse
import pathlib
import re
import stat


def collect(root, group, binary):
    incomplete = False

    def warn(message):
        nonlocal incomplete
        incomplete = True
        print('[확인 필요] ' + message)

    def locate(name):
        path = (root / name.lstrip('/')).resolve()
        if root != path and root not in path.parents:
            raise ValueError('수집 범위 밖을 가리키는 경로')
        return path

    def read(name):
        try:
            path = locate(name)
            if not path.is_file() or path.stat().st_size > 1024 * 1024:
                raise ValueError('일반 파일이 아니거나 크기 제한 초과')
            return path.read_text(encoding='utf-8').splitlines()
        except (OSError, ValueError, RuntimeError) as error:
            warn(f'{name}: {type(error).__name__}')
            return None

    # 비밀번호 필드는 결과에 포함하지 않는다.
    users, groups = [], []
    for name, size, target in [('/etc/passwd', 7, users),
                               ('/etc/group', 4, groups)]:
        lines = read(name)
        if lines is None:
            continue
        for number, line in enumerate(lines, 1):
            parts = line.split(':')
            numeric = (2, 3) if size == 7 else (2,)
            if (len(parts) != size or not parts[0] or
                parts[0].startswith(('+', '-')) or
                any(not re.fullmatch(r'[0-9]{1,10}', parts[i]) for i in numeric)):
                warn(f'{name}:{number} 레코드 형식 확인')
                continue
            if size == 7:
                target.append((parts[0], int(parts[3])))
            else:
                target.append((parts[0], int(parts[2]), parts[3]))
    matches = [entry for entry in groups if entry[0] == group]
    if len(matches) != 1:
        warn('지정 그룹의 로컬 레코드가 정확히 하나가 아님')
    else:
        _, gid, members = matches[0]
        primary = sorted(name for name, user_gid in users if user_gid == gid)
        print(f'[그룹] {group} GID={gid}')
        print('[기본 그룹] ' + (','.join(primary) or '(로컬 기록 없음)'))
        print('[추가 그룹] ' + (members or '(명시된 구성원 없음)'))

    # su를 실행하지 않고 대상 파일의 숫자 소유권과 모드만 읽는다.
    try:
        path = locate(binary)
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('일반 파일이 아님')
        print(f'[파일] {binary} UID={info.st_uid} GID={info.st_gid} '
              f'모드={stat.S_IMODE(info.st_mode):04o}')
        print('[기타 사용자 실행 비트] ' +
              ('있음' if info.st_mode & stat.S_IXOTH else '없음'))
    except (OSError, ValueError, RuntimeError) as error:
        warn(f'{binary}: {type(error).__name__}')

    for service in ('su', 'su-l'):
        name = '/etc/pam.d/' + service
        lines = read(name)
        if lines is None:
            continue
        print(f'[PAM 파일] {name}')
        found = False
        for number, line in enumerate(lines, 1):
            text = line.strip()
            if not text or text.startswith('#'):
                continue
            # 흐름을 해석하지 않고 원문과 줄 번호를 남긴다.
            print(f'  {number}: {text}')
            found = True
        if not found:
            warn(name + ': 활성 줄 없음')
    print('[범위] 로컬 파일 수집; PAM 흐름·모듈 로딩·NSS·ACL은 별도 확인')
    print('[판정] 자동 판정하지 않음')
    return 2 if incomplete else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='/', help='수집할 파일 트리')
    parser.add_argument('--group', default='wheel', help='확인할 허용 그룹')
    parser.add_argument('--su', default='/usr/bin/su', help='확인할 su 경로')
    args = parser.parse_args()
    try:
        return collect(pathlib.Path(args.root).resolve(), args.group, args.su)
    except (OSError, ValueError, RuntimeError) as error:
        print('[확인 필요] 수집 경로 오류: ' + type(error).__name__)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
