"""
Email service module for Wagoner Management Corp.'s financial operations.

This module handles all email communications including:
- Daily journal reports
- High pay-in alerts
- Missing deposit notifications
- Tips reports
"""

from datetime import date
from decimal import Decimal
from typing import Any, cast

import boto3

from ssm_parameter_store import SSMParameterStore
from store_config import StoreConfig
from tips import Tips


class EmailService:
    def __init__(self, store_config: StoreConfig):
        parameters = cast(SSMParameterStore, SSMParameterStore(prefix="/prod")["email"])
        self.from_email = parameters["from_email"]
        self.default_recipients = str(parameters["receiver_email"]).split(", ")
        self.charset = "UTF-8"
        self.client = boto3.client("ses")
        self.store_config = store_config
        self.style_tag = """
    <style>
      table,
      th,
      td {
        padding: 10px;
        border: 1px solid black;
        border-collapse: collapse;
      }
    </style>
"""

    def send_email(
        self, subject: str, message: str, recipients: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Send an HTML email using AWS SES.

        Args:
            subject: Email subject line
            message: HTML message content
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
                        "Data": f"<html><head><title>{subject}</title>{self.style_tag}</head><body>{message}</body></html>",
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
        subject = f"{store} missing deposit for {str(txdate)}"
        message = f"""
Folks,<br/>
I couldn't find a deposit for the following dates for these stores:<br/>
<pre>{store} is missing a deposit for {str(txdate)}\n</pre>
Please correct this and re-run.<br/><br/>
Thanks,<br/>
Josiah<br/>
(aka The Robot)"""
        self.send_email(subject, message)

    def send_high_payin_alert(self, store: str, amount: Decimal, payins: str) -> None:
        """Send alert email for high pay-in amounts."""
        self.send_email(
            f"High pay-in detected {store}", f"<pre>{store} - ${amount}\n{payins}</pre>"
        )

    def create_attendance_table(self, start_date: date, end_date: date) -> str:
        """Create HTML table of attendance data."""
        t = Tips()
        data = t.attendanceReport(self.store_config.all_stores, start_date, end_date)
        table = "<table>\n<tr>"
        table += "".join(f"<th>{str(item)}</th>" for item in data[0])
        table += "</tr>\n"

        for row in sorted(data[1:]):
            table += "<tr>"
            table += "".join(f"<td>{str(item)}</td>" for item in row)
            table += "</tr>\n"

        table += "</table>\n"
        return table
