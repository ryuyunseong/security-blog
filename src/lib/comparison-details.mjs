import { escapeXml as esc } from './core.mjs';

const label = (x, y, value, size, key = false, anchor = 'start') =>
  `<text x="${x}" y="${y}" font-size="${size}" fill="${key ? '#193e2f' : '#536b60'}" font-weight="${key ? 700 : 400}" text-anchor="${anchor}"${key ? ' data-role="key"' : ''}>${esc(value)}</text>`;
const folder = (x, y, emphasis = false) => `<path d="M${x} ${y + 6}v24h36V${y + 6}H${x + 17}l-5-6H${x}v6Z" fill="${emphasis ? '#f8e9b8' : '#e6f0e9'}" stroke="#536b60" stroke-width="2"/>`;
const file = (x, y, emphasis = false) => `<path d="M${x} ${y}h23l9 9v29H${x}Z M${x + 23} ${y}v9h9" fill="${emphasis ? '#f8e9b8' : '#fff'}" stroke="#536b60" stroke-width="2"/>`;

// 폴더와 파일의 연결을 그리며 입력 문구는 XML로 이스케이프한다.
export function renderPathTree(value, { x, y, size = 20 }) {
  const [directory, filename] = value.split('/');
  return { height: 104, svg: `<g data-illustration="path-tree">` +
    folder(x, y, directory.startsWith('.')) + label(x + 48, y + 25, `${directory}/`, size, true) +
    `<path d="M${x + 18} ${y + 37}v38h28" fill="none" stroke="#7eaa93" stroke-width="2"/>` +
    file(x + 48, y + 55, filename.startsWith('.')) + label(x + 92, y + 82, filename, size, true) + '</g>' };
}

export function renderPathOrder(value, { x, y, width, size = 20 }) {
  const entries = value.split(' → '), cell = (width - 38) / 2;
  let svg = '<g data-illustration="path-order">';
  entries.forEach((entry, index) => {
    const left = x + index * (cell + 38);
    svg += `<rect x="${left}" y="${y}" width="${cell}" height="90" rx="9" fill="${index ? '#fff' : '#e6f0e9'}" stroke="#7eaa93"/>`;
    svg += folder(left + cell / 2 - 18, y + 12) + label(left + cell / 2, y + 75, entry, size, true, 'middle');
    if (!index) svg += label(left + cell + 19, y + 56, '→', 24, false, 'middle');
  });
  return { height: 102, svg: svg + '</g>' };
}

export function renderPermissionBits(mode, { x, y, width, size = 20 }) {
  const group = width / 3, bitWidth = (group - 16) / 3, bits = Number.parseInt(mode, 8);
  let svg = `<g data-illustration="permission-bits" data-mode="${esc(mode)}">`;
  ['소유자', '그룹', '기타'].forEach((name, index) => {
    svg += label(x + group * (index + 0.5), y + size, name, size, false, 'middle');
    ['r', 'w', 'x'].forEach((permission, offset) => {
      const set = Boolean(bits & (1 << (8 - index * 3 - offset)));
      const left = x + index * group + 4 + offset * (bitWidth + 4);
      svg += `<rect x="${left}" y="${y + size + 10}" width="${bitWidth}" height="30" rx="4" fill="${set ? '#d5e8dc' : '#f1f6f2'}" stroke="#cadbd1"/>` +
        label(left + bitWidth / 2, y + size + 32, set ? permission : '-', 22, true, 'middle');
    });
  });
  return { height: size + 48, svg: svg + '</g>' };
}
