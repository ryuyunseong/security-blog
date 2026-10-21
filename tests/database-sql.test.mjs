import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { read, publishedPosts } from './content-helpers.mjs';
import { categories, classificationError } from '../src/lib/taxonomy.mjs';

const slug = 'cs-study-01-database-sql';

test('전산·NCS 글은 별도 카테고리를 사용하고 다섯 문제와 해설을 보존한다', async () => {
  const post = (await publishedPosts()).find((item) => item.slug === slug);
  assert.ok(post);
  assert.equal(post.category, 'cs-study');
  assert.equal(categories.find((item) => item.id === 'cs-study')?.label, '전산·NCS');
  assert.equal(post.assessmentTarget, undefined);
  assert.equal(post.series, undefined);
  assert.equal(post.seriesOrder, undefined);
  assert.equal(classificationError(post), null);
  for (const pattern of [/^### 문제 [1-5]\. /gm, /^### 문제 [1-5]: /gm]) {
    assert.equal([...post.source.matchAll(pattern)].length, 5);
  }
});

test('SQL 전체 예제 다운로드와 본문은 같은 원본이며 개별 실행 증거를 보존한다', async () => {
  const bytes = await readFile(new URL('../public/downloads/01-database-sql.py', import.meta.url));
  const source = bytes.toString('utf8').replace(/\r\n/g, '\n').trimEnd();
  const post = await read(`src/content/posts/${slug}.md`);
  assert.ok([...post.matchAll(/^```python\n([\s\S]*?)\n```\s*$/gm)].some((match) => match[1] === source));
  const record = JSON.parse(await read('src/data/executions.json')).posts[slug];
  const hash = createHash('sha256').update(bytes).digest('hex');
  assert.equal(record.sourceArtifactSha256, hash);
  assert.equal(record.runs.length, 1);
  assert.equal(record.runs[0].sourceCodeSha256, hash);
  assert.equal(record.runs[0].recordedAt, record.recordedAt);
  assert.equal(record.recordedAt, '2026-10-20T21:14:16+09:00');
  assert.equal(record.environment.sqlite, '3.43.1');
  assert.match(record.runs[0].stdout, /^SQL 결과 22건 및 제약 조건 3건 통과/m);
  assert.match(record.runs[0].stdout, /^q3-equal: \[\]$/m);
  assert.match(record.runs[0].stdout, /^q3-is: \[\[4\]\]$/m);
  assert.match(record.runs[0].stdout, /^q5: \[\[5, 4\]\]$/m);
});