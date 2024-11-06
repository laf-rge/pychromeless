locals {
  monitored_functions = toset([
    "daily-sales",
    "email-tips",
    "third-party-deposit",
    "invoice-sync",
    "daily_journal",
    "transform_tips",
    "get_mpvs"
  ])
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
  threshold           = "270000" # 270 seconds (90% of 5 minute timeout)
  alarm_description   = "Alert when ${each.key} lambda function is approaching timeout"

  dimensions = {
    FunctionName = each.key
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
}

resource "aws_sns_topic" "lambda_alerts" {
  name = "lambda-monitoring-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.lambda_alerts.arn
  protocol  = "email"
  endpoint  = "william@wagonermanagement.com"
}

resource "aws_cloudwatch_metric_alarm" "lambda_500_errors" {
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
