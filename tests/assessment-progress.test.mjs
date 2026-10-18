import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { assessmentCatalog as catalog, assessmentSeries, classificationError, populatedAssessmentTargets } from '../src/lib/taxonomy.mjs';
import { nextAssessment, makePlan, renderPost, validateArticle } from '../scripts/daily-publish.mjs';

const now = new Date('2026-10-18T10:00:00Z');
const completed = (target) => target.topics.map((topic) => ({
  slug: `${topic.code.toLowerCase()}-fixture`, category: 'critical-infrastructure', assessmentTarget: target.id,
  series: target.series, order: topic.order, draft: false, date: '2026-01-01T00:00:00+09:00',
}));

test('공식 목차의 12개 대상과 382개 항목을 연속 순서·개별 코드·페이지 범위로 보관한다', async () => {
  assert.deepEqual(catalog.targets.map((t) => [t.id, t.topics.length]), [
    ['unix', 67], ['windows', 64], ['web-service', 26], ['security-device', 23],
    ['network-device', 38], ['control-system', 51], ['pc', 18], ['dbms', 26],
    ['mobile', 4], ['web-application', 21], ['virtualization', 25], ['cloud', 19],
  ]);
  const codes = new Set();
  for (const [index, target] of catalog.targets.entries()) {
    assert.equal(target.chapter, index + 1);
    const definition = assessmentSeries[index];
    assert.equal(definition.id, target.series);
    assert.equal(definition.route, `critical-infrastructure-${target.id}-2026`);
    for (const [i, topic] of target.topics.entries()) {
      assert.equal(topic.order, i + 1);
      assert.match(topic.code, /^[A-Z]{1,3}(?:-\d{2})?$/);
      assert.ok(!codes.has(topic.code)); codes.add(topic.code);
      assert.ok(['상', '중', '하'].includes(topic.importance));
      assert.ok(topic.title.length > 0 && `${topic.code}: ${topic.title}`.length <= 160);
      assert.ok(topic.page <= topic.endPage && topic.endPage <= 873);
      if (i) assert.equal(target.topics[i - 1].endPage + 1, topic.page);
      assert.equal(classificationError({ category: 'critical-infrastructure', assessmentTarget: target.id,
        series: target.series, seriesOrder: topic.order }), null);
    }
  }
  assert.equal(codes.size, 382);
  assert.match(catalog.guideSha256, /^[a-f0-9]{64}$/);
  const old = JSON.parse(await readFile(new URL('../scripts/unix-2026-topics.json', import.meta.url), 'utf8'));
  assert.equal(catalog.guideSha256, old.guideSha256);
  assert.deepEqual(catalog.targets[0].topics.map(({ order, title, importance, page }) => ({ order, title, importance, page })), old.topics);
});

test('각 대상의 마지막 공개 항목 뒤에 다음 대상 첫 항목을 선택하고 전체 완료 시 종료한다', () => {
  const posts = [];
  for (const target of catalog.targets) {
    const first = nextAssessment(posts, now);
    assert.equal(first.assessment.target, target.id);
    assert.equal(first.next.code, target.topics[0].code);
    posts.push(...completed(target).slice(0, -1));
    const last = nextAssessment(posts, now);
    assert.equal(last.assessment.target, target.id);
    assert.equal(last.next.code, target.topics.at(-1).code);
    posts.push(completed(target).at(-1));
  }
  const final = makePlan(posts, 'publish', now);
  assert.equal(final.assessment, null); assert.equal(final.next, null);
  assert.ok(!final.requested.includes('assessment') && final.requested.includes('qualys'));
  assert.ok(final.progress.every((item) => item.completed === item.total));
});

test('마지막 항목의 초안·미래 글은 완료로 세지 않고 다음 대상으로 건너뛰지 않는다', () => {
  const unix = completed(catalog.targets[0]);
  for (const last of [{ ...unix.at(-1), draft: true }, { ...unix.at(-1), date: '2099-01-01T00:00:00Z' }]) {
    const plan = makePlan([...unix.slice(0, -1), last], 'publish', now);
    assert.equal(plan.assessment.target, 'unix'); assert.equal(plan.next.code, 'U-67');
    assert.ok(!plan.requested.includes('assessment'));
    assert.equal(plan.withheld[0].kind, 'assessment');
  }
  const windowsDraft = { ...completed(catalog.targets[1])[0], draft: true };
  const plan = makePlan([...unix, windowsDraft], 'publish', now);
  assert.equal(plan.assessment.target, 'windows'); assert.equal(plan.next.code, 'W-01');
  assert.ok(!plan.requested.includes('assessment') && plan.requested.includes('qualys'));
});

test('대상 전환일에도 주통기는 하루 한 편이며 대상별 제목·분류·시리즈를 지정한다', () => {
  const unix = completed(catalog.targets[0]);
  const todayUnix = unix.map((post, i) => i === unix.length - 1 ? { ...post, date: '2026-10-18T18:10:00+09:00' } : post);
  assert.equal(makePlan(todayUnix, 'publish', now).assessment.target, 'windows');
  assert.ok(!makePlan(todayUnix, 'publish', now).requested.includes('assessment'));
  const windows = makePlan(unix, 'publish', now);
  assert.equal(windows.assessmentTitle, 'W-01: Administrator 계정 이름 변경 등 보안성 강화');
  const post = renderPost({ kind: 'assessment', title: windows.assessmentTitle, description: '설명', tags: ['Windows'], body: '본문', sources: [] }, windows, '2026-10-18T19:00:00+09:00');
  assert.match(post, /category: "critical-infrastructure"/);
  assert.match(post, /assessmentTarget: "windows"/); assert.match(post, /series: "windows-2026"/);
  assert.match(post, /seriesOrder: 1/);
  const first = completed(catalog.targets[1])[0];
  assert.deepEqual(populatedAssessmentTargets([...unix, first]).map((t) => t.id), ['unix', 'windows']);
  assert.ok(classificationError({ category: 'critical-infrastructure', assessmentTarget: 'windows', series: 'unix-2026', seriesOrder: 1 }));
});

test('웹 애플리케이션은 CI·SI 등 원문 코드를 쓰고 대상별 빠진 번호·중복·범위 초과를 거부한다', () => {
  const preceding = catalog.targets.slice(0, 9).flatMap(completed);
  const plan = makePlan(preceding, 'publish', now);
  assert.equal(plan.assessment.target, 'web-application'); assert.match(plan.assessmentTitle, /^CI: /);
  const sample = { kind: 'assessment', slug: 'u-01-wrong-target', title: plan.assessmentTitle,
    description: '대상별 코드 검증을 위한 설명입니다.', tags: ['보안'], body: '', visual: {}, sources: [], scope: '', finding: '' };
  assert.throws(() => validateArticle(sample, plan, []), /경로/);
  const unix = completed(catalog.targets[0]), windows = completed(catalog.targets[1]);
  for (const entries of [windows.filter((p) => p.order !== 3), [...windows, windows[0]], [...windows, { ...windows[0], order: 65 }]]) {
    assert.throws(() => nextAssessment([...unix, ...entries], now), /시리즈/);
  }
});
