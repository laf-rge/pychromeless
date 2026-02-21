"""
Email service module for Wagoner Management Corp.'s financial operations.

This module handles all email communications including:
- Daily journal reports
- High pay-in alerts
- Missing deposit notifications
- Tips reports
"""

import html
from datetime import date
from decimal import Decimal
from typing import Any, cast

import boto3

from email_templates import render_alert_email
from ssm_parameter_store import SSMParameterStore
from store_config import StoreConfig


class EmailService:
    def __init__(self, store_config: StoreConfig):
        parameters = cast(
            "SSMParameterStore", SSMParameterStore(prefix="/prod")["email"]
        )
        self.from_email = parameters["from_email"]
        self.default_recipients = str(parameters["receiver_email"]).split(", ")
        self.charset = "UTF-8"
        self.client = boto3.client("ses")
        self.store_config = store_config

    def send_email(
        self, subject: str, message: str, recipients: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Send an HTML email using AWS SES.

        Args:
            subject: Email subject line
            message: Complete HTML document string (from template render functions)
            recipients: Optional list of recipient email addresses.
                      If None, uses default recipients from SSM.

        Returns:
            dict: AWS SES send_email response

        Raises:
            ClientError: If email sending fails
        """
        receiver_emails = (
            recipients if recipients is not None else self.default_recipients
        )

        result: dict[str, Any] = self.client.send_email(
            Destination={
                "ToAddresses": receiver_emails,
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": self.charset,
                        "Data": message,
                    },
                },
                "Subject": {
                    "Charset": self.charset,
                    "Data": subject,
                },
            },
            Source=self.from_email,
        )
        return result

    def send_missing_deposit_alert(self, store: str, txdate: date) -> None:
        """Send alert email for missing store deposits."""
        subject = f"{store} missing deposit for {txdate!s}"
        body_html = (
            f"Folks,<br/><br/>"
            f"I couldn't find a deposit for <strong>{html.escape(store)}</strong> "
            f"on <strong>{html.escape(str(txdate))}</strong>.<br/><br/>"
            f"Please correct this and re-run.<br/><br/>"
            f"Thanks,<br/>Josiah<br/>(aka The Robot)"
        )
        message = render_alert_email(subject, txdate, body_html)
        self.send_email(subject, message)

    def send_high_payin_alert(self, store: str, amount: Decimal, payins: str) -> None:
        """Send alert email for high pay-in amounts."""
        subject = f"High pay-in detected {store}"
        body_html = (
            f"<strong>{html.escape(store)}</strong> &mdash; "
            f"<strong>${html.escape(str(amount))}</strong><br/><br/>"
            f'<pre style="font-size:12px;margin:0;white-space:pre-wrap;">{html.escape(payins)}</pre>'
        )
        message = render_alert_email(subject, date.today(), body_html)
        self.send_email(subject, message)
