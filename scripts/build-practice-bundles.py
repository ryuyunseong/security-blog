"""글별 실습 파일과 실행 안내를 재현 가능한 ZIP으로 만든다."""
import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path('src/data/practice-bundles.json')
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}')


def checked_file(root, name):
    """다운로드 폴더 안의 명시한 일반 파일만 읽는다."""
    parts = PurePosixPath(name)
    if (not name or '\\' in name or parts.is_absolute()
            or any(part in {'.', '..'} for part in name.split('/'))
            or not all(NAME.fullmatch(part) for part in parts.parts)):
        raise ValueError(f'다운로드 경로 형식 오류: {name}')
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'다운로드 파일 범위 오류: {name}')
    return path.read_bytes()


def article_source(root, slug):
    if not SLUG.fullmatch(slug):
        raise ValueError('글 슬러그 형식 오류')
    source = (root / 'src/content/posts' / f'{slug}.md').read_text(encoding='utf-8')
    front = source.split('\n---\n', 1)[0]
    if not re.search(r'^draft: false$', front, re.M):
        raise ValueError(f'공개하지 않은 글: {slug}')
    date = json.loads(re.search(r'^date: (.+)$', front, re.M)[1])
    when = datetime.fromisoformat(date.replace('Z', '+00:00'))
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone(timedelta(hours=9)))
    if when > datetime.now(timezone.utc):
        raise ValueError(f'미래 날짜 글: {slug}')
    title = json.loads(re.search(r'^title: (.+)$', front, re.M)[1])
    return title, source


def member_files(root, slug, entry):
    title, source = article_source(root, slug)
    blocks = re.findall(r'^```([^\n]*)\n([\s\S]*?)\n```\s*$', source, re.M)
    members = {}
    for item in entry['files']:
        name = item['name']
        if not NAME.fullmatch(name) or name in {'.', '..'} or name.casefold() == 'readme.md':
            raise ValueError(f'ZIP 파일 이름 오류: {name}')
        if name.casefold() in {key.casefold() for key in members}:
            raise ValueError(f'ZIP 파일 이름 중복: {name}')
        if ('source' in item) == ('block' in item):
            raise ValueError('파일 원본 또는 본문 코드 중 하나만 필요함')
        if 'source' in item:
            data = checked_file(root / 'public/downloads', item['source'])
        else:
            index = item['block']
            if type(index) is not int or not 0 <= index < len(blocks):
                raise ValueError('본문 코드 번호 오류')
            language, code = blocks[index]
            if language != item['language'] or language != 'bash':
                raise ValueError('준비 스크립트의 본문 언어 불일치')
            data = (code + '\n').encode('utf-8')
        members[name] = data
    if not members or not entry['steps']:
        raise ValueError('실습 파일과 실행 명령이 필요함')
    members['README.md'] = readme(slug, title, entry, members).encode('utf-8')
    return members


def readme(slug, title, entry, members):
    lines = [f'# {title}', '', f'본문: https://ryuyunseong.github.io/security-blog/posts/{slug}/', '',
             '## 준비', '', entry['requirements'], '',
             'ZIP을 빈 폴더에 풀고, 아래 파일이 모여 있는 폴더로 이동한다.',
             'Windows에서는 파일 탐색기의 모두 추출을 사용할 수 있다.',
             '아래 실행 명령은 Linux/WSL의 Bash 기준이다. Python 예제의 assert 검사를 끄는 -O 옵션은 사용하지 않는다.', '',
             '```bash', f'cd {slug}', '```', '', '## 포함 파일', '']
    lines += [f'- `{name}`' for name in members]
    lines += ['- `README.md`: 준비 조건, 실행 명령과 결과 읽는 방법', '', '## 실행', '']
    for number, step in enumerate(entry['steps'], 1):
        if type(step['exitCode']) is not int or not 0 <= step['exitCode'] <= 255:
            raise ValueError('예상 종료 코드 형식 오류')
        command = step['command']
        if not isinstance(command, str) or any(x in command for x in ['\n', '\r', '```']):
            raise ValueError('실행 명령 형식 오류')
        if 'stdin' in step:
            if step['stdin'] not in members:
                raise ValueError('표준 입력 파일 누락')
            command += f" < {step['stdin']}"
        lines += [f'### {number}', '', '```bash', command, 'echo $?', '```', '',
                  f"예상 종료 코드: {step['exitCode']}. {step['expected']}", '']
    if entry['notes']:
        lines += ['## 실행 조건과 정리', ''] + [f'- {note}' for note in entry['notes']] + ['']
    if any(step['exitCode'] == 1 for step in entry['steps']):
        lines += ['종료 코드 1이 예상된 단계는 차이나 정책 거부를 재현하는 실습이다. 해당 단계의 기대 출력과 함께 읽는다.', '']
    return '\n'.join(lines)


def archive_bytes(slug, members):
    if not SLUG.fullmatch(slug):
        raise ValueError('글 슬러그 형식 오류')
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(f'{slug}/{name}', (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def build(root=ROOT, check=False):
    manifest_path = root / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['version'] != 1:
        raise ValueError('지원하지 않는 묶음 형식 버전')
    expected = set()
    changed = []
    for slug, entry in manifest['posts'].items():
        members = member_files(root, slug, entry)
        data = archive_bytes(slug, members)
        relative = f'downloads/bundles/{slug}.zip'
        target = root / 'public' / relative
        if not target.resolve().is_relative_to((root / 'public/downloads').resolve()):
            raise ValueError(f'ZIP 출력 경로 범위 오류: {slug}')
        expected.add(target.name)
        metadata = {'path': relative, 'bytes': len(data), 'sha256': sha256(data).hexdigest(),
                    'members': {name: sha256(body).hexdigest() for name, body in sorted(members.items())}}
        if target.is_symlink():
            raise ValueError(f'ZIP 출력은 심볼릭 링크일 수 없음: {slug}')
        if not target.exists() or target.read_bytes() != data or entry.get('archive') != metadata:
            changed.append(slug)
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                entry['archive'] = metadata
    extra = {p.name for p in (root / 'public/downloads/bundles').glob('*.zip')} - expected
    if extra:
        raise ValueError(f'목록에 없는 ZIP: {sorted(extra)}')
    if check and changed:
        raise ValueError(f'실습 ZIP 재생성 필요: {", ".join(changed)}')
    if not check:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    return len(manifest['posts']), changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='파일을 쓰지 않고 본문·원본 파일·ZIP의 일치를 검사')
    arguments = parser.parse_args()
    count, changed = build(check=arguments.check)
    print(f'실습 ZIP {count}개 {"검사 통과" if arguments.check else f"생성 ({len(changed)}개 갱신)"}')
