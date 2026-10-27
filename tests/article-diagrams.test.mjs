import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { escapeXml } from '../src/lib/core.mjs';
import { renderArticleDiagram } from '../src/lib/article-diagrams.mjs';
import { renderMobileArticleDiagram } from '../src/lib/article-diagrams-mobile.mjs';

const visuals = JSON.parse(await readFile(new URL('../src/data/article-visuals.json', import.meta.url), 'utf8'));
const attribute = (source, name) => source.match(new RegExp(`(?:^|\\s)${name}="([^"]*)"`))?.[1];
const cards = (svg) => [...svg.matchAll(/<rect\b([^>]+)\/>/g)]
  .filter(([, attrs]) => attribute(attrs, 'x') !== undefined)
  .map(([, attrs]) => Object.fromEntries(['x', 'y', 'width', 'height'].map((name) => [name, Number(attribute(attrs, name))])));

test('합류도의 입력 상자에 세 문구를 보존하고 설명 줄 사이에 여유를 둔다', () => {
  for (const [slug, item] of Object.entries(visuals).filter(([, item]) => item.kind === 'merge')) {
    const svg = renderArticleDiagram(item);
    const labels = [...svg.matchAll(/<text\b([^>]+)>(.*?)<\/text>/g)].map(([, attrs, value]) => ({
      x: Number(attribute(attrs, 'x')), y: Number(attribute(attrs, 'y')),
      size: Number(attribute(attrs, 'font-size')), value,
    }));
    for (const [index, card] of cards(svg).slice(0, 2).entries()) {
      const rows = labels.filter((label) => label.x >= card.x && label.x < card.x + card.width && label.y > card.y && label.y < card.y + card.height)
        .sort((a, b) => a.y - b.y);
      assert.deepEqual(rows.slice(1).map((row) => row.value), item.nodes[index].map(escapeXml), slug);
      for (let row = 1; row < rows.length; row++) {
        assert.ok(rows[row].y - rows[row - 1].y >= Math.max(rows[row].size, rows[row - 1].size) + 4,
          `${slug}: ${rows[row - 1].value} / ${rows[row].value}`);
      }
      assert.ok(rows.at(-1).y + rows.at(-1).size / 4 <= card.y + card.height - 10, slug);
    }
  }
});

test('모바일 합류·연결 도식의 화살표는 결과 상자 위에서 아래로 한 번만 향한다', () => {
  for (const [slug, item] of Object.entries(visuals).filter(([, item]) => ['merge', 'topology'].includes(item.kind))) {
    const { svg } = renderMobileArticleDiagram(item);
    const arrows = [...svg.matchAll(/<path\b([^>]+)\/>/g)].filter(([, attrs]) => attribute(attrs, 'marker-end'));
    assert.equal(arrows.length, 1, slug);
    const d = attribute(arrows[0][1], 'd');
    assert.equal((d.match(/M/g) ?? []).length, 1, `${slug}: 화살표 경로에는 끊긴 하위 경로가 없어야 한다`);
    const points = d.match(/^M([\d.]+) ([\d.]+)V([\d.]+)$/);
    assert.ok(points, `${slug}: 결과로 향하는 수직 화살표`);
    const [x, startY, endY] = points.slice(1).map(Number);
    const result = cards(svg).at(-1);
    assert.ok(x > result.x && x < result.x + result.width, slug);
    assert.ok(endY > startY && result.y - endY >= 0 && result.y - endY <= 12, slug);
  }
});
