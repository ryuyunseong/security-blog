const measure = (value) => [...value].reduce((sum, char) => sum + (/\s/u.test(char) ? 0.35 : /[MW@]/.test(char) ? 0.9 : char.codePointAt(0) > 255 ? 1 : 0.65), 0);

export function wrapDiagramText(value, units) {
  const lines = [];
  let line = '';
  for (const word of value.trim().split(/\s+/u)) {
    if (line && measure(`${line} ${word}`) <= units) { line += ` ${word}`; continue; }
    if (line) { lines.push(line); line = ''; }
    const parts = word.includes('/') ? word.match(/[^/]*\/|[^/]+$/g) ?? [word]
      : /^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z][a-zA-Z0-9-]*$/.test(word) ? word.match(/[^.]*\.|[^.]+$/g) ?? [word] : [word];
    for (const part of parts) {
      if (measure(part) <= units) {
        if (line && measure(line + part) > units) { lines.push(line); line = ''; }
        line += part;
      } else for (const char of part) {
        if (line && measure(line + char) > units) { lines.push(line); line = ''; }
        line += char;
      }
    }
  }
  if (line) lines.push(line);
  return lines;
}
