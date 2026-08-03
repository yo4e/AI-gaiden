import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { DEFAULT_DESCRIPTION } from '../lib/site';

export async function GET(context: APIContext) {
  const entries = (await getCollection('daily')).sort((a, b) =>
    b.data.date.localeCompare(a.data.date),
  );
  return rss({
    title: '海外AIニュース速報｜AI外電',
    description: DEFAULT_DESCRIPTION,
    site: context.site!,
    trailingSlash: true,
    items: entries.map((entry) => ({
      title: entry.data.title,
      description: entry.data.description,
      pubDate: new Date(entry.data.publishedAt),
      link: `/daily/${entry.data.date}/`,
      categories: entry.data.sources,
    })),
    customData: '<language>ja</language>',
  });
}
