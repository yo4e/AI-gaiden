export const SITE_NAME = 'AI外電';
export const DEFAULT_TITLE = '海外AIニュース速報｜AI外電';
export const DEFAULT_DESCRIPTION =
  'Google AI、Hugging Face、GitHub、NVIDIAなどの海外AI公式発表を、日本語の短い日刊ダイジェストで紹介します。';
export const SITE_HEADLINE = '海外AI公式発表を日本語で毎日ダイジェスト';
export const REPOSITORY_URL = 'https://github.com/yo4e/AI-gaiden';

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

export function formatJapaneseDateTime(value: string): string {
  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}
