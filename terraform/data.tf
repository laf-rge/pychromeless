data "lastpass_secret" "flexepos_lp" {
  id = var.settings.flexepos_cred
}

data "lastpass_secret" "crunchtime_lp" {
  id = var.settings.crunchtime_cred
}

data "lastpass_secret" "email_lp" {
  id = var.settings.email_cred
}
