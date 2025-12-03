# BOCCO Webhook システム

## 概要

このシステムは、BOCCO emoの人感センサーが人の動きを検知したときに、Flaskで構築されたWebhookサーバーを通じて通知を受け取り、BOCCO emoがメッセージを発話する一連の処理を実現するものです。

複数のセンサタイプに対応し、時間帯や数値データに基づいて柔軟なメッセージを生成できます。

さらに、**Firebase から取得したユーザーの感情データを分析**し、その日の感情に寄り添ったメッセージを動的に生成します。

---

## 🚀 クイックスタート（完全セットアップガイド）

### ステップ 1️⃣ 事前準備

#### 1-1. 部屋情報の確認

まず、あなたの BOCCO emoの部屋情報を取得します：

```bash
python get_room_info.py
```

**出力例:**
```
部屋 #1
================================================================================
  名前: bocco05
  UUID: 388625ac-1753-48b8-9c91-0a526f861a95

部屋 #2
================================================================================
  名前: bocco02
  UUID: 9ca852fa-44eb-4d3c-894e-c7203a66bd85

部屋 #3
================================================================================
  名前: bocco01
  UUID: 0c070376-cce9-451d-b2b3-5555e7e839ce
```

これをメモしておいてください。この情報を使って `.env` を設定します。

#### 1-2. Firebase 認証ファイルの確認

`peak_value_estimator.py`の以下の行を、あなたの Firebase 認証ファイルのパスに変更してください：

```python
cred = credentials.Certificate('emoji-test-aad3a-firebase-adminsdk-fbsvc-009abfa2ad.json')
```

---

### ステップ 2️⃣ 仮想環境の構築

#### PowerShell の場合

```powershell
# 仮想環境を作成
python -m venv .venv

# 仮想環境を有効化
.venv\Scripts\Activate.ps1
```

**エラーが出た場合（実行ポリシーエラー）:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# その後、もう一度実行
.venv\Scripts\Activate.ps1
```

#### Command Prompt の場合

```cmd
# 仮想環境を作成
python -m venv .venv

# 仮想環境を有効化
.venv\Scripts\activate.bat
```

---

### ステップ 3️⃣ 依存パッケージをインストール

仮想環境が有効な状態で実行：

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**確認:**
```bash
pip list
```

---

### ステップ 4️⃣ .env ファイルの作成・編集

`.env` ファイルを以下の内容で作成・編集します：

```env
BOCCO_ACCESS_TOKEN="あなたのアクセストークン"
BOCCO_REFRESH_TOKEN="db43b831-d523-4f4e-9f81-72e243b8be3c"

# Room ID と room 名のマッピング（JSON形式）
# ステップ1で確認した UUID と名前を使用
BOCCO_ROOM_USER_MAPPING='{"388625ac-1753-48b8-9c91-0a526f861a95": "bocco05", "9ca852fa-44eb-4d3c-894e-c7203a66bd85": "bocco02", "0c070376-cce9-451d-b2b3-5555e7e839ce": "bocco01"}'

FLASK_ENV=development
```

**重要:** `BOCCO_ROOM_USER_MAPPING` の `bocco05`, `bocco02`, `bocco01` をあなたの部屋名に変更してください。

---

### ステップ 5️⃣ Flaskサーバーを起動

**ターミナル1（Flaskサーバー用）:**

```bash
python bocco_webhook.py
```

**出力例:**
```
 * Running on http://0.0.0.0:5001
```

サーバーが起動したら、ターミナルはそのまま開いておいてください。

---

### ステップ 6️⃣ ngrok で localhost を外部公開

**ターミナル2（ngrok用）:** 新しいターミナルウィンドウを開いて実行

```bash
ngrok http 5001
```

**出力例:**
```
Session Status                online
Forwarding                    https://abcd1234.ngrok-free.app -> http://localhost:5001
```

**このngrok URLをコピーしてメモします:** `https://abcd1234.ngrok-free.app`

---

### ステップ 7️⃣ Webhook URLを設定

`register_webhook.py` を開いて、以下の行を編集します：

```python
webhook_url = "https://abcd1234.ngrok-free.app/webhook"  # ← ステップ6のngrok URLに変更
```

---

### ステップ 8️⃣ Webhook を登録

**ターミナル3（Webhook登録用）:** 新しいターミナルウィンドウを開いて実行

仮想環境を有効化してから実行：

```powershell
# PowerShell
.venv\Scripts\Activate.ps1

# または Command Prompt
.venv\Scripts\activate.bat

# Webhook登録スクリプト実行
python register_webhook.py
```

**成功出力:**
```
[OK] 新しいアクセストークン: eyJ0eXAiOiJKV1QiLCJhbGci...
[OK] .env ファイルを更新しました
[INFO] Webhook登録中...
Webhook登録: 201 {...}
[INFO] イベント登録中...
イベント登録: 200 {...}
[OK] すべての登録に成功しました！
```

---

### ステップ 9️⃣ BOCCO emo の前を通る

✅ **これでセットアップ完了！**

BOCCO emoの人感センサーの前を通ると：

1. ✅ Webhookサーバーがイベントを受信
2. ✅ Firebaseから本日の感情を推定
3. ✅ 感情に基づいたメッセージを生成
4. ✅ BOCCO emoがメッセージを発話

**ターミナル1に表示されるログ:**
```
2025-11-13 19:00:00 - INFO - Webhook受信: {'uuid': '388625ac-1753-48b8-9c91-0a526f861a95', 'event': 'human_sensor.detected', ...}
2025-11-13 19:00:00 - INFO - 解析結果 - room_id: 388625ac-1753-48b8-9c91-0a526f861a95, sensor_type: human_sensor, event_type: detected
2025-11-13 19:00:00 - INFO - [OK] Room ID 388625ac-1753-48b8-9c91-0a526f861a95 → User ID: bocco05
2025-11-13 19:00:00 - INFO - [OK] 本日の推定感情 (User: bocco05): Positive
2025-11-13 19:00:00 - INFO - [OK] BOCCO発話成功 (Room: 388625ac-1753-48b8-9c91-0a526f861a95, User: bocco05): おかえりなさい！素敵な表情ですね。その調子で頑張ってください！
```

---

## 機能

- ✅ BOCCO emoの複数センサイベントを受信（人感、温度、湿度、ドアセンサーなど）
- ✅ 時間帯に応じた動的メッセージ生成（朝・昼・夜で異なるあいさつ）
- ✅ **Firebaseから感情データを取得し、本日の感情を推定**
- ✅ **感情に基づいた対応メッセージ（ポジティブなら褒める、ネガティブなら励ます）**
- ✅ センサ値を活用した柔軟な応答（温度・湿度の変化に対応）
- ✅ モジュール化された設計で容易に拡張可能
- ✅ 詳細なログ出力でトラブルシューティングが簡単
- ✅ トークン無効時の自動更新と再試行

---

## 使用技術

- **Python 3.13**
- **Flask** - Webhookサーバー
- **requests** - HTTP通信
- **python-dotenv** - 環境変数管理
- **pandas** - データ分析
- **firebase-admin** - Firebase 連携
- **ngrok** - ローカルホストの外部公開

---

## フォルダ構成

```
bocco_webhook/
├── .env                              # 環境変数（秘密情報）
├── requirements.txt                  # 依存パッケージ
├── bocco_webhook.py                  # Flaskサーバー本体
├── sensor_handler.py                 # センサイベント処理
├── peak_value_estimator.py           # 感情推定アルゴリズム
├── register_webhook.py               # Webhook登録スクリプト
├── webhook_test.py                   # Webhook動作テスト
└── README.md                         # このファイル
```

---

## 環境設定

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. .envファイルの作成

プロジェクトルートに`.env`ファイルを作成し、以下の内容を記述します。

```env
BOCCO_ACCESS_TOKEN=あなたのアクセストークン
BOCCO_REFRESH_TOKEN=あなたのリフレッシュトークン

# Room ID と room 名のマッピング（JSON形式）
# 形式: {"room_uuid": "room_name"}
BOCCO_ROOM_USER_MAPPING='{"room_uuid_1": "user_name_1", "room_uuid_2": "user_name_2"}'

FLASK_ENV=development
```

**Room-User マッピングの取得方法:**

```bash
# get_room_info.py を実行して、room 情報を確認
python get_room_info.py
```

出力例から、以下の形式でマッピングを作成してください：

```json
{
  "388625ac-1753-48b8-9c91-0a526f861a95": "bocco05",
  "9ca852fa-44eb-4d3c-894e-c7203a66bd85": "bocco02",
  "0c070376-cce9-451d-b2b3-5555e7e839ce": "bocco01"
}
```

### 3. Firebase 認証ファイルの設定

`peak_value_estimator.py`内の以下の行を、あなたの Firebase 認証ファイルのパスに変更してください：

```python
cred = credentials.Certificate('emoji-test-aad3a-firebase-adminsdk-fbsvc-009abfa2ad.json')
```

---

## セットアップ手順（詳細版）

### 1. 仮想環境の構築

```powershell
# PowerShell の場合
python -m venv .venv
.venv\Scripts\Activate.ps1

# Command Prompt の場合
python -m venv .venv
.venv\Scripts\activate.bat
```

### 2. 依存パッケージのインストール

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**インストール確認:**
```bash
pip list
```

### 3. Flaskサーバーの起動

```bash
python bocco_webhook.py
```

サーバーがポート5001で起動します。

### 4. ngrokでローカルサーバーを外部公開

別のターミナルで以下を実行します（仮想環境の有効化は不要）。

```bash
ngrok http 5001
```

表示されたForwarding URL（例：`https://xxxx.ngrok-free.app`）をコピーします。

### 5. Webhookの登録

`register_webhook.py`を編集し、以下の行を先ほどのngrok URLに変更します。

```python
webhook_url = "https://xxxx.ngrok-free.app/webhook"  # ← このURLを変更
```

その後、スクリプトを実行します（仮想環境を有効化した状態で実行）。

```bash
python register_webhook.py
```

成功すると以下のような出力が表示されます。

```
[OK] 新しいアクセストークン: eyJ0eXAiOiJKV1QiLCJhbGci...
[OK] .env ファイルを更新しました
[INFO] Webhook登録中...
Webhook登録: 201 {...}
[INFO] イベント登録中...
イベント登録: 200 {...}
[OK] すべての登録に成功しました！
```

---

## 動作確認

### 基本動作テスト

自宅のBOCCO emoの人感センサーの前を通ると、以下の処理が実行されます。

1. ✅ BOCCO emoがセンサイベントを発生
2. ✅ Webhookサーバーがインターネット経由でイベントを受信
3. ✅ ローカルマッピングからユーザーIDを取得（高速）
4. ✅ Firebaseから本日の感情データを取得して推定
5. ✅ 推定感情に基づいたメッセージを生成
6. ✅ BOCCO emoがメッセージを発話

**ログ出力例:**
```
INFO - Webhook受信: {'uuid': '388625ac-1753-48b8-9c91-0a526f861a95', 'event': 'human_sensor.detected', ...}
INFO - 解析結果 - room_id: 388625ac-1753-48b8-9c91-0a526f861a95, sensor_type: human_sensor, event_type: detected
INFO - [OK] Room ID 388625ac-1753-48b8-9c91-0a526f861a95 → User ID: bocco05
INFO - [OK] 本日の推定感情 (User: bocco05): Positive
INFO - [OK] BOCCO発話成功 (Room: 388625ac-1753-48b8-9c91-0a526f861a95, User: bocco05): おかえりなさい！素敵な表情ですね。その調子で頑張ってください！
```

### ヘルスチェック

サーバーが正常に動作しているか確認できます：

```bash
curl http://localhost:5001/health
```

**レスポンス:**
```json
{"status": "healthy"}
```

---

## ファイル詳細

### bocco_webhook.py

メインのWebhookサーバー。

**動作:**
1. `/webhook`エンドポイントでセンサイベントを受信
2. webhook の `uuid` から room_id を抽出
3. ローカルマッピング（`.env`）から user_id を高速取得
4. `SensorEventHandler`を使ってイベントを処理
5. 該当するメッセージがあれば、BOCCO APIに送信
6. `/health`エンドポイントでサーバーの健康状態を確認

### sensor_handler.py

センサイベント処理とメッセージ生成を一元管理するモジュール。

**主な機能:**
- センサイベント受信
- Firebase から感情推定（`peak_value_estimator.py`を使用）
- 感情に基づいたメッセージ生成
- トークン無効時の自動更新と再試行

**対応センサタイプ:**
| センサタイプ | イベント | ポジティブな日 | ネガティブな日 | ニュートラルな日 |
|-------------|---------|-----------|-----------|-----------|
| `human_sensor` | `detected` | ほめるメッセージ | 励ますメッセージ | 通常のあいさつ |
| `human_sensor` | `left` | いってらっしゃい！ | いってらっしゃい！ | いってらっしゃい！ |
| `temperature` | `changed` | 温度に応じたメッセージ | 温度に応じたメッセージ | 温度に応じたメッセージ |
| `humidity` | `changed` | 湿度に応じたメッセージ | 湿度に応じたメッセージ | 湿度に応じたメッセージ |
| `door` | `opened` / `closed` | ドア開閉メッセージ | ドア開閉メッセージ | ドア開閉メッセージ |

### peak_value_estimator.py

Firebase から感情データを取得し、**ピーク値法**で本日の感情を推定するモジュール。

**ピーク値法:**
1. その日の全感情記録（Valence値）を取得
2. Valence値を正規化（[-1, 1]の範囲）
3. 正規化後の絶対値が最大のものを採用
4. その値の符号で感情を判定（Positive/Neutral/Negative）

**使用例:**
```python
from peak_value_estimator import estimate_single_day
from datetime import date

# 本日の感情を推定
emotion = estimate_single_day(
    user_id='bocco05',
    target_date=date.today(),
    verbose=True
)
```

### register_webhook.py

BOCCO Platform APIにWebhookを登録するスクリプト。

**処理:**
1. リフレッシュトークンを使ってアクセストークンを取得
2. 新しいトークンを`.env`ファイルに保存
3. Webhook URLを登録
4. リッスンするイベントタイプを指定（`human_sensor.detected`）

**使用方法:**
```bash
python register_webhook.py
```

### get_room_info.py

BOCCO の部屋情報とセンサ情報を取得するツール。

**使用方法:**
```bash
# 通常表示
python get_room_info.py

# JSON形式で表示
python get_room_info.py --json

# ファイルに保存
python get_room_info.py --save room_info.json
```

### webhook_test.py

Webhook動作確認用スクリプト。

**使用方法:**
```bash
python webhook_test.py
```

ブラウザで `http://localhost:5001/webhook` にアクセスしてテスト。

---

## 本番環境への対応

### ⚠️ 開発環境vs本番環境

**開発環境（現在）:**
- Flask開発サーバーを使用
- デバッグモード有効

**本番環境への対応:**

1. **Gunicornをインストール**

```bash
pip install gunicorn
```

2. **Gunicornで起動**

```bash
gunicorn -w 4 -b 0.0.0.0:5001 bocco_webhook:app
```

3. **.env に設定を追加**

```env
FLASK_ENV=production
```

4. **Nginxでリバースプロキシ設定**（詳細は別途参照）

---

## トラブルシューティング

### バージョン互換性エラー

```
ValueError: numpy.dtype size changed, may indicate binary incompatibility
```

**解決方法:**

```powershell
# 1. 仮想環境を削除（PowerShell）
Remove-Item -Recurse -Force .venv

# または（Command Prompt）
rmdir /s /q .venv

# 2. 新しい仮想環境を作成
python -m venv .venv

# 3. 仮想環境を有効化
.venv\Scripts\Activate.ps1

# 4. 再インストール
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 実行ポリシーエラー

```
PowerShell スクリプトを実行できないため、ファイル .venv\Scripts\Activate.ps1 を読み込むことができません。
```

**解決方法:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ModuleNotFoundError: pandas/firebase-admin

```bash
pip install -r requirements.txt
```

を再度実行してください。

### Webhookが届かない

- ✅ ngrokが起動しているか確認
- ✅ ngrok URLが正しく`register_webhook.py`に設定されているか確認
- ✅ **`/webhook`が末尾に付いているか確認**（重要！）
- ✅ Flaskサーバーが起動しているか確認
- ✅ ngrokセッションが切れていないか確認（URLは起動するたびに変わる）

### BOCCO emoがしゃべらない

- ✅ `BOCCO_ACCESS_TOKEN`が`.env`に正しく設定されているか確認
- ✅ アクセストークンの有効期限を確認
  - `python register_webhook.py`を実行してトークンをリフレッシュ
- ✅ `BOCCO_ROOM_USER_MAPPING`が正しい形式か確認
  - room_uuid と room 名が正しく対応しているか確認
- ✅ BOCCOの音声設定がONになっているか確認
- ✅ Firebase 認証ファイルが正しく設定されているか確認

### 感情推定が失敗する

```
[ERROR] Firebase接続に失敗しました
```

この場合：
- Firebase 認証ファイルのパスを確認
- user_id が Firestore に存在するか確認
- Firebaseにデータが保存されているか確認

```bash
python peak_value_estimator.py
```

を実行して動作確認してください。

### Room 情報が取得できない

```bash
# get_room_info.py を実行
python get_room_info.py
```

トークンが無効な場合は、以下でリフレッシュしてください：

```bash
python register_webhook.py
```

---

## 複数 BOCCO の管理

複数の BOCCO emo を利用する場合、`.env` の `BOCCO_ROOM_USER_MAPPING` に全て登録するだけです。

```env
BOCCO_ROOM_USER_MAPPING='{"room_uuid_1": "user_name_1", "room_uuid_2": "user_name_2", "room_uuid_3": "user_name_3"}'
```

各 BOCCO は独立した user_id で感情データを管理し、自動的に対応するユーザーの感情に基づいてメッセージを発話します。

---

## セキュリティ注意事項

- 🔒 `.env`ファイルは**絶対にGitにコミットしない**
- 🔒 Firebase 認証ファイルも秘密に保つ
- 🔒 `.gitignore`に以下を追加してください

```
.env
.env.local
*.json
__pycache__/
*.pyc
```

- 🔒 ngrok URLを他人と共有しないこと
- 🔒 BOCCOのアクセストークンとリフレッシュトークンは秘密に保つこと

---

## ライセンス

このプロジェクトは個人利用を想定しています。

---

## 参考リンク

- [BOCCO emo Platform API ドキュメント](https://platform-api.bocco.me/docs)
- [ngrok Documentation](https://ngrok.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Firebase Admin SDK for Python](https://firebase.google.com/docs/database/admin/start)
- [pandas Documentation](https://pandas.pydata.org/)