"""
Slack 通知モジュール

センサイベント時に、ユーザーに対応する URL を Slack に送信
"""

import requests
import logging
import json
from typing import Optional, Dict

# ログ設定
logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack に通知を送信するクラス"""
    
    def __init__(
        self,
        slack_webhook_mapping: Dict[str, str],
        feedback_url_mapping: Dict[str, str]
    ):
        """
        Args:
            slack_webhook_mapping (dict): ユーザーID と Slack Webhook URL のマッピング
                形式: {"user_id": "https://hooks.slack.com/services/..."},
            feedback_url_mapping (dict): ユーザーID とフィードバック URL のマッピング
                形式: {"user_id": "https://example.com"}
        """
        self.slack_webhook_mapping = slack_webhook_mapping
        self.feedback_url_mapping = feedback_url_mapping
    
    def send_message_notification(
        self,
        user_id: str,
        message: str,
        emotion: Optional[str] = None
    ) -> bool:
        """
        BOCCO の発話メッセージと共にフィードバック URL を Slack に送信
        
        Parameters:
        -----------
        user_id : str
            ユーザーID
        message : str
            BOCCO が発話したメッセージ
        emotion : str
            推定感情（オプション）
        
        Returns:
        --------
        bool: 送信成功時 True、失敗時 False
        """
        # ユーザーIDから Slack Webhook URL を取得
        webhook_url = self.slack_webhook_mapping.get(user_id)
        if not webhook_url:
            logger.warning(f"[WARNING] User ID {user_id} に対応する Slack Webhook URL が見つかりません")
            return False
        
        # ユーザーIDからフィードバック URL を取得
        feedback_url = self.feedback_url_mapping.get(user_id)
        if not feedback_url:
            logger.warning(f"[WARNING] User ID {user_id} に対応するフィードバック URL が見つかりません")
            return False
        
        # Slack メッセージペイロードを構成
        payload = self._build_message_payload(message, feedback_url, emotion)
        
        # Slack に送信
        return self._send_to_slack(webhook_url, payload)
    
    def _build_message_payload(
        self,
        message: str,
        feedback_url: str,
        emotion: Optional[str] = None
    ) -> dict:
        """
        Slack 送信用のメッセージペイロードを構成
        
        Parameters:
        -----------
        message : str
            BOCCO が発話したメッセージ
        feedback_url : str
            フィードバック URL
        emotion : str
            推定感情
        
        Returns:
        --------
        dict: Slack メッセージペイロード
        """
        # 感情に応じた色を設定
        color_map = {
            "Positive": "#36a64f",
            "Neutral": "#808080",
            "Negative": "#ff0000"
        }
        color = color_map.get(emotion, "#0099ff")
        
        payload = {
            "text": "@channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": '@channel'
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f'"{message}"'
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "▼フィードバックが届きました！"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{feedback_url}"
                    }
                }
            ]
        }
        
        return payload
    
    def _send_to_slack(self, webhook_url: str, payload: dict) -> bool:
        """
        Slack に JSON ペイロードを送信
        
        Parameters:
        -----------
        webhook_url : str
            Slack Incoming Webhook URL
        payload : dict
            Slack メッセージペイロード
        
        Returns:
        --------
        bool: 送信成功時 True、失敗時 False
        """
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("[OK] Slack 通知送信成功")
                return True
            else:
                logger.error(f"[ERROR] Slack 送信失敗: HTTP {response.status_code}")
                logger.error(f"[ERROR] レスポンス: {response.text}")
                return False
        except requests.exceptions.Timeout:
            logger.error("[ERROR] Slack リクエストタイムアウト")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Slack 送信エラー: {str(e)}")
            return False
