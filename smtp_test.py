import smtplib, ssl

# 送信元 Xserver メール情報
XSERVER_USER = "iios9402@globalaudio.info"
XSERVER_PASS = "GolfTest2026"
XSERVER_SMTP = "sv10527.xserver.jp"

# テスト送信先
TEST_EMAIL = "iios9402@yahoo.co.jp"

subject = "Xserver送信テスト"
body = "これは Xserver から送信できるか確認するテストメールです。"

context = ssl.create_default_context()

try:
    with smtplib.SMTP_SSL(XSERVER_SMTP, 465, context=context) as server:
        server.login(XSERVER_USER, XSERVER_PASS)
        msg = f"Subject: {subject}\n\n{body}"
        server.sendmail(XSERVER_USER, TEST_EMAIL, msg)
        print("送信成功！")
except Exception as e:
    print("送信失敗:", e)
