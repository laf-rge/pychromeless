variable "settings" {
  default = {
    account_number  = "262877227567"
    region          = "us-east-2"
    owner           = "william@wagonermanagement.com"
    accounting      = "20025"
    s3_bucket       = "wagonermanagementcorp"
    flexepos_cred   = "1375006941907287503"
    crunchtime_cred = "3333641072972018802"
  }
}

locals {
  common_tags = {
    Owner      = var.settings["owner"]
    Accounting = var.settings["accounting"]
    Name       = "flexepos-${terraform.workspace}"
  }
}

