"""
Email Sender Toolkit — Send emails via SMTP using Agno framework.

Setup:
  Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env
  For Gmail: SMTP_HOST=smtp.gmail.com, SMTP_PORT=587, use App Password
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from agno.tools import Toolkit

logger = logging.getLogger(__name__)


class EmailSenderToolkit(Toolkit):
    """Toolkit for sending emails via SMTP."""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_address: str = None,
    ):
        super().__init__(name="email_sender")
        self._host = smtp_host or os.getenv("SMTP_HOST")
        self._port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self._user = smtp_user or os.getenv("SMTP_USER")
        self._password = smtp_password or os.getenv("SMTP_PASSWORD")
        self._from = from_address or os.getenv("SMTP_FROM", self._user)

        self.register(self.send_email)
        self.register(self.send_html_email)

    def send_email(self, to: str, subject: str, body: str) -> dict:
        """
        Send a plain text email to a recipient.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Plain text email body content

        Returns:
            A dictionary with status and recipient information
        """
        return self._send(to, subject, body, is_html=False)

    def send_html_email(self, to: str, subject: str, html_body: str) -> dict:
        """
        Send an HTML-formatted email to a recipient.

        Args:
            to: Recipient email address
            subject: Email subject line
            html_body: HTML-formatted email body content

        Returns:
            A dictionary with status and recipient information
        """
        return self._send(to, subject, html_body, is_html=True)

    def _send(self, to: str, subject: str, body: str, is_html: bool = False) -> dict:
        """Internal method to send the email."""
        if not all([self._host, self._user, self._password]):
            return {"error": "SMTP not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env"}

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._from
            msg["To"] = to

            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type))

            with smtplib.SMTP(self._host, self._port) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.send_message(msg)

            logger.info(f"Email sent to {to}: {subject}")
            return {"status": "sent", "to": to, "subject": subject, "format": content_type}

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"error": str(e)}


# Backward compatibility
DESCRIPTION = "Send an email via SMTP. Supports plain text and HTML content."
PARAMETERS = {
    "to": {"type": "string", "description": "Recipient email address"},
    "subject": {"type": "string", "description": "Email subject line"},
    "body": {"type": "string", "description": "Email body (plain text or HTML)"},
    "is_html": {"type": "boolean", "description": "If true, body is treated as HTML", "default": False},
}


def run(to: str, subject: str, body: str, is_html: bool = False) -> dict:
    """Send an email (legacy interface)."""
    toolkit = EmailSenderToolkit()
    return toolkit._send(to, subject, body, is_html)
