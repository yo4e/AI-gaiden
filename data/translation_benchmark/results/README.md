# Translation benchmark results

このディレクトリは、明示的にローカル比較を実行した結果スナップショットを保存します。
大きなモデルの取得・実測は通常CI・日次workflowで行わず、結果ファイルは人間が再現条件を確認したうえで更新します。

```bash
python scripts/run_translation_benchmark.py
```

`translation-benchmark.json`、`.csv`、`.md`が同じ評価条件から出力されます。
モデルを取得する場合だけ、ローカルで`--allow-model-download`を明示してください。

実測値には、実行環境、モデルリビジョン、初回取得時間、推論時間、ピークRSS、
設定したローカルキャッシュ容量を含めます。取得時間が分離できない場合や候補を実行できない場合は、
理由とともに`null`または`unknown`で記録し、値を推測しません。
