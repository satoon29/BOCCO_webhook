from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])  # ← GETも許可
def webhook():
    print(f"リクエストメソッド: {request.method}")
    if request.method == "GET":
        return "✅ Flaskは動いてるよ！", 200

    # POSTのとき（BOCCO emoから通知が来たとき）
    data = request.get_json(force=True, silent=True)
    print("📦 受け取ったデータ:", data)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)  # ← 外部アクセス対応
