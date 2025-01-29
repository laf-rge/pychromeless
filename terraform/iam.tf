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
