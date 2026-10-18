import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getPosts } from '../lib/posts';
import { categoryLabel, postPath, siteInfo, assessmentTargetLabel } from '../lib/site';

export async function GET(context: APIContext) {
  return rss({
    title: siteInfo.title,
    description: siteInfo.description,
    site: context.site!,
    customData: '<language>ko-kr</language>',
    items: (await getPosts()).map(({ id, data }) => ({
      title: `${data.example ? '[예제] ' : ''}${data.title}`,
      pubDate: data.date,
      description: data.description,
      link: postPath(id),
      categories: [...new Set([categoryLabel(data.category), ...(data.assessmentTarget ? [assessmentTargetLabel(data.assessmentTarget)] : []), ...data.tags])],
    })),
  });
}
