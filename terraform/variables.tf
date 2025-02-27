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

    # Google Drive
    gdrive_json = string
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
  }))
}

# Environment configurations
locals {
  # Base environment configuration template
  base_env_config = {
    PATH       = "/opt/bin"
    PYTHONPATH = "/var/task/src:/opt/lib"
  }

  # Service environments using the base configuration
  invoice_sync   = { prod = local.base_env_config }
  daily_sales    = { prod = local.base_env_config }
  daily_journal  = { prod = local.base_env_config }
  email_tips     = { prod = local.base_env_config }
  transform_tips = { prod = local.base_env_config }
  get_mpvs       = { prod = local.base_env_config }
  authorizer     = { prod = local.base_env_config }

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

  get_food_handler_links = { prod = local.base_env_config }

  lambda_env_get_food_handler_links = local.get_food_handler_links[terraform.workspace]

  update_food_handler_pdfs            = { prod = local.base_env_config }
  lambda_env_update_food_handler_pdfs = local.update_food_handler_pdfs[terraform.workspace]
}
