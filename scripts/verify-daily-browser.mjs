import { chromium } from 'playwright';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { readPosts } from './daily-publish.mjs';

const base = process.env.BLOG_QA_ORIGIN || 'http://127.0.0.1:4322/security-blog/';
const bundle = await readFile('.qa/daily-bundle.json', 'utf8').then(JSON.parse).catch(() => null);
const posts = await readPosts();
const evidence = JSON.parse(await readFile('src/data/executions.json', 'utf8'));
const visuals = JSON.parse(await readFile('src/data/article-visuals.json', 'utf8'));
const slugs = bundle && process.env.BLOG_QA_ALL !== '1' ? bundle.articles.map((a) => a.slug) : posts
  .filter((p) => !p.draft && new Date(p.date) <= new Date()).map((p) => p.slug);
const seriesCount = posts.filter((p) => !p.draft && new Date(p.date) <= new Date() && p.series === 'unix-2026').length;
const browser = await chromium.launch({ headless: true,
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}) });
try {
  await mkdir('.qa/browser', { recursive: true });
  const page = await browser.newPage({ reducedMotion: 'reduce' }), errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  let checks = 0;
  const widths = [1440, 767, 390, 320];
  for (const width of widths) {
    await page.setViewportSize({ width, height: 1080 });
    await page.goto(base + 'series/critical-infrastructure-unix-2026/');
    assert.equal(await page.locator('.post-row').count(), seriesCount);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); checks++;
    for (const slug of slugs) {
      await page.goto(base + `posts/${slug}/`);
      assert.equal(await page.locator('h1').count(), 1);
      await page.locator('.article-visual img').first().evaluate((img) => img.decode());
      assert.equal(await page.locator('.article-visual img').first().evaluate((img) => img.naturalWidth), width <= 767 ? 360 : 960, `${slug}: 화면에 맞는 도식 선택`);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert.equal(await page.locator('.prose .article-visual').count(), 1);
      assert.equal(await page.locator('.prose .article-photo').count(), Number(Boolean(visuals[slug].photo)));
      assert.ok(!/\[\[(?:diagram|photo|run:)/.test(await page.locator('.prose').innerText()), `${slug}: 배치 표식 노출`);
      const duplicateIds = await page.evaluate(() => {
        const ids = [...document.querySelectorAll('[id]')].map((node) => node.id);
        return ids.filter((id, index) => ids.indexOf(id) !== index);
      });
      assert.deepEqual(duplicateIds, [], `${slug}: 중복 앵커`);
      const source = posts.find((post) => post.slug === slug).source;
      const expectedCode = [...source.matchAll(/^```[^\n]*\n([\s\S]*?)\n```\s*$/gm)].map((m) => m[1].trimEnd());
      const renderedCode = await page.locator('.prose pre:not(.execution-command):not(.execution-output) > code').allTextContents();
      assert.deepEqual(renderedCode.map((code) => code.trimEnd()), expectedCode, `${slug}: 코드 원문 보존`);
      const runs = evidence.posts[slug]?.runs ?? [];
      assert.equal(await page.locator('.prose .execution-inline').count(), runs.length);
      const actualOutput = await page.locator('.execution-full-output .execution-output code').allTextContents();
      assert.deepEqual(actualOutput.map((output) => output.trimEnd()), runs.map((run) => run.stdout.trimEnd()), `${slug}: 원본 출력 보존`);
      for (const details of await page.locator('.code-details, .execution-run').all()) {
        if (await details.getAttribute('open') === null) {
          await details.locator(':scope > summary').click();
          assert.notEqual(await details.getAttribute('open'), null, `${slug}: 코드·실행 기록 펼치기`);
        }
      }
      for (const output of await page.locator('.execution-full-output').all()) {
        if (await output.getAttribute('open') === null) await output.locator(':scope > summary').click();
        assert.ok(await output.locator('pre').isVisible(), `${slug}: 전체 출력 접근`);
      }
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${slug}: 펼친 뒤 가로 넘침`);
      const overflow = await page.evaluate(async () => {
        const image = document.querySelector('.article-visual img');
        const source = await fetch(image.currentSrc).then((r) => r.text());
        const svg = new DOMParser().parseFromString(source, 'image/svg+xml').documentElement;
        svg.style.position = 'fixed'; svg.style.left = '-2000px'; document.body.append(svg);
        const labels = [...svg.querySelectorAll('text')];
        const bounds = svg.viewBox.baseVal;
        const outside = labels.filter((node) => { const b = node.getBBox(); return b.x < 0 || b.x + b.width > bounds.width || b.y < 0 || b.y + b.height > bounds.height; }).map((n) => n.textContent);
        if (svg.dataset.layout === 'mobile') {
          const scale = image.clientWidth / bounds.width;
          for (const label of labels) {
            const minimum = label.dataset.role === 'key' ? 16 : 14;
            if (Number(label.getAttribute('font-size')) * scale < minimum) outside.push(`작은 글자: ${label.textContent}`);
          }
        }
        if (svg.dataset.layout === 'mobile' || ['matrix', 'timeline', 'decision', 'cycle', 'topology', 'intervals'].includes(svg.dataset.diagramKind)) {
          for (let i = 0; i < labels.length; i++) {
            const a = labels[i].getBBox();
            for (const label of labels.slice(i + 1)) {
              const b = label.getBBox();
              if (a.width && b.width && a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height) {
                outside.push(`문구 겹침: ${labels[i].textContent} / ${label.textContent}`);
              }
            }
          }
        }
        svg.remove(); return outside;
      });
      assert.deepEqual(overflow, [], `${slug}: 도식 글자 경계`);
      await page.locator('.article-visual').scrollIntoViewIfNeeded();
      await page.screenshot({ path: `.qa/browser/${slug}-${width}.png` }); checks++;
      await page.locator('.article-visual a').first().click();
      await page.locator('.figure-scroll picture img').evaluate((img) => img.decode());
      assert.equal(await page.locator('.figure-scroll picture img').evaluate((img) => img.naturalWidth), width <= 767 ? 360 : 960);
      const figureFits = () => page.locator('.figure-scroll').evaluate((region) => region.scrollWidth <= region.clientWidth + 1);
      assert.ok(await figureFits(), `${slug}: 그림 처음 화면 맞춤`);
      await page.locator('.figure-zoom-label').click();
      assert.ok(await page.locator('#figure-zoom').isChecked(), `${slug}: 그림 확대 선택`);
      assert.ok(await page.locator('.figure-original').isVisible(), `${slug}: 원본 확대 표시`);
      assert.equal(await page.locator('.figure-original').evaluate((img) => img.naturalWidth), 960, `${slug}: 확대 원본 해상도`);
      assert.ok(!await page.locator('.figure-scroll picture').isVisible(), `${slug}: 확대 중 중복 그림 숨김`);
      assert.ok(await page.locator('.figure-scroll').evaluate((region) => region.scrollWidth > region.clientWidth), `${slug}: 그림 영역 안에서 확대`);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${slug}: 확대 후 페이지 넘침`);
      await page.locator('.figure-zoom-label').click();
      assert.ok(await page.locator('.figure-scroll picture').isVisible(), `${slug}: 화면별 배치로 복귀`);
      assert.ok(!await page.locator('.figure-original').isVisible(), `${slug}: 원본 확대 숨김`);
      assert.ok(await figureFits(), `${slug}: 그림 화면 맞춤 복귀`); checks++;
    }
  }
  assert.deepEqual(errors, []);
  const result = { passed: true, checks, slugs, widths, origin: base, errors };
  await writeFile('.qa/browser/result.json', JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify(result));
} finally { await browser.close(); }
