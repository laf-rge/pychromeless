// SETTINGS
provider "aws" {
  region = var.settings["region"]
}

provider "lastpass" {
    version = ">=0.4.2"
} 

terraform {
  backend "s3" {
    bucket = "wagonermanagementcorp"
    key    = "flexepos/flexepos.tfstate"
    region = "us-east-2"
    encrypt = true
  }
}

