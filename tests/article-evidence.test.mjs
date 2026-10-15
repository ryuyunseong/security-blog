import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const read = async (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const visuals = JSON.parse(await read('src/data/article-visuals.json'));
const executions = JSON.parse(await read('src/data/executions.json'));
const contexts = JSON.parse(await read('src/data/execution-context.json'));
const manifest = JSON.parse(await read('src/data/migration.json'));
const published = manifest.posts.filter((post) => post.status === 'migrated').map((post) => post.slug).sort();

test('21편에 설명 도식을 제공하고 외부 실행 코드가 없는 SVG로 보관한다', async () => {
  assert.deepEqual(Object.keys(visuals).sort(), published);
  for (const [slug, visual] of Object.entries(visuals)) {
    const svg = await read(`public/assets/posts/${slug}.svg`);
    assert.ok(svg.includes('<title id="title">'));
    assert.ok(svg.includes(visual.caption));
    assert.ok(!/<script|onload=|foreignObject|href=/i.test(svg));
    assert.ok(visual.caption.length > 15);
    if (visual.photo) {
      assert.match(visual.photo.caption, /AI 생성/);
      assert.match(visual.photo.src, /^assets\/posts\/[\w-]+\.png$/);
      const image = await readFile(new URL(`../public/${visual.photo.src}`, import.meta.url));
      assert.equal(image.subarray(1, 4).toString(), 'PNG');
      assert.equal(image.readUInt32BE(16), visual.photo.width);
      assert.equal(image.readUInt32BE(20), visual.photo.height);
    }
  }
});

test('17편 20개 실행 기록이 현재 본문 코드와 일치하며 환경·범위를 명시한다', async () => {
  assert.equal(Object.keys(executions.posts).length, 17);
  assert.deepEqual(Object.keys(contexts).sort(), Object.keys(executions.posts).sort());
  assert.equal(Object.values(executions.posts).reduce((sum, post) => sum + post.runs.length, 0), 20);
  assert.equal(executions.pythonSyntaxCount, 13);
  assert.ok(Number.isFinite(Date.parse(executions.recordedAt)));
  assert.match(executions.environment.os, /Ubuntu/);
  for (const [slug, evidence] of Object.entries(executions.posts)) {
    assert.ok(published.includes(slug));
    const source = (await read(`src/content/posts/${slug}.md`)).replace(/\r\n/g, '\n');
    const blocks = [...source.matchAll(/^(`{3,4})([\w+-]*)\n(.*?)\n\1\s*$/gms)].map((match) => match[3]);
    const hash = createHash('sha256').update(blocks.join('\0')).digest('hex');
    assert.equal(evidence.sourceCodeSha256, hash, `${slug}: 코드 변경 후 실행 결과 갱신 필요`);
    assert.ok(contexts[slug].scope.length > 20 && contexts[slug].finding.length > 20);
    for (const run of evidence.runs) {
      assert.ok(run.command && run.label && run.stdout);
      assert.ok(Number.isInteger(run.exitCode));
      assert.ok(!/C:\\Users\\|\/home\/(?!oldvendor)|security-blog-examples-/i.test(run.stdout));
    }
  }
  assert.ok(!Object.keys(executions.posts).some((slug) => slug.startsWith('qualys-')));
});

test('출처 안내는 콘텐츠와 사이트 설정에 남기지 않는다', async () => {
  for (const slug of published) assert.ok(!/tistory|티스토리|^sourceUrl:|^migrated:/im.test(await read(`src/content/posts/${slug}.md`)));
  for (const path of ['src/pages/index.astro', 'src/pages/portfolio.astro', 'src/components/TopicRail.astro', 'src/layouts/BaseLayout.astro', 'src/lib/site.ts']) {
    assert.ok(!/tistory|티스토리|isBasedOn/i.test(await read(path)), path);
  }
});
