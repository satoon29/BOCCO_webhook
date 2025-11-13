# BOCCO Webhook システム

## 概要

このシステムは、BOCCO emoの人感センサーが人の動きを検知したときに、Flaskで構築されたWebhookサーバーを通じて通知を受け取り、BOCCO emoがメッセージを発話する一連の処理を実現するものです。Firebaseと連携して絵文字による感情記録を取得し、ユーザーの感情に応じた応答も可能になります。

---

## 機能

- BOCCO emoの人感センサーイベントを受信
- Firebaseから当日の感情記録（絵文字）を取得
- 感情データに基づいてメッセージを生成
- BOCCO emoが音声でメッセージを発話

---

## 使用技術

- **Python 3.13**
- **Flask** - Webhookサーバー
- **Firebase Admin SDK** - Firestore連携
- **requests** - HTTP通信
- **python-dotenv** - 環境変数管理
- **ngrok** - ローカルホストの外部公開

---

## フォルダ構成

```
bocco_webhook/
├── .env                              # 環境変数（秘密情報）
├── bocco_webhook.py                  # Flaskサーバー本体
├── register_webhook.py               # Webhook登録スクリプト
├── choose_messege.py                 # 感情分析・メッセージ選択
├── firebaseTest.py                   # Firebase接続テスト
├── webhook_test.py                   # Webhook動作テスト
├── emoji-test-aad3a-firebase-adminsdk-*.json  # Firebase認証鍵
└── README.md                         # このファイル
```

---

## 環境設定

### 1. .envファイルの作成

プロジェクトルートに`.env`ファイルを作成し、以下の内容を記述します。

```env
BOCCO_ROOM_ID=あなたのBOCCOルームID
BOCCO_ACCESS_TOKEN=あなたのアクセストークン
BOCCO_REFRESH_TOKEN=あなたのリフレッシュトークン

```

### 2. Firebase認証ファイルの配置

Firebase Admin SDKの認証JSONファイルをプロジェクトルートに配置します。

---

## セットアップ手順

### 1. 依存パッケージのインストール

```bash
pip install flask requests python-dotenv firebase-admin
```

### 2. Flaskサーバーの起動

```bash
python bocco_webhook.py
```

サーバーがポート5000で起動します。

### 3. ngrokでローカルサーバーを外部公開

別のターミナルで以下を実行します。

```bash
ngrok http 5000
```

表示されたForwarding URL（例：`https://xxxx.ngrok-free.app`）をコピーします。

### 4. Webhookの登録

`register_webhook.py`を編集し、`webhook_url`を先ほどのngrok URLに変更します。

```python
webhook_url = "https://xxxx.ngrok-free.app/webhook"
```

その後、スクリプトを実行します。

```bash
python register_webhook.py
```

成功すると以下のような出力が表示されます。

```
新しいアクセストークン: eyJ0eXAiOiJKV1QiLCJhbGci...
Webhook登録: 201 {"description":"my webhook",...}
イベント登録: 200 {"description":"my webhook","events":["human_sensor.detected"],...}
```

---

## 動作確認

### 1. 基本動作テスト

BOCCO emoの人感センサーの前を通ると、以下の処理が実行されます。

1. Webhookサーバーがイベントを受信
2. Firebaseから当日の感情記録を取得
3. 感情データに基づいてメッセージを生成
4. BOCCO emoがメッセージを発話

### 2. Firebaseテスト

```bash
python firebaseTest.py
```

当日のFirestoreデータが正しく取得できることを確認します。

### 3. Webhookテスト

```bash
python webhook_test.py
```

ブラウザで `http://localhost:5001/webhook` にアクセスし、「✅ Flaskは動いてるよ！」が表示されることを確認します。

---

## ファイル詳細

### bocco_webhook.py

メインのWebhookサーバー。人感センサーイベントを受信し、Firebaseから感情データを取得してBOCCO emoに発話させます。

### register_webhook.py

BOCCO Platform APIにWebhookを登録するスクリプト。リフレッシュトークンを使ってアクセストークンを取得し、Webhook URLとイベントタイプを登録します。

### choose_messege.py

感情分析関数群。絵文字からvalence（感情価）とarousal（覚醒度）を計算し、適切なメッセージを選択します。

- `valence_emoji()`: 感情価を-1〜1で返す
- `arousal_emoji()`: 覚醒度を-1〜1で返す
- `choose_message()`: 絵文字リストから適切なメッセージを選択

### firebaseTest.py

Firestore接続テスト用スクリプト。当日の'day'フィールドが一致するドキュメントを取得して表示します。

---

## トラブルシューティング

### Webhookが届かない

- ngrokのURLが正しく登録されているか確認
- Flaskサーバーが起動しているか確認
- ngrokセッションが切れていないか確認

### Firebaseからデータが取得できない

- 認証JSONファイルのパスが正しいか確認
- `day`フィールドの形式が`YYYY/MM/DD`になっているか確認
- タイムゾーンが日本時間(JST)に設定されているか確認

### BOCCO emoがしゃべらない

- `BOCCO_ROOM_ID`と`BOCCO_ACCESS_TOKEN`が正しいか確認
- アクセストークンの有効期限が切れていないか確認（リフレッシュが必要）

---

## セキュリティ注意事項

- `.env`ファイルや認証JSONファイルは**絶対にGitにコミットしない**
- `.gitignore`に以下を追加してください

```
.env
*firebase-adminsdk*.json
```

---

## ライセンス

このプロジェクトは個人利用を想定しています。

---

## 参考リンク

- [BOCCO emo Platform API ドキュメント](https://platform-api.bocco.me/docs)
- [Firebase Admin SDK for Python](https://firebase.google.com/docs/admin/setup)
- [ngrok Documentation](https://ngrok.com/docs)