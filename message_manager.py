"""
メッセージ管理モジュール

message.csv から感情別メッセージを管理し、
各ルームで一日一回、順番にメッセージを発話させる
"""

import csv
import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


class MessageManager:
    """メッセージ CSV を管理し、感情別にメッセージを提供するクラス"""
    
    def __init__(self, csv_path: str = "message.csv", counter_file: str = "message_counter.json"):
        """
        Args:
            csv_path (str): message.csv のパス
            counter_file (str): カウンター永続化ファイルのパス
        """
        self.csv_path = Path(csv_path)
        self.counter_file = Path(counter_file)
        self.messages = self._load_messages()
        self.last_spoken_date = {}  # {room_id: date} - 最後に発話した日付を記録
        self.message_counter = self._load_counter()  # {room_id: {emotion: index}} - 永続化されたカウンター
        
        logging.info(f"[OK] メッセージマネージャーを初期化しました")
        logging.info(f"    Positive: {len(self.messages.get('Positive', []))}個")
        logging.info(f"    Neutral: {len(self.messages.get('Neutral', []))}個")
        logging.info(f"    Negative: {len(self.messages.get('Negative', []))}個")
    
    def _load_messages(self) -> Dict[str, List[str]]:
        """
        message.csv からメッセージを読み込む
        
        Returns:
        --------
        dict: {"Positive": [...], "Neutral": [...], "Negative": [...]}
        """
        messages = {"Positive": [], "Neutral": [], "Negative": []}
        
        if not self.csv_path.exists():
            logging.error(f"[ERROR] {self.csv_path} が見つかりません")
            return messages
        
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row.get("Category", "").strip()
                    message = row.get("Message", "").strip()
                    
                    if category in messages and message:
                        messages[category].append(message)
            
            logging.info(f"[OK] message.csv を読み込みました")
            return messages
        except Exception as e:
            logging.error(f"[ERROR] message.csv の読み込みに失敗しました: {e}")
            return messages
    
    def _load_counter(self) -> Dict[str, Dict[str, int]]:
        """
        カウンターを JSON ファイルから読み込む（永続化）
        
        Returns:
        --------
        dict: {room_id: {emotion: index}}
        """
        if not self.counter_file.exists():
            return {}
        
        try:
            with open(self.counter_file, "r", encoding="utf-8") as f:
                counter = json.load(f)
            logging.info(f"[OK] メッセージカウンターを読み込みました")
            return counter
        except Exception as e:
            logging.error(f"[ERROR] カウンターの読み込みに失敗しました: {e}")
            return {}
    
    def _save_counter(self):
        """
        カウンターを JSON ファイルに保存（永続化）
        """
        try:
            with open(self.counter_file, "w", encoding="utf-8") as f:
                json.dump(self.message_counter, f, ensure_ascii=False, indent=2)
            logging.info(f"[OK] メッセージカウンターを保存しました")
        except Exception as e:
            logging.error(f"[ERROR] カウンターの保存に失敗しました: {e}")
    
    def get_message_for_room(self, room_id: str, emotion: str) -> Optional[str]:
        """
        ルームの感情に対応するメッセージを取得（順序付き）
        
        一日に一回だけメッセージを返す。
        同じ日に複数回呼び出された場合は None を返す。
        
        Parameters:
        -----------
        room_id : str
            ルームID
        emotion : str
            推定感情（Positive/Neutral/Negative）
        
        Returns:
        --------
        str: メッセージ、今日既に発話済みの場合は None
        """
        # 該当するメッセージが存在するか確認
        if emotion not in self.messages or not self.messages[emotion]:
            logging.warning(f"[WARNING] 感情 {emotion} に対応するメッセージがありません")
            return None
        
        today = date.today()
        
        # 【重要】一日に一回だけ発話する制御
        if room_id in self.last_spoken_date:
            if self.last_spoken_date[room_id] == today:
                # 今日既に発話済み
                logging.info(f"[INFO] {room_id} は今日既にメッセージを発話済みです")
                return None
        
        # ルームのカウンターを初期化（初回時）
        if room_id not in self.message_counter:
            self.message_counter[room_id] = {}
        
        # 感情ごとのカウンターを初期化（初回時）
        if emotion not in self.message_counter[room_id]:
            self.message_counter[room_id][emotion] = 0
        
        # 現在のインデックスを取得
        current_index = self.message_counter[room_id][emotion]
        
        # インデックスがメッセージ数を超えたらループ（1番目に戻す）
        if current_index >= len(self.messages[emotion]):
            current_index = 0
            logging.info(f"[INFO] {room_id} の {emotion} メッセージがループしました（{current_index + 1}番目に戻ります）")
        
        # メッセージを取得
        message = self.messages[emotion][current_index]
        
        # カウンターをインクリメント
        self.message_counter[room_id][emotion] = current_index + 1
        
        # 最後に発話した日付を記録
        self.last_spoken_date[room_id] = today
        
        # カウンターを永続化
        self._save_counter()
        
        logging.info(
            f"[OK] メッセージ取得: Room {room_id}, Emotion {emotion}, "
            f"Index {current_index + 1}/{len(self.messages[emotion])}"
        )
        
        return message
    
    def get_counter_status(self, room_id: str) -> Dict[str, int]:
        """
        ルームの現在のカウンター状態を取得
        
        Parameters:
        -----------
        room_id : str
            ルームID
        
        Returns:
        --------
        dict: 各感情のカウンター（{"Positive": 2, "Neutral": 1, "Negative": 0}）
        """
        if room_id not in self.message_counter:
            return {"Positive": 0, "Neutral": 0, "Negative": 0}
        
        return self.message_counter.get(room_id, {})
    
    def get_last_spoken_date(self, room_id: str) -> Optional[str]:
        """
        ルームが最後にメッセージを発話した日付を取得
        
        Parameters:
        -----------
        room_id : str
            ルームID
        
        Returns:
        --------
        str: 日付（YYYY-MM-DD形式）、未発話の場合は None
        """
        if room_id in self.last_spoken_date:
            return str(self.last_spoken_date[room_id])
        return None
    
    def reset_counter_for_room(self, room_id: str):
        """
        ルームのカウンターを全感情でリセット（デバッグ用）
        
        Parameters:
        -----------
        room_id : str
            ルームID
        """
        if room_id in self.message_counter:
            self.message_counter[room_id] = {"Positive": 0, "Neutral": 0, "Negative": 0}
            self._save_counter()
            logging.info(f"[OK] {room_id} のメッセージカウンターをリセットしました")
    
    def print_messages(self):
        """デバッグ用：すべてのメッセージを表示"""
        print("\n=== メッセージ一覧 ===\n")
        
        for emotion, messages in self.messages.items():
            print(f"【{emotion}】({len(messages)}個)")
            for i, msg in enumerate(messages, 1):
                print(f"  {i}. {msg}")
            print()
    
    def print_counter_status(self):
        """デバッグ用：すべてのカウンター状態を表示"""
        print("\n=== カウンター状態 ===\n")
        
        for room_id, counter in self.message_counter.items():
            last_date = self.get_last_spoken_date(room_id)
            print(f"【{room_id}】")
            print(f"  最後に発話した日付: {last_date}")
            for emotion, index in counter.items():
                print(f"  {emotion}: {index}番目")
            print()
