import { getCollection } from 'astro:content';
import { isPublished } from './core.mjs';

export async function getPosts() {
  return (await getCollection('posts', ({ data }) => isPublished(data)))
    .sort((a, b) => b.data.date.getTime() - a.data.date.getTime() || a.id.localeCompare(b.id));
}
