import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, mkdtemp, copyFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const read = (file) => readFile(new URL(`../${file}`, import.meta.url), 'utf8');
const evidence = JSON.parse(await read('src/data/executions.json'));
const examples = [
  ['u-01-root-remote-login', 'check_u01_ssh.sh', 1],
  ['u-02-password-policy', 'check_u02_policy.sh', 2],
  ['u-03-account-lockout', 'check_u03_lockout.sh', 1],
  ['u-05-root-uid', 'check_u05.sh', 1],
  ['u-06-su-restriction', 'check_u06.py', 3],
  ['u-07-unused-accounts', 'check_u07.py', 2],
  ['u-08-admin-group', 'check_u08.py', 4],
  ['u-09-unused-gid', 'check_u09.py', 5],
  ['u-10-duplicate-uid', 'check_u10.py', 2],
  ['u-11-service-account-shell', 'check_u11_demo.py', 0],
  ['u-12-session-timeout', 'check_u12_idle.sh', 0],
  ['u-13-password-hash-algorithms', 'u13_hash_format.py', 0],
  ['u-14-root-path-search', 'u14_path_lookup.py', 0],
  ['u-15-file-directory-owners', 'u15_owner_mapping.py', 0],
  ['u-16-passwd-owner-permissions', 'u16_passwd_mode.py', 0],
];

test('주통기 다운로드는 본문 전체 코드와 같고 준비 파일 링크도 존재한다', async () => {
  for (const [slug, filename, index] of examples) {
    const source = await read(`src/content/posts/${slug}.md`);
    const blocks = [...source.matchAll(/^```[^\n]*\n([\s\S]*?)\n```\s*$/gm)].map((m) => m[1]);
    assert.equal(await read(`public/downloads/${filename}`), `${blocks[index]}\n`, slug);
    assert.ok(source.includes(`../../downloads/${filename}`), slug);
    const files = evidence.posts[slug].preparationFiles;
    assert.ok(files.includes(filename), slug);
    for (const file of files) {
      assert.match(file, /^[a-z0-9_]+\.(sh|py)$/);
      assert.ok((await read(`public/downloads/${file}`)).length > 20);
    }
    if (slug.startsWith('u-01-')) assert.equal(await read('public/downloads/u01_match_lab.sh'), `${blocks[4]}\n`);
  }
});

test('새 가상 자료 실행의 날짜·환경과 준비 코드·수집기 해시를 함께 보존한다', async () => {
  for (const [slug, collector] of examples.filter(([slug]) => /^u-0[236]-/.test(slug))) {
    const record = evidence.posts[slug];
    const run = record.runs.at(-1);
    assert.ok(Number.isFinite(Date.parse(run.recordedAt)));
    assert.match(run.environment.os, /Ubuntu/);
    assert.ok(run.environment.python && run.environment.bash && run.environment.openssl);
    const fixture = record.preparationFiles.find((name) => name.endsWith('_fixture_lab.py'));
    const hash = async (name) => createHash('sha256').update(await read(`public/downloads/${name}`)).digest('hex');
    assert.equal(run.sourceCodeSha256, await hash(fixture), slug);
    assert.equal(run.collectorSourceCodeSha256, await hash(collector), slug);
    assert.ok(run.scope.length > 30 && run.finding.length > 30);
    assert.equal(run.exitCode, 0);
    assert.ok(run.stdout.endsWith('실습 파일 정리: 완료\n'));
  }
});

test('Linux에서 가상 자료를 준비해 수집 상태와 오류를 비교하고 자체 정리한다', { skip: process.platform !== 'linux' && 'Linux 파일 모드와 Bash가 필요한 실습' }, async () => {
  for (const number of ['02', '03', '05', '06']) {
    const [slug, collector] = examples.find(([slug]) => slug.startsWith(`u-${number}-`));
    const fixture = `u${number}_fixture_lab.py`;
    const directory = await mkdtemp(join(tmpdir(), 'assessment test '));
    try {
      for (const file of [collector, fixture]) await copyFile(new URL(`../public/downloads/${file}`, import.meta.url), join(directory, file));
      const result = spawnSync('python3', ['-I', '-B', fixture, `./${collector}`], { cwd: directory, encoding: 'utf8', timeout: 15000 });
      assert.equal(result.status, 0, result.stderr);
      assert.equal(result.stderr, '');
      assert.ok(result.stdout.endsWith('실습 파일 정리: 완료\n'));
      if (number !== '05' && number !== '06') assert.equal(result.stdout, evidence.posts[slug].runs.at(-1).stdout);
      if (number === '06') {
        // 파일 소유권은 실행 사용자의 값이므로 호스트마다 달라질 수 있다.
        const normalizeOwner = (text) => text.replace(/UID=\d+ GID=\d+ 모드=0750/g, 'UID=실행사용자 GID=실행그룹 모드=0750');
        assert.equal(normalizeOwner(result.stdout), normalizeOwner(evidence.posts[slug].runs.at(-1).stdout));
      }
      if (number === '05') assert.deepEqual([...result.stdout.matchAll(/수집기 종료 코드: (\d)/g)].map((m) => Number(m[1])), [0, 1, 2]);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  }
});
