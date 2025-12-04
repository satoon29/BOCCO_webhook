import os
import sys
import io
import json
import requests
from flask import Flask, request, jsonify
import logging
from dotenv import load_dotenv
from sensor_handler import SensorEventHandler
from slack_notifier import SlackNotifier
from message_manager import MessageManager

# Windows環境での文字コード対応
if sys.platform == "win32":
    # コンソール出力の文字コードを UTF-8 に設定
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .envから環境変数を読み込む
load_dotenv()

# 環境変数から設定を読み込み
ACCESS_TOKEN = os.getenv("BOCCO_ACCESS_TOKEN")
ROOM_USER_MAPPING_STR = os.getenv("BOCCO_ROOM_USER_MAPPING", "{}")
SLACK_USER_URL_MAPPING_STR = os.getenv("SLACK_USER_URL_MAPPING", "{}")
FEEDBACK_USER_URL_MAPPING_STR = os.getenv("FEEDBACK_USER_URL_MAPPING", "{}")

# Flaskアプリの作成
app = Flask(__name__)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Room ID と room 名のマッピングを読み込み
try:
    ROOM_USER_MAPPING = json.loads(ROOM_USER_MAPPING_STR)
    logging.info(f"[OK] Room-User マッピングを読み込みました: {ROOM_USER_MAPPING}")
except json.JSONDecodeError as e:
    logging.error(f"[ERROR] BOCCO_ROOM_USER_MAPPING のJSON解析に失敗しました: {e}")
    ROOM_USER_MAPPING = {}

# Slack 通知機能を初期化
slack_notifier = None
if SLACK_USER_URL_MAPPING_STR and FEEDBACK_USER_URL_MAPPING_STR:
    try:
        slack_user_url_mapping = json.loads(SLACK_USER_URL_MAPPING_STR)
        feedback_user_url_mapping = json.loads(FEEDBACK_USER_URL_MAPPING_STR)
        slack_notifier = SlackNotifier(slack_user_url_mapping, feedback_user_url_mapping)
        logging.info(f"[OK] Slack 通知機能を有効化しました")
    except json.JSONDecodeError as e:
        logging.error(f"[ERROR] Slack マッピングのJSON解析に失敗しました: {e}")
else:
    logging.warning("[WARNING] Slack マッピングが設定されていません")

# メッセージマネージャーを初期化
message_manager = MessageManager("message.csv")
logging.info("[OK] メッセージマネージャーを初期化しました")


def get_user_id_from_room_id(room_id):
    """
    Room ID から user_id を取得（ローカルマッピングから）
    
    Parameters:
    -----------
    room_id : str
        BOCCO の部屋ID
    
    Returns:
    --------
    str: user_id、マッピングに存在しない場合は None
    """
    user_id = ROOM_USER_MAPPING.get(room_id)
    if user_id:
        logging.info(f"[OK] Room ID {room_id} → User ID: {user_id}")
        return user_id
    else:
        logging.warning(f"[WARNING] Room ID {room_id} はマッピングに存在しません")
        return None


# Webhookで受け取るエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.info(f"Webhook受信: {data}")

    if not data:
        return jsonify({"error": "no JSON payload"}), 400

    # BOCCOから送られるデータを解析
    room_id = data.get("uuid")  # webhook の "uuid" が Room ID
    event = data.get("event")  # "human_sensor.detected"
    sensor_data = data.get("data")  # ネストされたセンサデータ
    
    # イベント名から sensor_type と event_type を抽出
    if event:
        parts = event.split(".")
        sensor_type = parts[0] if len(parts) > 0 else None
        event_type = parts[1] if len(parts) > 1 else None
    else:
        sensor_type = None
        event_type = None

    logging.info(f"解析結果 - room_id: {room_id}, sensor_type: {sensor_type}, event_type: {event_type}")

    # ローカルマッピングから user_id を取得
    user_id = get_user_id_from_room_id(room_id)
    if not user_id:
        logging.warning(f"[WARNING] Room ID {room_id} の user_id が見つかりません")
        return jsonify({"status": "processed", "success": False}), 200

    # SensorEventHandler を動的に作成（slack_notifier と message_manager を渡す）
    handler = SensorEventHandler(
        room_id,
        ACCESS_TOKEN,
        user_id,
        slack_notifier,
        message_manager
    )

    # センサイベントを処理
    success = handler.handle_sensor_event(sensor_type, event_type, sensor_data)
    
    return jsonify({"status": "processed", "success": success}), 200

@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({"status": "healthy"}), 200
    
if __name__ == "__main__":
    # 環境変数の確認
    if not ACCESS_TOKEN:
        logging.error("[ERROR] .env ファイルに BOCCO_ACCESS_TOKEN を設定してください")
        exit(1)
    
    if not ROOM_USER_MAPPING:
        logging.error("[ERROR] .env ファイルに BOCCO_ROOM_USER_MAPPING を設定してください")
        exit(1)
    
    # 開発環境用の設定
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=5001, debug=debug_mode, use_reloader=False)

