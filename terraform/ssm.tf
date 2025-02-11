# EzCater credentials
resource "aws_ssm_parameter" "ezcater_user" {
  name        = "/${terraform.workspace}/ezcater/user"
  description = "EzCater username"
  type        = "String"
  value       = var.service_credentials.ezcater_user
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "ezcater_password" {
  name        = "/${terraform.workspace}/ezcater/password"
  description = "EzCater password"
  type        = "SecureString"
  value       = var.service_credentials.ezcater_password
  tags        = local.common_tags
}

# FlexePOS credentials
resource "aws_ssm_parameter" "flexepos_user" {
  name        = "/${terraform.workspace}/flexepos/user"
  description = "FlexePOS username"
  type        = "String"
  value       = var.service_credentials.flexepos_user
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "flexepos_password" {
  name        = "/${terraform.workspace}/flexepos/password"
  description = "FlexePOS password"
  type        = "SecureString"
  value       = var.service_credentials.flexepos_password
  tags        = local.common_tags
}

# CrunchTime credentials
resource "aws_ssm_parameter" "crunchtime_user" {
  name        = "/${terraform.workspace}/crunchtime/user"
  description = "CrunchTime username"
  type        = "String"
  value       = var.service_credentials.crunchtime_user
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "crunchtime_password" {
  name        = "/${terraform.workspace}/crunchtime/password"
  description = "CrunchTime password"
  type        = "SecureString"
  value       = var.service_credentials.crunchtime_password
  tags        = local.common_tags
}

# DoorDash credentials
resource "aws_ssm_parameter" "doordash_user" {
  name        = "/${terraform.workspace}/doordash/user"
  description = "DoorDash username"
  type        = "String"
  value       = var.service_credentials.doordash_user
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "doordash_password" {
  name        = "/${terraform.workspace}/doordash/password"
  description = "DoorDash password"
  type        = "SecureString"
  value       = var.service_credentials.doordash_password
  tags        = local.common_tags
}

# GrubHub credentials
resource "aws_ssm_parameter" "grubhub_user" {
  name        = "/${terraform.workspace}/grubhub/user"
  description = "GrubHub username"
  type        = "String"
  value       = var.service_credentials.grubhub_user
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "grubhub_password" {
  name        = "/${terraform.workspace}/grubhub/password"
  description = "GrubHub password"
  type        = "SecureString"
  value       = var.service_credentials.grubhub_password
  tags        = local.common_tags
}

# UberEats credentials
resource "aws_ssm_parameter" "ubereats_user" {
  name        = "/${terraform.workspace}/ubereats/user"
  description = "UberEats username"
  type        = "String"
  value       = var.service_credentials.ubereats_user
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "ubereats_password" {
  name        = "/${terraform.workspace}/ubereats/password"
  description = "UberEats password"
  type        = "SecureString"
  value       = var.service_credentials.ubereats_password
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "ubereats_pin" {
  name        = "/${terraform.workspace}/ubereats/pin"
  description = "UberEats PIN"
  type        = "String"
  value       = var.service_credentials.ubereats_pin
  tags        = local.common_tags
}

# WhenIWork credentials
resource "aws_ssm_parameter" "wheniwork_user" {
  name        = "/${terraform.workspace}/wheniwork/user"
  description = "WhenIWork username"
  type        = "String"
  value       = var.service_credentials.wheniwork_user
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "wheniwork_password" {
  name        = "/${terraform.workspace}/wheniwork/password"
  description = "WhenIWork password"
  type        = "SecureString"
  value       = var.service_credentials.wheniwork_password
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "wheniwork_key" {
  name        = "/${terraform.workspace}/wheniwork/key"
  description = "WhenIWork API key"
  type        = "SecureString"
  value       = var.service_credentials.wheniwork_key
  tags        = local.common_tags
}

# Google Cloud Platform configuration
resource "aws_ssm_parameter" "gdrive_json" {
  name        = "/${terraform.workspace}/gcp/gdrive"
  description = "Google Drive service account credentials"
  type        = "SecureString"
  value       = var.service_credentials.gdrive_json
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "gcp_employees_folder" {
  name        = "/${terraform.workspace}/gcp/employees_folder"
  description = "Google Drive employees folder ID"
  type        = "String"
  value       = var.gcp_config.employees_folder
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "gcp_journal_folder" {
  name        = "/${terraform.workspace}/gcp/journal_folder"
  description = "Google Drive journal folder ID"
  type        = "String"
  value       = var.gcp_config.journal_folder
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "gcp_public_folder" {
  name  = "/prod/gcp/public_folder"
  type  = "String"
  value = var.gcp_config.public_folder
  tags  = local.common_tags
}

# Email configuration
resource "aws_ssm_parameter" "receiver_email" {
  name        = "/${terraform.workspace}/email/receiver_email"
  description = "Recipient email addresses for notifications"
  type        = "String"
  value       = join(", ", var.email_config.receiver_emails)
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "from_email" {
  name        = "/${terraform.workspace}/email/from_email"
  description = "Sender email address for notifications"
  type        = "String"
  value       = var.email_config.from_email
  tags        = local.common_tags
}

# Store configuration
resource "aws_ssm_parameter" "store_config" {
  name        = "/${terraform.workspace}/stores/config"
  description = "Store configuration including open/close dates"
  type        = "String"
  value       = jsonencode(var.store_config)
  tags        = local.common_tags
}
