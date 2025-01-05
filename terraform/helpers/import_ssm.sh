#!/bin/bash

# Import EzCater parameters
terraform import aws_ssm_parameter.ezcater_user "/prod/ezcater/user"
terraform import aws_ssm_parameter.ezcater_password "/prod/ezcater/password"

# Import FlexePOS parameters
terraform import aws_ssm_parameter.flexepos_user "/prod/flexepos/user"
terraform import aws_ssm_parameter.flexepos_password "/prod/flexepos/password"

# Import CrunchTime parameters
terraform import aws_ssm_parameter.crunchtime_user "/prod/crunchtime/user"
terraform import aws_ssm_parameter.crunchtime_password "/prod/crunchtime/password"

# Import DoorDash parameters
terraform import aws_ssm_parameter.doordash_user "/prod/doordash/user"
terraform import aws_ssm_parameter.doordash_password "/prod/doordash/password"

# Import GrubHub parameters
terraform import aws_ssm_parameter.grubhub_user "/prod/grubhub/user"
terraform import aws_ssm_parameter.grubhub_password "/prod/grubhub/password"

# Import UberEats parameters
terraform import aws_ssm_parameter.ubereats_user "/prod/ubereats/user"
terraform import aws_ssm_parameter.ubereats_password "/prod/ubereats/password"
terraform import aws_ssm_parameter.ubereats_pin "/prod/ubereats/pin"

# Import WhenIWork parameters
terraform import aws_ssm_parameter.wheniwork_user "/prod/wheniwork/user"
terraform import aws_ssm_parameter.wheniwork_password "/prod/wheniwork/password"
terraform import aws_ssm_parameter.wheniwork_key "/prod/wheniwork/key"

# Import GCP parameters
terraform import aws_ssm_parameter.gdrive_json "/prod/gcp/gdrive"
terraform import aws_ssm_parameter.gcp_employees_folder "/prod/gcp/employees_folder"
terraform import aws_ssm_parameter.gcp_journal_folder "/prod/gcp/journal_folder"

# Import Email parameters
terraform import aws_ssm_parameter.receiver_email "/prod/email/receiver_email"
terraform import aws_ssm_parameter.from_email "/prod/email/from_email"