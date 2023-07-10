data "aws_ecr_image" "wmc_image" {
  repository_name = "wmc"
  most_recent       = true
}

data "aws_caller_identity" "current" {
  # Retrieves information about the AWS account corresponding to the
  # access key being used to run Terraform, which we need to populate
  # the "source_account" on the permission resource.
}

resource "aws_lambda_function" "invoice_sync" {
  function_name = "invoice-sync-${terraform.workspace}"
  description   = "[${terraform.workspace}] Syncs the last 30 days of invoices from CrunchTime into Quickbooks"

  role             = aws_iam_role.flexepos_lambda_role.arn
  package_type     = "Image"
  image_uri        = "262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc@${data.aws_ecr_image.wmc_image.id}"
  image_config {
    command = ["lambda_function.invoice_sync_handler"]
  }
  timeout          = 480
  memory_size      = 960

  environment {
    variables = local.lambda_env_invoice_sync
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "daily_journal" {
  function_name = "daily-journal-${terraform.workspace}"
  description   = "[${terraform.workspace}] Sends an email report on store operations."

  role             = aws_iam_role.flexepos_lambda_role.arn
  package_type     = "Image"
  image_uri        = "262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest"
  image_config {
    command = ["lambda_function.daily_journal_handler"]
  }
  timeout          = 480
  memory_size      = 960

  environment {
    variables = local.lambda_env_daily_journal
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "daily_sales" {
  function_name = "daily-sales-${terraform.workspace}"
  description   = "[${terraform.workspace}] Enters daily sales for yesterday."

  role             = aws_iam_role.flexepos_lambda_role.arn
  package_type     = "Image"
  image_uri        = "262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest"
  image_config {
    command = ["lambda_function.daily_sales_handler"]
  }
  timeout          = 480
  memory_size      = 960

  environment {
    variables = local.lambda_env_daily_sales
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "email_tips" {
  function_name = "email-tips-${terraform.workspace}"
  description   = "[${terraform.workspace}] Emails tips spreadsheet."

  role             = aws_iam_role.flexepos_lambda_role.arn
  package_type     = "Image"
  image_uri        = "262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest"
  image_config {
    command = ["lambda_function.email_tips_handler"]
  }
  timeout          = 480
  memory_size      = 960

  environment {
    variables = local.lambda_env_email_tips
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "transform_tips" {
  function_name = "transform_tips-${terraform.workspace}"
  description   = "[${terraform.workspace}] Takes the excel tip spreadsheet and returns the Gusto CSV for import."

  role             = aws_iam_role.flexepos_lambda_role.arn
  package_type     = "Image"
  image_uri        = "262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest"
  image_config {
    command = ["lambda_function.transform_tips_handler"]
  }
  timeout          = 480
  memory_size      = 960

  environment {
    variables = local.lambda_env_transform_tips
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "get_mpvs" {
  function_name = "get-mpvs-${terraform.workspace}"
  description   = "[${terraform.workspace}] Returns MPVs for a specific pay period or the whole month."

  role             = aws_iam_role.flexepos_lambda_role.arn
  package_type     = "Image"
  image_uri        = "262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest"
  image_config {
    command = ["lambda_function.get_mpvs_handler"]
  }
  timeout          = 480
  memory_size      = 960

  environment {
    variables = local.lambda_env_get_mpvs
  }

  tags = local.common_tags
}

resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
  request_parameters = {
    "method.request.querystring.day"   = true,
    "method.request.querystring.month" = true,
    "method.request.querystring.year"  = true
  }
  request_validator_id = "unx39u"
}

resource "aws_api_gateway_integration" "lambda_root" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_root.resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method

  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = aws_lambda_function.daily_sales.invoke_arn
  content_handling        = "CONVERT_TO_TEXT"
  request_parameters = {
    "integration.request.header.X-Amz-Invocation-Type" = "'Event'",
    "integration.request.querystring.day"              = "method.request.querystring.day",
    "integration.request.querystring.month"            = "method.request.querystring.month",
    "integration.request.querystring.year"             = "method.request.querystring.year"
  }
  request_templates = {
    "application/json" = <<-EOT
                #set($inputRoot = $input.path('$'))
                {
                "year": "$input.params('year')",
                "month": "$input.params('month')",
                "day": "$input.params('day')"
                }
            EOT
  }
}

resource "aws_api_gateway_method_response" "root_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "lambda_root_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method = aws_api_gateway_integration.lambda_root.http_method
  status_code = aws_api_gateway_method_response.root_method_response_200.status_code
  response_templates = {
    "application/json" = jsonencode({
      body = "Josiah is on it!"
    })
  }
}

resource "aws_api_gateway_resource" "email_tips_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "email_tips"
}

resource "aws_api_gateway_method" "proxy_email_tips" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.email_tips_resource.id
  http_method   = "ANY"
  authorization = "NONE"
  request_parameters = {
    "method.request.querystring.day"   = true,
    "method.request.querystring.month" = true,
    "method.request.querystring.year"  = true
  }
  request_validator_id = "unx39u"
}

resource "aws_api_gateway_integration" "lambda_email_tips" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_email_tips.resource_id
  http_method = aws_api_gateway_method.proxy_email_tips.http_method

  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = aws_lambda_function.email_tips.invoke_arn
  content_handling        = "CONVERT_TO_TEXT"
  request_parameters = {
    "integration.request.header.X-Amz-Invocation-Type" = "'Event'",
    "integration.request.querystring.day"              = "method.request.querystring.day",
    "integration.request.querystring.month"            = "method.request.querystring.month",
    "integration.request.querystring.year"             = "method.request.querystring.year"
  }
  request_templates = {
    "application/json" = <<-EOT
                #set($inputRoot = $input.path('$'))
                {
                "year": "$input.params('year')",
                "month": "$input.params('month')",
                "day": "$input.params('day')"
                }
            EOT
  }
}

resource "aws_api_gateway_method_response" "email_tips_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id
  http_method = aws_api_gateway_method.proxy_email_tips.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "lambda_email_tips_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id
  http_method = aws_api_gateway_integration.lambda_email_tips.http_method
  status_code = aws_api_gateway_method_response.email_tips_method_response_200.status_code
  response_templates = {
    "application/json" = jsonencode({
      body = "Josiah is on it!"
    })
  }
}

resource "aws_api_gateway_resource" "transform_tips_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "transform_tips"
}

resource "aws_api_gateway_method" "proxy_transform_tips" {
  rest_api_id        = aws_api_gateway_rest_api.josiah.id
  resource_id        = aws_api_gateway_resource.transform_tips_resource.id
  http_method        = "POST"
  authorization      = "NONE"
  request_parameters = {}
}

resource "aws_api_gateway_integration" "lambda_transform_tips" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_transform_tips.resource_id
  http_method = aws_api_gateway_method.proxy_transform_tips.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.transform_tips.invoke_arn
}

resource "aws_api_gateway_method_response" "transform_tips_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.transform_tips_resource.id
  http_method = aws_api_gateway_method.proxy_transform_tips.http_method
  status_code = "200"
}

resource "aws_api_gateway_resource" "get_mpvs_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "get_mpvs"
}

resource "aws_api_gateway_method" "proxy_get_mpvs" {
  rest_api_id        = aws_api_gateway_rest_api.josiah.id
  resource_id        = aws_api_gateway_resource.get_mpvs_resource.id
  http_method        = "POST"
  authorization      = "NONE"
  request_parameters = {}
}

resource "aws_api_gateway_integration" "lambda_get_mpvs" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_get_mpvs.resource_id
  http_method = aws_api_gateway_method.proxy_get_mpvs.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_mpvs.invoke_arn
}

resource "aws_api_gateway_method_response" "get_mpvs_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_mpvs_resource.id
  http_method = aws_api_gateway_method.proxy_get_mpvs.http_method
  status_code = "200"
}

resource "aws_api_gateway_deployment" "josiah" {
  depends_on = [
    aws_api_gateway_integration.lambda_root,
    aws_api_gateway_integration.lambda_email_tips,
    aws_api_gateway_integration.lambda_transform_tips,
    aws_api_gateway_integration.lambda_get_mpvs
  ]

  rest_api_id = aws_api_gateway_rest_api.josiah.id
  stage_name  = "test"
  description = "Deployed at ${timestamp()}"
  lifecycle {
    create_before_destroy = true
  }
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