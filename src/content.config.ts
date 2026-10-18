import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';
import { classificationError } from './lib/taxonomy.mjs';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: z.object({
    title: z.string().min(1).max(160),
    description: z.string().min(1).max(200),
    date: z.coerce.date(),
    updated: z.coerce.date().optional(),
    sourcesChecked: z.coerce.date().optional(),
    category: z.enum(['critical-infrastructure', 'unix', 'application-security', 'infrastructure', 'cve', 'qualys', 'coding-test']),
    assessmentTarget: z.string().regex(/^[a-z][a-z0-9-]{0,39}$/).optional(),
    tags: z.array(z.string().trim().min(1).max(30).regex(/^[\p{L}\p{N}_ -]+$/u)).min(1).max(8),
    draft: z.boolean().default(true),
    example: z.boolean().default(false),
    series: z.string().regex(/^[a-z][a-z0-9-]{0,59}$/).optional(),
    seriesOrder: z.number().int().min(1).optional(),
  }).superRefine((data, context) => {
    if (data.category !== 'critical-infrastructure' && data.title.length > 100) {
      context.addIssue({ code: 'custom', path: ['title'], message: '일반 글 제목은 100자 이내로 작성하세요.' });
    }
    const error = classificationError(data);
    if (error) context.addIssue({ code: 'custom', message: error });
  }),
});

export const collections = { posts };
