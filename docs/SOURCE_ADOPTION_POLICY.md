# 一次情報ソース採用方式の再分類

Issue #49 の Phase 3A 実運用結果を受け、`PRIMARY_SOURCE_MONITORING_RECOMMENDATION.csv` の監視推奨85件を、**取得方式**と**記事採用方式**の二軸で再分類する。

## 背景

Phase 3A で Sourcegraph Technical Changelog RSS を実運用したところ、取得・翻訳・生成パイプライン自体は正常に動作した一方、最初の実収集として一般的な self-hosted パッチリリースが記事化された。

この結果から、「企業・媒体を監視対象にするか」だけでは粗く、次の二つを分離する必要がある。

1. **どう取得するか**: RSS / GitHub Releases API / GitHub Organization API / HTML差分
2. **取得した候補をどう採用するか**: 全件採用 / AI関連記事のみ採用 / 対象外

元の一次情報ソース台帳は破棄・再調査しない。今回の分類は、監視推奨85件に対する運用レイヤーとして追加する。

正本:
- `docs/PRIMARY_SOURCE_MONITORING_RECOMMENDATION.csv`
- `docs/PRIMARY_SOURCE_ADOPTION_CLASSIFICATION.csv`

## 再分類結果

85件の `adoption_mode`:

- `all`: 47件
- `filtered`: 35件
- `none`: 3件

取得・導入段階 (`collection_phase`):

- `current_rss`: 9件
- `phase_3b`: 13件
- `phase_3c`: 2件
- `later_html`: 25件
- `later_github_org`: 22件
- `duplicate`: 11件
- `hold`: 3件

`duplicate` は別の推奨行と同じ実フィード・同じ監視面を指すため、二重巡回しない。

## adoption_mode

### `all`

媒体・配信面自体がAI/MLに十分限定されており、AI関連度フィルタを通さず候補化してよい。

例:
- OpenAI News
- Google DeepMind Blog
- Hugging Face Blog
- GitHub AI & ML
- AWS Machine Learning
- NVIDIA Deep Learning
- Apple Machine Learning Research
- MLCommons
- Mistral AI
- AI専用OSSのGitHub Releases（LangChain / PyTorch / vLLM / Ollama / LlamaIndex / llama.cpp 等）

`all` は「重要度の高い記事だけ」という意味ではない。AI外電の掲載対象領域に属するかどうかの判定を省略できる、という意味。

### `filtered`

企業・媒体・リリース面がAI以外の話題を含むため、タイトル・概要・カテゴリ等でAI関連度フィルタを通したものだけ候補化する。

代表例:
- Sourcegraph Technical Changelog
- Microsoft Cloud Blog
- Redis Releases
- Brave Releases
- Bun / Deno Releases
- GitHub Changelog / 一般Blog / Newsroom
- Google Cloud Blog / Press
- Apple Newsroom / Developer Releases
- Cloudflare Changelog
- NVIDIA Developer Blog / Newsroom
- Databricks Blog / Release Notes
- AWS Developer Blog / Amazon Science

### `none`

監視面が広すぎ、より限定された公式ソースで代替できるため、現時点では採用しない。

- AWS公式トップ
- GitHub公式トップ
- Google Cloud公式トップ

## ai_terms_v1

初期実装はLLM判定を使わず、タイトル・概要・カテゴリ/タグに対する決定論的な用語フィルタから始める。

### 強いAI語

単独一致で採用候補にできる語・句の例:

- artificial intelligence
- generative AI / genAI
- LLM / large language model
- foundation model
- AI agent / agentic
- MCP / Model Context Protocol
- RAG / retrieval-augmented generation
- machine learning / deep learning
- Copilot
- Gemini
- Claude
- GPT
- Llama
- Bedrock
- Vertex AI
- Workers AI
- AI Gateway
- Apple Intelligence
- Cody
- Mosaic AI

`AI` / `ML` は部分文字列ではなく単語境界で判定する。

### 文脈が必要な弱い語

単独では一般技術にも現れるため、強いAI語または別の弱いAI語との組み合わせを要求する。

- agent
- model
- inference
- vector
- embedding
- training
- sandbox
- computer use
- search
- runtime

例: `vector search` は採用寄りだが、`vector` 単独では採用しない。

### 除外寄りのシグナル

以下は、それ自体ではAI関連記事とみなさない。

- generic patch release / version bump
- CDN
- network
- security
- browser engine
- JavaScript runtime
- database maintenance
- generic performance improvement
- generic self-hosted release

ただし同じ候補内に強いAIシグナルがあれば採用可能。

## 判定対象フィールド

初期版では次を使用する。

1. title
2. summary / description
3. category / tag（取得できる場合）

本文HTMLのスクレイピングは前提にしない。

## 実装上の形

将来的に `config/feeds.yml` 等で、取得設定と採用設定を分離する。

```yaml
admission:
  mode: all
```

または:

```yaml
admission:
  mode: filtered
  policy: ai_terms_v1
```

GitHub Releases/API系でも同じ採用設定を再利用できるようにし、RSS専用ロジックにはしない。

## Phase 3 の進め方

従来の「RSS → GitHub API → 部分採用」を完全に直列化せず、取得方式と採用方式を独立させる。

### まず

- 現行のAI専用RSSは `all` のまま維持
- Sourcegraph は `filtered / ai_terms_v1` に変更する
- Microsoft Cloud Blog は `filtered / ai_terms_v1` が利用可能になるまで追加しない

### Phase 3B

GitHub Releases API の取得基盤を追加する。

最初の導入候補は `phase_3b` の13件。AI専用プロジェクトは `all`、Brave / Redis / Bun / Deno は `filtered` として同じ採用レイヤーへ流す。

### Phase 3C

`ai_terms_v1` を共通の候補フィルタとして実装し、RSS・GitHub Releases/APIの双方から利用できるようにする。

Sourcegraph を最初の回帰テストケースにする。

最低限、既に実収集された一般的な Sourcegraph self-hosted パッチリリースは不採用になり、Cody / AI agent / LLM / MCP 等が明示された候補は採用されることをテストする。

## 今回やらないこと

- 181組織・753情報源の再調査
- LLMによる意味ベース判定
- AI重要度スコア
- 本文スクレイピング
- `later_html` / `later_github_org` の一括実装

これらは用語フィルタの偽陽性・偽陰性を実運用で確認してから必要性を判断する。
