import { readFile, writeFile, readdir, mkdir, mkdtemp, rm, rmdir, lstat, chmod } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { createHash, randomUUID } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { pathToFileURL } from 'node:url';
import { validateArticleLayout } from '../src/lib/article-layout.mjs';
import { diagramTextLimits, validateDiagramNodes } from '../src/lib/diagram-spec.mjs';

const exec = promisify(execFile);
const root = resolve(process.cwd());
const qa = join(root, '.qa');
const topics = JSON.parse(await readFile(new URL('./unix-2026-topics.json', import.meta.url), 'utf8'));
export const sourceHosts = ['www.kisa.kr', 'www.krcert.or.kr', 'docs.qualys.com', 'man7.org',
  'www.gnu.org', 'docs.python.org', 'www.openssh.com', 'www.freedesktop.org', 'documentation.ubuntu.com', 'docs.redhat.com',
  'developer.mozilla.org', 'www.rfc-editor.org'];
const image = 'python:3.12-slim';
const digest = (s) => createHash('sha256').update(s).digest('hex');
const normalized = (s) => s.normalize('NFKC').replace(/\s+/g, ' ').trim();
const titleKey = (s) => normalized(s).toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
function proseKey(s) { return titleKey(s.replace(/^---\n[\s\S]*?\n---\n/, '').replace(/^```[\s\S]*?^```\s*$/gm, '')); }
function substantiallySame(a, b) {
  const shingles = (s) => new Set(Array.from({ length: Math.max(0, s.length - 4) }, (_, i) => s.slice(i, i + 5)));
  const left = shingles(proseKey(a)), right = shingles(proseKey(b));
  if (Math.min(left.size, right.size) < 500) return false;
  return [...left].filter((x) => right.has(x)).length / Math.min(left.size, right.size) > 0.8;
}
function requireThat(condition, message) { if (!condition) throw new Error(message); }
function text(value, min, max, label) {
  requireThat(typeof value === 'string' && value.length >= min && value.length <= max && !/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(value), `${label} 형식 오류`);
}
function keys(value, expected) {
  requireThat(value && typeof value === 'object' && !Array.isArray(value) &&
    JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...expected].sort()), 'JSON 필드 불일치');
}
export function seoulDay(now = new Date()) { return new Date(now.getTime() + 9 * 3600000).toISOString().slice(0, 10); }
export function publicationWindow(now = new Date()) {
  const local = new Date(now.getTime() + 9 * 3600000);
  return [0, 6].includes(local.getUTCDay()) || local.getUTCHours() >= 18;
}
function seoulStamp(now = new Date()) { return new Date(now.getTime() + 9 * 3600000).toISOString().slice(0, 19) + '+09:00'; }
async function json(path, max = 8 * 1024 * 1024) {
  const data = await readFile(path);
  requireThat(data.length <= max, 'JSON 크기 초과');
  try { return JSON.parse(data.toString('utf8')); } catch { throw new Error('JSON 구문 오류'); }
}
async function saveJson(path, data) { await writeFile(path, JSON.stringify(data, null, 2) + '\n'); }
async function git(...args) { return (await exec('git', args, { cwd: root })).stdout.trimEnd(); }
function field(source, name) {
  const frontmatter = source.split('\n---\n')[0];
  return frontmatter.match(new RegExp(`^${name}:\\s*(.*?)\\s*$`, 'm'))?.[1].replace(/^["']|["']$/g, '');
}
export async function readPosts() {
  const directory = join(root, 'src/content/posts');
  return Promise.all((await readdir(directory)).filter((f) => f.endsWith('.md')).map(async (file) => {
    const source = (await readFile(join(directory, file), 'utf8')).replace(/\r\n/g, '\n');
    return { slug: file.slice(0, -3), title: field(source, 'title'), category: field(source, 'category'),
      date: field(source, 'date'), draft: field(source, 'draft') !== 'false',
      series: field(source, 'series'), order: Number(field(source, 'seriesOrder')) || null, source };
  }));
}
export function makePlan(posts, mode, now = new Date()) {
  requireThat(['verify', 'preview', 'publish'].includes(mode), '실행 모드 오류');
  const day = seoulDay(now), requested = [], withheld = [];
  const published = posts.filter((p) => !p.draft && new Date(p.date) <= now);
  const orders = published.filter((p) => p.series === 'unix-2026').map((p) => p.order).sort((a, b) => a - b);
  requireThat(orders.every((order, i) => order === i + 1) && orders.length <= 67, '시리즈 번호 대조 필요');
  const next = topics.topics[orders.length] ?? null;
  const today = (kind) => posts.some((p) => p.category === kind && (kind !== 'unix' || p.series === 'unix-2026') &&
    Number.isFinite(Date.parse(p.date)) && seoulDay(new Date(p.date)) === day);
  const allowedTime = mode !== 'publish' || publicationWindow(now);
  if (allowedTime && next && (mode === 'preview' || !today('unix'))) {
    if (posts.some((p) => p.series === 'unix-2026' && p.order === next.order)) withheld.push({ kind: 'unix', reason: '다음 번호의 기존 초안 확인 필요' });
    else requested.push('unix');
  }
  if (allowedTime && (mode === 'preview' || !today('qualys'))) requested.push('qualys');
  const local = new Date(now.getTime() + 9 * 3600000), weekday = local.getUTCDay();
  local.setUTCDate(local.getUTCDate() - (weekday + 6) % 7);
  const weekStart = local.toISOString().slice(0, 10);
  const practical = posts.filter((p) => ['web', 'infrastructure'].includes(p.category) && Number.isFinite(Date.parse(p.date)));
  const weekCount = practical.filter((p) => {
    const date = seoulDay(new Date(p.date));
    return date >= weekStart && date <= day;
  }).length;
  // 추가 실습은 수·토에 한 편씩 검토한다. 초안과 수동 작성 글도 주간 상한에 포함한다.
  if (allowedTime && [3, 6].includes(weekday) && (mode === 'preview' || (weekCount < 2 && !today('web') && !today('infrastructure')))) {
    const last = (kind) => Math.max(0, ...practical.filter((p) => p.category === kind).map((p) => Date.parse(p.date)));
    requested.push(last('web') <= last('infrastructure') ? 'web' : 'infrastructure');
  }
  return { version: 1, mode, day, requested, withheld, next,
    unixTitle: next ? `U-${String(next.order).padStart(2, '0')}: ${next.title}` : null,
    guideExcerpt: '', sourceHosts, guideUrl: topics.guideUrl, guidePage: topics.guidePage,
    inventory: posts.map(({ slug, title, category, date, draft, order }) => ({ slug, title, category, date, draft, order })) };
}
export function allowedUrl(value) {
  requireThat(typeof value === 'string' && !/[\s<>"'\\]/.test(value), '참고 URL에 허용하지 않는 문자');
  let url;
  try { url = new URL(value); } catch { throw new Error('참고 URL 형식 오류'); }
  requireThat(url.protocol === 'https:' && !url.username && !url.password && (!url.port || url.port === '443') && sourceHosts.includes(url.hostname), '허용되지 않은 참고 URL');
  return url;
}
function cleanHtml(html) {
  return normalized(html.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<[^>]*>/g, ' ').replace(/&#x([\da-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>'));
}
async function fetchText(value) {
  let url = allowedUrl(value);
  for (let i = 0; i < 5; i++) {
    const response = await fetch(url, { redirect: 'manual', signal: AbortSignal.timeout(25000) });
    if (response.status >= 300 && response.status < 400) { url = allowedUrl(new URL(response.headers.get('location'), url).href); continue; }
    requireThat(response.ok && /text\/html|text\/plain/.test(response.headers.get('content-type') ?? ''), '공식 문서 응답 확인 실패');
    const chunks = []; let size = 0;
    for await (const chunk of response.body) { size += chunk.length; requireThat(size <= 3 * 1024 * 1024, '문서 크기 초과'); chunks.push(chunk); }
    return cleanHtml(Buffer.concat(chunks).toString('utf8'));
  }
  throw new Error('문서 리디렉션 한도 초과');
}
export function pythonCode(body) {
  const blocks = [...body.matchAll(/^(`{3})([\w+-]*)\n(.*?)\n\1\s*$/gms)];
  requireThat(blocks.length === 1 && blocks[0][2] === 'python' && (body.match(/^```/gm) ?? []).length === 2, 'Python 예제 하나만 허용');
  const code = blocks[0][3];
  requireThat(code.length < 16000 && (code.match(/\bassert\b/g) ?? []).length >= 3, '예제 크기 또는 검증 조건 확인 필요');
  return code;
}
export function validateArticle(article, plan, posts) {
  keys(article, ['kind', 'slug', 'title', 'description', 'tags', 'body', 'visual', 'sources', 'scope', 'finding']);
  requireThat(plan.requested.includes(article.kind), '요청하지 않은 글 종류');
  const prefix = article.kind === 'unix' ? `u-${String(plan.next.order).padStart(2, '0')}-` :
    { qualys: 'qualys-', web: 'web-', infrastructure: 'infra-' }[article.kind];
  requireThat(typeof article.slug === 'string' && /^[a-z][a-z0-9-]{5,79}$/.test(article.slug) &&
    typeof prefix === 'string' && article.slug.startsWith(prefix),
  '글 경로 형식 오류');
  requireThat(!posts.some((p) => p.slug === article.slug || titleKey(p.title) === titleKey(article.title)), '기존 글과 경로 또는 제목 중복');
  text(article.title, 8, 100, '제목'); text(article.description, 20, 200, '설명');
  if (article.kind === 'unix') requireThat(article.title === plan.unixTitle, '공식 번호·제목 불일치');
  requireThat(Array.isArray(article.tags) && article.tags.length >= 1 && article.tags.length <= 8 && article.tags.every((t) => typeof t === 'string' && /^[\p{L}\p{N}_ -]{1,30}$/u.test(t)), '태그 형식 오류');
  text(article.body, 2000, 24000, '본문'); text(article.scope, 20, 500, '실행 범위'); text(article.finding, 20, 500, '결과 해석');
  const code = pythonCode(article.body);
  validateArticleLayout(article.body, { runCount: 1 });
  const prose = article.body.replace(/^```python\n.*?\n```/gms, '');
  requireThat((prose.match(/^## /gm) ?? []).length >= 4 && /가상/.test(prose) && /실제/.test(prose), '본문 구성·실습 범위 확인 필요');
  requireThat(!/^(?:자료|문서) 확인일\s*:|^#{1,6} .*참고 자료.*\([^\n]*확인\)/m.test(prose), '확인일은 본문 대신 관리 메타데이터에 보관');
  requireThat(!/^---\s*$/m.test(prose) && !/<[!\/?A-Za-z]|!\[|(?:javascript|data|file|vbscript):/i.test(prose), '본문의 실행 가능 마크업 또는 외부 이미지 금지');
  requireThat(!/\]\s*(?:\(|\[)|^\s*\[[^\]]+\]:/m.test(prose), '본문 링크는 sources로 분리');
  requireThat(article.kind === 'unix' || !posts.some((p) => substantiallySame(article.body, p.source)), '기존 본문과 중복');
  requireThat(!/sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}/.test(JSON.stringify(article)), '비밀 값 형태 감지');
  requireThat(!/ti\u0073tory|\uD2F0\uC2A4\uD1A0\uB9AC/i.test(JSON.stringify(article)), '사용하지 않는 외부 서비스 문구 감지');
  for (const match of prose.matchAll(/https?:\/\/[^\s)<>"']+/g)) allowedUrl(match[0]);
  requireThat(Array.isArray(article.sources) && article.sources.length >= 2 && article.sources.length <= 5, '공식 근거 문서 수 확인 필요');
  const urls = new Set();
  for (const source of article.sources) {
    keys(source, ['title', 'url', 'quote']);
    text(source.title, 3, 120, '문서 제목');
    requireThat(!/[<>\[\]\r\n]/.test(source.title), '문서 제목에 허용하지 않는 문자');
    const url = allowedUrl(source.url); url.hash = ''; urls.add(url.href);
    text(source.quote, 12, 180, '문서 근거'); requireThat(source.quote.trim().split(/\s+/).length <= 25, '근거 인용 길이 초과');
  }
  requireThat(urls.size === article.sources.length, '참고 문서 중복');
  requireThat(article.kind !== 'qualys' || [...urls].filter((u) => new URL(u).hostname === 'docs.qualys.com').length >= 2, 'Qualys 공식 근거 부족');
  requireThat(article.kind !== 'unix' || [...urls].includes(topics.guidePage) || [...urls].includes(topics.guideUrl), 'KISA 원문 근거 누락');
  const visual = article.visual;
  keys(visual, ['title', 'kind', 'nodes', 'note', 'caption']);
  text(visual.title, 5, 28, '도식 제목'); text(visual.note, 10, 60, '도식 설명'); text(visual.caption, 16, 150, '도식 캡션');
  validateDiagramNodes(visual);
  const limits = diagramTextLimits(visual.kind);
  for (const node of visual.nodes) {
    node.forEach((part, i) => text(part, 1, limits[i], '도식 문구'));
  }
  return code;
}
export function validateEnvelope(payload, plan) {
  keys(payload, ['articles', 'withheld']);
  requireThat(Array.isArray(payload.articles) && Array.isArray(payload.withheld) && payload.articles.length + payload.withheld.length === plan.requested.length, '하루 글 수 불일치');
  const kinds = [...payload.articles, ...payload.withheld].map((p) => p.kind).sort();
  requireThat(JSON.stringify(kinds) === JSON.stringify([...plan.requested].sort()), '글 종류 중복·누락');
  for (const item of payload.withheld) { keys(item, ['kind', 'reason']); text(item.reason, 5, 300, '보류 이유'); }
}
async function verifySources(article, plan) {
  for (const source of article.sources) {
    const sourceText = [topics.guidePage, topics.guideUrl].includes(source.url) ? normalized(plan.guideExcerpt) : await fetchText(source.url);
    requireThat(sourceText.includes(normalized(source.quote)), '공식 문서에서 근거를 대조하지 못함');
  }
}
export const dockerOptions = ['--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
  '--pids-limit=32', '--memory=128m', '--cpus=1', '--user=65534:65534',
  '--tmpfs=/tmp:rw,noexec,nosuid,size=32m', '--workdir=/tmp', '-e', 'PYTHONIOENCODING=utf-8'];
async function dockerRun(args) {
  const name = `blog-example-${randomUUID()}`;
  try {
    return await exec('docker', ['run', '--rm', '--name', name, ...dockerOptions, ...args],
      { timeout: 15000, maxBuffer: 65536, killSignal: 'SIGKILL' });
  } finally { await exec('docker', ['rm', '-f', name], { timeout: 10000 }).catch(() => {}); }
}
async function environment() {
  const command = 'import json,platform,ssl; from pathlib import Path; print(json.dumps({"os":next(x.split("=",1)[1].strip(chr(34)) for x in Path("/etc/os-release").read_text().splitlines() if x.startswith("PRETTY_NAME="))+" / Docker (network none)","python":platform.python_version(),"pythonSsl":ssl.OPENSSL_VERSION,"openssl":"CLI 미사용; Python ssl 버전으로 기록"}))';
  return JSON.parse((await dockerRun([image, 'python3', '-I', '-B', '-c', command])).stdout);
}
async function executeArticle(article, env) {
  const code = pythonCode(article.body), directory = await mkdtemp(join(tmpdir(), 'blog-example-'));
  try {
    await chmod(directory, 0o755);
    await writeFile(join(directory, 'example.py'), code + '\n', { mode: 0o644 });
    const result = await dockerRun(['--mount', `type=bind,source=${directory},target=/example,readonly`, image, 'python3', '-I', '-B', '/example/example.py']);
    requireThat(result.stdout.trim().length > 0 && !result.stderr.trim(), '실행 출력 또는 오류 확인 필요');
    requireThat(!/sk-(?:proj-)?[A-Za-z0-9_-]{20,}|\/home\/runner|C:\\Users\\/.test(result.stdout), '공개할 수 없는 실행 출력');
    return { recordedAt: new Date().toISOString(), environment: env, sourceCodeSha256: digest(code),
      runs: [{ label: '네트워크 없는 컨테이너에서 가상 자료 예제 실행', command: 'python3 -I -B example.py (Docker, network=none)',
        exitCode: 0, stdout: result.stdout, stderr: result.stderr }] };
  } finally {
    await rm(join(directory, 'example.py'), { force: true });
    await rmdir(directory);
  }
}
async function appendEntries(path, additions) {
  const original = (await readFile(path, 'utf8')).trimEnd(), data = JSON.parse(original);
  for (const key of Object.keys(additions)) requireThat(!Object.hasOwn(data, key), '기존 기록 덮어쓰기 금지');
  const suffix = Object.entries(additions).map(([key, value]) => `  ${JSON.stringify(key)}: ${JSON.stringify(value)}`).join(',\n');
  await writeFile(path, original.slice(0, -1).trimEnd() + (Object.keys(data).length ? ',\n' : '\n') + suffix + '\n}\n');
}
export function renderPost(article, plan, date) {
  const lines = ['---', `title: ${JSON.stringify(article.title)}`, `description: ${JSON.stringify(article.description)}`,
    `date: ${JSON.stringify(date)}`, `sourcesChecked: ${JSON.stringify(plan.day)}`, `category: ${JSON.stringify(article.kind)}`, `tags: ${JSON.stringify(article.tags)}`, 'draft: false', 'example: false'];
  if (article.kind === 'unix') lines.push('series: "unix-2026"', `seriesOrder: ${plan.next.order}`);
  return lines.join('\n') + '\n---\n\n' + article.body.trim() + '\n\n## 참고 자료\n\n' +
    article.sources.map((source) => `- [${source.title}](${allowedUrl(source.url).href.replace(/\(/g, '%28').replace(/\)/g, '%29')})`).join('\n') + '\n';
}
async function materialize(bundle) {
  const { plan, articles, evidence } = bundle;
  requireThat(plan.day === seoulDay() && articles.length >= 1 && articles.length <= 3, '날짜 또는 글 수 재확인 필요');
  const current = await readPosts(), visual = {}, contexts = {};
  const executions = await json(join(root, 'src/data/executions.json'));
  for (const article of articles) {
    validateArticle(article, plan, current);
    const record = evidence[article.slug];
    requireThat(record?.sourceCodeSha256 === digest(pythonCode(article.body)) && record.runs?.length === 1 &&
      record.runs[0].exitCode === 0 && record.runs[0].stdout && Number.isFinite(Date.parse(record.recordedAt)), '실행 근거 불일치');
    requireThat(record.environment?.os && record.environment.python && record.environment.pythonSsl && record.environment.openssl, '실행 환경 누락');
    requireThat(!Object.hasOwn(executions.posts, article.slug), '기존 실행 기록 덮어쓰기 금지');
    await writeFile(join(root, 'src/content/posts', `${article.slug}.md`), renderPost(article, plan, seoulStamp()), { flag: 'wx' });
    visual[article.slug] = article.visual; contexts[article.slug] = { scope: article.scope, finding: article.finding };
    executions.posts[article.slug] = record;
  }
  await appendEntries(join(root, 'src/data/article-visuals.json'), visual);
  await appendEntries(join(root, 'src/data/execution-context.json'), contexts);
  await saveJson(join(root, 'src/data/executions.json'), executions);
  await exec(process.execPath, ['scripts/build-article-diagrams.mjs'], { cwd: root });
  return articles.flatMap((a) => [`src/content/posts/${a.slug}.md`, `public/assets/posts/${a.slug}.svg`])
    .concat(['src/data/article-visuals.json', 'src/data/execution-context.json', 'src/data/executions.json']);
}
async function output(name, value) {
  if (process.env.GITHUB_OUTPUT) await writeFile(process.env.GITHUB_OUTPUT, `${name}=${value}\n`, { flag: 'a' });
}
async function prepare(mode) {
  const plan = makePlan(await readPosts(), mode);
  plan.baseSha = await git('rev-parse', 'HEAD');
  if (plan.requested.includes('unix') || (mode === 'verify' && plan.next)) {
    try {
      // 공식 URL은 curl 요청에 HTTP 400을 반환해 Node 기본 HTTP 클라이언트를 쓴다.
      // TLS 검증은 유지하고 리디렉션·크기·파일 형식·해시를 모두 확인한다.
      const response = await fetch(topics.guideUrl, { redirect: 'error', signal: AbortSignal.timeout(45000) });
      requireThat(response.ok, '공식 PDF HTTP 응답 확인 실패');
      const chunks = []; let size = 0;
      for await (const chunk of response.body) { size += chunk.length; requireThat(size <= 16 * 1024 * 1024, '공식 PDF 크기 초과'); chunks.push(chunk); }
      const pdf = Buffer.concat(chunks);
      requireThat(pdf.subarray(0, 5).toString() === '%PDF-' && digest(pdf) === topics.guideSha256, '공식 가이드 파일 변경 확인 필요');
      await writeFile(join(qa, 'guide.pdf'), pdf);
      const last = topics.topics[plan.next.order]?.page - 1 || 173;
      await exec('pdftotext', ['-f', String(plan.next.page), '-l', String(last), '-layout', join(qa, 'guide.pdf'), join(qa, 'guide-excerpt.txt')]);
      plan.guideExcerpt = (await readFile(join(qa, 'guide-excerpt.txt'), 'utf8')).slice(0, 32000);
      requireThat(plan.guideExcerpt.includes(`U-${String(plan.next.order).padStart(2, '0')}`), '원문 항목 추출 실패');
    } catch (error) {
      console.error(error.cause?.code ?? error.message);
      if (mode === 'verify') throw new Error('클라우드에서 2026 KISA PDF 다운로드·해시·항목 대조 실패');
      plan.requested = plan.requested.filter((kind) => kind !== 'unix');
      plan.withheld.push({ kind: 'unix', reason: '2026 공식 PDF 다운로드·해시·항목 대조 실패' });
    }
  }
  await saveJson(join(qa, 'daily-plan.json'), plan);
  const prompt = await readFile(join(root, '.github/prompts/daily-posts.md'), 'utf8');
  await writeFile(join(qa, 'daily-prompt.md'), prompt + '\n\n## 이번 실행 계획\n\n' + JSON.stringify(plan, null, 2));
  await output('requested', plan.requested.length > 0 ? 'true' : 'false'); await output('base_sha', plan.baseSha);
  console.log(`일일 계획: ${plan.day}, 작성 ${plan.requested.join(', ') || '없음'}, 보류 ${plan.withheld.length}개`);
}
async function validate() {
  const plan = await json(join(qa, 'daily-plan.json')), payload = await json(join(qa, 'daily-generation.json'), 200000);
  requireThat(plan.baseSha === await git('rev-parse', 'HEAD') && plan.day === seoulDay(), '실행 계획의 기준 커밋·날짜 불일치');
  validateEnvelope(payload, plan);
  const posts = await readPosts(), accepted = [], evidence = {}, withheld = [...plan.withheld, ...payload.withheld];
  const env = payload.articles.length ? await environment() : null;
  for (const article of payload.articles) {
    try {
      validateArticle(article, plan, posts); await verifySources(article, plan);
      evidence[article.slug] = await executeArticle(article, env); accepted.push(article);
    } catch (error) {
      withheld.push({ kind: article.kind, reason: '본문·공식 근거·격리 실행 검증 실패' });
      const reason = error.cmd ? '격리 예제 실행 실패. 원문 코드와 종료 조건 확인 필요' : error.message;
      console.error(`${article.kind} 글 보류: ${reason}`);
    }
  }
  requireThat(accepted.length > 0, '발행 조건을 통과한 글이 없음');
  const bundle = { version: 1, plan, articles: accepted, evidence, withheld };
  await saveJson(join(qa, 'daily-bundle.json'), bundle); await materialize(bundle);
  console.log(`검증된 글 ${accepted.length}편, 보류 ${withheld.length}개`);
}
async function publish() {
  const plan = await json(join(qa, 'daily-plan.json'));
  requireThat(plan.mode === 'publish' && plan.day === seoulDay() && /^[a-f0-9]{40}$/.test(plan.baseSha), '발행 계획 오류');
  requireThat(await git('rev-parse', 'HEAD') === plan.baseSha && (await git('ls-remote', 'origin', 'refs/heads/main')).split(/\s+/)[0] === plan.baseSha, '원격 main이 변경됨. 새 실행에서 다시 검증 필요');
  requireThat(!(await git('status', '--porcelain')), '발행 작업 폴더가 깨끗하지 않음');
  if (!plan.requested.length) { await output('sha', plan.baseSha); return; }
  const bundle = await json(join(qa, 'daily-bundle.json'), 500000);
  requireThat(JSON.stringify(bundle.plan) === JSON.stringify(plan), '아티팩트 실행 계획 불일치');
  const fresh = makePlan(await readPosts(), 'publish');
  requireThat(bundle.articles.every((a) => fresh.requested.includes(a.kind)), '오늘 글 중복 발행 금지');
  const paths = await materialize(bundle);
  const changed = (await git('status', '--porcelain', '-uall')).split('\n').filter(Boolean).map((line) => line.slice(3));
  requireThat(changed.every((path) => paths.includes(path)) && changed.length === paths.length, '발행 허용 파일 범위 불일치');
  for (const path of paths) requireThat((await lstat(join(root, path))).isFile(), '일반 파일만 발행 가능');
  await git('add', '--', ...paths); await git('diff', '--cached', '--check');
  await git('config', 'user.name', 'github-actions[bot]');
  await git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com');
  await git('commit', '-m', `docs(content): ${plan.day} 보안 점검 글 ${bundle.articles.length}편 추가`, '-m',
    '공식 문서 근거와 가상 자료 Python 예제를 검증하고 도식·격리 실행 출력·코드 해시를 함께 기록한다. 자동 생성·검증이며 사실 판단의 한계는 발행 운영 문서에 남긴다.');
  await git('push', 'origin', 'HEAD:main'); await output('sha', await git('rev-parse', 'HEAD'));
}
async function verifyRuntime() {
  const code = 'import os,socket; from pathlib import Path\nassert not os.environ.get("OPENAI_API_KEY")\ntry:\n Path("/forbidden").write_text("x")\nexcept OSError:\n print("루트 파일시스템 쓰기 차단")\nelse:\n raise AssertionError("root write")\ntry:\n socket.create_connection(("1.1.1.1",443),timeout=1)\nexcept OSError:\n print("외부 네트워크 연결 차단")\nelse:\n raise AssertionError("network")\nprint("API 키 전달 없음")\n';
  console.log((await dockerRun([image, 'python3', '-I', '-B', '-c', code])).stdout.trim());
  const env = await environment();
  console.log('격리 실행 환경:', JSON.stringify(env));
  const sample = (await readPosts()).find((post) => post.slug === 'u-11-service-account-shell');
  requireThat(sample, '컨테이너 실행 검증용 공개 예제 누락');
  const result = await executeArticle({ body: sample.source }, env);
  const recorded = await json(join(root, 'src/data/executions.json'));
  requireThat(result.sourceCodeSha256 === recorded.posts[sample.slug].sourceCodeSha256 &&
    result.runs[0].stdout === recorded.posts[sample.slug].runs[0].stdout, '본문 코드·컨테이너 출력 대조 실패');
  console.log('본문 예제 읽기 전용 마운트·실행·출력 수집 확인:', sample.slug);
}
async function verifyPublic() {
  const plan = await json(join(qa, 'daily-plan.json'));
  const bundle = await json(join(qa, 'daily-bundle.json')).catch(() => null);
  const base = (process.env.SITE_URL || 'https://ryuyunseong.github.io').replace(/\/$/, '') + (process.env.BASE_PATH || '/security-blog/');
  const articles = bundle?.articles ?? [];
  async function get(path) {
    for (let attempt = 0; attempt < 10; attempt++) {
      const response = await fetch(base + path, { signal: AbortSignal.timeout(15000), cache: 'no-store' });
      if (response.ok) return response;
      await new Promise((done) => setTimeout(done, 3000));
    }
    throw new Error('공개 페이지 응답 확인 실패');
  }
  const search = await get('search.json').then((r) => r.json());
  const rss = await get('rss.xml').then((r) => r.text());
  for (const article of articles) {
    const html = await get(`posts/${article.slug}/`).then((r) => r.text());
    requireThat(html.includes('article-visual') && html.includes('execution-results'), '공개 글의 도식·실행 기록 확인 실패');
    const svg = Buffer.from(await get(`assets/posts/${article.slug}.svg`).then((r) => r.arrayBuffer()));
    requireThat(digest(svg) === digest(await readFile(join(root, `public/assets/posts/${article.slug}.svg`))), '공개 도식과 검증한 도식 불일치');
    requireThat(JSON.stringify(search).includes(article.slug) && rss.includes(`/posts/${article.slug}/`), '검색·RSS 반영 확인 실패');
  }
  console.log(`공개 확인: ${plan.day}, 새 글 ${articles.length}편, 그림·실행 기록·검색·RSS`);
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    await mkdir(qa, { recursive: true });
    const [command, mode = 'publish'] = process.argv.slice(2);
    if (command === 'plan') await prepare(mode);
    else if (command === 'validate') await validate();
    else if (command === 'publish') await publish();
    else if (command === 'verify-runtime') await verifyRuntime();
    else if (command === 'verify-public') await verifyPublic();
    else throw new Error('지원하지 않는 명령');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
