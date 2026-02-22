import os
import requests
from github_persistence import get_file
import json

NTFY_TOPIC = os.getenv("NTFY_TOPIC")  # ntfy.sh で作ったトピック

def send_ntfy(message: str):
    if not NTFY_TOPIC:
        print("NTFY_TOPIC 未設定")
        return

    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    r = requests.post(url, data=message.encode("utf-8"))
    if r.status_code == 200 or r.status_code == 201:
        print("ntfy 送信成功")
    else:
        print(f"ntfy 送信失敗: {r.status_code}, {r.text}")

def notify_reservation(result: dict):
    content, _ = get_file()
    settings = json.loads(content)
    emails = settings.get("emails", [])

    date = result["date"]
    judge = result["judge"]
    reason = result["reason"]

    message = f"予約日: {date}\n判定: {judge}\n理由: {reason}"

    # ntfy送信
    send_ntfy(message)

    # メール送信（ntfyゲートウェイ利用）
    for email in emails:
        msg_email = f"{message}\n宛先: {email}"
        send_ntfy(msg_email)  # 本番ではSMTPでも可
