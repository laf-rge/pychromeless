"""
Progress tracking utilities for AWS Lambda operations.

This module provides functionality to track progress of parallel operations
using DynamoDB for atomic updates and completion detection.
"""

import logging
import os
import time
from datetime import UTC, date, datetime
from typing import Any, cast

import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

logger = logging.getLogger(__name__)

# Initialize DynamoDB resource
dynamodb = cast(DynamoDBServiceResource, boto3.resource("dynamodb"))


class DailySalesProgressTracker:
    """Helper class for tracking daily sales progress across parallel store processing."""

    def __init__(self):
        self.table_name = os.environ.get("DAILY_SALES_PROGRESS_TABLE")
        if self.table_name:
            self.table = cast(Any, dynamodb.Table(self.table_name))
        else:
            self.table = None

    def initialize_progress(
        self, request_id: str, stores: list[str], txdate: date
    ) -> None:
        """Initialize progress tracking for a new daily sales operation."""
        if not self.table:
            logger.warning("Progress table not available - skipping progress tracking")
            return

        try:
            # Calculate TTL (24 hours from now)
            ttl_timestamp = int(time.time() + (24 * 60 * 60))

            self.table.put_item(
                Item={
                    "request_id": request_id,
                    "txdate": txdate.isoformat(),
                    "total_stores": len(stores),
                    "completed_stores": 0,
                    "failed_stores": 0,
                    "store_statuses": {store: "dispatched" for store in stores},
                    "created_at": datetime.now(UTC).isoformat(),
                    "ttl": ttl_timestamp,
                }
            )
            logger.info(
                "Initialized progress tracking",
                extra={
                    "request_id": request_id,
                    "total_stores": len(stores),
                    "stores": stores,
                },
            )
        except Exception as e:
            logger.exception(
                "Failed to initialize progress tracking",
                extra={"request_id": request_id, "error": str(e)},
            )

    def update_store_completion(
        self, request_id: str, store: str, status: str, error: str | None = None
    ) -> dict:
        """
        Update completion status for a single store and return current progress.

        Returns dict with: {
            "completed": int,
            "failed": int,
            "total": int,
            "is_complete": bool,
            "store_statuses": dict
        }
        """
        if not self.table:
            logger.warning("Progress table not available - skipping progress update")
            return {
                "completed": 0,
                "failed": 0,
                "total": 0,
                "is_complete": False,
                "store_statuses": {},
            }

        try:
            # Update store status and increment counters atomically
            update_expression = "SET store_statuses.#store = :status"
            expression_values = {":status": status}
            expression_names = {"#store": store}

            if status == "completed":
                update_expression += ", completed_stores = completed_stores + :inc"
                expression_values[":inc"] = 1  # type: ignore
            elif status == "failed":
                update_expression += ", failed_stores = failed_stores + :inc"
                expression_values[":inc"] = 1  # type: ignore
                if error:
                    update_expression += ", store_statuses.#store_error = :error"
                    expression_names["#store_error"] = f"{store}_error"
                    expression_values[":error"] = error

            # Perform atomic update and return new values
            response = self.table.update_item(
                Key={"request_id": request_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW",
            )

            item = response["Attributes"]
            total = int(item["total_stores"])
            completed = int(item["completed_stores"])
            failed = int(item["failed_stores"])
            is_complete = (completed + failed) >= total

            logger.info(
                "Updated store progress",
                extra={
                    "request_id": request_id,
                    "store": store,
                    "status": status,
                    "completed": completed,
                    "failed": failed,
                    "total": total,
                    "is_complete": is_complete,
                },
            )

            return {
                "completed": completed,
                "failed": failed,
                "total": total,
                "is_complete": is_complete,
                "store_statuses": item["store_statuses"],
            }

        except Exception as e:
            logger.exception(
                "Failed to update store progress",
                extra={
                    "request_id": request_id,
                    "store": store,
                    "status": status,
                    "error": str(e),
                },
            )
            return {
                "completed": 0,
                "failed": 0,
                "total": 0,
                "is_complete": False,
                "store_statuses": {},
            }
