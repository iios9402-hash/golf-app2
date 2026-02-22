import requests
import pandas as pd

# --- 矢板カントリークラブの天気予報URL ---
URL = "https://tenki.jp/forecast/3/16/1610/9120/14days.json"  # 仮のJSONエンドポイント

def fetch_weather():
    """
    tenki.jp から14日間の天気データを取得して DataFrame に変換
    """
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()
    
    # 日付、降水量、風速、天気テキストを抜き出す
    days = []
    for i, day in enumerate(data['forecasts'][:14]):
        days.append({
            "date": day["date"],
            "precip_mm": float(day.get("precipitation", 0)),
            "wind_ms": float(day.get("wind_speed", 0)),
            "weather_text": day.get("telop", "")
        })
    df = pd.DataFrame(days)
    return df

def judge_playability(row, day_index):
    """
    判定アルゴリズム（百十番様規定）
    """
    rain = row["precip_mm"]
    wind = row["wind_ms"]
    telop = row["weather_text"]

    # 通常期間（1-10日, 14日目）
    if day_index <= 9 or day_index == 13:
        if rain >= 1.0:
            return "× 不可", "降水量1.0mm以上"
        if wind >= 5.0:
            return "× 不可", "風速5.0m/s以上"
        return "◯ 可", ""

    # 警戒期間（11-13日目 → index10-12）
    if 10 <= day_index <= 12:
        if rain >= 1.0:
            return "× 不可", "降水量1.0mm以上"
        if wind >= 5.0:
            return "× 不可", "風速5.0m/s以上"
        if "雨" in telop:
            return "× 不可", "予報文に雨を検出"
        return "◯ 可", ""

def main():
    df = fetch_weather()
    results = []
    for idx, row in df.iterrows():
        judge, reason = judge_playability(row, idx)
        results.append({
            "date": row["date"],
            "weather": row["weather_text"],
            "judge": judge,
            "reason": reason
        })
    result_df = pd.DataFrame(results)
    print(result_df)

if __name__ == "__main__":
    main()
