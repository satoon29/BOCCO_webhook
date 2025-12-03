"""
Slack 通知モジュール

センサイベント時に、ユーザーに対応する URL を Slack に送信
"""

import requests
import logging
from typing import Optional, Dict

# ログ設定
logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack に通知を送信するクラス"""
    
    def __init__(self, webhook_url: str, user_url_mapping: Dict[str, str]):
        """
        Args:
            webhook_url (str): Slack の Incoming Webhook URL
            user_url_mapping (dict): ユーザーID と URL のマッピング
                形式: {"user_id": "https://example.com"}
        """
        self.webhook_url = webhook_url
        self.user_url_mapping = user_url_mapping
    
    def send_notification(self, user_id: str, emotion: Optional[str] = None) -> bool:
        """
        ユーザーに対応する URL を Slack に送信
        
        Parameters:
        -----------
        user_id : str
            ユーザーID
        emotion : str
            推定感情（オプション）
        
        Returns:
        --------
        bool: 送信成功時 True、失敗時 False
        """
        # ユーザーIDから URL を取得
        url = self.user_url_mapping.get(user_id)
        if not url:
            logger.warning(f"[WARNING] User ID {user_id} に対応する URL が見つかりません")
            return False
        
        # メッセージを構成
        message = self._build_message(user_id, url, emotion)
        
        # Slack に送信
        return self._send_to_slack(message)
    
    def _build_message(self, user_id: str, url: str, emotion: Optional[str] = None) -> dict:
        """
        Slack 送信用のメッセージを構成
        
        Parameters:
        -----------
        user_id : str
            ユーザーID
        url : str
            送信する URL
        emotion : str
            推定感情
        
        Returns:
        --------
        dict: Slack メッセージペイロード
        """
        # 感情に応じた絵文字を設定
        emoji_map = {
            "Positive": "😊",
            "Neutral": "😐",
            "Negative": "😔"
        }
        emoji = emoji_map.get(emotion, "👋")
        
        # メッセージを構成
        if emotion:
            title = f"{emoji} 本日の感情: {emotion}"
            text = f"ユーザー: {user_id}\n感情: {emotion}"
        else:
            title = f"👋 新規通知"
            text = f"ユーザー: {user_id}"
        
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title}*\n{text}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*URL:*\n{url}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "URL を開く"
                            },
                            "url": url
                        }
                    ]
                }
            ]
        }
        
        return payload
    
    def _send_to_slack(self, payload: dict) -> bool:
        """
        Slack に JSON ペイロードを送信
        
        Parameters:
        -----------
        payload : dict
            Slack メッセージペイロード
        
        Returns:
        --------
        bool: 送信成功時 True、失敗時 False
        """
        try:
            response = requests.post(
                self.webhook_url,
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
    
    def send_notification_with_emotion(
        self,
        user_id: str,
        emotion: str,
        room_name: str
    ) -> bool:
        """
        感情情報を含めた通知を送信
        
        Parameters:
        -----------
        user_id : str
            ユーザーID
        emotion : str
            推定感情（Positive/Neutral/Negative）
        room_name : str
            BOCCO の部屋名
        
        Returns:
        --------
        bool: 送信成功時 True、失敗時 False
        """
        url = self.user_url_mapping.get(user_id)
        if not url:
            logger.warning(f"[WARNING] User ID {user_id} に対応する URL が見つかりません")
            return False
        
        # 感情に応じた絵文字と色を設定
        emotion_config = {
            "Positive": {
                "emoji": "😊",
                "color": "36a64f",
                "text": "良好な感情状態です！"
            },
            "Neutral": {
                "emoji": "😐",
                "color": "808080",
                "text": "標準的な感情状態です。"
            },
            "Negative": {
                "emoji": "😔",
                "color": "ff0000",
                "text": "ネガティブな感情状態のようです。"
            }
        }
        
        config = emotion_config.get(emotion, emotion_config["Neutral"])
        
        # Slack メッセージペイロード（より詳細版）
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{config['emoji']} BOCCO からのお知らせ"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*ユーザー:*\n{user_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*部屋:*\n{room_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*推定感情:*\n{emotion}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*ステータス:*\n{config['text']}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*詳細情報:*\n{url}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "詳細を確認"
                            },
                            "url": url,
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"[OK] Slack 通知送信成功: {user_id} ({emotion})")
                return True
            else:
                logger.error(f"[ERROR] Slack 送信失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"[ERROR] Slack 送信エラー: {str(e)}")
            return False
