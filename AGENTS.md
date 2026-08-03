# Codex作業指示

このリポジトリでは、[`docs/IMPLEMENTATION_SPEC.md`](docs/IMPLEMENTATION_SPEC.md)を唯一の実装仕様として扱ってください。

## 目的

「海外AIニュース速報｜AI外電」のMVPを、設計書に従って一気に実装してください。

完成地点は、公式RSS/Atomの取得、日本語日刊ダイジェストの静的生成、GitHub Actionsによる定時更新、mainへの自動コミット、Cloudflare PagesのGit連携による自動デプロイまでです。

Bluesky投稿は今回の対象外です。

## 絶対条件

- 公式RSS/Atomだけを取得する。
- 記事ページHTMLをスクレイピングしない。
- `og:image`を取りに行かない。
- 外部AI API、翻訳API、要約APIを使わない。
- 日本語化はGitHub Actions内のローカル翻訳モデルで行う。
- フィードにない事実を追加しない。
- 全ページに「試験運用中」と自動収集・自動翻訳の説明を表示する。
- SEOをMVPの必須要件として実装する。
- 新着がある場合だけ生成コンテンツをmainへ自動コミットする。
- Cloudflare PagesはGitHubリポジトリとのGit Integrationでデプロイする。
- Wrangler、Cloudflare API Token、Direct Uploadは使わない。
- 当面は`pages.dev` URLを使い、独自ドメインを前提にしない。
- SecretやTokenをコミットしない。
- Bluesky関連コードを実装しない。

## SEO優先事項

- サイト名: `AI外電`
- SEOタイトル: `海外AIニュース速報｜AI外電`
- H1: `海外AI公式発表を日本語で毎日ダイジェスト`
- ページごとに一意なtitle、description、canonical、OGメタ
- `CollectionPage`、`ItemList`、`BreadcrumbList`等の適切なJSON-LD
- sitemap.xml
- robots.txt
- 自サイトRSS/Atom
- 日付アーカイブと内部リンク
- Cloudflare Preview環境の`noindex,nofollow`
- 新着0件の薄いページを作らない
- 同一ニュースを再掲載しない
- 原文タイトル、配信元、公式リンクを必ず表示する
- Lighthouse SEO 95以上を目標にする

## 推奨作業順

1. Astroの静的サイトを初期化する。
2. サンプルデータでトップ、日次、アーカイブ、情報源、About、Privacy、404ページを完成させる。
3. 共通レイアウトと試験運用バナーを実装する。
4. RSS取得、正規化、サニタイズを実装する。
5. 重複排除を実装する。
6. Argos Translateの英日翻訳アダプタを実装する。
7. 日本語短報と日次Markdown生成を実装する。
8. RSS画像だけを使う画像抽出を実装する。
9. SEO、構造化データ、サイトマップ、サイトRSSを実装する。
10. pytest、ruff、Astro check/buildを通す。
11. `ci.yml`と`daily-news.yml`を実装する。
12. READMEへローカル実行、Cloudflare設定、障害対応を追記する。

## GitHub Actionsの方針

- 日次実行は日本時間07:17相当を標準とする。
- `workflow_dispatch`で手動実行可能にする。
- 自動コミット対象は原則`src/content/daily/`と`data/seen.json`だけに限定する。
- PythonテストとAstro buildが成功するまでpushしない。
- 新着がない場合はコミットしない。
- 全フィード失敗時は既存コンテンツを変更しない。
- GitHub Actionsの`contents: write`以外に不要な権限を与えない。

## Cloudflare Pagesの前提

CodexはCloudflareアカウントへアクセスできなくてもよい。リポジトリ側を次の設定で接続可能な状態にしてください。

- Production branch: `main`
- Framework preset: Astro
- Build command: `npm ci && npm run build`
- Output directory: `dist`
- Root directory: `/`
- 本番環境変数: `SITE_URL=https://<実際のプロジェクト名>.pages.dev`

GitHub Actionsがmainへ生成コンテンツをpushすると、Cloudflare Pages側のGit Integrationが自動で再ビルド・再デプロイする構成です。

Preview Deploymentでは`CF_PAGES_BRANCH`等を使い、`main`以外を`noindex,nofollow`にしてください。

## 実装時の判断

設計書に書かれていない細部は、安全性、再現性、保守性、SEO、実行コストの順で判断してください。

公式RSSが確認できない企業は無理に追加せず、ソース設定から除外してください。スクレイピングへの切り替えは禁止です。

自動翻訳結果が壊れている場合は公開せず、ログに理由を残してください。SEO目的で低品質なページを生成しないでください。

## 完了報告

完了時は次を報告してください。

- 実装した機能
- 採用した公式フィード
- ローカル実行方法
- テスト結果
- GitHub Actionsの動作
- Cloudflare側でユーザーが行う操作
- 必要なRepository Settings / Variables一覧
- 公開後に確認すべきSEO項目
- Phase 2へ残したもの
