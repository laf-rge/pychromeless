locals {
  monitored_functions = toset([
    "daily-sales-${terraform.workspace}",
    "email-tips-${terraform.workspace}",
    "invoice-sync-${terraform.workspace}",
    "daily-journal-${terraform.workspace}",
    "transform-tips-${terraform.workspace}",
    "get-mpvs-${terraform.workspace}"
  ])
  function_timeouts = {
    for k, v in local.lambda_functions : "${v.name}-${terraform.workspace}" => v.timeout
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = local.monitored_functions

  alarm_name          = "${each.key}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors ${each.key} lambda function errors"

  dimensions = {
    FunctionName = each.key
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
  tags          = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = local.monitored_functions

  alarm_name          = "${each.key}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Maximum"
  threshold           = local.function_timeouts[each.key] * 900 # 90% of timeout in milliseconds
  alarm_description   = "Alert when ${each.key} lambda function is approaching timeout"

  dimensions = {
    FunctionName = each.key
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
  tags          = local.common_tags
}

resource "aws_sns_topic" "lambda_alerts" {
  name = "lambda-monitoring-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.lambda_alerts.arn
  protocol  = "email"
  endpoint  = "william@wagonermanagement.com"
}

/*resource "aws_cloudwatch_metric_alarm" "lambda_500_errors" {
  for_each = local.monitored_functions

  alarm_name          = "${each.key}-500-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors ${each.key} for HTTP 500 errors"

  dimensions = {
    ApiName      = "${each.key}-api"
    FunctionName = each.key
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
}
*/
