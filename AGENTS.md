# Codex作業指示

このリポジトリでは、[`docs/IMPLEMENTATION_SPEC.md`](docs/IMPLEMENTATION_SPEC.md)を唯一の実装仕様として扱ってください。

## 目的

「海外AIニュース速報｜AI外電」のMVPを、設計書に従って一気に実装してください。

完成地点は、公式RSS/Atomの取得から日本語日刊ダイジェストの静的生成、GitHub Actionsによる定時更新、Cloudflare Pagesへの自動デプロイまでです。

Bluesky投稿は今回の対象外です。

## 絶対条件

- 公式RSS/Atomだけを取得する
- 記事ページHTMLをスクレイピングしない
- `og:image`を取りに行かない
- 外部AI API、翻訳API、要約APIを使わない
- 日本語化はローカル翻訳モデルで行う
- フィードにない事実を追加しない
- 全ページに「試験運用中」と自動収集・自動翻訳の説明を表示する
- SEOをMVPの必須要件として実装する
- Cloudflare PagesへWranglerでDirect Uploadする
- 当面は`pages.dev` URLを使い、独自ドメインを前提にしない
- SecretやTokenをコミットしない
- Bluesky関連コードを実装しない

## SEO優先事項

- サイト名：`AI外電`
- SEOタイトル：`海外AIニュース速報｜AI外電`
- H1：`海外AI公式発表を日本語で毎日ダイジェスト`
- 個別title、description、canonical、OGメタ
- JSON-LD
- sitemap.xml
- robots.txt
- 自サイトRSS/Atom
- 日付アーカイブと内部リンク
- 新着0件の薄いページを作らない
- 同一ニュースを再掲載しない
- Lighthouse SEO 95以上を目標にする

## 推奨作業順

1. Astroの静的サイトを初期化
2. サンプルJSONでトップ・日刊・固定ページを完成
3. RSS取得と正規化
4. 重複排除とAI関連度フィルタ
5. ローカル翻訳
6. 画像抽出
7. SEOと構造化データ
8. pytestとビルドテスト
9. GitHub Actions
10. Cloudflare Pagesデプロイ
11. READMEへセットアップ・実行・障害対応を追記

## 実装時の判断

設計書に書かれていない細部は、安全性、再現性、保守性、SEO、実行コストの順で判断してください。

公式RSSが確認できない企業は無理に追加せず、ソース設定から除外してください。スクレイピングへの切り替えは禁止です。

Cloudflareのアカウント固有値やSecretがないためデプロイ確認まで到達できない場合も、ローカルビルドとActionsワークフローを完成させ、ユーザーが必要な値を登録すれば`workflow_dispatch`で公開できる状態にしてください。

## 完了報告

完了時は次を報告してください。

- 実装した機能
- 採用した公式フィード
- ローカル実行方法
- テスト結果
- Cloudflare側でユーザーが行う操作
- GitHub Secrets / Variables一覧
- 公開後に確認すべきSEO項目
- Phase 2へ残したもの
