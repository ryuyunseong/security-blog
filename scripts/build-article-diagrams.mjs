import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { renderArticleDiagram } from '../src/lib/article-diagrams.mjs';
import { renderMobileArticleDiagram } from '../src/lib/article-diagrams-mobile.mjs';

const visuals = JSON.parse(await readFile(new URL('../src/data/article-visuals.json', import.meta.url), 'utf8'));
const destination = new URL('../public/assets/posts/', import.meta.url);
await mkdir(destination, { recursive: true });
for (const [id, item] of Object.entries(visuals)) {
  await writeFile(new URL(`${id}.svg`, destination), renderArticleDiagram(item) + '\n');
  await writeFile(new URL(`${id}.mobile.svg`, destination), renderMobileArticleDiagram(item).svg + '\n');
}
console.log(`${Object.keys(visuals).length}개 글의 원본·모바일 도식 생성`);
