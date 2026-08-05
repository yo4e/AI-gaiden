# オフライン翻訳モデル比較

Issue #16では、現在のArgos Translateを含む英日ローカル翻訳候補を、実際のAI外電RSSスナップショットで比較できる基盤を追加しています。これは翻訳APIや生成AI APIを追加する変更ではなく、通常の日次更新・サイト生成とは独立したローカル評価です。

## 評価データ

`data/translation_benchmark/corpus.jsonl` は、2026年8月5日に有効な公式RSS/Atomから取得した40件のタイトルと短い概要です。各行に配信元、元記事URL、配信日時を残し、人間参考訳（`reference_title_ja`、`reference_summary_ja`）と人間採点（`human_*_score`）は空欄にしています。サイト記事や `data/seen.json` を評価のために再生成しません。

## 候補と一次情報

候補の機械可読な記録は `config/translation_benchmark.yml` にあります。公式モデルカード・公式リポジトリで確認できない値は `unknown` または `not_measured` とします。

| 候補                                  | 一次情報                                                                                                                                                          | ライセンス         | 容量記録                                | 本番候補         |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | --------------------------------------- | ---------------- |
| Argos Translate `translate-en_ja-1_1` | [Argos Translate](https://github.com/argosopentech/argos-translate)、[公式issueの個別ライセンス確認](https://github.com/argosopentech/argos-translate/issues/507) | 個別パッケージ不明 | 未計測                                  | 除外             |
| OPUS-MT `Helsinki-NLP/opus-mt-en-jap` | [公式モデルカード](https://huggingface.co/Helsinki-NLP/opus-mt-en-jap)                                                                                            | Apache-2.0         | 551 MB（モデルカードのリポジトリ表示）  | 比較候補         |
| FuguMT `staka/fugumt-en-ja`           | [公式モデルカード](https://huggingface.co/staka/fugumt-en-ja)                                                                                                     | CC BY-SA 4.0       | 124 MB（モデルカードのリポジトリ表示）  | 人手確認まで除外 |
| M2M100 `facebook/m2m100_418M`         | [公式モデルカード](https://huggingface.co/facebook/m2m100_418M)                                                                                                   | MIT                | 3.88 GB（モデルカードのリポジトリ表示） | 比較候補         |

FuguMTは商用禁止と断定していませんが、ShareAlike条件とモデル・データの来歴確認が必要なため本番候補から除外しています。Argos英日パッケージは個別ライセンスが不明なため除外します。OPUS-MTとM2M100もライセンスだけで本番採用を決めず、品質・運用・法務を人間が確認します。

## 実行条件と出力

```bash
python scripts/run_translation_benchmark.py
```

OPUS-MT、FuguMT、M2M100のTransformersアダプタを実測する場合は、通常の依存ロックへ追加せずローカルだけに任意依存を入れます。

```bash
python -m pip install "transformers<5"
python scripts/run_translation_benchmark.py --candidate opus-mt-en-ja
```

runnerは各候補へタイトルと概要を別々に渡し、同じ `max_input_tokens=512`、`max_new_tokens=256`、`num_beams=1` を使用します。M2M100だけは英語入力・日本語出力のための言語IDを設定します。URL、数字、用語集で保護する製品名は候補共通の前処理で保護し、既存の `check_translation_quality` を全出力へ適用します。

`data/translation_benchmark/results/` へ次を生成します。

- JSON: 候補メタデータ、実行条件、各入力の翻訳、品質ゲート、推論時間、メモリ、保持率、集計値
- CSV: 1入力・1候補・1対象種別の機械可読な行
- Markdown: タイトル/概要別の集計表

モデルの取得は既定で無効です。キャッシュ済みのモデルだけを比較し、明示的にローカルで取得する場合は次を使います。

```bash
python scripts/run_translation_benchmark.py --allow-model-download
```

このオプションをCIや日次workflowへ追加しません。結果の `not_measured` を実測値に置き換える際は、OS、CPU、メモリ、Python依存、モデルリビジョン、キャッシュ有無、実行日時を記録してください。

## 用語集と品質ゲート

小さな用語集は `config/translation_glossary.yml` に独立して置き、製品名の保護と定型的な日本語用語の後処理を分けています。数字、URL、製品名の保持率は `scripts/translation_quality.py` の `translation_fidelity_metrics` で集計します。流暢さ、人間参考訳、人間採点は品質ゲートの自動判定に混ぜません。

比較結果だけで本番モデルを切り替えず、人間参考訳の作成、自然さの評価、ライセンス確認、Actionsでの実行可能性確認を完了条件として残します。
