import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: z.object({
    title: z.string().min(1).max(100),
    description: z.string().min(1).max(200),
    date: z.coerce.date(),
    updated: z.coerce.date().optional(),
    sourcesChecked: z.coerce.date().optional(),
    category: z.enum(['unix', 'web', 'infrastructure', 'cve', 'qualys']),
    tags: z.array(z.string().trim().min(1).max(30).regex(/^[\p{L}\p{N}_ -]+$/u)).min(1).max(8),
    draft: z.boolean().default(true),
    example: z.boolean().default(false),
    series: z.literal('unix-2026').optional(),
    seriesOrder: z.number().int().min(1).max(67).optional(),
  }).refine((data) => Boolean(data.series) === Boolean(data.seriesOrder), {
    message: '시리즈와 시리즈 순서를 함께 지정하세요.',
  }),
});

export const collections = { posts };
