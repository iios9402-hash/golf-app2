import streamlit as st
import pandas as pd
import requests
import datetime
from bs4 import BeautifulSoup
import smtplib, ssl
from email.message import EmailMessage
import os

# -------------------------------
# 設定: GitHub / Xserver
# -------------------------------
XSERVER_USER = os.environ.get("XSERVER_USER")
XSERVER_PASS = os.environ.get("XSERVER_PASS")
XSERVER_SMTP = os.environ.get("XSERVER_SMTP", "sv***.xserver.jp")
XSERVER_PORT = 465  # SSL

TENKI_URL = "https://tenki.jp/leisure/golf/3/12/644217/week.html"

# -------------------------------
# tenki.jp から HTML 解析
# -------------------------------
def get_weather():
    res = requests.get(TENKI_URL)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    # 予報テーブルを抽出（ページ構造に合わせて調整）
    # tenki.jpでは日別予報の <tr class="weather-table__body-tr"> に情報がある場合が多い
    table_rows = soup.select("table.weather-weekly__table tbody tr")
    
    dates, weathers, precipitations, winds = [], [], [], []

    today = datetime.date.today()
    start = today + datetime.timedelta(days=1)
    end = start + datetime.timedelta(days=14)

    # ダミー初期化（実運用ではHTML構造を確認して正確に取得）
    for i in range(14):
        day = start + datetime.timedelta(days=i)
        dates.append(day)
        # ここでは例として取得できる情報がなければダミー
        weathers.append("晴")  # 実運用では soup.select + .text で取得
        precipitations.append(0.0)  # mm
        winds.append(2.0)  # m/s

    df = pd.DataFrame({
        "date": dates,
        "天気": weathers,
        "降水量": precipitations,
        "風速": winds
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
        if (day_index <=10 or day_index==14):
            if rain >= 1.0: reason.append(f"降水量 {rain}mm"); ok=False
            if wind >=5.0: reason.append(f"風速 {wind}m/s"); ok=False
        else:
            if rain >=1.0: reason.append(f"降水量 {rain}mm"); ok=False
            if wind >=5.0: reason.append(f"風速 {wind}m/s"); ok=False
            if "雨" in text: reason.append("天気に雨"); ok=False
        judgments.append("○ 可" if ok else "× 不可")
        reasons.append(", ".join(reason))
    df["判定"] = judgments
    df["理由"] = reasons

    return df[["曜日付き日付","天気","判定","理由"]]

# -------------------------------
# メール送信（UTF-8対応）
# -------------------------------
def send_mail(subject, body, emails):
    msg = EmailMessage()
    msg["From"] = XSERVER_USER
    msg["To"] = ", ".join(emails)
    msg["Subject"] = subject
    msg.set_content(body, charset="utf-8")

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
