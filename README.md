# BOCCO Webhook システム

## 概要

このシステムは、BOCCO emoの人感センサーが人の動きを検知したときに、Flaskで構築されたWebhookサーバーを通じて通知を受け取り、BOCCO emoがメッセージを発話する一連の処理を実現するものです。

複数のセンサタイプに対応し、時間帯や数値データに基づいて柔軟なメッセージを生成できます。

---

## 🌍 ネットワーク構成

```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  【自宅】                          【大学】                │
│  ┌──────────────┐                ┌──────────────┐        │
│  │ BOCCO emo    │                │ Webhook      │        │
│  │ (Wi-Fi接続)  │ ─────ngrok─── │ サーバー      │        │
│  │              │  (インターネット経由) │              │        │
│  └──────────────┘                └──────────────┘        │
│                                                           │
└─────────────────────────────────────────────────────────┘

✅ 自宅のBOCCO emo と 大学のWebhookサーバー間の通信
✅ ngrok経由でインターネットを通じて接続
✅ ファイアウォールの制限を回避可能
```

---

## 🚀 クイックスタート（5分で発話させる）

### ステップ 1️⃣ パッケージをインストール

**大学のサーバーで実行:**

```bash
pip install flask requests python-dotenv
```

### ステップ 2️⃣ Flaskサーバーを起動

**大学のサーバーで実行:**

```bash
python bocco_webhook.py
```

**出力例:**
```
 * Running on http://0.0.0.0:5001
```

### ステップ 3️⃣ 別のターミナルでngrokを起動

**大学のサーバーで実行:**

```bash
ngrok http 5001
```

**出力例:**
```
Forwarding                    https://abcd1234.ngrok-free.app -> http://localhost:5001
```

**このURLをメモします！** ← 重要 🔗

### ステップ 4️⃣ register_webhook.py のURLを更新

**大学のサーバーで実行:**

`register_webhook.py`を開いて、以下の行を編集します：

```python
webhook_url = "https://abcd1234.ngrok-free.app/webhook"  # ← さっきのngrok URLを貼り付け
```

### ステップ 5️⃣ Webhookを登録

**大学のサーバーで実行:**

```bash
python register_webhook.py
```

**成功出力:**
```
✅ 新しいアクセストークン: eyJ0eXAiOiJKV1QiLCJhbGci...
✅ .env ファイルを更新しました
📝 Webhook登録中...
Webhook登録: 201 {"description":"my webhook",...}
📝 イベント登録中...
イベント登録: 200 {"description":"my webhook","events":["human_sensor.detected"],...}
✅ すべての登録に成功しました！
```

### ステップ 6️⃣ 自宅のBOCCO emoの前を通る

✅ **BOCCO emoが発話します！**

**大学のサーバーのターミナルに表示される:**
```
INFO:root:Webhook受信: {'event': 'human_sensor.detected', ...}
INFO:root:解析結果 - sensor_type: human_sensor, event_type: detected
INFO:root:✓ BOCCO発話成功: おかえりなさい！
```

---

## 🔄 通信フロー

```
【自宅】                        【インターネット】              【大学】
BOCCO emo センサ検知
   ↓
   │ (センサイベント発生)
   ↓
BOCCOプラットフォームに通知
   ↓
   │ (Webhook URL に POST)
   ↓ ─────────────────────────→ ngrok トンネル ────→ Flaskサーバー
                                                        ↓
                                          sensor_handler.py
                                                        ↓
                                          BOCCO API にメッセージ送信
                                                        ↓
   ← ─────────────────────────── 自宅のBOCCOに送信 ← ←
   ↓
BOCCO emo が発話 ✅
```

---

## 🔧 異なるネットワーク間でのセットアップ

### ネットワーク構成

| 項目 | 場所 | 役割 |
|-----|------|------|
| BOCCO emo | 自宅 | センサイベントを発生させる |
| Webhookサーバー | 大学 | イベントを受け取り、メッセージを送信 |
| ngrok | クラウド | 両者の通信をトンネリング |

### セットアップ手順（大学のサーバー）

1. **依存パッケージをインストール**

```bash
pip install flask requests python-dotenv
```

2. **Flaskサーバーを起動**

```bash
python bocco_webhook.py
```

3. **ngrokを起動（別ターミナル）**

```bash
ngrok http 5001
```

4. **Webhook URLを設定して登録**

```python
# register_webhook.py
webhook_url = "https://xxxx.ngrok-free.app/webhook"
```

```bash
python register_webhook.py
```

---

## 💾 必要なファイル

大学のサーバーに必要なファイル：

```
bocco_webhook/
├── .env                    # BOCCO認証情報
├── bocco_webhook.py        # Webhookサーバー
├── sensor_handler.py       # センサ処理
├── register_webhook.py     # Webhook登録
└── requirements.txt        # 依存パッケージ
```

---

## ⚠️ 注意事項

### ngrok URLの有効期限

```
⚠️ ngrokは起動するたびにURLが変わります
```

起動するたびに以下を実行してください：

1. ngrokを起動
2. 新しいURLをコピー
3. `register_webhook.py`のURLを更新
4. `python register_webhook.py`を実行

または、**ngrok有料版を使う**と固定URLが使用できます。

---

## 🔐 セキュリティ

```
✅ ngrok は HTTPS (暗号化通信) を使用
✅ BOCCOの認証トークンで保護
✅ 不正アクセスの心配はない
```

---

## 機能

- ✅ BOCCO emoの複数センサイベントを受信（人感、温度、湿度、ドアセンサーなど）
- ✅ 時間帯に応じた動的メッセージ生成（朝・昼・夜で異なるあいさつ）
- ✅ センサ値を活用した柔軟な応答（温度・湿度の変化に対応）
- ✅ モジュール化された設計で容易に拡張可能
- ✅ 詳細なログ出力でトラブルシューティングが簡単
- ✅ **異なるネットワーク間での通信に対応**

---

## 使用技術

- **Python 3.13**
- **Flask** - Webhookサーバー
- **requests** - HTTP通信
- **python-dotenv** - 環境変数管理
- **ngrok** - トンネリング（異なるネットワーク間の通信）

---

## フォルダ構成

```
bocco_webhook/
├── .env                              # 環境変数（秘密情報）
├── bocco_webhook.py                  # Flaskサーバー本体
├── sensor_handler.py                 # センサイベント処理
├── register_webhook.py               # Webhook登録スクリプト
├── webhook_test.py                   # Webhook動作テスト
├── requirements.txt                  # 依存パッケージ
└── README.md                         # このファイル
```

---

## 環境設定

### 1. .envファイルの作成（大学のサーバー）

`.env`ファイルを作成し、以下の内容を記述します。

```env
BOCCO_ROOM_ID=あなたのBOCCOルームID
BOCCO_ACCESS_TOKEN=あなたのアクセストークン
BOCCO_REFRESH_TOKEN=あなたのリフレッシュトークン
FLASK_ENV=development
```

---

## 動作確認

### 基本動作テスト

自宅のBOCCO emoの人感センサーの前を通ると、以下の処理が実行されます。

1. ✅ BOCCO emoがセンサイベントを発生
2. ✅ Webhookサーバーがインターネット経由でイベントを受信
3. ✅ メッセージを生成
4. ✅ BOCCO emoにメッセージを送信
5. ✅ BOCCO emoがメッセージを発話

**ログ出力例（大学のサーバーのターミナル）:**
```
INFO:root:Webhook受信: {'event': 'human_sensor.detected', ...}
INFO:root:解析結果 - sensor_type: human_sensor, event_type: detected
INFO:root:✓ BOCCO発話成功: おかえりなさい！
```

---

## ファイル詳細

### bocco_webhook.py

メインのWebhookサーバー。

**動作:**
1. `/webhook`エンドポイントでセンサイベントを受信
2. `SensorEventHandler`を使ってイベントを処理
3. 該当するメッセージがあれば、BOCCO APIに送信
4. `/health`エンドポイントでサーバーの健康状態を確認

### sensor_handler.py

センサイベント処理とメッセージ生成を一元管理するモジュール。

**対応センサタイプ:**

| センサタイプ | イベント | 応答例 |
|-------------|---------|-------|
| `human_sensor` | `detected` | おかえりなさい！（時間帯による） |
| `human_sensor` | `left` | いってらっしゃい！ |
| `temperature` | `changed` | 暑いですね。温度は30度です。 |
| `humidity` | `changed` | 湿度が高いですね。75パーセントです。 |
| `door` | `opened` | ドアが開きました。 |
| `door` | `closed` | ドアが閉じました。 |

### register_webhook.py

BOCCO Platform APIにWebhookを登録するスクリプト。

**処理:**
1. リフレッシュトークンを使ってアクセストークンを取得
2. Webhook URLを登録
3. リッスンするイベントタイプを指定
4. `.env`ファイルを自動更新

---

## トラブルシューティング

### Webhookが届かない

- ✅ ngrokが起動しているか確認
- ✅ ngrok URLが正しく`register_webhook.py`に設定されているか確認
- ✅ **`/webhook`が末尾に付いているか確認**（重要！）
- ✅ Flaskサーバーが起動しているか確認
- ✅ ngrokセッションが切れていないか確認（URLは起動するたびに変わる）

### BOCCO emoがしゃべらない

- ✅ `BOCCO_ROOM_ID`と`BOCCO_ACCESS_TOKEN`が`.env`に正しく設定されているか確認
- ✅ アクセストークンの有効期限を確認
  - `python register_webhook.py`を実行してトークンをリフレッシュ
- ✅ BOCCOの音声設定がONになっているか確認

### トークンエラー (401 Unauthorized)

```
ERROR:root:❌ BOCCO発話失敗: アクセストークンが無効です
```

この場合、以下を実行してトークンを更新してください：

```bash
python register_webhook.py
```

---

## セキュリティ注意事項

- 🔒 `.env`ファイルは**絶対にGitにコミットしない**
- 🔒 `.gitignore`に以下を追加してください

```
.env
.env.local
*.json
__pycache__/
*.pyc
```

- 🔒 ngrok URLを他人と共有しないこと
- 🔒 BOCCOの認証情報は秘密に保つこと

---

## ライセンス

このプロジェクトは個人利用を想定しています。

---

## 参考リンク

- [BOCCO emo Platform API ドキュメント](https://platform-api.bocco.me/docs)
- [ngrok Documentation](https://ngrok.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)