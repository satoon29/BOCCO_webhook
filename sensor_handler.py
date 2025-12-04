import requests
import logging
from datetime import datetime
import subprocess
import sys
import io
from peak_value_estimator import estimate_single_day
from message_manager import MessageManager

# Windows環境での文字コード対応
if sys.platform == "win32":
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SensorEventHandler:
    """センサイベントを処理し、BOCCOに発話させるクラス"""
    
    def __init__(self, room_id, access_token, user_id, slack_notifier=None, message_manager=None):
        """
        Args:
            room_id: BOCCOの部屋ID（webhook の uuid）
            access_token: BOCCOアクセストークン
            user_id: Firebase のユーザーID（room の名前）
            slack_notifier: SlackNotifier インスタンス（オプション）
            message_manager: MessageManager インスタンス（オプション）
        """
        self.room_id = room_id
        self.access_token = access_token
        self.user_id = user_id
        self.slack_notifier = slack_notifier
        self.message_manager = message_manager
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
        data = {"text": "おかえりなさい。" + message + "今日のフィードバックを確認してみましょう！"}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logging.info(f"[OK] BOCCO発話成功 (Room: {self.room_id}, User: {self.user_id}): {message}")
            
            # 発話成功時、Slack にも通知
            if self.slack_notifier:
                self._notify_slack_for_speech(message)
            
            return True
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401 and retry:
                logging.error("[ERROR] BOCCO発話失敗: アクセストークンが無効です")
                logging.error("[INFO] register_webhook.py を自動実行して更新します...")
                
                # トークンを更新
                if self._refresh_token_and_retry():
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
        try:
            emotion = estimate_single_day(self.user_id, datetime.now().date())
            if emotion:
                logging.info(f"[OK] 本日の推定感情 (User: {self.user_id}): {emotion}")
                return emotion
        except Exception as e:
            logging.error(f"[ERROR] 感情推定エラー: {str(e)}")
        
        return None
    
    def handle_sensor_event(self, sensor_type, event_type, data=None):
        """
        センサイベントに応じてBOCCOを発話させる
        
        Args:
            sensor_type (str): センサタイプ
            event_type (str): イベントタイプ
            data (dict): 追加データ
        
        Returns:
            bool: 発話成功時True
        """
        message = self._generate_message(sensor_type, event_type, data)
        
        if message:
            # speak() 内で自動的に Slack 通知も行われる
            success = self.speak(message)
            return success
        else:
            logging.info(f"[INFO] 対象外のイベント: {sensor_type}.{event_type}")
            return False
    
    def _notify_slack_for_speech(self, message: str):
        """
        BOCCO の発話に基づいて Slack に通知
        
        Parameters:
        -----------
        message : str
            BOCCO が発話したメッセージ
        """
        if not self.slack_notifier:
            return
        
        try:
            emotion = self._estimate_today_emotion()
            self.slack_notifier.send_message_notification(
                user_id=self.user_id,
                message=message,
                emotion=emotion
            )
        except Exception as e:
            logging.warning(f"[WARNING] Slack 通知エラー: {str(e)}")
    
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
        
        # 人感センサー
        if sensor_type == "human_sensor":
            if event_type == "detected":
                # 本日の感情を推定
                emotion = self._estimate_today_emotion()
                
                # message_manager から順序付きメッセージを取得
                if self.message_manager and emotion:
                    message = self.message_manager.get_message_for_room(self.room_id, emotion)
                    if message:
                        logging.info(f"[OK] メッセージマネージャーから取得: {emotion}")
                        return message

        