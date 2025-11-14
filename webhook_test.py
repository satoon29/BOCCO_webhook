import sys
import io
from flask import Flask, request

# Windows環境での文字コード対応
if sys.platform == "win32":
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    print(f"リクエストメソッド: {request.method}")
    if request.method == "GET":
        return "[OK] Flaskは動いてるよ！", 200

    # POSTのとき（BOCCO emoから通知が来たとき）
    data = request.get_json(force=True, silent=True)
    print("[INFO] 受け取ったデータ:", data)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
