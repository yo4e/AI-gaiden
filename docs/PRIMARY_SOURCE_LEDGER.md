# 一次情報ソース台帳（第1弾・第2弾）

このディレクトリには、外電通信が将来の「AI外電」および「テック外電」で利用することを想定した、**発信主体自身による一次情報の監視候補**を記録しています。メイン成果物は `PRIMARY_SOURCE_LEDGER.csv` であり、Excel等へ直接取り込めるUTF-8 with BOMのCSVです。今回の台帳は既存の自動収集設定を変更しません。したがって、現行の `config/feeds.yml` に新規フィードを追加するものではなく、選定・検証・将来導入のための独立した台帳です。

| 項目 | 値 |
|---|---:|
| 確認日 | 2026-08-18（JST） |
| 登録組織・プロジェクト数 | 181 |
| 優先度A / B / C | 99 / 82 / 0 |
| 公式RSS/AtomのURLを確認して記録した件数 | 11 |
| 機械取得候補（詳細台帳） | 174 |

## 収録範囲と記入規則

登録対象は、企業・研究機関・OSSプロジェクト自身が運営する公式サイト、Newsroom、Blog、Research、Developer Blog、Release Notes、公式GitHubです。二次情報メディア、個人ブログ、外部ニュースまとめ、非公式RSS変換サービスは収録していません。各レコードの `primary_monitor_url` は、同じ発表が複数ページに載る場合に**最初に確認すべき主監視先**です。背景やSDKの細部は、同じレコード内のResearch・Developer Blog・Release Notesで補完します。

`rss_atom_url` は、公式フィードとしてURLを確認できたものだけに限定しています。`machine_access` のGitHub URLは公開リポジトリ一覧のAPIエンドポイントを固定しており、個別プロジェクトのRelease APIは、対象リポジトリを選定してから利用する前提です。RSS/API欄の空欄は、今回の調査で安全に特定できなかったことを示すだけで、当該機能が存在しないと断定するものではありません。URLを推測して補ってはいけません。

> 現行システムは公式RSS/Atomのみを取得し、記事HTMLをスクレイピングしない方針です。台帳中の「HTML巡回」は将来の監視方式の候補であり、現行実装への追加・切替を意味しません。導入前には、利用規約、robots.txt、更新頻度、重複・配信遅延、失敗時の扱いを個別に再確認してください。

## カラム仕様

| カラム | 意味 |
|---|---|
| `source_id` | 半永久的に扱う小文字kebab-caseの識別子。将来の設定ファイル・DBの主キー候補。 |
| `organization_name`〜`primary_domains` | 組織の同定、地域、分類、主要領域。 |
| `official_*_url` | 発信主体の公式ページ。空欄は今回安全にURLを特定できなかった欄。 |
| `github_org_url` | 公式GitHub Organization。特定リポジトリしか確認できない場合は空欄にしないため、組織URLのみを基本にした。 |
| `rss_atom_url` | 公式で確認したRSS/AtomのURLだけを登録。 |
| `machine_access` | 公開GitHub Organization APIまたは、公式に文書化されたGitHub Releases API利用を示す。 |
| `primary_monitor_url` / `primary_monitor_rationale` | 監視の起点と、その選定理由。 |
| `update_frequency` | 公式一覧の更新状況に基づく概数。固定スケジュールの保証ではない。 |
| `ai_gaiden_relevance` / `tech_gaiden_relevance` | 編集対象との関連度（非常に高・高・中）。 |
| `priority` | A=継続監視の価値が非常に高い、B=定期確認、C=特定分野で参照。 |
| `update_detection` / `automation_ease` | 監視実装の起点と、相対的な自動化しやすさ。 |
| `notes` / `last_verified` | 運用上の注意と確認日。 |

## 優先度の判断方法

優先度は知名度だけでは決めていません。新モデル・新製品の発表頻度、技術情報の密度、一次資料としての価値、AI／テック業界への影響、継続的な更新の存在を合わせて評価しました。Aには、基盤モデル、クラウド、半導体、重要な開発プラットフォーム、AIの主要OSS・評価団体を中心に置いています。Bは価値が高い一方で、更新の偏り、領域の限定性、または一次記事化の頻度を考慮して定期確認に置いています。第1弾ではCを設定せず、必要性の低い候補を無理に登録する代わりに、100件すべてをAまたはBの実運用候補として精選しました。

## 監視用の抽出ファイル

| ファイル | 件数 | 用途 |
|---|---:|---|
| `PRIMARY_SOURCE_LEDGER_DAILY_TOP20.csv` | 20 | 毎日監視する最重要ソース。公式RSS、GitHub Release、更新頻度の高い公式Changelogを優先。 |
| `PRIMARY_SOURCE_LEDGER_WEEKLY.csv` | 60 | 週1程度の巡回に適したソース。大規模な発表や専門領域の変化を捉える。 |
| `PRIMARY_SOURCE_LEDGER_TECH_FOCUS.csv` | 50 | 将来のテック外電を見据え、Web、クラウド、開発、半導体、クリエイティブ、ブラウザに重心を置いた抽出。 |

## 毎日監視したい上位20

| 順位 | 組織・プロジェクト | 主監視先 | 検知方法 |
|---:|---|---|---|
| 1 | OpenAI | https://openai.com/news/ | 公式RSS/Atom |
| 2 | Anthropic | https://www.anthropic.com/news | 公式Newsroom／Blog／Research一覧のHTML巡回（Release Notesがある場合は補完） |
| 3 | Google DeepMind | https://deepmind.google/blog/ | 公式RSS/Atom |
| 4 | Meta AI | https://about.fb.com/news/ | 公式Newsroom／Blog／Research一覧のHTML巡回（Release Notesがある場合は補完） |
| 5 | Mistral AI | https://mistral.ai/news/ | 公式RSS/Atom |
| 6 | DeepSeek | https://api-docs.deepseek.com/news/news | 公式Newsroom／Blog／Research一覧のHTML巡回（Release Notesがある場合は補完） |
| 7 | Amazon Web Services | https://press.aboutamazon.com/aws | 公式RSS/Atom |
| 8 | Google Cloud | https://cloud.google.com/press | 公式Newsroom／Blog／Research一覧のHTML巡回（Release Notesがある場合は補完） |
| 9 | Microsoft AI / Azure AI | https://news.microsoft.com/ | 公式RSS/Atom |
| 10 | NVIDIA | https://blogs.nvidia.com/blog/category/deep-learning/ | 公式RSS/Atom |
| 11 | GitHub | https://github.blog/ai-and-ml/ | 公式RSS/Atom |
| 12 | Cloudflare | https://www.cloudflare.com/press/ | 公式Newsroom／Blog／Research一覧のHTML巡回（Release Notesがある場合は補完） |
| 13 | Vercel | https://vercel.com/blog | 公式Newsroom／Blog／Research一覧のHTML巡回（Release Notesがある場合は補完） |
| 14 | Databricks | https://www.databricks.com/company/newsroom | 公式Newsroom／Blog／Research一覧のHTML巡回（Release Notesがある場合は補完） |
| 15 | Hugging Face | https://huggingface.co/blog | 公式RSS/Atom |
| 16 | PyTorch | https://github.com/pytorch/pytorch/releases | GitHub Releases／Tags／公開リポジトリ更新 |
| 17 | vLLM | https://github.com/vllm-project/vllm/releases | GitHub Releases／Tags／公開リポジトリ更新 |
| 18 | Ollama | https://github.com/ollama/ollama/releases | GitHub Releases／Tags／公開リポジトリ更新 |
| 19 | LangChain | https://github.com/langchain-ai/langchain/releases | GitHub Releases／Tags／公開リポジトリ更新 |
| 20 | MLCommons | https://mlcommons.org/category/news/ | 公式RSS/Atom |

## 週1程度で十分な情報源

`PRIMARY_SOURCE_LEDGER_WEEKLY.csv` に抽出済みです。モデル・プロダクト企業ではCohere、AI21 Labs、Qwen、Sakana AI、Stability AI、Midjourney、Runway、ElevenLabs、Perplexity、Writerを中心に、クラウド・開発・半導体・デザイン・研究・OSSまで広げています。日次運用でシグナルを落とさず、専門領域の変化も追うための補完レイヤーです。

## AI外電より将来のテック外電向きの情報源

`PRIMARY_SOURCE_LEDGER_TECH_FOCUS.csv` に抽出済みです。Cloudflare、Vercel、GitHub、GitLab、Docker、HashiCorp、Supabase、MongoDB、Elastic、Datadog、Postman、Stripe、NVIDIA、Arm、TSMC、Adobe、Figma、Shopify、Apple、Mozilla、Braveなどは、AIに直結する発表も扱いつつ、Web基盤・開発者ツール・半導体・ブラウザ・デザイン・コマースという拡張先の中心となります。



## 第2弾：情報源単位の詳細台帳と監視推奨セット

第2弾では第1弾の100組織を正本として保持したまま、81組織・プロジェクトを追加し、総数を**181**へ拡張しました。さらに、組織単位の台帳とは別に、Newsroom、Blog、Research、Developer、Release Notes、GitHub、RSS等を**1情報源＝1行**で保持する詳細台帳を新設しています。現行の`config/feeds.yml`、自動収集コード、GitHub Actionsは変更していません。

| 成果物 | 件数 | 内容 |
|---|---:|---|
| `PRIMARY_SOURCE_LEDGER.csv` | 181組織 | 組織単位の正本。第1弾100件を維持し、第2弾81件を追加。 |
| `PRIMARY_SOURCE_LEDGER_DETAILED.csv` | 753情報源 | 1情報源＝1行の詳細台帳。URL、種類、公式性、Feed、機械取得、JavaScript要否、優先度を構造化。 |
| `PRIMARY_SOURCE_MONITORING_RECOMMENDATION.csv` | 85情報源 | AI外電に導入する候補。P1（日次）35件、P2（週次）30件、P3（補助）20件。 |

詳細台帳で`feed_status=confirmed`とするのは、公式RSS/Atom URLを確認できた11件のみです。それ以外のRSS／Atom／JSON Feedは`unknown`または空欄とし、URLを推測していません。`machine_fetchability`は、`rss_atom`、`github_releases_api`、`github_api`、`html_diff`のいずれかを、現段階での機械取得手段として示します。HTML巡回は将来候補であり、現行のRSS-only収集実装への追加を意味しません。

## 参照・検証の根拠

公式RSSの一部は、既存の有効フィード設定（[config/feeds.yml](../config/feeds.yml)）にも採用されているものです。OpenAIの公式Newsは研究・製品・安全性・エンジニアリング等を公式カテゴリで集約し、主監視先として適しています。[1] NVIDIAは公式RSS案内ページでDeveloper Blogを含む複数の公式フィードを案内しています。[2] Google DeepMindとAnthropicも公式サイト上に時系列のニュース発信面を持ちます。[3] [4] 研究機関ではStanford HAIが研究・政策・教育をNewsで公式に発信しています。[5] GitHubの公開Releaseは公式REST APIで取得でき、OSSの変更検知に利用できます。[6]

[1]: https://openai.com/news/ "OpenAI News"
[2]: https://www.nvidia.com/en-us/about-nvidia/rss/ "NVIDIA RSS Feeds"
[3]: https://deepmind.google/blog/ "Google DeepMind News"
[4]: https://www.anthropic.com/news "Anthropic Newsroom"
[5]: https://hai.stanford.edu/news "Stanford HAI News"
[6]: https://docs.github.com/en/rest/releases/releases "GitHub REST API: Releases"
