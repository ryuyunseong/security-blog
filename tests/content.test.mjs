import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { read, publishedPosts } from './content-helpers.mjs';
import { assessmentSeries } from '../src/lib/taxonomy.mjs';

const baseline = JSON.parse(await read('src/data/content-baseline.json'));
const posts = await publishedPosts();

test('기존 글의 발행일을 보존하며 새 공개 글도 허용한다', () => {
  assert.equal(baseline.posts.length, 21);
  assert.equal(new Set(posts.map((post) => post.slug)).size, posts.length);
  for (const original of baseline.posts) {
    assert.equal(posts.find((post) => post.slug === original.slug)?.date, original.date);
  }
  assert.ok(!posts.some((post) => /^(draft|future)-example$/.test(post.slug)));
});

test('주통기 번호가 중복되거나 빠지지 않고 최초 10편의 순서를 보존한다', () => {
  for (const definition of assessmentSeries) {
    const series = posts.filter((post) => post.series === definition.id).sort((a, b) => a.seriesOrder - b.seriesOrder);
    assert.ok(series.length <= definition.maxOrder);
    assert.deepEqual(series.map((post) => post.seriesOrder), Array.from({ length: series.length }, (_, index) => index + 1));
  }
  const series = posts.filter((post) => post.series === 'unix-2026');
  assert.ok(series.length >= 10);
  for (const original of baseline.posts.filter((post) => post.seriesOrder)) {
    assert.equal(series.find((post) => post.slug === original.slug)?.seriesOrder, original.seriesOrder);
  }
});

test('기존 코드 95개를 개수·순서·본문 해시로 대조한다', () => {
  let count = 0;
  for (const original of baseline.posts) {
    const source = posts.find((post) => post.slug === original.slug)?.source;
    assert.ok(source, original.slug);
    const blocks = [...source.matchAll(/^(`{3,4})([\w+-]*)\n(.*?)\n\1\s*$/gms)].map((match) => match[3]);
    assert.equal(blocks.length, original.codeCount, original.slug);
    assert.equal(createHash('sha256').update(blocks.join('\0')).digest('hex'), original.codeSha256, original.slug);
    count += blocks.length;
    assert.ok(!source.includes('<script'));
  }
  assert.equal(count, 95);
});
