import { getPosts } from '../lib/posts';
import { categoryLabel, postPath } from '../lib/site';

export async function GET() {
  const entries = (await getPosts()).map(({ id, data }) => ({
    title: data.title,
    description: data.description,
    category: categoryLabel(data.category),
    tags: data.tags,
    url: postPath(id),
    example: data.example,
  }));
  return Response.json(entries);
}
