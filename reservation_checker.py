import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =====================
# 1. GitHub Persistence Module
# =====================
GITHUB_REPO = "iios9402-hash/golf-app2"
SETTINGS_FILE = "settings.json"
GH_TOKEN = os.getenv("GH_TOKEN")

def load_settings():
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{SETTINGS_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}"} if GH_TOKEN else {}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return {"reserved_date": None, "emails": ["iios9402@yahoo.co.jp"]}
    return r.json()

settings = load_settings()
reserved_date_str = settings.get("reserved_date")
emails = settings.get("emails", ["iios9402@yahoo.co.jp"])
reserved_date = datetime.strptime(reserved_date_str, "%Y-%m-%d") if reserved_date_str else None

# =====================
# 2. Weather Engine
# =====================
# Open-Meteo API: 矢板カントリークラブ座標
LAT, LON = 36.8091, 139.9073
API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=weathercode,precipitation_sum,windspeed_10m_max&timezone=Asia/Tokyo"

resp = requests.get(API_URL)
data = resp.json()
daily = data["daily"]
df = pd.DataFrame({
    "date": daily["time"],
    "weather": daily["weathercode"],
    "precipitation": daily["precipitation_sum"],
    "wind": daily["windspeed_10m_max"]
})
df["date"] = pd.to_datetime(df["date"])

# =====================
# 3. 判定ロジック
# =====================
def weather_text(code):
    # 簡易変換: 0=晴, 雨=雨など
    mapping = {0: "晴", 1: "曇", 2: "雨"}
    return mapping.get(code, "不明")

def judge(row, idx):
    # 判定期間
    if idx < 10 or idx == 13:  # 0-9, 13 → 通常
        if row["precipitation"] >= 1.0 or row["wind"] >= 5.0:
            return "× 不可", "数値基準超過"
    else:  # 11-13日目 → 警戒
        if row["precipitation"] >= 1.0 or row["wind"] >= 5.0 or "雨" in weather_text(row["weather"]):
            return "× 不可", "警戒条件"
    return "◯ 可", ""

df["判定"] = ""
df["理由"] = ""
for i, row in df.iterrows():
    result, reason = judge(row, i)
    df.at[i, "判定"] = result
    df.at[i, "理由"] = reason

# =====================
# 4. メール送信 (Xサーバー SMTP)
# =====================
SMTP_SERVER = os.getenv("XSERVER_SMTP")
SMTP_PORT = int(os.getenv("XSERVER_PORT"))
SMTP_USER = os.getenv("XSERVER_USER")
SMTP_PASS = os.getenv("XSERVER_PASS")

def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(emails)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, emails, msg.as_string())
        print("メール送信成功")
    except Exception as e:
        print("メール送信失敗:", e)

# 予約日判定
if reserved_date:
    target = df[df["date"] == reserved_date]
    if not target.empty:
        row = target.iloc[0]
        print("=== 予約日判定 ===")
        print(f"日付: {reserved_date.strftime('%Y-%m-%d (%a)')}")
        print(f"天気: {weather_text(row['weather'])}")
        print(f"判定: {row['判定']}")
        print(f"理由: {row['理由']}")
        if row["判定"].startswith("×"):
            send_email(f"予約不可: {reserved_date.strftime('%Y-%m-%d')}",
                       f"予約日 {reserved_date.strftime('%Y-%m-%d')} は不可です。\n理由: {row['理由']}")

# =====================
# 5. 強制送信テスト機能
# =====================
TEST_MODE = os.getenv("TEST_MODE", "0") == "1"
if TEST_MODE:
    print("=== 強制送信テスト ===")
    send_email("テスト送信", "これは強制送信テストです。")
