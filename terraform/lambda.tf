data "aws_ecr_repository" "wmc_ecr" {
  name = "wmc"
}

data "aws_ecr_image" "wmc_image" {
  repository_name = "wmc"
  most_recent     = true
}

data "aws_caller_identity" "current" {
  # Retrieves information about the AWS account corresponding to the
  # access key being used to run Terraform, which we need to populate
  # the "source_account" on the permission resource.
}

resource "aws_lambda_function" "authorizer" {
  function_name = "authorizer-${terraform.workspace}"
  description   = "[${terraform.workspace}] Validates MSAL tokens."

  role        = aws_iam_role.flexepos_lambda_role.arn
  filename    = "../deploy/validate_token.zip"
  handler     = "validate_token.lambda_handler"
  runtime     = "python3.12"
  timeout     = 30
  memory_size = 128

  source_code_hash = filebase64sha256("../deploy/validate_token.zip")

  environment {
    variables = local.lambda_env_authorizer
  }

  tags = local.common_tags
  logging_config {
    application_log_level = local.common_logging.application_log_level
    log_format            = local.common_logging.log_format
  }
}

locals {
  lambda_functions = {
    invoice_sync = {
      name        = "invoice-sync"
      description = "Syncs the last 30 days of invoices from CrunchTime into Quickbooks"
      handler     = "lambda_function.invoice_sync_handler"
      timeout     = 600
      memory      = 10240
      env_vars    = local.lambda_env_invoice_sync
    },
    daily_journal = {
      name        = "daily-journal"
      description = "Sends an email report on store operations"
      handler     = "lambda_function.daily_journal_handler"
      timeout     = 480
      memory      = 10240
      env_vars    = local.lambda_env_daily_journal
    }
    daily_sales = {
      name        = "daily-sales"
      description = "Enters daily sales for yesterday."
      handler     = "lambda_function.daily_sales_handler"
      timeout     = 480
      memory      = 10240
      env_vars    = local.lambda_env_daily_sales
    }
    email_tips = {
      name        = "email-tips"
      description = "Emails tips spreadsheet."
      handler     = "lambda_function.email_tips_handler"
      timeout     = 480
      memory      = 10240
      env_vars    = local.lambda_env_email_tips
    }
    transform_tips = {
      name        = "transform-tips"
      description = "Takes the excel tip spreadsheet and returns the Gusto CSV for import."
      handler     = "lambda_function.transform_tips_handler"
      timeout     = 480
      memory      = 10240
      env_vars    = local.lambda_env_transform_tips
    }
    get_mpvs = {
      name        = "get-mpvs"
      description = "Returns MPVs for a specific pay period or the whole month."
      handler     = "lambda_function.get_mpvs_handler"
      timeout     = 480
      memory      = 10240
      env_vars    = local.lambda_env_get_mpvs
    }
  }
}

resource "aws_lambda_function" "functions" {
  for_each      = local.lambda_functions
  function_name = "${each.value.name}-${terraform.workspace}"
  description   = "[${terraform.workspace}] ${each.value.description}"

  role         = aws_iam_role.flexepos_lambda_role.arn
  package_type = "Image"
  image_uri    = "${data.aws_ecr_repository.wmc_ecr.repository_url}@${data.aws_ecr_image.wmc_image.id}"

  image_config {
    command = [each.value.handler]
  }

  timeout     = each.value.timeout
  memory_size = each.value.memory

  environment {
    variables = each.value.env_vars
  }

  tags = local.common_tags
  logging_config {
    application_log_level = local.common_logging.application_log_level
    log_format            = local.common_logging.log_format
  }
}

resource "aws_lambda_permission" "apigw" {
  for_each      = aws_lambda_function.functions
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = each.value.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.josiah.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw-auth" {
  statement_id  = "AllowAPIGatewayInvoke-auth"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.josiah.execution_arn}/*/*"
}
