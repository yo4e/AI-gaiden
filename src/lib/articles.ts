import { formatJapaneseDate } from './site';

export interface ArticleData {
  articleId: string;
  titleJa: string;
  titleOriginal: string;
  description: string;
  briefJa: string;
  excerptJa: string;
  publishedAt: string;
  dateJst: string;
  sourceId: string;
  sourceName: string;
  sourceHomepage?: string | null;
  sourceUrl: string;
  canonicalUrl: string;
  imageUrl?: string | null;
  imageLicense?: string | null;
  author?: string | null;
  translationStatus: 'complete' | 'partial';
  dedupeKey: string;
  fetchedAt: string;
  generatedAt: string;
  updatedAt: string;
  humanEdited: boolean;
  correctionHistory: unknown[];
  noindex: boolean;
}

export interface ArticleLike {
  data: ArticleData;
}

export function articlePath(data: Pick<ArticleData, 'dateJst' | 'articleId'>): string {
  const [year, month, day] = data.dateJst.split('-');
  return `/articles/${year}/${month}/${day}/${data.articleId}/`;
}

export function sortArticles<T extends ArticleLike>(articles: T[]): T[] {
  return [...articles].sort((a, b) => {
    const published = b.data.publishedAt.localeCompare(a.data.publishedAt);
    return published || a.data.articleId.localeCompare(b.data.articleId);
  });
}

export function groupArticlesByDate<T extends ArticleLike>(articles: T[]): Map<string, T[]> {
  const groups = new Map<string, T[]>();
  for (const article of sortArticles(articles)) {
    groups.set(article.data.dateJst, [...(groups.get(article.data.dateJst) || []), article]);
  }
  return groups;
}

export function dailyTitle(date: string, articles: ArticleLike[]): string {
  const headline = articles[0]?.data.titleJa || '海外AI公式発表';
  const shortHeadline = headline.length > 32 ? `${headline.slice(0, 31)}…` : headline;
  return `海外AIニュース ${formatJapaneseDate(date)}｜${shortHeadline}｜AI外電`;
}

export function dailyDescription(date: string, articles: ArticleLike[]): string {
  const sources = [...new Set(articles.map((article) => article.data.sourceName))].join('、');
  const headlines = articles
    .slice(0, 2)
    .map((article) => article.data.titleJa)
    .join('、');
  const text = `${formatJapaneseDate(date)}に${sources}が公式配信した海外AIニュース${articles.length}件を日本語で紹介します。${headlines}などの発表をまとめています。各項目から原文の公式発表を確認できます。`;
  if (text.length <= 160) return text;
  const candidate = text.slice(0, 160);
  const boundary = Math.max(
    candidate.lastIndexOf('。'),
    candidate.lastIndexOf('！'),
    candidate.lastIndexOf('？'),
  );
  return boundary >= 119
    ? candidate.slice(0, boundary + 1)
    : `${candidate.slice(0, 159).trimEnd()}…`;
}

export function articleDateRange(articles: ArticleLike[]): {
  publishedAt: string;
  updatedAt: string;
} {
  const publishedAt = [...articles].sort((a, b) =>
    a.data.publishedAt.localeCompare(b.data.publishedAt),
  )[0]?.data.publishedAt;
  const updatedAt = [...articles].sort((a, b) =>
    b.data.updatedAt.localeCompare(a.data.updatedAt),
  )[0]?.data.updatedAt;
  return { publishedAt: publishedAt || updatedAt, updatedAt: updatedAt || publishedAt };
}
