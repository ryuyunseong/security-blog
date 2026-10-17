import { createSatteriMarkdownProcessor } from '@astrojs/markdown-satteri';
import { escapeXml } from './core.mjs';

export const articleMarkdownOptions = { shikiConfig: { themes: { light: 'github-dark', dark: 'github-dark' } } };
let processor;

/** @param {import('./article-layout.mjs').ArticleBlock[]} blocks @param {{depth:number,slug:string}[]} headings */
export async function renderArticleBlocks(blocks, headings) {
  processor ??= createSatteriMarkdownProcessor(articleMarkdownOptions);
  const markdown = await processor;
  const rendered = await Promise.all(blocks.map(async (block) => block.type === 'markdown'
    ? { ...block, html: (await markdown.render(block.text)).code } : block));
  let position = 0;
  for (const block of rendered) {
    if (block.type !== 'markdown') continue;
    block.html = block.html.replace(/<h([1-6])\b[^>]*>/g, (tag, depth) => {
      const heading = headings[position++];
      if (!heading || heading.depth !== Number(depth)) throw new Error('분할 본문의 목차 순서 불일치');
      const id = `id="${escapeXml(heading.slug)}"`;
      return /\bid="[^"]*"/.test(tag) ? tag.replace(/\bid="[^"]*"/, id) : tag.replace(/>$/, ` ${id}>`);
    });
    block.html = block.html.replace(/<pre\b[^>]*>[\s\S]*?<\/pre>/g, (pre) => {
      const lines = (pre.match(/\n/g) ?? []).length + 1;
      return lines > 70 ? `<details class="code-details"><summary>전체 코드 보기 · ${lines}줄</summary>${pre}</details>` : pre;
    });
  }
  if (position !== headings.length) throw new Error('분할 본문의 목차 누락');
  return rendered;
}
