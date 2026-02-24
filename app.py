import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta
import base64

# =========================
# 基本設定
# =========================
st.set_page_config(page_title="Yaita Reservation Monitor", layout="wide")

GITHUB_REPO = "iios9402-hash/golf-app2"
SETTINGS_FILE = "settings.json"
GH_TOKEN = os.getenv("GH_TOKEN")

LAT, LON = 36.8091, 139.9073

# =========================
# GitHub 永続化
# =========================
def load_settings():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SETTINGS_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode()
        return json.loads(content), r.json()["sha"]
    else:
        return {"reserved_date": None, "emails": ["iios9402@yahoo.co.jp"]}, None

def save_settings(data, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SETTINGS_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    encoded = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
    payload = {
        "message": "Update settings.json",
        "content": encoded,
        "sha": sha
    }
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code == 200

settings, sha = load_settings()

# =========================
# 天気取得
# =========================
API_URL = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}"
    "&daily=weathercode,precipitation_sum,windspeed_10m_max"
    "&timezone=Asia/Tokyo"
)

resp = requests.get(API_URL).json()

df = pd.DataFrame({
    "date": resp["daily"]["time"],
    "weathercode": resp["daily"]["weathercode"],
    "precipitation": resp["daily"]["precipitation_sum"],
    "wind": resp["daily"]["windspeed_10m_max"]
})

df["date"] = pd.to_datetime(df["date"])

def weather_text(code):
    if code == 0:
        return "晴"
    if code in [1,2,3]:
        return "曇"
    if code >= 51:
        return "雨"
    return "不明"

def judge(row, idx):
    if idx < 10 or idx == 13:
        if row["precipitation"] >= 1.0 or row["wind"] >= 5.0:
            return "× 不可", "数値基準超過"
    else:
        if (row["precipitation"] >= 1.0 or
            row["wind"] >= 5.0 or
            "雨" in weather_text(row["weathercode"])):
            return "× 不可", "警戒条件"
    return "◯ 可", ""

df["曜日付き日付"] = df["date"].dt.strftime("%Y-%m-%d (%a)")
df["天気"] = df["weathercode"].apply(weather_text)

results = []
reasons = []
for i, row in df.iterrows():
    r, reason = judge(row, i)
    results.append(r)
    reasons.append(reason)

df["判定"] = results
df["理由"] = reasons

display_df = df[["曜日付き日付","天気","判定","理由"]]

# =========================
# UI表示
# =========================
st.title("矢板カントリークラブ 予約監視")

st.table(display_df)

st.divider()

# 予約日設定
st.subheader("予約確定日設定")

selected_date = st.date_input(
    "予約日",
    value=datetime.strptime(settings["reserved_date"], "%Y-%m-%d").date()
    if settings["reserved_date"] else datetime.today().date()
)

emails_input = st.text_area(
    "通知メール（カンマ区切り）",
    value=",".join(settings["emails"])
)

if st.button("設定を完全に保存する"):
    new_settings = {
        "reserved_date": selected_date.strftime("%Y-%m-%d"),
        "emails": [e.strip() for e in emails_input.split(",")]
    }
    if save_settings(new_settings, sha):
        st.success("保存完了（GitHub同期済）")
    else:
        st.error("保存失敗")

# 予約判定アラート
if settings["reserved_date"]:
    target = df[df["date"] == pd.to_datetime(settings["reserved_date"])]
    if not target.empty:
        if target.iloc[0]["判定"].startswith("×"):
            st.error("予約日：プレー不可")
        else:
            st.success("予約日：プレー可能")

st.divider()

st.link_button(
    "公式予約サイトへ",
    "https://reserve.accordiagolf.com/golfLinkCourseDetail/?gid=162"
)
