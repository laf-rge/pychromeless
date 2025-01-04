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

1. Configure AWS credentials
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables:
```bash
cp .env.example .env
# Add your credentials
```

## Deployment

```bash
# Deploy Lambda functions
serverless deploy

# Configure schedules
aws events put-rule ...
```

## Security Notes

- Credentials stored in AWS Secrets Manager
- IP whitelisting for FlexePOS access
- Rate limiting for API calls
- Secure data transmission

## Error Handling

- Automated retries for failed scrapes
- Error notifications via SNS/SES
- Daily health check reports
- Logging and monitoring via CloudWatch

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

## License

MIT License - See LICENSE file

## Support

For issues and feature requests, please use the GitHub issue tracker.