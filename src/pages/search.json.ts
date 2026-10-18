import { getPosts } from '../lib/posts';
import { categoryLabel, postPath, assessmentTargetLabel } from '../lib/site';

export async function GET() {
  const entries = (await getPosts()).map(({ id, data }) => ({
    title: data.title,
    description: data.description,
    category: categoryLabel(data.category) + (data.assessmentTarget ? ` · ${assessmentTargetLabel(data.assessmentTarget)}` : ''),
    tags: data.tags,
    url: postPath(id),
    example: data.example,
  }));
  return Response.json(entries);
}
