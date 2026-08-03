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
    id: 'openai-news',
    name: 'OpenAI News',
    homepage: 'https://openai.com/news/',
    feedUrl: 'https://openai.com/news/rss.xml',
    description: 'OpenAIの製品、研究、安全性、企業発表を掲載する公式ニュース',
    enabled: true,
  },
  {
    id: 'google-ai',
    name: 'Google AI',
    homepage: 'https://blog.google/technology/ai/',
    feedUrl: 'https://blog.google/technology/ai/rss/',
    description: 'Googleが公式ブログで発表するAI関連情報',
    enabled: true,
  },
  {
    id: 'google-deepmind',
    name: 'Google DeepMind',
    homepage: 'https://deepmind.google/blog/',
    feedUrl: 'https://deepmind.google/blog/rss.xml',
    description: 'Google DeepMindのモデル、研究、安全性、科学分野の公式発表',
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
    id: 'aws-machine-learning',
    name: 'AWS Artificial Intelligence',
    homepage: 'https://aws.amazon.com/blogs/machine-learning/',
    feedUrl: 'https://aws.amazon.com/blogs/machine-learning/feed/',
    description: 'AWSの生成AI、機械学習、Amazon Bedrockなどに関する公式技術情報',
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
