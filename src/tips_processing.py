"""
Tips and file processing utilities for AWS Lambda handlers.

This module contains handlers for processing tips data and multipart file uploads,
including tips transformation and meal period violations (MPV) processing.
"""

import base64
import email
import io
import json
import logging
from datetime import date
from email.message import Message
from typing import Any

import pandas as pd

from decimal_utils import FinancialJsonEncoder
from store_config import StoreConfig
from tips import Tips

logger = logging.getLogger(__name__)

# Initialize store config
store_config = StoreConfig()


def create_response(
    status_code: int,
    body: object,
    content_type: str = "application/json",
    filename: str | None = None,
    _request_id: str | None = None,
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
        "body": (
            json.dumps(body, cls=FinancialJsonEncoder)
            if content_type == "application/json"
            else body
        ),
        "headers": headers,
    }


def decode_upload(event: dict[str, Any]) -> dict[str, bytes]:
    """
    Decode multipart form data from API Gateway event.

    Based on: https://github.com/srcecde/aws-tutorial-code/blob/master/lambda/lambda_api_multipart.py

    Args:
        event: API Gateway event containing base64-encoded multipart data

    Returns:
        Dictionary mapping form field names to their decoded byte values
    """
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
    multipart_content: dict[str, bytes] = {}
    # Track counts for duplicate field names (e.g., file[] sent multiple times)
    name_counts: dict[str, int] = {}
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
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        base_key = str(name_param)
                        # Handle duplicate field names by appending index
                        count = name_counts.get(base_key, 0)
                        if count > 0:
                            # This is a duplicate, use indexed key
                            key = f"{base_key}_{count}"
                        else:
                            # First occurrence, use original key
                            key = base_key
                        name_counts[base_key] = count + 1
                        multipart_content[key] = payload
    return multipart_content


def transform_tips_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Transform tips data from Excel format to Gusto CSV format.

    Lambda invocation:
        - HTTP Method: POST
        - Content-Type: multipart/form-data
        - Form fields:
            - file[]: Excel file containing tips data
            - year: YYYY (optional)
            - month: MM (optional)
            - pay_period: N (optional)

    Local development:
        >>> from tips_processing import transform_tips_handler
        >>> transform_tips_handler(event, context)
        >>> # Or with Excel file:
        >>> transform_tips_handler(excel="tips-aug.xlsx")

    Returns:
        CSV file for Gusto import or error response
    """
    csv = ""
    year = date.today().day
    month = date.today().month
    pay_period = 3

    try:
        event = {}
        if args is not None and len(args) == 2:
            event = args[0]
            # context = args[1]

        tips_stream: io.BufferedIOBase
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
        csv_tips = t.export_tips_transform(tips_stream)
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
            csv_mpvs = t.export_meal_period_violations(
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


def get_mpvs_handler(*args: Any, **_kwargs: Any) -> dict[str, Any]:
    """
    Generate meal period violations (MPV) report for payroll processing.

    Lambda invocation:
        - HTTP Method: POST
        - Content-Type: multipart/form-data
        - Form fields:
            - year: YYYY (optional)
            - month: MM (optional)
            - pay_period: N (optional)

    Local development:
        >>> from tips_processing import get_mpvs_handler
        >>> get_mpvs_handler(event, context)

    Returns:
        CSV file containing MPV data for Gusto import or error response
    """
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
        csv = t.export_meal_period_violations(
            store_config.all_stores, date(year, month, 5), pay_period
        )
    except Exception:
        error_body = {"message": "Error generating MPVs"}
        logger.exception(error_body["message"])
        return create_response(400, error_body)
    return create_response(200, csv, content_type="text/csv", filename="gusto_mpvs.csv")
