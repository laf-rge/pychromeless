# DynamoDB table for WebSocket connections
resource "aws_dynamodb_table" "websocket_connections" {
  name             = "${local.common_tags.Name}-websocket-connections"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "connection_id"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "connection_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = local.common_tags
}

# DynamoDB table for task states
resource "aws_dynamodb_table" "task_states" {
  name         = "${local.common_tags.Name}-task-states"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "task_id"
  range_key    = "timestamp"

  attribute {
    name = "task_id"
    type = "S"
  }

  attribute {
    name = "operation"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  global_secondary_index {
    name            = "operation_type-index"
    hash_key        = "operation"
    range_key       = "timestamp"
    projection_type = "ALL"
    write_capacity  = 5
    read_capacity   = 5
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = local.common_tags
}

# IAM policy for DynamoDB access
resource "aws_iam_policy" "dynamodb_access" {
  name        = "${local.common_tags.Name}-dynamodb-access"
  description = "IAM policy for DynamoDB access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.websocket_connections.arn,
          aws_dynamodb_table.task_states.arn,
          "${aws_dynamodb_table.task_states.arn}/index/operation_type-index",
          aws_dynamodb_table.daily_sales_progress.arn
        ]
      }
    ]
  })
}

# DynamoDB table for daily sales progress tracking
resource "aws_dynamodb_table" "daily_sales_progress" {
  name         = "${local.common_tags.Name}-daily-sales-progress"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = local.common_tags
}

# Attach DynamoDB access policy to Lambda role
resource "aws_iam_role_policy_attachment" "dynamodb_access_attach" {
  role       = aws_iam_role.flexepos_lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}
