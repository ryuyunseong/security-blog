import type { APIContext } from 'astro';
import { getPosts } from '../lib/posts';
import { categories, path, postPath, tagPath, unixSeries } from '../lib/site';
import { escapeXml } from '../lib/core.mjs';

export async function GET(context: APIContext) {
  const posts = await getPosts();
  const tags = [...new Set(posts.flatMap((post) => post.data.tags))];
  const urls = [path(), path('categories/'), path('tags/'), unixSeries.path,
    ...categories.map((category) => path(`categories/${category.id}/`)),
    ...tags.map(tagPath), ...posts.map((post) => postPath(post.id))];
  const xml = `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.map((url) => `<url><loc>${escapeXml(new URL(url, context.site).href)}</loc></url>`).join('')}</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
