import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createPath, isPublished, searchEntries, escapeXml } from '../src/lib/core.mjs';

test('루트 및 프로젝트 Pages 경로에 접두사를 한 번 붙인다', () => {
  assert.equal(createPath('/')('posts/test/'), '/posts/test/');
  assert.equal(createPath('/security-blog/')('/posts/test/'), '/security-blog/posts/test/');
  assert.equal(createPath('/security-blog/')(), '/security-blog/');
});

test('명시적으로 공개한 과거 글만 노출한다', () => {
  const now = new Date('2026-10-16T12:00:00Z');
  assert.equal(isPublished({ draft: false, date: '2026-10-15' }, now), true);
  assert.equal(isPublished({ draft: true, date: '2026-10-15' }, now), false);
  assert.equal(isPublished({ date: '2026-10-15' }, now), false);
  assert.equal(isPublished({ draft: false, date: '2026-10-17' }, now), false);
  assert.equal(isPublished({ draft: false, date: 'invalid' }, now), false);
});

test('한글, 대소문자, 여러 키워드와 유니코드 정규화를 처리한다', () => {
  const entries = [
    { title: '파일 권한', description: '읽기', category: 'Unix', tags: ['Linux'] },
    { title: '응답 헤더', description: '기록', category: '웹 보안', tags: ['HTTP'] },
  ];
  assert.deepEqual(searchEntries(entries, '권한 LINUX'), [entries[0]]);
  assert.deepEqual(searchEntries(entries, 'ＨＴＴＰ'), [entries[1]]);
  assert.deepEqual(searchEntries(entries, '존재하지않음'), []);
  assert.deepEqual(searchEntries(entries, '  '), entries);
});

test('사용자 검색어를 정규식으로 실행하지 않는다', () => {
  assert.deepEqual(searchEntries([{ title: '정상', description: '', category: '', tags: [] }], '[.*<script>'), []);
});

test('XML 메타데이터의 특수 문자를 이스케이프한다', () => {
  assert.equal(escapeXml('<a x="1">&\'</a>'), '&lt;a x=&quot;1&quot;&gt;&amp;&apos;&lt;/a&gt;');
});
