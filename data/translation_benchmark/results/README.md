# Translation benchmark results

このディレクトリは、明示的にローカル比較を実行したときの生成先です。
大きなモデルや実測値を通常CI・日次workflowへ持ち込まず、結果ファイルはコミットしません。

```bash
python scripts/run_translation_benchmark.py
```

`translation-benchmark.json`、`.csv`、`.md`が同じ評価条件から出力されます。
モデルを取得する場合だけ、ローカルで`--allow-model-download`を明示してください。
