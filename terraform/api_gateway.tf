resource "aws_api_gateway_authorizer" "azure_auth" {
  name           = "msal"
  rest_api_id    = aws_api_gateway_rest_api.josiah.id
  authorizer_uri = aws_lambda_function.authorizer.invoke_arn
}

resource "aws_api_gateway_rest_api" "josiah" {
  name        = "JosiahWeb"
  description = "Josiah's Button Mashing Game"
  binary_media_types = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "multipart/form-data"]
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  tags = local.common_tags
}

output "base_url" {
  value = aws_api_gateway_stage.test.invoke_url
}

resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {
    "method.request.querystring.day"   = true,
    "method.request.querystring.month" = true,
    "method.request.querystring.year"  = true
  }
  request_validator_id = aws_api_gateway_request_validator.parameters.id
}

resource "aws_api_gateway_integration" "lambda_root" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_root.resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method

  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = aws_lambda_function.functions["daily_sales"].invoke_arn
  content_handling        = "CONVERT_TO_TEXT"
  request_parameters = {
    "integration.request.header.X-Amz-Invocation-Type" = "'Event'",
    "integration.request.querystring.day"              = "method.request.querystring.day",
    "integration.request.querystring.month"            = "method.request.querystring.month",
    "integration.request.querystring.year"             = "method.request.querystring.year"
  }
  request_templates = {
    "multipart/form-data" = <<-EOT
                #set($inputRoot = $input.path('$'))
                {
                "year": "$input.params('year')",
                "month": "$input.params('month')",
                "day": "$input.params('day')",
                "requestContext": {
                    "requestId": "$context.requestId"
                }
                }
            EOT
  }
}

resource "aws_api_gateway_method_response" "root_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

resource "aws_api_gateway_integration_response" "lambda_root_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method = aws_api_gateway_integration.lambda_root.http_method
  status_code = aws_api_gateway_method_response.root_method_response_200.status_code

  response_templates = {
    "application/json" = <<EOF
    #set($context.responseOverride.header.X-Request-ID = $context.requestId)
    {
      "message": $input.json('$.message'),
      "task_id": "$context.requestId"
    }
    EOF
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'",
    "method.response.header.X-Request-ID"                = "context.requestId"
  }
}

resource "aws_api_gateway_integration" "integration-OPTIONS" {
  http_method = "OPTIONS"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "root_options_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method = aws_api_gateway_method.proxy_root_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Origin" = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
  "method.response.header.Access-Control-Allow-Methods" = true }
}

resource "aws_api_gateway_method" "proxy_root_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method   = aws_api_gateway_integration.integration-OPTIONS.http_method
  authorization = "NONE"
}

resource "aws_api_gateway_integration_response" "proxy_root_options-200" {
  http_method = aws_api_gateway_integration.integration-OPTIONS.http_method
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = local.cors_methods
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
  status_code = "200"
}

resource "aws_api_gateway_resource" "email_tips_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "email_tips"
}

resource "aws_api_gateway_method" "proxy_email_tips" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.email_tips_resource.id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {
    "method.request.querystring.day"   = true,
    "method.request.querystring.month" = true,
    "method.request.querystring.year"  = true
  }
  request_validator_id = aws_api_gateway_request_validator.parameters.id
}

resource "aws_api_gateway_integration" "lambda_email_tips" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_email_tips.resource_id
  http_method = aws_api_gateway_method.proxy_email_tips.http_method

  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = aws_lambda_function.functions["email_tips"].invoke_arn
  content_handling        = "CONVERT_TO_TEXT"
  request_parameters = {
    "integration.request.header.X-Amz-Invocation-Type" = "'Event'",
    "integration.request.querystring.day"              = "method.request.querystring.day",
    "integration.request.querystring.month"            = "method.request.querystring.month",
    "integration.request.querystring.year"             = "method.request.querystring.year"
  }
  request_templates = {
    "multipart/form-data" = <<-EOT
                #set($inputRoot = $input.path('$'))
                {
                "year": "$input.params('year')",
                "month": "$input.params('month')",
                "day": "$input.params('day')",
                "requestContext": {
                    "requestId": "$context.requestId"
                }
                }
            EOT
  }
}

resource "aws_api_gateway_method_response" "email_tips_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id
  http_method = aws_api_gateway_method.proxy_email_tips.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

resource "aws_api_gateway_integration_response" "lambda_email_tips_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id
  http_method = aws_api_gateway_integration.lambda_email_tips.http_method
  status_code = aws_api_gateway_method_response.email_tips_method_response_200.status_code
  response_templates = {
    "application/json" = <<EOF
    #set($context.responseOverride.header.X-Request-ID = $context.requestId)
    {
      "message": "Josiah is on it!",
      "task_id": "$context.requestId"
    }
    EOF
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'",
    "method.response.header.X-Request-ID"                = "context.requestId"
  }
}

resource "aws_api_gateway_method" "method_email_tips_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.email_tips_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_email_tips_OPTIONS" {
  http_method = aws_api_gateway_method.method_email_tips_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "email_tips_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id
  http_method = aws_api_gateway_method.method_email_tips_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Origin" = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
  "method.response.header.Access-Control-Allow-Methods" = true }
}

resource "aws_api_gateway_integration_response" "email_tips_options-200" {
  http_method = aws_api_gateway_integration.integration_email_tips_OPTIONS.http_method
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = local.cors_methods
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
  status_code = "200"
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
  authorization      = "CUSTOM"
  authorizer_id      = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {}
}

resource "aws_api_gateway_integration" "lambda_transform_tips" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_transform_tips.resource_id
  http_method = aws_api_gateway_method.proxy_transform_tips.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.functions["transform_tips"].invoke_arn
}

resource "aws_api_gateway_method_response" "transform_tips_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.transform_tips_resource.id
  http_method = aws_api_gateway_method.proxy_transform_tips.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

resource "aws_api_gateway_method" "method_transform_tips_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.transform_tips_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_transform_tips_OPTIONS" {
  http_method = aws_api_gateway_method.method_transform_tips_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.transform_tips_resource.id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "transform_tips_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.transform_tips_resource.id
  http_method = aws_api_gateway_method.method_transform_tips_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Origin" = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
  "method.response.header.Access-Control-Allow-Methods" = true }
}

resource "aws_api_gateway_integration_response" "transform_tips_options-200" {
  http_method = aws_api_gateway_method.method_transform_tips_options.http_method
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.transform_tips_resource.id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = local.cors_methods
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
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
  authorization      = "CUSTOM"
  authorizer_id      = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {}
}

resource "aws_api_gateway_integration" "lambda_get_mpvs" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_get_mpvs.resource_id
  http_method = aws_api_gateway_method.proxy_get_mpvs.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.functions["get_mpvs"].invoke_arn
}

resource "aws_api_gateway_method_response" "get_mpvs_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_mpvs_resource.id
  http_method = aws_api_gateway_method.proxy_get_mpvs.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Origin" = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
  "method.response.header.Access-Control-Allow-Methods" = true }
}

resource "aws_api_gateway_method" "method_get_mpvs_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.get_mpvs_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_get_mpvs_OPTIONS" {
  http_method = aws_api_gateway_method.method_get_mpvs_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_mpvs_resource.id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "get_mpvs_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_mpvs_resource.id
  http_method = aws_api_gateway_method.method_get_mpvs_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Origin" = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
  "method.response.header.Access-Control-Allow-Methods" = true }
}

resource "aws_api_gateway_integration_response" "get_mpvs_options-200" {
  http_method = aws_api_gateway_integration.integration_get_mpvs_OPTIONS.http_method
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_mpvs_resource.id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = local.cors_methods
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
  status_code = "200"
}

resource "aws_api_gateway_resource" "invoice_sync_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "invoice_sync"
}

resource "aws_api_gateway_method" "proxy_invoice_sync" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.invoice_sync_resource.id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {
    "method.request.querystring.month" = true,
    "method.request.querystring.year"  = true
  }
  request_validator_id = aws_api_gateway_request_validator.parameters.id
}

resource "aws_api_gateway_integration" "lambda_invoice_sync" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_invoice_sync.resource_id
  http_method = aws_api_gateway_method.proxy_invoice_sync.http_method

  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = aws_lambda_function.functions["invoice_sync"].invoke_arn
  content_handling        = "CONVERT_TO_TEXT"
  request_parameters = {
    "integration.request.header.X-Amz-Invocation-Type" = "'Event'",
    "integration.request.querystring.month"            = "method.request.querystring.month",
    "integration.request.querystring.year"             = "method.request.querystring.year"
  }
  request_templates = {
    "multipart/form-data" = <<-EOT
                #set($inputRoot = $input.path('$'))
                {
                "year": "$input.params('year')",
                "month": "$input.params('month')",
                "requestContext": {
                    "requestId": "$context.requestId"
                }
                }
            EOT
  }
}

resource "aws_api_gateway_method_response" "invoice_sync_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.invoice_sync_resource.id
  http_method = aws_api_gateway_method.proxy_invoice_sync.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

resource "aws_api_gateway_integration_response" "lambda_invoice_sync_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.invoice_sync_resource.id
  http_method = aws_api_gateway_integration.lambda_invoice_sync.http_method
  status_code = aws_api_gateway_method_response.invoice_sync_method_response_200.status_code
  response_templates = {
    "application/json" = <<EOF
    #set($context.responseOverride.header.X-Request-ID = $context.requestId)
    {
      "message": "Josiah is on it!",
      "task_id": "$context.requestId"
    }
    EOF
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'",
    "method.response.header.X-Request-ID"                = "context.requestId"
  }
}

resource "aws_api_gateway_method" "method_invoice_sync_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.invoice_sync_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_invoice_sync_OPTIONS" {
  http_method = aws_api_gateway_method.method_invoice_sync_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.invoice_sync_resource.id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "invoice_sync_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.invoice_sync_resource.id
  http_method = aws_api_gateway_method.method_invoice_sync_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "invoice_sync_options-200" {
  http_method = aws_api_gateway_integration.integration_invoice_sync_OPTIONS.http_method
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.invoice_sync_resource.id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = local.cors_methods
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
  status_code = "200"
}

resource "aws_api_gateway_deployment" "josiah" {
  depends_on = [
    aws_api_gateway_integration.lambda_root,
    aws_api_gateway_integration.lambda_email_tips,
    aws_api_gateway_integration.lambda_transform_tips,
    aws_api_gateway_integration.lambda_get_mpvs,
    aws_api_gateway_integration.lambda_invoice_sync,
    aws_api_gateway_integration.lambda_get_food_handler_links,
    aws_api_gateway_integration.lambda_update_food_handler_pdfs,
    aws_api_gateway_integration.integration-OPTIONS,
    aws_api_gateway_integration.integration_email_tips_OPTIONS,
    aws_api_gateway_integration.integration_transform_tips_OPTIONS,
    aws_api_gateway_integration.integration_get_mpvs_OPTIONS,
    aws_api_gateway_integration.integration_invoice_sync_OPTIONS,
    aws_api_gateway_integration.integration_get_food_handler_links_OPTIONS,
    aws_api_gateway_integration.integration_update_food_handler_pdfs_OPTIONS,
    aws_api_gateway_integration.lambda_split_bill,
    aws_api_gateway_integration.integration_split_bill_OPTIONS,
    aws_api_gateway_integration_response.update_food_handler_pdfs_response,
    aws_api_gateway_method_response.update_food_handler_pdfs_method_response_202,
    aws_api_gateway_integration.get_task_status_by_id_integration,
    aws_api_gateway_integration.get_task_status_by_operation_integration,
    aws_api_gateway_integration.task_status_options_integration,
    aws_api_gateway_integration.lambda_payroll_allocation,
    aws_api_gateway_integration.integration_payroll_allocation_OPTIONS,
    aws_api_gateway_integration.lambda_grubhub_csv_import,
    aws_api_gateway_integration.integration_grubhub_csv_import_OPTIONS,
    aws_api_gateway_integration.lambda_fdms_statement_import,
    aws_api_gateway_integration.integration_fdms_statement_import_OPTIONS
  ]

  rest_api_id = aws_api_gateway_rest_api.josiah.id

  triggers = {
    redeployment = sha1(jsonencode({
      get_food_handler_links_integration   = aws_api_gateway_integration.lambda_get_food_handler_links.id
      get_food_handler_links_method        = aws_api_gateway_method.proxy_get_food_handler_links.id
      get_food_handler_links_response      = aws_api_gateway_method_response.get_food_handler_links_method_response_200.id
      get_food_handler_links_options       = aws_api_gateway_integration.integration_get_food_handler_links_OPTIONS.id
      update_food_handler_pdfs_integration = aws_api_gateway_integration.lambda_update_food_handler_pdfs.id
      update_food_handler_pdfs_method      = aws_api_gateway_method.proxy_update_food_handler_pdfs.id
      update_food_handler_pdfs_response    = aws_api_gateway_integration_response.update_food_handler_pdfs_response.id
      update_food_handler_pdfs_options     = aws_api_gateway_integration.integration_update_food_handler_pdfs_OPTIONS.id
      split_bill_integration               = aws_api_gateway_integration.lambda_split_bill.id
      split_bill_method                    = aws_api_gateway_method.proxy_split_bill.id
      split_bill_response                  = aws_api_gateway_method_response.split_bill_method_response_200.id
      split_bill_options                   = aws_api_gateway_integration.integration_split_bill_OPTIONS.id
      task_status_integration              = aws_api_gateway_integration.get_task_status_by_id_integration.id
      task_status_by_operation_integration = aws_api_gateway_integration.get_task_status_by_operation_integration.id
      task_status_options_integration      = aws_api_gateway_integration.task_status_options_integration.id
      payroll_allocation_integration       = aws_api_gateway_integration.lambda_payroll_allocation.id
      payroll_allocation_method            = aws_api_gateway_method.proxy_payroll_allocation.id
      payroll_allocation_response          = aws_api_gateway_method_response.payroll_allocation_method_response_200.id
      payroll_allocation_options           = aws_api_gateway_integration.integration_payroll_allocation_OPTIONS.id
      grubhub_csv_import_integration       = aws_api_gateway_integration.lambda_grubhub_csv_import.id
      grubhub_csv_import_method            = aws_api_gateway_method.proxy_grubhub_csv_import.id
      grubhub_csv_import_response          = aws_api_gateway_method_response.grubhub_csv_import_method_response_200.id
      grubhub_csv_import_options           = aws_api_gateway_integration.integration_grubhub_csv_import_OPTIONS.id
      fdms_statement_import_integration    = aws_api_gateway_integration.lambda_fdms_statement_import.id
      fdms_statement_import_method         = aws_api_gateway_method.proxy_fdms_statement_import.id
      fdms_statement_import_response       = aws_api_gateway_method_response.fdms_statement_import_method_response_200.id
      fdms_statement_import_options        = aws_api_gateway_integration.integration_fdms_statement_import_OPTIONS.id
    }))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "test" {
  depends_on = [
    aws_api_gateway_account.main
  ]
  deployment_id = aws_api_gateway_deployment.josiah.id
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  stage_name    = "production"

  description = "Production stage for Josiah API"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format          = "$context.identity.sourceIp $context.identity.caller $context.identity.user [$context.requestTime] \"$context.httpMethod $context.resourcePath $context.protocol\" $context.status $context.responseLength $context.requestId"
  }

  xray_tracing_enabled = true

  variables = {
    "environment" = terraform.workspace
  }

  lifecycle {
    ignore_changes = [
      deployment_id, // Prevent unwanted updates
      description    // Prevent description changes from forcing updates
    ]
  }

  tags = local.common_tags
}

# Add CloudWatch log group for API Gateway access logs
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${aws_api_gateway_rest_api.josiah.name}"
  retention_in_days = 30
  tags              = local.common_tags
}

resource "aws_api_gateway_request_validator" "parameters" {
  name                        = "validate-parameters"
  rest_api_id                 = aws_api_gateway_rest_api.josiah.id
  validate_request_body       = false
  validate_request_parameters = true
}

locals {
  cors_headers = "'Content-Disposition,Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amzn-RequestId'"
  cors_methods = "'GET,POST,OPTIONS'"
  cors_origin  = "'*'"
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  stage_name  = aws_api_gateway_stage.test.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "INFO"
    data_trace_enabled     = true
    throttling_burst_limit = 5000
    throttling_rate_limit  = 10000
  }
}

resource "aws_api_gateway_resource" "split_bill_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "split_bill"
}

resource "aws_api_gateway_method" "proxy_split_bill" {
  rest_api_id        = aws_api_gateway_rest_api.josiah.id
  resource_id        = aws_api_gateway_resource.split_bill_resource.id
  http_method        = "POST"
  authorization      = "CUSTOM"
  authorizer_id      = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {}
}

resource "aws_api_gateway_integration" "lambda_split_bill" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_split_bill.resource_id
  http_method = aws_api_gateway_method.proxy_split_bill.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.functions["split_bill"].invoke_arn
}

resource "aws_api_gateway_method_response" "split_bill_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.split_bill_resource.id
  http_method = aws_api_gateway_method.proxy_split_bill.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method" "method_split_bill_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.split_bill_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_split_bill_OPTIONS" {
  http_method = aws_api_gateway_method.method_split_bill_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.split_bill_resource.id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "split_bill_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.split_bill_resource.id
  http_method = aws_api_gateway_method.method_split_bill_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "split_bill_options-200" {
  http_method = aws_api_gateway_integration.integration_split_bill_OPTIONS.http_method
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.split_bill_resource.id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = local.cors_methods
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
  status_code = "200"
}

resource "aws_api_gateway_resource" "get_food_handler_links_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "get_food_handler_links"
}

resource "aws_api_gateway_method" "proxy_get_food_handler_links" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.get_food_handler_links_resource.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.azure_auth.id
}

resource "aws_api_gateway_integration" "lambda_get_food_handler_links" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_get_food_handler_links.resource_id
  http_method = aws_api_gateway_method.proxy_get_food_handler_links.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.functions["get_food_handler_links"].invoke_arn
  timeout_milliseconds    = 29000 # API Gateway maximum (29 seconds)
}

resource "aws_api_gateway_method_response" "get_food_handler_links_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_food_handler_links_resource.id
  http_method = aws_api_gateway_method.proxy_get_food_handler_links.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

# Add OPTIONS method for CORS
resource "aws_api_gateway_method" "method_get_food_handler_links_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.get_food_handler_links_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_get_food_handler_links_OPTIONS" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_food_handler_links_resource.id
  http_method = aws_api_gateway_method.method_get_food_handler_links_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }

  depends_on = [
    aws_api_gateway_method.method_get_food_handler_links_options
  ]
}

resource "aws_api_gateway_method_response" "get_food_handler_links_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_food_handler_links_resource.id
  http_method = aws_api_gateway_method.method_get_food_handler_links_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "get_food_handler_links_options-200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_food_handler_links_resource.id
  http_method = aws_api_gateway_method.method_get_food_handler_links_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }

  depends_on = [
    aws_api_gateway_integration.integration_get_food_handler_links_OPTIONS,
    aws_api_gateway_method_response.get_food_handler_links_method_response_options
  ]
}

resource "aws_api_gateway_resource" "update_food_handler_pdfs_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "update_food_handler_pdfs"
}

resource "aws_api_gateway_method" "proxy_update_food_handler_pdfs" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.update_food_handler_pdfs_resource.id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.azure_auth.id
}

resource "aws_api_gateway_integration" "lambda_update_food_handler_pdfs" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_update_food_handler_pdfs.resource_id
  http_method = aws_api_gateway_method.proxy_update_food_handler_pdfs.http_method

  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = "arn:aws:apigateway:${var.settings.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.functions["update_food_handler_pdfs"].arn}/invocations"

  request_parameters = {
    "integration.request.header.X-Amz-Invocation-Type" = "'Event'"
  }

  request_templates = {
    "application/json" = <<EOF
{
  "body": $input.json('$'),
  "requestContext": {
    "requestId": "$context.requestId"
  }
}
EOF
  }
}

# Update integration response for async to include CORS headers
resource "aws_api_gateway_integration_response" "update_food_handler_pdfs_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.update_food_handler_pdfs_resource.id
  http_method = aws_api_gateway_method.proxy_update_food_handler_pdfs.http_method
  status_code = "202"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.X-Request-ID"                 = "context.requestId"
  }

  response_templates = {
    "application/json" = <<EOF
{
  "message": "PDF update started",
  "task_id": "$context.requestId"
}
EOF
  }

  depends_on = [
    aws_api_gateway_integration.lambda_update_food_handler_pdfs,
    aws_api_gateway_method_response.update_food_handler_pdfs_method_response_202
  ]
}

# Add 202 method response
resource "aws_api_gateway_method_response" "update_food_handler_pdfs_method_response_202" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.update_food_handler_pdfs_resource.id
  http_method = aws_api_gateway_method.proxy_update_food_handler_pdfs.http_method
  status_code = "202"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

# Add OPTIONS method for CORS
resource "aws_api_gateway_method" "method_update_food_handler_pdfs_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.update_food_handler_pdfs_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_update_food_handler_pdfs_OPTIONS" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.update_food_handler_pdfs_resource.id
  http_method = aws_api_gateway_method.method_update_food_handler_pdfs_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "update_food_handler_pdfs_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.update_food_handler_pdfs_resource.id
  http_method = aws_api_gateway_method.proxy_update_food_handler_pdfs.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

# Add method response for OPTIONS
resource "aws_api_gateway_method_response" "update_food_handler_pdfs_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.update_food_handler_pdfs_resource.id
  http_method = aws_api_gateway_method.method_update_food_handler_pdfs_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

# Update integration response to depend on method response
resource "aws_api_gateway_integration_response" "update_food_handler_pdfs_options-200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.update_food_handler_pdfs_resource.id
  http_method = aws_api_gateway_method.method_update_food_handler_pdfs_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }

  depends_on = [
    aws_api_gateway_integration.integration_update_food_handler_pdfs_OPTIONS,
    aws_api_gateway_method_response.update_food_handler_pdfs_method_response_options
  ]
}

# Task Status API Resources
resource "aws_api_gateway_resource" "task_status_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "task-status"
}

# Resource for getting specific task by ID
resource "aws_api_gateway_resource" "task_status_by_id_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_resource.task_status_resource.id
  path_part   = "{task_id}"
}

# Method for getting specific task by ID
resource "aws_api_gateway_method" "get_task_status_by_id" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.task_status_by_id_resource.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.azure_auth.id
}

# Integration for getting specific task by ID
resource "aws_api_gateway_integration" "get_task_status_by_id_integration" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.task_status_by_id_resource.id
  http_method = aws_api_gateway_method.get_task_status_by_id.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.task_status.invoke_arn
}

# Method for getting tasks by operation type or recent tasks
resource "aws_api_gateway_method" "get_task_status_by_operation" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.task_status_resource.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {
    "method.request.querystring.operation" = false
    "method.request.querystring.recent"    = false
    "method.request.querystring.hours"     = false
    "method.request.querystring.limit"     = false
  }
}

# Integration for getting tasks by operation type
resource "aws_api_gateway_integration" "get_task_status_by_operation_integration" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.task_status_resource.id
  http_method = aws_api_gateway_method.get_task_status_by_operation.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.task_status.invoke_arn
}

# Method response for task status endpoints
resource "aws_api_gateway_method_response" "task_status_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.task_status_resource.id
  http_method = aws_api_gateway_method.get_task_status_by_operation.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

# Method response for specific task endpoint
resource "aws_api_gateway_method_response" "task_status_by_id_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.task_status_by_id_resource.id
  http_method = aws_api_gateway_method.get_task_status_by_id.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

# OPTIONS method for task status endpoints
resource "aws_api_gateway_method" "task_status_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.task_status_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# OPTIONS integration for task status endpoints
resource "aws_api_gateway_integration" "task_status_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.task_status_resource.id
  http_method = aws_api_gateway_method.task_status_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }

  depends_on = [
    aws_api_gateway_method.task_status_options
  ]
}

# OPTIONS method response for task status endpoints
resource "aws_api_gateway_method_response" "task_status_options_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.task_status_resource.id
  http_method = aws_api_gateway_method.task_status_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

# OPTIONS integration response for task status endpoints
resource "aws_api_gateway_integration_response" "task_status_options_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.task_status_resource.id
  http_method = aws_api_gateway_method.task_status_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }

  depends_on = [
    aws_api_gateway_integration.task_status_options_integration,
    aws_api_gateway_method_response.task_status_options_response
  ]
}

# Payroll Allocation API Resources
resource "aws_api_gateway_resource" "payroll_allocation_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "payroll_allocation"
}

resource "aws_api_gateway_method" "proxy_payroll_allocation" {
  rest_api_id        = aws_api_gateway_rest_api.josiah.id
  resource_id        = aws_api_gateway_resource.payroll_allocation_resource.id
  http_method        = "POST"
  authorization      = "CUSTOM"
  authorizer_id      = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {}
}

resource "aws_api_gateway_integration" "lambda_payroll_allocation" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_payroll_allocation.resource_id
  http_method = aws_api_gateway_method.proxy_payroll_allocation.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.functions["payroll_allocation"].invoke_arn
}

resource "aws_api_gateway_method_response" "payroll_allocation_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.payroll_allocation_resource.id
  http_method = aws_api_gateway_method.proxy_payroll_allocation.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

resource "aws_api_gateway_method" "method_payroll_allocation_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.payroll_allocation_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_payroll_allocation_OPTIONS" {
  http_method = aws_api_gateway_method.method_payroll_allocation_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.payroll_allocation_resource.id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "payroll_allocation_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.payroll_allocation_resource.id
  http_method = aws_api_gateway_method.method_payroll_allocation_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "payroll_allocation_options-200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.payroll_allocation_resource.id
  http_method = aws_api_gateway_method.method_payroll_allocation_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }

  depends_on = [
    aws_api_gateway_integration.integration_payroll_allocation_OPTIONS,
    aws_api_gateway_method_response.payroll_allocation_method_response_options
  ]
}

# GrubHub CSV Import API Resources
resource "aws_api_gateway_resource" "grubhub_csv_import_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "grubhub_csv_import"
}

resource "aws_api_gateway_method" "proxy_grubhub_csv_import" {
  rest_api_id        = aws_api_gateway_rest_api.josiah.id
  resource_id        = aws_api_gateway_resource.grubhub_csv_import_resource.id
  http_method        = "POST"
  authorization      = "CUSTOM"
  authorizer_id      = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {}
}

resource "aws_api_gateway_integration" "lambda_grubhub_csv_import" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_grubhub_csv_import.resource_id
  http_method = aws_api_gateway_method.proxy_grubhub_csv_import.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.functions["grubhub_csv_import"].invoke_arn
}

resource "aws_api_gateway_method_response" "grubhub_csv_import_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.grubhub_csv_import_resource.id
  http_method = aws_api_gateway_method.proxy_grubhub_csv_import.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

resource "aws_api_gateway_method" "method_grubhub_csv_import_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.grubhub_csv_import_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_grubhub_csv_import_OPTIONS" {
  http_method = aws_api_gateway_method.method_grubhub_csv_import_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.grubhub_csv_import_resource.id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "grubhub_csv_import_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.grubhub_csv_import_resource.id
  http_method = aws_api_gateway_method.method_grubhub_csv_import_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "grubhub_csv_import_options-200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.grubhub_csv_import_resource.id
  http_method = aws_api_gateway_method.method_grubhub_csv_import_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }

  depends_on = [
    aws_api_gateway_integration.integration_grubhub_csv_import_OPTIONS,
    aws_api_gateway_method_response.grubhub_csv_import_method_response_options
  ]
}

# FDMS Statement Import API Resources
resource "aws_api_gateway_resource" "fdms_statement_import_resource" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  parent_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  path_part   = "fdms_statement_import"
}

resource "aws_api_gateway_method" "proxy_fdms_statement_import" {
  rest_api_id        = aws_api_gateway_rest_api.josiah.id
  resource_id        = aws_api_gateway_resource.fdms_statement_import_resource.id
  http_method        = "POST"
  authorization      = "CUSTOM"
  authorizer_id      = aws_api_gateway_authorizer.azure_auth.id
  request_parameters = {}
}

resource "aws_api_gateway_integration" "lambda_fdms_statement_import" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_method.proxy_fdms_statement_import.resource_id
  http_method = aws_api_gateway_method.proxy_fdms_statement_import.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.functions["fdms_statement_import"].invoke_arn
}

resource "aws_api_gateway_method_response" "fdms_statement_import_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.fdms_statement_import_resource.id
  http_method = aws_api_gateway_method.proxy_fdms_statement_import.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.X-Request-ID"                 = true
  }
}

resource "aws_api_gateway_method" "method_fdms_statement_import_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.fdms_statement_import_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration_fdms_statement_import_OPTIONS" {
  http_method = aws_api_gateway_method.method_fdms_statement_import_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.fdms_statement_import_resource.id
  type        = "MOCK"
}

resource "aws_api_gateway_method_response" "fdms_statement_import_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.fdms_statement_import_resource.id
  http_method = aws_api_gateway_method.method_fdms_statement_import_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "fdms_statement_import_options-200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.fdms_statement_import_resource.id
  http_method = aws_api_gateway_method.method_fdms_statement_import_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }

  depends_on = [
    aws_api_gateway_integration.integration_fdms_statement_import_OPTIONS,
    aws_api_gateway_method_response.fdms_statement_import_method_response_options
  ]
}
