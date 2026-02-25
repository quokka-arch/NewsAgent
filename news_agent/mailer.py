"""Gmail SMTP sender for daily news reports."""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

RECIPIENT = "josey4869@gmail.com"


def send_report(html_path: str, recipient: str = RECIPIENT) -> None:
    """Send the HTML report as a rich email via Gmail SMTP.

    Requires env vars:
        GMAIL_USER         – your Gmail address (e.g. you@gmail.com)
        GMAIL_APP_PASSWORD – 16-char App Password from Google account
    """
    gmail_user = os.environ.get("GMAIL_USER", "").strip()
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    if not gmail_user or not gmail_password:
        raise ValueError(
            "请在 .env 文件中设置 GMAIL_USER 和 GMAIL_APP_PASSWORD"
        )

    html_path = Path(html_path)
    if not html_path.exists():
        raise FileNotFoundError(f"报告文件不存在: {html_path}")

    html_content = html_path.read_text(encoding="utf-8")
    date_str = datetime.now().strftime("%Y年%m月%d日")
    subject = f"🌍 国际政治每日简报 · {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"NewsAgent <{gmail_user}>"
    msg["To"] = recipient

    # Plain-text fallback
    plain = f"国际政治每日简报 {date_str}\n请用支持 HTML 的邮件客户端查看。"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    # HTML body
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    print(f"  📧 正在发送邮件至 {recipient} …")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipient, msg.as_string())

    print(f"  ✅ 邮件发送成功！")
