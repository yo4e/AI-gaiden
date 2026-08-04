import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    articleId: z.string().regex(/^[a-z0-9][a-z0-9-]*-[0-9a-f]{8}$/),
    titleJa: z.string().min(1),
    titleOriginal: z.string().min(1),
    description: z.string().min(1),
    briefJa: z.string().min(1),
    excerptJa: z.string().min(1),
    publishedAt: z.iso.datetime({ offset: true }),
    dateJst: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    sourceId: z.string().min(1),
    sourceName: z.string().min(1),
    sourceHomepage: z.url().nullable().optional(),
    sourceUrl: z.url(),
    canonicalUrl: z.url(),
    imageUrl: z.url().nullable().optional(),
    imageLicense: z.string().nullable().optional(),
    author: z.string().nullable().optional(),
    translationStatus: z.enum(['complete', 'partial']),
    titleTranslationStatus: z
      .enum(['legacy', 'translated', 'quality_rejected', 'translation_failed', 'source_missing'])
      .optional(),
    summaryTranslationStatus: z
      .enum(['legacy', 'translated', 'quality_rejected', 'translation_failed', 'source_missing'])
      .optional(),
    titleQualityGate: z.enum(['passed', 'rejected', 'not_run']).optional(),
    summaryQualityGate: z.enum(['passed', 'rejected', 'not_run']).optional(),
    titleFallbackApplied: z.boolean().optional(),
    summaryFallbackApplied: z.boolean().optional(),
    titleFallbackReasons: z.array(z.string()).optional(),
    summaryFallbackReasons: z.array(z.string()).optional(),
    translationFallbackReasons: z.array(z.string()).optional(),
    dedupeKey: z.string().min(1),
    fetchedAt: z.iso.datetime({ offset: true }),
    generatedAt: z.iso.datetime({ offset: true }),
    updatedAt: z.iso.datetime({ offset: true }),
    humanEdited: z.boolean().default(false),
    correctionHistory: z.array(z.unknown()).default([]),
    noindex: z.boolean().default(false),
  }),
});

export const collections = { articles };
