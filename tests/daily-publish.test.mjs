import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { makePlan, seoulDay, publicationWindow, allowedUrl, validateEnvelope, validateArticle, readPosts, renderPost, dockerOptions, articlePublicationPaths } from '../scripts/daily-publish.mjs';
import { diagramNodeCounts } from '../src/lib/diagram-spec.mjs';

const posts = await readPosts();
// 일일 발행으로 저장소가 늘어나도 이 시나리오의 기준 날짜·명단은 고정한다.
const baselinePosts = posts.filter((p) => Date.parse(p.date) < Date.parse('2026-10-17T00:00:00+09:00'));
const otherPosts = posts.filter((p) => p.slug !== 'qualys-static-dynamic-tags');
const now = new Date('2026-10-17T00:00:00Z');
const plan = makePlan(baselinePosts, 'publish', now);

test('예약 발행 파일 목록에는 각 글의 원본과 모바일 도식을 함께 포함한다', () => {
  assert.deepEqual(articlePublicationPaths([{ slug: 'qualys-fixture' }]), [
    'src/content/posts/qualys-fixture.md', 'public/assets/posts/qualys-fixture.svg', 'public/assets/posts/qualys-fixture.mobile.svg',
    'src/data/article-visuals.json', 'src/data/execution-context.json', 'src/data/executions.json',
  ]);
});
const source = posts.find((p) => p.slug === 'qualys-static-dynamic-tags').source;
const body = source.slice(source.indexOf('\n---\n') + 5).split('\n## 공식 참고 자료')[0]
  .replace('assigned = {"lab-01", "lab-02"}', 'assigned = {"lab-01", "lab-02"}\n    assert len(assets) == 3');
function article() {
  return { kind: 'qualys', slug: 'qualys-guard-fixture', title: 'Qualys 태그 비교 입력 검증 사례',
    description: '분류 자료와 누락 입력을 구분하는 가상 예제의 검증용 문서입니다.', tags: ['Qualys'], body,
    scope: '코드 안의 가상 자산만 사용하며 외부 네트워크와 제품 API에 연결하지 않는다.',
    finding: '분류 목록의 차이만 확인하며 실제 제품의 태그 재평가 시점이나 스캔 완료를 입증하지 않는다.',
    visual: { title: '자산 목록의 분류 근거', kind: 'compare', nodes: [['직접 지정', '가상 자산 두 개', '담당자 기준 확인'], ['조건 비교', 'Linux와 prod', '관찰 정보 확인']],
      note: '제품 결과가 아닌 가상 자료의 비교다.', caption: '직접 지정한 목록과 조건으로 고른 목록을 비교하는 도식.' },
    sources: [
      { title: 'VM/VMDR: Manage Tags', url: 'https://docs.qualys.com/en/vm/latest/mergedProjects/analyze_reports_and_dashboards/assets/manage_tags.htm', quote: 'Static tags are created without rules.' },
      { title: 'GAV: Manage Asset Tags', url: 'https://docs.qualys.com/en/gav/latest/Tags/manage_your_tags.htm', quote: 'When you save your static tag' },
    ] };
}
test('한국 날짜 경계와 오늘 글 중복을 함께 처리한다', () => {
  assert.equal(seoulDay(new Date('2026-10-16T14:59:59Z')), '2026-10-16');
  assert.equal(seoulDay(new Date('2026-10-16T15:00:00Z')), '2026-10-17');
  assert.equal(plan.next.order, 12);
  assert.deepEqual(plan.requested, ['unix', 'qualys']);
  assert.deepEqual(makePlan(baselinePosts, 'publish', new Date('2026-10-16T14:00:00Z')).requested, []);
  const draft = { ...posts.find((p) => p.order === 11), order: 12, draft: true, date: '2026-10-15T00:00:00Z' };
  const held = makePlan([...baselinePosts, draft], 'publish', now);
  assert.deepEqual(held.requested, ['qualys']);
  assert.equal(held.withheld[0].kind, 'unix');
});
test('공식 Unix 67개 이후 번호를 만들지 않고 빠진 번호를 감지한다', () => {
  const all = Array.from({ length: 67 }, (_, i) => ({ slug: `u-${i + 1}`, title: '항목', category: 'unix',
    series: 'unix-2026', order: i + 1, draft: false, date: '2026-01-01T00:00:00Z' }));
  const complete = makePlan(all, 'publish', now);
  assert.equal(complete.next, null); assert.deepEqual(complete.requested, ['qualys', 'web']);
  assert.throws(() => makePlan(all.filter((p) => p.order !== 3), 'publish', now), /시리즈/);
  assert.throws(() => makePlan([...all, { ...all[0], order: 68 }], 'publish', now), /시리즈/);
});

test('평일 18시 이전 발행을 막고 주말과 읽기 전용 preview를 허용한다', () => {
  const before = new Date('2026-10-19T08:59:59Z'), after = new Date('2026-10-19T09:00:00Z');
  assert.equal(publicationWindow(before), false);
  assert.equal(publicationWindow(after), true);
  assert.equal(publicationWindow(new Date('2026-10-17T00:00:00Z')), true);
  assert.deepEqual(makePlan(baselinePosts, 'publish', before).requested, []);
  assert.deepEqual(makePlan(baselinePosts, 'publish', after).requested, ['unix', 'qualys']);
  assert.deepEqual(makePlan(baselinePosts, 'preview', before).requested, ['unix', 'qualys']);
});

test('추가 실습은 수·토에 하루 한 편, 초안과 수동 글을 포함해 주 두 편까지만 계획한다', () => {
  const wed = new Date('2026-10-21T10:00:00Z');
  assert.deepEqual(makePlan(baselinePosts, 'publish', wed).requested, ['unix', 'qualys', 'infrastructure']);
  const extra = (category, date) => ({ category, date, draft: true, title: '추가 실습 초안' });
  assert.deepEqual(makePlan([...baselinePosts, extra('web', '2026-10-21T18:00:00+09:00')], 'publish', wed).requested, ['unix', 'qualys']);
  const two = [...baselinePosts, extra('web', '2026-10-19T18:00:00+09:00'), extra('infrastructure', '2026-10-20T18:00:00+09:00')];
  assert.deepEqual(makePlan(two, 'publish', wed).requested, ['unix', 'qualys']);
  assert.deepEqual(makePlan(two, 'publish', new Date('2026-10-24T01:00:00Z')).requested, ['unix', 'qualys']);
});
test('출처 URL은 HTTPS 공식 호스트로 제한하며 인증·내부 주소·개행을 거부한다', () => {
  assert.equal(allowedUrl('https://docs.qualys.com/en/vm/').hostname, 'docs.qualys.com');
  for (const value of ['http://docs.qualys.com/', 'https://127.0.0.1/', 'https://docs.qualys.com.evil.example/',
    'https://user:pass@docs.qualys.com/', 'https://docs.qualys.com:444/', 'file:///etc/passwd',
    'https://docs.qualys.com/a)\n![x](x)', 'https://docs.qualys.com/"x']) assert.throws(() => allowedUrl(value));
});
test('생성 결과는 요청한 종류별 한 편 또는 명시적인 보류만 받는다', () => {
  validateEnvelope({ articles: [article()], withheld: plan.requested.filter((kind) => kind !== 'qualys').map((kind) => ({ kind, reason: '공식 근거 확인 필요' })) }, plan);
  assert.throws(() => validateEnvelope({ articles: [article(), article()], withheld: [] }, plan));
  assert.throws(() => validateEnvelope({ articles: [], withheld: [] }, plan));
  assert.throws(() => validateEnvelope({ articles: [], withheld: [], files: [] }, plan));
});
test('경로 탈출·기존 글 덮어쓰기·실행 마크업·추가 코드 블록을 차단한다', () => {
  assert.ok(validateArticle(article(), plan, otherPosts).includes('def compare'));
  assert.throws(() => validateArticle(article(), plan, posts), /본문과 중복/);
  for (const slug of ['../README', 'qualys-../../x', 'qualys-x/y', 'qualys-static-dynamic-tags']) {
    assert.throws(() => validateArticle({ ...article(), slug }, plan, posts));
  }
  for (const suffix of ['\n<img src=x onerror=alert(1)>', '\n![외부](https://example.com/a.png)', '\n```bash\necho x\n```']) {
    assert.throws(() => validateArticle({ ...article(), body: body + suffix }, plan, posts));
  }
  assert.throws(() => validateArticle({ ...article(), body: body.replace('[[diagram]]', '') }, plan, otherPosts), /배치 수/);
  assert.throws(() => validateArticle({ ...article(), body: body.replace('[[run:1]]', '[[run:9]]') }, plan, otherPosts), /실행 기록 배치/);
  assert.throws(() => validateArticle({ ...article(), body: body + '\n[x](java&#x73;cript:alert(1))' }, plan, otherPosts), /링크/);
  assert.throws(() => validateArticle({ ...article(), body: body + '\n자료 확인일: 2026-10-17.' }, plan, otherPosts), /확인일/);
  assert.throws(() => validateArticle({ ...article(), title: posts[0].title }, plan, posts));
});
test('번호·원문 출처·코드와 메타데이터의 조건을 검증한다', () => {
  assert.throws(() => validateArticle({ ...article(), kind: 'unix', slug: 'u-12-session-timeout', title: 'U-12: 임의 제목' }, plan, baselinePosts), /공식/);
  assert.throws(() => validateArticle({ ...article(), sources: [article().sources[0], article().sources[0]] }, plan, otherPosts), /중복/);
  assert.throws(() => validateArticle({ ...article(), tags: ['<script>'] }, plan, posts), /태그/);
  const rendered = renderPost(article(), plan, '2026-10-17T09:01:00+09:00');
  assert.ok(rendered.includes('category: "qualys"') && rendered.includes('sourcesChecked: "2026-10-17"'));
  assert.ok(rendered.includes('[VM/VMDR: Manage Tags]'));
  assert.ok(!rendered.includes('자료 확인일') && !rendered.includes('공식 문서 1'));
  assert.throws(() => validateArticle({ ...article(), sources: article().sources.map((source) => ({ ...source, title: '[bad](x)' })) }, plan, otherPosts), /문서 제목/);
  assert.ok(!rendered.includes(article().sources[0].quote));
});

test('예약 도식의 형식과 렌더러 계약을 맞추고 구간·글자 수 오류를 거부한다', async () => {
  const schema = JSON.parse(await readFile(new URL('../scripts/daily-output.schema.json', import.meta.url), 'utf8'));
  assert.deepEqual(schema.$defs.article.properties.visual.properties.kind.enum, Object.keys(diagramNodeCounts));
  for (const [kind, count] of Object.entries(diagramNodeCounts)) {
    const nodes = kind === 'intervals' ? [['앞', '0', '127'], ['뒤', '128', '255'], ['중첩', '64', '127'], ['병합', '0', '255']]
      : Array.from({ length: count }, () => ['항목', '조건', '해석']);
    const candidate = { ...article(), visual: { ...article().visual, kind, nodes } };
    assert.ok(validateArticle(candidate, plan, otherPosts).includes('def compare'), kind);
    assert.throws(() => validateArticle({ ...candidate, visual: { ...candidate.visual, nodes: nodes.slice(1) } }, plan, otherPosts), /노드 수/);
  }
  const candidate = article();
  candidate.visual.nodes[0][0] = '가'.repeat(11);
  assert.throws(() => validateArticle(candidate, plan, otherPosts), /도식 문구/);
  assert.throws(() => validateArticle({ ...article(), visual: { ...article().visual, kind: 'custom-svg' } }, plan, otherPosts), /도식 종류/);
});

test('추가 실습도 기존 글 중복과 경로·근거 검사를 동일하게 적용한다', () => {
  const practicalPlan = makePlan(baselinePosts, 'publish', new Date('2026-10-21T10:00:00Z'));
  const extra = { ...article(), kind: 'infrastructure', slug: 'infra-check-fixture' };
  assert.ok(validateArticle(extra, practicalPlan, otherPosts).includes('def compare'));
  assert.throws(() => validateArticle(extra, practicalPlan, posts), /본문과 중복/);
  assert.throws(() => validateArticle({ ...extra, slug: 'web-check-fixture' }, practicalPlan, otherPosts), /경로/);
  assert.throws(() => validateArticle({ ...extra, kind: 'cve' }, practicalPlan, otherPosts), /종류/);
});
test('컨테이너는 네트워크·권한·쓰기·자원을 제한하고 API 키를 전달하지 않는다', () => {
  for (const flag of ['--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
    '--pids-limit=32', '--memory=128m', '--cpus=1', '--user=65534:65534']) assert.ok(dockerOptions.includes(flag));
  assert.ok(!dockerOptions.some((value) => /OPENAI|GITHUB|privileged|docker.sock/.test(value)));
});
test('공식 항목 목록은 원문 해시와 67개 연속 번호를 보관한다', async () => {
  const data = JSON.parse(await readFile(new URL('../scripts/unix-2026-topics.json', import.meta.url), 'utf8'));
  assert.deepEqual(data.topics.map((p) => p.order), Array.from({ length: 67 }, (_, i) => i + 1));
  assert.match(data.guideSha256, /^[a-f0-9]{64}$/);
  assert.equal(data.topics[11].title, '세션 종료 시간 설정');
  assert.equal(data.topics[66].title, '로그 디렉터리 소유자 및 권한 설정');
});
