import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { publishedPosts } from './content-helpers.mjs';
import { articleDiagramFrame, renderArticleDiagram } from '../src/lib/article-diagrams.mjs';
import { renderMobileArticleDiagram, wrapDiagramText } from '../src/lib/article-diagrams-mobile.mjs';
import { escapeXml } from '../src/lib/core.mjs';

const read = async (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const visuals = JSON.parse(await read('src/data/article-visuals.json'));
const executions = JSON.parse(await read('src/data/executions.json'));
const contexts = JSON.parse(await read('src/data/execution-context.json'));
const published = (await publishedPosts()).map((post) => post.slug).sort();

test('공개 글에 설명 도식을 제공하고 외부 실행 코드가 없는 SVG로 보관한다', async () => {
  assert.deepEqual(Object.keys(visuals).sort(), published);
  for (const [slug, visual] of Object.entries(visuals)) {
    const svg = await read(`public/assets/posts/${slug}.svg`);
    assert.equal(svg, renderArticleDiagram(visual) + '\n', `${slug}: 도식 재생성 필요`);
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

test('모바일 도식도 모든 문구와 범위를 보존하고 실행 코드가 없는 SVG로 재생성한다', async () => {
  for (const [slug, visual] of Object.entries(visuals)) {
    const mobile = renderMobileArticleDiagram(visual);
    const svg = await read(`public/assets/posts/${slug}.mobile.svg`);
    assert.equal(svg, mobile.svg + '\n', `${slug}: 모바일 도식 재생성 필요`);
    assert.equal(mobile.width, 360);
    assert.ok(mobile.height > 240 && mobile.height < 1800, slug);
    assert.ok(!/<script|onload=|foreignObject|href=/i.test(svg));
    const text = svg.replace(/<[^>]*>/g, '').replace(/\s/g, '');
    for (const value of [visual.title, visual.note, ...visual.nodes.flat()]) {
      assert.ok(text.includes(escapeXml(value).replace(/\s/g, '')), `${slug}: 모바일 문구 보존: ${value}`);
    }
  }
});

test('그림에는 노드와 관계를 표시하고 전체 제목·보충 설명은 메타데이터에 보존한다', () => {
  for (const [slug, visual] of Object.entries(visuals)) {
    const desktop = renderArticleDiagram(visual);
    const frame = articleDiagramFrame(visual.kind);
    assert.ok(desktop.includes(`height="${frame.height}" viewBox="${frame.viewBox}"`), slug);
    assert.ok(frame.height < 540, slug);
    for (const svg of [desktop, renderMobileArticleDiagram(visual).svg]) {
      assert.ok(!/<text\b[^>]*><\/text>/.test(svg), `${slug}: 빈 문구 요소`);
      const visible = [...svg.matchAll(/<text\b[^>]*>([\s\S]*?)<\/text>/g)]
        .map((match) => match[1].replace(/<[^>]*>/g, '')).join('').replace(/\s/g, '');
      assert.ok(svg.includes(`<title id="title">${escapeXml(visual.title)}</title>`), slug);
      assert.ok(svg.includes(`<desc id="desc">${escapeXml(`${visual.caption} ${visual.note}`)}</desc>`), slug);
      for (const value of visual.nodes.flat()) {
        assert.ok(visible.includes(escapeXml(value).replace(/\s/g, '')), `${slug}: 노드 문구 보존: ${value}`);
      }
      for (const duplicate of [visual.title, visual.note, '보안 노트', '왼쪽에서 오른쪽으로 진행']) {
        assert.ok(!visible.includes(escapeXml(duplicate).replace(/\s/g, '')), `${slug}: 반복 문구 표시: ${duplicate}`);
      }
    }
  }
});

test('모바일 줄바꿈은 긴 식별자를 생략하지 않고 XML 문구를 안전하게 표시한다', () => {
  const value = '긴 식별자 PermitRootLogin과 한글 문구';
  const lines = wrapDiagramText(value, 8);
  assert.ok(lines.length > 2);
  assert.equal(lines.join('').replace(/\s/g, ''), value.replace(/\s/g, ''));
  const svg = renderMobileArticleDiagram({ ...visuals['u-03-account-lockout'], title: '<설정 & 조건>' }).svg;
  assert.ok(svg.includes('&lt;설정 &amp; 조건&gt;'));
  assert.ok(!svg.includes('<설정'));
  const range = renderMobileArticleDiagram(visuals['cidr-interval-binary-search']).svg;
  assert.ok(range.includes('width="164"') && range.includes('width="82"') && range.includes('width="328"'));
});

test('도식은 입력 문구를 XML로 이스케이프하고 알 수 없는 형식을 거부한다', () => {
  const visual = { ...visuals['u-03-account-lockout'], title: '<설정 & 조건>', nodes: [['<첫째>', 'A & B', '"범위"'], ['둘째', '조건', '결과'], ['셋째', '조건', '결과']] };
  const svg = renderArticleDiagram(visual);
  assert.ok(svg.includes('&lt;설정 &amp; 조건&gt;') && svg.includes('&lt;첫째&gt;'));
  assert.ok(!svg.includes('<첫째>'));
  assert.throws(() => renderArticleDiagram({ ...visual, kind: 'unknown' }), /도식 종류/);
  assert.throws(() => renderArticleDiagram({ ...visual, nodes: visual.nodes.slice(1) }), /노드 수/);
});

test('주소 구간의 길이는 양 끝을 포함하며 빈틈이나 잘못된 합집합을 그리지 않는다', () => {
  const visual = visuals['cidr-interval-binary-search'];
  const svg = renderArticleDiagram(visual);
  assert.ok(svg.includes('x="300" y="166" width="300"'));
  assert.ok(svg.includes('x="450" y="300" width="150"'));
  assert.ok(svg.includes('x="300" y="367" width="600"'));
  for (const [start, end] of [['-1', '127'], ['0', '256'], ['128', '127'], ['00', '127'], ['0.5', '127'], ['0', 'NaN']]) {
    assert.throws(() => renderArticleDiagram({ ...visual, nodes: [[visual.nodes[0][0], start, end], ...visual.nodes.slice(1)] }), /구간/);
  }
  const nodes = structuredClone(visual.nodes);
  nodes[3][2] = '254';
  assert.throws(() => renderArticleDiagram({ ...visual, nodes }), /합집합/);
  const gap = [['앞', '0', '10'], ['뒤', '12', '20'], ['중첩', '2', '5'], ['병합', '0', '20']];
  assert.throws(() => renderArticleDiagram({ ...visual, nodes: gap }), /빈 구간/);
  const single = [['첫째', '255', '255'], ['둘째', '255', '255'], ['셋째', '255', '255'], ['병합', '255', '255']];
  assert.ok(renderArticleDiagram({ ...visual, nodes: single }).includes('width="2.34375"'));
});

test('실행 기록이 현재 본문 코드와 일치하며 환경·범위를 명시한다', async () => {
  assert.ok(Object.keys(executions.posts).length >= 17);
  assert.deepEqual(Object.keys(contexts).sort(), Object.keys(executions.posts).sort());
  assert.ok(Object.values(executions.posts).reduce((sum, post) => sum + post.runs.length, 0) >= 20);
  assert.ok(executions.pythonSyntaxCount >= 13);
  assert.ok(Number.isFinite(Date.parse(executions.recordedAt)));
  assert.match(executions.environment.os, /Ubuntu/);
  for (const [slug, evidence] of Object.entries(executions.posts)) {
    assert.ok(published.includes(slug));
    const environment = evidence.environment ?? executions.environment;
    assert.ok(environment.os && environment.python && environment.pythonSsl && environment.openssl, slug);
    assert.ok(Number.isFinite(Date.parse(evidence.recordedAt ?? executions.recordedAt)), slug);
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
  // 문서 해설로 작성한 기존 글에 제품 실행 결과를 덧붙이지 않는다.
  for (const slug of ['qualys-authenticated-scan', 'qualys-collection-coverage', 'qualys-learning-environment', 'qualys-vulnerability-management']) {
    assert.ok(!Object.hasOwn(executions.posts, slug));
  }
});

test('외부 블로그 안내는 콘텐츠와 사이트 설정에 남기지 않는다', async () => {
  const legacy = /ti\u0073tory|\uD2F0\uC2A4\uD1A0\uB9AC|^sourceUrl:|^migrated:/im;
  for (const slug of published) assert.ok(!legacy.test(await read(`src/content/posts/${slug}.md`)));
  for (const path of ['src/pages/index.astro', 'src/pages/portfolio.astro', 'src/components/TopicRail.astro', 'src/layouts/BaseLayout.astro', 'src/lib/site.ts']) {
    assert.ok(!legacy.test(await read(path)) && !(await read(path)).includes('isBasedOn'), path);
  }
});
