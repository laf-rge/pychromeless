"""
AWS Lambda handlers for Wagoner Management Corp.'s financial operations.

This module contains Lambda handlers for various financial operations including:
- Daily sales processing
- Invoice synchronization
- Third-party deposit handling
- Tips management
- Daily journal reporting

The handlers can be invoked both via AWS Lambda and locally for development.
"""

import json
import base64
import calendar
import email
import io
import re
import logging
import sys
import os
from datetime import date, datetime, timedelta
from pythonjsonlogger import jsonlogger
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from decimal import Decimal
from email.message import Message
from functools import partial  # noqa # pylint: disable=unused-import
from locale import LC_NUMERIC, atof, setlocale
from operator import itemgetter
from typing import Any

import crunchtime
import pandas as pd
import qb
from botocore.exceptions import ClientError
from doordash import Doordash
from ezcater import EZCater
from flexepos import Flexepos
from grubhub import Grubhub
from tips import Tips
from ubereats import UberEats
from wmcgdrive import WMCGdrive
from store_config import StoreConfig
from email_service import EmailService


store_config = StoreConfig()
email_service = EmailService(store_config)


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


class ColorizedJsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, json_default=CustomJsonEncoder().default)

    def format(self, record):
        json_str = super().format(record)
        return highlight(json_str, JsonLexer(), TerminalFormatter())


def setup_json_logger():
    json_handler = logging.StreamHandler(sys.stdout)
    json_formatter = ColorizedJsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    json_handler.setFormatter(json_formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(json_handler)
    root_logger.setLevel(logging.INFO)


if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    setup_json_logger()
logger = logging.getLogger(__name__)

# warning! this won't work if we multiply
TWO_PLACES = Decimal(10) ** -2
setlocale(LC_NUMERIC, "en_US.UTF-8")
pattern = re.compile(r"\d+\.\d\d")


def create_response(
    status_code: int,
    body: object,
    content_type: str = "application/json",
    filename: str | None = None,
) -> dict:
    headers = {
        "Content-type": content_type,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Expose-Headers": "Content-Disposition,Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    }
    if filename is not None:
        headers["Content-Disposition"] = f"attachment; filename={filename}"
    return {
        "statusCode": status_code,
        "body": json.dumps(body) if content_type == "application/json" else body,
        "headers": headers,
    }


def third_party_deposit_handler(*args, **kwargs) -> dict:
    """
    Process third-party deposits from various services.

    Lambda invocation:
        - Schedule: Daily
        - No event parameters required

    Local development:
        >>> from lambda_function import third_party_deposit_handler
        >>> third_party_deposit_handler()
    """
    start_date = date.today() - timedelta(days=28)
    end_date = date.today()

    services = [
        (Flexepos(), "getGiftCardACH", store_config.all_stores, start_date, end_date),
        (Doordash(), "get_payments", store_config.all_stores, start_date, end_date),
        (
            UberEats(store_config),
            "get_payments",
            store_config.all_stores,
            start_date,
            end_date,
        ),
        (Grubhub(), "get_payments", start_date, end_date),
        (EZCater(), "get_payments", store_config.all_stores, start_date, end_date),
    ]

    for service, method, *service_args in services:
        try:
            results = getattr(service, method)(*service_args)
            for result in results:
                try:
                    qb.sync_third_party_deposit(*result)
                except Exception:
                    logger.exception(
                        f"Exception in sync_third_party_deposit for {service.__class__.__name__}"
                    )
                    logger.info(result)
        except Exception:
            logger.exception(f"Exception in {service.__class__.__name__}")

    return create_response(200, {"message": "Success"})


def invoice_sync_handler(*args, **kwargs) -> dict:
    """
    Process invoice and inventory data from Crunchtime into Quickbooks.

    Lambda invocation:
        - Schedule: Daily at 3 AM PST
        - Event format (for API Gateway):
            {
                "year": "YYYY",     # Optional: defaults to current year
                "month": "MM"       # Optional: defaults to current month
            }

    Local development:
        >>> from lambda_function import invoice_sync_handler
        >>> invoice_sync_handler()  # Process current month
        >>> invoice_sync_handler({"year": "2024", "month": "03"})  # Process specific month
    """
    try:
        event = {}
        if args is not None and len(args) > 0:
            event = args[0]

        today = date.today()
        target_year = int(event.get("year", today.year))
        target_month = int(event.get("month", today.month))
        target_date = date(target_year, target_month, 1)

        ct = crunchtime.Crunchtime()
        # Always process GL report
        ct.process_gl_report(store_config.all_stores)

        # Determine if we should process inventory report
        should_process_inventory = False

        first_monday = None
        if target_date.year == today.year and target_date.month == today.month:
            # Find first Monday of the month
            first_monday = target_date
            while first_monday.weekday() != 0:  # 0 is Monday
                first_monday += timedelta(days=1)

            # We need the day after the first Monday (Tuesday) to ensure Monday's data is available
            first_tuesday = first_monday + timedelta(days=1)

            # Find the last day of the month
            if target_month == 12:
                next_month = date(target_year + 1, 1, 1)
            else:
                next_month = date(target_year, target_month + 1, 1)
            last_day = next_month - timedelta(days=1)

            # If we're processing the current month and we're in the first few days of the next month,
            # we need to wait until Tuesday to ensure all end-of-month data is available
            if today.month != target_month:
                # We're in the next month, make sure it's at least Tuesday
                should_process_inventory = today.weekday() >= 1  # Tuesday = 1
            else:
                # We're in the target month, make sure we're past the first Tuesday
                should_process_inventory = today >= first_tuesday
        else:
            # For past months, always process as long as we're at least on the 2nd of next month
            next_month = (
                date(target_year, target_month + 1, 1)
                if target_month < 12
                else date(target_year + 1, 1, 1)
            )
            second_of_next_month = next_month + timedelta(days=1)
            should_process_inventory = (
                today >= second_of_next_month
            )  # Must be at least the 2nd

        if should_process_inventory:
            ct.process_inventory_report(
                store_config.all_stores, target_year, target_month
            )
            logger.info(
                "Processed inventory report",
                extra={
                    "year": target_year,
                    "month": target_month,
                    "stores": store_config.all_stores,
                },
            )
        else:
            wait_reason = (
                "waiting for first Tuesday"
                if today.month == target_month
                else "waiting for complete end-of-month data (2nd of next month)"
            )
            logger.info(
                f"Skipping inventory report - {wait_reason}",
                extra={
                    "year": target_year,
                    "month": target_month,
                    "first_monday": first_monday.isoformat() if first_monday else None,
                    "first_tuesday": first_tuesday.isoformat()
                    if "first_tuesday" in locals()
                    else None,
                    "today": today.isoformat(),
                    "target_date": target_date.isoformat(),
                },
            )

        return create_response(200, {"message": "Success"})
    except Exception:
        logger.exception("Error processing invoice sync")
        return create_response(500, {"message": "Error processing invoice sync"})


def daily_sales_handler(*args, **kwargs) -> dict:
    """
    Process daily sales data and create related financial entries.

    Lambda invocation:
        - Schedule: Daily at HH:MM UTC
        - Event format:
            {
                "year": "YYYY",    # Optional: defaults to yesterday
                "month": "MM",     # Optional: defaults to yesterday
                "day": "DD"        # Optional: defaults to yesterday
            }

    Local development:
        >>> from lambda_function import daily_sales_handler
        >>> daily_sales_handler()  # Process yesterday's sales
        >>> daily_sales_handler({"year": "2024", "month": "01", "day": "15"})
    """
    event = {}
    if args is not None and len(args) > 0:
        event = args[0]
    if "year" in event:
        txdates = [
            date(
                year=int(event["year"]),
                month=int(event["month"]),
                day=int(event["day"]),
            )
        ]
    else:
        txdates = [date.today() - timedelta(days=1)]
    # txdates = [date(2024, 10, 29), date(2024, 10, 31)]
    # txdates = list(map(partial(date, 2025, 1), range(13, 22)))
    logger.info(
        "Started daily sales",
        extra={"txdates": [txdate.isoformat() for txdate in txdates]},
    )
    dj = Flexepos()
    success = False
    for txdate in txdates:
        stores = store_config.get_active_stores(txdate)
        journal = {}
        for store in stores:
            retry = 3
            while retry:
                try:
                    journal.update(dj.getDailySales(store, txdate))
                    retry = 0
                except (ConnectionError, TimeoutError, Exception) as e:
                    logger.exception(f"error {txdate.isoformat()}: {str(e)}")
                    retry -= 1
            if store not in journal or "Payins" not in journal[store]:
                logger.info(
                    "Skipping store: no sales",
                    extra={"store": store, "txdate": txdate.isoformat()},
                )
                journal.pop(store)
        qb.create_daily_sales(txdate, journal)
        logger.info(
            "Successfully processed daily sales",
            extra={"txdate": txdate.isoformat(), "stores": stores},
        )
        for store in stores:
            # store not open guard
            if (
                store_config.is_store_active(store, txdate)
                and store in journal
                and "Payins" in journal[store]
            ):
                if (
                    journal[store]["Bank Deposits"] is None
                    or journal[store]["Bank Deposits"] == ""
                ):
                    email_service.send_missing_deposit_alert(store, txdate)
                payins = journal[store]["Payins"].strip()
                if payins.count("\n") > 0:
                    amount = Decimal(0)
                    for payin_line in payins.split("\n")[1:]:
                        if payin_line.startswith("TOTAL"):
                            continue
                        match = pattern.search(payin_line)
                        if match:
                            amount = amount + Decimal(atof(match.group()))
                    if amount.quantize(TWO_PLACES) > Decimal(150):
                        email_service.send_high_payin_alert(store, amount, payins)
                else:
                    logger.info(
                        "No payin or missing deposits issues detected",
                        extra={"store": store, "txdate": txdate.isoformat()},
                    )
            else:
                logger.info(
                    "Skipping store deposit emails: no sales data",
                    extra={"store": store, "txdate": txdate.isoformat()},
                )
        success = True
    if not success:
        return create_response(500, {"message": "Error processing daily sales"})
    txdate = txdates[0]
    try:
        payment_data = dj.getOnlinePayments(
            store_config.all_stores, txdate.year, txdate.month
        )
        qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data)
        royalty_data = dj.getRoyaltyReport(
            "wmc",
            date(txdate.year, txdate.month, 1),
            date(
                txdate.year,
                txdate.month,
                calendar.monthrange(txdate.year, txdate.month)[1],
            ),
        )
        qb.update_royalty(txdate.year, txdate.month, royalty_data)
    except Exception as e:
        logger.exception(
            "Error processing online payments or royalty report",
            extra={"error": str(e), "txdate": txdate.isoformat()},
        )
        return create_response(500, {"message": "Error processing daily sales"})
    return create_response(200, {"message": "Success"})


def online_cc_fee(*args, **kwargs) -> dict:
    txdate = date.today() - timedelta(days=1)

    dj = Flexepos()
    payment_data = dj.getOnlinePayments(
        store_config.all_stores, txdate.year, txdate.month
    )
    qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data)
    return create_response(200, {"message": "Success"})


def daily_journal_handler(*args, **kwargs) -> dict:
    """
    Generate and email daily journal reports.

    Lambda invocation:
        - Schedule: Daily
        - No event parameters required

    Local development:
        >>> from lambda_function import daily_journal_handler
        >>> daily_journal_handler()
    """
    yesterday = date.today() - timedelta(days=1)

    subject = "Daily Journal Report {}".format(yesterday.strftime("%m/%d/%Y"))

    dj = Flexepos()
    drawer_opens = dict()
    drawer_opens = dj.getDailyJournal(
        store_config.all_stores, yesterday.strftime("%m%d%Y")
    )

    gdrive = WMCGdrive()
    for store in store_config.all_stores:
        gdrive.upload(
            "{0}-{1}_daily_journal.txt".format(str(yesterday), store),
            drawer_opens[store].encode("utf-8"),
            "text/plain",
        )

    message = "<h1>Wagoner Management Corp.</h1>\n\n<h2>Cash Drawer Opens:</h2>\n<pre>"

    for store, journal in drawer_opens.items():
        message = "{}{}: {}\n".format(message, store, journal.count("Cash Drawer Open"))

    message += "</pre>\n\n<h2>Missing Punches:</h2>\n<pre>"

    t = Tips()
    for time in t.getMissingPunches():
        user = t._users[time["user_id"]]
        message = "{}{}, {} : {} - {}\n".format(
            message,
            user["last_name"],
            user["first_name"],
            t._locations[time["location_id"]]["name"],
            time["start_time"],
        )
    message += "</pre>\n\n<h2>Meal Period Violations:</h2>\n<pre>"
    for item in sorted(
        t.getMealPeriodViolations(store_config.all_stores, yesterday),
        key=itemgetter("store", "start_time"),
    ):
        message += f"MPV {item['store']} {item['last_name']}, {item['first_name']}, {item['start_time']}\n"

    message += "</pre><h2>Attendance Report:</h2><div>"
    message += email_service.create_attendance_table(yesterday, date.today())

    message += "</div>\n\n<div><pre>Thanks!\nJosiah (aka The Robot)</pre></div>"

    response = None
    try:
        response = email_service.send_email(subject, message)
    except ClientError as e:
        error_message = e.response.get("Error", {}).get(
            "Message", "Unknown error occurred"
        )
        logger.exception(error_message)
        return create_response(400, {"message": f"Email Failed: {error_message}"})

    return create_response(200, response)


def email_tips_handler(*args, **kwargs) -> dict:
    year = date.today().year
    month = date.today().month
    pay_period = 0

    event = {}
    if args is not None and len(args) > 0:
        event = args[0]
    if "year" in event:
        year = int(event["year"])
        month = int(event["month"])
        pay_period = int(event["day"])
    logger.info(f"year: {year}, month: {month}, pay_period: {pay_period}")
    t = Tips()
    t.emailTips(store_config.all_stores, date(year, month, 5), pay_period)
    return create_response(200, {"message": "Email Sent!"})


# https://github.com/srcecde/aws-tutorial-code/blob/master/lambda/lambda_api_multipart.py
def decode_upload(event: dict[str, Any]) -> dict[str, bytes]:
    # decoding form-data into bytes
    post_data = base64.b64decode(event["body"])
    # fetching content-type
    try:
        content_type = event["headers"]["Content-Type"]
    except KeyError:
        content_type = event["headers"]["content-type"]
    # concat Content-Type: with content_type from event
    ct = "Content-Type: " + content_type + "\n"

    # parsing message from bytes
    msg: Message = email.message_from_bytes(ct.encode() + post_data)

    # checking if the message is multipart
    logger.info(f"Multipart check : {msg.is_multipart()}")
    multipart_content = {}
    # if message is multipart
    if msg.is_multipart():
        # retrieving form-data
        for part in msg.get_payload():
            # Ensure part is an instance of Message
            if isinstance(part, Message):
                # checking if filename exist as a part of content-disposition header
                if part.get_filename():
                    # fetching the filename
                    file_name = part.get_filename()
                    logger.info(f"file_name: {file_name}")
                logger.info(f"part.get_content_type(): {part.get_content_type()}")
                logger.info(
                    f"part.get_param('name', header='content-disposition'): {part.get_param('name', header='content-disposition')}"
                )
                name_param = part.get_param("name", header="content-disposition")
                if name_param:
                    multipart_content[name_param] = part.get_payload(decode=True)
    return multipart_content


def transform_tips_handler(*args, **kwargs) -> dict:
    csv = ""
    year = date.today().day
    month = date.today().month
    pay_period = 3

    try:
        event = {}
        if args is not None and len(args) == 2:
            event = args[0]
            # context = args[1]
        tips_stream = None

        if "excel" in kwargs:
            tips_stream = open("tips-aug.xlsx", "rb")
        else:
            multipart_content = decode_upload(event)
            tips_stream = io.BytesIO(multipart_content.get("file[]", b""))
            if "year" in multipart_content:
                try:
                    year = int(multipart_content["year"])
                    month = int(multipart_content["month"])
                    pay_period = int(multipart_content["pay_period"])
                except Exception:
                    error_body = {"message": "Error parsing the multipart content"}
                    logger.exception(error_body["message"])
                    return create_response(400, error_body)
        t = Tips()
        csv_tips = t.exportTipsTransform(tips_stream)
        lines = csv_tips.strip().split("\n")
        if len(lines) <= 1:
            # CSV text contains only the header and no data
            # Fail fast or handle the scenario accordingly
            return create_response(
                400,
                {
                    "message": "No tips generated please save the file in Excel before uploading to fix."
                },
            )
        if pay_period >= 3:
            csv = csv_tips
        else:
            csv_mpvs = t.exportMealPeriodViolations(
                store_config.all_stores, date(year, month, 5), pay_period
            )
            merged_data = pd.merge(
                pd.read_csv(io.StringIO(csv_tips)),
                pd.read_csv(io.StringIO(csv_mpvs)),
                on=["last_name", "first_name", "title"],
                how="outer",
            )
            csv = merged_data.to_csv(index=False)

    except Exception:
        error_body = {"message": "Error parsing tips"}
        logger.exception(error_body["message"])
        return create_response(400, error_body)
    return create_response(200, csv, content_type="text/csv", filename="gusto_tips.csv")


def get_mpvs_handler(*args, **kwargs):
    csv = ""
    year = date.today().year
    month = date.today().month
    pay_period = 2

    try:
        event = {}
        if args is not None and len(args) == 2:
            event = args[0]
            # context = args[1]
        multipart_content = decode_upload(event)
        if "year" in multipart_content:
            try:
                year = int(multipart_content["year"])
                month = int(multipart_content["month"])
                pay_period = int(multipart_content["pay_period"])
            except Exception:
                error_body = {"message": "Error parsing the multipart content"}
                logger.exception(error_body["message"])
                return create_response(400, error_body)
        t = Tips()
        csv = t.exportMealPeriodViolations(
            store_config.all_stores, date(year, month, 5), pay_period
        )
    except Exception:
        error_body = {"message": "Error generating MPVs"}
        logger.exception(error_body["message"])
        return create_response(400, error_body)
    return create_response(200, csv, content_type="text/csv", filename="gusto_mpvs.csv")


def update_food_handler_pdfs_handler(*args, **kwargs) -> dict:
    """
    Asynchronously update the combined food handler PDFs for each store.

    Lambda invocation:
        - HTTP Method: POST
        - No parameters required

    Returns:
        Success message while the update runs in the background
    """
    try:
        gdrive = WMCGdrive()
        # This will run and update the PDFs
        gdrive.combine_food_handler_cards_by_store()
        return create_response(200, {"message": "PDF update completed"})
    except Exception:
        logger.exception("Error updating food handler PDFs")
        return create_response(500, {"message": "Error starting PDF update"})


def get_food_handler_links_handler(*args, **kwargs) -> dict:
    """
    Get current public links to combined food handler PDFs for each store.

    Lambda invocation:
        - HTTP Method: GET
        - No parameters required

    Returns:
        Dictionary mapping store numbers to PDF download links
    """
    try:
        gdrive = WMCGdrive()
        links = gdrive.get_food_handler_pdf_links()
        return create_response(200, links)
    except Exception:
        logger.exception("Error getting food handler PDF links")
        return create_response(500, {"message": "Error getting food handler PDF links"})
