data "lastpass_secret" "flexepos_lp" {
  id = var.settings.flexepos_cred
}

data "lastpass_secret" "crunchtime_lp" {
  id = var.settings.crunchtime_cred
}

data "lastpass_secret" "email_lp" {
  id = var.settings.email_cred
}

data "lastpass_secret" "doordash_lp" {
  id = var.settings.doordash_cred
}

data "lastpass_secret" "grubhub_lp" {
  id = var.settings.grubhub_cred
}

data "lastpass_secret" "postmates_lp" {
  id = var.settings.postmates_cred
}

data "lastpass_secret" "ubereats_lp" {
  id = var.settings.ubereats_cred
}
