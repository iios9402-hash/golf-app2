import os
print("TEST")  # workflow がこのファイルを正しく実行しているか確認用

import json
from weather_engine import run_engine
from github_persistence import get_file
from notifier import notify_reservation  # 通知モジュール

def check_reservation():
    print("DEBUG: NTFY_TOPIC =", os.getenv("NTFY_TOPIC"))
    content, _ = get_file()
    settings = json.loads(content)
    reserved_date = settings.get("reserved_date")
    if not reserved_date:
        print("予約日未設定")
        return
    results = run_engine()
    for row in results:
        if row["date"] == reserved_date:
            print("=== 予約日判定 ===")
            print(f"日付: {row['date']} ({row['weekday']})")
            print(f"天気: {row['weather']}")
            print(f"判定: {row['judge']}")
            print(f"理由: {row['reason']}")
            notify_reservation(row)
            if "×" in row["judge"]:
                print("⚠ 警告：プレー不可")
            else:
                print("◎ プレー可能")
            return
    print("予約日が14日範囲外です")

if __name__ == "__main__":
    check_reservation()
