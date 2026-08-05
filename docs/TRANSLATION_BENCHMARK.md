# オフライン翻訳モデル比較

Issue #16では、現在のArgos Translateを含む英日ローカル翻訳候補を、実際のAI外電RSSスナップショットで比較できる基盤を追加しています。これは翻訳APIや生成AI APIを追加する変更ではなく、通常の日次更新・サイト生成とは独立したローカル評価です。

## 評価データ

`data/translation_benchmark/corpus.jsonl` は、2026年8月5日に有効な公式RSS/Atomから取得した40件のタイトルと短い概要です。各行に配信元、元記事URL、配信日時を残し、人間参考訳（`reference_title_ja`、`reference_summary_ja`）と人間採点（`human_*_score`）は空欄にしています。サイト記事や `data/seen.json` を評価のために再生成しません。

## 候補と一次情報

候補の機械可読な記録は `config/translation_benchmark.yml` にあります。公式モデルカード・公式リポジトリで確認できない値は `unknown` または `not_measured` とします。

| 候補                                  | 一次情報                                                                                                                                                                                                                                 | ライセンス                                     | 容量記録                                | 本番候補             |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | --------------------------------------- | -------------------- |
| Argos Translate `translate-en_ja-1_1` | [Argos Translate](https://github.com/argosopentech/argos-translate)、[package index](https://github.com/argosopentech/argospm-index/blob/main/index.json)、[公式issue #507](https://github.com/argosopentech/argos-translate/issues/507) | 個別パッケージ不明                             | 未計測                                  | 暫定運用のみ         |
| OPUS-MT `Helsinki-NLP/opus-mt-en-jap` | [モデルカード](https://huggingface.co/Helsinki-NLP/opus-mt-en-jap)、[OPUS-MT](https://github.com/Helsinki-NLP/Opus-MT)、[OPUS-MT-train](https://github.com/Helsinki-NLP/OPUS-MT-train)                                                   | HF: Apache-2.0 / upstream: CC-BY-4.0（不一致） | 551 MB（モデルカードのリポジトリ表示）  | 不採用               |
| FuguMT `staka/fugumt-en-ja`           | [モデルカード](https://huggingface.co/staka/fugumt-en-ja)、[公式リポジトリ](https://github.com/s-taka/fugumt)、[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)                                                           | CC BY-SA 4.0（帰属・ShareAlike条件）           | 124 MB（モデルカードのリポジトリ表示）  | 修正・確認後に再評価 |
| M2M100 `facebook/m2m100_418M`         | [モデルカード](https://huggingface.co/facebook/m2m100_418M)、[Meta公式説明](https://ai.meta.com/research/publications/Beyond-English-Centric-Multilingual-Machine-Translation/)                                                          | MIT（モデルライセンス上は商用可）              | 3.88 GB（モデルカードのリポジトリ表示） | 不採用               |

## ライセンス・データ来歴・最終運用判断（2026-08-05）

以下は公式モデルカード、公式リポジトリ、公式ライセンス本文を突き合わせた運用記録であり、法的助言ではありません。`production_candidate` はライセンスだけで自動的に決めず、品質、実行性、適用ライセンス、学習データ来歴の確認をすべて満たす場合だけ `true` にします。

### Argos Translate en→ja (`translate-en_ja-1_1`)

- package indexには言語、バージョン、配布URLはあるが、個別packageのライセンス欄はない。
- 公式Issue #507でも `translate-en_ja-1_1.argosmodel` はライセンス未記載の対象として残っている。
- 個別packageの学習データ内訳・来歴も、確認できる公式metadataからは確定できない。
- 現行運用は既存の取得経路に限って暫定継続するが、権利確認済みの本番候補とは扱わない。モデルの再配布、改変配布、利用範囲の拡大は行わない。

### OPUS-MT en→ja (`Helsinki-NLP/opus-mt-en-jap`)

- Hugging FaceモデルカードはApache-2.0と表示する一方、公式OPUS-MT/OPUS-MT-trainは公開pre-trained modelをCC-BY 4.0として説明している。
- どちらも商用利用を禁止する表示ではないが、当該モデルへ適用すべきライセンスと表示・再配布条件を一意に確定できない。
- モデルカードのデータ記載は `dataset: opus` にとどまり、英日学習データの構成corpusと権利条件をこのモデル単位では特定できない。
- 人間評価でも意味不成立の出力が多いため、品質と来歴・ライセンス表示の未確定を理由に不採用とする。

### FuguMT en→ja (`staka/fugumt-en-ja`)

- モデルカードとupstreamはCC BY-SA 4.0を示しており、非商用限定とは断定しない。商用利用を妨げない一方、帰属表示と、改変・派生配布時のShareAlike条件を守る必要がある。
- upstreamはJESC、KFTT、Tanaka Corpus、JSNLI、WikiMatrix等と独自収集データ、約660万対訳pairを記録しているが、Hugging Face版とupstreamのモデルversion対応は明示的にpinできない。
- 人間評価では自然さが最良だったが、`ZX...QXZ`形式の保護placeholder破損が複数あり、固有名詞・製品名保持の品質ゲート上、本番利用は不可。
- placeholder保護修正、モデルversionとデータ来歴の対応確認、帰属表示方針の確定、再評価が終わるまで本番候補にしない。

### M2M100 418M (`facebook/m2m100_418M`)

- 公式モデルカードはMITで、モデルライセンス上は商用利用・改変・再配布を妨げない。
- Metaの公式説明は多数言語の学習データを大規模なminingで構築したと説明するが、モデルカードだけでは英日部分のsource-level corpusと権利条件を個別に列挙していない。
- 今回は実行結果がなく、3.88 GBのresource負荷、GitHub Actionsでの実用性、品質を評価できない。
- したがって、ライセンス表示だけを根拠に採用せず、未実測とデータ来歴未確定を理由に不採用とする。

### 最終運用判断案

品質・実行性・権利情報の三条件を現時点で同時に満たす切替候補はない。

1. 本番モデルは切り替えず、既存Argosを個別packageのライセンス未確認を明示した暫定運用として維持する。
2. 品質ゲート、保護placeholder、数字・固有名詞検査の失敗時は、原題中心の安全な表示へフォールバックする。
3. OPUS-MTは品質不良とライセンス表示・学習データ来歴の未確定により不採用とする。
4. FuguMTは自然さの有力候補だが、placeholder保護、version/provenance、帰属表示を解決して再評価するまで不採用とする。
5. M2M100はモデルライセンス上の商用可否は肯定できるが、未実測・resource負荷・source-level来歴未確定のため不採用とする。

この判断は比較用記録にのみ反映し、通常CI・日次workflowで大型モデルを取得せず、本番モデルの切替も行わない。

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

比較結果だけで本番モデルを切り替えず、人間参考訳の作成、追加の自然さ評価、FuguMTのplaceholder保護修正、候補ごとのversion/provenance確認、必要に応じたActions実行可能性確認を残課題とします。今回の一次情報確認では、未確認事項を商用可または商用不可と推測して確定していません。

## 人間評価用の匿名サンプル

`scripts/create_human_evaluation.py` は、実測JSONから12件（10〜15件の範囲）の代表サンプルを決定的に抽出し、タイトルと概要を含むA〜Dの匿名評価表を `data/translation_benchmark/human_evaluation/representative_samples.csv` と `.md` に出力します。Markdownは`(sample_id, target_type)`単位の24セクションに分け、各セクションをA〜Dの4候補と対応する原文だけにします。評価項目は意味の正確さ、日本語の自然さ、見出しの明瞭さ、数字・固有名詞保持、原文にない追加です。評価者は空欄を記入し、評価完了後にだけ同ディレクトリの `model_key.csv` を開きます。対応表を使う前に候補を自動採用せず、実測結果だけで本番モデルを切り替えません。

```bash
python scripts/create_human_evaluation.py
```

`representative_samples.csv` と `.md` は評価用の空欄を保持し、`model_key.csv` はモデル名との対応を別ファイルに分離します。

### 評価済みの結果と暫定判断

2026-08-05の人間評価では、S01・S05・S07・S09・S10のtitle/summary計10組についてC（Argos Translate）とD（FuguMT）を比較し、Dが7票、Cが3票でした。自然さ・読みやすさはFuguMTが優勢でしたが、FuguMTには`ZX...QXZ`形式の保護プレースホルダー破損が複数あり、固有名詞・製品名保持に致命的なリスクがあります。OPUS-MTは意味不成立が多く、M2M100は実行結果がなく評価不能でした。

暫定的には現行Argosを維持し、FuguMT・OPUS-MT・M2M100への本番切替は行いません。品質ゲート、保護プレースホルダー、数字・固有名詞検査に失敗した場合は原題中心の安全な表示へフォールバックします。評価結果の機械可読データとMarkdown要約は [`data/translation_benchmark/human_evaluation/evaluation_results.json`](../data/translation_benchmark/human_evaluation/evaluation_results.json) と [`evaluation_results.md`](../data/translation_benchmark/human_evaluation/evaluation_results.md) に保存しています。

残作業は、FuguMTのプレースホルダー保護修正後の再評価、Hugging Face版とupstreamのversion/provenance対応の確認、必要時のM2M100再実測、人間参考訳と追加の自然さ評価です。Argosの個別package権利情報とOPUS-MTの適用ライセンス・corpus単位の権利情報は未確定のままです。本PRでは本番モデルを切り替えません。
