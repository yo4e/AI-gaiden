import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { sortArticles } from '../lib/articles';
import { latestArticleUpdatedAt, RSS_NAMESPACES, rssItemForArticle } from '../lib/rss';
import { DEFAULT_DESCRIPTION } from '../lib/site';

export async function GET(context: APIContext) {
  const articles = sortArticles(await getCollection('articles'));
  const site = context.site!;
  const feedUrl = new URL('/feed.xml', site).href;
  const latestUpdatedAt = latestArticleUpdatedAt(articles);
  return rss({
    title: '海外AIニュース速報｜AI外電',
    description: DEFAULT_DESCRIPTION,
    site,
    trailingSlash: true,
    items: articles.map((article) => rssItemForArticle(article, site)),
    xmlns: RSS_NAMESPACES,
    customData: [
      '<language>ja</language>',
      `<atom:link href="${feedUrl}" rel="self" type="application/rss+xml" />`,
      latestUpdatedAt ? `<lastBuildDate>${latestUpdatedAt.toUTCString()}</lastBuildDate>` : '',
    ].join(''),
  });
}
