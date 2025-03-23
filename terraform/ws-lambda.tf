locals {
  ws_lambda_functions = {
    connect = {
      name        = "connect"
      description = "Handles WebSocket connect events"
      handler     = "lambda_function.connect_handler"
      timeout     = 30
      memory      = 128
      env_vars = merge(local.lambda_env_websocket, {
        CONNECTIONS_TABLE = aws_dynamodb_table.websocket_connections.name
      })
    },
    disconnect = {
      name        = "disconnect"
      description = "Handles WebSocket disconnect events"
      handler     = "lambda_function.disconnect_handler"
      timeout     = 30
      memory      = 128
      env_vars = merge(local.lambda_env_websocket, {
        CONNECTIONS_TABLE = aws_dynamodb_table.websocket_connections.name
      })
    },
    default = {
      name        = "default"
      description = "Handles default WebSocket events"
      handler     = "lambda_function.default_handler"
      timeout     = 30
      memory      = 128
      env_vars = merge(local.lambda_env_websocket, {
        CONNECTIONS_TABLE = aws_dynamodb_table.websocket_connections.name
      })
    },
    cleanup_connections = {
      name        = "cleanup-connections"
      description = "Cleanup stale WebSocket connections"
      handler     = "lambda_function.cleanup_connections_handler"
      timeout     = 60
      memory      = 128
      env_vars = merge(local.lambda_env_websocket, {
        CONNECTIONS_TABLE = aws_dynamodb_table.websocket_connections.name
      })
    }
  }
}

# WebSocket Lambda Functions
resource "aws_lambda_function" "ws_functions" {
  for_each      = local.ws_lambda_functions
  function_name = "${each.value.name}-${terraform.workspace}"
  description   = "[${terraform.workspace}] ${each.value.description}"

  role             = aws_iam_role.flexepos_lambda_role.arn
  filename         = "../deploy/websocket.zip"
  handler          = each.value.handler
  runtime          = "python3.13"
  timeout          = each.value.timeout
  memory_size      = each.value.memory
  source_code_hash = filebase64sha256("../deploy/websocket.zip")

  environment {
    variables = each.value.env_vars
  }

  tags = local.common_tags
  logging_config {
    application_log_level = local.common_logging.application_log_level
    log_format            = local.common_logging.log_format
  }
}

# Lambda permissions for WebSocket API Gateway
resource "aws_lambda_permission" "ws_functions" {
  for_each      = aws_lambda_function.ws_functions
  statement_id  = "AllowExecutionFromAPIGatewayWS"
  action        = "lambda:InvokeFunction"
  function_name = each.value.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

# CloudWatch Event Rule for cleanup
resource "aws_cloudwatch_event_rule" "cleanup_connections" {
  name                = "${local.common_tags.Name}-cleanup-connections"
  description         = "Trigger WebSocket connections cleanup"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "cleanup_connections" {
  rule      = aws_cloudwatch_event_rule.cleanup_connections.name
  target_id = "CleanupConnections"
  arn       = aws_lambda_function.ws_functions["cleanup_connections"].arn
}

resource "aws_lambda_permission" "cleanup_connections" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_functions["cleanup_connections"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cleanup_connections.arn
}
