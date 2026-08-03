# 海外AIニュース速報｜AI外電

海外のAI関連企業・開発者組織が公式に配信するRSS/Atomだけを収集し、日本語の短い日刊ダイジェストとして公開する静的サイトです。

> **試験運用中**  
> 本サイトの記事は、公式フィードを基に自動収集・自動翻訳・定型編集を行います。翻訳や要約に誤りが含まれる可能性があるため、重要な情報は必ずリンク先の公式発表をご確認ください。

外部AI API・翻訳API、記事ページのHTMLスクレイピング、RSSにない `og:image` の取得は行いません。英日翻訳はGitHub Actionsランナー内のArgos Translateで完結します。Bluesky連携はPhase 2の候補で、現在のコードには含まれません。

## 技術構成

- Astro 7 + TypeScript（静的HTML）
- Python 3.12（RSS取得、正規化、重複排除、翻訳、Markdown生成）
- Argos Translate（ローカル英日翻訳）
- GitHub Actions（CI、毎日07:17 JST頃の更新）
- Cloudflare Pages Git Integration（mainの更新を自動デプロイ）

生成コンテンツは `src/content/daily/YYYY-MM-DD.md`、重複判定状態は `data/seen.json` に保存します。この2箇所は日次ワークフローが管理するため、原則として手動編集しないでください。

## 取得対象の公式フィード

2026年8月3日にHTTPステータスとRSS/XMLのContent-Typeを再確認した初期フィードです。

| 配信元 | 公式フィード | 用途 |
| --- | --- | --- |
| Google AI | <https://blog.google/technology/ai/rss/> | Google公式ブログのAI発表 |
| Hugging Face Blog | <https://huggingface.co/blog/feed.xml> | モデル、データセット、研究・開発情報 |
| GitHub AI & ML | <https://github.blog/ai-and-ml/feed/> | 開発者向けAI・機械学習情報 |
| NVIDIA Deep Learning Blog | <https://blogs.nvidia.com/blog/category/deep-learning/feed/> | ディープラーニング関連情報 |

設定は `config/feeds.yml` にあります。新しい配信元は公式RSS/Atomであることを人間が確認したうえで追加し、表示用の `src/data/sources.ts` も同じIDで更新してください。RSSがないサイトをHTML解析で代替してはいけません。

## ローカル実行

Node.js 22とPython 3.12が必要です。

```bash
npm ci
npm run dev
```

Python環境とテスト:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
ruff check .
pytest
python scripts/validate_repository.py
```

Astroの型検証と本番ビルド:

```bash
npm run check
SITE_URL=https://example.pages.dev npm run build
```

ローカル開発では `SITE_URL` を省略すると `http://localhost:4321` を使います。Cloudflare Pages上では `SITE_URL` が未設定だと意図的にビルドを失敗させます。

## ニュース更新

初回だけArgos公式パッケージインデックスから英日モデルを取得します。以降はローカルのモデルを再利用します。

```bash
export ARGOS_PACKAGES_DIR="$PWD/.cache/argos/packages"
export ARGOS_AUTO_INSTALL=1
python scripts/update_news.py --bootstrap-days 3
```

`--bootstrap-days` は1〜7日です。初回は全フィード合計10件まで取り込みます。新着が0件なら日次ページと `seen.json` を変更しません。1フィードだけ失敗した場合は他を継続し、全フィードが失敗した場合や翻訳モデルを準備できない場合は既存コンテンツを変更せず失敗します。

フィード取得の条件付きGET状態は `.cache/feed-state.json` に保存され、日次Actionsでは専用cacheから前回値を復元します。Gitには含めません。元記事HTMLへのリクエストを行うコードはありません。

### 翻訳モデルとライセンス

[Argos Translate](https://github.com/argosopentech/argos-translate) のプログラム本体と公式パッケージインデックスはMITまたはCC0のデュアルライセンスです。日次処理は公式インデックスの `en → ja` パッケージをダウンロードし、外部翻訳APIへテキストを送信しません。

英日モデル `translate-en_ja-1_1` は、2026年8月時点の配布パッケージ内READMEにモデル個別のライセンス表記がありません。モデルはリポジトリや公開成果物へ再配布せず、Actionsキャッシュ内で実行時利用だけを行います。本番運用を拡大する前に、公式側の最新メタデータと配布条件を再確認してください。

## GitHub Actions

### CI (`.github/workflows/ci.yml`)

Pull Requestとmainへのpushで次を行います。外部RSSにはアクセスせず、テストfixtureだけを使用します。

1. `ruff check .`
2. `pytest`
3. 生成済みfrontmatter・設定・URL形式の検証
4. `npm ci`
5. `npm run check`
6. `npm run build`

### 日次更新 (`.github/workflows/daily-news.yml`)

- 毎日22:17 UTC（07:17 JST頃）と `workflow_dispatch` で実行
- `contents: write` だけを付与し、Secretsや外部APIキーは不使用
- Argos英日モデルをActions cacheへ保存
- PythonテストとAstro buildが成功した後だけ処理を継続
- 変更対象が `src/content/daily/*.md` と `data/seen.json` 以外なら失敗
- ステージ済み差分がある場合だけbot名義でmainへ通常push（force pushなし）
- 新着0件ならコミットしない

Repositoryの **Settings → Actions → General → Workflow permissions** で、ActionsがmainへコミットできるようにRead and write permissionsを許可してください。mainのbranch protection/rulesetを使う場合は、日次ワークフローの通常pushを許可するか、別途レビュー運用へ変更してください。

推奨Repository Variable:

| 名前 | 値 | 必須性 |
| --- | --- | --- |
| `SITE_URL` | `https://<実際のプロジェクト名>.pages.dev` | 日次ビルドのcanonical検証用。設定を推奨 |

Repository Secretsは不要です。Cloudflare API Tokenも登録しないでください。

## Cloudflare Pages設定

WranglerやDirect Uploadは使わず、Cloudflare DashboardでGit Integrationを設定します。

1. **Workers & Pages → Create application → Pages → Connect to Git** を開く。
2. GitHubの `yo4e/AI-gaiden` だけへのアクセスを許可する。
3. Production branchを `main` にする。
4. Framework presetを `Astro` にする。
5. Build commandを `npm ci && npm run build` にする。
6. Build output directoryを `dist`、Root directoryを `/` にする。
7. 初回に割り当てられた `pages.dev` URLを、ProductionとPreview両方の環境変数 `SITE_URL` に設定する。
8. 再デプロイする。

Cloudflareが自動で設定する `CF_PAGES_BRANCH` が `main` 以外の場合、全ページは `noindex,nofollow` になり、Previewではsitemapも生成しません。canonicalは `SITE_URL` の本番URLを指します。

GitHub Actionsが生成コンテンツをmainへpushすると、Cloudflare PagesがGit更新を検知して再ビルド・再デプロイします。Cloudflare API Token、Wrangler、Pages Functionsは不要です。

## 障害対応

- **全フィード失敗**: Actionsログの配信元別エラーを確認します。既存Markdownと `seen.json` は変更されません。
- **Argosモデル取得失敗**: Actions cacheを削除して手動再実行します。公式パッケージインデックスの障害中は待機し、外部翻訳APIへ切り替えません。
- **schema / Astro build失敗**: 自動pushされません。生成frontmatterとテスト結果を確認します。
- **push拒否**: mainのrulesetとActionsのWorkflow permissionsを確認します。force pushで回避しません。
- **外部画像切れ**: RSS URLを保存しているだけなので、記事本文は既定画像の背景とaltで引き続き読めます。記事HTMLから代替画像を探しません。

## 公開後のSEO確認

- 各ページのtitle、description、canonical、OGメタが一意で本番URLを指すこと
- `/robots.txt` が `/sitemap-index.xml` を参照すること
- `/feed.xml` が本番URLで読めること
- 日次ページに `CollectionPage`、`ItemList`、`BreadcrumbList` のJSON-LDがあること
- Preview Deploymentが `noindex,nofollow` であること
- 404、空の日次ページ、重複ニュースがインデックス対象に入っていないこと
- LighthouseでPerformance 90、Accessibility 90、Best Practices 90、SEO 95以上を目標に確認すること

## Phase 2候補

Blueskyへの日次告知、投稿済みID管理、カスタムドメイン、Search Console、Cloudflare Web Analytics、公式フィード追加、人間による追記欄、翻訳モデル品質比較はPhase 2へ残しています。

詳細仕様は [`docs/IMPLEMENTATION_SPEC.md`](docs/IMPLEMENTATION_SPEC.md)、作業規則は [`AGENTS.md`](AGENTS.md) を参照してください。
