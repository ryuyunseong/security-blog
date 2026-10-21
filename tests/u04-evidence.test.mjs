import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { read } from './content-helpers.mjs';

test('U-04 다운로드 수집기는 기존 본문 코드와 같고 추가 실습의 코드 해시를 대조한다', async () => {
  const source = await read('src/content/posts/u-04-password-file.md');
  const code = [...source.matchAll(/^```bash\n([\s\S]*?)\n```\s*$/gm)]
    .map((match) => match[1]).find((value) => value.startsWith('#!/usr/bin/env bash'));
  const collector = await readFile(new URL('../public/downloads/check_u04_password_file.sh', import.meta.url));
  const fixture = await readFile(new URL('../public/downloads/u04_fixture_lab.sh', import.meta.url));
  assert.equal(collector.toString('utf8'), `${code}\n`);
  const record = JSON.parse(await read('src/data/executions.json')).posts['u-04-password-file'];
  assert.equal(record.runs.length, 2);
  assert.equal(record.recordedAt, '2026-10-16T12:29:49.824195+00:00');
  assert.match(record.runs[0].stdout, /일반 레코드: 2\n쉐도우 참조 x: 2/);
  const run = record.runs[1];
  assert.equal(run.exitCode, 0);
  assert.equal(run.sourceCodeSha256, createHash('sha256').update(fixture).digest('hex'));
  assert.equal(run.collectorSourceCodeSha256, createHash('sha256').update(collector).digest('hex'));
  assert.ok(Date.parse(run.recordedAt) > Date.parse(record.recordedAt));
  assert.ok(run.environment.bash && run.scope && run.finding);
  for (const status of [0, 1, 2]) assert.ok(run.stdout.includes(`수집기 종료 코드: ${status}`));
  assert.match(run.stdout, /일반 레코드: 4/);
  assert.match(run.stdout, /실습 파일 정리: 완료/);
});
