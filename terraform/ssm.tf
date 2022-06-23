resource "aws_ssm_parameter" "fpuser" {
  name  = "/${terraform.workspace}/flexepos/user"
  type  = "String"
  value = data.lastpass_secret.flexepos_lp.username
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "fppass" {
  name  = "/${terraform.workspace}/flexepos/password"
  type  = "SecureString"
  value = data.lastpass_secret.flexepos_lp.password
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "ctuser" {
  name  = "/${terraform.workspace}/crunchtime/user"
  type  = "String"
  value = data.lastpass_secret.crunchtime_lp.username
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "ctpass" {
  name  = "/${terraform.workspace}/crunchtime/password"
  type  = "SecureString"
  value = data.lastpass_secret.crunchtime_lp.password
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "doordashuser" {
  name  = "/${terraform.workspace}/doordash/user"
  type  = "String"
  value = data.lastpass_secret.doordash_lp.username
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "doordashpass" {
  name  = "/${terraform.workspace}/doordash/password"
  type  = "SecureString"
  value = data.lastpass_secret.doordash_lp.password
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "grubhubuser" {
  name  = "/${terraform.workspace}/grubhub/user"
  type  = "String"
  value = data.lastpass_secret.grubhub_lp.username
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "grubhubpass" {
  name  = "/${terraform.workspace}/grubhub/password"
  type  = "SecureString"
  value = data.lastpass_secret.grubhub_lp.password
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "ubereatsuser" {
  name  = "/${terraform.workspace}/ubereats/user"
  type  = "String"
  value = data.lastpass_secret.ubereats_lp.username
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "ubereatspass" {
  name  = "/${terraform.workspace}/ubereats/password"
  type  = "SecureString"
  value = data.lastpass_secret.ubereats_lp.password
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "receiver_email" {
  name  = "/${terraform.workspace}/email/receiver_email"
  type  = "String"
  value = "info@wagonermanagement.com"
  tags  = local.common_tags
}
resource "aws_ssm_parameter" "from_email" {
  name  = "/${terraform.workspace}/email/from_email"
  type  = "String"
  value = "Josiah Info Robot <info@wagonermanagement.com>"
  tags  = local.common_tags
}