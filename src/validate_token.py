import logging
from typing import Any

from auth_utils import AuthPolicy, HttpVerb, OAuth2TokenValidation, extract_token

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    REST API Gateway authorizer that validates MSAL tokens.
    """
    logger.info(f"Event: {event}")

    token = extract_token(event, "rest")

    oat = OAuth2TokenValidation(
        "4d83363f-a694-437f-892e-3ee76d388743", "32483067-a12e-43ba-a194-a4a6e0a579b2"
    )
    bearer = oat.validate_token_and_decode_it(token)

    principalId = bearer["oid"]

    tmp = event["methodArn"].split(":")
    apiGatewayArnTmp = tmp[5].split("/")
    awsAccountId = tmp[4]

    policy = AuthPolicy(principalId, awsAccountId)
    policy.restApiId = apiGatewayArnTmp[0]
    policy.region = tmp[3]
    policy.stage = apiGatewayArnTmp[1]
    if bearer["scp"] == "WMCWeb.Josiah":
        policy.allowAllMethods()
    else:
        policy.denyAllMethods()

    authResponse = policy.build()

    context = {
        "key": "value",  # $context.authorizer.key -> value
        "number": 1,
        "bool": True,
    }

    authResponse["context"] = context

    result: dict[str, Any] = authResponse
    return result
