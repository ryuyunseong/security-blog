import type { APIContext } from 'astro';
import { path } from '../lib/site';

export function GET(context: APIContext) {
  return new Response(`User-agent: *\nAllow: /\nSitemap: ${new URL(path('sitemap.xml'), context.site).href}\n`, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
