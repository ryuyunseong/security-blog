import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, mkdtemp, copyFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, basename } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const read = (file) => readFile(new URL(`../${file}`, import.meta.url), 'utf8');
const evidence = JSON.parse(await read('src/data/executions.json'));
const python = process.platform === 'win32' ? 'python' : 'python3';
const files = [
  ['gzip-output-limit', 'gzip_limit.py', 0],
  ['download-path-validation', 'path_lab.py', 1],
  ['cors-authentication-authorization', 'cors_auth_lab.py', 1],
  ['tls-version-and-identity', 'tls_identity_lab.py', 0],
  ['login-failure-sliding-window', 'login-failure/solution.py', 5],
  ['login-failure-sliding-window', 'login-failure/test_solution.py', 7],
  ['login-failure-sliding-window', 'login-failure/input.txt', 1],
  ['cidr-interval-binary-search', 'cidr-lookup/solution.py', 4],
  ['cidr-interval-binary-search', 'cidr-lookup/test_solution.py', 6],
  ['cidr-interval-binary-search', 'cidr-lookup/input.txt', 1],
  ['qualys-static-dynamic-tags', 'compare_tags_demo.py', 0],
  ['qualys-detection-status-transitions', 'qualys_status_example.py', 0],
  ['qualys-tcp-udp-port-scope', 'qualys_port_scope.py', 0],
];
const blocks = (source) => [...source.matchAll(/^```[^\n]*\n([\s\S]*?)\n```\s*$/gm)].map((m) => m[1]);
const hash = (source) => createHash('sha256').update(source).digest('hex');
const execute = (directory, args, input) => {
  const result = spawnSync(python, ['-B', '-X', 'utf8', ...args], {
    cwd: directory, input, encoding: 'utf8', timeout: 30000,
  });
  assert.ifError(result.error);
  // Python의 Windows 콘솔 줄바꿈만 통일하며 저장된 실행 증거는 바꾸지 않는다.
  result.stdout = result.stdout.replace(/\r\n/g, '\n');
  result.stderr = result.stderr.replace(/\r\n/g, '\n');
  return result;
};

test('실습 준비 파일은 본문 코드·예제 입력과 같고 파일명 안내를 보존한다', async () => {
  for (const [slug, filename, index] of files) {
    const source = await read(`src/content/posts/${slug}.md`);
    assert.equal(await read(`public/downloads/${filename}`), `${blocks(source)[index]}\n`, filename);
    assert.ok(source.includes(`\`${basename(filename)}\``), filename);
    assert.ok(evidence.posts[slug].preparationFiles.includes(filename), filename);
  }
  assert.deepEqual(evidence.posts['umask-and-file-permissions'].preparationFiles, ['umask_lab.sh']);
});

test('문제별 폴더에서 예제 입력과 같은 폴더의 풀이를 가져오는 테스트가 실행된다', async () => {
  for (const slug of ['login-failure-sliding-window', 'cidr-interval-binary-search']) {
    const directory = await mkdtemp(join(tmpdir(), 'practice input '));
    try {
      for (const name of evidence.posts[slug].preparationFiles) {
        await copyFile(new URL(`../public/downloads/${name}`, import.meta.url), join(directory, basename(name)));
      }
      const input = await readFile(join(directory, 'input.txt'), 'utf8');
      const output = blocks(await read(`src/content/posts/${slug}.md`))[2] + '\n';
      const direct = execute(directory, ['solution.py'], input);
      assert.equal(direct.status, 0, direct.stderr);
      assert.equal(direct.stdout, output);
      assert.equal(direct.stderr, '');
      const tests = execute(directory, ['test_solution.py']);
      const saved = evidence.posts[slug].runs[0];
      assert.equal(tests.status, saved.exitCode, tests.stderr);
      assert.equal(tests.stdout, saved.stdout);
      assert.equal(tests.stderr, saved.stderr);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  }
});

test('가상 태그·탐지 상태·포트 집합 예제의 출력과 오류 거부 검사가 기록과 같다', async () => {
  for (const [slug, file] of files.filter(([slug]) => slug.startsWith('qualys-'))) {
    const directory = await mkdtemp(join(tmpdir(), 'practice model '));
    try {
      await copyFile(new URL(`../public/downloads/${file}`, import.meta.url), join(directory, file));
      const result = execute(directory, ['-I', file]);
      const saved = evidence.posts[slug].runs[0];
      assert.equal(result.status, saved.exitCode, result.stderr);
      assert.equal(result.stdout, saved.stdout);
      assert.equal(result.stderr, saved.stderr);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  }
});

test('gzip 파일 준비는 기존 파일을 덮어쓰지 않고 해제량 경계와 종료 코드를 구분한다', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'gzip file '));
  const preparation = 'import gzip; open("sample.gz", "xb").write(gzip.compress(b"A" * 65536, mtime=0))';
  try {
    await copyFile(new URL('../public/downloads/gzip_limit.py', import.meta.url), join(directory, 'gzip_limit.py'));
    const made = execute(directory, ['-c', preparation]);
    assert.equal(made.status, 0, made.stderr);
    const before = await readFile(join(directory, 'sample.gz'));
    const again = execute(directory, ['-c', preparation]);
    assert.notEqual(again.status, 0);
    assert.match(again.stderr, /FileExistsError/);
    assert.deepEqual(await readFile(join(directory, 'sample.gz')), before);
    const run = evidence.posts['gzip-output-limit'].runs[1];
    assert.ok(Number.isFinite(Date.parse(run.recordedAt)));
    assert.match(run.environment.os, /Ubuntu/);
    assert.equal(run.sourceCodeSha256, hash(await read('public/downloads/gzip_limit.py')));
    assert.equal(run.preparationCodeSha256, hash(preparation));
    assert.ok(run.command.includes(preparation));
    const accepted = execute(directory, ['-I', 'gzip_limit.py', './sample.gz', '--limit', '65536']);
    assert.equal(accepted.status, run.exitCode, accepted.stderr);
    assert.equal(accepted.stdout, run.stdout);
    assert.equal(accepted.stderr, run.stderr);
    const rejected = execute(directory, ['-I', 'gzip_limit.py', './sample.gz', '--limit', '65535']);
    assert.equal(rejected.status, 1);
    assert.equal(rejected.stdout, '');
    assert.equal(rejected.stderr, '정책상 거부: 압축 해제 출력 한도 초과\n');
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
