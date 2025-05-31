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

import base64
import calendar
import email
import io
import json
import logging
import os
import re
import time
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from email.message import Message
from functools import partial  # noqa # pylint: disable=unused-import
from locale import LC_NUMERIC, atof, setlocale
from operator import itemgetter
from typing import Any, Dict, cast

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from quickbooks.objects import Bill

import crunchtime
import qb
from doordash import Doordash
from email_service import EmailService
from ezcater import EZCater
from flexepos import Flexepos
from grubhub import Grubhub
from logging_utils import setup_json_logger
from operation_types import OperationType
from store_config import StoreConfig
from tips import Tips
from ubereats import UberEats
from websocket_manager import WebSocketManager
from wmcgdrive import WMCGdrive

load_dotenv()

store_config = StoreConfig()
email_service = EmailService(store_config)

dynamodb = cast(DynamoDBServiceResource, boto3.resource("dynamodb"))
table = cast(Any, dynamodb.Table(os.environ["CONNECTIONS_TABLE"]))

# warning! this won't work if we multiply
TWO_PLACES = Decimal(10) ** -2
setlocale(LC_NUMERIC, "en_US.UTF-8")
pattern = re.compile(r"\d+\.\d\d")

if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    setup_json_logger()
logger = logging.getLogger(__name__)


def create_response(
    status_code: int,
    body: object,
    content_type: str = "application/json",
    filename: str | None = None,
    request_id: str | None = None,
) -> dict:
    """Create a standardized API response with request ID tracking"""
    headers = {
        "Content-type": content_type,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Expose-Headers": (
            "Content-Disposition,Content-Type,X-Amz-Date,Authorization,"
            "X-Api-Key,X-Amz-Security-Token,X-Amzn-RequestId"
        ),
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
    start_date = date.today() - timedelta(days=14)
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
        event = args[0] if args and len(args) > 0 else {}
        today = date.today()

        ct = crunchtime.Crunchtime()
        # Always process GL report
        ct.process_gl_report(store_config.all_stores)

        # Determine which month's inventory to process
        if "year" in event and "month" in event:
            # Use specified year and month from event
            inventory_year = int(event["year"])
            inventory_month = int(event["month"])
        else:
            # Use business rules (process previous month until second Tuesday of new month)
            inventory_year, inventory_month = (
                store_config.get_inventory_processing_month(today)
            )

        # Process inventory report for the determined month
        ct.process_inventory_report(
            store_config.all_stores, inventory_year, inventory_month
        )
        logger.info(
            "Processed inventory report",
            extra={
                "processing_date": today.isoformat(),
                "inventory_year": inventory_year,
                "inventory_month": inventory_month,
                "stores": store_config.all_stores,
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
    event = args[0] if args and len(args) > 0 else {}
    context = args[1] if args and len(args) > 1 else None
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or (context.aws_request_id if context else None)
        or f"local-{str(uuid.uuid4())}"
    )
    ws_manager = WebSocketManager()
    txdates = []
    txdate = date.today()

    try:
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
            extra={
                "requestId": request_id,
                "txdates": [txdate.isoformat() for txdate in txdates],
            },
        )

        # Notify start
        ws_manager.broadcast_status(
            task_id=request_id, operation=OperationType.DAILY_SALES, status="started"
        )

        dj = Flexepos()
        success = False
        total_stores = len(store_config.all_stores)
        processed_stores = 0
        stores = []

        for txdate in txdates:
            stores = store_config.get_active_stores(txdate)
            journal = {}

            for store in stores:
                processed_stores += 1
                # Update progress
                ws_manager.broadcast_status(
                    task_id=request_id,
                    operation=OperationType.DAILY_SALES,
                    status="processing",
                    progress={
                        "current": processed_stores,
                        "total": total_stores,
                        "message": f"Processing store {store} for {txdate.isoformat()}",
                    },
                )

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
            ws_manager.broadcast_status(
                task_id=request_id,
                operation=OperationType.DAILY_SALES,
                status="failed",
                error="Failed to process daily sales",
            )
            return create_response(
                500, {"message": "Error processing daily sales"}, request_id=request_id
            )

        # Process online payments and royalty
        try:
            txdate = txdates[0]
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

            ws_manager.broadcast_status(
                task_id=request_id,
                operation=OperationType.DAILY_SALES,
                status="completed",
                result={
                    "processed_dates": [d.isoformat() for d in txdates],
                    "processed_stores": list(stores),
                },
            )

            return create_response(
                200,
                {"message": "Success", "task_id": request_id},
                request_id=request_id,
            )

        except Exception as e:
            error_msg = "Error processing online payments or royalty report"
            logger.exception(
                error_msg, extra={"error": str(e), "txdate": txdate.isoformat()}
            )

            ws_manager.broadcast_status(
                task_id=request_id,
                operation=OperationType.DAILY_SALES,
                status="failed",
                error=error_msg,
            )

            return create_response(500, {"message": error_msg}, request_id=request_id)

    except Exception as e:
        ws_manager.broadcast_status(
            task_id=request_id,
            operation=OperationType.DAILY_SALES,
            status="failed",
            error=str(e),
        )
        return create_response(500, {"message": str(e)}, request_id=request_id)


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
    for time_record in t.getMissingPunches():
        user = t._users[time_record["user_id"]]
        message = "{}{}, {} : {} - {}\n".format(
            message,
            user["last_name"],
            user["first_name"],
            t._locations[time_record["location_id"]]["name"],
            time_record["start_time"],
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
                    f"part.get_param('name', header='content-disposition'): "
                    f"{part.get_param('name', header='content-disposition')}"
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


def split_bill_handler(*args, **kwargs) -> dict:
    """
    Split a QuickBooks bill between multiple locations.

    Lambda invocation:
        - HTTP Method: POST
        - Request format:
            {
                "doc_number": "string",
                "locations": ["string"],
                "split_ratios": {                    # Optional
                    "location": number
                }
            }

    Returns:
        On success:
            {
                "message": "Bill split successfully",
                "split_doc_numbers": ["string"]
            }
        On error:
            {
                "message": "Error message"
            }
    """
    try:
        event = args[0] if args and len(args) > 0 else {}

        # Parse and validate input parameters
        try:
            body = json.loads(event.get("body", "{}"))
            doc_number = body.get("doc_number")
            locations = body.get("locations", [])
            split_ratios = body.get("split_ratios")

            if not doc_number:
                return create_response(400, {"message": "doc_number is required"})
            if not locations or not isinstance(locations, list):
                return create_response(
                    400, {"message": "locations must be a non-empty list"}
                )

            # Validate split_ratios if provided
            if split_ratios:
                if not isinstance(split_ratios, dict):
                    return create_response(
                        400, {"message": "split_ratios must be a dictionary"}
                    )
                if not all(isinstance(v, (int, float)) for v in split_ratios.values()):
                    return create_response(
                        400, {"message": "split_ratios values must be numbers"}
                    )
                if not all(loc in locations for loc in split_ratios.keys()):
                    return create_response(
                        400, {"message": "split_ratios keys must match locations"}
                    )

                # Convert split_ratios values to float for calculation
                split_ratios = {k: float(v) for k, v in split_ratios.items()}

        except json.JSONDecodeError:
            return create_response(400, {"message": "Invalid JSON in request body"})
        except Exception as e:
            logger.exception("Error parsing request parameters")
            return create_response(
                400, {"message": f"Invalid request parameters: {str(e)}"}
            )

        # Find the bill to split
        qb.refresh_session()
        bills = Bill.filter(DocNumber=doc_number, qb=qb.CLIENT)
        if not bills:
            return create_response(404, {"message": f"Bill not found: {doc_number}"})

        original_bill = bills[0]

        # Call the split_bill function
        try:
            new_bills = qb.split_bill(original_bill, locations, split_ratios)
            split_doc_numbers = [bill.DocNumber for bill in new_bills]

            return create_response(
                200,
                {
                    "message": "Bill split successfully",
                    "split_doc_numbers": split_doc_numbers,
                },
            )

        except ValueError as ve:
            logger.warning("Invalid split parameters", extra={"error": str(ve)})
            return create_response(400, {"message": str(ve)})
        except Exception as e:
            logger.exception(
                "Error splitting bill",
                extra={
                    "doc_number": doc_number,
                    "locations": locations,
                    "error": str(e),
                },
            )
            return create_response(500, {"message": "Error splitting bill"})

    except Exception as e:
        logger.exception("Unexpected error in split_bill_handler")
        return create_response(500, {"message": f"Internal server error: {str(e)}"})


def connect_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle WebSocket connect events"""
    connection_id = event["requestContext"]["connectionId"]

    # Calculate TTL (24 hours from now)
    ttl_timestamp = int(time.time() + (24 * 60 * 60))

    try:
        # Store connection info with TTL
        table.put_item(
            Item={
                "connection_id": connection_id,
                "ttl": ttl_timestamp,
                "connected_at": datetime.now(UTC).isoformat(),
                "client_info": {
                    # Extract client info from request if available
                    "source_ip": event["requestContext"]
                    .get("identity", {})
                    .get("sourceIp", "unknown"),
                    "user_agent": event["requestContext"]
                    .get("identity", {})
                    .get("userAgent", "unknown"),
                },
            }
        )

        return {"statusCode": 200, "body": json.dumps({"message": "Connected"})}
    except Exception as e:
        print(f"Error connecting: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"message": "Failed to connect"})}


def disconnect_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle WebSocket disconnect events"""
    connection_id = event["requestContext"]["connectionId"]

    try:
        # Remove the connection record
        table.delete_item(Key={"connection_id": connection_id})

        return {"statusCode": 200, "body": json.dumps({"message": "Disconnected"})}
    except Exception as e:
        print(f"Error disconnecting: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to disconnect"}),
        }


def default_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle default WebSocket messages and update connection TTL"""
    connection_id = event["requestContext"]["connectionId"]

    try:
        # Update TTL for the connection (extend by 24 hours)
        new_ttl = int(time.time() + (24 * 60 * 60))

        table.update_item(
            Key={"connection_id": connection_id},
            UpdateExpression="SET #ttl = :ttl",
            ExpressionAttributeNames={"#ttl": "ttl"},
            ExpressionAttributeValues={":ttl": new_ttl},
            ConditionExpression="attribute_exists(connection_id)",
        )

        # Process the actual message
        body = json.loads(event.get("body", "{}"))
        message_type = body.get("type", "unknown")

        # Handle different message types here
        if message_type == "ping":
            return {"statusCode": 200, "body": json.dumps({"type": "pong"})}

        # Default response
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Message received", "type": message_type}),
        }

    except Exception as e:
        logger.exception(f"Error in default handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error"}),
        }


def cleanup_connections_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler for cleaning up stale WebSocket connections."""
    try:
        # Extract request ID from context
        request_id = context.aws_request_id
        logger.info(f"Processing cleanup request {request_id}")

        # Get the connections table
        table = cast(Any, dynamodb.Table(os.environ["CONNECTIONS_TABLE"]))

        # Scan for all connections
        response = table.scan()
        items = response.get("Items", [])

        # Continue scanning if we have more items
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        # Delete each connection
        for item in items:
            connection_id = item["connection_id"]
            table.delete_item(
                Key={"connection_id": connection_id},
                ConditionExpression="connection_id = :cid",
                ExpressionAttributeValues={":cid": connection_id},
            )
            logger.info(f"Deleted connection {connection_id}")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "X-Request-ID": request_id,
            },
            "body": json.dumps(
                {
                    "message": f"Successfully cleaned up {len(items)} connections",
                }
            ),
        }

    except Exception as e:
        logger.exception("Error in cleanup handler")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Cleanup failed",
                    "error": str(e),
                }
            ),
        }
