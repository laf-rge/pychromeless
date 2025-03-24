"""
Lambda handler for retrieving task status information.

This module provides endpoints for retrieving task status by ID or operation type,
using DynamoDB to store and query task states.
"""

import json
import os
import logging
from typing import Any, Dict, cast, Optional
import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from logging_utils import setup_json_logger

# Set up logging if not in Lambda environment
if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    setup_json_logger()
logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb = cast(DynamoDBServiceResource, boto3.resource("dynamodb"))
table = cast(Any, dynamodb.Table(os.environ["TASK_STATES_TABLE"]))


def get_task_status_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle requests for task status by ID or operation type.

    Args:
        event: API Gateway event containing request parameters
        context: Lambda context object

    Returns:
        Dict containing status code, headers, and response body
    """
    # Extract request ID from context
    request_id = context.aws_request_id if context else "local"
    logger.info(f"Processing task status request {request_id}")

    try:
        # Check if we're getting a specific task by ID
        if "pathParameters" in event and event["pathParameters"]:
            task_id = event["pathParameters"].get("task_id")
            if not task_id:
                # If no task_id provided, return all tasks
                response = table.scan()
                items = response.get("Items", [])

                # Handle pagination if there are more items
                while "LastEvaluatedKey" in response:
                    response = table.scan(
                        ExclusiveStartKey=response["LastEvaluatedKey"]
                    )
                    items.extend(response.get("Items", []))

                return create_response(200, items, request_id)

            # Get task by ID
            response = table.get_item(Key={"task_id": task_id})
            if "Item" not in response:
                return create_response(404, {"message": "Task not found"}, request_id)

            return create_response(200, response["Item"], request_id)

        # Check if we're getting tasks by operation type
        if "queryStringParameters" in event and event["queryStringParameters"]:
            operation = event["queryStringParameters"].get("operation")
            if not operation:
                # If no operation provided, return all tasks
                response = table.scan()
                items = response.get("Items", [])

                # Handle pagination if there are more items
                while "LastEvaluatedKey" in response:
                    response = table.scan(
                        ExclusiveStartKey=response["LastEvaluatedKey"]
                    )
                    items.extend(response.get("Items", []))

                return create_response(200, items, request_id)

            # Query tasks by operation type
            response = table.query(
                IndexName="operation_type-index",
                KeyConditionExpression="operation = :operation",
                ExpressionAttributeValues={":operation": operation},
            )

            return create_response(200, response.get("Items", []), request_id)

        # If no parameters provided, return all tasks
        response = table.scan()
        items = response.get("Items", [])

        # Handle pagination if there are more items
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        return create_response(200, items, request_id)

    except Exception as e:
        logger.exception("Error processing task status request")
        return create_response(500, {"message": "Internal server error"}, request_id)


def create_response(
    status_code: int,
    body: Dict[str, Any],
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized API response

    Args:
        status_code: HTTP status code
        body: Response body
        request_id: Optional request ID for tracking

    Returns:
        Dict containing the response
    """
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
        },
        "body": json.dumps(body),
    }

    if request_id:
        response["headers"]["X-Request-ID"] = request_id

    return response
