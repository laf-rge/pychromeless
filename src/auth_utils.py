import base64
import json
import logging
import re
import time
from typing import Any
from urllib.request import urlopen

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

logger = logging.getLogger(__name__)


# Custom exceptions for authentication and token validation
class TokenValidationError(Exception):
    """Base exception for token validation errors."""

    pass


class TokenDecodeError(TokenValidationError):
    """Raised when unable to decode token headers."""

    pass


class TokenExpiredError(TokenValidationError):
    """Raised when the token has expired."""

    pass


class InvalidTokenError(TokenValidationError):
    """Raised when the token is invalid."""

    pass


class RSAKeyNotFoundError(TokenValidationError):
    """Raised when the RSA key is not found in JWKS."""

    pass


class AuthorizationError(Exception):
    """Raised when authorization token is missing or invalid."""

    pass


class OAuth2TokenValidation:
    def __init__(self, tenant_id: str, client_id: str):
        self.jwks_url: str = (
            f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        )
        self.issuer_url: str = f"https://sts.windows.net/{tenant_id}/"
        self.audience: str = f"api://{client_id}"

        self.jwks: dict[str, Any] = json.loads(urlopen(self.jwks_url).read())
        self.last_jwks_public_key_update: float = time.time()

    def validate_token_and_decode_it(self, token: str) -> dict[str, Any]:
        """
        Validate the JWT token and decode it.

        :param token: The JWT token to validate.
        :return: The decoded token if valid, else raises an exception.
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception as e:
            raise TokenDecodeError(f"Unable to decode authorization token headers: {e}") from e

        try:
            rsa_key = self.find_rsa_key(self.jwks, unverified_header)
            public_key = self.rsa_pem_from_jwk(rsa_key)

            result: dict[str, Any] = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer_url,
            )
            return result
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError("Token has expired") from e
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError("Invalid token") from e
        except Exception as e:
            # Update the public key if not fresh and try again
            if int(time.time() - self.last_jwks_public_key_update) > 60:
                self.jwks = json.loads(urlopen(self.jwks_url).read())
                self.last_jwks_public_key_update = time.time()
                return self.validate_token_and_decode_it(token)
            else:
                raise TokenValidationError(f"Error validating token: {e}") from e

    @staticmethod
    def find_rsa_key(
        jwks: dict[str, Any], unverified_header: dict[str, Any]
    ) -> dict[str, str]:
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                return {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        raise RSAKeyNotFoundError("RSA key not found")

    @staticmethod
    def ensure_bytes(key: str | bytes) -> bytes:
        if isinstance(key, str):
            key = key.encode("utf-8")
        return key

    @staticmethod
    def decode_value(val: str | bytes) -> int:
        decoded = base64.urlsafe_b64decode(
            OAuth2TokenValidation.ensure_bytes(val) + b"=="
        )
        return int.from_bytes(decoded, "big")

    @staticmethod
    def rsa_pem_from_jwk(jwk: dict[str, str]) -> bytes:
        return (
            RSAPublicNumbers(
                n=OAuth2TokenValidation.decode_value(jwk["n"]),
                e=OAuth2TokenValidation.decode_value(jwk["e"]),
            )
            .public_key(default_backend())
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )


class AuthPolicy:
    """Generates IAM auth policy for API Gateway"""

    pathRegex = r"^[/.a-zA-Z0-9-*]+$"

    def __init__(self, principal: str, awsAccountId: str):
        self.awsAccountId = awsAccountId
        self.principalId = principal
        self.allowMethods: list[dict[str, Any]] = []
        self.denyMethods: list[dict[str, Any]] = []
        self.restApiId = "uu7jn6wcdh"
        self.region = "us-east-2"
        self.stage = "test"

    def _addMethod(
        self,
        effect: str,
        verb: str,
        resource: str,
        conditions: dict[str, Any] | None = None,
    ) -> None:
        if verb != "*" and not hasattr(HttpVerb, verb):
            raise NameError(
                f"Invalid HTTP verb {verb}. Allowed verbs in HttpVerb class"
            )
        resourcePattern = re.compile(self.pathRegex)
        if not resourcePattern.match(resource):
            raise NameError(
                f"Invalid resource path: {resource}. Path should match {self.pathRegex}"
            )

        if resource.startswith("/"):
            resource = resource[1:]

        resourceArn = f"arn:aws:execute-api:{self.region}:{self.awsAccountId}:{self.restApiId}/{self.stage}/{verb}/{resource}"

        if effect.lower() == "allow":
            self.allowMethods.append(
                {"resourceArn": resourceArn, "conditions": conditions}
            )
        elif effect.lower() == "deny":
            self.denyMethods.append(
                {"resourceArn": resourceArn, "conditions": conditions}
            )

    def _getEmptyStatement(self, effect: str) -> dict[str, Any]:
        return {
            "Action": "execute-api:Invoke",
            "Effect": effect.capitalize(),
            "Resource": [],
        }

    def _getStatementForEffect(
        self, effect: str, methods: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        statements = []

        if methods:
            statement = self._getEmptyStatement(effect)

            for curMethod in methods:
                if not curMethod["conditions"]:
                    statement["Resource"].append(curMethod["resourceArn"])
                else:
                    conditionalStatement = self._getEmptyStatement(effect)
                    conditionalStatement["Resource"].append(curMethod["resourceArn"])
                    conditionalStatement["Condition"] = curMethod["conditions"]
                    statements.append(conditionalStatement)

            if statement["Resource"]:
                statements.append(statement)

        return statements

    def allowAllMethods(self) -> None:
        self._addMethod("Allow", HttpVerb.ALL, "*")

    def denyAllMethods(self) -> None:
        self._addMethod("Deny", HttpVerb.ALL, "*")

    def allowMethod(self, verb: str, resource: str) -> None:
        self._addMethod("Allow", verb, resource)

    def denyMethod(self, verb: str, resource: str) -> None:
        self._addMethod("Deny", verb, resource)

    def allowMethodWithConditions(
        self, verb: str, resource: str, conditions: dict[str, Any]
    ) -> None:
        self._addMethod("Allow", verb, resource, conditions)

    def denyMethodWithConditions(
        self, verb: str, resource: str, conditions: dict[str, Any]
    ) -> None:
        self._addMethod("Deny", verb, resource, conditions)

    def build(self) -> dict[str, Any]:
        if not self.allowMethods and not self.denyMethods:
            raise NameError("No statements defined for the policy")

        statements: list[dict[str, Any]] = []
        statements.extend(self._getStatementForEffect("Allow", self.allowMethods))
        statements.extend(self._getStatementForEffect("Deny", self.denyMethods))

        policy: dict[str, Any] = {
            "principalId": self.principalId,
            "policyDocument": {"Version": "2012-10-17", "Statement": statements},
        }

        return policy


class HttpVerb:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    HEAD = "HEAD"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    ALL = "*"


def extract_token(event: dict[str, Any], source: str) -> str:
    """
    Extract Bearer token from event based on source.

    :param event: Lambda event
    :param source: Either 'rest' or 'websocket'
    :return: The token without 'Bearer ' prefix
    :raises: Exception if token is missing or invalid
    """
    if source == "rest":
        auth_param = event.get("authorizationToken", "")
        if not auth_param:
            raise AuthorizationError("No Authorization token found in authorizationToken")
    elif source == "websocket":
        auth_param = event.get("queryStringParameters", {}).get("Authorization", "")
        if not auth_param:
            raise AuthorizationError("No Authorization token found in query parameters")
    else:
        raise ValueError("Invalid source. Must be 'rest' or 'websocket'")

    if not auth_param.startswith("Bearer "):
        raise AuthorizationError("Invalid Authorization format. Must start with 'Bearer '")

    token: str = auth_param[7:]  # Remove "Bearer " prefix
    return token
