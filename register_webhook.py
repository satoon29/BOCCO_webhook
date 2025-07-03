import requests


refresh_token = "db43b831-d523-4f4e-9f81-72e243b8be3c"
auth_url = "https://platform-api.bocco.me/oauth/token/refresh"

def refresh_access_token():
    response = requests.post(auth_url, json={"refresh_token": refresh_token})
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("新しいアクセストークン:", access_token)
        return access_token
    else:
        print("リフレッシュ失敗:", response.status_code, response.text)
        return None
    

access_token = refresh_access_token()
if access_token is None:
    raise Exception("アクセストークンの取得に失敗しました")
webhook_url = "https://cb9b-133-19-169-3.ngrok-free.app/webhook"  # 上で出たngrokのURL！

# Webhook登録
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

