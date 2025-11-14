import os
import sys
import io
from flask import Flask, request, jsonify
import logging
from dotenv import load_dotenv
from sensor_handler import SensorEventHandler

# Windows環境での文字コード対応
if sys.platform == "win32":
    # コンソール出力の文字コードを UTF-8 に設定
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .envから環境変数を読み込む
load_dotenv()

# 環境変数から設定を読み込み
ROOM_ID = os.getenv("BOCCO_ROOM_ID")
ACCESS_TOKEN = os.getenv("BOCCO_ACCESS_TOKEN")
USER_ID = os.getenv("BOCCO_USER_ID", "test00")  # デフォルト: test00

# Flaskアプリの作成
app = Flask(__name__)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# SensorEventHandlerのインスタンス作成（user_idを渡す）
handler = SensorEventHandler(ROOM_ID, ACCESS_TOKEN, USER_ID)

# Webhookで受け取るエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.info(f"Webhook受信: {data}")

    if not data:
        return jsonify({"error": "no JSON payload"}), 400

    # BOCCOから送られるデータ構造を解析
    event = data.get("event")  # "human_sensor.detected"
    sensor_data = data.get("data")  # ネストされたセンサデータ
    
    # イベント名から sensor_type と event_type を抽出
    if event:
        parts = event.split(".")
        sensor_type = parts[0] if len(parts) > 0 else None  # "human_sensor"
        event_type = parts[1] if len(parts) > 1 else None   # "detected"
    else:
        sensor_type = None
        event_type = None

    logging.info(f"解析結果 - sensor_type: {sensor_type}, event_type: {event_type}")

    # センサイベントを処理
    success = handler.handle_sensor_event(sensor_type, event_type, sensor_data)
    
    return jsonify({"status": "processed", "success": success}), 200

@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({"status": "healthy"}), 200
    
if __name__ == "__main__":
    # 環境変数の確認
    if not ROOM_ID or not ACCESS_TOKEN:
        logging.error("[ERROR] .env ファイルに BOCCO_ROOM_ID と BOCCO_ACCESS_TOKEN を設定してください")
        exit(1)
    
    logging.info(f"[INFO] Firebase ユーザーID: {USER_ID}")
    
    # 開発環境用の設定
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=5001, debug=debug_mode, use_reloader=False)

