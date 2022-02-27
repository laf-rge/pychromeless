resource "aws_ssm_parameter" "fpuser" {
  name  = "/${terraform.workspace}/flexepos/user"
  type  = "String"
  value = data.lastpass_secret.flexepos_lp.username
  tags = local.common_tags
}
resource "aws_ssm_parameter" "fppass" {
  name  = "/${terraform.workspace}/flexepos/password"
  type  = "SecureString"
  value = data.lastpass_secret.flexepos_lp.password
  tags = local.common_tags
}
resource "aws_ssm_parameter" "ctuser" {
  name  = "/${terraform.workspace}/crunchtime/user"
  type  = "String"
  value = data.lastpass_secret.crunchtime_lp.username
  tags = local.common_tags
}
resource "aws_ssm_parameter" "ctpass" {
  name  = "/${terraform.workspace}/crunchtime/password"
  type  = "SecureString"
  value = data.lastpass_secret.crunchtime_lp.password
  tags = local.common_tags
}
resource "aws_ssm_parameter" "emailuser" {
  name  = "/${terraform.workspace}/email/user"
  type  = "String"
  value = data.lastpass_secret.email_lp.username
  tags = local.common_tags
}
resource "aws_ssm_parameter" "emailpass" {
  name  = "/${terraform.workspace}/email/password"
  type  = "SecureString"
  value = data.lastpass_secret.email_lp.password
  tags = local.common_tags
}
resource "aws_ssm_parameter" "doordashuser" {
  name  = "/${terraform.workspace}/doordash/user"
  type  = "String"
  value = data.lastpass_secret.doordash_lp.username
  tags = local.common_tags
}
resource "aws_ssm_parameter" "doordashpass" {
  name  = "/${terraform.workspace}/doordash/password"
  type  = "SecureString"
  value = data.lastpass_secret.doordash_lp.password
  tags = local.common_tags
}
resource "aws_ssm_parameter" "grubhubuser" {
  name  = "/${terraform.workspace}/grubhub/user"
  type  = "String"
  value = data.lastpass_secret.grubhub_lp.username
  tags = local.common_tags
}
resource "aws_ssm_parameter" "grubhubpass" {
  name  = "/${terraform.workspace}/grubhub/password"
  type  = "SecureString"
  value = data.lastpass_secret.grubhub_lp.password
  tags = local.common_tags
}
resource "aws_ssm_parameter" "postmatesuser" {
  name  = "/${terraform.workspace}/postmates/user"
  type  = "String"
  value = data.lastpass_secret.postmates_lp.username
  tags = local.common_tags
}
resource "aws_ssm_parameter" "postmatespass" {
  name  = "/${terraform.workspace}/postmates/password"
  type  = "SecureString"
  value = data.lastpass_secret.postmates_lp.password
  tags = local.common_tags
}
resource "aws_ssm_parameter" "ubereatsuser" {
  name  = "/${terraform.workspace}/ubereats/user"
  type  = "String"
  value = data.lastpass_secret.ubereats_lp.username
  tags = local.common_tags
}
resource "aws_ssm_parameter" "ubereatspass" {
  name  = "/${terraform.workspace}/ubereats/password"
  type  = "SecureString"
  value = data.lastpass_secret.ubereats_lp.password
  tags = local.common_tags
}
