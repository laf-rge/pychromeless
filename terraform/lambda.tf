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
}

resource "aws_lambda_function" "invoice_sync" {
  function_name = "invoice-sync-${terraform.workspace}"
  description   = "[${terraform.workspace}] Syncs the last 30 days of invoices from CrunchTime into Quickbooks"

  role         = aws_iam_role.flexepos_lambda_role.arn
  package_type = "Image"
  image_uri    = "${data.aws_ecr_repository.wmc_ecr.repository_url}@${data.aws_ecr_image.wmc_image.id}"
  image_config {
    command = ["lambda_function.invoice_sync_handler"]
  }
  timeout     = 480
  memory_size = 10240

  environment {
    variables = local.lambda_env_invoice_sync
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "daily_journal" {
  function_name = "daily-journal-${terraform.workspace}"
  description   = "[${terraform.workspace}] Sends an email report on store operations."

  role         = aws_iam_role.flexepos_lambda_role.arn
  package_type = "Image"
  image_uri    = "${data.aws_ecr_repository.wmc_ecr.repository_url}@${data.aws_ecr_image.wmc_image.id}"
  image_config {
    command = ["lambda_function.daily_journal_handler"]
  }
  timeout     = 480
  memory_size = 10240

  environment {
    variables = local.lambda_env_daily_journal
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "daily_sales" {
  function_name = "daily-sales-${terraform.workspace}"
  description   = "[${terraform.workspace}] Enters daily sales for yesterday."

  role         = aws_iam_role.flexepos_lambda_role.arn
  package_type = "Image"
  image_uri    = "${data.aws_ecr_repository.wmc_ecr.repository_url}@${data.aws_ecr_image.wmc_image.id}"
  image_config {
    command = ["lambda_function.daily_sales_handler"]
  }
  timeout     = 480
  memory_size = 10240

  environment {
    variables = local.lambda_env_daily_sales
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "email_tips" {
  function_name = "email-tips-${terraform.workspace}"
  description   = "[${terraform.workspace}] Emails tips spreadsheet."

  role         = aws_iam_role.flexepos_lambda_role.arn
  package_type = "Image"
  image_uri    = "${data.aws_ecr_repository.wmc_ecr.repository_url}@${data.aws_ecr_image.wmc_image.id}"
  image_config {
    command = ["lambda_function.email_tips_handler"]
  }
  timeout     = 480
  memory_size = 10240

  environment {
    variables = local.lambda_env_email_tips
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "transform_tips" {
  function_name = "transform_tips-${terraform.workspace}"
  description   = "[${terraform.workspace}] Takes the excel tip spreadsheet and returns the Gusto CSV for import."

  role         = aws_iam_role.flexepos_lambda_role.arn
  package_type = "Image"
  image_uri    = "${data.aws_ecr_repository.wmc_ecr.repository_url}@${data.aws_ecr_image.wmc_image.id}"
  image_config {
    command = ["lambda_function.transform_tips_handler"]
  }
  timeout     = 480
  memory_size = 10240

  environment {
    variables = local.lambda_env_transform_tips
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "get_mpvs" {
  function_name = "get-mpvs-${terraform.workspace}"
  description   = "[${terraform.workspace}] Returns MPVs for a specific pay period or the whole month."

  role         = aws_iam_role.flexepos_lambda_role.arn
  package_type = "Image"
  image_uri    = "${data.aws_ecr_repository.wmc_ecr.repository_url}@${data.aws_ecr_image.wmc_image.id}"
  image_config {
    command = ["lambda_function.get_mpvs_handler"]
  }
  timeout     = 480
  memory_size = 10240

  environment {
    variables = local.lambda_env_get_mpvs
  }

  tags = local.common_tags
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.daily_sales.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.josiah.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw-tips" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.email_tips.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.josiah.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw-transform-tips" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transform_tips.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.josiah.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw-mpvs" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_mpvs.function_name
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
