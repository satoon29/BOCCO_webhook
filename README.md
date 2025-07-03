# BOCCO_webhook

## 概要

このシステムは、BOCCO emoの人感センサーが人の動きを検知したときに、Flaskで構築されたWebhookサーバーを通じて通知を受け取り、BOCCO emoがメッセージを発話する一連の処理を実現するものです。絵文字による感情記録と連携することで、ユーザの感情に応じた応答も可能になります。

---

## 使用技術

- Python 3
- Flask
- requests
- dotenv
- ngrok（ローカルホストを外部公開）

---

## フォルダ構成例

```
project_root/
├── .env
├── bocco_webhook.py               # Flaskサーバー本体（webhook）
├── register_webhook.py  # WebhookをBOCCO側に登録するスクリプト
├── choose_message.py             # メッセージ選択などの補助関数

```

---

## .env ファイルの内容

```
BOCCO_ROOM_ID=あなたのBOCCOルームID
BOCCO_ACCESS_TOKEN=アクセストークン

```

---

## ステップ1：Flaskサーバーの起動

`bocco_webhook.py`

```python
import os
from flask import Flask, request, jsonify
import requests
import logging
from dotenv import load_dotenv

# .envから環境変数を読み込む
load_dotenv()

# 環境変数から設定を読み込み
ROOM_ID = os.getenv("BOCCO_ROOM_ID")
ACCESS_TOKEN = os.getenv("BOCCO_ACCESS_TOKEN")

# Flaskアプリの作成
app = Flask(__name__)

# ログ設定
logging.basicConfig(level=logging.INFO)

# BOCCO emoにしゃべらせる関数
def speak(room_id, token, message):
    url = f"https://platform-api.bocco.me/v1/rooms/{room_id}/messages/text"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "text": message
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logging.info(f"BOCCOに送信成功: {message}")
    except requests.exceptions.RequestException as e:
        logging.error(f"BOCCOへの送信エラー: {e}")
        return False
    return True

# Webhookで受け取るエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.info(f"Webhook受信: {data}")

    if not data:
        return jsonify({"error": "no JSON payload"}), 400

    sensor_type = data.get("sensor_type")
    event_type = data.get("event_type")

    if sensor_type == "human" and event_type == "detected":
        success = speak(
            room_id=ROOM_ID,
            token=ACCESS_TOKEN,
            message="おかえりなさい！"
        )
        return jsonify({"status": "spoken" if success else "failed"}), 200
    else:
        logging.info("対象外のイベントでした")
        return jsonify({"status": "ignored"}), 200
    
if __name__ == "__main__":
    app.run(port=5000)
```

---

## ステップ2：ngrokでローカルサーバーを外部公開

```bash
ngrok http 5001

```

表示されたURL（例：[https://xxxx.ngrok-free.app）を控えます。](https://xxxx.ngrok-free.xn--app)-t63cyd1lsfs128b./)

---

## ステップ3：Webhookの登録（register_webhook.py）

```python
import requests

refresh_token = "db43b831-d523-4f4e-9f81-72e243b8be3c"
auth_url = "https://platform-api.bocco.me/oauth/token/refresh"

def refresh_access_token():
    response = requests.post(auth_url, json={"refresh_token": refresh_token})
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("新しいアクセストークン:", access_token)
        return access_token
    else:
        print("リフレッシュ失敗:", response.status_code, response.text)
        return None
    

access_token = refresh_access_token()
if access_token is None:
    raise Exception("アクセストークンの取得に失敗しました")
webhook_url = "https://cb9b-133-19-169-3.ngrok-free.app/webhook"  # 上で出たngrokのURL！

# Webhook登録
res1 = requests.post(
    "https://platform-api.bocco.me/v1/webhook",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json={
        "description": "my webhook",
        "url": webhook_url
    }
)
print("Webhook登録:", res1.status_code, res1.text)

# イベント登録（人感センサー）
res2 = requests.put(
    "https://platform-api.bocco.me/v1/webhook/events",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json={
        "events": ["human_sensor.detected"]
    }
)
print("イベント登録:", res2.status_code, res2.text)

```

---

## ステップ4：動作確認

1. `python bocco_webhook.py` でFlaskを起動
2. `ngrok http 5001` を実行し、外部URLを取得
3. `register_webhook.py` を実行し、Webhookを登録
4. BOCCO emoの近くを通ると、ターミナルにログが出力され、BOCCOがしゃべります

---

## 備考

- `speak()`関数は後で感情に応じたメッセージ（choose_message関数など）と連携可能
- GETリクエストで `/webhook` にアクセスするとFlaskの生存確認ができます
- Webhook受信確認には [https://webhook.site](https://webhook.site/) も利用可能です（テスト用）