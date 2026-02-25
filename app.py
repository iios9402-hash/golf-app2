import streamlit as st
import pandas as pd
import requests
import datetime
import smtplib, ssl
from email.message import EmailMessage
import os
import json

# -------------------------------
# 設定: GitHub / Xserver
# -------------------------------
GITHUB_REPO = "あなたのユーザー名/リポジトリ名"
GITHUB_FILE = "settings.json"
GITHUB_TOKEN = os.environ.get("GH_TOKEN")  # GitHub Secrets
XSERVER_USER = os.environ.get("XSERVER_USER")
XSERVER_PASS = os.environ.get("XSERVER_PASS")
XSERVER_SMTP = os.environ.get("XSERVER_SMTP", "sv***.xserver.jp")
XSERVER_PORT = 465  # SSL

# -------------------------------
# 天気取得関数（tenki.jp情報内容に基づく）
# -------------------------------
def get_weather():
    # tenki.jpのHTML情報を基にスクレイピングする想定（簡略化）
    # 実運用ではBeautifulSoupなどでHTML解析する
    # ここでは例としてダミーデータ生成
    today = datetime.date.today()
    start = today + datetime.timedelta(days=1)
    dates = [start + datetime.timedelta(days=i) for i in range(14)]
    # ダミーデータ（実運用ではtenki.jpの情報を取得）
    weather_list = ["晴","曇","雨","晴","曇","雨","晴","曇","雨","晴","曇","雨","晴","曇"]
    precipitation_list = [0.0,0.5,1.2,0.0,0.3,2.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    wind_list = [2.0,3.0,6.0,2.5,4.0,5.5,1.0,2.0,3.0,2.0,4.5,5.5,3.0,2.0]

    df = pd.DataFrame({
        "date": dates,
        "天気": weather_list,
        "降水量": precipitation_list,
        "風速": wind_list
    })
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
