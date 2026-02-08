variable "settings" {
  description = "Core configuration settings for the application"
  type = object({
    account_number = string
    region         = string
    owner          = string
    accounting     = string
    s3_bucket      = string
  })
}

variable "service_credentials" {
  description = "Service credentials for various integrations"
  type = object({
    # Behind The Counter
    btc_user     = string
    btc_password = string

    # EzCater
    ezcater_user     = string
    ezcater_password = string

    # FlexePOS
    flexepos_user     = string
    flexepos_password = string

    # CrunchTime
    crunchtime_user     = string
    crunchtime_password = string

    # DoorDash
    doordash_user     = string
    doordash_password = string

    # GrubHub
    grubhub_user     = string
    grubhub_password = string

    # UberEats
    ubereats_user     = string
    ubereats_password = string
    ubereats_pin      = string # Added PIN parameter

    # WhenIWork
    wheniwork_user     = string
    wheniwork_password = string
    wheniwork_key      = string

    # Zenput
    zenput_token = string

    # QuickBooks Online
    qbo_company_id = string

    # Google Drive
    gdrive_json = string

    # Square
    square_application_id = string
    square_access_token   = string
  })
  sensitive = true
}

variable "gcp_config" {
  description = "Google Cloud Platform configuration"
  type = object({
    employees_folder = string
    journal_folder   = string
    public_folder    = string
  })
}

variable "email_config" {
  description = "Email notification configuration"
  type = object({
    receiver_emails = list(string)
    from_email      = string
  })
}

variable "store_config" {
  description = "Store configuration with open/close dates"
  type = map(object({
    name          = string
    open_date     = string
    ubereats_uuid = string
    close_date    = optional(string)
    manager_name  = optional(string)
  }))
}

variable "namecheap_frontend_config" {
  description = "Namecheap server configuration for frontend deployment"
  type = object({
    host    = string
    user    = string
    path    = string
    port    = number
    ssh_key = string
  })
  sensitive = true
}

variable "frontend_url" {
  description = "Frontend URL for OAuth callback redirects (e.g., https://josiah.wagonermanagement.com)"
  type        = string
}

# Environment configurations
locals {
  # Base environment configuration template
  base_env_config = {
    PATH                       = "/opt/bin"
    PYTHONPATH                 = "/var/task/src:/opt/lib"
    CONNECTIONS_TABLE          = aws_dynamodb_table.websocket_connections.name
    WEBSOCKET_ENDPOINT         = replace(aws_apigatewayv2_stage.websocket.invoke_url, "wss://", "https://")
    DAILY_SALES_PROGRESS_TABLE = aws_dynamodb_table.daily_sales_progress.name
    TASK_STATES_TABLE          = aws_dynamodb_table.task_states.name
  }

  # Service environments using the base configuration
  invoice_sync             = { prod = local.base_env_config }
  daily_sales              = { prod = local.base_env_config }
  daily_journal            = { prod = local.base_env_config }
  email_tips               = { prod = local.base_env_config }
  transform_tips           = { prod = local.base_env_config }
  get_mpvs                 = { prod = local.base_env_config }
  split_bill               = { prod = local.base_env_config }
  get_food_handler_links   = { prod = local.base_env_config }
  update_food_handler_pdfs = { prod = local.base_env_config }
  payroll_allocation       = { prod = local.base_env_config }
  grubhub_csv_import       = { prod = local.base_env_config }
  fdms_statement_import    = { prod = local.base_env_config }
  authorizer               = { prod = local.base_env_config }
  qb_auth_url              = { prod = local.base_env_config }
  qb_callback = {
    prod = merge(local.base_env_config, {
      FRONTEND_URL = var.frontend_url
    })
  }
  qb_connection_status = { prod = local.base_env_config }
  unlinked_deposits    = { prod = local.base_env_config }
  qb_mcp = {
    prod = {
      QBO_CREDENTIAL_MODE = "aws"
      QBO_SECRET_NAME     = "prod/qbo"
    }
  }
  timeout_detector = {
    prod = merge(local.base_env_config, {
      OPERATION_TIMEOUTS = jsonencode(local.operation_timeouts)
    })
  }

  # Websocket configuration with additional DynamoDB settings
  websocket = {
    prod = local.base_env_config
  }

  # Lambda environment mappings
  lambda_env_invoice_sync             = local.invoice_sync[terraform.workspace]
  lambda_env_daily_journal            = local.daily_journal[terraform.workspace]
  lambda_env_daily_sales              = local.daily_sales[terraform.workspace]
  lambda_env_email_tips               = local.email_tips[terraform.workspace]
  lambda_env_transform_tips           = local.transform_tips[terraform.workspace]
  lambda_env_get_mpvs                 = local.get_mpvs[terraform.workspace]
  lambda_env_authorizer               = local.authorizer[terraform.workspace]
  lambda_env_split_bill               = local.split_bill[terraform.workspace]
  lambda_env_get_food_handler_links   = local.get_food_handler_links[terraform.workspace]
  lambda_env_update_food_handler_pdfs = local.update_food_handler_pdfs[terraform.workspace]
  lambda_env_payroll_allocation       = local.payroll_allocation[terraform.workspace]
  lambda_env_grubhub_csv_import       = local.grubhub_csv_import[terraform.workspace]
  lambda_env_fdms_statement_import    = local.fdms_statement_import[terraform.workspace]
  lambda_env_qb_auth_url              = local.qb_auth_url[terraform.workspace]
  lambda_env_qb_callback              = local.qb_callback[terraform.workspace]
  lambda_env_qb_connection_status     = local.qb_connection_status[terraform.workspace]
  lambda_env_unlinked_deposits        = local.unlinked_deposits[terraform.workspace]
  lambda_env_timeout_detector         = local.timeout_detector[terraform.workspace]
  lambda_env_qb_mcp                   = local.qb_mcp[terraform.workspace]
  lambda_env_websocket = {
    CONNECTIONS_TABLE  = aws_dynamodb_table.websocket_connections.name
    WEBSOCKET_ENDPOINT = replace(aws_apigatewayv2_stage.websocket.invoke_url, "wss://", "https://")
  }

  # Common resource tags
  common_tags = {
    Owner      = var.settings.owner
    Accounting = var.settings.accounting
    Name       = "flexepos-${terraform.workspace}"
    Managed_By = "Terraform"
  }

  # Logging configuration
  common_logging = {
    log_format            = "JSON"
    application_log_level = "INFO"
  }
}
