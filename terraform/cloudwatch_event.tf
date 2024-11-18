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
