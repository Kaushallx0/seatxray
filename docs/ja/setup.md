# SeatXray ⚡️ セットアップガイド

SeatXray を利用するためには、Amadeus API キーの取得と設定が必要です。以下の手順に従ってください。

## 1. Amadeus Developers アカウントの作成
1. [Amadeus for Developers](https://developers.amadeus.com/) にアクセスします。
2. "Self-Service APIs" のアカウントを無料で作成（Sign Up）します。

## 2. アプリの登録とキーの取得
1. ログイン後、[My Apps](https://developers.amadeus.com/my-apps) ページを開きます。
2. "Create New App" をクリックし、アプリ名（例: `MySeatXray`）を入力して保存します。
3. アプリ詳細ページで **"Get production environment"** をクリックしてアップグレードを開始します。

### 本番環境（Production）へのリクエスト手順
本番環境のキーを取得するには、以下の4ステップを完了させる必要があります。
1. **Personal & Billing info**: 請求先情報を入力します。
2. **Payment method**: 支払い情報を登録します。
3. **Sign agreement & confirm**: 利用規約を確認し、同意します。

> アプリを本番環境へ移行する際、契約の締結と支払い情報の登録が必要になります。無料枠を超過しない限り請求が発生することはありません。

### APIの検証に関する質問
申請の途中で、追加の審査（Validation）が必要なAPIを使用しているか尋ねられます。

**"Does your app use an API that requires validation?"**

これには **「No」** を選択して進めてください。SeatXrayは検索と座席表示のみを行うアプリであり、追加の審査が必要な予約機能等は使用していないため、すぐに本番環境のキーが発行されます。

4. 手続き完了後、My Apps ページで **API Key** と **API Secret** をコピーします。

## 3. アプリへの設定
1. SeatXray を起動します。
2. 右上の設定アイコン ⚙️ をクリックします。
3. 取得した `API Key` と `API Secret` を入力します。
4. 「保存」をクリックして「接続テスト」を実行してください。

## 注意事項
- **FREE REQUEST QUOTA** が設定されており、月ごとの回数制限（検索2,000回、座席表1,000回等）が存在します。詳細は[公式料金ページ](https://developers.amadeus.com/pricing)をご確認ください。
- 取得したキーはご自身のデバイスや指定した保存先にのみ記録され、外部（開発元など）に送信・収集されることはありません。
