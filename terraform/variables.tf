variable "settings" {
  description = "Core configuration settings for the application"
  type = object({
    account_number = string
    region        = string
    owner         = string
    accounting    = string
    s3_bucket     = string
  })
  # Remove default values - require explicit configuration
}

variable "service_credentials" {
  description = "Credentials for various third-party services"
  type = object({
    flexepos_cred   = string
    crunchtime_cred = string
    doordash_cred   = string
    grubhub_cred    = string
    ubereats_cred   = string
    wheniwork_cred  = string
    ezcater_cred    = string
    gdrive_cred     = string
  })
  sensitive = true # Mark as sensitive to prevent exposure in logs
}

# Environment configurations
locals {
  # Base environment configuration template
  base_env_config = {
    PATH       = "/opt/bin"
    PYTHONPATH = "/var/task/src:/opt/lib"
  }

  # Service environments using the base configuration
  invoice_sync    = { prod = local.base_env_config }
  daily_sales     = { prod = local.base_env_config }
  daily_journal   = { prod = local.base_env_config }
  email_tips      = { prod = local.base_env_config }
  transform_tips  = { prod = local.base_env_config }
  get_mpvs        = { prod = local.base_env_config }
  authorizer      = { prod = local.base_env_config }
  
  # Websocket configuration with additional DynamoDB settings
  websocket = {
    prod = merge(local.base_env_config, {
      DYNAMODB_TABLE = aws_dynamodb_table.websocket_connections.name
    })
  }

  # Lambda environment mappings
  lambda_env_invoice_sync   = local.invoice_sync[terraform.workspace]
  lambda_env_daily_journal  = local.daily_journal[terraform.workspace]
  lambda_env_daily_sales    = local.daily_sales[terraform.workspace]
  lambda_env_email_tips     = local.email_tips[terraform.workspace]
  lambda_env_transform_tips = local.transform_tips[terraform.workspace]
  lambda_env_get_mpvs       = local.get_mpvs[terraform.workspace]
  lambda_env_authorizer     = local.authorizer[terraform.workspace]
  lambda_env_websocket      = local.websocket[terraform.workspace]

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