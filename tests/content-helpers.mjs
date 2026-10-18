import { readFile, readdir } from 'node:fs/promises';
import { isPublished } from '../src/lib/core.mjs';

export const read = async (path) => (await readFile(new URL(`../${path}`, import.meta.url), 'utf8')).replace(/\r\n/g, '\n');

export async function publishedPosts(directory = 'src/content/posts') {
  const posts = [];
  for (const file of await readdir(new URL(`../${directory}/`, import.meta.url))) {
    if (!file.endsWith('.md')) continue;
    const source = await read(`${directory}/${file}`);
    const frontmatter = source.split('\n---\n')[0];
    const field = (name) => frontmatter.match(new RegExp(`^${name}:\\s*(.*?)\\s*$`, 'm'))?.[1].replace(/^["']|["']$/g, '');
    const date = new Date(field('date'));
    if (!isPublished({ draft: field('draft') !== 'false', date })) continue;
    posts.push({ slug: file.slice(0, -3), source, date: field('date'),
      category: field('category'), assessmentTarget: field('assessmentTarget'),
      series: field('series'), seriesOrder: Number(field('seriesOrder')) || undefined });
  }
  return posts;
}
