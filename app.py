import streamlit as st
import pandas as pd
import datetime
import json
import os
import smtplib, ssl
from email.message import EmailMessage

# -------------------------------
# Xserver SMTP設定（環境変数推奨）
# -------------------------------
XSERVER_USER = os.environ.get("XSERVER_USER")
XSERVER_PASS = os.environ.get("XSERVER_PASS")
XSERVER_SMTP = os.environ.get("XSERVER_SMTP", "sv***.xserver.jp")
XSERVER_PORT = 465  # SSL

# -------------------------------
# JSONデータ読み込み
# -------------------------------
def load_weather_from_json(json_path="weather.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["曜日付き日付"] = df["date"].dt.strftime("%m/%d (%a)")
        df.rename(columns={"weather":"天気","precipitation":"降水量","wind":"風速"}, inplace=True)
        return df[["曜日付き日付","天気","降水量","風速"]]
    except Exception as e:
        st.error(f"天気データ読み込み失敗: {e}")
        return pd.DataFrame(columns=["曜日付き日付","天気","降水量","風速"])

# -------------------------------
# 判定ロジック（百十番様ルール）
# -------------------------------
def add_judgment(df):
    judgments, reasons = [], []
    for i, row in df.iterrows():
        idx = i + 1
        rain = row["降水量"]
        wind = row["風速"]
        text = row["天気"]
        ok = True
        reason = []
        if idx <=10 or idx==14:
            if rain >= 1.0: reason.append(f"降水量 {rain}mm"); ok=False
            if wind >= 5.0: reason.append(f"風速 {wind}m/s"); ok=False
        else:
            if rain >= 1.0: reason.append(f"降水量 {rain}mm"); ok=False
            if wind >= 5.0: reason.append(f"風速 {wind}m/s"); ok=False
            if "雨" in text: reason.append("天気に雨"); ok=False
        judgments.append("○ 可" if ok else "× 不可")
        reasons.append(", ".join(reason))
    df["判定"] = judgments
    df["理由"] = reasons
    return df

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
df = load_weather_from_json()
df = add_judgment(df)

st.subheader("2週間天気予報（ChatGPT提供データ）")
st.table(df)

# 予約日判定
today_row = df[df["曜日付き日付"].str.contains(selected_date.strftime("%m/%d"))]
if not today_row.empty:
    st.subheader("予約日判定")
    row = today_row.iloc[0]
    if row["判定"].startswith("×"):
        st.error(f'{row["判定"]} : {row["理由"]}')
    else:
        st.success(f'{row["判定"]} : {row["理由"]}')

# テスト送信
st.subheader("メール送信テスト")
test_email = st.text_input("テスト送信先", "iios9402@yahoo.co.jp")
if st.button("テスト送信"):
    try:
        send_mail("監視状況レポート", df.to_string(), [test_email])
        st.success("送信成功！メールを確認してください。")
    except Exception as e:
        st.error(f"送信失敗: {e}")

# 情報源リンク
st.markdown('[情報源: tenki.jp 矢板カントリークラブ２週間予報](https://tenki.jp/leisure/golf/3/12/644217/week.html)')
