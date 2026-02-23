import os
import requests

print("TEST")
print("DEBUG: NTFY_TOPIC =", os.getenv("NTFY_TOPIC"))

topic = os.getenv("NTFY_TOPIC")

print("=== 強制送信テスト ===")

if topic:
    response = requests.post(
        f"https://ntfy.sh/{topic}",
        data="テスト通知：送信確認"
    )

    if response.status_code == 200:
        print("ntfy 送信成功")
    else:
        print("ntfy 送信失敗", response.status_code)
else:
    print("NTFY_TOPIC が取得できていません")
