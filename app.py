import streamlit as st
import requests
import pandas as pd
import datetime
import json
import base64
import os
import smtplib
import ssl
from email.message import EmailMessage

# =========================
# 設定
# =========================
LAT = 36.8091
LON = 139.9073
GITHUB_REPO = "YOUR_GITHUB_ID/YOUR_REPO_NAME"
SETTINGS_FILE = "settings.json"
BRANCH = "main"

GH_TOKEN = os.getenv("GH_TOKEN")
XSERVER_USER = os.getenv("XSERVER_USER")
XSERVER_PASS = os.getenv("XSERVER_PASS")
XSERVER_SMTP = os.getenv("XSERVER_SMTP")  # 例: sv1234.xserver.jp

DEFAULT_EMAIL = "iios9402@yahoo.co.jp"

# =========================
# GitHub保存処理
# =========================
def load_settings():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SETTINGS_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode()
        return json.loads(content), r.json()["sha"]
    else:
        return {"reserved_date": "", "emails": [DEFAULT_EMAIL]}, None

def save_settings(data, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SETTINGS_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    encoded = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
    payload = {
        "message": "Update settings",
        "content": encoded,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
    requests.put(url, headers=headers, json=payload)

# =========================
# 天気取得
# =========================
def get_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}"
        f"&daily=weathercode,precipitation_sum,windspeed_10m_max"
        f"&forecast_days=14&timezone=Asia/Tokyo"
        f"&models=jma"
    )
    r = requests.get(url)
    data = r.json()["daily"]
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])
    return df

# =========================
# 判定ロジック
# =========================
def judge_weather(df):
    results = []
    for i, row in df.iterrows():
        rain = row["precipitation_sum"]
        wind = row["windspeed_10m_max"]

        reason = []
        status = "○ 可"

        if rain >= 1.0:
            status = "× 不可"
            reason.append("降水量超過")
        if wind >= 5.0:
            status = "× 不可"
            reason.append("風速超過")

        # 11-13日目は警戒期間
        if 10 <= i <= 12:
            if rain > 0:
                status = "× 不可"
                reason.append("警戒期間の降雨")

        results.append({
            "曜日付き日付": row["time"].strftime("%m/%d(%a)"),
            "天気": row["weathercode"],
            "判定": status,
            "理由": ",".join(reason) if reason else "基準内"
        })

    return pd.DataFrame(results)

# =========================
# メール送信（Xserver）
# =========================
def send_mail(subject, body, recipients):
    msg = EmailMessage()
    msg["From"] = XSERVER_USER
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(XSERVER_SMTP, 465, context=context) as server:
        server.login(XSERVER_USER, XSERVER_PASS)
        for mail in recipients:
            msg["To"] = mail
            server.send_message(msg)

# =========================
# UI
# =========================
st.set_page_config(layout="wide")
st.title("矢板カントリークラブ 予約監視")

settings, sha = load_settings()

df_raw = get_weather()
df = judge_weather(df_raw)

st.table(df)

# 予約日チェック
reserved = settings.get("reserved_date")
emails = settings.get("emails", [DEFAULT_EMAIL])

if reserved:
    reserved_dt = pd.to_datetime(reserved)
    match = df_raw[df_raw["time"] == reserved_dt]
    if not match.empty:
        idx = match.index[0]
        result = df.iloc[idx]["判定"]
        if "×" in result:
            st.error(f"{reserved} は不可")
        else:
            st.success(f"{reserved} は良好")

# 設定UI
st.divider()
new_date = st.date_input("予約日設定")
new_email = st.text_input("追加メールアドレス")

if st.button("設定を完全に保存する"):
    if new_email:
        emails.append(new_email)
    settings = {
        "reserved_date": str(new_date),
        "emails": list(set(emails))
    }
    save_settings(settings, sha)
    st.success("保存完了")

if st.button("現在の監視状況を全宛先へ送信"):
    body = df.to_string()
    send_mail("監視状況レポート", body, emails)
    st.success("送信完了")

st.divider()
st.markdown("[情報源: tenki.jp 矢板カントリークラブ２週間予報](https://tenki.jp/leisure/golf/3/12/644217/week.html)")
