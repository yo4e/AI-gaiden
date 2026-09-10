import type { RSSFeedItem } from '@astrojs/rss';
import { sources } from '../data/sources';
import { articlePath, type ArticleData, type ArticleLike } from './articles';

export const RSS_NAMESPACES = {
  atom: 'http://www.w3.org/2005/Atom',
  gaiden: 'https://github.com/yo4e/AI-gaiden/ns/rss',
};

const SOURCE_FEED_URLS = new Map(
  sources
    .filter((source) => source.sourceType !== 'github_releases')
    .map((source) => [source.id, source.feedUrl]),
);

const SOURCE_TYPES = new Map(
  sources.map((source) => [source.id, source.sourceType ?? 'rss'] as const),
);

type RssArticleData = Pick<
  ArticleData,
  | 'articleId'
  | 'titleJa'
  | 'briefJa'
  | 'publishedAt'
  | 'updatedAt'
  | 'sourceId'
  | 'sourceName'
  | 'translationStatus'
> & {
  titleTranslationStatus?: string;
  summaryTranslationStatus?: string;
};

export type RssArticle = ArticleLike & { data: RssArticleData };

export function absoluteArticleUrl(article: RssArticle, site: URL): string {
  return new URL(articlePath(article.data), site).href;
}

function sourceFeedUrl(sourceId: string): string | undefined {
  return SOURCE_FEED_URLS.get(sourceId);
}

function sourceType(sourceId: string): 'rss' | 'github_releases' {
  return SOURCE_TYPES.get(sourceId) ?? 'rss';
}

function itemCustomData(
  data: RssArticleData,
  sourceTransport: 'rss' | 'github_releases',
): string {
  const titleStatus = data.titleTranslationStatus
    ? `<gaiden:titleTranslationStatus>${data.titleTranslationStatus}</gaiden:titleTranslationStatus>`
    : '';
  const summaryStatus = data.summaryTranslationStatus
    ? `<gaiden:summaryTranslationStatus>${data.summaryTranslationStatus}</gaiden:summaryTranslationStatus>`
    : '';
  const updatedAt = new Date(data.updatedAt).toISOString();

  return [
    `<atom:updated>${updatedAt}</atom:updated>`,
    `<gaiden:articleId>${data.articleId}</gaiden:articleId>`,
    `<gaiden:sourceType>${sourceTransport}</gaiden:sourceType>`,
    `<gaiden:translationStatus>${data.translationStatus}</gaiden:translationStatus>`,
    titleStatus,
    summaryStatus,
  ].join('');
}

export function rssItemForArticle(article: RssArticle, site: URL): RSSFeedItem {
  const { data } = article;
  const link = absoluteArticleUrl(article, site);
  const feedUrl = sourceFeedUrl(data.sourceId);
  const sourceTransport = sourceType(data.sourceId);

  return {
    title: data.titleJa,
    // briefJa is the AI外電 short report. Do not use source HTML or image data here.
    description: data.briefJa,
    pubDate: new Date(data.publishedAt),
    link,
    categories: [data.sourceName],
    ...(feedUrl
      ? {
          source: {
            title: data.sourceName,
            // RSS 2.0 source.url identifies source channel XML. REST API URLs are omitted.
            url: feedUrl,
          },
        }
      : {}),
    customData: itemCustomData(data, sourceTransport),
  };
}

export function latestArticleUpdatedAt(articles: RssArticle[]): Date | undefined {
  const latest = articles.reduce<RssArticle | undefined>((current, article) => {
    if (!current || article.data.updatedAt > current.data.updatedAt) return article;
    return current;
  }, undefined);
  return latest ? new Date(latest.data.updatedAt) : undefined;
}
