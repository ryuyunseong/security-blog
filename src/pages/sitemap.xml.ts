import type { APIContext } from 'astro';
import { getPosts } from '../lib/posts';
import { archivePath, categories, path, postPath, postsPerPage, tagPath, seriesInfo, populatedAssessmentTargets, assessmentTargetPath } from '../lib/site';
import { assessmentSeries } from '../lib/taxonomy.mjs';
import { escapeXml } from '../lib/core.mjs';

export async function GET(context: APIContext) {
  const posts = await getPosts();
  const tags = [...new Set(posts.flatMap((post) => post.data.tags))];
  const urls = [path(), path('categories/'), path('tags/'),
    ...assessmentSeries.filter((series) => posts.some((post) => post.data.series === series.id)).map((series) => seriesInfo(series.id)!.path),
    ...Array.from({ length: Math.ceil(posts.length / postsPerPage) }, (_, index) => archivePath(index + 1)),
    ...categories.map((category) => path(`categories/${category.id}/`)),
    ...populatedAssessmentTargets(posts.map((post) => post.data)).map((target) => assessmentTargetPath(target.id)),
    ...tags.map(tagPath), ...posts.map((post) => postPath(post.id))];
  const xml = `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.map((url) => `<url><loc>${escapeXml(new URL(url, context.site).href)}</loc></url>`).join('')}</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
