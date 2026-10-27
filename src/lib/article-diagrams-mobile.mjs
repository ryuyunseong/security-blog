import { escapeXml as esc } from './core.mjs';
import { validateDiagramNodes } from './diagram-spec.mjs';

const width = 360;
const ink = '#193e2f';
const muted = '#536b60';
const measure = (value) => [...value].reduce((sum, char) => sum + (/\s/u.test(char) ? 0.35 : /[MW@]/.test(char) ? 0.9 : char.codePointAt(0) > 255 ? 1 : 0.65), 0);

// 단어를 먼저 보존하고, 한 줄보다 긴 식별자만 글자 단위로 나눈다.
export function wrapDiagramText(value, units) {
  const lines = [];
  let line = '';
  for (const word of value.trim().split(/\s+/u)) {
    if (line && measure(`${line} ${word}`) <= units) { line += ` ${word}`; continue; }
    if (line) { lines.push(line); line = ''; }
    for (const char of word) {
      if (line && measure(line + char) > units) { lines.push(line); line = ''; }
      line += char;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function block(x, y, value, maxWidth, size = 20, key = false) {
  const lines = wrapDiagramText(value, maxWidth / size);
  const lineHeight = Math.ceil(size * 1.4);
  return {
    height: lines.length * lineHeight,
    svg: `<text x="${x}" y="${y + size}" font-size="${size}" fill="${key ? ink : muted}" font-weight="${key ? 700 : 400}"${key ? ' data-role="key"' : ''}>` +
      lines.map((line, index) => `<tspan x="${x}" dy="${index ? lineHeight : 0}">${esc(line)}</tspan>`).join('') + '</text>',
  };
}
const line = (d, arrow = false) => `<path d="${d}" fill="none" stroke="#7eaa93" stroke-width="2"${arrow ? ' marker-end="url(#arrow)"' : ''}/>`;

function card(x, y, w, node, fill = '#fff') {
  let content = '', offset = 16;
  node.forEach((part, index) => {
    const label = block(x + 16, y + offset, part, w - 32, index ? 20 : 22, index === 0);
    content += label.svg;
    offset += label.height + (index < 2 ? 6 : 0);
  });
  const height = offset + 16;
  return { height, svg: `<rect x="${x}" y="${y}" width="${w}" height="${height}" rx="12" fill="${fill}" stroke="#cadbd1"/>` + content };
}

export function renderMobileArticleDiagram(item) {
  validateDiagramNodes(item);
  let y = 16, diagram = '';
  if (item.kind === 'decision') {
    const question = card(16, y, 328, item.nodes[0], '#e6f0e9');
    diagram += question.svg;
    const questionBottom = y + question.height;
    y = questionBottom + 54;
    const branches = [];
    for (let index = 1; index < 3; index++) {
      const branch = card(60, y, 284, item.nodes[index]);
      diagram += block(60, y - 34, index === 1 ? '예' : '아니요', 260, 22, true).svg + branch.svg;
      branches.push(y + 28);
      y += branch.height + 54;
    }
    diagram += line(`M180 ${questionBottom}v18H26V${branches[1]}`);
    diagram += branches.map((cy) => line(`M26 ${cy}H54`, true)).join('');
    y -= 30;
  } else if (item.kind === 'timeline') {
    const start = y + 12, points = [];
    item.nodes.forEach((node) => {
      points.push(y + 12);
      const label = card(52, y, 292, node);
      diagram += label.svg;
      y += label.height + 28;
    });
    diagram += line(`M26 ${start}V${points[2] + 10}`, true);
    diagram += points.map((cy) => `<circle cx="26" cy="${cy}" r="6" fill="#287056"/>`).join('');
  } else if (item.kind === 'merge' || item.kind === 'topology') {
    const starts = [];
    item.nodes.slice(0, 2).forEach((node) => {
      const input = card(52, y, 292, node);
      starts.push(y + input.height / 2);
      diagram += input.svg;
      y += input.height + 24;
    });
    if (item.kind === 'topology') {
      const transport = block(52, y, 'HTTPS로 플랫폼 연결', 292, 22, true);
      diagram += transport.svg; y += transport.height + 16;
    } else y += 12;
    const joinY = y - 16;
    diagram += line(`M52 ${starts[0]}H26V${joinY}H180`) + line(`M52 ${starts[1]}H26`);
    diagram += line(`M180 ${joinY}V${y - 6}`, true);
    const result = card(16, y, 328, item.nodes[2], '#e6f0e9');
    diagram += result.svg;
    y += result.height + 24;
  } else if (item.kind === 'intervals') {
    const x = (value) => 16 + Number(value) * 328 / 256;
    item.nodes.forEach(([label, start, end], index) => {
      const heading = block(16, y, label, 328, 22, true);
      diagram += heading.svg;
      y += heading.height + 8;
      diagram += `<rect x="16" y="${y}" width="328" height="24" rx="4" fill="#e0ebe4"/>`;
      diagram += `<rect x="${x(start)}" y="${y}" width="${(Number(end) - Number(start) + 1) * 328 / 256}" height="24" rx="3" fill="${index === 3 ? '#287056' : '#9abfa9'}"/>`;
      const range = block(16, y + 32, `${start} ~ ${end}`, 328, 22, true);
      diagram += range.svg;
      y += 32 + range.height + 28;
    });
    diagram += '<path d="M16 ' + y + 'H344" stroke="#cadbd1"/>';
    for (const tick of [0, 128, 255]) {
      diagram += `<text x="${x(tick)}" y="${y + 28}" font-size="20" fill="${muted}" text-anchor="${tick === 0 ? 'start' : tick === 255 ? 'end' : 'middle'}">${tick}</text>`;
    }
    y += 52;
  } else {
    const cycle = item.kind === 'cycle', x = cycle ? 42 : 16, w = cycle ? 302 : 328;
    const first = y, centers = [];
    item.nodes.forEach((node, index) => {
      const panel = card(x, y, w, node, item.kind === 'compare' && index ? '#e6f0e9' : '#fff');
      centers.push(y + panel.height / 2);
      diagram += panel.svg;
      y += panel.height;
      if (index < item.nodes.length - 1 && (item.kind === 'flow' || cycle)) {
        diagram += line(`M${x + w / 2} ${y + 5}v22`, true);
        y += 36;
      } else y += 16;
    });
    if (cycle) diagram += line(`M42 ${centers[2]}H20V${first + 28}H36`, true);
    y += 8;
  }
  const height = y + 8;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="360" height="${height}" viewBox="0 0 360 ${height}" data-diagram-kind="${item.kind}" data-layout="mobile" role="img" aria-labelledby="title desc"><title id="title">${esc(item.title)}</title><desc id="desc">${esc(`${item.caption} ${item.note}`)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#7eaa93"/></marker></defs><rect width="360" height="${height}" fill="#f1f6f2"/><g font-family="'Malgun Gothic','Noto Sans KR',sans-serif">${diagram}</g></svg>`;
  return { svg, width, height };
}
