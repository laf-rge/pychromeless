import logging
from typing import Any

from auth_utils import OAuth2TokenValidation, extract_token

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """
    WebSocket API Gateway authorizer that validates MSAL tokens.
    """
    try:
        logger.info(f"Event: {event}")

        token = extract_token(event, "websocket")
        logger.info("Token extracted successfully")

        oat = OAuth2TokenValidation(
            "4d83363f-a694-437f-892e-3ee76d388743",
            "32483067-a12e-43ba-a194-a4a6e0a579b2",
        )
        bearer = oat.validate_token_and_decode_it(token)
        logger.info("Token validated successfully")

        principalId = bearer["oid"]

        # Parse WebSocket API Gateway ARN format
        tmp = event["methodArn"].split(":")
        apiGatewayArnTmp = tmp[5].split("/")
        awsAccountId = tmp[4]

        # Generate policy
        policy = {
            "principalId": principalId,
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": (
                            "Allow" if bearer["scp"] == "WMCWeb.Josiah" else "Deny"
                        ),
                        "Resource": [
                            # Allow/deny access to all routes if authorized
                            f"arn:aws:execute-api:{tmp[3]}:{awsAccountId}:{apiGatewayArnTmp[0]}/{apiGatewayArnTmp[1]}/*"
                        ],
                    }
                ],
            },
            "context": {
                "principalId": principalId,
                "scope": bearer["scp"],
            },
        }
        logger.info("Policy generated successfully")
        return policy
    except Exception as e:
        logger.error(f"Error in WebSocket authorizer: {str(e)}", exc_info=True)
        raise
