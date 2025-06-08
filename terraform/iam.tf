resource "aws_iam_role" "flexepos_lambda_role" {
  name               = "flexepos_lambda_${terraform.workspace}"
  path               = "/service-role/"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  tags               = local.common_tags
}

resource "aws_iam_policy" "accesssecrets" {
  name        = "accesssecrets"
  description = "access secrets manager for qb integration"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetRandomPassword",
                "secretsmanager:GetResourcePolicy",
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret",
                "secretsmanager:PutSecretValue",
                "secretsmanager:CreateSecret",
                "secretsmanager:ListSecretVersionIds"
            ],
            "Resource": "*"
        }
    ]
}
EOF
  tags   = local.common_tags
}

resource "aws_iam_policy" "accessssm" {
  name        = "accessssm"
  description = "access ssm parameter store"
  policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:DescribeParameters"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameters", "ssm:GetParameter"
            ],
            "Resource": "*"
        }
    ]
}
EOF
  tags        = local.common_tags
}

resource "aws_iam_policy" "sendemail" {
  name        = "sendemail"
  description = "send ses emails"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*"
        }
    ]
}
EOF
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "accesssecrets-attach" {
  role       = aws_iam_role.flexepos_lambda_role.name
  policy_arn = aws_iam_policy.accesssecrets.arn
}

resource "aws_iam_role_policy_attachment" "accessssm-attach" {
  role       = aws_iam_role.flexepos_lambda_role.name
  policy_arn = aws_iam_policy.accessssm.arn
}

resource "aws_iam_role_policy_attachment" "sendmemail-attach" {
  role       = aws_iam_role.flexepos_lambda_role.name
  policy_arn = aws_iam_policy.sendemail.arn
}

resource "aws_iam_role_policy_attachment" "lambda-basic" {
  role       = aws_iam_role.flexepos_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_permission" "flexepos_invoice_sync_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions["invoice_sync"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.flexepos_daily_3am.arn
}

resource "aws_lambda_permission" "flexepos_journal_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions["daily_journal"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.flexepos_daily.arn
}

resource "aws_lambda_permission" "flexepos_sales_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions["daily_sales"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.flexepos_daily.arn
}

resource "aws_lambda_permission" "flexepos_email_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions["email_tips"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.flexepos_daily_3am.arn
}

# Create IAM role for API Gateway CloudWatch logging
resource "aws_iam_role" "api_gateway_cloudwatch_role" {
  name = "api_gateway_cloudwatch_role_${terraform.workspace}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Create policy for API Gateway CloudWatch logging
resource "aws_iam_role_policy" "api_gateway_cloudwatch_policy" {
  name = "api_gateway_cloudwatch_policy_${terraform.workspace}"
  role = aws_iam_role.api_gateway_cloudwatch_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents",
          "logs:GetLogEvents",
          "logs:FilterLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*" # Broader permission to create and manage log groups
      }
    ]
  })
}

# Attach the AWS managed policy for API Gateway pushing logs to CloudWatch
resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# Enable CloudWatch logging for API Gateway account
resource "aws_api_gateway_account" "main" {
  depends_on = [
    aws_iam_role_policy.api_gateway_cloudwatch_policy,
    aws_iam_role_policy_attachment.api_gateway_cloudwatch
  ]
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch_role.arn
}

# Create policy for managing WebSocket connections
resource "aws_iam_policy" "manage_websocket_connections" {
  name        = "manage_websocket_connections_${terraform.workspace}"
  description = "Allow managing WebSocket connections"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "${aws_apigatewayv2_api.websocket.execution_arn}/*/@connections/*"
      }
    ]
  })

  tags = local.common_tags
}

# Create policy for invoking Lambda functions
resource "aws_iam_policy" "invoke_lambda_functions" {
  name        = "invoke_lambda_functions_${terraform.workspace}"
  description = "Allow invoking other Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:*:*:function:*-${terraform.workspace}"
      }
    ]
  })

  tags = local.common_tags
}

# Attach WebSocket management policy to Lambda role
resource "aws_iam_role_policy_attachment" "manage_websocket_connections_attach" {
  role       = aws_iam_role.flexepos_lambda_role.name
  policy_arn = aws_iam_policy.manage_websocket_connections.arn
}

# Attach Lambda invocation policy to Lambda role
resource "aws_iam_role_policy_attachment" "invoke_lambda_functions_attach" {
  role       = aws_iam_role.flexepos_lambda_role.name
  policy_arn = aws_iam_policy.invoke_lambda_functions.arn
}
