import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { read, publishedPosts } from './content-helpers.mjs';
import { categories, classificationError } from '../src/lib/taxonomy.mjs';
import { renderArticleBlocks, studyAnswerHeadingIds } from '../src/lib/article-markdown.mjs';

const slug = 'cs-study-01-database-sql';

test('전산·NCS 해설은 문제별 기본 접힘을 유지하고 내부 Markdown을 보존한다', async () => {
  for (const post of (await publishedPosts()).filter((item) => item.category === 'cs-study')) {
    const answers = [...post.source.matchAll(/<details\b([^>]*\bclass="study-answer"[^>]*)>([\s\S]*?)<\/details>/g)];
    const questions = [...post.source.matchAll(/^### 문제 [1-5]\. /gm)];
    assert.equal(answers.length, 5, post.slug);
    assert.equal(questions.length, 5, post.slug);
    for (const [index, answer] of answers.entries()) {
      assert.ok(!/\bopen(?:\s|=|$)/.test(answer[1]), post.slug);
      assert.match(answer[2], new RegExp(`<summary>문제 ${index + 1} 정답·해설 보기</summary>`));
      assert.ok(questions[index].index < answer.index, `${post.slug}: 문제 뒤의 해설`);
      const next = questions[index + 1]?.index ?? post.source.indexOf('\n## ', answer.index);
      assert.ok(answer.index + answer[0].length <= next, `${post.slug}: 다음 문제 앞의 해설`);
      assert.equal(post.source.slice(answer.index + answer[0].length, next).trim(), '', `${post.slug}: 문제와 해설 짝의 연속 배치`);
    }
  }
  const source = '<details class="study-answer">\n<summary>문제 1 정답·해설 보기</summary>\n\n### 문제 1: ③\n\n선택한 이유\n\n```text\n5 | 4\n```\n\n</details>';
  const [rendered] = await renderArticleBlocks([{ type: 'markdown', text: source }], [{ depth: 3, slug: 'original-answer-anchor' }]);
  assert.match(rendered.html, /<details class="study-answer">/);
  assert.ok(!/<details\b[^>]*\bopen\b/.test(rendered.html));
  assert.ok(rendered.html.includes('<h3 id="original-answer-anchor">문제 1: ③</h3>'));
  assert.ok(rendered.html.includes('선택한 이유') && rendered.html.includes('5 | 4'));
  assert.deepEqual([...studyAnswerHeadingIds([rendered])], ['original-answer-anchor']);
});

test('문제 바로 아래로 옮긴 해설 제목만 위치와 무관하게 목차에서 구별한다', async () => {
  const text = '### 문제 1. SQL\n\n질문\n\n<details class="study-answer">\n<summary>정답·해설 보기</summary>\n\n### 첫 해설\n\n답\n\n</details>\n\n### 문제 2. NULL';
  const rendered = await renderArticleBlocks([{ type: 'markdown', text }], [
    { depth: 3, slug: 'question-1' }, { depth: 3, slug: 'answer-1' }, { depth: 3, slug: 'question-2' },
  ]);
  assert.deepEqual([...studyAnswerHeadingIds(rendered)], ['answer-1']);
  assert.deepEqual([...studyAnswerHeadingIds([{ type: 'diagram' }])], []);
});

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
