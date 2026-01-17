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
  runtime     = "python3.14"
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
  # Lambda timeout values (in seconds) - single source of truth
  lambda_timeouts = {
    invoice_sync             = 600
    daily_journal            = 480
    daily_sales              = 540
    email_tips               = 480
    transform_tips           = 480
    get_mpvs                 = 480
    split_bill               = 300
    get_food_handler_links   = 120
    update_food_handler_pdfs = 480
    payroll_allocation       = 300
    grubhub_csv_import       = 300
    fdms_statement_import    = 300
    qb_auth_url              = 30
    qb_callback              = 30
    qb_connection_status     = 30
    unlinked_deposits        = 30
    timeout_detector         = 60
  }

  # Map operation_type enum values to Lambda timeouts with 60s buffer
  # Used by timeout_detector to identify stale tasks
  operation_timeouts = {
    daily_sales              = local.lambda_timeouts.daily_sales + 60
    invoice_sync             = local.lambda_timeouts.invoice_sync + 60
    email_tips               = local.lambda_timeouts.email_tips + 60
    daily_journal            = local.lambda_timeouts.daily_journal + 60
    update_food_handler_pdfs = local.lambda_timeouts.update_food_handler_pdfs + 60
    payroll_allocation       = local.lambda_timeouts.payroll_allocation + 60
    grubhub_csv_import       = local.lambda_timeouts.grubhub_csv_import + 60
    fdms_statement_import    = local.lambda_timeouts.fdms_statement_import + 60
    third_party_deposit      = 360 # Not a direct Lambda, default 6 min
  }

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
    },
    daily_sales = {
      name        = "daily-sales"
      description = "Enters daily sales for yesterday."
      handler     = "lambda_function.daily_sales_handler"
      timeout     = 540
      memory      = 10240
      env_vars    = local.lambda_env_daily_sales
    },
    email_tips = {
      name        = "email-tips"
      description = "Emails tips spreadsheet."
      handler     = "lambda_function.email_tips_handler"
      timeout     = 480
      memory      = 10240
      env_vars    = local.lambda_env_email_tips
    },
    transform_tips = {
      name        = "transform-tips"
      description = "Takes the excel tip spreadsheet and returns the Gusto CSV for import."
      handler     = "lambda_function.transform_tips_handler"
      timeout     = 480
      memory      = 10240
      env_vars    = local.lambda_env_transform_tips
    },
    get_mpvs = {
      name        = "get-mpvs"
      description = "Returns MPVs for a specific pay period or the whole month."
      handler     = "lambda_function.get_mpvs_handler"
      timeout     = 480
      memory      = 10240
      env_vars    = local.lambda_env_get_mpvs
    },
    split_bill = {
      name        = "split-bill"
      description = "Splits a QuickBooks bill between multiple locations"
      handler     = "lambda_function.split_bill_handler"
      timeout     = 300
      memory      = 10240
      env_vars    = local.lambda_env_split_bill
    },
    get_food_handler_links = {
      name        = "get-food-handler-links"
      description = "Returns public links to combined food handler PDFs for each store"
      handler     = "lambda_function.get_food_handler_links_handler"
      timeout     = 120
      memory      = 10240
      env_vars    = local.lambda_env_get_food_handler_links
    },
    update_food_handler_pdfs = {
      name        = "update-food-handler-pdfs"
      description = "Asynchronously updates the combined food handler PDFs for each store"
      handler     = "lambda_function.update_food_handler_pdfs_handler"
      timeout     = 480 # 8 minutes since this runs async
      memory      = 10240
      env_vars    = local.lambda_env_update_food_handler_pdfs
    },
    process_store_sales_internal = {
      name        = "process-store-sales-internal"
      description = "Internal Lambda to process daily sales for a single store"
      handler     = "lambda_function.process_store_sales_internal_handler"
      timeout     = 300 # 5 minutes for single store processing
      memory      = 10240
      env_vars    = local.lambda_env_daily_sales
    },
    payroll_allocation = {
      name        = "payroll-allocation"
      description = "Process payroll allocation from Gusto CSV to QuickBooks journal entry"
      handler     = "lambda_function.payroll_allocation_handler"
      timeout     = 300 # 5 minutes
      memory      = 10240
      env_vars    = local.lambda_env_payroll_allocation
    },
    grubhub_csv_import = {
      name        = "grubhub-csv-import"
      description = "Import GrubHub deposits from CSV export to QuickBooks"
      handler     = "lambda_function.grubhub_csv_import_handler"
      timeout     = 300 # 5 minutes
      memory      = 10240
      env_vars    = local.lambda_env_grubhub_csv_import
    },
    fdms_statement_import = {
      name        = "fdms-statement-import"
      description = "Import FDMS statement PDFs and create bills in QuickBooks"
      handler     = "lambda_function.fdms_statement_import_handler"
      timeout     = 300 # 5 minutes
      memory      = 10240
      env_vars    = local.lambda_env_fdms_statement_import
    },
    qb_auth_url = {
      name        = "qb-auth-url"
      description = "Generate QuickBooks OAuth authorization URL"
      handler     = "lambda_function.qb_auth_url_handler"
      timeout     = 30
      memory      = 10240
      env_vars    = local.lambda_env_qb_auth_url
    },
    qb_callback = {
      name        = "qb-callback"
      description = "Handle QuickBooks OAuth callback"
      handler     = "lambda_function.qb_callback_handler"
      timeout     = 30
      memory      = 10240
      env_vars    = local.lambda_env_qb_callback
    },
    qb_connection_status = {
      name        = "qb-connection-status"
      description = "Get QuickBooks connection status"
      handler     = "lambda_function.qb_connection_status_handler"
      timeout     = 30
      memory      = 10240
      env_vars    = local.lambda_env_qb_connection_status
    },
    unlinked_deposits = {
      name        = "unlinked-deposits"
      description = "Get unlinked sales receipts (deposits without linked bank transactions)"
      handler     = "lambda_function.unlinked_deposits_handler"
      timeout     = 30
      memory      = 10240
      env_vars    = local.lambda_env_unlinked_deposits
    },
    timeout_detector = {
      name        = "timeout-detector"
      description = "Detects and marks stale tasks as failed"
      handler     = "lambda_function.timeout_detector_handler"
      timeout     = 60
      memory      = 256
      env_vars    = local.lambda_env_timeout_detector
    }
  }

  lambda_env_get_task_status = {
    TASK_STATES_TABLE = aws_dynamodb_table.task_states.name
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

# Separate Lambda function for task status since it uses a zip file
resource "aws_lambda_function" "task_status" {
  function_name = "get-task-status-${terraform.workspace}"
  description   = "[${terraform.workspace}] Retrieves task status by ID or operation type"

  role        = aws_iam_role.flexepos_lambda_role.arn
  filename    = "../deploy/task_status.zip"
  handler     = "task_status.get_task_status_handler"
  runtime     = "python3.14"
  timeout     = 30
  memory_size = 256

  source_code_hash = filebase64sha256("../deploy/task_status.zip")

  environment {
    variables = local.lambda_env_get_task_status
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
  source_arn    = "${aws_api_gateway_rest_api.josiah.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw-auth" {
  statement_id  = "AllowAPIGatewayInvoke-auth"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.josiah.execution_arn}/*/*"
}

# Add API Gateway permission for the task status function
resource "aws_lambda_permission" "apigw_task_status" {
  statement_id  = "AllowAPIGatewayInvoke-task-status"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.task_status.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.josiah.execution_arn}/*/*"
}

# Allow the daily_sales Lambda to invoke the internal store processing Lambda
resource "aws_lambda_permission" "daily_sales_invoke_internal" {
  statement_id  = "AllowDailySalesInvokeInternal"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions["process_store_sales_internal"].function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.functions["daily_sales"].arn
}
