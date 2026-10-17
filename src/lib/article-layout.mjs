/** @typedef {{type:'markdown',text:string}|{type:'diagram'}|{type:'photo'}|{type:'run',index:number,fold:boolean}} ArticleBlock */

/** Split only standalone editorial markers outside fenced code. @param {string} body @returns {ArticleBlock[]} */
export function parseArticleLayout(body) {
  const blocks = [], pending = [];
  let fence = null;
  const flush = () => {
    const text = pending.join('\n').trim();
    if (text) blocks.push({ type: 'markdown', text });
    pending.length = 0;
  };
  for (const line of body.replace(/\r\n/g, '\n').split('\n')) {
    const boundary = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (fence) {
      pending.push(line);
      if (boundary && boundary[1][0] === fence.char && boundary[1].length >= fence.length && !boundary[2].trim()) fence = null;
      continue;
    }
    if (boundary) { fence = { char: boundary[1][0], length: boundary[1].length }; pending.push(line); continue; }
    const marker = line.match(/^\[\[(diagram|photo|run:([1-9]\d*)(:fold)?)\]\]$/);
    if (!marker) {
      if (/^\[\[(?:diagram|photo|run:)/.test(line)) throw new Error('본문 자료 배치 표식 형식 오류');
      pending.push(line); continue;
    }
    flush();
    blocks.push(marker[2] ? { type: 'run', index: Number(marker[2]), fold: Boolean(marker[3]) } : { type: marker[1] });
  }
  flush();
  return blocks;
}

/** @param {string} body @param {{runCount:number,hasPhoto?:boolean}} options */
export function validateArticleLayout(body, { runCount, hasPhoto = false }) {
  const blocks = parseArticleLayout(body);
  const count = (type) => blocks.filter((block) => block.type === type).length;
  if (count('diagram') !== 1 || count('photo') !== Number(hasPhoto)) throw new Error('설명 그림·사진의 배치 수 불일치');
  const runs = blocks.filter((block) => block.type === 'run').map((block) => block.index);
  if (JSON.stringify(runs) !== JSON.stringify(Array.from({ length: runCount }, (_, i) => i + 1))) throw new Error('실행 기록 배치의 누락·중복·순서 오류');
  for (let i = 0; i < blocks.length; i++) {
    if (blocks[i].type === 'markdown') continue;
    if (blocks[i - 1]?.type !== 'markdown' || blocks[i + 1]?.type !== 'markdown') {
      throw new Error('자료는 본문 설명 사이에 배치해야 함');
    }
    if (blocks[i].type === 'run' && !blocks.slice(0, i).some((block) => block.type === 'markdown' && /^ {0,3}(`{3,}|~{3,})/m.test(block.text))) throw new Error('실행 기록은 관련 코드 뒤에 배치해야 함');
  }
  return blocks;
}
