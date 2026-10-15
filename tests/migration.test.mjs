import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const manifest = JSON.parse(await readFile(new URL('../src/data/migration.json', import.meta.url), 'utf8'));
const migrated = manifest.posts.filter((post) => post.status === 'migrated');
const content = new URL('../src/content/posts/', import.meta.url);

test('공개 원문 24편의 이전·유지 결정을 누락 없이 기록한다', () => {
  assert.equal(manifest.sourceCount, 24);
  assert.equal(manifest.posts.length, 24);
  assert.equal(new Set(manifest.posts.map((post) => post.url)).size, 24);
  assert.equal(migrated.length, 21);
  assert.equal(manifest.posts.filter((post) => post.status === 'retained').length, 3);
});

test('주통기 U-01부터 U-10까지 순서와 최초 발행일을 유지한다', async () => {
  const series = migrated.filter((post) => post.seriesOrder).sort((a, b) => a.seriesOrder - b.seriesOrder);
  assert.deepEqual(series.map((post) => post.seriesOrder), Array.from({ length: 10 }, (_, index) => index + 1));
  for (const post of series) {
    const source = (await readFile(new URL(`${post.slug}.md`, content), 'utf8')).replace(/\r\n/g, '\n');
    assert.ok(source.includes(`seriesOrder: ${post.seriesOrder}\n`));
    assert.ok(source.includes('series: "unix-2026"'));
    assert.ok(!/^sourceUrl:|^migrated:/m.test(source));
    assert.ok(source.includes(`date: "${post.date}"`));
  }
});

test('이전한 코드 95개를 원문의 블록 순서·본문 해시와 대조한다', async () => {
  let count = 0;
  for (const post of migrated) {
    const source = (await readFile(new URL(`${post.slug}.md`, content), 'utf8')).replace(/\r\n/g, '\n');
    const blocks = [...source.matchAll(/^(`{3,4})([\w+-]*)\n(.*?)\n\1\s*$/gms)].map((match) => match[3]);
    assert.equal(blocks.length, post.sourceCodeCount, `${post.slug}: 코드 개수`);
    assert.equal(createHash('sha256').update(blocks.join('\0')).digest('hex'), post.sourceCodeSha256, `${post.slug}: 코드 본문`);
    count += blocks.length;
    assert.ok(source.includes('draft: false'));
    assert.ok(!source.includes('<script'));
  }
  assert.equal(count, 95);
});

test('공개 콘텐츠는 이전한 글로만 구성하며 초기 예제는 초안으로 보관한다', async () => {
  const publicFiles = [];
  for (const file of await readdir(content)) {
    const source = await readFile(new URL(file, content), 'utf8');
    if (/^draft: false$/m.test(source) && file !== 'future-example.md') publicFiles.push(file.replace(/\.md$/, ''));
  }
  assert.deepEqual(publicFiles.sort(), migrated.map((post) => post.slug).sort());
});
