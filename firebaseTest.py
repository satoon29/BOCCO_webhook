import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
from datetime import datetime

# Firebase管理者SDKの認証情報を設定
cred = credentials.Certificate("emoji-test-aad3a-firebase-adminsdk-fbsvc-0d3087024f.json")
firebase_admin.initialize_app(cred)

# Firestoreクライアントを初期化
db = firestore.client()

# 今日の日付のUTC範囲を取得
now = datetime.now()
today = now.date()

# 今日の日付を"YYYY/MM/DD"形式の文字列に変換
today_str = today.strftime("%Y/%m/%d")
print(f"検索対象の日付: {today_str}")

# 'first-emoji'コレクションから、'day'フィールドが今日の日付と一致するドキュメントのみを取得
query = db.collection('first-emoji').where(filter=FieldFilter('day', '==', today_str))

docs = list(query.stream())
if not docs:
    print("本日分の絵文字データはないよ！")
else:
    for doc in docs:
        data = doc.to_dict()
        print(f"ドキュメントID: {doc.id}, データ: {data}")

