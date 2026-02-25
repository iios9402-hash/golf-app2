import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

URL = "https://tenki.jp/leisure/golf/3/12/644217/week.html"
OUTPUT_JSON = "weather.json"

def get_weather():
    res = requests.get(URL)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table", class_="forecast-week-table")
    if not table:
        raise ValueError("天気表が見つかりません")

    rows = table.find_all("tr")
    weather_list = []
    today = datetime.today()

    for i in range(1, 15):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")
        weekday = date_obj.strftime("%a")

        weather = rows[i].find_all("td")[1].get_text(strip=True) if len(rows) > i else "不明"
        precipitation = rows[i].find_all("td")[2].get_text(strip=True) if len(rows) > i else "0.0"
        wind = rows[i].find_all("td")[3].get_text(strip=True) if len(rows) > i else "0.0"

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
