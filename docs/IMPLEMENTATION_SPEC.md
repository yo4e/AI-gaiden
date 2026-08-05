# AI外電 実装設計書

更新日: 2026-08-05
対象リポジトリ: `yo4e/AI-gaiden`
実装担当想定: Codex

## 1. プロジェクト概要

### 1.1 サイト名

- ブランド名: **AI外電**
- SEOタイトル: **海外AIニュース速報｜AI外電**
- H1: **海外AI公式発表を日本語で毎日ダイジェスト**
- 初期公開先: Cloudflare Pages の `*.pages.dev`
- 独自ドメイン: 当面なし。継続運用の判断後に取得する。

### 1.2 目的

海外のAI関連企業・開発者組織が公式に配信しているRSS/Atomフィードを定期取得し、日本語の短いダイジェストへ整形して、静的ニュースサイトとして公開する。

本プロジェクトは小規模な試験運用であり、次の条件を守る。

- AI生成APIは使用しない。
- HTMLページのスクレイピングは行わない。
- 公式RSS/Atomおよび公式APIだけを情報源にする。
- 記事本文の全文転載は行わない。
- GitHub Actionsで収集・翻訳・生成・コミットを自動化する。
- GitHubへのpushを契機にCloudflare Pagesが自動デプロイする。
- Blueskyへの自動投稿はPhase 2とし、Phase 1には実装しない。

## 2. 試験運用表示

全ページ上部に、次の趣旨の告知を常時表示する。

> 試験運用中 — 本サイトは公式RSSを自動取得・自動翻訳して掲載しています。誤訳、取得漏れ、情報の遅延が生じる可能性があります。重要な情報は必ずリンク先の公式発表をご確認ください。

要件:

- トップページだけでなく全ページへ表示する。
- 視認できるが本文閲覧を妨げないデザインにする。
- 「試験運用中」の文字は省略しない。
- `/about/` に詳しい運用方針、情報源、免責、更新方式を掲載する。

## 3. Phase 1のスコープ

### 3.1 実装対象

1. 公式RSS/Atomフィードの取得
2. 新着判定と重複排除
3. RSS内タイトル・概要のサニタイズ
4. APIを使わないローカル英日翻訳
5. 日本語短報の定型生成
6. 日次ダイジェストページの生成
7. トップ、アーカイブ、情報源、About、Privacy、404ページの生成
8. SEOメタデータ、サイトマップ、robots.txt、構造化データ
9. GitHub Actionsの日次実行と手動実行
10. 変更がある場合だけ自動コミット
11. Cloudflare PagesのGit連携による自動デプロイ
12. テスト、ログ、失敗時の安全な停止

### 3.2 Phase 1で実装しないもの

- Bluesky投稿
- OpenAI等の有料または無料AI API
- 記事ページのHTMLスクレイピング
- RSSにない`og:image`の取得
- SNS埋め込み
- コメント機能
- 会員機能
- 独自ドメイン
- 広告
- 有料購読
- Cloudflare Workers / Pages Functions
- データベース
- WranglerによるDirect Upload

## 4. 技術構成

### 4.1 採用技術

- フロントエンド/静的サイト: Astro + TypeScript
- RSS取得・翻訳・コンテンツ生成: Python 3.12
- スタイリング: 素のCSSまたはAstro内のCSS。大型UIフレームワークは不要。
- ホスティング: Cloudflare Pages
- 定期実行: GitHub Actions
- コンテンツ保存: Gitリポジトリ内のMarkdown/JSON
- タイムゾーン: `Asia/Tokyo`

### 4.2 Astroを採用する理由

- 静的HTML出力でCloudflare Pagesと相性がよい。
- コンテンツコレクションでMarkdownの型検証ができる。
- SEOメタ情報、RSS、サイトマップを生成しやすい。
- JavaScriptを必要最小限に抑えられる。
- 日次アーカイブ型サイトに十分で、過剰なランタイムを必要としない。

### 4.3 想定依存関係

Node:

- `astro`
- `@astrojs/sitemap`
- `@astrojs/rss`
- `typescript`
- `prettier`
- `prettier-plugin-astro`

Python:

- `feedparser`
- `requests`
- `beautifulsoup4`
- `PyYAML`
- `python-dateutil`
- `argostranslate`
- `pytest`
- `ruff`

依存は必要最小限とし、未使用パッケージを追加しない。

## 5. 推奨ディレクトリ構成

```text
AI-gaiden/
├─ .github/
│  └─ workflows/
│     ├─ ci.yml
│     └─ daily-news.yml
├─ config/
│  ├─ feeds.yml
│  └─ site.yml
├─ data/
│  └─ seen.json
├─ docs/
│  └─ IMPLEMENTATION_SPEC.md
├─ public/
│  ├─ favicon.svg
│  ├─ default-news-image.svg
│  ├─ robots.txt
│  └─ _headers
├─ scripts/
│  ├─ update_news.py
│  ├─ feed_reader.py
│  ├─ translator.py
│  ├─ translation_quality.py
│  ├─ content_writer.py
│  ├─ migrate_articles.py
│  ├─ image_extractor.py
│  └─ utils.py
├─ src/
│  ├─ components/
│  │  ├─ TrialBanner.astro
│  │  ├─ NewsCard.astro
│  │  ├─ SourceBadge.astro
│  │  ├─ ArticleBulletin.astro
│  │  └─ SeoHead.astro
│  ├─ content/
│  │  ├─ config.ts
│  │  └─ articles/
│  │     └─ YYYY-MM-DD/
│  │        └─ <source-id>-<short-id>.md
│  ├─ layouts/
│  │  └─ BaseLayout.astro
│  ├─ pages/
│  │  ├─ index.astro
│  │  ├─ archive.astro
│  │  ├─ sources.astro
│  │  ├─ sources/[sourceId].astro
│  │  ├─ about.astro
│  │  ├─ editorial-policy.astro
│  │  ├─ privacy.astro
│  │  ├─ 404.astro
│  │  ├─ feed.xml.ts
│  │  ├─ daily/[date].astro
│  │  └─ articles/[year]/[month]/[day]/[slug].astro
│  └─ styles/
│     └─ global.css
├─ tests/
│  ├─ fixtures/
│  │  ├─ rss.xml
│  │  ├─ atom.xml
│  │  └─ malformed.xml
│  ├─ test_feed_reader.py
│  ├─ test_deduplication.py
│  ├─ test_translation.py
│  └─ test_content_writer.py
├─ .nvmrc
├─ astro.config.mjs
├─ package.json
├─ pyproject.toml
├─ requirements.lock
├─ README.md
└─ AGENTS.md
```

## 6. 情報源ポリシー

### 6.1 基本方針

- `config/feeds.yml`に明示された公式RSS/Atomだけを読む。
- 各フィードは人間が公式性を確認してから有効化する。
- RSSがないサイトはPhase 1では対象外とする。
- URL先のHTMLを取得して情報を補完してはならない。
- RSS内に含まれるタイトル、概要、公開日時、GUID、リンク、画像情報だけを使う。
- フィード取得のUser-Agentにはサイト名とリポジトリURLを含める。
- 同一ホストへのアクセスは1回のワークフローにつき原則1回とし、短時間の連続アクセスを避ける。

### 6.2 初期フィード候補

以下はPhase 1の初期候補。実装時にHTTPステータス、Content-Type、利用条件を再確認すること。

```yaml
feeds:
  - id: google-ai
    name: Google AI
    url: https://blog.google/technology/ai/rss/
    language: en
    enabled: true
    priority: 100

  - id: hugging-face
    name: Hugging Face Blog
    url: https://huggingface.co/blog/feed.xml
    language: en
    enabled: true
    priority: 90

  - id: github-ai-ml
    name: GitHub AI & ML
    url: https://github.blog/ai-and-ml/feed/
    language: en
    enabled: true
    priority: 80

  - id: nvidia-deep-learning
    name: NVIDIA Deep Learning Blog
    url: https://blogs.nvidia.com/blog/category/deep-learning/feed/
    language: en
    enabled: true
    priority: 70
```

OpenAI、Anthropic、Meta等は、公式RSSまたは公式APIが確認できた場合のみ追加する。ニュース一覧HTMLの解析で代替してはならない。

### 6.3 フィード設定項目

```yaml
id: string
name: string
url: string
language: en
homepage: string | null
enabled: boolean
priority: integer
max_items_per_run: integer
image_policy: rss_only
categories: string[]
```

## 7. RSS取得と正規化

### 7.1 取得処理

- タイムアウト: 接続10秒、読み込み30秒程度
- リトライ: 最大2回、指数バックオフ
- `ETag`と`Last-Modified`が得られる場合は状態を保存し、条件付きGETへ対応する。
- 1フィード失敗しても他フィードの処理は継続する。
- 全フィード取得失敗時はコンテンツを書き換えず、ワークフローを失敗させる。
- 取得結果が空の場合は警告するが、既存コンテンツを削除しない。

### 7.2 使うフィールド

- `title`
- `link`またはGUIDがパーマリンクの場合のGUID
- `id/guid`
- `published`または`updated`
- `summary`または`description`
- `author`（存在する場合）
- `media:thumbnail`
- `media:content`
- `enclosure`
- RSS本文内の`img`（RSSに埋め込まれたHTMLのみ）

### 7.3 サニタイズ

- HTMLはBeautifulSoupでテキスト化する。
- `script`、`style`、iframe、埋め込みコードは完全に破棄する。
- 改行と連続空白を正規化する。
- 元HTMLをMarkdownへそのまま保存しない。
- 外部から受け取った文字列をテンプレートコードとして評価しない。
- 画像URLは`https://`または`http://`だけを許可する。

### 7.4 日付

- 公開日時は元フィードのタイムゾーンを解釈し、内部ではUTC ISO 8601で保存する。
- 表示は`Asia/Tokyo`へ変換する。
- 日次ページの日付は日本時間を基準とする。
- 日付が解釈できない項目は、取得日時を公開日時として偽装せず、`date_status: unknown`として扱う。
- `date_status: unknown`の項目は原則掲載しない。

## 8. 重複排除

### 8.1 判定順

1. 正規化済みcanonical URL
2. GUID/ID
3. `source_id + normalized_title + published_date`のSHA-256

### 8.2 URL正規化

- URLフラグメントを削除
- 一般的なトラッキングパラメータを削除
  - `utm_*`
  - `ref`
  - `source`
  - `campaign`
- ホスト名を小文字化
- 不要な末尾スラッシュを統一
- HTTPからHTTPSへの勝手な書き換えはしない

### 8.3 状態保存

`data/seen.json`へ、最新5000件を上限として次を保存する。

```json
{
  "items": {
    "dedupe-key": {
      "url": "https://example.com/article",
      "source": "google-ai",
      "published_at": "2026-08-03T00:00:00Z",
      "first_seen_at": "2026-08-03T22:17:00Z"
    }
  }
}
```

既存Markdownからも重複キーを復元できるようにし、`seen.json`が壊れても二重掲載を最小化する。

## 9. 翻訳方式

### 9.1 制約

- 外部翻訳API、生成AI APIは使用しない。
- 非公式Google翻訳エンドポイント等へのアクセスは禁止。
- GitHub Actionsランナー内でローカル翻訳モデルを実行する。

### 9.2 初期実装

- Argos Translateの英語→日本語パッケージを使用する。
- モデルはワークフロー実行時に公式パッケージインデックスから取得し、GitHub Actions cacheへ保存する。
- 翻訳処理は`Translator`インターフェースで抽象化し、将来MarianMT等へ差し替え可能にする。
- モデルのライセンスと配布条件をREADMEに記載する。

### 9.3 翻訳対象

- タイトル
- RSSが提供する概要の先頭部分
- 著者名、企業名、製品名、モデル名は原綴りを優先する。
- URL、コード、バージョン番号、固有の製品名は翻訳しない。

### 9.4 失敗時

- タイトルと概要は別々の翻訳単位・品質判定単位として扱う。
- タイトル翻訳の品質不合格または処理失敗時は、不自然な日本語を公開せず原題を主表示する。記事自体は失わない。
- 概要翻訳の品質不合格または処理失敗時は、日本語概要を表示せず「概要の翻訳を掲載できないため、発表内容は公式リンクでご確認ください。」という定型案内へ切り替える。
- 英語全文を日本語ページへ無断でそのまま掲載しない。
- 既存記事は同一`dedupeKey`なら再生成せず、`humanEdited`、`correctionHistory`を含むfrontmatterを保護する。
- 失敗とフォールバックを、配信元ID・`dedupeKey`・対象種別・理由コード・フォールバック結果だけActionsログへ記録する。原文・翻訳文の全文はログへ出さない。

### 9.5 翻訳品質ゲート

品質ゲートは翻訳モデルから独立した`translation_quality.py`の`check_translation_quality(source_text, translated_text, target_type)`で実装し、`QualityGateResult(passed, reasons)`を返す。`target_type`は`title`または`summary`で、主観的な自然さの採点ではなく、誤検知を抑えた保守的な安全検査に限定する。

検査項目は次のとおり。

- 空文字、異常な短さ・長さ、制御文字
- 保護用プレースホルダーの残存
- 原文にある数字、割合、バージョン番号の欠落
- 原文URLの欠落または破損
- 製品名、モデル名、組織名など保護対象の固有名詞の欠落
- 同じ単語・短い語句の不自然な反復
- 日本語がほとんどなく英文が過剰に残る状態
- 記号列だけ、または日本語見出しとして成立しない状態
- 既知の誤訳パターン

理由コードは次を安定した文字列として扱い、frontmatter、テスト、ログから参照できるようにする。

`empty_translation`、`too_short`、`too_long`、`placeholder_remaining`、`missing_number`、`missing_url`、`invalid_url`、`missing_proper_noun`、`excessive_repetition`、`excessive_english`、`symbol_only`、`not_japanese_heading`、`known_mistranslation`、`invalid_characters`、`source_missing`、`translation_failed`

品質ゲート不合格は異常終了ではなく、タイトルまたは概要単位のフォールバックとして処理する。タイトルと概要の片方が不合格でも、もう片方の成功結果は保持する。

### 9.6 オフライン翻訳モデル比較（Phase 2 Issue #16）

翻訳品質の比較は、`scripts/run_translation_benchmark.py`をローカルで明示的に実行する独立処理とする。通常CIと日次workflowは比較モデルを取得せず、既存のArgos翻訳運用にも影響を与えない。

- 実際の公式RSS/Atomから取得した30〜50件のタイトル・概要を`data/translation_benchmark/corpus.jsonl`へ固定する。
- `reference_title_ja`、`reference_summary_ja`、人間採点は空欄または`null`のテンプレートとして保持し、値を自動生成しない。
- Argos、FuguMT、OPUS-MT、M2M100を同じテキスト入力契約で比較し、タイトルと概要を別々に計測する。
- `check_translation_quality`を全候補へ適用し、`translation_fidelity_metrics`で数字、URL、明示した固有名詞の総数・保持数を集計する。
- 推論時間、ピークメモリ、品質ゲート、保持率をJSON/CSV/Markdownへ出力する。未実測値を推測せず`not_measured`として記録する。
- 小さな用語集は`config/translation_glossary.yml`に独立させ、保護する製品名と安定した日本語表記を管理する。
- 公式モデルカード・公式リポジトリを一次情報としてライセンス、商用可否、容量、CPU・メモリ・取得時間・キャッシュ容量、Actions実行方針を`config/translation_benchmark.yml`へ記録する。
- 個別ライセンスが不明、または人間の法務確認が必要な候補は本番候補から除外する。本番採用モデルは比較結果から自動決定しない。
- `--allow-model-download`はローカル専用の明示オプションとし、大型モデルを通常CI・日次workflowで取得しない。
- 既存記事、固定URL、RSS、`data/seen.json`を比較のために再生成・更新しない。

実測フォローアップでは、40件の同一コーパスについて、タイトルと概要を分離した各行の出力をJSON・CSVへ保存し、Markdownに候補別集計を出力する。実行環境、モデルリビジョン、CPU推論時間、ピークRSS、初回取得時間、キャッシュ容量を記録し、候補を実行できない場合は理由を残して計測値を補完しない。取得時間はキャッシュ増分が確認できる場合のアダプタ初期化時間として扱い、ピークRSSは候補ごとに同一プロセス内で観測した累積値であることを結果に明記する。

人間評価用には10〜15件の代表サンプルをA〜Dへ匿名化し、意味の正確さ、日本語の自然さ、見出しの明瞭さ、数字・固有名詞保持、原文にない追加を空欄評価する。モデル対応表は別ファイルに分離し、人間評価前の自動採用判定を行わない。

## 10. 日本語短報の生成

生成AIを使わず、翻訳済み情報を定型フォーマットへ組み込む。

### 10.1 表示例

```text
Google AIは8月3日、「〇〇」を公開しました。公式RSSによると、今回の発表では〇〇が紹介されています。詳細や正確な仕様は、リンク先の公式発表をご確認ください。
```

### 10.2 ルール

- 1項目あたり120〜320日本語文字を目安とする。
- 元記事本文は取得しない。
- RSS概要を丸ごと翻訳・転載しない。
- 入力概要は最大400英語文字、原則1〜2文までに制限する。
- 断定を追加しない。
- 評価、感想、将来予測を自動で付加しない。
- 数値、日付、製品名は原文と照合できる形を維持する。
- 末尾に公式発表へのリンクを置く。
- 自動翻訳であることを記事ページ上にも表示する。

## 11. 個別記事と日次集約

### 11.1 正本と派生ビュー

1ニュースを1つのMarkdownファイルとして `src/content/articles/YYYY-MM-DD/<article-id>.md` に保存し、`articles` コレクションを情報の正本とする。日次ページは `dateJst` で個別記事を集約する派生ビューであり、日次Markdownを正本として保持しない。

SEO上の薄いページ量産は避けつつ、個別ニュースの恒久URL、検索導線、共有単位、修正履歴を持たせる。日次ページには記事本文を複製せず、抜粋・原文タイトル・配信元・個別記事リンクだけを表示する。

### 11.2 決定的なID・URL

`articleId` は `<source-id>-<sha256(dedupeKey)先頭8桁>` とする。公開URLは次の形式で、翻訳タイトルの変更に依存しない。

```text
/articles/YYYY/MM/DD/<articleId>/
```

同じ `dedupeKey` からは常に同じ `articleId` とMarkdownパスを生成する。短い固定IDは衝突を検知し、既存ファイルを上書きしない。

### 11.3 個別記事frontmatter

```yaml
---
articleId: google-ai-4a9b73e7
titleJa: 日本語タイトル
titleOriginal: Original title
description: 個別記事の検索向け説明文。
briefJa: 日本語短報
excerptJa: 日次ページ向けの短い抜粋
publishedAt: 2026-08-03T22:00:00Z
dateJst: 2026-08-04
sourceId: google-ai
sourceName: Google AI
sourceHomepage: https://blog.google/technology/ai/
sourceUrl: https://example.com/official-post
canonicalUrl: https://example.com/official-post
imageUrl: null
imageLicense: null
author: null
translationStatus: complete
titleTranslationStatus: translated
summaryTranslationStatus: translated
titleQualityGate: passed
summaryQualityGate: passed
titleFallbackApplied: false
summaryFallbackApplied: false
titleFallbackReasons: []
summaryFallbackReasons: []
translationFallbackReasons: []
dedupeKey: url:...
fetchedAt: 2026-08-04T22:17:00+09:00
generatedAt: 2026-08-04T22:17:00+09:00
updatedAt: 2026-08-04T22:17:00+09:00
humanEdited: false
correctionHistory: []
noindex: false
---
```

本文は生成せず、frontmatterを個別記事の正本として扱う。Astroの個別記事ページがfrontmatterから日本語短報、原文タイトル、公式リンク、自動収集・自動翻訳の注意書きを一度だけ表示する。`fetchedAt`、`generatedAt`、`updatedAt`、翻訳状態、人間修正フラグ、訂正履歴は後続の透明性・修正運用を阻害しないために保持する。`titleTranslationStatus`と`summaryTranslationStatus`は`translated`、`quality_rejected`、`translation_failed`、`source_missing`を区別し、`titleFallbackApplied`、`summaryFallbackApplied`と理由配列で安全弁の適用結果を保存する。既存記事ではこれらの新フィールドを省略可能とし、従来の`translationStatus`だけでも読み込めるようにする。`author`はRSSに含まれる原文著者として「原文著者」と表示し、AI外電の`NewsArticle.author`には設定しない。

### 11.4 日次ページ

既存の `/daily/YYYY-MM-DD/` URLは維持し、`articles` を `dateJst` でグループ化して静的生成する。日次ページの構造化データは `CollectionPage` + `ItemList` + `BreadcrumbList` とし、各 `ListItem` は個別記事URLを指す。前後の日次ページと同日個別記事への導線を表示する。

### 11.5 新着ゼロの日

- 空の日次ページは作らない。
- 「本日のニュースはありません」という薄いページを量産しない。
- リポジトリへ変更がなければコミットしない。
- トップページには最後に成功した更新日時を表示する。

### 11.6 初回実行

- 過去3日分だけを取得対象とする。
- フィードの全履歴を一括取り込みしない。
- 全フィード合計で最大10件までとする。
- `workflow_dispatch`の入力で`bootstrap_days`を変更できるようにするが、上限7日とする。

### 11.7 外電票と訂正履歴

個別記事のメタデータは再利用可能な`ArticleBulletin.astro`で表示し、記事本文と視覚的に分離する。

- 配信元、原文タイトル、原文公開日時、AI外電取得日時、初回生成日時、最終更新日時を表示する。
- タイトル翻訳状態、概要翻訳状態、フォールバックの有無、人間修正の有無、公式発表リンクを表示する。
- 翻訳の内部理由コードはそのまま表示せず、人間向けの状態名へ変換する。
- `correctionHistory`が空の場合は訂正・更新履歴欄を表示しない。
- 公開対象の履歴レコードは日時と説明だけを表示し、未定義・不正なレコードは表示しない。
- 既存記事frontmatterを一括変更せず、固定URL、`humanEdited`、`correctionHistory`を自動生成で上書きしない。
- 原文著者は記事情報として表示できるが、`NewsArticle.author`には設定しない。

## 12. 画像方針

### 12.1 取得優先順位

1. `media:thumbnail`
2. `media:content`の画像
3. `enclosure`の画像
4. RSS概要内の`img`
5. サイトの既定画像

### 12.2 制約

- RSSに明示的に含まれる画像URLだけを使用する。
- 元記事HTMLから`og:image`を取りに行かない。
- 画像ファイルをリポジトリへコピー保存しない。
- 外部画像が表示不能でもレイアウトが崩れないようにする。
- `loading="lazy"`、width/height、適切なaltを設定する。
- 画像がない場合は軽量なSVG既定画像を使う。
- 出典名と元記事リンクを画像付近に表示する。
- ライセンス情報がRSSに含まれる場合は保存・表示できる設計にする。

## 13. サイトページ

### 13.1 `/`

- SEO向けH1
- 試験運用バナー
- 最新日の個別記事抜粋と個別記事ページへのリンク
- 過去7日分へのリンク
- 情報源一覧への導線
- 最終更新日時

### 13.2 `/daily/YYYY-MM-DD/`

- 日付別ダイジェスト
- パンくず
- 前日/翌日の存在するページへのナビゲーション
- 各ニュースのH2と個別記事リンク
- 抜粋、原文タイトル、配信元、日時、画像、公式リンク（全文は個別ページ）

### 13.3 `/articles/YYYY/MM/DD/<article-id>/`

- 個別ニュースの恒久URL
- 日本語タイトル、短報、原文タイトル、配信元、公開日時、翻訳状態
- `NewsArticle` と `BreadcrumbList` の構造化データ
- 公式発表へのリンク
- 同日の日次ページ、前後記事、配信元ページへの内部リンク
- 自動収集・自動翻訳・定型編集であることの明示

### 13.4 `/archive/`

- 月別グループ
- 日付、見出し、件数、主な配信元
- ページ数が増えたら年別ページへ分割可能な構造

### 13.5 `/sources/`

- 全配信元への入口を維持し、配信元名から`/sources/<sourceId>/`へリンクする。
- 配信元名、公式ホームページ、公式RSS/Atom URL、取得対象の説明、有効/一時停止状態を表示する。
- カテゴリ、画像方針、AI外電の記事数を表示する。

### 13.5.1 `/sources/<sourceId>/`

- `sourceId`から生成する安定URLとし、例として`/sources/openai-news/`を使う。
- 配信元情報、公式サイト、RSS/Atom URL、取得状態、カテゴリ、画像方針、AI外電の記事数を表示する。
- 最新記事一覧は記事カードで表示し、記事カード、外電票、配信元ページを相互にリンクする。
- 掲載記事が2件未満の薄い配信元ページは生成するが、`noindex,nofollow`を付けてsitemapから除外する。
- 2件以上の記事がある配信元ページだけをindex対象とし、sitemapへ収録する。
- `config/feeds.yml`と`src/data/sources.ts`の配信元メタデータはリポジトリ検証で一致を確認する。
- アクセス解析や外部サービスはこの段階で実装しない。

### 13.6 `/about/`

- サイトの目的
- 試験運用中であること
- 自動取得・自動翻訳・定型生成の説明
- スクレイピングをしていないこと
- 誤訳や遅延の可能性
- 公式情報を優先するよう促す文
- 著作権・画像の取り扱い方針
- 編集・訂正ポリシーの概要と `/editorial-policy/` への導線
- 運営名「外電通信」と、外電通信が個人事業主・山田の事業の一つであること
- 連絡先は初期段階ではGitHub Issuesへのリンクでもよい

### 13.7 `/privacy/`

- 運営名「外電通信」と実際の運営主体の記載
- 初期段階でCookie、広告、個人情報収集を行わないこと
- Cloudflareの配信基盤を使用すること
- Analyticsを導入した場合は改訂すること

### 13.8 運営表記

- 運営名と運営主体の説明は共通設定へ定数化する。
- フッターは「運営: 外電通信」と簡潔に表示する。
- 個別記事画面では個人名を常時前面に出さない。
- 外電通信を法人、報道機関、既存通信社の系列・提携先と誤認させる表現を使わない。
- 住所・電話番号は新規公開しない。

### 13.9 `/editorial-policy/`

- 編集・訂正ポリシーは独立した安定URLを正本とし、固有のtitle、description、canonicalを設定する。
- Aboutの`#editorial-policy`には概要と独立ページへの導線だけを置く。
- 公式RSS/Atomのみを掲載対象とし、元記事HTMLのスクレイピングを行わないことを説明する。
- 原文タイトル、配信元、公式発表へのリンクを各記事で明示する方針を説明する。
- サイトRSSの利用条件と日次RSSを提供しない方針を掲載する。
- 自動収集・自動翻訳・定型編集を使い、原文にない評価、影響、推測、将来予測をニュース短報へ追加しない。
- 翻訳品質不合格時は原題表示または公式リンク案内へフォールバックし、不自然な訳文を公開しない。
- 誤りの連絡は記事URL、公式発表URL、誤りの箇所を添えたGitHub Issuesで受け付ける。
- 意味、数字、固有名詞、提供条件に関わる訂正を優先し、既存記事の固定URLと人手による訂正を自動更新で保護する。
- 公式発表の更新・撤回はRSS/Atomと公式発表で確認できる範囲を人手で見直し、自動処理だけで推測しない。
- 現在のニュース短報と将来の人間確認済み解説・コラムをカテゴリ・URL・責任範囲で分離する。
- 訂正履歴の個別記事表示と外電票は後続の#21-Bで整備する。

## 14. SEO要件

SEOは後付けではなく、初期実装の受け入れ条件とする。ただし、技術的SEOを整えても検索順位を保証するものではない。自動翻訳サイトであるため、薄いページや重複ページを増やさず、情報源の明示と読みやすさを優先する。

### 14.1 キーワードと命名

ブランド名だけでなく検索意図が伝わる語を使う。

- サイト名: AI外電
- デフォルトtitle: `海外AIニュース速報｜AI外電`
- H1: `海外AI公式発表を日本語で毎日ダイジェスト`
- 説明文には自然な範囲で以下を含める。
  - 海外AIニュース
  - AI最新情報
  - 生成AI
  - 公式発表
  - 日本語
  - Google AI
  - Hugging Face
  - GitHub
  - NVIDIA

キーワードの不自然な羅列は禁止。

### 14.2 ページtitle

- トップ: `海外AIニュース速報｜AI外電`
- 日次: `海外AIニュース YYYY年M月D日｜主要見出し｜AI外電`
- 個別記事: `<日本語タイトル>｜AI外電`
- アーカイブ: `海外AIニュース一覧・過去記事｜AI外電`
- 情報源: `海外AI公式ニュースの情報源一覧｜AI外電`
- About: `AI外電について｜海外AIニュース自動ダイジェスト`
- 編集・訂正ポリシー: `編集・訂正ポリシー｜AI外電`

- 主要見出しを入れる場合もtitle全体を過剰に長くしない。
- 各ページのtitleは一意にする。

### 14.3 メタ情報

各ページに以下を設定する。

- unique `title`
- unique `meta description`
- canonical URL
- `lang="ja"`
- Open Graph
- X/Twitter Card互換メタ
- `datePublished` / `dateModified`相当の情報
- favicon

日次descriptionと個別記事descriptionは、表示内容と一致する自然な文章で作る。単純なキーワード列挙や、途中で単語を切る不自然な切り詰めを避ける。

### 14.4 canonicalと環境分離

- 本番URLは環境変数`SITE_URL`で管理する。
- 初期値はCloudflare Pagesの本番`pages.dev` URLを設定する。
- URLをコードへハードコードしない。
- `main`以外のCloudflare Preview Deploymentは`noindex,nofollow`にする。
- Preview URLをcanonicalとして出力しない。
- 独自ドメイン取得後は`SITE_URL`を変更するだけでcanonical、sitemap、RSSが切り替わる構造にする。

### 14.5 構造化データ

- トップ: `WebSite`
- 日次ページ: `CollectionPage` + `ItemList`
- 個別記事: `NewsArticle` + `BreadcrumbList`（AI外電の短報ページであることを明示）
- パンくず: `BreadcrumbList`
- 運営主体が確定していない段階で架空の`Organization`を設定しない。
- 実際の表示内容と一致しない`NewsArticle`を乱用しない。
- 元記事を自サイトの記事として偽装する構造化データは禁止。

### 14.6 サイトマップ等

- `@astrojs/sitemap`で本番URL基準の`/sitemap-index.xml`または`/sitemap.xml`を生成する。
- `robots.txt`からサイトマップを参照する。
- サイト自身のRSS `/feed.xml`を生成する。
- `/feed.xml`は個別記事単位の正式なサイトRSSとし、各itemのlink/GUIDを絶対固定個別記事URLで一致させる。descriptionはAI外電の日本語短報だけを使い、元RSS本文、元記事本文、画像、長い逐語翻訳を含めない。
- 各itemは配信元、原文公開日時（`pubDate`）、AI外電の更新日時（Atom名前空間の`updated`）、翻訳状態を保持し、sitemapの個別記事URLと一致することを検証する。
- 日次単位の `/daily/feed.xml` は当面生成せず、RSS利用条件と方針を`/editorial-policy/`に掲載する。
- 空ページ、テストfixture、内部JSON、Preview環境をサイトマップへ入れない。
- `lastmod`を適切に出力する。

### 14.7 内部リンク

- トップから最新の個別記事とアーカイブへリンク
- 日次ページから前後の日次ページへリンク
- 配信元名から`/sources/<sourceId>/`の安定URLへリンク
- 個別記事から同日の日次ページ、前後記事、公式発表へリンク
- 配信元ページから掲載記事と公式発表へリンク
- パンくずを表示
- Aboutとフッターから`/editorial-policy/`へリンクする
- 孤立ページを作らない

### 14.8 コンテンツ品質

- 1項目だけの短いページを大量生成しない。
- 同一タイトルやほぼ同一descriptionを作らない。
- 原文タイトルと日本語タイトルを併記し、意味確認を可能にする。
- 配信元と公開日を明示する。
- 自動翻訳の限界を隠さない。
- 公式リンクへの導線を明確にする。
- 取得失敗による壊れた文章は公開しない。

### 14.9 パフォーマンスとアクセシビリティ

目標:

- Lighthouse Performance 90以上
- Accessibility 90以上
- Best Practices 90以上
- SEO 95以上

要件:

- JavaScriptなしでも記事が読める。
- レスポンシブ対応。
- セマンティックHTML。
- 色だけに依存しない表示。
- キーボード操作可能。
- CLSを抑えるため画像サイズを指定。
- Webフォントは原則使わず、システムフォントを優先。

### 14.10 将来の独自ドメイン移行

- ドメイン依存値は`SITE_URL`へ集約する。
- 独自ドメイン移行時にcanonicalを新ドメインへ変更する。
- 旧`pages.dev`から新ドメインへの301転送を将来タスクとして残す。
- Search Console登録は独自ドメイン取得後を推奨するが、試験中に`pages.dev`を登録してもよい。

## 15. GitHub Actions

### 15.1 `daily-news.yml`

トリガー:

```yaml
on:
  schedule:
    - cron: '17 22 * * *' # 日本時間 07:17
  workflow_dispatch:
    inputs:
      bootstrap_days:
        description: '初回または再取得する日数（最大7）'
        required: false
        default: '3'
```

0分付近の混雑を避けるため、07:17 JSTを採用する。時刻厳守を要件にしない。

権限:

```yaml
permissions:
  contents: write
```

処理:

1. checkout
2. Python 3.12セットアップ
3. pipキャッシュ
4. Argosモデルキャッシュ
5. Python依存インストール
6. `python scripts/update_news.py`
7. Pythonテスト
8. Nodeセットアップ
9. `npm ci`
10. `npm run check`
11. `npm run build`
12. 変更判定
13. 変更がある場合のみコミット・push

コミット例:

```text
chore(news): update daily AI digest for 2026-08-04
```

コミッター:

```text
github-actions[bot]
41898282+github-actions[bot]@users.noreply.github.com
```

安全要件:

- `git add -A`の前に対象差分を表示する。
- 自動生成対象外のソースコード差分が存在する場合はpushせず失敗させる。
- 自動コミット対象は`src/content/articles/**`と`data/seen.json`だけ。
- push前に`git pull --rebase`を行う。
- 同時実行を防ぐconcurrencyを設定する。

```yaml
concurrency:
  group: daily-news
  cancel-in-progress: false
```

### 15.2 `ci.yml`

対象:

- pull_request
- mainへのpush

処理:

- Python lint/test
- Astro check
- Astro build
- 生成済みコンテンツのschema検証
- リンクの最低限の形式チェック

CIでは外部RSSへアクセスしない。fixtureだけでテストする。

## 16. Cloudflare Pages

### 16.1 デプロイ方式

Cloudflare PagesのGit Integrationを使用する。

- Repository: `yo4e/AI-gaiden`
- Production branch: `main`
- Framework preset: Astro
- Build command: `npm ci && npm run build`
- Build output directory: `dist`
- Root directory: `/`
- Node version: `.nvmrc`で固定。推奨Node 22。

GitHub Actionsが新着コンテンツをmainへpushすると、Cloudflare Pagesが自動ビルド・自動デプロイする。

Phase 1ではWranglerによる直接デプロイを使用しない。Cloudflare APIトークンもGitHub Secretsへ登録しない。

### 16.2 初期URL

- Cloudflare Pages作成時に割り当てられる`*.pages.dev`を使用する。
- 実際のURLが決まったらCloudflareの環境変数`SITE_URL`へ設定する。
- `SITE_URL`未設定の本番ビルドは失敗させる。
- ローカル開発だけは`http://localhost:4321`を許可する。

### 16.3 Preview環境

- PR/ブランチのPreview Deploymentを有効にする。
- `CF_PAGES_BRANCH != main`の場合は全ページへ`noindex,nofollow`を出力する。
- Previewのcanonicalは本番URLへ向けるか、canonical自体を出さない。実装方針を統一する。
- Previewをサイトマップへ含めない。

### 16.4 手動設定手順

実装後、運営者がCloudflare Dashboardで行う。

1. Workers & Pagesを開く。
2. Create application → Pages → Connect to Git。
3. GitHubの`yo4e/AI-gaiden`だけにアクセスを許可する。
4. Production branchを`main`にする。
5. Framework presetをAstroにする。
6. Build commandを`npm ci && npm run build`にする。
7. Output directoryを`dist`にする。
8. 初回デプロイ後、発行された`pages.dev` URLを`SITE_URL`へ設定する。
9. 再デプロイし、canonical、sitemap、RSS、robots.txtを確認する。

参考:

- https://developers.cloudflare.com/pages/get-started/git-integration/
- https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/
- https://developers.cloudflare.com/pages/framework-guides/deploy-anything/

## 17. セキュリティ

- フィード内HTMLをそのまま描画しない。
- YAML/JSON入力をコードとして実行しない。
- URL schemeを検証する。
- リンクには`rel="noopener noreferrer"`を付ける。
- Actionsの権限は必要最小限とする。
- Phase 1では秘密情報を必要としない設計にする。
- Dependabotまたは定期的な依存更新を導入する。
- ログへフィード全文を出さない。
- 取得した外部文字列をコミットメッセージへ入れない。

## 18. ログと障害時の挙動

### 18.1 ログ

各実行で次を出力する。

- 取得フィード数
- 成功/失敗フィード
- 取得項目数
- 新着数
- 重複除外数
- 翻訳成功/失敗数
- 生成ページ
- コミット有無

### 18.2 失敗ポリシー

- 1フィード失敗: 警告し継続
- 全フィード失敗: 失敗終了、既存ファイル変更なし
- 翻訳モデル取得失敗: 失敗終了、既存ファイル変更なし
- schema違反: 失敗終了、pushなし
- Astro build失敗: 失敗終了、pushなし
- push競合: 自動上書きせず失敗終了

処理は一時ディレクトリで生成し、全検証成功後に本番ファイルへ置き換える。途中失敗で壊れたMarkdownを残さない。

## 19. テスト要件

### 19.1 単体テスト

- RSS 2.0解析
- Atom解析
- GUIDだけ存在する項目
- 日付形式の差異
- malformed feed
- HTML除去
- URL正規化
- 重複排除
- 画像優先順位
- 翻訳失敗
- 翻訳品質ゲート、理由コード、タイトル/概要別フォールバック
- 翻訳比較コーパスの件数、参考訳・人間採点の空欄、候補メタデータ、用語集、数字/URL/固有名詞保持率
- 比較runnerのタイトル/概要分離、候補共通品質ゲート、JSON/CSV/Markdown出力、モデル未取得時の扱い
- 文字数制限
- frontmatter生成

### 19.2 結合テスト

fixtureから個別記事Markdownを生成し、日次集約ページと個別記事ページを含むAstro buildが成功すること。

### 19.3 スナップショット

生成Markdownと主要HTMLの意図しない変化を検知できるテストを用意してよい。ただし更新が煩雑になりすぎない範囲とする。

## 20. デザイン要件

- ニュースサイトとして落ち着いた、読みやすいデザイン。
- 白または明るい背景を基本とする。
- ブランド名「AI外電」を明確に表示。
- 海外通信・外電らしい簡潔さは出してよいが、新聞社を装わない。
- カードを過剰に装飾しない。
- モバイルを優先する。
- 本文幅は読みやすい範囲に制限する。
- 画像なしの記事も自然に並ぶレイアウトにする。
- 試験運用バナーは全ページ共通コンポーネントにする。

## 21. READMEに記載する事項

- プロジェクト概要
- 現在は試験運用であること
- AI API不使用
- RSS限定・スクレイピング不使用
- 技術構成
- ローカル起動方法
- ニュース更新コマンド
- テスト方法
- Cloudflare Pages設定
- 自動生成ファイルを手動編集しない注意
- 翻訳モデルとライセンス
- オフライン翻訳比較のコーパス、候補メタデータ、実行条件、結果出力、未計測値の扱い
- Phase 2としてBluesky投稿を予定していること

## 22. Codex実装順序

1. Astroプロジェクト初期化
2. 共通レイアウト、デザイン、試験運用バナー
3. 仮データで全ページとSEOを実装
4. RSS設定とfixture
5. PythonのRSS解析・正規化・重複排除
6. Argos翻訳アダプタ
7. 短報・個別記事Markdown生成と日次集約
8. ActionsのCI
9. Actionsの日次更新
10. Cloudflare Pages向けビルド確認
11. READMEと運用手順
12. 全受け入れ条件の確認

Phase 2では、既存のArgos日次運用を変更せず、`scripts/run_translation_benchmark.py`によるローカル比較を追加できる。比較で得た数値だけでは本番モデルを切り替えず、人間による自然さ・参考訳・ライセンス・Actions実行可否の確認を経て別途判断する。

## 23. 受け入れ条件

以下をすべて満たしたらPhase 1完了とする。

- [ ] `npm ci && npm run build`が成功する。
- [ ] `pytest`が成功する。
- [ ] `ruff check .`が成功する。
- [ ] 全ページに「試験運用中」が表示される。
- [ ] HTMLスクレイピングを行うコードが存在しない。
- [ ] AI/翻訳APIキーを要求しない。
- [ ] fixtureから日本語個別記事と日次集約ページを生成できる。
- [ ] 既存日次Markdownの全記事が個別Markdownへ移行されている。
- [ ] 同じ`dedupeKey`から記事ID・固定URLが再現される。
- [ ] 既存の日次URLが利用でき、RSSとsitemapが個別記事URLを指す。
- [ ] RSSにない画像を記事ページから探しに行かない。
- [ ] 新着ゼロの日に空ページを生成しない。
- [ ] 同一記事を二重掲載しない。
- [ ] 全フィード失敗時に既存コンテンツを壊さない。
- [ ] title、description、canonical、OG情報がページごとに正しく出る。
- [ ] 本番sitemap、robots.txt、サイトRSSが生成される。
- [ ] Preview環境がnoindexになる。
- [ ] 日次ページが`CollectionPage`/`ItemList`の構造化データを持つ。
- [ ] Lighthouse SEO 95以上を目標として大きな問題がない。
- [ ] GitHub Actionsを手動実行できる。
- [ ] 新着がある場合だけ自動コミットする。
- [ ] mainへのpushでCloudflare Pagesがデプロイできる構成になっている。
- [ ] WranglerとCloudflare APIトークンを使用していない。
- [ ] Bluesky関連コードはまだ実装されていない。

## 24. Phase 2候補

Phase 1の運用確認後に別設計で実施する。

- Bluesky APIによる定時告知
- 投稿済みIDの保存と二重投稿防止
- 日次ダイジェストURLと主要見出しの投稿
- 投稿失敗時の再実行
- カスタムドメイン
- Search Console
- Cloudflare Web Analytics
- フィード追加
- 人間による注目記事への追記欄
- 本番翻訳モデルの選定と切り替え（オフライン比較基盤はIssue #16で追加）

## 25. 実装上の最重要原則

1. 公式RSS以外を勝手に巡回しない。
2. 取得できない情報を推測で補わない。
3. 自動翻訳であることを隠さない。
4. 壊れたデータを公開しない。
5. SEO目的で薄いページを量産しない。
6. 元記事と配信元を必ず明示する。
7. Phase 1を小さく、再現可能で、無人運転しても安全な構成に保つ。
