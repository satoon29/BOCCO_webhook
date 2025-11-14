import requests
import os
import sys
from pathlib import Path

# Windows環境での文字コード対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

refresh_token = "db43b831-d523-4f4e-9f81-72e243b8be3c"
auth_url = "https://platform-api.bocco.me/oauth/token/refresh"

def refresh_access_token():
    response = requests.post(auth_url, json={"refresh_token": refresh_token})
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("[OK] 新しいアクセストークン:", access_token)
        
        # .envファイルを更新
        update_env_token(access_token)
        return access_token
    else:
        print("[ERROR] リフレッシュ失敗:", response.status_code, response.text)
        return None

def update_env_token(new_token):
    """
    .envファイルのBOCCO_ACCESS_TOKENを更新
    """
    env_path = Path(".env")
    if not env_path.exists():
        print("[WARNING] .env ファイルが見つかりません")
        return
    
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    with open(env_path, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("BOCCO_ACCESS_TOKEN="):
                f.write(f'BOCCO_ACCESS_TOKEN="{new_token}"\n')
            else:
                f.write(line)
    
    print("[OK] .env ファイルを更新しました")

access_token = refresh_access_token()
if access_token is None:
    raise Exception("[ERROR] アクセストークンの取得に失敗しました")

# 重要: /webhook を末尾に追加！
webhook_url = "https://ddea9d11242c.ngrok-free.app/webhook"  # ← /webhook を追加

# Webhook登録
print("\n[INFO] Webhook登録中...")
res1 = requests.post(
    "https://platform-api.bocco.me/v1/webhook",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json={
        "description": "my webhook",
        "url": webhook_url
    }
)
print("Webhook登録:", res1.status_code, res1.text)

# イベント登録（人感センサー）
print("\n[INFO] イベント登録中...")
res2 = requests.put(
    "https://platform-api.bocco.me/v1/webhook/events",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json={
        "events": ["human_sensor.detected"]
    }
)
print("イベント登録:", res2.status_code, res2.text)

if res1.status_code == 201 and res2.status_code == 200:
    print("\n[OK] すべての登録に成功しました！")
else:
    print("\n[WARNING] 登録に失敗した可能性があります")

