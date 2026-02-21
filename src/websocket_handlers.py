"""
WebSocket connection handlers for AWS API Gateway WebSocket API.

This module contains handlers for WebSocket connection lifecycle events
including connect, disconnect, default message handling, and cleanup operations.
"""

import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any, cast

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

logger = logging.getLogger(__name__)

# Initialize DynamoDB resource and table
dynamodb = cast("DynamoDBServiceResource", boto3.resource("dynamodb"))

# Initialize table conditionally (only if environment variable exists)
if "CONNECTIONS_TABLE" in os.environ:
    table = cast("Any", dynamodb.Table(os.environ["CONNECTIONS_TABLE"]))
else:
    table = None


def connect_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Handle WebSocket connect events"""
    connection_id = event["requestContext"]["connectionId"]

    # Calculate TTL (24 hours from now)
    ttl_timestamp = int(time.time() + (24 * 60 * 60))

    try:
        if not table:
            logger.error("CONNECTIONS_TABLE not configured")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Database not configured"}),
            }

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
    except ClientError as e:
        logger.exception(f"Error connecting: {e!s}")
        return {"statusCode": 500, "body": json.dumps({"message": "Failed to connect"})}


def disconnect_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Handle WebSocket disconnect events"""
    connection_id = event["requestContext"]["connectionId"]

    try:
        if not table:
            logger.error("CONNECTIONS_TABLE not configured")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Database not configured"}),
            }

        # Remove the connection record
        table.delete_item(Key={"connection_id": connection_id})

        return {"statusCode": 200, "body": json.dumps({"message": "Disconnected"})}
    except ClientError as e:
        logger.exception(f"Error disconnecting: {e!s}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to disconnect"}),
        }


def default_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Handle default WebSocket messages and update connection TTL"""
    connection_id = event["requestContext"]["connectionId"]

    try:
        if not table:
            logger.error("CONNECTIONS_TABLE not configured")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Database not configured"}),
            }

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
        logger.exception(f"Error in default handler: {e!s}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error"}),
        }


def cleanup_connections_handler(_event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handler for cleaning up stale WebSocket connections."""
    try:
        # Extract request ID from context
        request_id = context.aws_request_id
        logger.info(f"Processing cleanup request {request_id}")

        # Get the connections table
        connections_table = cast("Any", dynamodb.Table(os.environ["CONNECTIONS_TABLE"]))

        # Scan for all connections
        response = connections_table.scan()
        items = response.get("Items", [])

        # Continue scanning if we have more items
        while "LastEvaluatedKey" in response:
            response = connections_table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))

        # Delete each connection
        for item in items:
            connection_id = item["connection_id"]
            connections_table.delete_item(
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
