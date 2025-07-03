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

