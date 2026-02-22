def fetch_weather():
    # 仮データ
    days = []
    for i in range(14):
        days.append({
            "date": f"2026-02-{22+i:02d}",
            "precip_mm": 0 if i % 3 != 0 else 2.0,
            "wind_ms": 3 if i % 5 != 0 else 6,
            "weather_text": "晴" if i % 2 == 0 else "雨"
        })
    df = pd.DataFrame(days)
    return df
