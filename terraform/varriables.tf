variable "settings" {
  default = {
    account_number  = "262877227567"
    region          = "us-east-2"
    owner           = "william@wagonermanagement.com"
    accounting      = "20025"
    s3_bucket       = "wagonermanagementcorp"
    flexepos_cred   = "4235601104097358741"
    crunchtime_cred = "3333641072972018802"
    doordash_cred   = "1054641869018106721"
    grubhub_cred    = "5283817055859461023"
    ubereats_cred   = "9013989643111798146"
    wheniwork_cred  = "365398016520677143"
  }
}

locals {
  invoice_sync = {
    prod = {
      PATH       = "/opt/bin"
      PYTHONPATH = "/var/task/src:/opt/lib"
    }
  }
  daily_sales = {
    prod = {
      PATH       = "/opt/bin"
      PYTHONPATH = "/var/task/src:/opt/lib"
    }
  }
  daily_journal = {
    prod = {
      PATH       = "/opt/bin"
      PYTHONPATH = "/var/task/src:/opt/lib"
    }
  }

  lambda_env_invoice_sync  = local.invoice_sync[terraform.workspace]
  lambda_env_daily_journal = local.daily_journal[terraform.workspace]
  lambda_env_daily_sales   = local.daily_sales[terraform.workspace]

  common_tags = {
    Owner      = var.settings["owner"]
    Accounting = var.settings["accounting"]
    Name       = "flexepos-${terraform.workspace}"
  }
}

