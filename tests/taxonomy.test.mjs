import { test } from 'node:test';
import assert from 'node:assert/strict';
import { publishedPosts } from './content-helpers.mjs';
import { categories, classificationError, populatedAssessmentTargets } from '../src/lib/taxonomy.mjs';
import { readPosts, makePlan, renderPost } from '../scripts/daily-publish.mjs';

test('주통기와 일반 Unix·코딩 테스트를 분리하고 모든 공개 글의 분류를 검증한다', async () => {
  const posts = await publishedPosts();
  const find = (slug) => posts.find((post) => post.slug === slug);
  for (const post of posts) {
    assert.equal(classificationError(post), null, post.slug);
    assert.ok(categories.some((item) => item.id === post.category), post.slug);
    if (post.series === 'unix-2026') assert.equal(post.category, 'critical-infrastructure');
  }
  assert.equal(find('umask-and-file-permissions').category, 'unix');
  for (const slug of ['cidr-interval-binary-search', 'login-failure-sliding-window']) assert.equal(find(slug).category, 'coding-test');
  for (const slug of ['gzip-output-limit', 'download-path-validation', 'cors-authentication-authorization']) assert.equal(find(slug).category, 'application-security');
  assert.equal(find('tls-version-and-identity').category, 'infrastructure');
  assert.ok(!posts.some((post) => post.category === 'unix' && post.assessmentTarget));
});

test('점검 대상·시리즈 조합을 검증하고 글이 없는 대상은 노출하지 않는다', () => {
  const valid = { category: 'critical-infrastructure', assessmentTarget: 'unix', series: 'unix-2026', seriesOrder: 12 };
  assert.equal(classificationError(valid), null);
  for (const data of [{ ...valid, category: 'unix' }, { ...valid, assessmentTarget: undefined },
    { ...valid, assessmentTarget: '../unix' }, { ...valid, series: 'unknown' }, { ...valid, seriesOrder: 68 },
    { ...valid, seriesOrder: undefined }]) assert.ok(classificationError(data));
  assert.deepEqual(populatedAssessmentTargets([]), []);
  assert.deepEqual(populatedAssessmentTargets([{ category: 'unix' }]), []);
  assert.deepEqual(populatedAssessmentTargets([valid]).map((item) => item.id), ['unix']);
});

test('생성 작업 종류를 새 카테고리로 발행하고 다른 대상·일반 글이 Unix 일일 작성을 막지 않는다', async () => {
  const posts = await readPosts();
  const now = new Date('2026-10-18T03:00:00Z');
  const plan = makePlan(posts, 'publish', now);
  assert.equal(plan.next.order, 13);
  const today = '2026-10-18T10:00:00+09:00';
  const extra = (overrides) => ({ category: 'unix', date: today, draft: false, title: '분류 검증', ...overrides });
  const others = [extra({}), extra({ category: 'critical-infrastructure', assessmentTarget: 'windows' }), extra({ category: 'coding-test' })];
  assert.ok(makePlan([...posts, ...others], 'publish', now).requested.includes('unix'));
  const publishedToday = posts.map((post) => post.order === 12 ? { ...post, date: today } : post);
  assert.ok(!makePlan(publishedToday, 'publish', now).requested.includes('unix'));
  const draft = extra({ category: 'critical-infrastructure', assessmentTarget: 'unix', series: 'unix-2026', order: 13, draft: true });
  assert.ok(!makePlan([...posts, draft], 'publish', now).requested.includes('unix'));
  const sample = { kind: 'unix', title: plan.unixTitle, description: '검증용', tags: ['Linux'], body: '본문', sources: [] };
  const rendered = renderPost(sample, plan, today);
  assert.ok(rendered.includes('category: "critical-infrastructure"') && rendered.includes('assessmentTarget: "unix"'));
  assert.ok(rendered.includes('series: "unix-2026"') && rendered.includes('seriesOrder: 13'));
  assert.ok(renderPost({ ...sample, kind: 'web' }, plan, today).includes('category: "application-security"'));
});
