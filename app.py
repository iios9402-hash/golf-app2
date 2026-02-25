# app.py
import json
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

# ----------------------------
# 設定
# ----------------------------
WEATHER_FILE = "weather.json"
DEFAULT_EMAILS = ["iios9402@yahoo.co.jp"]
XSERVER_SMTP = "ssl://smtp.xserver.jp"
XSERVER_PORT = 465
XSERVER_USER = st.secrets.get("XSERVER_USER")
XSERVER_PASS = st.secrets.get("XSERVER_PASS")
RESERVE_URL = "https://reserve.yaita-cc.com/"
TENKI_URL = "https://tenki.jp/leisure/golf/3/12/644217/week.html"

# ----------------------------
# データ読み込み
# ----------------------------
def load_weather():
    path = Path(WEATHER_FILE)
    if not path.exists():
        st.error(f"天気データが存在しません: {WEATHER_FILE}")
        return []
    with open(WEATHER_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            st.error("weather.json の読み込みに失敗しました")
            return []

# ----------------------------
# 判定ロジック
# ----------------------------
def judge_day(day, index):
    """
    百十番様規定判定
    - 通常：1-10,14日目 → 降水量>=1.0mm, 風>=5.0 → ×
    - 警戒：11-13日目 → 上記に加え「雨」の文字で不可
    """
    try:
        p = float(day.get("precipitation", 0))
    except:
        p = 0.0
    try:
        w = float(day.get("wind", 0))
    except:
        w = 0.0
    weather_text = day.get("weather", "")

    if index <= 9 or index == 13:
        if p >= 1.0 or w >= 5.0:
            return "× 不可", "降水量/風速超過"
    elif 10 <= index <= 12:
        if p >= 1.0 or w >= 5.0 or "雨" in weather_text:
            return "× 不可", "警戒期間: 降水量/風速/雨"
    return "○ 可", ""

# ----------------------------
# メール送信
# ----------------------------
def send_mail(subject, body, recipients):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = XSERVER_USER
    msg["To"] = ", ".join(recipients)

    try:
        server = smtplib.SMTP_SSL("smtp.xserver.jp", XSERVER_PORT)
        server.login(XSERVER_USER, XSERVER_PASS)
        server.send_message(msg)
        server.quit()
        st.success("メール送信成功")
    except Exception as e:
        st.error(f"メール送信失敗: {e}")

# ----------------------------
# Streamlit UI
# ----------------------------
def main():
    st.title("矢板カントリークラブ 予約最適化システム")

    st.markdown(f"[情報源: tenki.jp 矢板カントリークラブ２週間予報]({TENKI_URL})")

    weather_data = load_weather()
    if not weather_data:
        st.warning("天気データがありません。update_weather.py を実行してください。")
        return

    emails = st.text_area("通知先メールアドレス（カンマ区切り）", ", ".join(DEFAULT_EMAILS))
    email_list = [e.strip() for e in emails.split(",") if e.strip()]

    # 判定列を追加
    table_data = []
    for idx, day in enumerate(weather_data):
        judge, reason = judge_day(day, idx)
        table_data.append({
            "日付": f"{day.get('date')} ({day.get('曜日')})",
            "天気": day.get("weather"),
            "降水量(mm)": day.get("precipitation"),
            "風速(m/s)": day.get("wind"),
            "判定": judge,
            "理由": reason
        })

    st.table(table_data)

    # 公式予約ボタン
    st.markdown(f"[公式予約サイトへ]({RESERVE_URL})")

    # メール送信
    if st.button("判定結果をメール送信"):
        body_lines = []
        for row in table_data:
            body_lines.append(f"{row['日付']}: {row['天気']}, 降水量 {row['降水量(mm)']}mm, 風速 {row['風速(m/s)']}m/s → {row['判定']} ({row['理由']})")
        body_text = "\n".join(body_lines)
        send_mail("監視状況レポート", body_text, email_list)

if __name__ == "__main__":
    main()
