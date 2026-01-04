# SeatXray

<div align="right">
    <a href="README.md">English</a> | <a href="README.ja.md">日本語</a>
</div>

<div align="center">

<img src="src/assets/icon.png" width="128" alt="SeatXray Logo">

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/Flet-0.80.1-purple.svg)](https://flet.dev/)
[![Amadeus API](https://img.shields.io/badge/Amadeus-Flight%20Offers%20%26%20SeatMap-blue)](https://developers.amadeus.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-red.svg)](LICENSE)

</div>

## 概要

**SeatXray** は、航空便の空席状況を詳細に解析・可視化するためのデスクトップアプリケーションです。
通常のサイトではグレーアウトしていて指定できない座席が、「本当に人が座っている」のか、それとも「航空会社がブロックしている」のかを判別します。

Amadeus Self-Service APIを使用し、航空会社公式サイトよりも詳しい情報を取得しています。

## 主な機能

- 航空便の検索
- 各座席の空席、予約済み、ブロック中を色分けして座席表として表示
- 検索履歴・APIキーなどの一切のデータは利用者のみが保持し、開発者などに送信されることはありません
- 日英2言語に対応、将来拡張予定(翻訳していただける方募集中です)

## インストール

### Windows
Microsoft Store からダウンロードしてインストールしてください。

<a href="https://apps.microsoft.com/detail/9PB4V9J3LRQH" target="_blank">
<img src="https://get.microsoft.com/images/en-us%20dark.svg" width="200"/>
</a>

### macOS / Linux
現状はサポートしておりません。

## 使い方

### Amadeus APIキーの取得
本アプリの使用には、Amadeus for Developers のAPIキーが必要です。そのため、[公式ポータル](https://developers.amadeus.com/)にてAmadeus for Developersのアカウント登録を行い、`My Apps` から新しいアプリを作成して `API Key` と `API Secret` を取得してください。

また、すべてのデータにアクセスするには商用利用への切り替えも必要となります。本番データを取得したい場合は、アプリ詳細ページで "Get production environment" をクリックしてアップグレードを行ってください。

### アプリ設定
SeatXray を起動して設定画面を開き、取得したキーを入力して「接続テスト」を実行してください。成功ダイアログが出れば準備完了です。

### 便の検索
トップ画面で出発地、目的地、日時を入力し、検索範囲（その時間から何時間を検索範囲とするか）を選んで検索ボタンを押してください。表示されたフライトリストから気になる便をクリックすると、詳細な座席解析が始まります。

なお、検索範囲が大きい場合、人気路線だと結果を完全に取得できず、特に上位クラスの情報が漏れてしまう場合があります。国内幹線などでは検索範囲を短く設定することを推奨します。

## 開発者向け

ソースコードから実行する場合の手順です。

### 前提条件
- Python 3.12+
- Flutter (Fletのビルドに必要)

### セットアップ
```bash
# リポジトリのクローン
git clone https://github.com/ryyr-ry/seatxray.git
cd seatxray

# 依存関係のインストール
pip install -r requirements.txt

# 実行
flet run src/main.py
```

### Windows ビルド
```powershell
# 専用スクリプトによるビルド（Flet 0.80.1 のwindowsビルドにおけるバグ回避のため）
.\build_windows.ps1

# パッケージング (MSIX)
.\package_msix.ps1
```

## 免責事項

本アプリが表示するデータは Amadeus Test/Production API から取得したものですが、航空会社のリアルタイムな在庫状況と完全に一致することを保証するものではありません。

Amadeus APIの利用には所定の利用料が発生します。各APIごとに異なる無料枠や利用料が設定されておりますので、詳細はAmadeus for Developersの[pricingページ](https://developers.amadeus.com/pricing)をご確認ください。

本アプリは現状有姿で提供され、本アプリの利用に伴う料金等のAmadeus for Developersに関する諸事項、または本アプリの情報を元に行った予約やその他のトラブルについて、開発者は一切の責任を負いません。

## ライセンス

このプロジェクトは **GNU Affero General Public License v3.0 (AGPL-3.0)** の下で公開されています。
詳細は [LICENSE](LICENSE) ファイルをご確認ください。

---
Created by SeatXray/ryyr-ry
