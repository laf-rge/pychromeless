resource "aws_cloudwatch_event_rule" "flexepos_daily" {
  name                = "flexepos-daily-${terraform.workspace}"
  description         = "Trigger ${terraform.workspace} actions"
  schedule_expression = "cron(0 13 * * ? *)" # 6 AM PST
  depends_on          = [aws_lambda_function.functions["invoice_sync"]]
}

resource "aws_cloudwatch_event_rule" "flexepos_daily_3am" {
  name                = "flexepos-daily-3am-${terraform.workspace}"
  description         = "Trigger ${terraform.workspace} actions"
  schedule_expression = "cron(0 10 * * ? *)" # 3 AM PST
  depends_on          = [aws_lambda_function.functions["invoice_sync"]]
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "invoke_invoice_sync" {
  target_id = "invoice_sync_daily"
  rule      = aws_cloudwatch_event_rule.flexepos_daily_3am.name
  arn       = aws_lambda_function.functions["invoice_sync"].arn
}

resource "aws_cloudwatch_event_target" "invoke_journal_sync" {
  target_id = "journal_sync_daily"
  rule      = aws_cloudwatch_event_rule.flexepos_daily.name
  arn       = aws_lambda_function.functions["daily_journal"].arn
}

resource "aws_cloudwatch_event_target" "invoke_sales_sync" {
  target_id = "sales_sync_daily"
  rule      = aws_cloudwatch_event_rule.flexepos_daily.name
  arn       = aws_lambda_function.functions["daily_sales"].arn
}

# Timeout detector - runs every 5 minutes to mark stale tasks as failed
resource "aws_cloudwatch_event_rule" "timeout_detector" {
  name                = "timeout-detector-${terraform.workspace}"
  description         = "Run timeout detector every 5 minutes"
  schedule_expression = "rate(5 minutes)"
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "invoke_timeout_detector" {
  target_id = "timeout_detector"
  rule      = aws_cloudwatch_event_rule.timeout_detector.name
  arn       = aws_lambda_function.functions["timeout_detector"].arn
}

resource "aws_lambda_permission" "allow_cloudwatch_timeout_detector" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions["timeout_detector"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.timeout_detector.arn
}
