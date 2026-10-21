import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { publishedPosts } from './content-helpers.mjs';

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const bundles = JSON.parse(await read('src/data/practice-bundles.json'));
const executions = JSON.parse(await read('src/data/executions.json'));

test('공개 실행 예제는 글별 ZIP을 제공하고 모든 개별 준비 파일을 포함한다', async () => {
  const published = (await publishedPosts()).map((post) => post.slug);
  assert.deepEqual(Object.keys(bundles.posts).sort(), Object.keys(executions.posts).sort());
  for (const [slug, bundle] of Object.entries(bundles.posts)) {
    assert.ok(published.includes(slug), slug);
    assert.equal(bundle.archive.path, `downloads/bundles/${slug}.zip`);
    const bytes = await readFile(new URL(`../public/${bundle.archive.path}`, import.meta.url));
    assert.equal(bytes.length, bundle.archive.bytes);
    assert.equal(bytes.readUInt32LE(0), 0x04034b50);
    for (const file of executions.posts[slug].preparationFiles ?? []) {
      assert.ok(bundle.files.some((item) => item.source === file), `${slug}: ${file}`);
    }
  }
});

test('실습 ZIP의 원본 일치·경로 경계·준비 입력·재생성 검사를 통과한다', () => {
  const python = process.platform === 'win32' ? 'python' : 'python3';
  const result = spawnSync(python, ['-I', '-B', '-X', 'utf8', 'tests/practice-bundles.test.py'], {
    cwd: new URL('../', import.meta.url), encoding: 'utf8', timeout: 30000,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.match(result.stderr, /Ran 6 tests/);
  assert.match(result.stderr, /\bOK\b/);
});
