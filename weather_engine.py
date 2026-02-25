import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

TENKI_URL = "https://tenki.jp/leisure/golf/3/12/644217/week.html"

def fetch_weather():
    """
    tenki.jp 矢板カントリークラブ 2週間予報を取得
    本日を除く向こう2週間を DataFrame に展開
    """
    resp = requests.get(TENKI_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 日付・曜日
    dates = [d.text.strip() for d in soup.select(".forecast-point-week-day .date")]
    weekdays = [d.text.strip() for d in soup.select(".forecast-point-week-day .week")]
    # 天気テキスト
    weathers = [w["title"].strip() for w in soup.select(".forecast-point-week-weather img")]
    # 降水量(mm) と 風速(m/s)
    precs = [float(p.text.strip().replace("mm", "")) if p.text.strip() else 0.0 
             for p in soup.select(".rainfall span.value")]
    winds = [float(w.text.strip().replace("m/s","")) if w.text.strip() else 0.0 
             for w in soup.select(".wind span.value")]

    # DataFrame に変換
    df = pd.DataFrame({
        "date": dates,
        "weekday": weekdays,
        "weather": weathers,
        "precip": precs,
        "wind": winds
    })

    # 本日を除外
    today_str = datetime.now().strftime("%Y/%m/%d")
    df = df[df["date"] != today_str]

    # 最大14日分
    df = df.head(14)

    return df
