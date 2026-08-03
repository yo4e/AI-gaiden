export type Source = {
  id: string;
  name: string;
  homepage: string;
  feedUrl: string;
  description: string;
  enabled: boolean;
};

export const sources: Source[] = [
  {
    id: 'google-ai',
    name: 'Google AI',
    homepage: 'https://blog.google/technology/ai/',
    feedUrl: 'https://blog.google/technology/ai/rss/',
    description: 'Googleが公式ブログで発表するAI関連情報',
    enabled: true,
  },
  {
    id: 'hugging-face',
    name: 'Hugging Face Blog',
    homepage: 'https://huggingface.co/blog',
    feedUrl: 'https://huggingface.co/blog/feed.xml',
    description: 'Hugging Faceのモデル、データセット、研究・開発情報',
    enabled: true,
  },
  {
    id: 'github-ai-ml',
    name: 'GitHub AI & ML',
    homepage: 'https://github.blog/ai-and-ml/',
    feedUrl: 'https://github.blog/ai-and-ml/feed/',
    description: 'GitHubが公式ブログで発表するAI・機械学習情報',
    enabled: true,
  },
  {
    id: 'nvidia-deep-learning',
    name: 'NVIDIA Deep Learning Blog',
    homepage: 'https://blogs.nvidia.com/blog/category/deep-learning/',
    feedUrl: 'https://blogs.nvidia.com/blog/category/deep-learning/feed/',
    description: 'NVIDIA公式ブログのディープラーニング関連情報',
    enabled: true,
  },
];
