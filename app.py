import streamlit as st
import pandas as pd
import requests
import datetime
import smtplib, ssl
import json
from email.message import EmailMessage
import os

# -------------------------------
# 設定: GitHub / Xserver
# -------------------------------
GITHUB_REPO = "あなたのユーザー名/リポジトリ名"
GITHUB_FILE = "settings.json"
GITHUB_TOKEN = os.environ.get("GH_TOKEN")  # GitHub Secrets
XSERVER_USER = os.environ.get("XSERVER_USER")
XSERVER_PASS = os.environ.get("XSERVER_PASS")
XSERVER_SMTP = os.environ.get("XSERVER_SMTP", "sv***.xserver.jp")  # Xserver SMTPサーバー
XSERVER_PORT = 465  # SSL

# -------------------------------
# 天気取得関数
# -------------------------------
def get_weather():
    lat, lon = 36.8091, 139.9073
    today = datetime.date.today()
    start = today + datetime.timedelta(days=1)  # 翌日から
    end = start + datetime.timedelta(days=14)  # 14日間

    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=weathercode,precipitation_sum,windspeed_10m_max&timezone=Asia/Tokyo"
        f"&start_date={start}&end_date={end}"
    )
    r = requests.get(url)
    data = r.json()["daily"]

    df = pd.DataFrame({
        "date": pd.to_datetime(data["time"]),
        "天気コード": data["weathercode"],
        "降水量": data["precipitation_sum"],
        "風速": data["windspeed_10m_max"],
    })

    # 天気コードを日本語に変換
    weather_map = {0:"晴",1:"晴時々曇",2:"曇",3:"雨",45:"霧",48:"霧雨",51:"小雨",53:"小雨",55:"小雨",61:"雨",63:"雨",65:"雨",71:"雪",73:"雪",75:"雪",80:"にわか雨",81:"にわか雨",82:"にわか雨",95:"雷雨",96:"雷雨",99:"雷雨"}
    df["天気"] = df["天気コード"].map(lambda x: weather_map.get(x, "不明"))

    # 曜日付き日付
    df["曜日付き日付"] = df["date"].dt.strftime("%m/%d (%a)")

    # 判定・理由
    judgments = []
    reasons = []
    for i, row in df.iterrows():
        day_index = i + 1
        rain = row["降水量"]
        wind = row["風速"]
        text = row["天気"]
        reason = []
        ok = True
        # 判定
        if (day_index <=10 or day_index==14):
            if rain >= 1.0: reason.append(f"降水量 {rain}mm"); ok=False
            if wind >=5.0: reason.append(f"風速 {wind}m/s"); ok=False
        else:  # 11-13日目
            if rain >=1.0: reason.append(f"降水量 {rain}mm"); ok=False
            if wind >=5.0: reason.append(f"風速 {wind}m/s"); ok=False
            if "雨" in text: reason.append("天気に雨"); ok=False
        judgments.append("○ 可" if ok else "× 不可")
        reasons.append(", ".join(reason))
    df["判定"] = judgments
    df["理由"] = reasons

    return df[["曜日付き日付","天気","判定","理由"]]

# -------------------------------
# GitHub Persistence
# -------------------------------
def load_settings():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    r = requests.get(url, headers=headers)
    content = json.loads(requests.utils.unquote(r.json()["content"]))
    return content

def save_settings(data):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    payload = {
        "message": "update settings",
        "content": json.dumps(data),
        "branch": "main"
    }
    requests.put(url, headers=headers, data=json.dumps(payload))

# -------------------------------
# メール送信（UTF-8対応）
# -------------------------------
def send_mail(subject, body, emails):
    msg = EmailMessage()
    msg["From"] = XSERVER_USER
    msg["To"] = ", ".join(emails)
    msg["Subject"] = subject
    msg.set_content(body, charset="utf-8")  # ← UTF-8対応

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(XSERVER_SMTP, XSERVER_PORT, context=context) as server:
        server.login(XSERVER_USER, XSERVER_PASS)
        server.send_message(msg)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("矢板カントリークラブ 予約最適化システム")

# 予約日設定
st.subheader("予約日設定")
selected_date = st.date_input("予約日を選択", datetime.date.today() + datetime.timedelta(days=1))

# 通知先管理
st.subheader("通知先管理")
emails_text = st.text_area("通知先メールアドレス（カンマ区切り）", "iios9402@yahoo.co.jp")
emails = [e.strip() for e in emails_text.split(",") if e.strip()]

# 天気取得
df = get_weather()
st.subheader("2週間天気予報")
st.table(df)

# 判定アラート
today_row = df[df["曜日付き日付"].str.contains(selected_date.strftime("%m/%d"))]
if not today_row.empty:
    st.subheader("予約日判定")
    row = today_row.iloc[0]
    if row["判定"].startswith("×"):
        st.error(f'{row["判定"]} : {row["理由"]}')
    else:
        st.success(f'{row["判定"]} : {row["理由"]}')

# テスト送信ボタン
st.subheader("メール送信テスト")
test_email = st.text_input("テスト送信先メールアドレス", "iios9402@yahoo.co.jp")
if st.button("テスト送信"):
    try:
        send_mail("監視状況レポート", df.to_string(), [test_email])
        st.success("送信成功！メールを確認してください。")
    except Exception as e:
        st.error(f"送信失敗: {e}")

# tenki.jp リンク
st.markdown('[情報源: tenki.jp 矢板カントリークラブ２週間予報](https://tenki.jp/leisure/golf/3/12/644217/week.html)')
