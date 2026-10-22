import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import { resolve, relative, sep } from 'node:path';
import { articleDiagramFrame } from '../src/lib/article-diagrams.mjs';
import { categories, assessmentTargets, assessmentSeries, assessmentTargetLabel } from '../src/lib/taxonomy.mjs';
import { readPosts } from './daily-publish.mjs';

const root = resolve('dist');
const index = await readFile(resolve(root, 'index.html'), 'utf8');
const canonical = index.match(/<link\b[^>]*rel="canonical"[^>]*href="([^"]+)"/)?.[1];
assert.ok(canonical, '홈 canonical 누락');
const home = new URL(canonical.replaceAll('&amp;', '&'));
const base = home.pathname;
// 같은 Pages 호스트에서 운영하는 별도 사이트는 블로그 빌드 파일이 아니다.
const externalSites = new Set(['https://ryuyunseong.github.io/security-portfolio/']);
let checks = 0;
const check = (value, message) => { assert.ok(value, message); checks++; };

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  return (await Promise.all(entries.map((entry) => entry.isDirectory()
    ? walk(resolve(directory, entry.name)) : [resolve(directory, entry.name)]))).flat();
}
const files = await walk(root);
const htmlFiles = files.filter((file) => file.endsWith('.html'));
for (const file of files.filter((file) => /\.(html|json|xml|txt)$/.test(file))) {
  const source = await readFile(file, 'utf8');
  check(!/DRAFT_EXCLUSION_SENTINEL|초안검증전용|FUTURE_EXCLUSION_SENTINEL|미래검증전용/.test(source), `비공개 글 노출: ${relative(root, file)}`);
  check(!/ti\u0073tory|\uD2F0\uC2A4\uD1A0\uB9AC|isBasedOn/i.test(source), `사용하지 않는 외부 블로그 안내 노출: ${relative(root, file)}`);
}

for (const file of htmlFiles) {
  const source = await readFile(file, 'utf8');
  const pagePath = relative(root, file).split(sep).join('/').replace(/index\.html$/, '');
  const legacyFigure = pagePath.match(/^figures\/([a-z0-9-]+)\/$/);
  if (legacyFigure || pagePath === 'categories/web/') {
    // Astro의 정적 리다이렉트는 일반 콘텐츠 페이지와 별도로 목적지를 검증한다.
    const target = legacyFigure ? `${base}posts/${legacyFigure[1]}/#article-diagram` : `${base}categories/application-security/`;
    check(source.includes(`<meta http-equiv="refresh" content="0;url=${target}">`), `이전 그림 주소의 본문 이동 누락: ${file}`);
    check(source.includes(`rel="canonical" href="${new URL(target, home.origin).href}"`), `이전 그림 주소의 canonical 오류: ${file}`);
    check(source.includes('name="robots" content="noindex"'), `이전 그림 주소의 색인 제외 누락: ${file}`);
    check(!/<(?:img|button|input)\b/.test(source), `이전 그림 주소에 별도 보기 화면이 남음: ${file}`);
  } else {
    check(source.includes('lang="ko"'), `한국어 lang 누락: ${file}`);
    check((source.match(/<h1\b/g) ?? []).length === 1, `h1 개수 오류: ${file}`);
    check(/<title>[^<]+<\/title>/.test(source), `제목 누락: ${file}`);
    check(/name="description"/.test(source), `description 누락: ${file}`);
    check(/rel="canonical"/.test(source), `canonical 누락: ${file}`);
  }
  const current = new URL(base + pagePath, home.origin);
  for (const match of source.matchAll(/\b(?:href|src|srcset)="([^"]+)"/g)) {
    const ref = match[1].replaceAll('&amp;', '&');
    if (/^(mailto:|tel:|data:)/.test(ref)) continue;
    const url = new URL(ref, current);
    if (url.origin !== home.origin || externalSites.has(url.href)) continue;
    check(url.pathname.startsWith(base), `base 경로 누락: ${ref} (${file})`);
    const localPath = decodeURIComponent(url.pathname.slice(base.length));
    let target = resolve(root, localPath);
    check(target === root || target.startsWith(root + sep), `빌드 경로 이탈: ${ref}`);
    if (url.pathname.endsWith('/')) target = resolve(target, 'index.html');
    check(await stat(target).then((item) => item.isFile(), () => false), `끊어진 내부 링크: ${ref} (${file})`);
    if (url.hash && target.endsWith('.html')) {
      const targetHtml = target === file ? source : await readFile(target, 'utf8');
      check(targetHtml.includes(`id="${decodeURIComponent(url.hash.slice(1))}"`), `존재하지 않는 앵커: ${ref} (${file})`);
    }
  }
}

const entries = JSON.parse(await readFile(resolve(root, 'search.json'), 'utf8'));
const content = (await readPosts()).filter((post) => !post.draft && new Date(post.date) <= new Date());
const posts = htmlFiles.filter((file) => relative(root, file).startsWith(`posts${sep}`));
const figures = htmlFiles.filter((file) => relative(root, file).startsWith(`figures${sep}`));
check(figures.length === posts.length, '공개 글과 이전 그림 주소의 연결 수 불일치');
const evidence = JSON.parse(await readFile('src/data/executions.json', 'utf8'));
const visuals = JSON.parse(await readFile('src/data/article-visuals.json', 'utf8'));
for (const file of posts) {
  const source = await readFile(file, 'utf8');
  const slug = relative(root, file).split(sep)[1];
  const downloadLinks = [...source.matchAll(/<a\b[^>]*\bhref="([^"]+)"/g)]
    .map((match) => new URL(match[1].replaceAll('&amp;', '&'), new URL(base + `posts/${slug}/`, home.origin)))
    .filter((url) => url.origin === home.origin && url.pathname.startsWith(base + 'downloads/'))
    .map((url) => url.pathname);
  const expectedDownloads = Object.hasOwn(evidence.posts, slug) ? [`${base}downloads/bundles/${slug}.zip`] : [];
  check(JSON.stringify(downloadLinks) === JSON.stringify(expectedDownloads), `글별 ZIP 외의 다운로드 링크 또는 묶음 링크 누락: ${slug}`);
  check(/class="article-visual"/.test(source), `설명 도식 누락: ${slug}`);
  const frame = articleDiagramFrame(visuals[slug].kind);
  check(new RegExp(`<img[^>]+alt="[^"]+"[^>]+width="${frame.width}"[^>]+height="${frame.height}"`).test(source), `이미지 크기·대체 텍스트 누락: ${slug}`);
  check(source.includes('id="execution-results"') === Object.hasOwn(evidence.posts, slug), `실행 기록 유무 불일치: ${slug}`);
  check(!/\[\[(?:diagram|photo|download|run:)/.test(source), `본문 배치 표식 노출: ${slug}`);
  const bodyStart = source.indexOf('class="prose"');
  check(source.indexOf('class="article-visual"') > bodyStart, `본문 밖에 그림을 일괄 배치함: ${slug}`);
  check((source.match(/class="article-visual"/g) ?? []).length === 1, `설명 그림 중복: ${slug}`);
  if (Object.hasOwn(evidence.posts, slug)) {
    const downloadPosition = source.indexOf('class="practice-download"');
    check(downloadPosition > bodyStart && downloadPosition < source.indexOf('id="execution-results"'), `실습 ZIP이 본문 밖이나 첫 실행 기록 뒤에 배치됨: ${slug}`);
    check((source.match(/class="practice-download"/g) ?? []).length === 1, `실습 ZIP 안내 누락·중복: ${slug}`);
    check(source.indexOf('id="execution-results"') > bodyStart, `본문 밖에 실행 기록 배치: ${slug}`);
    check((source.match(/data-run="\d+"/g) ?? []).length === evidence.posts[slug].runs.length, `실행 기록 누락·중복: ${slug}`);
  }
  const ids = [...source.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
  check(new Set(ids).size === ids.length, `중복 HTML ID: ${slug}`);
  const figurePath = `${base}figures/${slug}/`;
  const svgPath = `${base}assets/posts/${slug}.svg`;
  const mobilePath = `${base}assets/posts/${slug}.mobile.svg`;
  check(source.includes(`srcset="${mobilePath}"`) && source.includes('media="(max-width: 767px)"'), `모바일 도식 선택 누락: ${slug}`);
  check(!source.includes(`href="${figurePath}"`) && source.includes('id="article-diagram"'), `본문 그림의 직접 읽기 구성 오류: ${slug}`);
  check(!source.includes(`href="${svgPath}"`), `그림 링크가 SVG 문서를 직접 엶: ${slug}`);
  check(source.includes(`src="${svgPath}"`), `본문의 데스크톱 도식 누락: ${slug}`);
  check(!/그림을 누르면 크게|그림 확대|figure-zoom/.test(source), `본문에 그림 확대 안내가 남음: ${slug}`);
}
check(entries.length === posts.length, '검색 색인과 공개 글 수 불일치');
const rss = await readFile(resolve(root, 'rss.xml'), 'utf8');
check((rss.match(/<item>/g) ?? []).length === posts.length, 'RSS와 공개 글 수 불일치');
const sitemap = await readFile(resolve(root, 'sitemap.xml'), 'utf8');
for (const category of categories) {
  const source = await readFile(resolve(root, `categories/${category.id}/index.html`), 'utf8');
  const expected = content.filter((post) => post.category === category.id).map((post) => `${base}posts/${post.slug}/`);
  check(expected.length > 0, `빈 카테고리 노출: ${category.id}`);
  const actual = [...source.matchAll(/<h3\b[^>]*>\s*<a\b[^>]*href="([^"]+)"/g)].map((match) => match[1]);
  check(actual.length === expected.length && expected.every((url) => actual.includes(url)), `카테고리의 글 누락·혼입: ${category.id}`);
  for (const post of content.filter((post) => post.category === category.id)) {
    const label = category.label + (post.assessmentTarget ? ` · ${assessmentTargetLabel(post.assessmentTarget)}` : '');
    check(entries.find((entry) => entry.url === `${base}posts/${post.slug}/`)?.category === label, `검색 카테고리 불일치: ${post.slug}`);
  }
}
check(!sitemap.includes(`${base}categories/web/`), '이전 카테고리가 사이트맵에 포함됨');
const listedPostUrls = (source) => [...source.matchAll(/<h3\b[^>]*>\s*<a\b[^>]*href="([^"]+)"/g)].map((match) => match[1]);
for (const target of assessmentTargets) {
  const path = `categories/critical-infrastructure/${target.id}/`;
  const expected = content.filter((post) => post.category === 'critical-infrastructure' && post.assessmentTarget === target.id)
    .map((post) => `${base}posts/${post.slug}/`);
  check(htmlFiles.includes(resolve(root, path, 'index.html')) === Boolean(expected.length), `점검 대상의 빈 페이지·목록 누락: ${target.id}`);
  check(sitemap.includes(`${base}${path}`) === Boolean(expected.length), `점검 대상 사이트맵 불일치: ${target.id}`);
  if (!expected.length) continue;
  const source = await readFile(resolve(root, path, 'index.html'), 'utf8');
  const actual = listedPostUrls(source);
  check(actual.length === expected.length && expected.every((url) => actual.includes(url)), `대상별 목록의 누락·혼입: ${target.id}`);
}
for (const series of assessmentSeries) {
  const path = `series/${series.route}/`;
  const expected = content.filter((post) => post.series === series.id).sort((a, b) => a.order - b.order)
    .map((post) => `${base}posts/${post.slug}/`);
  check(htmlFiles.includes(resolve(root, path, 'index.html')) === Boolean(expected.length), `시리즈의 빈 목차·페이지 누락: ${series.id}`);
  check(sitemap.includes(`${base}${path}`) === Boolean(expected.length), `시리즈 사이트맵 불일치: ${series.id}`);
  if (!expected.length) continue;
  const source = await readFile(resolve(root, path, 'index.html'), 'utf8');
  check(JSON.stringify(listedPostUrls(source)) === JSON.stringify(expected), `대상별 목차의 순서·누락·혼입: ${series.id}`);
  check(source.includes(`href="${base}categories/critical-infrastructure/${series.target}/"`), `목차의 점검 대상 연결 오류: ${series.id}`);
  const target = await readFile(resolve(root, `categories/critical-infrastructure/${series.target}/index.html`), 'utf8');
  check(target.includes(`href="${base}${path}"`), `대상 목록의 시리즈 목차 연결 오류: ${series.id}`);
}
const archiveFiles = htmlFiles.filter((file) => relative(root, file).startsWith(`archive${sep}`));
const listed = [];
for (const file of archiveFiles) {
  const source = await readFile(file, 'utf8');
  const links = [...source.matchAll(/<h3\b[^>]*>\s*<a\b[^>]*href="([^"]+)"/g)].map((match) => match[1]);
  check(links.length > 0 && links.length <= 12, `전체 글 페이지 크기 오류: ${file}`);
  check(source.includes('aria-label="글 목록 페이지"') && source.includes('aria-current="page"'), `페이지 탐색 누락: ${file}`);
  listed.push(...links);
  const url = new URL(base + relative(root, file).split(sep).join('/').replace(/index\.html$/, ''), home.origin).href;
  check(sitemap.includes(url), `전체 글 페이지 사이트맵 누락: ${file}`);
}
check(listed.length === posts.length && new Set(listed).size === posts.length && entries.every((entry) => listed.includes(entry.url)), '전체 글 목록에 누락·중복된 글이 있음');
check((index.match(/class="post-row"/g) ?? []).length === Math.min(posts.length, 8), '홈 최근 글 수 오류');
for (const entry of entries) {
  check(entry.url.startsWith(base), '검색 URL의 base 누락');
  const url = new URL(entry.url, home).href;
  check(rss.includes(url), `RSS 글 누락: ${entry.url}`);
  check(sitemap.includes(url), `사이트맵 글 누락: ${entry.url}`);
}
check(!sitemap.includes('/404') && !sitemap.includes('/search/'), '색인 제외 페이지가 사이트맵에 포함됨');
check(!sitemap.includes(`<loc>${new URL(base + 'portfolio/', home.origin).href}</loc>`), '포트폴리오 안내 페이지가 사이트맵에 포함됨');
check((await readFile(resolve(root, 'robots.txt'), 'utf8')).includes(new URL(base + 'sitemap.xml', home).href), 'robots 사이트맵 경로 오류');
console.log(`빌드 검증 통과: ${checks}개 검사, ${htmlFiles.length}개 HTML, ${posts.length}개 공개 글, base=${base}`);
