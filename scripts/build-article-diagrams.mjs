import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { escapeXml as esc } from '../src/lib/core.mjs';

const visuals = JSON.parse(await readFile(new URL('../src/data/article-visuals.json', import.meta.url), 'utf8'));
const destination = new URL('../public/assets/posts/', import.meta.url);
await mkdir(destination, { recursive: true });
const text = (x, y, value, size = 22, color = '#536b60', weight = 400) =>
  `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${weight}">${esc(value)}</text>`;
const box = (x, y, width, height, node, number) =>
  `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="12" fill="#fff" stroke="#cadbd1"/>` +
  text(x + 22, y + 35, number, 16, '#287056', 700) + text(x + 22, y + 77, node[0], 25, '#193e2f', 700) +
  text(x + 22, y + 119, node[1], 19) + text(x + 22, y + 150, node[2], 19);

for (const [id, item] of Object.entries(visuals)) {
  let diagram = '';
  if (item.kind === 'compare') {
    item.nodes.forEach((node, index) => { diagram += box(44 + index * 456, 164, 416, 210, node, `0${index + 1}`); });
  } else if (item.kind === 'layers') {
    item.nodes.forEach((node, index) => {
      const y = 145 + index * 88;
      diagram += `<rect x="44" y="${y}" width="872" height="76" rx="10" fill="${index % 2 ? '#e6f0e9' : '#fff'}" stroke="#cadbd1"/>`;
      diagram += text(65, y + 45, `0${index + 1}`, 18, '#287056', 700) + text(110, y + 45, node[0], 24, '#193e2f', 700);
      diagram += text(380, y + 31, node[1], 21) + text(380, y + 58, node[2], 19);
    });
  } else if (item.kind === 'merge') {
    item.nodes.slice(0, 2).forEach((node, index) => { diagram += box(44, 141 + index * 165, 390, 154, [node[0], node[1], ''], `0${index + 1}`); });
    diagram += '<path d="M434 218H480V300H524 M434 382H480V300" fill="none" stroke="#7eaa93" stroke-width="3"/>';
    diagram += box(524, 202, 392, 205, item.nodes[2], '03');
    // 왼쪽 식별자 아래에 각 계정의 조건도 표시한다.
    diagram += text(66, 278, item.nodes[0][2], 18) + text(66, 443, item.nodes[1][2], 18);
  } else {
    item.nodes.forEach((node, index) => {
      const x = 44 + index * 301;
      diagram += box(x, 170, 270, 218, node, `0${index + 1}`);
      if (index < 2) diagram += `<path d="M${x + 280} 279h12m-5-5 5 5-5 5" stroke="#7eaa93" stroke-width="2" fill="none"/>`;
    });
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc"><title id="title">${esc(item.title)}</title><desc id="desc">${esc(item.caption)}</desc><rect width="960" height="540" fill="#f1f6f2"/><g font-family="'Malgun Gothic','Noto Sans KR',sans-serif">${text(44, 49, '보안 노트', 16, '#287056', 700)}${text(44, 102, item.title, 31, '#193e2f', 700)}${diagram}<path d="M44 480H916" stroke="#cadbd1"/>${text(44, 516, item.note, 19)}</g></svg>`;
  await writeFile(new URL(`${id}.svg`, destination), svg + '\n');
}
console.log(`${Object.keys(visuals).length}개 글 도식 생성`);
