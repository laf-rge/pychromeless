# Pychromeless - Jersey Mike's Data Integration Suite

Serverless automation for syncing Jersey Mike's point-of-sale, delivery, and inventory data to QuickBooks.

## Features

- Automated scraping of FlexePOS system data
- Integration with third-party delivery services (DoorDash, GrubHub, UberEats, EzCater)
- CrunchTime inventory management sync
- WhenIWork scheduling integration
- Google Drive integration for data storage
- QuickBooks data synchronization
- Serverless deployment using AWS Lambda

## Architecture

- AWS Lambda functions with Chrome/Selenium
- Scheduled data collection and processing
- Secure credential management via AWS Systems Manager Parameter Store
- Error monitoring and notification system

## Prerequisites

- AWS Account with appropriate permissions
- Credentials for the following services:
  - FlexePOS
  - DoorDash
  - GrubHub
  - UberEats
  - EzCater
  - CrunchTime
  - WhenIWork
- Google Cloud Platform service account for Drive integration
- Terraform installed locally

## Setup

### 1. AWS Configuration

Ensure you have AWS credentials configured locally with appropriate permissions for:

- Lambda
- Systems Manager Parameter Store
- IAM
- CloudWatch
- S3

### 2. Terraform Configuration

1. Navigate to the `terraform` directory
2. Copy the template file to create your configuration:
   ```bash
   cp terraform.tfvars.template terraform.tfvars
   ```
3. Edit `terraform.tfvars` with your specific values:
   - AWS account details
   - Region preferences
   - Service credentials
   - S3 bucket name (must be globally unique)
   - Google Drive configuration
   - Email notification settings
   - Store configuration with opening and closing dates (optional)

### 3. Required Variables

The following variable groups must be configured:

#### Core Settings

```hcl
settings = {
  account_number = "YOUR_AWS_ACCOUNT"
  region        = "us-east-1"
  owner         = "team@example.com"
  accounting    = "TEAM_NAME"
  s3_bucket     = "your-bucket-name"
}
```

#### Service Credentials

Configure credentials for each service:

- FlexePOS (username/password)
- CrunchTime (username/password)
- DoorDash (username/password)
- GrubHub (username/password)
- UberEats (username/password/PIN)
- WhenIWork (username/password/API key)
- EzCater (username/password)

#### Google Cloud Platform

```hcl
gcp_config = {
  employees_folder = "FOLDER_ID"
  journal_folder  = "FOLDER_ID"
}
```

#### Email Configuration

```hcl
email_config = {
  receiver_emails = ["email1@example.com"]
  from_email     = "Bot Name <notifications@example.com>"
}
```

## Deployment

### Initial Deployment

1. Initialize Terraform:

   ```bash
   terraform init
   ```

2. Review the planned changes:

   ```bash
   terraform plan
   ```

3. Apply the configuration:
   ```bash
   terraform apply
   ```

### Updating Existing Deployment

1. Update values in terraform.tfvars
2. Run terraform plan to review changes
3. Apply changes with terraform apply

## Security Notes

- All sensitive credentials are stored in AWS Systems Manager Parameter Store
- Passwords and API keys are stored as SecureString parameters
- Never commit terraform.tfvars to version control
- Rotate service credentials regularly
- Monitor AWS CloudTrail for unauthorized API usage
- Review IAM roles and permissions regularly

## Error Handling

The system includes several error handling mechanisms:

- Automated retries for failed scrapes
- Comprehensive logging via CloudWatch
- Email notifications for failures
- Automated recovery procedures

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

Please ensure you:

- Do not commit any credentials
- Test all changes locally
- Update documentation as needed
- Follow existing code style

## Troubleshooting

Common issues and solutions:

- Credential issues: Check SSM Parameter Store values
- Lambda timeouts: Review Chrome instance memory usage
- Scraping failures: Verify service endpoint changes

## License

MIT License - See LICENSE file

## Support

For issues and feature requests, please use the GitHub issue tracker.
