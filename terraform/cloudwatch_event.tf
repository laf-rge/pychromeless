resource "aws_cloudwatch_event_rule" "flexepos_daily" {
  name                = "flexepos-daily-${terraform.workspace}"
  description         = "Trigger ${terraform.workspace} actions"
  schedule_expression = "cron(0 13 * * ? *)"
  depends_on          = [aws_lambda_function.invoice_sync]
}

resource "aws_cloudwatch_event_target" "invoke_invoice_sync" {
  target_id = "invoice_sync_daily"
  rule      = aws_cloudwatch_event_rule.flexepos_daily.name
  arn       = aws_lambda_function.invoice_sync.arn
}

resource "aws_cloudwatch_event_target" "invoke_journal_sync" {
  target_id = "journal_sync_daily"
  rule      = aws_cloudwatch_event_rule.flexepos_daily.name
  arn       = aws_lambda_function.daily_journal.arn
}

resource "aws_cloudwatch_event_target" "invoke_sales_sync" {
  target_id = "sales_sync_daily"
  rule      = aws_cloudwatch_event_rule.flexepos_daily.name
  arn       = aws_lambda_function.daily_sales.arn
}
