import os
import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict

import requests


def _send_webhook(payload: Dict[str, Any]) -> None:
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    if not webhook_url:
        return
    requests.post(webhook_url, json=payload, timeout=10)


def _send_email(payload: Dict[str, Any]) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    to_address = os.getenv("ALERT_EMAIL_TO")
    from_address = os.getenv("ALERT_EMAIL_FROM", smtp_user)
    if not smtp_host or not smtp_user or not smtp_password or not to_address:
        return

    body = f"AQI Alert for {payload['city']}\nAQI: {payload['aqi']}\nThreshold: {payload['threshold']}\nMessage: {payload['message']}"
    message = MIMEText(body)
    message["Subject"] = f"AQI Alert: {payload['city']}"
    message["From"] = from_address
    message["To"] = to_address

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.sendmail(from_address, [to_address], message.as_string())


def send_alert_notification(city: str, aqi: float, threshold: int) -> None:
    payload = {
        "city": city,
        "aqi": aqi,
        "threshold": threshold,
        "message": "AQI has crossed the configured alert threshold.",
    }
    _send_webhook(payload)
    _send_email(payload)
