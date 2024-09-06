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
from typing import Any, cast

import boto3
import crunchtime
import pandas as pd
import qb
from botocore.exceptions import ClientError
from doordash import Doordash
from ezcater import EZCater
from flexepos import Flexepos
from grubhub import Grubhub
from ssm_parameter_store import SSMParameterStore
from tips import Tips
from ubereats import UberEats
from wmcgdrive import WMCGdrive


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
TWOPLACES = Decimal(10) ** -2
setlocale(LC_NUMERIC, "en_US.UTF-8")
pattern = re.compile(r"\d+\.\d\d")

global_stores = ["20358", "20395", "20400", "20407"]


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
    start_date = date.today() - timedelta(days=28)
    end_date = date.today()
    # start_date = date(2022, 4, 1)
    results = []
    try:
        dj = Flexepos()
        results.extend(dj.getGiftCardACH(global_stores, start_date, end_date))
        d = Doordash()
        results.extend(d.get_payments(global_stores, start_date, end_date))
        u = UberEats()
        results.extend(u.get_payments(global_stores, start_date, end_date))
        g = Grubhub()
        results.extend(g.get_payments(start_date, end_date))
        e = EZCater()
        results.extend(e.get_payments(global_stores, start_date, end_date))
    except Exception:
        error_body = {
            "message": "Exception in third_party_deposit_handler",
            "exception": str(sys.exc_info()[0]),
        }
        logger.exception(error_body["message"])
        return create_response(500, error_body)
    finally:
        for result in results:
            qb.sync_third_party_deposit(*result)
    return create_response(200, {"message": "Success"})


def invoice_sync_handler(*args, **kwargs) -> dict:
    yesterday = date.today() - timedelta(days=1)
    ct = crunchtime.Crunchtime()
    ct.process_gl_report(global_stores)
    if yesterday.day < 6:
        last_month = date.today() - timedelta(days=7)
        ct.process_inventory_report(global_stores, last_month.year, last_month.month)
    else:
        ct.process_inventory_report(global_stores, yesterday.year, yesterday.month)
    return create_response(200, {"message": "Success"})


def daily_sales_handler(*args, **kwargs) -> dict:
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
    # txdates = [date(2024,3,9)]
    # txdates = list(map(partial(date, 2024, 8), range(1, 8)))
    logger.info(
        "Started daily sales",
        extra={"txdates": [txdate.isoformat() for txdate in txdates]},
    )
    dj = Flexepos()
    for txdate in txdates:
        retry = 4
        while retry:
            try:
                stores = global_stores.copy()
                if "20400" in stores and txdate < date(2024, 1, 31):
                    stores.remove("20400")
                if "20407" in stores and txdate < date(2024, 3, 6):
                    stores.remove("20407")
                journal = dj.getDailySales(stores, txdate)
                qb.create_daily_sales(txdate, journal)
                logger.info(
                    "Successfully processed daily sales",
                    extra={"txdate": txdate.isoformat(), "stores": stores},
                )
                retry = 0
                subject = ""
                message = ""
                for store in global_stores:
                    # store not open guard
                    if (store == "20400" and txdate < date(2024, 1, 31)) or (
                        store == "20407" and txdate < date(2024, 3, 6)
                    ):
                        logger.info(
                            "Skipping store",
                            extra={"store": store, "txdate": txdate.isoformat()},
                        )
                        continue
                    if (
                        journal[store]["Bank Deposits"] is None
                        or journal[store]["Bank Deposits"] == ""
                    ):
                        subject += f"{store} "
                        message += f"{store} is missing a deposit for {str(txdate)}\n"
                    payins = journal[store]["Payins"].strip()
                    if payins.count("\n") > 0:
                        amount = Decimal(0)
                        for payin_line in payins.split("\n")[1:]:
                            if payin_line.startswith("TOTAL"):
                                continue
                            match = pattern.search(payin_line)
                            if match:
                                amount = amount + Decimal(atof(match.group()))
                        if amount.quantize(TWOPLACES) > Decimal(150):
                            send_email(
                                f"High pay-in detected {store}",
                                f"<pre>{store} - ${amount.quantize(TWOPLACES)}\n{payins}</pre>",
                            )
                    else:
                        amount = Decimal(0)
                if subject != "":
                    subject += f" missing deposit for {str(txdate)}"
                    send_email(
                        subject,
                        f"""
Folks,<br/>
I couldn't find a depsoit for the following dates for these stores:<br/>
<pre>{message}</pre>
Please correct this and re-run.<br/><br/>
Thanks,<br/>
Josiah<br/>
(aka The Robot)""",
                    )

            except:
                logger.exception(f"error {txdate.isoformat()}")
                retry -= 1
    txdate = txdates[0]
    payment_data = dj.getOnlinePayments(global_stores, txdate.year, txdate.month)
    qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data)
    royalty_data = dj.getRoyaltyReport(
        "wmc",
        date(txdate.year, txdate.month, 1),
        date(
            txdate.year, txdate.month, calendar.monthrange(txdate.year, txdate.month)[1]
        ),
    )
    qb.update_royalty(txdate.year, txdate.month, royalty_data)
    return create_response(200, {"message": "Success"})


def online_cc_fee(*args, **kwargs) -> dict:
    txdate = date.today() - timedelta(days=1)

    dj = Flexepos()
    payment_data = dj.getOnlinePayments(global_stores, txdate.year, txdate.month)
    qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data)
    return create_response(200, {"message": "Success"})


def send_email(subject, message, recipients=None):
    parameters = cast(SSMParameterStore, SSMParameterStore(prefix="/prod")["email"])
    from_email = parameters["from_email"]
    style_tag = """
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
    # overwrite the recipients if provided
    if recipients is not None:
        receiver_emails = recipients
    else:
        receiver_emails = str(parameters["receiver_email"]).split(", ")
    charset = "UTF-8"
    client = boto3.client("ses")
    return client.send_email(
        Destination={
            "ToAddresses": receiver_emails,
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": charset,
                    "Data": f"<html><head><title>{subject}</title>{style_tag}</head><body>{message}</body></html>",
                },
                #'Text': {
                #'Charset': charset,
                #'Data': message,
                # },
            },
            "Subject": {
                "Charset": charset,
                "Data": subject,
            },
        },
        Source=from_email,
        # # If you are not using a configuration set, comment or delete the
        # # following line
        # ConfigurationSetName=CONFIGURATION_SET,
    )


def attendanceTable(start_date, end_date) -> str:
    t = Tips()
    data = t.attendanceReport(global_stores, start_date, end_date)
    table = "<table>\n<tr>"
    table += "".join(f"<th>{str(item)}</th>" for item in data[0])
    table += "</tr>\n"

    for row in sorted(data[1:]):
        table += "<tr>"
        table += "".join(f"<td>{str(item)}</td>" for item in row)
        table += "</tr>\n"

    table += "</table>\n"
    return table


def daily_journal_handler(*args, **kwargs) -> dict:
    yesterday = date.today() - timedelta(days=1)

    subject = "Daily Journal Report {}".format(yesterday.strftime("%m/%d/%Y"))

    dj = Flexepos()
    drawer_opens = dict()
    drawer_opens = dj.getDailyJournal(global_stores, yesterday.strftime("%m%d%Y"))

    gdrive = WMCGdrive()
    for store in global_stores:
        gdrive.upload(
            "{0}-{1}_daily_journal.txt".format(str(yesterday), store),
            drawer_opens[store].encode("utf-8"),
            "text/plain",
        )

    message = "<h1>Wagoner Management Corp.</h1>\n\n<h2>Cash Drawer Opens:</h2>\n<pre>"

    for store, journal in drawer_opens.items():
        message = "{}{}: {}\n" "".format(
            message, store, journal.count("Cash Drawer Open")
        )

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
        t.getMealPeriodViolations(global_stores, yesterday),
        key=itemgetter("store", "start_time"),
    ):
        message += f"MPV {item['store']} {item['last_name']}, {item['first_name']}, {item['start_time']}\n"

    message += "</pre><h2>Attendance Report:</h2><div>"
    message += attendanceTable(yesterday, date.today())

    message += "</div>\n\n<div><pre>Thanks!\nJosiah (aka The Robot)</pre></div>"

    response = None
    try:
        response = send_email(subject, message)
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
    t.emailTips(global_stores, date(year, month, 5), pay_period)
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
    # concate Content-Type: with content_type from event
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
                global_stores, date(year, month, 5), pay_period
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
            global_stores, date(year, month, 5), pay_period
        )
    except Exception:
        error_body = {"message": "Error generating MPVs"}
        logger.exception(error_body["message"])
        return create_response(400, error_body)
    return create_response(200, csv, content_type="text/csv", filename="gusto_mpvs.csv")
