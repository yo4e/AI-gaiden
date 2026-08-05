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

このフォローアップで作成した結果スナップショットは、実行日時の異なる値を混ぜないため、JSON・CSV・Markdownを同じコミットで保存します。`candidate_measurements`には実行環境、実際に読み込んだモデルリビジョン、アダプタ初期化に要した時間、推論時間、ピークRSS、設定したローカルキャッシュの前後容量を記録します。初回取得時間はダウンロードだけを分離できないため、キャッシュ増分があった場合の「アダプタ初期化（取得を含む）」として記録し、それ以外は`null`とします。今回の成功候補は候補ごとに別プロセスで実行しているため、ピークメモリは各候補のベンチマークプロセス内の累積ピークRSSです。複数候補を一度に指定した通常runner実行では候補間でRSSを分離できないため、その測定範囲も結果へ明記します。

モデルの取得は既定で無効です。キャッシュ済みのモデルだけを比較し、明示的にローカルで取得する場合は次を使います。

```bash
python scripts/run_translation_benchmark.py --allow-model-download
```

このオプションをCIや日次workflowへ追加しません。結果の `not_measured` を実測値に置き換える際は、OS、CPU、メモリ、Python依存、モデルリビジョン、キャッシュ有無、実行日時を記録してください。

## 用語集と品質ゲート

小さな用語集は `config/translation_glossary.yml` に独立して置き、製品名の保護と定型的な日本語用語の後処理を分けています。数字、URL、製品名の保持率は `scripts/translation_quality.py` の `translation_fidelity_metrics` で集計します。流暢さ、人間参考訳、人間採点は品質ゲートの自動判定に混ぜません。

比較結果だけで本番モデルを切り替えず、人間参考訳の作成、自然さの評価、ライセンス確認、Actionsでの実行可能性確認を完了条件として残します。

## 人間評価用の匿名サンプル

`scripts/create_human_evaluation.py` は、実測JSONから12件（10〜15件の範囲）の代表サンプルを決定的に抽出し、タイトルと概要を含むA〜Dの匿名評価表を `data/translation_benchmark/human_evaluation/representative_samples.csv` と `.md` に出力します。Markdownは`(sample_id, target_type)`単位の24セクションに分け、各セクションをA〜Dの4候補と対応する原文だけにします。評価項目は意味の正確さ、日本語の自然さ、見出しの明瞭さ、数字・固有名詞保持、原文にない追加です。評価者は空欄を記入し、評価完了後にだけ同ディレクトリの `model_key.csv` を開きます。対応表を使う前に候補を自動採用せず、実測結果だけで本番モデルを切り替えません。

```bash
python scripts/create_human_evaluation.py
```

`representative_samples.csv` と `.md` は評価用の空欄を保持し、`model_key.csv` はモデル名との対応を別ファイルに分離します。

### 評価済みの結果と暫定判断

2026-08-05の人間評価では、S01・S05・S07・S09・S10のtitle/summary計10組についてC（Argos Translate）とD（FuguMT）を比較し、Dが7票、Cが3票でした。自然さ・読みやすさはFuguMTが優勢でしたが、FuguMTには`ZX...QXZ`形式の保護プレースホルダー破損が複数あり、固有名詞・製品名保持に致命的なリスクがあります。OPUS-MTは意味不成立が多く、M2M100は実行結果がなく評価不能でした。

暫定的には現行Argosを維持し、FuguMT・OPUS-MT・M2M100への本番切替は行いません。品質ゲート、保護プレースホルダー、数字・固有名詞検査に失敗した場合は原題中心の安全な表示へフォールバックします。評価結果の機械可読データとMarkdown要約は [`data/translation_benchmark/human_evaluation/evaluation_results.json`](../data/translation_benchmark/human_evaluation/evaluation_results.json) と [`evaluation_results.md`](../data/translation_benchmark/human_evaluation/evaluation_results.md) に保存しています。

残作業は、候補のライセンス・データ来歴・商用可否の一次情報確認、採用/不採用理由の文書化、FuguMTのプレースホルダー保護修正後の再評価、必要時のM2M100再実測、人間参考訳と追加の自然さ評価です。本PRでは本番モデルを切り替えません。
