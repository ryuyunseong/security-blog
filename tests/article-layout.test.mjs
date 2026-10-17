import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parseArticleLayout, validateArticleLayout } from '../src/lib/article-layout.mjs';
import { renderArticleBlocks } from '../src/lib/article-markdown.mjs';
import { publishedPosts } from './content-helpers.mjs';

test('본문 배치 표식만 해석하고 코드 안의 같은 문자열은 보존한다', () => {
  const source = '설명\n\n````text\n[[diagram]]\n```\n[[run:9]]\n````\n\n[[diagram]]\n\n이후 설명';
  const blocks = validateArticleLayout(source, { runCount: 0 });
  assert.equal(blocks.filter((b) => b.type === 'diagram').length, 1);
  assert.ok(blocks[0].text.includes('[[run:9]]'));
  assert.throws(() => parseArticleLayout('[[run:0]]'), /형식/);
  for (const text of ['[[diagram]]\n\n끝', '앞\n\n[[diagram]]', '앞\n\n[[diagram]]\n\n[[run:2]]\n\n끝']) {
    assert.throws(() => validateArticleLayout(text, { runCount: 0 }));
  }
});

test('공개 글마다 본문 속 그림과 모든 실행 기록을 한 번씩 배치한다', async () => {
  const evidence = JSON.parse(await readFile(new URL('../src/data/executions.json', import.meta.url), 'utf8'));
  const visuals = JSON.parse(await readFile(new URL('../src/data/article-visuals.json', import.meta.url), 'utf8'));
  for (const post of await publishedPosts()) {
    const body = post.source.slice(post.source.indexOf('\n---\n') + 5);
    const blocks = validateArticleLayout(body, { runCount: evidence.posts[post.slug]?.runs.length ?? 0, hasPhoto: Boolean(visuals[post.slug].photo) });
    assert.ok(blocks.findIndex((b) => b.type === 'diagram') > 0, post.slug);
    const codeEnd = body.lastIndexOf('```');
    if (evidence.posts[post.slug]) assert.ok(body.indexOf('[[run:') > body.indexOf('```'), post.slug);
    assert.ok(codeEnd < body.length);
  }
});

test('자료 사이에 같은 제목이 반복돼도 전체 목차 ID와 긴 코드 내용을 보존한다', async () => {
  const code = Array.from({ length: 75 }, (_, i) => `print(${i})`).join('\n');
  const blocks = parseArticleLayout(`## 확인\n\n설명\n\n[[diagram]]\n\n## 확인\n\n\`\`\`python\n${code}\n\`\`\`\n\n마침`);
  const result = await renderArticleBlocks(blocks, [{ depth: 2, slug: '확인' }, { depth: 2, slug: '확인-1' }]);
  const html = result.filter((b) => b.type === 'markdown').map((b) => b.html).join('');
  assert.ok(html.includes('id="확인"') && html.includes('id="확인-1"'));
  assert.ok(html.includes('class="code-details"') && html.includes('print') && html.includes('74'));
  assert.ok(!html.includes('[[diagram]]'));
});
