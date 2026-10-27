# Python依存の更新と検証

`requirements.in` が直接依存の正本、`requirements.lock` がCI・日次運用のインストール対象です。片方だけの更新は完了と扱いません。

## 更新手順

1. Python 3.12の作業環境で `python -m pip install uv==0.12.17` を実行する。
2. `requirements.in` の対象パッケージを更新する。torch、pytestの大きい更新は小更新と混ぜず、個別に評価する。
3. `python scripts/lock_requirements.py` を実行し、両ファイルの差分を確認する。
4. `python scripts/lock_requirements.py --check` が成功することを確認する。
5. 新しい仮想環境に `python -m pip install -r requirements.lock` で導入し、`python -m pip check` と `python -m pip list --format=freeze` で実使用版を記録する。
6. `ruff check .`、`pytest`、`python scripts/validate_repository.py`、`npm run check`、`SITE_URL=https://ai.gaiden.news npm run build`、`npm run validate:rss` を実行する。
7. 入力とlockを同じPRに含め、CIログの実バージョンを確認する。ローカル成功とLinux CI成功は分けて記録する。

Dependabotが入力だけを変更した場合、CIはlock整合性確認で失敗します。上記手順でその提案ブランチのlockを再生成してからレビューします。自動コミットや `pull_request_target` は追加していません。依存更新のためにCIの失敗を無視してmergeしません。

## 固定する解決条件

- uv 0.12.17、Python 3.12、universal解決
- `--index-strategy unsafe-best-match --emit-index-url` は既存lock生成条件を維持
- `requirements.in` にあるPyPI／PyTorch CPU索引を使用
- 作業用ディレクトリに既存lockをコピーし、その版を優先して解決。対象と無関係な依存を一斉更新しない
- 検証モードでは元のlockを変更せず、実際のインストール指定（索引、版、環境marker）を再生成結果と比較。生成コメントと空行だけを除外
- CI・日次workflowはこの照合に成功してから、コミット済みlockをインストールする。索引へ到達できない場合も検証成功とは扱わない

直接依存だけでなく、推移依存やLinux／非Linuxのtorch指定も検査対象です。uv自体を更新する場合はスクリプトと両workflowの固定版を同時に変更し、lock差分をレビューしてください。

参考: [uvのlockと既存バージョン優先の仕様](https://docs.astral.sh/uv/pip/compile/)

## 2026-10-27の候補確認

#104（python-dateutil 3.0.0）と #107（ruff 0.17.2）は、それぞれ `requirements.in` だけを変更するPRです。ローカルの別フォルダで、旧lockの検証失敗→再生成→整合性確認成功を再現しました。#104は `tzdata` の追加が必要、#107はruffの版だけの変更でした。本変更の直接依存版は更新しておらず、候補PRのmergeも行っていません。これらのPRへ本手順を適用してlock差分とLinux CI結果を確認する作業は、公開・PR操作の承認後に行います。
