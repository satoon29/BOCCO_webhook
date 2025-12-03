"""
BOCCO の部屋情報とセンサ情報を取得して表示するスクリプト

部屋ID一覧の取得: GET /v1/rooms
部屋センサの一覧取得: GET /v1/rooms/{room_uuid}/sensors
"""

import requests
import json
from dotenv import load_dotenv
import os
import sys
import io
import subprocess

# Windows環境での文字コード対応
if sys.platform == "win32":
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .envから環境変数を読み込む
load_dotenv()

# 環境変数から設定を読み込み
ACCESS_TOKEN = os.getenv("BOCCO_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("BOCCO_REFRESH_TOKEN")

if not ACCESS_TOKEN:
    print("[ERROR] .env ファイルに BOCCO_ACCESS_TOKEN を設定してください")
    exit(1)

if not REFRESH_TOKEN:
    print("[ERROR] .env ファイルに BOCCO_REFRESH_TOKEN を設定してください")
    exit(1)


def refresh_access_token_if_needed(response):
    """
    レスポンスが401の場合、トークンを更新
    
    Parameters:
    -----------
    response : requests.Response
        APIレスポンス
    
    Returns:
    --------
    bool: トークンが更新されたかどうか
    """
    if response.status_code == 401:
        print("[ERROR] アクセストークンが無効です")
        print("[INFO] register_webhook.py を実行してトークンを更新します...")
        
        try:
            result = subprocess.run(
                [sys.executable, "register_webhook.py"],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                print("[OK] トークンが更新されました")
                # .envを再読み込み
                load_dotenv(override=True)
                return True
            else:
                print(f"[ERROR] トークン更新失敗: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] register_webhook.py のタイムアウト")
            return False
        except Exception as e:
            print(f"[ERROR] トークン更新エラー: {str(e)}")
            return False
    
    return False


def get_rooms(access_token=None):
    """
    部屋一覧を取得
    
    Parameters:
    -----------
    access_token : str
        アクセストークン（デフォルト: 環境変数から読み込み）
    
    Returns:
    --------
    list: 部屋情報のリスト
    """
    if access_token is None:
        access_token = os.getenv("BOCCO_ACCESS_TOKEN")
    
    url = "https://platform-api.bocco.me/v1/rooms"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        # 401エラーの場合はトークンを更新して再試行
        if response.status_code == 401:
            if refresh_access_token_if_needed(response):
                # トークン更新後に再試行
                new_token = os.getenv("BOCCO_ACCESS_TOKEN")
                return get_rooms(new_token)
            else:
                print("[ERROR] トークン更新に失敗しました")
                return []
        
        response.raise_for_status()
        
        # レスポンスを解析
        try:
            data = response.json()
            # レスポンスがリスト形式か、オブジェクト形式かを判定
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # rooms キーがあればそれを返す
                if "rooms" in data:
                    rooms = data["rooms"]
                    if isinstance(rooms, list):
                        return rooms
                # データ構造を確認
                print(f"[DEBUG] API レスポンス構造: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}")
                return data if isinstance(data, list) else []
            else:
                print(f"[ERROR] 予期しないレスポンス形式: {type(data)}")
                return []
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON解析エラー: {e}")
            print(f"[DEBUG] レスポンス: {response.text[:200]}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 部屋一覧の取得に失敗しました: {e}")
        return []


def get_sensors(room_uuid, access_token=None):
    """
    指定された部屋のセンサ一覧を取得
    
    Parameters:
    -----------
    room_uuid : str
        部屋のUUID
    access_token : str
        アクセストークン（デフォルト: 環境変数から読み込み）
    
    Returns:
    --------
    list: センサ情報のリスト
    """
    if access_token is None:
        access_token = os.getenv("BOCCO_ACCESS_TOKEN")
    
    url = f"https://platform-api.bocco.me/v1/rooms/{room_uuid}/sensors"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        # 401エラーの場合はトークンを更新して再試行
        if response.status_code == 401:
            if refresh_access_token_if_needed(response):
                new_token = os.getenv("BOCCO_ACCESS_TOKEN")
                return get_sensors(room_uuid, new_token)
            else:
                print("[ERROR] トークン更新に失敗しました")
                return []
        
        response.raise_for_status()
        
        # レスポンスを解析
        try:
            data = response.json()
            # レスポンスがリスト形式か、オブジェクト形式かを判定
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # sensors キーがあればそれを返す
                if "sensors" in data:
                    sensors = data["sensors"]
                    if isinstance(sensors, list):
                        return sensors
                return []
            else:
                return []
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON解析エラー: {e}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] センサ一覧の取得に失敗しました (部屋UUID: {room_uuid}): {e}")
        return []


def print_room_info():
    """
    部屋情報とセンサ情報を取得して表示
    """
    print("=" * 80)
    print("BOCCO 部屋情報とセンサ情報")
    print("=" * 80)
    
    # 部屋一覧を取得
    print("\n[INFO] 部屋一覧を取得中...")
    rooms = get_rooms()
    
    if not rooms or not isinstance(rooms, list):
        print("[WARNING] 部屋が見つかりません")
        print(f"[DEBUG] rooms の型: {type(rooms)}, 値: {rooms}")
        return
    
    print(f"\n[OK] {len(rooms)}個の部屋が見つかりました\n")
    
    # 各部屋の情報を表示
    for i, room in enumerate(rooms, 1):
        # room がリストまたは辞書でない場合のチェック
        if not isinstance(room, dict):
            print(f"[WARNING] 予期しない部屋データ形式: {type(room)}")
            continue
        
        room_uuid = room.get("uuid")
        room_name = room.get("name", "Unknown")
        room_nickname = room.get("nickname", "")
        serial_number = room.get("serial_number", "")
        
        print(f"{'='*80}")
        print(f"部屋 #{i}")
        print(f"{'='*80}")
        print(f"  名前: {room_name}")
        print(f"  ニックネーム: {room_nickname}")
        print(f"  UUID: {room_uuid}")
        print(f"  シリアル番号: {serial_number}")
        
        # この部屋のセンサ情報を取得
        print(f"\n  [INFO] センサ情報を取得中...")
        sensors = get_sensors(room_uuid)
        
        if not sensors or not isinstance(sensors, list):
            print(f"  [WARNING] センサが見つかりません")
        else:
            print(f"  [OK] {len(sensors)}個のセンサが見つかりました\n")
            
            # センサ情報を表示
            for j, sensor in enumerate(sensors, 1):
                if not isinstance(sensor, dict):
                    print(f"    [WARNING] 予期しないセンサデータ形式: {type(sensor)}")
                    continue
                
                sensor_uuid = sensor.get("uuid")
                sensor_type = sensor.get("type", "Unknown")
                sensor_name = sensor.get("name", "")
                sensor_nickname = sensor.get("nickname", "")
                
                print(f"    センサ #{j}")
                print(f"      タイプ: {sensor_type}")
                print(f"      名前: {sensor_name}")
                print(f"      ニックネーム: {sensor_nickname}")
                print(f"      UUID: {sensor_uuid}")
                print()
        
        print()


def print_room_info_json():
    """
    部屋情報とセンサ情報をJSON形式で取得して表示
    """
    print("=" * 80)
    print("BOCCO 部屋情報とセンサ情報 (JSON形式)")
    print("=" * 80)
    
    # 部屋一覧を取得
    print("\n[INFO] 部屋一覧を取得中...")
    rooms = get_rooms()
    
    if not rooms:
        print("[WARNING] 部屋が見つかりません")
        return
    
    print(f"\n[OK] {len(rooms)}個の部屋が見つかりました\n")
    
    # すべての部屋情報を集約
    all_rooms_data = []
    
    for room in rooms:
        room_uuid = room.get("uuid")
        room_name = room.get("name", "Unknown")
        
        # この部屋のセンサ情報を取得
        print(f"[INFO] {room_name} のセンサ情報を取得中...")
        sensors = get_sensors(room_uuid)
        
        room_data = {
            "room": room,
            "sensors": sensors
        }
        all_rooms_data.append(room_data)
    
    # JSON形式で表示
    print("\n[JSON出力]\n")
    print(json.dumps(all_rooms_data, indent=2, ensure_ascii=False))


def export_room_info_to_file(filename="room_info.json"):
    """
    部屋情報とセンサ情報をJSONファイルに保存
    
    Parameters:
    -----------
    filename : str
        保存先ファイル名
    """
    print(f"[INFO] 部屋情報を {filename} に保存中...")
    
    # 部屋一覧を取得
    rooms = get_rooms()
    
    if not rooms:
        print("[WARNING] 部屋が見つかりません")
        return
    
    # すべての部屋情報を集約
    all_rooms_data = []
    
    for room in rooms:
        room_uuid = room.get("uuid")
        room_name = room.get("name", "Unknown")
        
        # この部屋のセンサ情報を取得
        print(f"[INFO] {room_name} のセンサ情報を取得中...")
        sensors = get_sensors(room_uuid)
        
        room_data = {
            "room": room,
            "sensors": sensors
        }
        all_rooms_data.append(room_data)
    
    # JSONファイルに保存
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_rooms_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] {filename} に保存しました")
    except Exception as e:
        print(f"[ERROR] ファイル保存に失敗しました: {e}")


# ========================================
# メイン処理
# ========================================

def main():
    """
    メイン処理
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="BOCCO の部屋情報とセンサ情報を取得して表示"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で出力"
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="指定したファイル名でJSONファイルに保存"
    )
    
    args = parser.parse_args()
    
    if args.save:
        # ファイルに保存
        export_room_info_to_file(args.save)
    elif args.json:
        # JSON形式で表示
        print_room_info_json()
    else:
        # 通常形式で表示
        print_room_info()


if __name__ == "__main__":
    main()
