import os
import smtplib
from email.message import EmailMessage
from weather_engine import fetch_weather

# 判定アルゴリズム
def judge(df):
    results = []
    for i, row in df.iterrows():
        reason = []
        # 通常期間: 1-10日, 14日目
        if i < 10 or i == 13:
            if row["precip"] >= 1.0:
                reason.append("降水量超過")
            if row["wind"] >= 5.0:
                reason.append("風速超過")
        # 警戒期間: 11-13日目
        elif 10 <= i <= 12:
            if row["precip"] >= 1.0:
                reason.append("降水量超過")
            if row["wind"] >= 5.0:
                reason.append("風速超過")
            if "雨" in row["weather"]:
                reason.append("天気: 雨")

        judge_mark = "× 不可" if reason else "◯ 可"
        results.append((row["date"], row["weekday"], row["weather"], judge_mark, ", ".join(reason)))
    return results

# メール送信
def send_mail(subject, body, to_email):
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASS = os.environ.get("SMTP_PASS")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"メール送信成功: {to_email}")
    except Exception as e:
        print(f"メール送信失敗: {e}")

def main():
    df = fetch_weather()
    results = judge(df)

    # コンソール出力確認用
    print("=== 予約日判定 ===")
    for r in results:
        print(f"日付: {r[0]} ({r[1]})")
        print(f"天気: {r[2]}")
        print(f"判定: {r[3]}")
        print(f"理由: {r[4]}\n")

    # × 不可 の日があればメール通知
    for r in results:
        if r[3] == "× 不可":
            send_mail(
                subject=f"矢板CC 予約不可通知 {r[0]}",
                body=f"日付: {r[0]} ({r[1]})\n天気: {r[2]}\n判定: {r[3]}\n理由: {r[4]}",
                to_email="iios9402@yahoo.co.jp"
            )

if __name__ == "__main__":
    main()
