import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { articlePath, sortArticles } from '../lib/articles';
import { DEFAULT_DESCRIPTION } from '../lib/site';

export async function GET(context: APIContext) {
  const articles = sortArticles(await getCollection('articles'));
  return rss({
    title: '海外AIニュース速報｜AI外電',
    description: DEFAULT_DESCRIPTION,
    site: context.site!,
    trailingSlash: true,
    items: articles.map((article) => ({
      title: article.data.titleJa,
      description: article.data.briefJa,
      pubDate: new Date(article.data.publishedAt),
      link: articlePath(article.data),
      categories: [article.data.sourceName],
    })),
    customData: '<language>ja</language>',
  });
}
