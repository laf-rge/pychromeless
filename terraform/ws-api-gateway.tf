# WebSocket API Gateway
resource "aws_apigatewayv2_api" "websocket" {
  name                       = "${local.common_tags.Name}-websocket-api"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
  tags                       = local.common_tags
}

# Create WebSocket-specific authorizer Lambda function
resource "aws_lambda_function" "ws_authorizer" {
  filename         = "../deploy/ws_validate_token.zip"
  function_name    = "ws-validate-token"
  role             = aws_iam_role.flexepos_lambda_role.arn
  handler          = "ws_validate_token.lambda_handler"
  runtime          = "python3.14"
  timeout          = 10
  source_code_hash = filebase64sha256("../deploy/ws_validate_token.zip")

  environment {
    variables = {
      TENANT_ID = "4d83363f-a694-437f-892e-3ee76d388743"
      CLIENT_ID = "32483067-a12e-43ba-a194-a4a6e0a579b2"
    }
  }
}

# Update WebSocket authorizer to use the new function
resource "aws_apigatewayv2_authorizer" "msal" {
  api_id           = aws_apigatewayv2_api.websocket.id
  authorizer_type  = "REQUEST"
  authorizer_uri   = aws_lambda_function.ws_authorizer.invoke_arn
  identity_sources = ["route.request.querystring.Authorization", "route.request.header.Origin"]
  name             = "msal-ws"
}

# Add permission for WebSocket API Gateway to invoke the new authorizer
resource "aws_lambda_permission" "ws_authorizer" {
  statement_id  = "AllowWebSocketAPIInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/authorizers/${aws_apigatewayv2_authorizer.msal.id}"
}

# WebSocket API Gateway Stage
resource "aws_apigatewayv2_stage" "websocket" {
  api_id      = aws_apigatewayv2_api.websocket.id
  name        = "production"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit   = 5000
    throttling_rate_limit    = 10000
    detailed_metrics_enabled = true
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.websocket_logs.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      ip               = "$context.identity.sourceIp"
      requestTime      = "$context.requestTime"
      routeKey         = "$context.routeKey"
      status           = "$context.status"
      connectionId     = "$context.connectionId"
      errorMessage     = "$context.error.message"
      integrationError = "$context.integration.error"
      origin           = "$context.identity.origin"
      userAgent        = "$context.identity.userAgent"
    })
  }
}

# CloudWatch Log Group for WebSocket API Gateway
resource "aws_cloudwatch_log_group" "websocket_logs" {
  name              = "/aws/apigateway/${aws_apigatewayv2_api.websocket.name}"
  retention_in_days = 30
  tags              = local.common_tags
}

# WebSocket API Gateway Routes
resource "aws_apigatewayv2_route" "connect" {
  api_id             = aws_apigatewayv2_api.websocket.id
  route_key          = "$connect"
  target             = "integrations/${aws_apigatewayv2_integration.connect.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.msal.id
}

# Add route response for $connect
resource "aws_apigatewayv2_route_response" "connect" {
  api_id             = aws_apigatewayv2_api.websocket.id
  route_id           = aws_apigatewayv2_route.connect.id
  route_response_key = "$default"
}

resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.disconnect.id}"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.default.id}"
}

# WebSocket API Gateway Integrations
resource "aws_apigatewayv2_integration" "connect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.ws_functions["connect"].invoke_arn

  request_parameters = {
    "integration.request.header.Origin" = "context.identity.origin"
  }
}

# Add integration response for connect
resource "aws_apigatewayv2_integration_response" "connect" {
  api_id                   = aws_apigatewayv2_api.websocket.id
  integration_id           = aws_apigatewayv2_integration.connect.id
  integration_response_key = "/200/"
}

resource "aws_apigatewayv2_integration" "disconnect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.ws_functions["disconnect"].invoke_arn
}

resource "aws_apigatewayv2_integration" "default" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.ws_functions["default"].invoke_arn
}

output "ws_base_url" {
  value = aws_apigatewayv2_stage.websocket.invoke_url
}
