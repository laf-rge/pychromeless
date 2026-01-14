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

import calendar
import json
import logging
import os
import re
import uuid
from concurrent.futures import (  # pylint: disable=no-name-in-module  # type: ignore[attr-defined]  # noqa: F401
    ThreadPoolExecutor,
    as_completed,
)
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import partial  # noqa # pylint: disable=unused-import
from locale import LC_NUMERIC, atof, setlocale
from operator import itemgetter
from typing import Any, cast

import boto3
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

# Initialize table conditionally (only if environment variable exists)
if "CONNECTIONS_TABLE" in os.environ:
    table = cast(Any, dynamodb.Table(os.environ["CONNECTIONS_TABLE"]))
else:
    table = None

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

    if request_id is not None:
        headers["X-Request-ID"] = request_id

    return {
        "statusCode": status_code,
        "body": json.dumps(body) if content_type == "application/json" else body,
        "headers": headers,
    }


def third_party_deposit_handler(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    """
    Process third-party deposits from various services.

    Lambda invocation:
        - Schedule: Daily
        - No event parameters required

    Local development:
        >>> from lambda_function import third_party_deposit_handler
        >>> third_party_deposit_handler()
    """
    context = _args[1] if _args and len(_args) > 1 else None
    task_id = (
        context.aws_request_id if context else None
    ) or f"local-{str(uuid.uuid4())}"
    ws_manager = WebSocketManager()

    ws_manager.broadcast_status(
        task_id=task_id,
        operation=OperationType.THIRD_PARTY_DEPOSIT,
        status="started",
    )

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
        # (Grubhub(), "get_payments", start_date, end_date),
        (EZCater(), "get_payments", store_config.all_stores, start_date, end_date),
    ]

    failed_services: list[str] = []
    successful_services: list[str] = []

    for service, method, *service_args in services:
        service_name = service.__class__.__name__
        try:
            results = getattr(service, method)(*service_args)
            for result in results:
                try:
                    qb.sync_third_party_deposit(*result)
                except Exception:
                    logger.exception(
                        f"Exception in sync_third_party_deposit for {service_name}"
                    )
                    logger.info(result)
            successful_services.append(service_name)
        except Exception:
            logger.exception(f"Exception in {service_name}")
            failed_services.append(service_name)

    if failed_services:
        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.THIRD_PARTY_DEPOSIT,
            status="completed_with_errors",
            result={
                "summary": f"Processed {len(successful_services)} services, {len(failed_services)} failed",
                "successful_services": successful_services,
                "failed_services": failed_services,
            },
        )
    else:
        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.THIRD_PARTY_DEPOSIT,
            status="completed",
            result={
                "summary": f"Successfully processed {len(successful_services)} services",
                "successful_services": successful_services,
            },
        )

    return create_response(200, {"message": "Success"})


def invoice_sync_handler(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
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
    context = _args[1] if _args and len(_args) > 1 else None
    task_id = (
        context.aws_request_id if context else None
    ) or f"local-{str(uuid.uuid4())}"
    ws_manager = WebSocketManager()

    ws_manager.broadcast_status(
        task_id=task_id,
        operation=OperationType.INVOICE_SYNC,
        status="started",
    )

    try:
        event = _args[0] if _args and len(_args) > 0 else {}
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

        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.INVOICE_SYNC,
            status="completed",
            result={
                "summary": f"Processed GL and inventory for {inventory_year}-{inventory_month:02d}",
                "inventory_year": inventory_year,
                "inventory_month": inventory_month,
                "stores": store_config.all_stores,
            },
        )

        return create_response(200, {"message": "Success"})
    except Exception as e:
        logger.exception("Error processing invoice sync")
        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.INVOICE_SYNC,
            status="failed",
            error=str(e),
        )
        return create_response(500, {"message": "Error processing invoice sync"})


def daily_sales_handler(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
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
    event = _args[0] if _args and len(_args) > 0 else {}
    context = _args[1] if _args and len(_args) > 1 else None
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
        # txdates = list(map(partial(date, 2025, 11), range(5, 30)))
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

        # Initialize Lambda client only if running in AWS
        if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
            # Configure boto3 client with timeouts that match Lambda function timeout (300s + buffer)
            # pylint: disable=import-outside-toplevel
            from botocore.config import Config

            config = Config(
                read_timeout=350,  # 350 seconds (internal lambda timeout + buffer)
                connect_timeout=10,  # 10 seconds for connection
                retries={
                    "max_attempts": 0
                },  # Disable retries to avoid double processing
            )
            lambda_client = boto3.client("lambda", config=config)
            # Determine the internal Lambda function name from current function name
            workspace = os.environ["AWS_LAMBDA_FUNCTION_NAME"].split("-")[-1]
            internal_function_name = f"process-store-sales-internal-{workspace}"
        else:
            lambda_client = None
            internal_function_name = None

        success = False
        stores: list[str] = []
        all_journal_data: dict[str, dict[str, Any]] = {}
        failed_stores: list[str] = []

        for txdate in txdates:
            stores = store_config.get_active_stores(txdate)

            # Process stores - parallel Lambda invocations in AWS, sequential calls locally
            is_local = "AWS_LAMBDA_FUNCTION_NAME" not in os.environ
            logger.info(
                "Starting store processing",
                extra={
                    "txdate": txdate.isoformat(),
                    "stores": stores,
                    "total_stores": len(stores),
                    "is_local": is_local,
                    "processing_mode": "sequential" if is_local else "parallel",
                },
            )

            # Process all stores and aggregate results

            # Reset for this transaction date
            all_journal_data.clear()
            failed_stores.clear()

            def invoke_store_lambda(
                store: str, txdate: date = txdate
            ) -> tuple[str, dict[str, Any]]:
                """Helper function for AWS Lambda invocation"""
                try:
                    assert lambda_client is not None  # Type hint for linter
                    assert internal_function_name is not None  # Type hint for linter
                    response = lambda_client.invoke(
                        FunctionName=internal_function_name,
                        InvocationType="RequestResponse",  # Synchronous call
                        Payload=json.dumps(
                            {
                                "store": store,
                                "txdate": txdate.isoformat(),
                                "request_id": request_id,
                            }
                        ),
                    )
                    payload = json.loads(response["Payload"].read())
                    return store, payload
                except Exception as e:
                    error_type = type(e).__name__
                    error_msg = str(e)

                    # Provide specific guidance for timeout errors
                    if (
                        "ReadTimeoutError" in error_type
                        or "timeout" in error_msg.lower()
                    ):
                        logger.warning(
                            "Lambda invocation timed out - store processing taking longer than expected",
                            extra={
                                "store": store,
                                "txdate": txdate.isoformat(),
                                "error_type": error_type,
                                "timeout_duration": "350s",
                                "suggestion": "Consider checking Flexepos response times or increasing Lambda timeout",
                            },
                        )
                    else:
                        logger.exception(
                            "Failed to invoke Lambda for store",
                            extra={
                                "store": store,
                                "txdate": txdate.isoformat(),
                                "error_type": error_type,
                                "error": error_msg,
                            },
                        )
                    return store, {
                        "statusCode": 500,
                        "error": f"{error_type}: {error_msg}",
                    }

            # Send initial processing status with store count
            ws_manager.broadcast_status(
                task_id=request_id,
                operation=OperationType.DAILY_SALES,
                status="processing",
                progress={
                    "current": 0,
                    "total": len(stores),
                    "message": f"Starting processing for {len(stores)} stores",
                },
            )

            # Process stores based on environment
            if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
                # Local: process sequentially
                completed_count = 0
                for store in stores:
                    try:
                        logger.info(
                            "Running locally - calling store processing function directly",
                            extra={"store": store, "txdate": txdate.isoformat()},
                        )
                        store_event = {
                            "store": store,
                            "txdate": txdate.isoformat(),
                            "request_id": request_id,
                        }
                        result = process_store_sales_internal_handler(store_event, None)

                        # Extract journal data from response
                        if result.get("statusCode") == 200:
                            response_body = json.loads(result["body"])
                            if "journal_data" in response_body:
                                all_journal_data.update(response_body["journal_data"])
                            completed_count += 1

                            # Send progress update for local processing
                            ws_manager.broadcast_status(
                                task_id=request_id,
                                operation=OperationType.DAILY_SALES,
                                status="processing",
                                progress={
                                    "current": completed_count,
                                    "total": len(stores),
                                    "message": f"Processed store {store} ({completed_count}/{len(stores)})",
                                },
                            )
                        else:
                            failed_stores.append(store)
                            completed_count += 1
                            logger.error(
                                "Store processing failed locally",
                                extra={"store": store, "result": result},
                            )

                            # Send progress update even for failures
                            ws_manager.broadcast_status(
                                task_id=request_id,
                                operation=OperationType.DAILY_SALES,
                                status="processing",
                                progress={
                                    "current": completed_count,
                                    "total": len(stores),
                                    "message": f"Failed to process store {store} ({completed_count}/{len(stores)})",
                                },
                            )
                    except Exception as e:
                        failed_stores.append(store)
                        completed_count += 1
                        logger.exception(
                            "Failed to process store locally",
                            extra={
                                "store": store,
                                "txdate": txdate.isoformat(),
                                "error": str(e),
                            },
                        )

                        # Send progress update for exception
                        ws_manager.broadcast_status(
                            task_id=request_id,
                            operation=OperationType.DAILY_SALES,
                            status="processing",
                            progress={
                                "current": completed_count,
                                "total": len(stores),
                                "message": f"Error processing store {store} ({completed_count}/{len(stores)})",
                            },
                        )
            else:
                # AWS: process concurrently using ThreadPoolExecutor
                logger.info(
                    "Processing stores concurrently in AWS",
                    extra={
                        "store_count": len(stores),
                        "txdate": txdate.isoformat(),
                    },
                )

                import time

                start_time = time.time()

                with ThreadPoolExecutor(max_workers=min(len(stores), 10)) as executor:
                    # Submit all lambda invocations with a 10-second delay between each
                    future_to_store = {}
                    for idx, store in enumerate(stores):
                        future_to_store[executor.submit(invoke_store_lambda, store)] = (
                            store
                        )
                        if idx < len(stores) - 1:
                            time.sleep(
                                10
                            )  # Wait 10 seconds before submitting the next store

                    logger.info(
                        "Submitted all Lambda invocations",
                        extra={
                            "submitted_count": len(future_to_store),
                            "max_workers": min(len(stores), 10),
                        },
                    )

                    # Collect results as they complete
                    completed_count = 0
                    for future in as_completed(future_to_store):
                        original_store = future_to_store[future]
                        try:
                            store, payload = future.result()
                            completed_count += 1

                            logger.info(
                                "Lambda invocation completed",
                                extra={
                                    "store": store,
                                    "completed": completed_count,
                                    "total": len(stores),
                                    "elapsed_time": f"{time.time() - start_time:.1f}s",
                                },
                            )

                            # Send progress update for each completed store
                            success = payload.get("statusCode") == 200
                            status_msg = (
                                f"Processed store {store}"
                                if success
                                else f"Failed to process store {store}"
                            )

                            ws_manager.broadcast_status(
                                task_id=request_id,
                                operation=OperationType.DAILY_SALES,
                                status="processing",
                                progress={
                                    "current": completed_count,
                                    "total": len(stores),
                                    "message": f"{status_msg} ({completed_count}/{len(stores)}) - {time.time() - start_time:.1f}s elapsed",
                                },
                            )

                            if payload.get("statusCode") == 200:
                                response_body = json.loads(payload["body"])
                                if "journal_data" in response_body:
                                    all_journal_data.update(
                                        response_body["journal_data"]
                                    )
                                logger.info(
                                    "Successfully processed store via concurrent Lambda",
                                    extra={
                                        "store": store,
                                        "txdate": txdate.isoformat(),
                                    },
                                )
                            else:
                                failed_stores.append(store)
                                logger.error(
                                    "Store processing failed in concurrent Lambda",
                                    extra={"store": store, "response": payload},
                                )
                        except Exception as e:
                            failed_stores.append(original_store)
                            completed_count += 1
                            logger.exception(
                                "Failed to get result from concurrent Lambda",
                                extra={
                                    "store": original_store,
                                    "txdate": txdate.isoformat(),
                                    "error": str(e),
                                },
                            )

                            # Send progress update for exception
                            ws_manager.broadcast_status(
                                task_id=request_id,
                                operation=OperationType.DAILY_SALES,
                                status="processing",
                                progress={
                                    "current": completed_count,
                                    "total": len(stores),
                                    "message": f"Error processing store {original_store} ({completed_count}/{len(stores)}) - {time.time() - start_time:.1f}s elapsed",
                                },
                            )

                logger.info(
                    "Completed all Lambda invocations",
                    extra={
                        "total_time": f"{time.time() - start_time:.1f}s",
                        "successful_stores": len(all_journal_data),
                        "failed_stores": len(failed_stores),
                        "total_stores": len(stores),
                    },
                )

            # Now make a single QB call with all collected data
            if all_journal_data:
                try:
                    logger.info(
                        "Creating daily sales in QuickBooks",
                        extra={
                            "txdate": txdate.isoformat(),
                            "stores_with_data": list(all_journal_data.keys()),
                        },
                    )
                    qb.create_daily_sales(txdate, all_journal_data)

                    ws_manager.broadcast_status(
                        task_id=request_id,
                        operation=OperationType.DAILY_SALES,
                        status="processing",
                        progress={
                            "current": len(stores),
                            "total": len(stores),
                            "message": f"QuickBooks entries created for {len(all_journal_data)} stores"
                            + (
                                f" ({len(failed_stores)} failed)"
                                if failed_stores
                                else ""
                            ),
                        },
                    )
                except Exception as e:
                    logger.exception(
                        "Failed to create daily sales in QuickBooks",
                        extra={
                            "txdate": txdate.isoformat(),
                            "stores": list(all_journal_data.keys()),
                            "error": str(e),
                        },
                    )
                    ws_manager.broadcast_status(
                        task_id=request_id,
                        operation=OperationType.DAILY_SALES,
                        status="failed",
                        error=f"Failed to create QuickBooks entries: {str(e)}",
                    )
                    return create_response(
                        500,
                        {"message": f"Failed to create QuickBooks entries: {str(e)}"},
                        request_id=request_id,
                    )
            else:
                logger.info(
                    "No journal data collected from any stores",
                    extra={
                        "txdate": txdate.isoformat(),
                        "failed_stores": failed_stores,
                    },
                )

            # Log completion of store data collection
            is_local = "AWS_LAMBDA_FUNCTION_NAME" not in os.environ
            logger.info(
                "Completed store data collection",
                extra={
                    "txdate": txdate.isoformat(),
                    "stores_processed": len(all_journal_data),
                    "stores_failed": len(failed_stores),
                    "total_stores": len(stores),
                    "is_local": is_local,
                },
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
            dj = Flexepos()  # Initialize for online payments/royalty processing
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

            # Determine final status based on results
            final_status = (
                "completed" if len(failed_stores) == 0 else "completed_with_errors"
            )

            ws_manager.broadcast_status(
                task_id=request_id,
                operation=OperationType.DAILY_SALES,
                status=final_status,
                result={
                    "processed_dates": [d.isoformat() for d in txdates],
                    "successful_stores": list(all_journal_data.keys()),
                    "failed_stores": failed_stores,
                    "total_stores": len(stores),
                    "success_count": len(all_journal_data),
                    "failure_count": len(failed_stores),
                    "summary": f"Processed {len(all_journal_data)} of {len(stores)} stores successfully"
                    + (f" ({len(failed_stores)} failed)" if failed_stores else ""),
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


def online_cc_fee(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    txdate = date.today() - timedelta(days=1)

    dj = Flexepos()
    payment_data = dj.getOnlinePayments(
        store_config.all_stores, txdate.year, txdate.month
    )
    qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data)
    return create_response(200, {"message": "Success"})


def daily_journal_handler(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    """
    Generate and email daily journal reports.

    Lambda invocation:
        - Schedule: Daily
        - No event parameters required

    Local development:
        >>> from lambda_function import daily_journal_handler
        >>> daily_journal_handler()
    """
    context = _args[1] if _args and len(_args) > 1 else None
    task_id = (
        context.aws_request_id if context else None
    ) or f"local-{str(uuid.uuid4())}"
    ws_manager = WebSocketManager()

    ws_manager.broadcast_status(
        task_id=task_id,
        operation=OperationType.DAILY_JOURNAL,
        status="started",
    )

    try:
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

        message = (
            "<h1>Wagoner Management Corp.</h1>\n\n<h2>Cash Drawer Opens:</h2>\n<pre>"
        )

        for store, journal in drawer_opens.items():
            message = "{}{}: {}\n".format(
                message, store, journal.count("Cash Drawer Open")
            )

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
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.DAILY_JOURNAL,
                status="failed",
                error=f"Email Failed: {error_message}",
            )
            return create_response(400, {"message": f"Email Failed: {error_message}"})

        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.DAILY_JOURNAL,
            status="completed",
            result={
                "summary": f"Daily journal report for {yesterday.strftime('%m/%d/%Y')} sent",
                "report_date": yesterday.isoformat(),
                "stores": store_config.all_stores,
            },
        )

        return create_response(200, response)
    except Exception as e:
        logger.exception("Error processing daily journal")
        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.DAILY_JOURNAL,
            status="failed",
            error=str(e),
        )
        raise


def email_tips_handler(*args: Any, **_kwargs: Any) -> dict[str, Any]:
    context = args[1] if args and len(args) > 1 else None
    task_id = (
        context.aws_request_id if context else None
    ) or f"local-{str(uuid.uuid4())}"
    ws_manager = WebSocketManager()

    ws_manager.broadcast_status(
        task_id=task_id,
        operation=OperationType.EMAIL_TIPS,
        status="started",
    )

    try:
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

        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.EMAIL_TIPS,
            status="completed",
            result={
                "summary": f"Tips email sent for {year}-{month:02d} pay period {pay_period}",
                "year": year,
                "month": month,
                "pay_period": pay_period,
            },
        )

        return create_response(200, {"message": "Email Sent!"})
    except Exception as e:
        logger.exception("Error processing email tips")
        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.EMAIL_TIPS,
            status="failed",
            error=str(e),
        )
        raise


def update_food_handler_pdfs_handler(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
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


def get_food_handler_links_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
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


def split_bill_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
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
                split_ratios = {k: Decimal(v) for k, v in split_ratios.items()}

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
            if new_bills:
                split_doc_numbers = [bill.DocNumber for bill in new_bills]
                return create_response(
                    200,
                    {
                        "message": "Bill split successfully",
                        "split_doc_numbers": split_doc_numbers,
                    },
                )
            else:
                logger.error(
                    "Error splitting bill", extra={"error": "No new bills created"}
                )
                return create_response(500, {"message": "Error splitting bill"})

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


def process_store_sales_internal_handler(
    event: dict[str, Any], context: Any
) -> dict[str, Any]:
    """
    Internal Lambda handler to process daily sales for a single store.

    Called by daily_sales_handler via fire-and-forget Lambda invocation.

    Event format:
        {
            "store": "store_id",
            "txdate": "YYYY-MM-DD",
            "request_id": "uuid"
        }
    """
    try:
        # Extract parameters from event
        store = event["store"]
        txdate = datetime.fromisoformat(event["txdate"]).date()
        request_id = event["request_id"]

        # Process this store's daily sales with retry logic
        dj = Flexepos()
        journal_data = None
        retry = 3

        while retry:
            try:
                journal_data = dj.getDailySales(store, txdate)
                retry = 0
            except Exception as e:
                logger.exception(f"error {txdate.isoformat()}: {str(e)}")
                retry -= 1
                if retry == 0:
                    # Final failure - return error
                    logger.error(
                        "Failed to process store sales after retries",
                        extra={
                            "store": store,
                            "txdate": txdate.isoformat(),
                            "error": str(e),
                        },
                    )
                    return create_response(
                        500,
                        {
                            "message": f"Failed to get sales data for store {store}: {str(e)}"
                        },
                    )

        # Check if we have valid sales data
        if not journal_data or "Payins" not in journal_data[store]:
            logger.info(
                "Skipping store: no sales data",
                extra={
                    "store": store,
                    "txdate": txdate.isoformat(),
                    "journal_data": journal_data,
                },
            )
            # Return empty result (no sales = successful completion, but no data to process)
            return create_response(
                200, {"message": f"No sales data for store {store}", "journal_data": {}}
            )

        # Send deposit and payin alerts for this store
        if store_config.is_store_active(store, txdate):
            # Check for missing deposits
            if (
                journal_data[store]["Bank Deposits"] is None
                or journal_data[store]["Bank Deposits"] == ""
            ):
                email_service.send_missing_deposit_alert(store, txdate)

            # Check for high payins
            payins = journal_data[store]["Payins"].strip()
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
                "Skipping store deposit emails: store not active",
                extra={"store": store, "txdate": txdate.isoformat()},
            )

        logger.info(
            "Successfully processed store sales data",
            extra={
                "store": store,
                "txdate": txdate.isoformat(),
                "request_id": request_id,
            },
        )

        # Return the journal data for aggregation by main lambda
        return create_response(
            200,
            {
                "message": f"Successfully processed store {store}",
                "journal_data": journal_data,
            },
        )

    except Exception as e:
        # Handle any unexpected errors
        store = event.get("store", "unknown")
        request_id = event.get("request_id", "unknown")

        logger.exception(
            "Unexpected error in process_store_sales_internal_handler",
            extra={"store": store, "request_id": request_id, "error": str(e)},
        )

        # Log the failure for debugging

        return create_response(
            500, {"message": f"Internal error processing store {store}"}
        )


# =============================================================================
# Wrapper functions for Terraform compatibility
# These functions delegate to the extracted modules while maintaining the
# expected lambda_function.handler_name interface that Terraform requires.
# =============================================================================


def transform_tips_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Wrapper for tips_processing.transform_tips_handler (required by Terraform)"""
    # pylint: disable=import-outside-toplevel
    from tips_processing import transform_tips_handler as _impl

    result: dict[str, Any] = _impl(*args, **kwargs)
    return result


def get_mpvs_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Wrapper for tips_processing.get_mpvs_handler (required by Terraform)"""
    # pylint: disable=import-outside-toplevel
    from tips_processing import get_mpvs_handler as _impl

    result: dict[str, Any] = _impl(*args, **kwargs)
    return result


def connect_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Wrapper for websocket_handlers.connect_handler (required by Terraform)"""
    # pylint: disable=import-outside-toplevel
    from websocket_handlers import connect_handler as _impl

    result: dict[str, Any] = _impl(event, context)
    return result


def disconnect_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Wrapper for websocket_handlers.disconnect_handler (required by Terraform)"""
    # pylint: disable=import-outside-toplevel
    from websocket_handlers import disconnect_handler as _impl

    result: dict[str, Any] = _impl(event, context)
    return result


def default_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Wrapper for websocket_handlers.default_handler (required by Terraform)"""
    # pylint: disable=import-outside-toplevel
    from websocket_handlers import default_handler as _impl

    result: dict[str, Any] = _impl(event, context)
    return result


def cleanup_connections_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Wrapper for websocket_handlers.cleanup_connections_handler (required by Terraform)"""
    # pylint: disable=import-outside-toplevel
    from websocket_handlers import cleanup_connections_handler as _impl

    result: dict[str, Any] = _impl(event, context)
    return result


def payroll_allocation_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Process payroll allocation from Gusto CSV to QuickBooks journal entry.

    Lambda invocation:
        - HTTP Method: POST
        - Content-Type: multipart/form-data
        - Form fields:
            - file: Gusto "Total By Location" CSV file
            - year: YYYY (required)
            - month: MM (required)
            - allow_update: "true" to replace existing entry (optional, default false)

    Returns:
        JSON response with:
            - success: bool
            - journal_entry_url: str (if successful)
            - doc_number: str (e.g., "labor-2025-11")
            - summary: dict with allocation summary
            - warnings: list of any warnings (e.g., reimbursements to handle)
            - exists: bool (if entry already exists and allow_update was false)
            - existing_url: str (URL to existing entry if exists is true)
    """
    # pylint: disable=import-outside-toplevel
    from payroll_allocation import process_payroll_allocation
    from tips_processing import decode_upload

    context = args[1] if args and len(args) > 1 else None
    task_id = (context.aws_request_id if context else None) or f"local-{uuid.uuid4()}"
    ws_manager = WebSocketManager()

    ws_manager.broadcast_status(
        task_id=task_id,
        operation=OperationType.PAYROLL_ALLOCATION,
        status="started",
    )

    try:
        event = args[0] if args and len(args) > 0 else {}

        # Parse multipart form data
        multipart_content = decode_upload(event)

        # Extract year and month from form data
        year_bytes = multipart_content.get("year", b"")
        month_bytes = multipart_content.get("month", b"")

        if not year_bytes or not month_bytes:
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.PAYROLL_ALLOCATION,
                status="failed",
                error="year and month are required",
            )
            return create_response(400, {"message": "year and month are required"})

        year = int(year_bytes.decode("utf-8"))
        month = int(month_bytes.decode("utf-8"))

        # Extract allow_update flag (default to False)
        allow_update_bytes = multipart_content.get("allow_update", b"")
        allow_update = allow_update_bytes.decode("utf-8").lower() == "true"

        # Extract CSV file content
        csv_content = multipart_content.get("file", b"")
        if not csv_content:
            # Try alternative field names
            csv_content = multipart_content.get("file[]", b"")

        if not csv_content:
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.PAYROLL_ALLOCATION,
                status="failed",
                error="CSV file is required",
            )
            return create_response(400, {"message": "CSV file is required"})

        # Process payroll allocation
        result = process_payroll_allocation(
            year, month, csv_content, allow_update=allow_update
        )

        if result.get("success"):
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.PAYROLL_ALLOCATION,
                status="completed",
                result={
                    "summary": f"Created journal entry {result['doc_number']}",
                    "journal_entry_url": result.get("journal_entry_url"),
                    "warnings": result.get("warnings", []),
                },
            )
            return create_response(200, result)
        else:
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.PAYROLL_ALLOCATION,
                status="failed",
                error=result.get("error", "Unknown error"),
            )
            return create_response(400, result)

    except Exception as e:
        logger.exception("Error processing payroll allocation")
        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.PAYROLL_ALLOCATION,
            status="failed",
            error=str(e),
        )
        return create_response(500, {"message": f"Error: {str(e)}"})


def grubhub_csv_import_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Import GrubHub deposits from CSV export to QuickBooks.

    Lambda invocation:
        - HTTP Method: POST
        - Content-Type: multipart/form-data
        - Form fields:
            - file: GrubHub deposit CSV export (required)
            - start_date: YYYY-MM-DD (optional, filter deposits after this date)
            - end_date: YYYY-MM-DD (optional, filter deposits before this date)

    Returns:
        JSON response with:
            - success: bool
            - summary: dict with total/imported/skipped/failed counts
            - imported_deposits: list of imported deposits
            - skipped_deposits: list of skipped deposits (duplicates)
            - errors: list of failed deposits with error messages
    """
    # pylint: disable=import-outside-toplevel
    import tempfile
    from datetime import date

    from grubhub import Grubhub
    from tips_processing import decode_upload

    context = args[1] if args and len(args) > 1 else None
    task_id = (context.aws_request_id if context else None) or f"local-{uuid.uuid4()}"
    ws_manager = WebSocketManager()

    ws_manager.broadcast_status(
        task_id=task_id,
        operation=OperationType.GRUBHUB_CSV_IMPORT,
        status="started",
    )

    try:
        event = args[0] if args and len(args) > 0 else {}

        # Parse multipart form data
        multipart_content = decode_upload(event)

        # Extract CSV file content
        csv_content = multipart_content.get("file", b"")
        if not csv_content:
            csv_content = multipart_content.get("file[]", b"")

        if not csv_content:
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.GRUBHUB_CSV_IMPORT,
                status="failed",
                error="CSV file is required",
            )
            return create_response(400, {"message": "CSV file is required"})

        # Extract optional date filters
        start_date: date | None = None
        end_date: date | None = None

        start_date_bytes = multipart_content.get("start_date", b"")
        if start_date_bytes:
            start_date_str = start_date_bytes.decode("utf-8").strip()
            if start_date_str:
                start_date = date.fromisoformat(start_date_str)

        end_date_bytes = multipart_content.get("end_date", b"")
        if end_date_bytes:
            end_date_str = end_date_bytes.decode("utf-8").strip()
            if end_date_str:
                end_date = date.fromisoformat(end_date_str)

        # Write CSV to temp file for parsing
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv", delete=False
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_filename = tmp_file.name

        try:
            # Parse CSV
            gh = Grubhub()
            results = gh.get_payments_from_csv(tmp_filename, start_date, end_date)
        finally:
            # Clean up temp file
            import os

            os.unlink(tmp_filename)

        if not results:
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.GRUBHUB_CSV_IMPORT,
                status="completed",
                result={
                    "summary": "No deposits found in CSV for the specified date range"
                },
            )
            return create_response(
                200,
                {
                    "success": True,
                    "summary": {
                        "total_deposits": 0,
                        "imported": 0,
                        "skipped": 0,
                        "failed": 0,
                    },
                    "imported_deposits": [],
                    "skipped_deposits": [],
                    "errors": [],
                },
            )

        # Import deposits to QuickBooks
        imported_deposits = []
        skipped_deposits = []
        errors = []

        for i, result in enumerate(results):
            service, txdate, notes, lines, store = result
            amount = lines[0][2] if lines else "0"

            try:
                status = qb.sync_third_party_deposit(
                    service, txdate, notes, lines, store
                )

                if status == "created":
                    imported_deposits.append(
                        {"store": store, "date": str(txdate), "amount": amount}
                    )
                else:  # status == "skipped"
                    skipped_deposits.append(
                        {
                            "store": store,
                            "date": str(txdate),
                            "amount": amount,
                            "reason": "Already exists",
                        }
                    )

                # Send progress update
                ws_manager.broadcast_status(
                    task_id=task_id,
                    operation=OperationType.GRUBHUB_CSV_IMPORT,
                    status="in_progress",
                    result={
                        "message": f"Processing deposit {i + 1} of {len(results)}",
                        "current": i + 1,
                        "total": len(results),
                    },
                )

            except Exception as e:
                logger.exception(
                    "Failed to import deposit",
                    extra={"store": store, "date": str(txdate), "amount": amount},
                )
                errors.append(
                    {
                        "store": store,
                        "date": str(txdate),
                        "amount": amount,
                        "error": str(e),
                    }
                )

        summary = {
            "total_deposits": len(results),
            "imported": len(imported_deposits),
            "skipped": len(skipped_deposits),
            "failed": len(errors),
        }

        success = len(errors) == 0

        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.GRUBHUB_CSV_IMPORT,
            status="completed" if success else "completed_with_errors",
            result={
                "summary": f"Imported {summary['imported']}, skipped {summary['skipped']}, failed {summary['failed']}",
            },
        )

        return create_response(
            200,
            {
                "success": success,
                "summary": summary,
                "imported_deposits": imported_deposits,
                "skipped_deposits": skipped_deposits,
                "errors": errors,
            },
        )

    except Exception as e:
        logger.exception("Error processing GrubHub CSV import")
        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.GRUBHUB_CSV_IMPORT,
            status="failed",
            error=str(e),
        )
        return create_response(500, {"message": f"Error: {str(e)}"})


def fdms_statement_import_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Import FDMS statement PDFs and create bills in QuickBooks.

    Lambda invocation:
        - HTTP Method: POST
        - Content-Type: multipart/form-data
        - Form fields:
            - file[]: One or more FDMS statement PDF files

    Returns:
        JSON response with:
            - success: bool
            - summary: dict with total_files/bills_created/files_with_chargebacks/failed
            - results: list of per-file results with bill URLs and chargeback/adjustment info
    """
    # pylint: disable=import-outside-toplevel
    from fdms_statement import (
        FDMSParseError,
        create_fdms_bills,
        parse_fdms_pdf,
    )
    from tips_processing import decode_upload

    context = args[1] if args and len(args) > 1 else None
    task_id = (context.aws_request_id if context else None) or f"local-{uuid.uuid4()}"
    ws_manager = WebSocketManager()

    ws_manager.broadcast_status(
        task_id=task_id,
        operation=OperationType.FDMS_STATEMENT_IMPORT,
        status="started",
    )

    try:
        event = args[0] if args and len(args) > 0 else {}

        # Parse multipart form data
        multipart_content = decode_upload(event)

        # Collect all PDF files from form data
        pdf_files: list[tuple[str, bytes]] = []

        for key, value in multipart_content.items():
            # Accept file[], file[0], file[1], etc. or just "file"
            if key.startswith("file") and isinstance(value, bytes):
                # Try to get filename from content-disposition if available
                filename = f"statement_{len(pdf_files) + 1}.pdf"
                pdf_files.append((filename, value))

        if not pdf_files:
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.FDMS_STATEMENT_IMPORT,
                status="failed",
                error="No PDF files provided",
            )
            return create_response(400, {"message": "No PDF files provided"})

        # Process each PDF
        results: list[dict[str, Any]] = []
        bills_created = 0
        files_with_chargebacks = 0
        failed = 0

        for i, (filename, pdf_content) in enumerate(pdf_files):
            result: dict[str, Any] = {
                "filename": filename,
                "store": None,
                "statement_month": None,
                "total_fees": None,
                "bills_count": 0,
                "bill_doc_number": None,
                "has_chargebacks": False,
                "has_adjustments": False,
                "chargebacks_text": None,
                "adjustments_text": None,
                "error": None,
            }

            try:
                # Parse PDF
                data = parse_fdms_pdf(pdf_content)
                result["store"] = data.store_number
                result["statement_month"] = data.statement_month.strftime("%B %Y")
                total = (
                    data.interchange_program_fees
                    + data.service_charges
                    + data.total_fees
                )
                result["total_fees"] = f"${total}"
                result["bill_doc_number"] = (
                    f"FDMS-{data.store_number}-{data.statement_month.strftime('%Y%m')}"
                )

                # Create bills in QuickBooks (one per fee type: INT, SVC, FEE)
                bills_count, chargebacks_text, adjustments_text = create_fdms_bills(
                    data
                )
                result["bills_count"] = bills_count
                result["chargebacks_text"] = chargebacks_text
                result["adjustments_text"] = adjustments_text
                result["has_chargebacks"] = bool(data.chargebacks)
                result["has_adjustments"] = bool(data.adjustments)

                bills_created += bills_count
                if data.chargebacks or data.adjustments:
                    files_with_chargebacks += 1

                logger.info(
                    "Successfully processed FDMS statement",
                    extra={
                        "file_name": filename,
                        "store": data.store_number,
                        "statement_month": str(data.statement_month),
                        "total_fees": str(total),
                        "bills_count": bills_count,
                    },
                )

            except FDMSParseError as e:
                result["error"] = f"Parse error: {str(e)}"
                failed += 1
                logger.warning(
                    "Failed to parse FDMS statement",
                    extra={"file_name": filename, "error": str(e)},
                )

            except Exception as e:
                result["error"] = f"Error: {str(e)}"
                failed += 1
                logger.exception(
                    "Error processing FDMS statement",
                    extra={"file_name": filename},
                )

            results.append(result)

            # Send progress update
            ws_manager.broadcast_status(
                task_id=task_id,
                operation=OperationType.FDMS_STATEMENT_IMPORT,
                status="in_progress",
                result={
                    "message": f"Processed file {i + 1} of {len(pdf_files)}",
                    "current": i + 1,
                    "total": len(pdf_files),
                },
            )

        summary = {
            "total_files": len(pdf_files),
            "bills_created": bills_created,
            "files_with_chargebacks": files_with_chargebacks,
            "failed": failed,
        }

        success = failed == 0

        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.FDMS_STATEMENT_IMPORT,
            status="completed" if success else "completed_with_errors",
            result={
                "summary": f"Created {bills_created} bills, {files_with_chargebacks} with chargebacks/adjustments, {failed} failed",
            },
        )

        return create_response(
            200,
            {
                "success": success,
                "summary": summary,
                "results": results,
            },
        )

    except Exception as e:
        logger.exception("Error processing FDMS statement import")
        ws_manager.broadcast_status(
            task_id=task_id,
            operation=OperationType.FDMS_STATEMENT_IMPORT,
            status="failed",
            error=str(e),
        )
        return create_response(500, {"message": f"Error: {str(e)}"})


def qb_auth_url_handler(*args: Any, **_kwargs: Any) -> dict[str, Any]:
    """
    Generate QuickBooks OAuth authorization URL.

    Lambda invocation:
        - HTTP Method: GET
        - Authenticated: Yes (Azure MSAL)

    Returns:
        JSON response with:
            - url: str (Intuit OAuth authorization URL)
            - state: str (CSRF protection state token)
    """
    try:
        # Generate a unique state token for CSRF protection
        state = str(uuid.uuid4())

        # Get authorization URL from qb module
        result = qb.get_auth_url(state)

        logger.info("Generated QuickBooks auth URL", extra={"state": state})

        return create_response(200, result)

    except Exception as e:
        logger.exception("Error generating QuickBooks auth URL")
        return create_response(500, {"message": f"Error: {str(e)}"})


def qb_callback_handler(*args: Any, **_kwargs: Any) -> dict[str, Any]:
    """
    Handle QuickBooks OAuth callback.

    Lambda invocation:
        - HTTP Method: GET
        - Authenticated: No (called by Intuit OAuth redirect)
        - Query params: code, realmId, state

    Returns:
        302 redirect to frontend callback page with success/error status
    """
    frontend_url = os.environ.get("FRONTEND_URL", "")
    callback_path = "/qb-callback"

    try:
        event = args[0] if args and len(args) > 0 else {}

        # Get query parameters
        params = event.get("queryStringParameters", {}) or {}
        code = params.get("code", "")
        realm_id = params.get("realmId", "")
        state = params.get("state", "")

        # Log callback receipt (without sensitive data)
        logger.info(
            "Received QuickBooks OAuth callback",
            extra={
                "has_code": bool(code),
                "has_realm_id": bool(realm_id),
                "state": state,
            },
        )

        if not code:
            error_msg = params.get(
                "error_description",
                params.get("error", "No authorization code received"),
            )
            logger.warning(
                "QuickBooks OAuth callback missing code", extra={"error": error_msg}
            )
            redirect_url = f"{frontend_url}{callback_path}?error={error_msg}"
            return {
                "statusCode": 302,
                "headers": {
                    "Location": redirect_url,
                    "Access-Control-Allow-Origin": "*",
                },
                "body": "",
            }

        # Exchange code for tokens
        result = qb.exchange_auth_code(code, realm_id)

        if result.get("success"):
            logger.info(
                "QuickBooks OAuth token exchange successful",
                extra={"realm_id": realm_id},
            )
            redirect_url = f"{frontend_url}{callback_path}?success=true"
        else:
            error_msg = result.get("error", "Token exchange failed")
            logger.error(
                "QuickBooks OAuth token exchange failed", extra={"error": error_msg}
            )
            redirect_url = f"{frontend_url}{callback_path}?error={error_msg}"

        return {
            "statusCode": 302,
            "headers": {
                "Location": redirect_url,
                "Access-Control-Allow-Origin": "*",
            },
            "body": "",
        }

    except Exception as e:
        logger.exception("Error processing QuickBooks OAuth callback")
        error_msg = str(e)
        redirect_url = f"{frontend_url}{callback_path}?error={error_msg}"
        return {
            "statusCode": 302,
            "headers": {
                "Location": redirect_url,
                "Access-Control-Allow-Origin": "*",
            },
            "body": "",
        }


def qb_connection_status_handler(*args: Any, **_kwargs: Any) -> dict[str, Any]:
    """
    Get QuickBooks connection status.

    Lambda invocation:
        - HTTP Method: GET
        - Authenticated: Yes (Azure MSAL)

    Returns:
        JSON response with:
            - connected: bool
            - company_id: str (if connected)
            - message: str
    """
    try:
        result = qb.get_connection_status()
        return create_response(200, result)
    except Exception as e:
        logger.exception("Error checking QuickBooks connection status")
        return create_response(500, {"message": f"Error: {str(e)}"})
