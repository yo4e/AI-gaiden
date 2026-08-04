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
    id: 'microsoft-ai',
    name: 'Microsoft AI Blog',
    homepage: 'https://www.microsoft.com/en-us/ai/blog/',
    feedUrl: 'https://www.microsoft.com/en-us/ai/blog/feed',
    description: 'MicrosoftのAI製品、企業導入、開発基盤に関する公式発表',
    enabled: true,
  },
  {
    id: 'mistral-ai',
    name: 'Mistral AI News',
    homepage: 'https://mistral.ai/news/',
    feedUrl: 'https://mistral.ai/rss.xml',
    description: 'Mistral AIのモデル、製品、研究、企業向け機能の公式発表',
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
    id: 'apple-ml-research',
    name: 'Apple Machine Learning Research',
    homepage: 'https://machinelearning.apple.com/',
    feedUrl: 'https://machinelearning.apple.com/rss.xml',
    description: 'Appleの基盤モデル、オンデバイスAI、機械学習研究の公式発表',
    enabled: true,
  },
  {
    id: 'cohere-blog',
    name: 'Cohere Blog',
    homepage: 'https://cohere.com/blog',
    feedUrl: 'https://cohere.com/blog/rss.xml',
    description: 'Cohereの企業向けAI、モデル、研究、導入事例に関する公式ブログ',
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
  {
    id: 'mlcommons',
    name: 'MLCommons',
    homepage: 'https://mlcommons.org/',
    feedUrl: 'https://mlcommons.org/feed/',
    description: 'AIベンチマーク、性能評価、安全性評価に関するMLCommons公式発表',
    enabled: true,
  },
];
