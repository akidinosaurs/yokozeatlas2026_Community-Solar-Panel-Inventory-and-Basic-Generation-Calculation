# 横瀬町ソーラーパネル OSM編集スマホアプリ スターター

このディレクトリは、既存の横瀬町ソーラーパネル台帳をベースにした、スマホ向けOSM編集アプリの初期実装です。

## 目的

横瀬町内の太陽光設備について、現地確認をしながら次の作業を行うためのアプリを目指します。

- ソーラーパネル地物の追加候補を作る
- 既存OSM地物の削除候補を記録する
- OSM反映前に変更差分を確認・エクスポートする
- 将来的にOSM OAuth認証を通してOSM APIへ反映する

## 現在できること

- `../data/yokoze_solar_panels.geojson` を読み込み、既存ソーラーパネルを地図表示
- スマホ向けの下部操作パネル
- 追加モード
  - 地図をタップして、指定面積の正方形ポリゴンを下書き作成
  - OSM用タグ候補を付与
- 削除モード
  - 既存ポリゴンをタップして削除候補として記録
- 下書きエクスポート
  - `yokoze-solar-osm-draft.geojson`
  - `yokoze-solar-osm-additions.osc`
  - `yokoze-solar-osm-deletions-review.json`

## まだ本番OSMへ直接アップロードしない理由

OSM編集には、OSM APIのOAuth認証、changeset作成、編集コメント、既存地物のversion確認、削除理由の明記が必要です。

特に削除は影響が大きいため、このスターターでは本番アップロードを無効にし、まずは差分を確認できる下書き出力までにしています。

## 次に実装すること

1. OSM OAuth 2.0 / PKCE の設定
2. OSM APIの開発用サーバーでアップロードテスト
3. 既存wayの最新version取得
4. changesetコメント・source・review_requestedタグの固定
5. 追加・削除前の確認画面
6. OSM本番APIへのアップロード解放

## 差分検証の方法

この実装は `codex/mobile-osm-editor-starter` ブランチで管理します。

GitHub上でForkまたはPull Requestを使うと、元のmainとの差分を後から確認できます。
