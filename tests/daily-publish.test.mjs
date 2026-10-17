import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { makePlan, seoulDay, allowedUrl, validateEnvelope, validateArticle, readPosts, renderPost, dockerOptions } from '../scripts/daily-publish.mjs';

const posts = await readPosts();
// 일일 발행으로 저장소가 늘어나도 이 시나리오의 기준 날짜·명단은 고정한다.
const baselinePosts = posts.filter((p) => Date.parse(p.date) < Date.parse('2026-10-17T00:00:00+09:00'));
const otherPosts = posts.filter((p) => p.slug !== 'qualys-static-dynamic-tags');
const now = new Date('2026-10-17T00:00:00Z');
const plan = makePlan(baselinePosts, 'publish', now);
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
      { url: 'https://docs.qualys.com/en/vm/latest/mergedProjects/analyze_reports_and_dashboards/assets/manage_tags.htm', quote: 'Static tags are created without rules.' },
      { url: 'https://docs.qualys.com/en/gav/latest/Tags/manage_your_tags.htm', quote: 'When you save your static tag' },
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
  assert.equal(complete.next, null); assert.deepEqual(complete.requested, ['qualys']);
  assert.throws(() => makePlan(all.filter((p) => p.order !== 3), 'publish', now), /시리즈/);
  assert.throws(() => makePlan([...all, { ...all[0], order: 68 }], 'publish', now), /시리즈/);
});
test('출처 URL은 HTTPS 공식 호스트로 제한하며 인증·내부 주소·개행을 거부한다', () => {
  assert.equal(allowedUrl('https://docs.qualys.com/en/vm/').hostname, 'docs.qualys.com');
  for (const value of ['http://docs.qualys.com/', 'https://127.0.0.1/', 'https://docs.qualys.com.evil.example/',
    'https://user:pass@docs.qualys.com/', 'https://docs.qualys.com:444/', 'file:///etc/passwd',
    'https://docs.qualys.com/a)\n![x](x)', 'https://docs.qualys.com/"x']) assert.throws(() => allowedUrl(value));
});
test('생성 결과는 요청한 종류별 한 편 또는 명시적인 보류만 받는다', () => {
  validateEnvelope({ articles: [article()], withheld: [{ kind: 'unix', reason: '원문 근거 확인 필요' }] }, plan);
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
  assert.throws(() => validateArticle({ ...article(), body: body + '\n[x](java&#x73;cript:alert(1))' }, plan, otherPosts), /링크/);
  assert.throws(() => validateArticle({ ...article(), title: posts[0].title }, plan, posts));
});
test('번호·원문 출처·코드와 메타데이터의 조건을 검증한다', () => {
  assert.throws(() => validateArticle({ ...article(), kind: 'unix', slug: 'u-12-session-timeout', title: 'U-12: 임의 제목' }, plan, baselinePosts), /공식/);
  assert.throws(() => validateArticle({ ...article(), sources: [article().sources[0], article().sources[0]] }, plan, otherPosts), /중복/);
  assert.throws(() => validateArticle({ ...article(), tags: ['<script>'] }, plan, posts), /태그/);
  const rendered = renderPost(article(), plan, '2026-10-17T09:01:00+09:00');
  assert.ok(rendered.includes('category: "qualys"') && rendered.includes('자료 확인일: 2026-10-17'));
  assert.ok(!rendered.includes(article().sources[0].quote));
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
