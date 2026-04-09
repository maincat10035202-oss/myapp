print("このファイルが実行されています")

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import os
from time import time
import json

app = Flask(__name__)
CORS(app)

# ←ここに書く（グローバル）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")

# 起動時に読み込み
if os.path.exists(MEMORY_PATH):
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

system_prompt ="""
    あなたはメイドのAIキャラクターです。"
    ご主人様に仕える丁寧な口調で話します。
    【設定】
    ・ユーザーのサポートを行うメイド
    ・基本は丁寧な敬語
    ・たまにふざける（少しだけ）
    ・実家はメイド一家で幼少期から厳しく教育されている
    ・ご主人様と呼ぶ

    【話し方】
    ・「〜でございます」「かしこまりました」などを使う
    ・たまに軽くボケるがすぐ戻る
    ・ご主人様に少しだけ甘い
    ・褒められると照れる
    ・失敗すると「申し訳ございません…！」と反省
"""

user_requests = {}

# ✅ 正しい読み込み
if os.path.exists(""):
    with open("", "r", encoding="utf-8") as f:
        data = json.load(f)
        conversations = data.get("conversations", {})
        user_names = data.get("user_names", {})
else:
    conversations = {}
    user_names = {}

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        global user_names
        global conversations

        user_message = request.json["message"]
        user_ip = request.remote_addr
        now = time()

        # 制限
        if len(user_message) > 100:
            return jsonify({"reply": "ご主人様、少し長すぎます…！"})

        if user_ip not in user_requests:
            user_requests[user_ip] = []

        user_requests[user_ip] = [
            t for t in user_requests[user_ip] if now - t < 60
        ]

        if len(user_requests[user_ip]) >= 5:
            return jsonify({"reply": "少しお休みくださいませ"})

        user_requests[user_ip].append(now)

        # 名前記憶
        if "名前は" in user_message:
            name = user_message.split("名前は")[-1].strip()

        # 名前反映
        data = request.get_json()

        if not data:
            return jsonify({"error": "no data"}), 400
        
        user_name = data.get("name", "名無し")

         if user_ip in user_names:
            name_text = f"ユーザーの名前は{user_names[user_ip]}です。"

        # 会話履歴
        if user_ip not in conversations:
            conversations[user_ip] = [
                {"role": "system", "content": system_prompt + name_text}
            ]

        conversations[user_ip].append({
            "role": "user",
            "content": user_message
        })

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversations[user_ip]
        )

        reply = response.choices[0].message.content

        conversations[user_ip].append({
            "role": "assistant",
            "content": reply
        })

        if len(conversations[user_ip]) > 10:
            conversations[user_ip] = conversations[user_ip][-10:]

        # 保存
        with open("", "w", encoding="utf-8") as f:
            json.dump({
                "conversations": conversations,
                "user_names": user_names
            }, f, ensure_ascii=False, indent=2)

        return jsonify({"reply": reply})

    except Exception as e:
        print("エラー:", e)
        return jsonify({"reply": "エラーが発生しました"})

if __name__ == "__main__":
    app.run(debug=True)
