"""
Email Sender Tool — Send emails via SMTP.

Setup:
  Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env
  For Gmail: SMTP_HOST=smtp.gmail.com, SMTP_PORT=587, use App Password
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

DESCRIPTION = "Send an email via SMTP. Supports plain text and HTML content."

PARAMETERS = {
    "to": {"type": "string", "description": "Recipient email address"},
    "subject": {"type": "string", "description": "Email subject line"},
    "body": {"type": "string", "description": "Email body (plain text or HTML)"},
    "is_html": {"type": "boolean", "description": "If true, body is treated as HTML", "default": False},
}


def run(to: str, subject: str, body: str, is_html: bool = False) -> dict:
    """Send an email."""
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("SMTP_FROM", user)

    if not all([host, user, password]):
        return {"error": "SMTP not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to

        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type))

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        logger.info(f"Email sent to {to}: {subject}")
        return {"status": "sent", "to": to, "subject": subject}

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return {"error": str(e)}
