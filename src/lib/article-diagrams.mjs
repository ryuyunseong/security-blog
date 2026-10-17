import { escapeXml as esc } from './core.mjs';
import { validateDiagramNodes } from './diagram-spec.mjs';

const text = (x, y, value, size = 22, color = '#536b60', weight = 400, anchor = 'start') =>
  `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${weight}" text-anchor="${anchor}">${esc(String(value))}</text>`;
const rect = (x, y, width, height, fill = '#fff') =>
  `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="12" fill="${fill}" stroke="#cadbd1"/>`;
const path = (d, arrow = false) => `<path d="${d}" fill="none" stroke="#7eaa93" stroke-width="3"${arrow ? ' marker-end="url(#arrow)"' : ''}/>`;
const box = (x, y, width, height, node, number) => rect(x, y, width, height) +
  text(x + 22, y + 35, number, 16, '#287056', 700) + text(x + 22, y + 77, node[0], 25, '#193e2f', 700) +
  text(x + 22, y + 119, node[1], 19) + text(x + 22, y + 150, node[2], 19);
const compactBox = (x, y, width, height, node, size = 18) => rect(x, y, width, height) +
  text(x + 22, y + 34, node[0], 22, '#193e2f', 700) +
  text(x + 22, y + 67, node[1], size) + text(x + 22, y + 96, node[2], size);

export function renderArticleDiagram(item) {
  validateDiagramNodes(item);
  let diagram = '';
  if (item.kind === 'compare') {
    item.nodes.forEach((node, index) => { diagram += box(44 + index * 456, 164, 416, 210, node, `0${index + 1}`); });
  } else if (item.kind === 'layers') {
    item.nodes.forEach((node, index) => {
      const y = 145 + index * 88;
      diagram += rect(44, y, 872, 76, index % 2 ? '#e6f0e9' : '#fff');
      diagram += text(65, y + 45, `0${index + 1}`, 18, '#287056', 700) + text(110, y + 45, node[0], 24, '#193e2f', 700);
      diagram += text(380, y + 31, node[1], 21) + text(380, y + 58, node[2], 19);
    });
  } else if (item.kind === 'merge') {
    item.nodes.slice(0, 2).forEach((node, index) => { diagram += box(44, 141 + index * 165, 390, 154, [node[0], node[1], ''], `0${index + 1}`); });
    diagram += path('M434 218H480V300H524 M434 382H480V300');
    diagram += box(524, 202, 392, 205, item.nodes[2], '03');
    diagram += text(66, 278, item.nodes[0][2], 18) + text(66, 443, item.nodes[1][2], 18);
  } else if (item.kind === 'matrix') {
    diagram += rect(44, 144, 872, 292);
    diagram += '<path d="M44 190H916 M44 272H916 M44 354H916 M272 144V436 M576 144V436" stroke="#cadbd1"/>';
    diagram += text(66, 175, '항목', 18, '#287056', 700) + text(294, 175, '동작·조건', 18, '#287056', 700) + text(598, 175, '의미·확인 대상', 18, '#287056', 700);
    item.nodes.forEach((node, index) => {
      const y = 240 + index * 82;
      diagram += text(66, y, node[0], 22, '#193e2f', 700) + text(294, y, node[1], 18) + text(598, y, node[2], 18);
    });
  } else if (item.kind === 'timeline') {
    diagram += path('M110 232H850', true);
    item.nodes.forEach((node, index) => {
      const x = 130 + index * 350;
      diagram += `<circle cx="${x}" cy="232" r="10" fill="#287056" stroke="#f1f6f2" stroke-width="4"/>`;
      diagram += text(x, 195, node[0], 24, '#193e2f', 700, 'middle');
      diagram += text(x, 295, node[1], 19, '#536b60', 400, 'middle') + text(x, 332, node[2], 18, '#536b60', 400, 'middle');
    });
    diagram += text(480, 418, '왼쪽에서 오른쪽으로 진행', 17, '#287056', 400, 'middle');
  } else if (item.kind === 'decision') {
    diagram += '<path d="M480 140L650 220L480 300L310 220Z" fill="#e6f0e9" stroke="#7eaa93" stroke-width="2"/>';
    diagram += text(480, 214, item.nodes[0][0], 22, '#193e2f', 700, 'middle') + text(480, 244, item.nodes[0][1], 17, '#536b60', 400, 'middle');
    diagram += text(480, 132, item.nodes[0][2], 16, '#536b60', 400, 'middle');
    diagram += path('M310 220H240V329', true) + path('M650 220H720V329', true);
    diagram += text(254, 295, '예', 19, '#287056', 700) + text(734, 295, '아니요', 19, '#287056', 700);
    diagram += compactBox(44, 338, 392, 116, item.nodes[1]) + compactBox(524, 338, 392, 116, item.nodes[2]);
  } else if (item.kind === 'cycle') {
    diagram += path('M600 214Q744 218 744 298', true) + path('M620 377H347', true) + path('M215 308Q211 211 350 211', true);
    diagram += compactBox(360, 143, 240, 120, item.nodes[0], 16);
    diagram += compactBox(620, 308, 250, 120, item.nodes[1], 16);
    diagram += compactBox(90, 308, 250, 120, item.nodes[2], 16);
  } else if (item.kind === 'topology') {
    diagram += path('M344 210H475V280H580', true) + path('M344 380H475V320H580', true);
    diagram += text(407, 180, 'HTTPS', 17, '#287056', 700) + text(407, 421, 'HTTPS', 17, '#287056', 700);
    diagram += compactBox(44, 150, 300, 120, item.nodes[0]) + compactBox(44, 320, 300, 120, item.nodes[1]);
    diagram += compactBox(590, 242, 326, 120, item.nodes[2]);
  } else if (item.kind === 'intervals') {
    const x = (value) => 300 + Number(value) * 600 / 256;
    for (const tick of [0, 64, 128, 192, 255]) {
      diagram += `<path d="M${x(tick)} 145V437" stroke="#dbe6df"/>` + text(x(tick), 462, tick, 16, '#536b60', 400, 'middle');
    }
    item.nodes.forEach(([label, start, end], index) => {
      const y = 166 + index * 67;
      diagram += text(44, y + 22, label, 18, '#193e2f', 700);
      diagram += `<rect x="${x(start)}" y="${y}" width="${(Number(end) - Number(start) + 1) * 600 / 256}" height="26" rx="4" fill="${index === 3 ? '#287056' : '#9abfa9'}"/>`;
      diagram += text(Number(start) > 192 ? 900 : x(start), y + 47, `${start} ~ ${end}`, 16, '#536b60', 400, Number(start) > 192 ? 'end' : 'start');
    });
  } else if (item.kind === 'flow') {
    item.nodes.forEach((node, index) => {
      const x = 44 + index * 301;
      diagram += box(x, 170, 270, 218, node, `0${index + 1}`);
      if (index < 2) diagram += `<path d="M${x + 280} 279h12m-5-5 5 5-5 5" stroke="#7eaa93" stroke-width="2" fill="none"/>`;
    });
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" data-diagram-kind="${item.kind}" role="img" aria-labelledby="title desc"><title id="title">${esc(item.title)}</title><desc id="desc">${esc(item.caption)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#7eaa93"/></marker></defs><rect width="960" height="540" fill="#f1f6f2"/><g font-family="'Malgun Gothic','Noto Sans KR',sans-serif">${text(44, 49, '보안 노트', 16, '#287056', 700)}${text(44, 102, item.title, 31, '#193e2f', 700)}${diagram}<path d="M44 480H916" stroke="#cadbd1"/>${text(44, 516, item.note, 19)}</g></svg>`;
}
