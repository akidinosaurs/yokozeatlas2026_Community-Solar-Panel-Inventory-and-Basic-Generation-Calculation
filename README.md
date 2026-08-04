# 横瀬町コミュニティ・ソーラーパネル台帳 / 発電量簡易推計

横瀬町周辺の OpenStreetMap（OSM）登録データから、太陽光設備としてタグ付けされた面ポリゴンを取得し、面積・推計容量・年間想定発電量を簡易計算する GitHub Pages 用の地図アプリです。

## 公開ページ

https://akidinosaurs.github.io/yokozeatlas2026_Community-Solar-Panel-Inventory-and-Basic-Generation-Calculation/

## スマホOSM編集アプリ構想

`mobile-osm-editor/` に、今回の台帳アプリをベースにしたスマホ向けOSM編集アプリのスターターを追加しています。

このスターターでは、OSM本番APIへ直接反映する前段階として、太陽光設備の追加候補・削除候補をスマホ地図上で作成し、差分を下書きデータとしてエクスポートできます。

OSMへの本番反映には、OSM OAuth認証、changeset作成、既存地物のversion確認、削除理由の明記が必要です。

## 主な機能

- Overpass API から太陽光設備候補の OSM ポリゴンを取得
- 取得対象タグの確認
  - `power=generator` + `generator:source=solar`
  - `power=plant` + `plant:source=solar`
  - `building=solar_panels`
  - `landuse=solar_panel`
- テーブル上で「検索条件に一致したタグ」と「OSMに登録されているタグ一覧」を表示
- 面積・推計容量・年間想定発電量・ピーク出力ごとのランキング表示
- OpenAerialMap（OAM）空撮レイヤの重ね表示
- OAMレイヤのON/OFFと透明度調整
- CSV / GeoJSON エクスポート
- 地図上の右クリック地点の座標表示・コピー

## 提出用データ

提出用データは `data/` ディレクトリに格納しています。

| 区分 | ファイル | 形式 | 内容 |
| --- | --- | --- | --- |
| メインデータ | `data/yokoze_solar_panels.geojson` | GeoJSON | 横瀬町行政界内の太陽光設備ポリゴン、OSMタグ、面積、推計容量、年間想定発電量 |
| サブデータ1 | `data/yokoze_boundary.geojson` | GeoJSON | 横瀬町の行政界ポリゴン |
| サブデータ2 | `data/yokoze_solar_panels.csv` | CSV | メインデータを表形式で確認・提出できる一覧 |
| 参考補助 | `data/yokoze_solar_tag_summary.csv` | CSV | 検索条件に一致したOSMタグ別の件数集計 |

生成条件:

- 横瀬町行政界: OSM relation `1768252`
- 太陽光設備候補タグ:
  - `power=generator` + `generator:source=solar`
  - `power=plant` + `plant:source=solar`
  - `building=solar_panels`
  - `landuse=solar_panel`
- 行政界での絞り込み: 横瀬町行政界の bbox で候補を取得し、取得ポリゴンの重心が横瀬町行政界ポリゴン内にあるものを採用
- データ生成スクリプト: `scripts/generate_submission_data.py`

## 参考データ・出典

### 空撮画像

- OpenAerialMap（OAM）タイル
  - 使用URL: `https://tiles.openaerialmap.org/62aeecdea896280006b0a6d6/0/62aeecdea896280006b0a6d7/{z}/{x}/{y}`
  - 撮影時期: 2022年度撮影データ
  - 用途: 太陽光設備ポリゴン確認のための参考背景・オーバーレイ
  - OAM / Open Imagery Network の画像は CC BY 4.0 ライセンスで公開されているデータを利用しています。

### 地図・地物データ

- OpenStreetMap contributors
- Overpass API
- Esri World Imagery
- 国土地理院 陰影起伏図
- CARTO basemaps

## 注意事項

- 本アプリの太陽光設備一覧は、OSMに登録されているタグとポリゴン形状に依存します。
- OAM空撮画像は2022年度撮影の参考画像です。現況と異なる可能性があります。
- 発電量・容量は面積からの簡易推計であり、設備仕様、方位、傾斜、影、劣化、稼働状況などは反映していません。
- 行政判断や設備診断には、現地確認および一次資料の確認が必要です。
