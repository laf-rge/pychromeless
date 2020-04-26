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
