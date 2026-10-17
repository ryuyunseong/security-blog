import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import { resolve, relative, sep } from 'node:path';

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
  check(source.includes('lang="ko"'), `한국어 lang 누락: ${file}`);
  check((source.match(/<h1\b/g) ?? []).length === 1, `h1 개수 오류: ${file}`);
  check(/<title>[^<]+<\/title>/.test(source), `제목 누락: ${file}`);
  check(/name="description"/.test(source), `description 누락: ${file}`);
  check(/rel="canonical"/.test(source), `canonical 누락: ${file}`);
  const pagePath = relative(root, file).split(sep).join('/').replace(/index\.html$/, '');
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
const posts = htmlFiles.filter((file) => relative(root, file).startsWith(`posts${sep}`));
const figures = htmlFiles.filter((file) => relative(root, file).startsWith(`figures${sep}`));
check(figures.length === posts.length, '공개 글과 그림 보기 페이지 수 불일치');
const evidence = JSON.parse(await readFile('src/data/executions.json', 'utf8'));
for (const file of posts) {
  const source = await readFile(file, 'utf8');
  const slug = relative(root, file).split(sep)[1];
  check(/class="article-visual"/.test(source), `설명 도식 누락: ${slug}`);
  check(/<img[^>]+alt="[^"]+"[^>]+width="960"[^>]+height="540"/.test(source), `이미지 크기·대체 텍스트 누락: ${slug}`);
  check(source.includes('id="execution-results"') === Object.hasOwn(evidence.posts, slug), `실행 기록 유무 불일치: ${slug}`);
  check(!/\[\[(?:diagram|photo|run:)/.test(source), `본문 배치 표식 노출: ${slug}`);
  const bodyStart = source.indexOf('class="prose"');
  check(source.indexOf('class="article-visual"') > bodyStart, `본문 밖에 그림을 일괄 배치함: ${slug}`);
  check((source.match(/class="article-visual"/g) ?? []).length === 1, `설명 그림 중복: ${slug}`);
  if (Object.hasOwn(evidence.posts, slug)) {
    check(source.indexOf('id="execution-results"') > bodyStart, `본문 밖에 실행 기록 배치: ${slug}`);
    check((source.match(/data-run="\d+"/g) ?? []).length === evidence.posts[slug].runs.length, `실행 기록 누락·중복: ${slug}`);
  }
  const ids = [...source.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
  check(new Set(ids).size === ids.length, `중복 HTML ID: ${slug}`);
  const figurePath = `${base}figures/${slug}/`;
  const svgPath = `${base}assets/posts/${slug}.svg`;
  const mobilePath = `${base}assets/posts/${slug}.mobile.svg`;
  check(source.includes(`srcset="${mobilePath}"`) && source.includes('media="(max-width: 767px)"'), `모바일 도식 선택 누락: ${slug}`);
  check(source.includes(`href="${figurePath}"`), `그림 보기 링크 누락: ${slug}`);
  check(!source.includes(`href="${svgPath}"`), `그림 링크가 SVG 문서를 직접 엶: ${slug}`);
  const figure = await readFile(resolve(root, 'figures', slug, 'index.html'), 'utf8');
  check(figure.includes(`srcset="${mobilePath}"`) && figure.includes('class="figure-original"'), `그림 보기 모바일·원본 전환 누락: ${slug}`);
  check(/<img\b[^>]*src="[^"]+\.svg"/.test(figure) && figure.includes(`src="${svgPath}"`), `그림 보기 이미지 누락: ${slug}`);
  check(figure.includes(`href="${base}posts/${slug}/"`), `원문 복귀 링크 누락: ${slug}`);
  check([...figure.matchAll(/<a\b[^>]*>/g)].some(([link]) => link.includes(`href="${svgPath}"`) && /\bdownload(?:[\s=>])/.test(link)), `SVG 다운로드 링크 누락: ${slug}`);
  check(figure.includes('name="robots" content="noindex,follow"'), `그림 보기 색인 제외 누락: ${slug}`);
  check(figure.includes(`rel="canonical" href="${new URL(`${base}posts/${slug}/`, home.origin).href}"`), `그림 보기 canonical이 원문과 다름: ${slug}`);
}
check(entries.length === posts.length, '검색 색인과 공개 글 수 불일치');
const rss = await readFile(resolve(root, 'rss.xml'), 'utf8');
check((rss.match(/<item>/g) ?? []).length === posts.length, 'RSS와 공개 글 수 불일치');
const sitemap = await readFile(resolve(root, 'sitemap.xml'), 'utf8');
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
check(!sitemap.includes(`${base}categories/cve/`) && !index.includes(`${base}categories/cve/`), '빈 CVE 카테고리 노출');
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
