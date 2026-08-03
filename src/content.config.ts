import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const newsItem = z.object({
  titleJa: z.string().min(1),
  titleOriginal: z.string().min(1),
  briefJa: z.string().min(1),
  url: z.url(),
  sourceId: z.string().min(1),
  sourceName: z.string().min(1),
  publishedAt: z.iso.datetime({ offset: true }),
  imageUrl: z.url().nullable().optional(),
  imageLicense: z.string().nullable().optional(),
  author: z.string().nullable().optional(),
  translationStatus: z.enum(['complete', 'partial']),
  dedupeKey: z.string().min(1),
});

const daily = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/daily' }),
  schema: z.object({
    title: z.string().min(1),
    description: z.string().min(1),
    date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    publishedAt: z.iso.datetime({ offset: true }),
    updatedAt: z.iso.datetime({ offset: true }),
    itemCount: z.number().int().positive(),
    sources: z.array(z.string()).min(1),
    noindex: z.boolean().default(false),
    items: z.array(newsItem).min(1),
  }),
});

export const collections = { daily };
