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
# 基本設定
# =========================
LAT = 36.8091
LON = 139.9073
GITHUB_REPO = "YOUR_GITHUB_ID/YOUR_REPO_NAME"
SETTINGS_FILE = "settings.json"
BRANCH = "main"

GH_TOKEN = os.getenv("GH_TOKEN")
XSERVER_USER = os.getenv("XSERVER_USER")
XSERVER_PASS = os.getenv("XSERVER_PASS")
XSERVER_SMTP = os.getenv("XSERVER_SMTP")

DEFAULT_EMAIL = "iios9402@yahoo.co.jp"

# =========================
# 天気コード → 日本語
# =========================
WEATHER_MAP = {
    0: "晴れ",
    1: "主に晴れ",
    2: "部分的に曇り",
    3: "曇り",
    45: "霧",
    48: "霧（凍結）",
    51: "小雨",
    53: "中雨",
    55: "強い雨",
    56: "小雪混じり雨",
    57: "強い雪混じり雨",
    61: "小雨",
    63: "中雨",
    65: "強い雨",
    66: "小雪混じり雨",
    67: "強い雪混じり雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "霰",
    80: "雨",
    81: "強い雨",
    82: "豪雨",
    85: "雪",
    86: "強い雪",
    95: "雷雨",
    96: "雷雨 + 雪",
    99: "暴風雨",
}

# =========================
# GitHub設定読込
# =========================
def load_settings():
    if not GH_TOKEN:
        return {"reserved_date": "", "emails": [DEFAULT_EMAIL]}, None
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SETTINGS_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode()
        return json.loads(content), r.json()["sha"]
    return {"reserved_date": "", "emails": [DEFAULT_EMAIL]}, None

def save_settings(data, sha):
    if not GH_TOKEN:
        return
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
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&daily=weathercode,precipitation_sum,windspeed_10m_max"
        "&forecast_days=15"
        "&timezone=Asia/Tokyo"
    )
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f"API接続失敗: {r.status_code}")
    data = r.json()
    if "daily" not in data:
        raise Exception(f"API異常レスポンス: {data}")
    df = pd.DataFrame(data["daily"])
    df["time"] = pd.to_datetime(df["time"])
    # 翌日から14日間
    df = df.iloc[1:15].reset_index(drop=True)
    df["weather_text"] = df["weathercode"].map(lambda x: WEATHER_MAP.get(x, "不明"))
    return df

# =========================
# 判定ロジック
# =========================
def judge_weather(df):
    results = []
    for i, row in df.iterrows():
        rain = row["precipitation_sum"]
        wind = row["windspeed_10m_max"]
        status = "○ 可"
        reason = []

        if i in range(0,10) or i == 13:  # 通常日・14日目
            if rain >= 1.0:
                status = "× 不可"
                reason.append("降水量超過")
            if wind >= 5.0:
                status = "× 不可"
                reason.append("風速超過")
        elif i in [10,11,12]:  # 警戒日
            if rain >= 1.0:
                status = "× 不可"
                reason.append("降水量超過")
            if wind >= 5.0:
                status = "× 不可"
                reason.append("風速超過")
            if rain > 0:
                status = "× 不可"
                reason.append("警戒期間降雨")

        results.append({
            "date": row["time"],
            "曜日付き日付": row["time"].strftime("%m/%d(%a)"),
            "天気": row["weather_text"],
            "判定": status,
            "理由": ",".join(reason) if reason else "基準内"
        })
    return pd.DataFrame(results)

# =========================
# 安全なメール送信（Base64 AUTH LOGIN）
# =========================
def send_mail(subject, body, recipients):
    if not all([XSERVER_USER, XSERVER_PASS, XSERVER_SMTP]):
        print("メール設定未完了")
        return

    user = XSERVER_USER.strip()
    password = XSERVER_PASS.strip()
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(XSERVER_SMTP, 465, context=context) as server:
        # Base64 AUTH LOGIN
        server.docmd("AUTH LOGIN", base64.b64encode(user.encode("utf-8")).decode())
        server.docmd(base64.b64encode(password.encode("utf-8")).decode())

        for r in recipients:
            msg = EmailMessage()
            msg["From"] = user
            msg["To"] = r
            msg["Subject"] = subject
            msg.set_content(body, charset="utf-8")
            server.send_message(msg)

# =========================
# メイン
# =========================
def main():
    settings, sha = load_settings()
    df_raw = get_weather()
    df = judge_weather(df_raw)

    # GitHub Actions実行時（UIなし）
    if not st.runtime.exists():
        reserved = settings.get("reserved_date")
        emails = settings.get("emails", [DEFAULT_EMAIL])
        if reserved:
            reserved_dt = pd.to_datetime(reserved)
            match = df[df["date"] == reserved_dt]
            if not match.empty and "×" in match.iloc[0]["判定"]:
                send_mail("【警告】予約日プレー不可", df.to_string(), emails)
        return

    # Streamlit UI
    st.set_page_config(layout="wide")
    st.title("矢板カントリークラブ 予約監視")
    st.table(df[["曜日付き日付", "天気", "判定", "理由"]])

    reserved = settings.get("reserved_date")
    emails = settings.get("emails", [DEFAULT_EMAIL])
    if reserved:
        reserved_dt = pd.to_datetime(reserved)
        match = df[df["date"] == reserved_dt]
        if not match.empty:
            if "×" in match.iloc[0]["判定"]:
                st.error(f"{reserved} は不可")
            else:
                st.success(f"{reserved} は良好")

    st.divider()
    new_date = st.date_input("予約日設定")
    new_email = st.text_input("追加メール")

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
        send_mail("監視状況レポート", df.to_string(), emails)
        st.success("送信完了")

    st.divider()
    st.markdown("[情報源: tenki.jp 矢板カントリークラブ２週間予報](https://tenki.jp/leisure/golf/3/12/644217/week.html)")
    st.markdown("[公式予約サイトへ](https://reserve.golf-yaita.com)")

if __name__ == "__main__":
    main()
