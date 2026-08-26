export const SITE_NAME = 'AI外電';
export const DEFAULT_TITLE = '海外AIニュース速報｜AI外電';
export const DEFAULT_DESCRIPTION =
  'Google AI、Hugging Face、GitHub、NVIDIAなどの海外AI公式発表を、日本語の短い日刊ダイジェストで紹介します。';
export const SITE_HEADLINE = '海外AI公式発表を\n日本語で毎日ダイジェスト';
export const SITE_URL = 'https://ai.gaiden.news';
export const REPOSITORY_URL = 'https://github.com/yo4e/AI-gaiden';
export const OPERATOR_NAME = '外電通信';
export const OPERATOR_URL = 'https://gaiden.news/';
export const OPERATOR_DISCLOSURE = '外電通信は、個人事業主・山田佳江が運営する事業の一つです。';
export const OPERATOR_STATEMENT = `AI外電は、${OPERATOR_NAME}が運営しています。${OPERATOR_DISCLOSURE}`;

const DEFAULT_NEWS_IMAGE_PATHS = [
  '/default-news-image-1.webp',
  '/default-news-image-2.webp',
  '/default-news-image-3.webp',
  '/default-news-image-4.webp',
  '/default-news-image-5.webp',
  '/default-news-image-6.webp',
  '/default-news-image-7.webp',
  '/default-news-image-8.webp',
  '/default-news-image-9.webp',
  '/default-news-image-10.webp',
] as const;

interface NewsCardImageInput {
  articleId: string;
  imageUrl?: string | null;
}

export interface NewsCardImageSelection {
  src: string;
  isSource: boolean;
}

export function isPreviewBuild(): boolean {
  return Boolean(process.env.CF_PAGES) && process.env.CF_PAGES_BRANCH !== 'main';
}

export function formatJapaneseDate(value: string): string {
  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(`${value}T00:00:00+09:00`));
}

export function formatJapaneseMonth(value: string): string {
  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'long',
  }).format(new Date(`${value}-01T00:00:00+09:00`));
}

export function formatJapaneseDateTime(value: string): string {
  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(new Date(value));
}

export function defaultNewsImagePath(seed: string, avoidPath?: string | null): string {
  const randomSuffix = seed.match(/[0-9a-f]{8}$/i)?.[0];
  let index: number;

  if (randomSuffix) {
    index = Number.parseInt(randomSuffix, 16) % DEFAULT_NEWS_IMAGE_PATHS.length;
  } else {
    let hash = 2166136261;
    for (const character of seed) {
      hash ^= character.charCodeAt(0);
      hash = Math.imul(hash, 16777619) >>> 0;
    }
    index = hash % DEFAULT_NEWS_IMAGE_PATHS.length;
  }

  if (
    avoidPath &&
    DEFAULT_NEWS_IMAGE_PATHS.length > 1 &&
    DEFAULT_NEWS_IMAGE_PATHS[index] === avoidPath
  ) {
    index = (index + 1) % DEFAULT_NEWS_IMAGE_PATHS.length;
  }

  return DEFAULT_NEWS_IMAGE_PATHS[index];
}

export function selectSequentialNewsCardImages(
  items: readonly NewsCardImageInput[],
): NewsCardImageSelection[] {
  let previousSrc: string | null = null;

  return items.map((item) => {
    const sourceImage = item.imageUrl?.trim() || null;
    let src = sourceImage || defaultNewsImagePath(item.articleId, previousSrc);
    let isSource = Boolean(sourceImage);

    if (src === previousSrc) {
      src = defaultNewsImagePath(item.articleId, previousSrc);
      isSource = false;
    }

    previousSrc = src;
    return { src, isSource };
  });
}
