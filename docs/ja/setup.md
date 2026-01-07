# SeatXray セットアップガイド

SeatXrayを利用するためには、Amadeus Self-Service APIのAPI KeyとAPI Secretの取得と設定が必要です。以下の手順に従ってください。

## 1. Amadeus Developers アカウントの作成

1. [Amadeus for Developers](https://developers.amadeus.com/) にアクセスします。
2. Self-Service APIsのアカウント作成ページ（Sign Up）へ進み、アカウントを作成します。

## 2. アプリの登録とキーの取得

1. ログイン後、[My Apps](https://developers.amadeus.com/my-apps) ページを開いて登録済みアプリ一覧を表示します。
2. "Create New App" をクリックし、`MySeatXray` などの判別しやすいアプリ名を入力して保存します。
3. アプリ詳細ページに移動し、App KeysよりAPI KeyとAPI Secretをコピーして控えてください。
すべてのデータにアクセスしたい場合は、**"Get production environment"** をクリックしてアップグレードを行ってください。

### 本番環境（Production）へのリクエスト手順

本番環境のキーを取得するには、以下の情報を入力して手続きを完了させる必要があります。
1. 請求先情報（Personal & Billing info）を入力
2. 支払い情報（Payment method）を登録
3. 利用規約を確認し、内容に同意して契約を締結

> アプリを本番環境へ移行する際、契約の締結と支払い情報の登録が必要になりますが、無料枠を超過しない限り請求が発生することはありません。

申請の途中で `Does your app use an API that requires validation?` と尋ねられた場合は、**No** を選択して進めてください。
SeatXrayは検索と座席表示のみを行うアプリであり、追加の審査が必要な予約機能等は使用していないため、通常は72時間以内にキーが発行されます。

4. 手続きを完了後、My Apps ページに表示される `API Key` と `API Secret` をコピーして控えておきます。

## 3. アプリでの設定

1. SeatXrayを起動して初期画面を表示します。
2. 画面左側(Windows版)または右下(Android版)の設定アイコンをクリックして設定画面を開きます。
3. 先ほど取得した `API Key` と `API Secret` をそれぞれの入力欄に貼り付けます。
4. 「保存して接続テスト」ボタンをクリックし、正常に通信できることを確認します。

## 注意事項
Amadeus Self-Service APIには月ごとの無料利用枠（FREE REQUEST QUOTA）が設定されており、検索や座席表取得の回数に制限があります。
取得したキーはご自身のデバイスや指定した保存先にのみ記録され、外部へ送信されたり収集されたりすることはありません。
詳細は[公式料金ページ](https://developers.amadeus.com/pricing)をご確認ください。
