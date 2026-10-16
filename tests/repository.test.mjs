import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';

test('현재 소스와 문서에 사용하지 않는 외부 블로그 자료가 없다', async () => {
  const forbidden = /ti\u0073tory|\uD2F0\uC2A4\uD1A0\uB9AC|(?:src\/data|docs)\/mi\u0067ration[.]/i;
  async function inspect(path) {
    const directory = new URL(`../${path}/`, import.meta.url);
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const child = `${path}/${entry.name}`;
      if (entry.isDirectory()) await inspect(child);
      else if (/\.(md|mjs|py|ts|astro|json|ya?ml|css)$/.test(entry.name)) {
        assert.ok(!forbidden.test(await readFile(new URL(`../${child}`, import.meta.url), 'utf8')), child);
      }
    }
  }
  for (const directory of ['docs', 'src', 'tests', 'scripts', 'templates', '.github']) await inspect(directory);
  assert.ok(!forbidden.test(await readFile(new URL('../README.md', import.meta.url), 'utf8')));
});
