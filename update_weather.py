# update_weather.py
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# tenki.jp 矢板カントリークラブ 2週間予報
URL = "https://tenki.jp/leisure/golf/3/12/644217/week.html"
OUTPUT_JSON = "weather.json"

def get_weather():
    # User-Agent を付けてアクセス
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0 Safari/537.36"
        )
    }
    res = requests.get(URL, headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    # 最新 HTML 構造に合わせて table を取得
    table = soup.find("table", class_="forecast-week-table")
    if not table:
        # デバッグ用にHTML保存
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(res.text)
        raise ValueError("天気表が見つかりません。debug.html を確認してください。")

    rows = table.find_all("tr")
    if len(rows) < 15:
        raise ValueError("天気表の行数が不足しています。")

    weather_list = []
    today = datetime.today()

    # 翌日から14日分
    for i in range(1, 15):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")
        weekday = date_obj.strftime("%a")

        try:
            tds = rows[i].find_all("td")
            weather = tds[1].get_text(strip=True)
            precipitation = tds[2].get_text(strip=True)
            wind = tds[3].get_text(strip=True)
        except Exception:
            weather = "不明"
            precipitation = "0.0"
            wind = "0.0"

        weather_list.append({
            "date": date_str,
            "曜日": weekday,
            "weather": weather,
            "precipitation": precipitation,
            "wind": wind
        })

    return weather_list

if __name__ == "__main__":
    data = get_weather()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("weather.json を更新しました。")
