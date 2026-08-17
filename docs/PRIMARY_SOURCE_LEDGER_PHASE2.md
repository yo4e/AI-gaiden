# 一次情報ソース台帳 第2弾：完了サマリー

第1弾の100組織を再調査せず正本として維持し、81組織・プロジェクトを追加しました。現行のRSS収集設定、アプリコード、GitHub Actionsは変更していません。今回の新設物は、将来の監視網実装のための**1情報源＝1行**の詳細台帳と、AI外電向けの優先監視候補です。

| 指標 | 件数 |
|---|---:|
| 総組織数 | 181 |
| 追加組織数（第2弾） | 81 |
| 総情報源数（URL重複除去後） | 753 |
| 確認済みRSS/Atom数 | 11 |
| 機械取得候補（RSS/GitHub API/Release） | 174 |
| P1 / P2 / P3 | 35 / 30 / 20 |

## 主要な発見

AI外電に直結する最も取得しやすい層は、公式RSS、公開GitHub Releases、公式Changelogです。第1弾で確認済みのRSSは引き続き最優先とし、第2弾ではFireworks AIの公式Changelog、Waymoの公式ブログ、NISTのAI公式ページを重点的に確認しました。標準化・政府・ロボティクスの情報源は、モデル発表とは異なるものの、AIの評価、安全性、規制、フィジカルAIの変化を補うため、将来のテック外電で特に有用です。

## 未解決・要手動確認

RSS／Atom／JSON Feedは、第1弾で既に確認されたもの以外を推測で補っていません。`feed_status=unknown`、`requires_javascript=unknown`、または`machine_fetchability=html_diff`の情報源は、実装導入前に、公式導線、コンテンツ種別、利用条件、robots.txt、取得頻度、重複排除を個別に確認してください。

## AI外電への導入候補

`PRIMARY_SOURCE_MONITORING_RECOMMENDATION.csv` のP1を日次、P2を週次、P3を補助監視として使用できます。導入は既存のRSS-only設計を変えず、まず確認済みRSSとGitHub Releases APIの対象から段階的に評価することを推奨します。

## 参照

NISTのAI公式ページはAI RMF、AI標準、評価、News／Blog／RSS導線を掲載しています。[1] Waymoの公式ブログWaypointはCompany News、Safety、Technology等を同社カテゴリで公開しています。[2] Fireworks AIの公式Changelogは日付付きのモデル、API、SDK、文書更新を示しています。[3]

[1]: https://www.nist.gov/artificial-intelligence "NIST Artificial intelligence"
[2]: https://waymo.com/blog/ "Waypoint — The official Waymo blog"
[3]: https://docs.fireworks.ai/updates/changelog "Fireworks AI Changelog"
