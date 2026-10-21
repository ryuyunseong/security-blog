from copy import deepcopy
from hashlib import sha256
import gzip
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bundles', ROOT / 'scripts/build-practice-bundles.py')
bundles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundles)


class PracticeBundlesTests(unittest.TestCase):
    def test_archives_match_sources_and_safe_members(self):
        count, changed = bundles.build(check=True)
        manifest = json.loads((ROOT / bundles.MANIFEST).read_text(encoding='utf-8'))
        self.assertEqual(count, len(manifest['posts']))
        self.assertEqual(changed, [])
        for slug, entry in manifest['posts'].items():
            expected = bundles.member_files(ROOT, slug, entry)
            with self.subTest(slug=slug), zipfile.ZipFile(ROOT / 'public' / entry['archive']['path']) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(sorted(archive.namelist()), sorted(f'{slug}/{name}' for name in expected))
                for info in archive.infolist():
                    name = info.filename.split('/')[1]
                    self.assertEqual(len(info.filename.split('/')), 2)
                    self.assertTrue(stat.S_ISREG(info.external_attr >> 16))
                    self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                    self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                    self.assertEqual(archive.read(info), expected[name])
                    self.assertEqual(sha256(archive.read(info)).hexdigest(), entry['archive']['members'][name])
                readme = archive.read(f'{slug}/README.md').decode('utf-8')
                self.assertIn(f'cd {slug}', readme)
                self.assertIn('예상 종료 코드:', readme)
                self.assertNotRegex(readme, r'C:\\Users\\|\.codex|OPENAI_API_KEY')

    def test_gzip_input_is_the_documented_fixture(self):
        source = ROOT / 'public/downloads/gzip-sample.gz'
        self.assertEqual(gzip.decompress(source.read_bytes()), b'A' * 65536)
        with zipfile.ZipFile(ROOT / 'public/downloads/bundles/gzip-output-limit.zip') as archive:
            self.assertEqual(archive.read('gzip-output-limit/sample.gz'), source.read_bytes())

    def test_source_paths_cannot_leave_download_directory(self):
        root = ROOT / 'public/downloads'
        for name in ['../README.md', '/etc/passwd', 'a/../../passwd', 'a\\file.py',
                     'C:/file.py', './gzip_limit.py', 'a//file.py', '', '.env']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                bundles.checked_file(root, name)

    def test_member_name_and_code_index_are_validated(self):
        entry = json.loads((ROOT / bundles.MANIFEST).read_text(encoding='utf-8'))['posts']['u-07-unused-accounts']
        for name in ['../x.py', '/x.py', 'a/x.py', 'a\\x.py', '..', 'README.md']:
            broken = deepcopy(entry)
            broken['files'][0]['name'] = name
            with self.subTest(name=name), self.assertRaises(ValueError):
                bundles.member_files(ROOT, 'u-07-unused-accounts', broken)
        broken = deepcopy(entry)
        broken['files'].append(deepcopy(broken['files'][0]))
        with self.assertRaisesRegex(ValueError, '중복'):
            bundles.member_files(ROOT, 'u-07-unused-accounts', broken)
        for index in [True, -1, 999]:
            broken = deepcopy(entry)
            broken['files'][-1]['block'] = index
            with self.subTest(index=index), self.assertRaises(ValueError):
                bundles.member_files(ROOT, 'u-07-unused-accounts', broken)
        with self.assertRaises(ValueError):
            bundles.member_files(ROOT, '../README', entry)

    def test_stale_archive_metadata_and_extra_zip_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='bundle test ') as directory:
            root = Path(directory)
            post = root / 'src/content/posts/example.md'
            post.parent.mkdir(parents=True)
            post.write_text('---\ntitle: "예제"\ndate: "2000-01-01"\ndraft: false\n---\n', encoding='utf-8')
            source = root / 'public/downloads/example.py'
            source.parent.mkdir(parents=True)
            source.write_text('print(1)\n', encoding='utf-8')
            manifest = root / bundles.MANIFEST
            manifest.parent.mkdir(parents=True)
            data = {'version': 1, 'posts': {'example': {
                'files': [{'source': 'example.py', 'name': 'example.py'}], 'requirements': 'Python 3.12',
                'steps': [{'command': 'python3 example.py', 'exitCode': 0, 'expected': '1'}], 'notes': [],
            }}}
            manifest.write_text(json.dumps(data), encoding='utf-8')
            self.assertEqual(bundles.build(root), (1, ['example']))
            archive = root / 'public/downloads/bundles/example.zip'
            before = archive.read_bytes()
            self.assertEqual(bundles.build(root, check=True), (1, []))
            source.write_text('print(2)\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '재생성'):
                bundles.build(root, check=True)
            self.assertEqual(archive.read_bytes(), before)
            bundles.build(root)
            (archive.parent / 'extra.zip').write_bytes(b'extra')
            with self.assertRaisesRegex(ValueError, '목록에 없는'):
                bundles.build(root, check=True)

    def test_draft_and_future_article_are_not_packaged(self):
        with tempfile.TemporaryDirectory(prefix='bundle post ') as directory:
            root = Path(directory)
            post = root / 'src/content/posts/example.md'
            post.parent.mkdir(parents=True)
            for date, draft in [('2000-01-01', 'true'), ('9999-01-01', 'false')]:
                post.write_text(f'---\ntitle: "예제"\ndate: "{date}"\ndraft: {draft}\n---\n', encoding='utf-8')
                with self.subTest(date=date), self.assertRaises(ValueError):
                    bundles.article_source(root, 'example')


if __name__ == '__main__':
    unittest.main()
