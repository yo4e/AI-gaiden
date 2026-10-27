# AI外電 運用メモ

この文書は、実装仕様とは別に、公開後の運用変更と判断理由を記録する。

## 2026-08-07: Chromeで`gaiden.news`がブロックされた事象と復旧手順

通常のChromeプロファイルで、`https://gaiden.news/`が開けたり、HTTP 403のようなエラー表示になったりする事象を調査した。

調査時に再現した実際のエラーは、Cloudflareや配信元が返したHTTP 403ではなく、Chrome内部の`ERR_BLOCKED_BY_CLIENT`だった。

### 確認結果

- `https://ai.gaiden.news/`は通常Chromeで12回再読み込みし、すべて正常表示した
- `https://gaiden.news/`は通常Chromeで12回再読み込みし、すべて`ERR_BLOCKED_BY_CLIENT`になった
- `https://ai-gaiden.pages.dev/`と`https://gaiden-news.pages.dev/`は正常表示した
- シークレットウィンドウでは`https://gaiden.news/`を正常表示できた
- エラー時の`document.URL`は`chrome-error://chromewebdata/`だった
- エラー本文は「このページは Chrome によってブロックされています」だった
- Cloudflare Security Eventsには、該当ホスト・該当時間帯のイベントがなかった
- Cloudflareへ到達したHTTPレスポンスがないため、`cf-ray`、`server`、`cf-cache-status`、`cf-mitigated`等のレスポンスヘッダーも存在しなかった

以上から、調査時に再現した事象はCloudflareやサイト実装ではなく、通常Chromeプロファイル内でネットワーク送信前に遮断されたものと判断した。

### MetaMaskとの関係

Chrome拡張機能MetaMaskのcontent scriptから、次の警告が出ていた。

- `MaxListenersExceededWarning`
- `ObjectMultiplex - orphaned data`
- `app-init-liveness`
- `background-liveness`

拡張機能IDは`nkbihfbeogaeaoehlefnkodbefgpgknn`、スクリプトは`scripts/contentscript.js`だった。

MetaMaskを一時的に無効化すると`https://gaiden.news/`は正常表示した。その後MetaMaskを再有効化しても正常表示を維持した。

このため、恒常的なドメインブロックではなく、MetaMaskのcontent script、バックグラウンド処理、Service Worker等の一時的な内部状態不良が解消した可能性が高い。ただし、警告と遮断の直接的な因果関係までは確認していない。

### 再発時の初動

同様の表示障害が起きた場合は、Cloudflare設定を変更する前に次の順で切り分ける。

1. エラー表示が`HTTP ERROR 403`か`ERR_BLOCKED_BY_CLIENT`か確認する
2. シークレットウィンドウで同じURLを開く
3. `*.pages.dev`のPages標準ドメインでも確認する
4. 通常Chromeだけ失敗する場合は、MetaMaskを一度無効化して再読み込みする
5. 復旧後にMetaMaskを再有効化し、再発するか確認する
6. 直らない場合は、広告ブロック、セキュリティ、VPN、プロキシ等の拡張機能を順に確認する

`ERR_BLOCKED_BY_CLIENT`で`document.URL`が`chrome-error://chromewebdata/`の場合、Cloudflareへリクエストが届いていないため、Security EventsやRay IDの調査を先に行っても該当記録は得られない。

### 本物のHTTP 403が再発した場合

Chromeのエラーではなく、documentリクエストとしてHTTP 403が記録された場合は別事象として扱う。

DevToolsのNetworkで次を記録し、`cf-ray`をCloudflare Security Eventsと照合する。

- Request URL
- Request Method
- Status Code
- `cf-ray`
- `server`
- `cf-cache-status`
- `cf-mitigated`
- `location`
- Response本文

原因が特定できるまで、DNS、Pages Custom domains、Managed Rules、Redirect Rules等の設定は変更しない。

## 2026-08-04: RSS取得頻度を6時間ごとへ変更

公式フィード追加後の一時的な毎時実行で、自動取得・自動生成・mainへのコミット・Cloudflare Pagesへの反映が正常に動くことを確認したため、定期実行を6時間ごとへ変更した。

### 実行時刻

日本時間（JST）:

- 00:17
- 06:17
- 12:17
- 18:17

GitHub ActionsのcronはUTC基準のため、設定値は次のとおり。

```yaml
schedule:
  - cron: '17 3,9,15,21 * * *'
```

### 変更理由

- 1日4回の更新で速報性と運用負荷のバランスを取るため
- 一時検証用の毎時実行を終了するため
- GitHub Actionsで混雑しやすい毎時0分ちょうどを避けるため
- 新着がない実行ではコミットもCloudflare Pagesの再ビルドも発生しないため

### デプロイへの影響

GitHub Actionsは6時間ごとに起動するが、新着ニュースがない場合はmainへコミットしない。そのため、Cloudflare Pagesの再ビルドも発生しない。

新着がある場合のみ、生成済みMarkdownと`data/seen.json`をコミットし、Cloudflare PagesのGit Integrationによって再デプロイする。

### 見直し条件

次の状況では頻度を再検討する。

- 更新の遅れが目立つ場合
- Cloudflare Pagesのビルド回数が無料枠へ近づいた場合
- 配信元RSSへのアクセス頻度を下げる必要が生じた場合
- Actionsの実行時間や失敗率が増えた場合
- 更新鮮度より運用コストを優先する段階へ移行した場合

## 2026-08-03: RSS取得頻度を3時間ごとへ変更

`.github/workflows/daily-news.yml` の定期実行を、1日1回から3時間ごとへ変更した。

### 実行時刻

日本時間（JST）:

- 01:17
- 04:17
- 07:17
- 10:17
- 13:17
- 16:17
- 19:17
- 22:17

GitHub ActionsのcronはUTC基準のため、設定値は次のとおり。

```yaml
schedule:
  - cron: '17 1,4,7,10,13,16,19,22 * * *'
```

### 変更理由

- 海外AI公式情報の更新を、日刊より早くサイトへ反映するため
- 1時間ごとより実行負荷を抑えながら、速報性を維持するため
- Cloudflare Pages Freeの月間ビルド枠に余裕を持たせるため

### デプロイへの影響

GitHub Actionsは3時間ごとに起動するが、新着ニュースがない場合はmainへコミットしない。そのため、Cloudflare Pagesの再ビルドも発生しない。

新着がある場合のみ、生成済みMarkdownと`data/seen.json`をコミットし、Cloudflare PagesのGit Integrationによって再デプロイする。

### 見直し条件

次の状況では頻度を再検討する。

- Cloudflare Pagesのビルド回数が無料枠へ近づいた場合
- 配信元RSSへのアクセス頻度を下げる必要が生じた場合
- Actionsの実行時間や失敗率が増えた場合
- 更新鮮度より運用コストを優先する段階へ移行した場合

## GitHub Releasesの旧記事表記を訂正する（Issue #78）

新規記事の生成は取得方式を保持して表記を選びます。既存のMarkdownは通常のニュース更新で上書きされないため、旧定型文は次の専用スクリプトで確認します。

```bash
python scripts/correct_release_wording.py --updated-at <訂正時点のタイムゾーン付きISO日時>
# 表示された候補を確認した後、ローカル差分へ適用する
python scripts/correct_release_wording.py --updated-at <同じ日時> --apply
```

既定はdry-runです。GitHub Releasesの配信元だけに対し、既知の定型文を訂正し、descriptionと抜粋の長さを制限内に保ちます。短報末尾の自動翻訳の注意書きは保ちます。`updatedAt` と読者向け `correctionHistory` を更新し、記事ID・公開日・取得日・原文・URL・翻訳状態・既読管理は維持します。`humanEdited`、既存訂正履歴、Markdown本文がある記事は保護し、対象候補全体の検証が成功してから書き込みます。既存の保護記事は別途レビューしてください。再実行で同じ訂正を重ねません。

2026-10-27のローカル訂正案は69件（LangChain 46、Ollama 15、llama.cpp 4、vLLM 4）、保護対象0件でした。これは公開済みという意味ではありません。公開前にmainの更新と競合を確認し、差分・訂正日時をレビューしてください。
