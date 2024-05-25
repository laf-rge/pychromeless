import re
import time
import jwt
import base64
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import json
from urllib.request import urlopen
from typing import Any, Dict, List, Optional, Union

class OAuth2TokenValidation:
    def __init__(self, tenant_id: str, client_id: str):
        self.jwks_url: str = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        self.issuer_url: str = f"https://sts.windows.net/{tenant_id}/"
        self.audience: str = f"api://{client_id}"

        self.jwks: Dict[str, Any] = json.loads(urlopen(self.jwks_url).read())
        self.last_jwks_public_key_update: float = time.time()

    def validate_token_and_decode_it(self, token: str) -> Dict[str, Any]:
        """
        Validate the JWT token and decode it.

        :param token: The JWT token to validate.
        :return: The decoded token if valid, else raises an exception.
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception as e:
            raise Exception(f"Unable to decode authorization token headers: {e}")

        try:
            rsa_key = self.find_rsa_key(self.jwks, unverified_header)
            public_key = self.rsa_pem_from_jwk(rsa_key)

            return jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer_url
            )
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
        except Exception as e:
            # Update the public key if not fresh and try again
            if int(time.time() - self.last_jwks_public_key_update) > 60:
                self.jwks = json.loads(urlopen(self.jwks_url).read())
                self.last_jwks_public_key_update = time.time()
                return self.validate_token_and_decode_it(token)
            else:
                raise Exception(f"Error validating token: {e}")

    @staticmethod
    def find_rsa_key(jwks: Dict[str, Any], unverified_header: Dict[str, Any]) -> Dict[str, str]:
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                return {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        raise Exception("RSA key not found")

    @staticmethod
    def ensure_bytes(key: Union[str, bytes]) -> bytes:
        if isinstance(key, str):
            key = key.encode('utf-8')
        return key

    @staticmethod
    def decode_value(val: Union[str, bytes]) -> int:
        decoded = base64.urlsafe_b64decode(OAuth2TokenValidation.ensure_bytes(val) + b'==')
        return int.from_bytes(decoded, 'big')

    @staticmethod
    def rsa_pem_from_jwk(jwk: Dict[str, str]) -> bytes:
        return RSAPublicNumbers(
            n=OAuth2TokenValidation.decode_value(jwk['n']),
            e=OAuth2TokenValidation.decode_value(jwk['e'])
        ).public_key(default_backend()).public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    print("Client token: " + event['authorizationToken'])
    print("Method ARN: " + event['methodArn'])

    oat = OAuth2TokenValidation('4d83363f-a694-437f-892e-3ee76d388743', '32483067-a12e-43ba-a194-a4a6e0a579b2')
    bearer = oat.validate_token_and_decode_it(event['authorizationToken'])

    principalId = bearer['oid']

    tmp = event['methodArn'].split(':')
    apiGatewayArnTmp = tmp[5].split('/')
    awsAccountId = tmp[4]

    policy = AuthPolicy(principalId, awsAccountId)
    policy.restApiId = apiGatewayArnTmp[0]
    policy.region = tmp[3]
    policy.stage = apiGatewayArnTmp[1]
    if bearer['scp'] == "WMCWeb.Josiah":
        policy.allowMethod(HttpVerb.ALL, '*')
    else:
        policy.denyAllMethods()

    authResponse = policy.build()

    context = {
        'key': 'value',  # $context.authorizer.key -> value
        'number': 1,
        'bool': True
    }

    authResponse['context'] = context

    return authResponse


class HttpVerb:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'
    ALL = '*'


class AuthPolicy:
    pathRegex = r'^[/.a-zA-Z0-9-*]+$'

    def __init__(self, principal: str, awsAccountId: str):
        self.awsAccountId = awsAccountId
        self.principalId = principal
        self.allowMethods: List[Dict[str, Any]] = []
        self.denyMethods: List[Dict[str, Any]] = []
        self.restApiId = "uu7jn6wcdh"
        self.region = "us-east-2"
        self.stage = "test"

    def _addMethod(self, effect: str, verb: str, resource: str, conditions: Optional[Dict[str, Any]] = None) -> None:
        if verb != '*' and not hasattr(HttpVerb, verb):
            raise NameError(f'Invalid HTTP verb {verb}. Allowed verbs in HttpVerb class')
        resourcePattern = re.compile(self.pathRegex)
        if not resourcePattern.match(resource):
            raise NameError(f'Invalid resource path: {resource}. Path should match {self.pathRegex}')

        if resource.startswith('/'):
            resource = resource[1:]

        resourceArn = f'arn:aws:execute-api:{self.region}:{self.awsAccountId}:{self.restApiId}/{self.stage}/{verb}/{resource}'

        if effect.lower() == 'allow':
            self.allowMethods.append({
                'resourceArn': resourceArn,
                'conditions': conditions
            })
        elif effect.lower() == 'deny':
            self.denyMethods.append({
                'resourceArn': resourceArn,
                'conditions': conditions
            })

    def _getEmptyStatement(self, effect: str) -> Dict[str, Any]:
        return {
            'Action': 'execute-api:Invoke',
            'Effect': effect.capitalize(),
            'Resource': []
        }

    def _getStatementForEffect(self, effect: str, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        statements = []

        if methods:
            statement = self._getEmptyStatement(effect)

            for curMethod in methods:
                if not curMethod['conditions']:
                    statement['Resource'].append(curMethod['resourceArn'])
                else:
                    conditionalStatement = self._getEmptyStatement(effect)
                    conditionalStatement['Resource'].append(curMethod['resourceArn'])
                    conditionalStatement['Condition'] = curMethod['conditions']
                    statements.append(conditionalStatement)

            if statement['Resource']:
                statements.append(statement)

        return statements

    def allowAllMethods(self) -> None:
        self._addMethod('Allow', HttpVerb.ALL, '*')

    def denyAllMethods(self) -> None:
        self._addMethod('Deny', HttpVerb.ALL, '*')

    def allowMethod(self, verb: str, resource: str) -> None:
        self._addMethod('Allow', verb, resource)

    def denyMethod(self, verb: str, resource: str) -> None:
        self._addMethod('Deny', verb, resource)

    def allowMethodWithConditions(self, verb: str, resource: str, conditions: Dict[str, Any]) -> None:
        self._addMethod('Allow', verb, resource, conditions)

    def denyMethodWithConditions(self, verb: str, resource: str, conditions: Dict[str, Any]) -> None:
        self._addMethod('Deny', verb, resource, conditions)

    def build(self) -> Dict[str, Any]:
        if not self.allowMethods and not self.denyMethods:
            raise NameError('No statements defined for the policy')

        policy = {
            'principalId': self.principalId,
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': []
            }
        }

        policy['policyDocument']['Statement'].extend(self._getStatementForEffect('Allow', self.allowMethods))
        policy['policyDocument']['Statement'].extend(self._getStatementForEffect('Deny', self.denyMethods))

        return policy
