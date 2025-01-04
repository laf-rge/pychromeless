# Pychromeless - Jersey Mike's Data Integration Suite

Serverless automation for syncing Jersey Mike's point-of-sale, delivery, and inventory data to QuickBooks.

## Features

- Automated scraping of FlexePOS system data
- Integration with third-party delivery services
- CrunchTime inventory management sync
- QuickBooks data synchronization
- Serverless deployment using AWS Lambda

## Architecture

- AWS Lambda functions with Chrome/Selenium
- Scheduled data collection and processing
- Secure credential management via AWS Secrets Manager
- Error monitoring and notification system

## Setup

### Terraform Configuration

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

Important: Never commit your `terraform.tfvars` file to version control as it contains sensitive information.

#### Required Variables:

- `settings`: Core AWS and project configuration
  - `account_number`: Your AWS account number
  - `region`: AWS region for deployment
  - `owner`: Owner's email or identifier
  - `accounting`: Team or department identifier
  - `s3_bucket`: Unique S3 bucket name for your deployment

- `service_credentials`: Integration credentials
  - Required for each service (FlexePOS, DoorDash, GrubHub, etc.)
  - Obtain these from your service providers' admin panels

## Deployment

# Deploy Lambda functions

# Configure schedules

## Security Notes

- Keep your `terraform.tfvars` file secure and never commit it to version control
- Rotate service credentials regularly
- Use AWS IAM roles with minimum required permissions
- Monitor AWS CloudTrail for unauthorized API usage

## Error Handling

- Automated retries for failed scrapes
- Logging and monitoring via CloudWatch

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

## License

MIT License - See LICENSE file

## Support

For issues and feature requests, please use the GitHub issue tracker.