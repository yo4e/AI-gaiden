import type { RSSFeedItem } from '@astrojs/rss';
import { sources } from '../data/sources';
import { articlePath, type ArticleData, type ArticleLike } from './articles';

export const RSS_NAMESPACES = {
  atom: 'http://www.w3.org/2005/Atom',
  gaiden: 'https://github.com/yo4e/AI-gaiden/ns/rss',
};

const SOURCE_FEED_URLS = new Map(sources.map((source) => [source.id, source.feedUrl]));

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

function sourceFeedUrl(sourceId: string): string {
  const feedUrl = SOURCE_FEED_URLS.get(sourceId);
  if (!feedUrl) throw new Error(`RSS source feed is not configured: ${sourceId}`);
  return feedUrl;
}

function itemCustomData(data: RssArticleData): string {
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
    `<gaiden:translationStatus>${data.translationStatus}</gaiden:translationStatus>`,
    titleStatus,
    summaryStatus,
  ].join('');
}

export function rssItemForArticle(article: RssArticle, site: URL): RSSFeedItem {
  const { data } = article;
  const link = absoluteArticleUrl(article, site);

  return {
    title: data.titleJa,
    // briefJa is the AI外電 short report. Do not use source RSS HTML, article HTML, or image data here.
    description: data.briefJa,
    pubDate: new Date(data.publishedAt),
    link,
    categories: [data.sourceName],
    source: {
      title: data.sourceName,
      // RSS 2.0 source.url identifies the source channel XML, not its homepage or article URL.
      url: sourceFeedUrl(data.sourceId),
    },
    customData: itemCustomData(data),
  };
}

export function latestArticleUpdatedAt(articles: RssArticle[]): Date | undefined {
  const latest = articles.reduce<RssArticle | undefined>((current, article) => {
    if (!current || article.data.updatedAt > current.data.updatedAt) return article;
    return current;
  }, undefined);
  return latest ? new Date(latest.data.updatedAt) : undefined;
}
