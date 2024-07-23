# Connect Lambda Function
resource "aws_lambda_function" "connect" {
  function_name = "${local.common_tags.Name}-connect"
  description   = "[${terraform.workspace}] Handles WebSocket connect events"

  role             = aws_iam_role.flexepos_lambda_role.arn
  filename         = "../deploy/websocket.zip"
  handler          = "lambda_function.connect_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128
  source_code_hash = filebase64sha256("../deploy/websocket.zip")

  environment {
    variables = local.lambda_env_websocket
  }

  tags = local.common_tags
}

# Disconnect Lambda Function
resource "aws_lambda_function" "disconnect" {
  function_name = "${local.common_tags.Name}-disconnect"
  description   = "[${terraform.workspace}] Handles WebSocket disconnect events"

  role             = aws_iam_role.flexepos_lambda_role.arn
  filename         = "../deploy/websocket.zip"
  handler          = "lambda_function.disconnect_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128
  source_code_hash = filebase64sha256("../deploy/websocket.zip")

  environment {
    variables = local.lambda_env_websocket
  }

  tags = local.common_tags
}

# Default Lambda Function
resource "aws_lambda_function" "default" {
  function_name = "${local.common_tags.Name}-default"
  description   = "[${terraform.workspace}] Handles default WebSocket events"

  role             = aws_iam_role.flexepos_lambda_role.arn
  filename         = "../deploy/websocket.zip"
  handler          = "lambda_function.default_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128
  source_code_hash = filebase64sha256("../deploy/websocket.zip")

  environment {
    variables = local.lambda_env_websocket
  }

  tags = local.common_tags
}

# Reuse existing Lambda permissions
resource "aws_lambda_permission" "connect_ws" {
  statement_id  = "AllowExecutionFromAPIGatewayConnectWS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.connect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

resource "aws_lambda_permission" "disconnect_ws" {
  statement_id  = "AllowExecutionFromAPIGatewayDisconnectWS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.disconnect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

resource "aws_lambda_permission" "default_ws" {
  statement_id  = "AllowExecutionFromAPIGatewayDefalutWS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.default.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

# Lambda permission for the custom authorizer
resource "aws_lambda_permission" "api_gateway_custom_authorizer" {
  statement_id  = "AllowAPIGatewayInvokeCustomAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/authorizers/${aws_apigatewayv2_authorizer.msal.id}"
}
resource "aws_lambda_permission" "ws-apigw-auth" {
  statement_id  = "AllowAPIGatewayInvoke-ws"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}
