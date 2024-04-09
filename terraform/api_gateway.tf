resource "aws_api_gateway_authorizer" "azure_auth" {
  name                   = "msal"
  rest_api_id            = aws_api_gateway_rest_api.josiah.id
  authorizer_uri         = aws_lambda_function.authorizer.invoke_arn
}

resource "aws_api_gateway_rest_api" "josiah" {
  name        = "JosiahWeb"
  description = "Josiah's Button Mashing Game"
  binary_media_types = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "multipart/form-data"]
}

output "base_url" {
  value = aws_api_gateway_deployment.josiah.invoke_url
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
    "multipart/form-data" = <<-EOT
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
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = false,
  }
}

resource "aws_api_gateway_integration_response" "lambda_root_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method = aws_api_gateway_integration.lambda_root.http_method
  status_code = aws_api_gateway_method_response.root_method_response_200.status_code
  response_templates = {
    "application/json" = jsonencode({
      body = "Josiah is on it!",
      headers = {"Access-Control-Allow-Origin": "*"},
    })
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'",
  }
}

resource "aws_api_gateway_integration" "integration-OPTIONS" {
  http_method          = "OPTIONS"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  type                 = "MOCK"
}

resource "aws_api_gateway_method_response" "root_options_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method = aws_api_gateway_method.proxy_root_options.http_method
  status_code = "200"
  response_parameters = {"method.response.header.Access-Control-Allow-Origin"= true, 
  "method.response.header.Access-Control-Allow-Headers"=true,
  "method.response.header.Access-Control-Allow-Methods"=true }
}

resource "aws_api_gateway_method" "proxy_root_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_rest_api.josiah.root_resource_id
  http_method   = aws_api_gateway_integration.integration-OPTIONS.http_method
  authorization = "NONE"
authorizer_id = aws_api_gateway_authorizer.azure_auth.id
}

resource "aws_api_gateway_integration_response" "proxy_root_options-200" {
  http_method = aws_api_gateway_method.proxy_root_options.http_method
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_rest_api.josiah.root_resource_id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Disposition,Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
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
    "multipart/form-data" = <<-EOT
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
  response_parameters = {"method.response.header.Access-Control-Allow-Origin"= true, 
  "method.response.header.Access-Control-Allow-Headers"=true,
  "method.response.header.Access-Control-Allow-Methods"=true }
}

resource "aws_api_gateway_integration_response" "lambda_email_tips_response" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id
  http_method = aws_api_gateway_integration.lambda_email_tips.http_method
  status_code = aws_api_gateway_method_response.email_tips_method_response_200.status_code
  response_templates = {
    "application/json" = jsonencode({
      body = "Josiah is on it!",
      headers = {"Access-Control-Allow-Origin": "*"},
    })
  }
  response_parameters = {
     "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
}

resource "aws_api_gateway_method" "method_email_tips_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.email_tips_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
authorizer_id = aws_api_gateway_authorizer.azure_auth.id
}

resource "aws_api_gateway_integration" "integration_email_tips_OPTIONS" {
  http_method          = aws_api_gateway_method.method_email_tips_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.email_tips_resource.id
  type                 = "MOCK"
}

resource "aws_api_gateway_method_response" "email_tips_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.email_tips_resource.id
  http_method = aws_api_gateway_method.method_email_tips_options.http_method
  status_code = "200"
  response_parameters = {"method.response.header.Access-Control-Allow-Origin"= true, 
  "method.response.header.Access-Control-Allow-Headers"=true,
  "method.response.header.Access-Control-Allow-Methods"=true }
}

resource "aws_api_gateway_integration_response" "email_tips_options-200" {
  http_method = aws_api_gateway_method.method_email_tips_options.http_method
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.email_tips_resource.id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Disposition,Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
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
  uri                     = aws_lambda_function.transform_tips.invoke_arn
}

resource "aws_api_gateway_method_response" "transform_tips_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.transform_tips_resource.id
  http_method = aws_api_gateway_method.proxy_transform_tips.http_method
  status_code = "200"
  response_parameters = {"method.response.header.Access-Control-Allow-Origin"= true, 
  "method.response.header.Access-Control-Allow-Headers"=true,
  "method.response.header.Access-Control-Allow-Methods"=true }
}

resource "aws_api_gateway_method" "method_transform_tips_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.transform_tips_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
authorizer_id = aws_api_gateway_authorizer.azure_auth.id
}

resource "aws_api_gateway_integration" "integration_transform_tips_OPTIONS" {
  http_method          = aws_api_gateway_method.method_transform_tips_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.transform_tips_resource.id
  type                 = "MOCK"
}

resource "aws_api_gateway_method_response" "transform_tips_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.transform_tips_resource.id
  http_method = aws_api_gateway_method.method_transform_tips_options.http_method
  status_code = "200"
  response_parameters = {"method.response.header.Access-Control-Allow-Origin"= true, 
  "method.response.header.Access-Control-Allow-Headers"=true,
  "method.response.header.Access-Control-Allow-Methods"=true }
}

resource "aws_api_gateway_integration_response" "transform_tips_options-200" {
  http_method = aws_api_gateway_method.method_transform_tips_options.http_method
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.transform_tips_resource.id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Disposition,Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
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
  uri                     = aws_lambda_function.get_mpvs.invoke_arn
}

resource "aws_api_gateway_method_response" "get_mpvs_method_response_200" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_mpvs_resource.id
  http_method = aws_api_gateway_method.proxy_get_mpvs.http_method
  status_code = "200"
  response_parameters = {"method.response.header.Access-Control-Allow-Origin"= true, 
  "method.response.header.Access-Control-Allow-Headers"=true,
  "method.response.header.Access-Control-Allow-Methods"=true }
}

resource "aws_api_gateway_method" "method_get_mpvs_options" {
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.get_mpvs_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
authorizer_id = aws_api_gateway_authorizer.azure_auth.id
}

resource "aws_api_gateway_integration" "integration_get_mpvs_OPTIONS" {
  http_method          = aws_api_gateway_method.method_get_mpvs_options.http_method
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.get_mpvs_resource.id
  type                 = "MOCK"
}

resource "aws_api_gateway_method_response" "get_mpvs_method_response_options" {
  rest_api_id = aws_api_gateway_rest_api.josiah.id
  resource_id = aws_api_gateway_resource.get_mpvs_resource.id
  http_method = aws_api_gateway_method.method_get_mpvs_options.http_method
  status_code = "200"
  response_parameters = {"method.response.header.Access-Control-Allow-Origin"= true, 
  "method.response.header.Access-Control-Allow-Headers"=true,
  "method.response.header.Access-Control-Allow-Methods"=true }
}

resource "aws_api_gateway_integration_response" "get_mpvs_options-200" {
  http_method = aws_api_gateway_integration.integration_get_mpvs_OPTIONS.http_method
  rest_api_id   = aws_api_gateway_rest_api.josiah.id
  resource_id   = aws_api_gateway_resource.get_mpvs_resource.id

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Disposition,Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
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
  stage_description = "Deployed at ${timestamp()}"
  description = "Deployed at ${timestamp()}"
  lifecycle {
    create_before_destroy = true
  }
}