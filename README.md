# 海外AIニュース速報｜AI外電

海外のAI関連企業・開発者組織が公式に配信するRSS/Atomフィードを収集し、日本語の短い日刊ダイジェストとして公開する自動運用サイトです。

> **試験運用中**  
> 本サイトの記事は、公式フィードを基に自動収集・自動翻訳・定型編集を行います。翻訳や要約に誤りが含まれる可能性があるため、重要な情報は必ずリンク先の公式発表をご確認ください。

## MVPの範囲

- 公式RSS/Atomフィードのみを取得
- 記事ページHTMLのスクレイピングは行わない
- 外部AI API・翻訳APIは使用しない
- 英語タイトルとフィード概要をローカル翻訳モデルで日本語化
- 日付別のニュースダイジェストを静的生成
- SEOを意識したメタ情報・構造化データ・サイトマップを生成
- GitHub Actionsで毎日更新し、新着がある場合だけmainへコミット
- Cloudflare PagesのGit Integrationで自動デプロイ
- 当面はCloudflareの`*.pages.dev` URLで運用

Blueskyへの自動告知は次のフェーズで実装します。

## 実装資料

- 詳細設計: [`docs/IMPLEMENTATION_SPEC.md`](docs/IMPLEMENTATION_SPEC.md)
- Codex向け作業指示: [`AGENTS.md`](AGENTS.md)

## Cloudflare Pagesの予定設定

- Production branch: `main`
- Framework preset: Astro
- Build command: `npm ci && npm run build`
- Output directory: `dist`
- Root directory: `/`
- Environment variable: `SITE_URL=https://<project-name>.pages.dev`

Phase 1ではWrangler、Cloudflare API Token、Direct Uploadを使用しません。GitHubへのpushをCloudflare Pagesが検知してビルド・公開します。
