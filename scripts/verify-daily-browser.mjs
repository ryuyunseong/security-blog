import { chromium } from 'playwright';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { readPosts } from './daily-publish.mjs';

const base = process.env.BLOG_QA_ORIGIN || 'http://127.0.0.1:4322/security-blog/';
const bundle = await readFile('.qa/daily-bundle.json', 'utf8').then(JSON.parse).catch(() => null);
const posts = await readPosts();
const slugs = bundle ? bundle.articles.map((a) => a.slug) : posts.filter((p) => !p.draft && new Date(p.date) <= new Date())
  .sort((a, b) => Date.parse(b.date) - Date.parse(a.date)).slice(0, 2).map((p) => p.slug);
const seriesCount = posts.filter((p) => !p.draft && new Date(p.date) <= new Date() && p.series === 'unix-2026').length;
const browser = await chromium.launch({ headless: true,
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}) });
try {
  await mkdir('.qa/browser', { recursive: true });
  const page = await browser.newPage({ reducedMotion: 'reduce' }), errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  let checks = 0;
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1080 });
    await page.goto(base + 'series/critical-infrastructure-unix-2026/');
    assert.equal(await page.locator('.post-row').count(), seriesCount);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); checks++;
    for (const slug of slugs) {
      await page.goto(base + `posts/${slug}/`);
      assert.equal(await page.locator('h1').count(), 1);
      assert.ok(await page.locator('.article-visual img').first().evaluate((img) => img.complete && img.naturalWidth === 960));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      if (bundle) assert.ok((await page.locator('.execution-output').first().innerText()).trim());
      const overflow = await page.evaluate(async () => {
        const image = document.querySelector('.article-visual img');
        const source = await fetch(image.src).then((r) => r.text());
        const svg = new DOMParser().parseFromString(source, 'image/svg+xml').documentElement;
        svg.style.position = 'fixed'; svg.style.left = '-2000px'; document.body.append(svg);
        const outside = [...svg.querySelectorAll('text')].filter((node) => { const b = node.getBBox(); return b.x < 0 || b.x + b.width > 960 || b.y < 0 || b.y + b.height > 540; }).map((n) => n.textContent);
        svg.remove(); return outside;
      });
      assert.deepEqual(overflow, [], `${slug}: 도식 글자 경계`);
      await page.locator('.article-visual').scrollIntoViewIfNeeded();
      await page.screenshot({ path: `.qa/browser/${slug}-${width}.png` }); checks++;
    }
  }
  assert.deepEqual(errors, []);
  const result = { passed: true, checks, slugs, widths: [1440, 390, 320], errors };
  await writeFile('.qa/browser/result.json', JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify(result));
} finally { await browser.close(); }
