import type { Source } from '../data/sources';

const CATEGORY_LABELS: Record<string, string> = {
  'artificial-intelligence': 'AI',
  product: '製品',
  research: '研究',
  safety: '安全性',
  'machine-learning': '機械学習',
  'open-source': 'オープンソース',
  enterprise: '企業導入',
  'developer-tools': '開発者向けツール',
  'on-device': 'オンデバイスAI',
  cloud: 'クラウド',
  'deep-learning': 'ディープラーニング',
  hardware: 'ハードウェア',
  benchmarks: 'ベンチマーク',
};

export function sourceCategoryLabel(category: string): string {
  return CATEGORY_LABELS[category] || category.replaceAll('-', ' ');
}

export function sourceImagePolicyLabel(imagePolicy: Source['imagePolicy']): string {
  if (imagePolicy === 'rss_only') return '公式RSS・Atomに明示された画像のみ';
  return '画像を取得しない';
}
