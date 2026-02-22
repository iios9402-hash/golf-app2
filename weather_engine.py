import pandas as pd
from datetime import datetime, timedelta


# ===============================
# 1. 仮の14日データ生成（後でAPIに差替）
# ===============================
def fetch_weather_data():
    today = datetime.today()
    rows = []

    for i in range(14):
        date = today + timedelta(days=i)

        rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "weekday": date.strftime("%a"),
            "precip_mm": 0 if i % 4 != 0 else 2.0,
            "wind_ms": 3 if i % 6 != 0 else 6.0,
            "weather_text": "晴" if i % 3 != 0 else "雨"
        })

    return pd.DataFrame(rows)


# ===============================
# 2. 百十番様判定ロジック
# ===============================
def judge_playability(row, index):

    rain = row["precip_mm"]
    wind = row["wind_ms"]
    telop = row["weather_text"]

    # 通常期間（1-10日目 + 14日目）
    if index <= 9 or index == 13:
        if rain >= 1.0:
            return "× 不可", "降水量1.0mm以上"
        if wind >= 5.0:
            return "× 不可", "風速5.0m/s以上"
        return "◯ 可", ""

    # 警戒期間（11-13日目）
    if 10 <= index <= 12:
        if rain >= 1.0:
            return "× 不可", "降水量1.0mm以上"
        if wind >= 5.0:
            return "× 不可", "風速5.0m/s以上"
        if "雨" in telop:
            return "× 不可", "予報文に雨を検出"
        return "◯ 可", ""


# ===============================
# 3. 実行関数
# ===============================
def run_engine():

    df = fetch_weather_data()
    results = []

    for idx, row in df.iterrows():
        judge, reason = judge_playability(row, idx)

        results.append({
            "date": row["date"],
            "weekday": row["weekday"],
            "weather": row["weather_text"],
            "judge": judge,
            "reason": reason
        })

    return results


if __name__ == "__main__":
    output = run_engine()
    for row in output:
        print(row)
