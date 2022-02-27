variable "settings" {
  default = {
    account_number  = "262877227567"
    region          = "us-east-2"
    owner           = "william@wagonermanagement.com"
    accounting      = "20025"
    s3_bucket       = "wagonermanagementcorp"
    flexepos_cred   = "4235601104097358741"
    crunchtime_cred = "3333641072972018802"
    email_cred      = "7653141078630413087"
    doordash_cred   = "3852185866371626650"
    grubhub_cred    = "6705538157312948204"
    postmates_cred  = "8128598083756399362"
    ubereats_cred   = "6840207492185843759"
  }
}

locals {
  invoice_sync = {
    prod = {
      PATH = "/opt/bin"
      PYTHONPATH = "/var/task/src:/opt/lib"
    }
  }
  daily_sales = {
    prod = {
      PATH = "/opt/bin"
      PYTHONPATH = "/var/task/src:/opt/lib"
    }
  }
  daily_journal = {
    prod = {
      PATH = "/opt/bin"
      PYTHONPATH = "/var/task/src:/opt/lib"
    }
  }

  lambda_env_invoice_sync      = local.invoice_sync[terraform.workspace]
  lambda_env_daily_journal     = local.daily_journal[terraform.workspace]
  lambda_env_daily_sales       = local.daily_sales[terraform.workspace]

  common_tags = {
    Owner      = var.settings["owner"]
    Accounting = var.settings["accounting"]
    Name       = "flexepos-${terraform.workspace}"
  }
}

