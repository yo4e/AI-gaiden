# 人間評価用サンプル

`representative_samples.csv` と `representative_samples.md` は、40件コーパスから選んだ12件について、タイトルと概要をA〜Dへ匿名化した評価表です。Markdownは`(sample_id, target_type)`ごとの24セクションに分かれ、各セクションはA〜Dの4候補と対応する原文だけを含みます。モデル名はこの2ファイルに含めません。

各出力を次の基準で評価してください。

- `meaning_accuracy`: 意味の正確さ。1（不正確）〜5（原文に忠実）
- `naturalness`: 日本語の自然さ。1（読みにくい）〜5（自然）
- `heading_clarity`: 見出しの明瞭さ。1（不明瞭）〜5（明快）。概要行は必要に応じて`N/A`
- `number_proper_noun_retention`: 数字・固有名詞保持。1（欠落/破損）〜5（完全）
- `added_facts`: 原文にない追加。`なし`または`あり`

評価とメモを書き終えてから、別ファイルの`model_key.csv`を開いてA〜Dとの対応を確認してください。比較結果から本番採用候補を自動決定しません。

評価後の機械可読な記録は`evaluation_results.json`、人間向けの要約は`evaluation_results.md`です。これらは評価完了後の判断記録であり、匿名サンプルの評価前には開かないでください。
