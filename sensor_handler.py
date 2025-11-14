import requests
import logging
from datetime import datetime
import subprocess
import sys

class SensorEventHandler:
    """センサイベントを処理し、BOCCOに発話させるクラス"""
    
    def __init__(self, room_id, access_token):
        """
        Args:
            room_id: BOCCOルームID
            access_token: BOCCOアクセストークン
        """
        self.room_id = room_id
        self.access_token = access_token
        self.api_url = "https://platform-api.bocco.me/v1/rooms/{}/messages/text"
    
    def speak(self, message):
        """
        BOCCOに指定されたメッセージを発話させる
        
        Args:
            message (str): 発話させるテキスト
        
        Returns:
            bool: 成功時True、失敗時False
        """
        url = self.api_url.format(self.room_id)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {"text": message}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logging.info(f"✓ BOCCO発話成功: {message}")
            return True
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                logging.error("❌ BOCCO発話失敗: アクセストークンが無効です")
                logging.error("   → register_webhook.py を自動実行して更新します...")
                self._refresh_token_and_retry()
                return False
            else:
                logging.error(f"❌ BOCCO発話失敗: HTTP {response.status_code} エラー")
            return False
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ BOCCO発話失敗: {str(e)}")
            return False
    
    def _refresh_token_and_retry(self):
        """
        トークンを更新して再試行
        """
        try:
            logging.info("🔄 register_webhook.py を実行中...")
            result = subprocess.run(
                [sys.executable, "register_webhook.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logging.info("✅ トークン更新成功")
                logging.info("📝 次のリクエストから新しいトークンが使用されます")
                # .envを再度読み込む
                self._reload_token()
            else:
                logging.error(f"❌ トークン更新失敗: {result.stderr}")
        except subprocess.TimeoutExpired:
            logging.error("❌ register_webhook.py のタイムアウト")
        except Exception as e:
            logging.error(f"❌ トークン更新エラー: {str(e)}")
    
    def _reload_token(self):
        """
        .envファイルから新しいトークンを読み込む
        """
        try:
            from dotenv import load_dotenv
            import os
            
            # .envを再読み込み
            load_dotenv(override=True)
            new_token = os.getenv("BOCCO_ACCESS_TOKEN")
            
            if new_token:
                self.access_token = new_token
                logging.info("✅ 新しいトークンを読み込みました")
        except Exception as e:
            logging.error(f"❌ トークン読み込みエラー: {str(e)}")
    
    def handle_sensor_event(self, sensor_type, event_type, data=None):
        """
        センサイベントに応じてBOCCOを発話させる
        
        Args:
            sensor_type (str): センサタイプ（"human_sensor", "temperature", "humidity"等）
            event_type (str): イベントタイプ（"detected", "changed"等）
            data (dict): 追加データ
        
        Returns:
            bool: 発話成功時True
        """
        message = self._generate_message(sensor_type, event_type, data)
        
        if message:
            return self.speak(message)
        else:
            logging.info(f"対象外のイベント: {sensor_type}.{event_type}")
            return False
    
    def _generate_message(self, sensor_type, event_type, data=None):
        """
        センサイベントに応じたメッセージを生成
        
        Args:
            sensor_type (str): センサタイプ
            event_type (str): イベントタイプ
            data (dict): 追加データ
        
        Returns:
            str: 生成されたメッセージ、対象外の場合はNone
        """
        data = data or {}
        
        # 人感センサー（BOCCOから "human_sensor" で送られる）
        if sensor_type == "human_sensor":
            if event_type == "detected":
                hour = datetime.now().hour
                if 5 <= hour < 12:
                    return "おはようございます！"
                elif 12 <= hour < 18:
                    return "おかえりなさい！"
                else:
                    return "おつかれさまです！"
            elif event_type == "left":
                return "いってらっしゃい！"
        
        # 温度センサー
        elif sensor_type == "temperature":
            if event_type == "changed":
                temp = data.get("value")
                if temp is not None:
                    if temp > 28:
                        return f"暑いですね。温度は{temp}度です。"
                    elif temp < 15:
                        return f"寒いですね。温度は{temp}度です。"
                    else:
                        return f"温度は{temp}度です。"
        
        # 湿度センサー
        elif sensor_type == "humidity":
            if event_type == "changed":
                humidity = data.get("value")
                if humidity is not None:
                    if humidity > 70:
                        return f"湿度が高いですね。{humidity}パーセントです。"
                    elif humidity < 30:
                        return f"湿度が低いですね。{humidity}パーセントです。"
        
        # ドアセンサー
        elif sensor_type == "door":
            if event_type == "opened":
                return "ドアが開きました。"
            elif event_type == "closed":
                return "ドアが閉じました。"
        
        return None
