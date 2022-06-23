// SETTINGS
terraform {
  required_providers {
    lastpass = {
      source = "nrkno/lastpass"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
  backend "s3" {
    bucket  = "wagonermanagementcorp"
    key     = "flexepos/flexepos.tfstate"
    region  = "us-east-2"
    encrypt = true
  }
}

provider "aws" {
  region = "us-east-2"
}


