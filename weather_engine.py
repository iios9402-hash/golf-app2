import pandas as pd

def fetch_weather():
    # 仮データで14日間を生成
    days = []
    for i in range(14):
        days.append({
            "date": f"2026-02-{22+i:02d}",
            "precip_mm": 0 if i % 3 != 0 else 2.0,  # 3の倍数は降水量2mmで不可判定用
            "wind_ms": 3 if i % 5 != 0 else 6,      # 5の倍数は風速6m/sで不可判定用
            "weather_text": "晴" if i % 2 == 0 else "雨"
        })
    return pd.DataFrame(days)

def judge_playability(row, day_index):
    rain = row["precip_mm"]
    wind = row["wind_ms"]
    telop = row["weather_text"]

    if day_index <= 9 or day_index == 13:
        if rain >= 1.0:
            return "× 不可", "降水量1.0mm以上"
        if wind >= 5.0:
            return "× 不可", "風速5.0m/s以上"
        return "◯ 可", ""

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
    print(pd.DataFrame(results))

if __name__ == "__main__":
    main()
