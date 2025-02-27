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
        Resource = aws_dynamodb_table.websocket_connections.arn
      }
    ]
  })
}

# Attach DynamoDB access policy to Lambda role
resource "aws_iam_role_policy_attachment" "dynamodb_access_attach" {
  role       = aws_iam_role.flexepos_lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}
