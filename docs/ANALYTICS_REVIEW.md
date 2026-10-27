# 解析とプライバシー説明の確認（Issue #43）

## 2026-10-27の確認結果

本人がログイン済みブラウザーの利用を許可した後、11:01–11:07 JSTにCloudflare管理画面と実配信のDOMを読み取り確認しました。設定変更、権限追加、デプロイ、新しい計測の有効化はしていません。

| 確認対象                     | 実際の状態                                                                                                                                                                                                         |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Pagesプロジェクト            | `ai-gaiden`、リポジトリ `yo4e/AI-gaiden`、本番 `main`、ドメイン `ai.gaiden.news` / `ai-gaiden.pages.dev`                                                                                                           |
| 最新本番デプロイ             | `eb80d033-d91a-41ff-8ede-16f263d8510b`、commit `9b6bb9ed1673668f88e78aa15c087ac8a84a5b69`、2026-10-27 05:34 JST、成功                                                                                              |
| 実ビルド環境                 | 2026-10-26T20:34:07.633821Zのログに `nodejs@22.23.4`。05:34:24 JSTに `npm ci && npm run build` を実行                                                                                                              |
| Pages独自のWeb Analytics連携 | Metrics / Productionで `Web analytics is disabled`                                                                                                                                                                 |
| ゾーン側のWeb Analytics      | `gaiden.news` のAutomatic setup。`Enable, excluding visitor data in the EU`が選択済み                                                                                                                              |
| 本番への適用                 | MacのChromeで `https://ai.gaiden.news/` を開き、Cloudflareのbeaconスクリプトを1本確認。リポジトリには手動の計測スクリプトなし                                                                                      |
| 到達の証拠                   | Web Analyticsの `Site: gaiden.news` / `Host: ai.gaiden.news` / `Exclude bots: Yes` / Last 7 daysで10 page views、8 visitsを表示。Last 30 daysでは60 page views。管理画面の表示値であり、実訪問総数とは同一視しない |
| Previewの確認                | 既存 `16fc3af1.ai-gaiden.pages.dev`（ruffのDependabot preview）のトップはbeaconなし、`noindex,nofollow`、本番canonical                                                                                             |

Pages側が無効でも、ゾーン側の既存自動挿入によって本番が計測されていました。公開Privacyの「アクセス解析未導入」はこの実態と不一致です。ローカル修正では、Cloudflare Web Analyticsの利用目的・集計対象・EU除外設定を明記し、独自の入力機能と配信基盤の通信情報を分けて説明します。

先の背景HTTP取得ではbeaconを検出できませんでしたが、今回のブラウザーDOMと管理画面には計測の証拠があります。取得経路・地域等で応答が異なり得るため、その不検出を無効の根拠にはしません。EUからのアクセスを再現する試験はしておらず、EU除外は設定値として確認しました。

`CF_PAGES_BRANCH` によるnoindex/sitemap制御は、Cloudflare側の計測制御ではありません。Previewの非計測は上記1デプロイの観測結果で、全履歴・将来のPreviewを保証するものではありません。Web Analyticsの表示フィルターも収集自体の除外設定ではありません。Advanced OptionsはProへの案内のみで、詳細ルール一覧は表示されませんでした。

## 残る判断・公開後の確認

1. 公開時点で設定を再照合し、承認されたPrivacy文面を公開後、本番の説明・計測スクリプト・到達を確認する。今回の差分は未公開。
2. 管理画面では保持期間や閲覧者一覧を確認していないため、独自の保持期限や「運営者だけが閲覧できる」という断定はしない。運用方針として別途確定する。
3. EU除外設定を含む採用方式の同意要否、広告導入前の基準値、追加クリック計測は別途判断する。今回、新規計測や外部設定の変更は行わない。
4. 追加の計測方式を採用する場合はPreview・ローカルの除外を明示し、JavaScript無効・計測遮断時にも記事と公式リンクが使えることを確認する。

**今回対象の実設定とPrivacy説明の不一致は、検証可能なローカル差分で解消しました。Issue #43全体の追加計測・運用設計まで完了したという意味ではありません。**

## 計測指標と追加設計の候補

| 指標                         | 定義・分母                              | 単位・確認頻度               | 現状／候補                             |
| ---------------------------- | --------------------------------------- | ---------------------------- | -------------------------------------- |
| 閲覧傾向                     | page view数。人数や再訪率と同一視しない | 本番hostname・path・日、週次 | 既存Web Analyticsで本番計測を確認済み  |
| 公式リンクへの遷移率         | 公式リンクclick数 / 個別記事view数      | 記事・配信元・週、週次       | 未計測。custom event方式の別判断が必要 |
| 日次／配信元からの記事遷移率 | 記事リンクclick数 / 対象一覧view数      | 一覧種別・週、週次           | 未計測                                 |
| 7日／30日再訪率              | 期間内再訪者 / 起点訪問者               | 週／月                       | 持続的識別を避け、当面対象外           |
| 検索CTR                      | Google検索click数 / impression数        | ページ・週、週次             | Search Console候補。設定未確認         |
| RSS利用                      | feed取得数（bot・再取得を含む）         | 日、週次                     | 購読者数と区別。取得可否未確認         |
| 翻訳品質                     | fallback・訂正の件数 / 記録のある記事数 | 全体・配信元・日、週次       | `report_quality_metrics.py`で既存実装  |

候補イベントは `official_link_click`（個別記事の公式リンク）、`daily_article_click`（日次一覧）、`source_article_click`（配信元一覧）。採用するときはquery・fragmentを除いたサイト内path、記事ID、配信元ID、イベント名だけを許可し、本文、検索語、氏名、メール、ログインID、任意URL・query、個人識別子を送信しない設計にします。今回イベント送信は実装しません。

既存Cloudflare Web Analyticsは基礎集計に利用されていますが、custom events未対応のためクリック率を推定値で代替しません。識別を伴う再訪追跡や高機能な録画・広告解析は当面採用しません。欠損・遮断・未計測は0として集計せず、未計測／母数不明と記録します。広告導入前の基準値は、対象期間と本番hostnameの条件を決めてから取得します。

## 参照した一次資料

2026-10-27確認:

- [Cookie・localStorage・fingerprintを使わない設計](https://www.cloudflare.com/web-analytics/)
- [Cloudflare Web Analytics概要](https://developers.cloudflare.com/web-analytics/about/)
- [導入と自動挿入](https://developers.cloudflare.com/web-analytics/get-started/)
- [自動挿入の対象ルール](https://developers.cloudflare.com/web-analytics/configuration-options/rules/)
- [FAQ：edge analyticsとの違い、custom events](https://developers.cloudflare.com/web-analytics/faq/)
- [送信先と収集方法](https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/)
- [Cloudflare Privacy Policy](https://www.cloudflare.com/privacypolicy/)
