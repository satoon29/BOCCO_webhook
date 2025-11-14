import requests
import logging
from datetime import datetime, date
import subprocess
import sys
import io
from peak_value_estimator import estimate_single_day, initialize_firebase, fetch_emotion_data

# Windows環境での文字コード対応
if sys.platform == "win32":
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SensorEventHandler:
    """センサイベントを処理し、BOCCOに発話させるクラス"""
    
    def __init__(self, room_id, access_token, user_id=None):
        """
        Args:
            room_id: BOCCOルームID
            access_token: BOCCOアクセストークン
            user_id: Firebase ユーザーID（感情推定用）
        """
        self.room_id = room_id
        self.access_token = access_token
        self.user_id = user_id
        self.api_url = "https://platform-api.bocco.me/v1/rooms/{}/messages/text"
    
    def speak(self, message, retry=True):
        """
        BOCCOに指定されたメッセージを発話させる
        
        Args:
            message (str): 発話させるテキスト
            retry (bool): トークン無効時に再試行するか
        
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
            logging.info(f"[OK] BOCCO発話成功: {message}")
            return True
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401 and retry:
                logging.error("[ERROR] BOCCO発話失敗: アクセストークンが無効です")
                logging.error("[INFO] register_webhook.py を自動実行して更新します...")
                
                # トークンを更新
                if self._refresh_token_and_retry():
                    # トークン更新成功 → 再試行（retry=Falseで無限ループを防止）
                    logging.info("[INFO] トークン更新成功。発話を再試行します...")
                    return self.speak(message, retry=False)
                else:
                    logging.error("[ERROR] トークン更新失敗。発話できません")
                    return False
            else:
                logging.error(f"[ERROR] BOCCO発話失敗: HTTP {response.status_code} エラー")
            return False
        except requests.exceptions.RequestException as e:
            logging.error(f"[ERROR] BOCCO発話失敗: {str(e)}")
            return False
    
    def _refresh_token_and_retry(self):
        """
        トークンを更新する
        
        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            logging.info("[INFO] register_webhook.py を実行中...")
            result = subprocess.run(
                [sys.executable, "register_webhook.py"],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                logging.info("[OK] トークン更新成功")
                # .envを再度読み込む
                self._reload_token()
                return True
            else:
                logging.error(f"[ERROR] トークン更新失敗: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logging.error("[ERROR] register_webhook.py のタイムアウト")
            return False
        except Exception as e:
            logging.error(f"[ERROR] トークン更新エラー: {str(e)}")
            return False
    
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
                logging.info("[OK] 新しいトークンを読み込みました")
                return True
            else:
                logging.error("[ERROR] 新しいトークンが見つかりません")
                return False
        except Exception as e:
            logging.error(f"[ERROR] トークン読み込みエラー: {str(e)}")
            return False
    
    def _estimate_today_emotion(self):
        """
        本日の感情を推定する
        
        Returns:
            str: 推定感情 ('Positive', 'Neutral', 'Negative') または None
        """
        if not self.user_id:
            logging.info("[INFO] user_id が設定されていません。感情推定をスキップします")
            return None
        
        try:
            emotion = estimate_single_day(self.user_id, date.today())
            if emotion:
                logging.info(f"[OK] 本日の推定感情: {emotion}")
                return emotion
        except Exception as e:
            logging.error(f"[ERROR] 感情推定エラー: {str(e)}")
        
        return None
    
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
            logging.info(f"[INFO] 対象外のイベント: {sensor_type}.{event_type}")
            return False
    
    def _generate_message(self, sensor_type, event_type, data=None):
        """
        センサイベントに応じたメッセージを生成
        感情推定に基づいて動的にメッセージを変更
        
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
                
                # 本日の感情を推定
                emotion = self._estimate_today_emotion()
                
                # 感情に基づいたメッセージを生成
                if emotion == "Positive":
                    # ポジティブな日 → ほめる
                    if 5 <= hour < 12:
                        return "おはようございます！いい朝ですね。今日も一日頑張ってください！"
                    elif 12 <= hour < 18:
                        return "おかえりなさい！素敵な表情ですね。その調子で頑張ってください！"
                    else:
                        return "おつかれさまです！今日も頑張りましたね。ゆっくり休んでください。"
                
                elif emotion == "Negative":
                    # ネガティブな日 → 励ます
                    if 5 <= hour < 12:
                        return "おはようございます。何か悩んでいるのかな？話を聞きますよ。"
                    elif 12 <= hour < 18:
                        return "おかえりなさい。大変な一日のようですね。何かお手伝いできることはありませんか？"
                    else:
                        return "おつかれさまです。ネガティブな気持ちも大切です。明日はもっと素敵な日になりますよ。"
                
                else:  # Neutral
                    # ニュートラルな日 → 通常のあいさつ
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
                        return f"暑いですね。温度は{temp}度です。水分補給してください。"
                    elif temp < 15:
                        return f"寒いですね。温度は{temp}度です。暖かくしてください。"
                    else:
                        return f"快適です。温度は{temp}度です。"
        
        # 湿度センサー
        elif sensor_type == "humidity":
            if event_type == "changed":
                humidity = data.get("value")
                if humidity is not None:
                    if humidity > 70:
                        return f"湿度が高いですね。{humidity}パーセントです。換気しましょう。"
                    elif humidity < 30:
                        return f"湿度が低いですね。{humidity}パーセントです。加湿しましょう。"
        
        # ドアセンサー
        elif sensor_type == "door":
            if event_type == "opened":
                return "ドアが開きました。"
            elif event_type == "closed":
                return "ドアが閉じました。"
        
        return None
