import os
import smtplib
import socket
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional

import requests

from services.sftp_service import load_env_file

load_env_file()


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _run_context() -> str:
    host = socket.gethostname()
    run_id = os.getenv("GITHUB_RUN_ID")
    repo = os.getenv("GITHUB_REPOSITORY")
    if run_id and repo:
        return (
            f"GitHub Actions run: {repo} #{run_id}\n"
            f"https://github.com/{repo}/actions/runs/{run_id}"
        )
    return f"Host: {host}"

def send_teams_alert(title: str, message: str) -> bool:
    webhook_url = _get("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print("Teams notification skipped: TEAMS_WEBHOOK_URL is not set.")
        return False

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "D93F3F",
        "title": f"⚠️ {title}",
        "text": f"{message}\n\n{_run_context()}",
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
        print("Teams notification sent.")
        return True
    except requests.RequestException as e:
        print(f"Failed to send Teams notification: {e}")
        return False
    webhook_url = _get("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print("Teams notification skipped: TEAMS_WEBHOOK_URL is not set.")
        return False

    payload = {
        "title": title,
        "message": message,
        "context": _run_context(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
        print("Teams notification sent.")
        return True
    except requests.RequestException as e:
        print(f"Failed to send Teams notification: {e}")
        return False


def send_email_alert(subject: str, message: str) -> bool:
    host = _get("EMAIL_HOST")
    port_raw = _get("EMAIL_PORT", "587")
    username = _get("EMAIL_USERNAME")
    password = _get("EMAIL_PASSWORD")
    sender = _get("EMAIL_FROM") or username
    recipients_raw = _get("EMAIL_TO")

    missing = [
        name for name, val in [
            ("EMAIL_HOST", host),
            ("EMAIL_USERNAME", username),
            ("EMAIL_PASSWORD", password),
            ("EMAIL_TO", recipients_raw),
        ] if not val
    ]
    if missing:
        print(f"Email notification skipped: missing {', '.join(missing)}.")
        return False

    try:
        port = int(port_raw)
    except ValueError:
        port = 587

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    email_msg = EmailMessage()
    email_msg["Subject"] = subject
    email_msg["From"] = sender
    email_msg["To"] = ", ".join(recipients)
    email_msg.set_content(f"{message}\n\n{_run_context()}")

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(email_msg)
        print("Email notification sent.")
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"Failed to send email notification: {e}")
        return False


def notify_failure(stage: str, error: Exception, extra: Optional[str] = None) -> None:
    title = "Aawsat E-Paper Automation FAILED"
    message = f"Stage: {stage}\nError: {error}"
    if extra:
        message += f"\n{extra}"

    print(f"\n=== Sending failure notifications ({stage}) ===")

    try:
        send_teams_alert(title, message)
    except Exception as e:
        print(f"Unexpected error sending Teams notification: {e}")

    try:
        send_email_alert(title, message)
    except Exception as e:
        print(f"Unexpected error sending email notification: {e}")