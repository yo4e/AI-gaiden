# AI外電 実装設計書

更新日：2026-08-03  
対象リポジトリ：`yo4e/AI-gaiden`

## 1. プロジェクト概要

### 1.1 サイト名

- ブランド名：**AI外電**
- SEOタイトル：**海外AIニュース速報｜AI外電**
- H1：**海外AI公式発表を日本語で毎日ダイジェスト**
- 基本説明文：**OpenAI、Google、Anthropic、GitHub、NVIDIAなど、海外のAI関連組織が発信する公式情報を収集し、日本語の短いニュースとして紹介する自動ダイジェストサイト。**

### 1.2 目的

海外のAI関連組織が公式に配信するRSS/Atomフィードを定期取得し、英語の見出しとフィード内概要を日本語化して、日付別の短いニュースダイジェストとして公開する。

本プロジェクトは、小規模な自動ニュースサイトをGitHub ActionsとCloudflare Pagesだけで運用できるかを検証する試験運用である。

### 1.3 サイト上の必須表示

全ページのヘッダー直下またはファーストビュー内に、次の趣旨を明示する。

> 試験運用中：本サイトの記事は、公式フィードを基に機械的な収集・自動翻訳・定型編集を行っています。翻訳や要約に誤りが含まれる可能性があるため、重要な情報はリンク先の公式発表をご確認ください。

記事本文にも次を表示する。

- 自動収集
- 自動翻訳
- 情報源は公式発表
- 最終確認はリンク先を推奨

この表示は目立たなく隠さず、ただし記事の可読性を損なわないデザインにする。

## 2. MVPの範囲

### 2.1 今回実装するもの

1. 公式RSS/Atomフィードの取得
2. フィード項目の正規化
3. 重複排除
4. AI関連度による簡易フィルタリング
5. 英語タイトルとフィード概要の日本語化
6. 定型ルールによる短いニュース本文の生成
7. 日刊ダイジェストページの静的生成
8. トップページ、日付アーカイブ、情報源ページの生成
9. SEO基本実装
10. GitHub Actionsによる定時更新
11. Cloudflare Pagesへの自動デプロイ
12. 手動実行とローカル実行
13. 最低限のテスト

### 2.2 今回実装しないもの

- Blueskyへの自動投稿
- X、Instagram、Facebook等への投稿
- 記事ページHTMLのスクレイピング
- `og:image`取得のための記事ページ巡回
- 外部AI API、翻訳API、要約APIの利用
- ユーザー登録、コメント、検索バックエンド
- データベース
- Cloudflare Workers / Pages Functions
- 独自ドメイン
- 広告

Bluesky連携はPhase 2として別設計にする。

## 3. 基本方針

### 3.1 取得対象

取得対象は、配信元が明示的に公開しているRSSまたはAtomフィードに限定する。

- 公式企業ブログ
- 公式研究組織ブログ
- 公式製品アップデート
- 公式GitHub ChangelogやReleases

HTMLページを巡回して情報を抜き出す処理はMVPに含めない。

### 3.2 著作権・転載配慮

掲載する情報は次に限定する。

- 記事タイトルの日本語訳
- フィードに含まれる概要を基にした短い日本語文
- 配信元名
- 公開日時
- 元記事URL
- フィードが明示的に配信しているサムネイルURL

以下は行わない。

- 記事本文の全文転載
- 長文の逐語翻訳
- 記事ページからの画像取得
- 画像ファイルのリポジトリ内保存
- 元記事を読んだように見せる独自の補足
- フィードに存在しない事実の推測

各項目に必ず「公式発表を読む」リンクを付ける。

### 3.3 AI APIを使わない

翻訳はGitHub ActionsのLinuxランナー上でローカルモデルを実行する。

第一候補：

- モデル：`Helsinki-NLP/opus-mt-en-jap`
- ライセンス：Apache-2.0
- 実行：Python + Transformers 4系 + PyTorch CPU

`transformers`は5系で翻訳pipelineの扱いが変わっているため、初期実装では互換性を優先して`transformers<5`に固定する。

モデルは毎回リポジトリへ保存せず、GitHub Actionsのキャッシュを利用する。

### 3.4 翻訳と記事化の境界

このサイトは生成AIによる自由作文を行わない。

記事本文は次の入力だけから作る。

- RSSタイトル
- RSS概要・description・summary
- RSSのカテゴリ
- RSS公開日時
- 配信元名

処理は次の順番とする。

1. HTMLタグを除去
2. 不要な定型文を除去
3. 英文を最大2〜3文に制限
4. タイトルと概要を日本語翻訳
5. 用語辞書で表記統一
6. 定型文として整形
7. 文字数を約120〜300字に制限

翻訳結果を基に新しい事実を付け足してはならない。

## 4. 技術構成

### 4.1 推奨スタック

- 静的サイト：Astro
- 言語：TypeScript（strict）
- RSS取得・翻訳：Python 3.12
- フィード解析：`feedparser`
- HTML除去：`beautifulsoup4`
- HTTP：`httpx`
- 設定：YAML
- 翻訳：`transformers<5`, `torch`, `sentencepiece`
- テスト：`pytest`、Astroのビルド確認
- パッケージ管理：npmとpip
- デプロイ：Cloudflare Pages Direct Upload
- デプロイCLI：Wrangler

Astroは完全静的出力とし、MVPではクライアントJavaScriptを極力配信しない。

### 4.2 Cloudflare Pages

- プロジェクト名候補：`ai-gaiden`
- 公開先：`<project-name>.pages.dev`
- 独自ドメイン：当面設定しない
- 出力ディレクトリ：`dist`
- デプロイ方式：GitHub ActionsからWranglerによるDirect Upload

Cloudflare PagesプロジェクトはユーザーがCloudflare側で一度作成する。Codexは、作成後に必要なワークフローと設定を実装する。

GitHub Secrets：

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

GitHub Repository Variableまたはコード定数：

- `CLOUDFLARE_PAGES_PROJECT=ai-gaiden`
- `SITE_URL=https://ai-gaiden.pages.dev`（実際のプロジェクトURL確定後に変更）

API TokenはCloudflare Pagesの編集に必要な最小権限にする。

## 5. ディレクトリ案

```text
.
├── .github/
│   └── workflows/
│       ├── update-and-deploy.yml
│       └── ci.yml
├── config/
│   ├── sources.yml
│   ├── glossary.yml
│   └── filters.yml
├── data/
│   ├── entries/
│   │   └── YYYY/MM/*.json
│   ├── digests/
│   │   └── YYYY-MM-DD.json
│   └── state.json
├── docs/
│   └── IMPLEMENTATION_SPEC.md
├── scripts/
│   ├── fetch_feeds.py
│   ├── normalize.py
│   ├── translate.py
│   ├── build_digest.py
│   └── validate_data.py
├── src/
│   ├── components/
│   ├── layouts/
│   ├── pages/
│   │   ├── index.astro
│   │   ├── about.astro
│   │   ├── methodology.astro
│   │   ├── sources.astro
│   │   ├── archive.astro
│   │   └── news/[...slug].astro
│   ├── styles/
│   └── lib/
├── public/
│   ├── favicon.svg
│   ├── robots.txt
│   └── default-og.svg
├── tests/
├── AGENTS.md
├── README.md
├── astro.config.mjs
├── package.json
├── package-lock.json
├── pyproject.toml
└── requirements.lock または requirements.txt
```

Codexは実装時に合理的な変更をしてよいが、データ、取得処理、表示処理を分離すること。

## 6. RSSソース管理

### 6.1 `config/sources.yml`

想定スキーマ：

```yaml
sources:
  - id: github-changelog
    name: GitHub Changelog
    organization: GitHub
    feed_url: https://github.blog/changelog/feed/
    site_url: https://github.blog/changelog/
    language: en
    enabled: true
    trust_level: official
    include_keywords:
      - AI
      - Copilot
      - model
      - agent
      - machine learning
    exclude_keywords: []
```

### 6.2 初期ソース候補

Codexは実装時にHTTP応答とフィード形式を確認し、正常に解析できる公式フィードだけを有効化する。

候補：

- Google公式ブログRSS：`https://blog.google/rss/`
- GitHub Changelog：`https://github.blog/changelog/feed/`
- NVIDIA Generative AIカテゴリ：`https://blogs.nvidia.com/blog/category/generative-ai/feed/`
- Hugging Face Blog：`https://huggingface.co/blog/feed.xml`

OpenAI、Anthropic、Google DeepMind、Meta AI等について、公式RSS/Atomが確認できない場合はMVPで無理に追加しない。HTMLスクレイピングに切り替えてはならない。

### 6.3 フィード障害

- 1ソースだけ失敗：警告をログ出力し、他ソースの処理を継続
- すべて失敗：ワークフローを失敗させ、既存サイトを更新しない
- XML不正：そのソースをスキップ
- タイムアウト：最大2回まで短い再試行
- User-Agent：サイト名とリポジトリURLを含む識別可能な値

## 7. データモデル

各ニュース項目の必須項目：

```json
{
  "id": "sha256-based-stable-id",
  "source_id": "github-changelog",
  "source_name": "GitHub Changelog",
  "organization": "GitHub",
  "original_title": "Original English title",
  "title_ja": "日本語タイトル",
  "original_summary": "Feed-provided summary",
  "summary_ja": "日本語の短い記事",
  "source_url": "https://example.com/article",
  "canonical_source_url": "https://example.com/article",
  "published_at": "2026-08-03T00:00:00Z",
  "collected_at": "2026-08-03T07:17:00+09:00",
  "image_url": null,
  "categories": ["AI"],
  "translation_status": "success",
  "automation_notice": true
}
```

### 7.1 IDと重複排除

優先順：

1. RSS GUID
2. 正規化済みURL
3. `source_id + original_title + published_at`のSHA-256

URL正規化：

- `utm_*`等の追跡クエリを除去
- フラグメントを除去
-末尾スラッシュを統一
- ホスト名を小文字化

同一URLまたは同一GUIDは再掲載しない。

## 8. AI関連度フィルタ

### 8.1 目的

Google等の総合フィードから、AI関連項目だけを抽出する。

### 8.2 初期ルール

タイトル、概要、カテゴリを小文字化し、キーワード一致でスコアリングする。

高スコア語：

- artificial intelligence
- generative AI
- large language model
- LLM
- machine learning
- foundation model
- AI agent / agents
- Gemini
- Claude
- ChatGPT
- Copilot
- model release

除外候補：

- AIと無関係な一般企業ニュース
- 採用情報だけの記事
- イベント告知だけで技術・製品情報がないもの

初期は複雑な分類器を作らず、設定ファイルで調整できる決定的ルールを使う。

## 9. 画像の扱い

### 9.1 取得優先順

1. `media:thumbnail`
2. `media:content`の画像
3. `enclosure`の画像
4. フィード本文内の`img`要素
5. 画像なし

### 9.2 禁止事項

- 元記事HTMLへアクセスして`og:image`を取らない
- 画像をGitHubへコピーしない
- 画像を変換・トリミングして再配布しない
- ライセンス不明画像をサイトの所有物のように扱わない

### 9.3 表示

- 外部URLを直接参照
- `loading="lazy"`
- `decoding="async"`
- 幅と高さまたはaspect-ratioを指定しCLSを防ぐ
- altは記事タイトルと配信元から機械生成
- 表示失敗時は配信元名入りのCSSプレースホルダー
- 画像クリック先は元記事
- 画像付近に配信元名を表示

## 10. 翻訳仕様

### 10.1 入力制限

- タイトル：全文
- 概要：HTML除去後、最大1,000英字程度
- 最大3文
- ナビゲーション、Cookie文、購読誘導等を除去

### 10.2 用語辞書

`config/glossary.yml`で表記を固定する。

例：

```yaml
OpenAI: OpenAI
Anthropic: Anthropic
Google DeepMind: Google DeepMind
GitHub Copilot: GitHub Copilot
large language model: 大規模言語モデル
AI agent: AIエージェント
open source: オープンソース
```

製品名や組織名は不用意に翻訳しない。

### 10.3 短い記事の生成ルール

- 自動翻訳した概要から最大2文を採用
- 文章の重複や不自然な改行を整える
- 120〜300字を目安
- 断定表現は元概要の範囲内
- 主語が不明な場合は配信元名を補う
- 内容が不足する場合は無理に水増ししない
- 「〜とみられます」「〜かもしれません」等の推測を追加しない

記事末尾には必ず次の導線を置く。

- `公式発表を読む（英語）`

### 10.4 失敗時

- タイトル翻訳失敗：その項目は掲載しない
- 概要翻訳失敗：タイトルと定型説明だけで掲載可能
- モデルロード失敗：新規記事を公開せずワークフロー失敗
- 不自然な文字化け：検証エラーとして掲載しない

## 11. ページ構成

### 11.1 トップページ

- 試験運用バナー
- サイトタイトルと説明
- 最新の日刊ダイジェスト
- 過去7日分へのリンク
- 情報源別リンク
- 更新日時
- 運用方法へのリンク

### 11.2 日刊ページ

URL例：

`/news/2026/08/03/`

ページタイトル例：

`2026年8月3日の海外AIニュース｜AI外電`

内容：

- 日付
- 掲載件数
- 各ニュースカード
- 原文タイトル
- 日本語タイトル
- 短い日本語記事
- 配信元
- 公開日時
- サムネイル（存在する場合）
- 公式発表へのリンク
- 自動翻訳・試験運用表示
- 前日・翌日ナビゲーション

新着が0件の日は薄い日刊ページを生成しない。トップページに最終更新日時だけ表示する。

### 11.3 固定ページ

- `/about/`：サイト概要と試験運用の説明
- `/methodology/`：収集・翻訳・選定方法
- `/sources/`：採用中の公式フィード一覧
- `/archive/`：年月別アーカイブ

### 11.4 将来ページ

- 情報源別アーカイブ
- カテゴリ別アーカイブ
- 検索
- 訂正履歴

## 12. SEO要件

SEOは後付けではなくMVPの必須要件とする。

### 12.1 基本メタ情報

全ページで個別に生成する。

- `<title>`
- meta description
- canonical URL
- Open Graph
- X/Twitter Card互換メタ
- `lang="ja"`
- 適切なviewport

トップページ：

- title：`海外AIニュース速報｜AI外電`
- description：`OpenAI、Google、Anthropic、GitHub、NVIDIAなど、海外AI関連組織の公式発表を日本語の短いニュースで毎日紹介する自動ダイジェスト。`

日刊ページ：

- title：`YYYY年M月D日の海外AIニュース｜AI外電`
- description：当日の主要見出し2〜3件を含む自然な要約

### 12.2 見出し構造

- 1ページにつきH1は1つ
- 各ニュース見出しはH2
- 補助見出しはH3
- 見た目のために見出し階層を飛ばさない

### 12.3 構造化データ

JSON-LDを生成する。

トップページ：

- `WebSite`
- `Organization`

日刊ページ：

- `ItemList`
- 各ニュース項目に`NewsArticle`または`Article`

各項目の`isBasedOn`または適切な参照プロパティで元記事URLを示す。`author`をAI外電の編集部と偽装せず、自動ダイジェストであることを説明文に含める。

### 12.4 クロール支援

- `sitemap.xml`自動生成
- `robots.txt`
- 自サイトRSS/Atomフィード
- 過去記事への内部リンク
- パンくずリスト
- 孤立ページを作らない

### 12.5 URL設計

- 小文字英数字と日付
- 恒久的で変更しない
- クエリ依存ページを作らない
- canonicalを必ず指定

### 12.6 重複・薄いコンテンツ対策

- 同一ニュースを複数日に掲載しない
- 新着0件の日刊ページを作らない
- タグページを大量生成しない
- 自動生成された無内容な個別ページを作らない
- トップページ全文と日刊ページ全文を完全重複させない
- トップページは最新記事の抜粋、日刊ページは全文

### 12.7 信頼性と透明性

SEO上の信頼性も意識し、次を明示する。

- 自動運用であること
- 公式情報源のみを対象にすること
- 翻訳・要約に誤りがあり得ること
- 元記事を確認すべきこと
- 収集方法
- 採用情報源
- 修正依頼先としてGitHub Issuesへのリンク

### 12.8 パフォーマンス

- 静的HTML
- JavaScript最小化
- CSS最小化
- Webフォントを必須にしない
- 画像の遅延読み込み
- CLS対策
- 不要な外部トラッカーなし
- Lighthouse SEO 95以上を目標
- Lighthouse Performance 90以上を目標
- Accessibility 95以上を目標

### 12.9 独自ドメイン移行

当面は`pages.dev`をcanonicalとして使用する。

独自ドメイン取得後は、次を同時に行う前提で設計する。

1. `SITE_URL`を独自ドメインへ変更
2. canonical、sitemap、OG URLを再生成
3. `pages.dev`から独自ドメインへ301リダイレクト
4. Search Console等の設定を移行

URL生成処理にドメインを直書きせず、環境変数またはAstro設定から一元管理する。

## 13. デザイン要件

### 13.1 方針

- ニュースサイトとして読みやすい
- 自動生成サイト特有の安っぽさを避ける
- 日本語本文を主役にする
- スマートフォン優先
- 派手なアニメーション不要

### 13.2 必須要素

- サイトロゴまたは文字ロゴ「AI外電」
- 「海外AIニュース速報」の説明
- 試験運用バッジ
- 配信元が分かるニュースカード
- 日付と更新時刻
- 公式発表への明確なボタン

### 13.3 アクセシビリティ

- 十分なコントラスト
- キーボード操作
- focus-visible
- 意味のあるalt
- リンク文言を「こちら」だけにしない
- 日付は機械可読な`time`要素

## 14. GitHub Actions

### 14.1 `update-and-deploy.yml`

トリガー：

- 毎日 07:17 Asia/Tokyo
- `workflow_dispatch`

例：

```yaml
on:
  schedule:
    - cron: '17 7 * * *'
      timezone: 'Asia/Tokyo'
  workflow_dispatch:
```

毎時0分付近は混雑遅延が起きやすいため避ける。

### 14.2 処理順

1. checkout
2. Pythonセットアップ
3. Nodeセットアップ
4. pip / npm / Hugging Faceモデルのキャッシュ
5. RSS取得
6. 正規化・重複排除
7. 翻訳
8. データ検証
9. 日刊JSON生成
10. テスト
11. Astroビルド
12. 新規データをGitへコミット
13. Cloudflare Pagesへ`dist`をデプロイ

### 14.3 権限

最低限：

```yaml
permissions:
  contents: write
  deployments: write
```

Cloudflareの資格情報はSecretsから渡す。ログへ出力しない。

### 14.4 concurrency

同時実行を防ぐ。

```yaml
concurrency:
  group: ai-gaiden-production
  cancel-in-progress: false
```

### 14.5 デプロイ条件

- テスト成功
- データ検証成功
- Astroビルド成功
- 全RSS取得失敗ではない

既存本番を壊す可能性がある場合はデプロイしない。

### 14.6 `ci.yml`

トリガー：

- pull_request
- mainへのpush

処理：

- Python lint/test
- TypeScript/Astro check
- 静的ビルド
- リンクと構造化データの基本検証

PRからCloudflare本番へはデプロイしない。

## 15. Cloudflare初期設定手順

Codexの実装完了後、ユーザーが行う作業：

1. Cloudflare DashboardでWorkers & Pagesを開く
2. PagesのDirect Uploadプロジェクトを`ai-gaiden`名で作成
3. Cloudflare API Tokenを作成
4. Account IDを確認
5. GitHubリポジトリSecretsへ登録
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
6. 必要に応じてRepository Variableへ登録
   - `CLOUDFLARE_PAGES_PROJECT=ai-gaiden`
   - `SITE_URL=https://実際のプロジェクト名.pages.dev`
7. GitHub Actionsの`workflow_dispatch`を実行
8. 公開URLとcanonicalが一致することを確認

CloudflareのGit連携ではなく、GitHub Actions内で収集・翻訳・ビルドした成果物をWranglerでDirect Uploadする。

## 16. テスト要件

### 16.1 Python

- RSS 2.0の解析
- Atomの解析
- Media RSS画像抽出
- enclosure画像抽出
- HTML除去
- URL正規化
- GUID重複排除
- キーワードフィルタ
- 文字数制限
- 翻訳失敗時の扱い
- タイムゾーン変換

テスト用フィクスチャはローカルXMLを使い、CIで外部サイトへ依存しない。

### 16.2 サイト

- トップページ生成
- 日刊ページ生成
- 新着0件時に空ページを作らない
- canonical存在
- description存在
- H1が1つ
- JSON-LDがvalid JSON
- sitemapに日刊ページが含まれる
- robots.txt存在
- 画像なしでもレイアウトが崩れない

### 16.3 E2E相当

サンプルRSSから次を確認する。

1. 取得
2. 日本語データ生成
3. 日刊ページ生成
4. `dist`完成

実モデルを使う重い翻訳テストは通常CIではモック可能。定時ワークフローでは実モデルを使用する。

## 17. エラー・ログ

ログに含める：

- ソースごとの取得成功/失敗
- 取得件数
- フィルタ通過件数
- 重複除外件数
- 翻訳成功/失敗件数
- 掲載件数
- デプロイ結果

ログに含めない：

- Secret
- API Token
- Cloudflare認証情報
- 不要な全文RSS本文

## 18. セキュリティ

- RSS URLは設定ファイルのallow-listのみ
- フィード由来HTMLをそのまま描画しない
- HTMLは必ず除去またはサニタイズ
- URLスキームは`https`を基本とする
- JavaScript URL等を拒否
- GitHub Actionsの外部Actionはメジャーバージョンだけでなく可能ならコミットSHA固定
- Dependabotを有効化可能な構成
- SecretをPRワークフローへ渡さない

## 19. 受け入れ条件

CodexによるMVP完了条件：

- [ ] `npm ci && npm run build`で静的サイトが生成される
- [ ] Pythonスクリプトで公式RSSを取得できる
- [ ] HTMLページのスクレイピングを行っていない
- [ ] 外部AI API・翻訳APIを利用していない
- [ ] ローカル翻訳モデルで日本語タイトルと概要を生成できる
- [ ] 重複記事が再掲載されない
- [ ] RSS内画像が存在する場合のみ表示される
- [ ] 画像がなくても崩れない
- [ ] 全ページに試験運用表示がある
- [ ] 日刊ページが生成される
- [ ] 新着0件の日刊ページを作らない
- [ ] canonical、meta description、OG、JSON-LDがある
- [ ] sitemap.xml、robots.txt、自サイトRSSがある
- [ ] Lighthouse SEO 95以上を目標にした実装
- [ ] GitHub Actionsを手動実行できる
- [ ] 毎日07:17 Asia/Tokyoに定期実行される
- [ ] Cloudflare PagesへWranglerでデプロイできる
- [ ] Cloudflare Secret未設定時は分かりやすく失敗する
- [ ] Bluesky関連コードをまだ実装していない
- [ ] READMEにローカル実行と初期設定手順がある
- [ ] テストが通る

## 20. Phase 2候補

MVPが安定した後に検討する。

- Blueskyへの定時告知
- 当日の主要3見出しを投稿
- 投稿済みIDの保存
- 独自ドメイン
- Search Console
- ソース追加
- 人手による見出し修正
- 訂正履歴
- 情報源別ページ強化
- 日本語RSSの配信
- OGP画像の自動生成

## 21. Codexへの実装優先順位

1. 最小のAstroサイトを作る
2. サンプルデータで日刊ページを生成する
3. RSS取得・正規化・重複排除を実装する
4. ローカル翻訳を実装する
5. 画像抽出を実装する
6. SEO要件を満たす
7. テストを整える
8. GitHub Actionsを作る
9. Cloudflare Pagesデプロイを作る
10. ドキュメントを更新する

見た目より先に、取得データの正しさ、再実行安全性、透明性、SEOの基礎、デプロイの再現性を完成させること。
