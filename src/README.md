# PyChromeless Lambda Functions

This directory contains AWS Lambda functions for Wagoner Management Corp.'s financial operations.

## Project Structure

```
src/
├── lambda_function.py     # Main Lambda handlers
├── email_service.py       # Email functionality
├── tips.py               # Tips processing
└── [...other modules]    # Additional functionality
```

## Local Development Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:

   - Copy `.env.example` to `.env` (if not exists)
   - Set required environment variables for AWS credentials and other configurations
   - `export CHROME_HEADLESS=2` to control a local instance of Chrome
   - `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 &`

3. Local testing examples:

   ```python
   # Test daily sales processing for yesterday
   python -c "from lambda_function import daily_sales_handler; daily_sales_handler()"

   # Test daily sales for specific date
   python -c "from lambda_function import daily_sales_handler; daily_sales_handler({'year': '2024', 'month': '01', 'day': '15'})"

   # Test invoice sync
   python -c "from lambda_function import invoice_sync_handler; invoice_sync_handler()"
   ```

## Lambda Function Handlers

### daily_sales_handler

Processes daily sales data and creates financial entries.

- Schedule: Daily
- Event format:
  ```json
  {
      "year": "YYYY",    # Optional: defaults to yesterday
      "month": "MM",     # Optional: defaults to yesterday
      "day": "DD"        # Optional: defaults to yesterday
  }
  ```

### invoice_sync_handler

Synchronizes invoice data from Crunchtime.

- Schedule: Daily
- No event parameters required

### third_party_deposit_handler

Handles third-party deposits from various services.

- Schedule: Daily
- No event parameters required

### daily_journal_handler

Generates and emails daily journal reports.

- Schedule: Daily
- No event parameters required

### email_tips_handler

Emails tips reports.

- Event format:
  ```json
  {
      "year": "YYYY",    # Optional: defaults to current
      "month": "MM",     # Optional: defaults to current
      "day": "DD"        # Optional: defaults to current
  }
  ```

### transform_tips_handler

Transforms tips data for payroll processing.

- Accepts multipart form data with:
  - file[]: Excel file containing tips data
  - year: YYYY (optional)
  - month: MM (optional)
  - pay_period: N (optional)

### get_mpvs_handler

Gets meal period violations data.

- Accepts multipart form data with:
  - year: YYYY (optional)
  - month: MM (optional)
  - pay_period: N (optional)

### timeout_detector_handler

Detects and marks stale tasks as failed. Tasks stuck in 'started' or 'processing' state beyond their operation's timeout are automatically marked as failed.

- Schedule: Every 5 minutes (CloudWatch Events)
- No event parameters required
- Broadcasts failure status to connected WebSocket clients

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_tips.py
```

## Deployment

The project uses Terraform for infrastructure management and deploys via CloudFormation/SAM.

See the `/terraform` directory for deployment configuration details.
