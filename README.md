# 横瀬町コミュニティ・ソーラーパネル台帳 / 発電量簡易推計

横瀬町周辺の OpenStreetMap（OSM）登録データから、太陽光設備としてタグ付けされた面ポリゴンを取得し、面積・推計容量・年間想定発電量を簡易計算する GitHub Pages 用の地図アプリです。

## 公開ページ

https://akidinosaurs.github.io/yokozeatlas2026_Community-Solar-Panel-Inventory-and-Basic-Generation-Calculation/

## 主な機能

- Overpass API から太陽光設備候補の OSM ポリゴンを取得
- 取得対象タグの確認
  - `power=generator` + `generator:source=solar`
  - `power=plant` + `plant:source=solar`
  - `building=solar_panels`
  - `landuse=solar_panel`
- テーブル上で「検索条件に一致したタグ」と「OSMに登録されているタグ一覧」を表示
- OpenAerialMap（OAM）空撮レイヤの重ね表示
- OAMレイヤのON/OFFと透明度調整
- CSV / GeoJSON エクスポート

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
