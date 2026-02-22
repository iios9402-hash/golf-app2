import json
from weather_engine import run_engine
from github_persistence import get_file
from notifier import notify_reservation  # 通知モジュール

def check_reservation():

    # settings.json取得
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

            # ◯ 可でもテスト送信するように完全統合
            notify_reservation(row)

            if "×" in row["judge"]:
                print("⚠ 警告：プレー不可")
            else:
                print("◎ プレー可能")

            return

    print("予約日が14日範囲外です")


if __name__ == "__main__":
    check_reservation()
