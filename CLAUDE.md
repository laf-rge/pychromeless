# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a serverless automation system for Jersey Mike's financial operations, syncing POS (FlexePOS), delivery services (DoorDash, GrubHub, UberEats, EzCater), inventory (CrunchTime), and scheduling (WhenIWork) data to QuickBooks. The system runs on AWS Lambda using containerized Python with headless Chrome for web scraping.

## Development Commands

### Setup & Installation
```bash
make install          # Install development dependencies
make install-prod     # Install production dependencies only
```

### Testing
```bash
make test                  # Run all tests
make test-unit            # Run unit tests only
make test-integration     # Run integration tests only
make test-coverage        # Run tests with HTML coverage report
make test-parallel        # Run tests in parallel (faster)
```

### Code Quality
```bash
make lint                 # Run basic linting (black, isort, flake8, mypy)
make lint-comprehensive   # Run comprehensive linting (adds pylint, bandit)
make format               # Auto-format code with black and isort
make security-check       # Run bandit + safety vulnerability scanning
```

### Build & Deployment
```bash
make all                  # Build everything and deploy to AWS
make clean               # Remove build artifacts

# Individual Lambda function builds
make websocket           # Build WebSocket handler
make validate_token      # Build token validator
make task_status         # Build task status handler

# Frontend (React 19 + Vite 7 + Tailwind CSS 4)
make frontend-install    # Install frontend dependencies (uses Bun)
make frontend-build      # Build frontend for production
make frontend-test       # Run frontend tests
make frontend-lint       # Lint frontend code
make frontend-deploy     # Deploy frontend to Namecheap server
```

### Terraform
```bash
cd terraform
terraform init           # Initialize Terraform
terraform plan          # Preview infrastructure changes
terraform apply         # Apply infrastructure changes
```

## Architecture

### Lambda Functions Architecture

The system uses a dual-architecture Lambda setup:

1. **Container-based Lambdas** (Main Processing Functions)
   - Built from custom Docker image with Chrome + Selenium
   - Handles web scraping operations (FlexePOS, delivery services, etc.)
   - Functions: `daily_sales`, `invoice_sync`, `email_tips`, `daily_journal`, etc.
   - Deployed via ECR (Elastic Container Registry)
   - Entry point: `src/lambda_function.py`

2. **Zip-based Lambdas** (Lightweight Functions)
   - Simple Python functions without heavy dependencies
   - Functions: `validate_token`, `ws_validate_token`, `task_status`
   - Deployed via direct .zip upload

### Data Flow

```
Third-party Services (FlexePOS, DoorDash, etc.)
           ↓ (Selenium scraping)
    Lambda Functions (Container)
           ↓
    WebSocket Manager → DynamoDB (progress tracking)
           ↓
    QuickBooks API / Google Drive
           ↓
    Email Service (notifications)
```

### Key Components

- **WebSocket Manager** (`websocket_manager.py`): Real-time progress updates to frontend via API Gateway WebSocket API
- **Progress Tracker** (`progress_tracker.py`): Tracks multi-step operation progress in DynamoDB
- **Store Config** (`store_config.py`): Manages multi-store configuration (store opening/closing dates, locations)
- **SSM Parameter Store** (`ssm_parameter_store.py`): Centralized secrets/config management
- **Operation Types** (`operation_types.py`): Enum-based operation definitions with TTL and display names

### State Management

- **DynamoDB Tables**:
  - `websocket_connections`: Active WebSocket connections for real-time updates
  - `task_states`: Task execution state with operation-based indexing
  - `daily_sales_progress`: Fine-grained progress tracking for daily sales operations

- **TTL Strategy**: Each operation type has custom TTL (12-48 hours) to auto-cleanup old task states

### Frontend Architecture

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4 (with PostCSS plugin)
- **UI Components**: Headless UI + Radix UI for accessibility
- **Authentication**: Azure MSAL (Microsoft Authentication Library)
- **Package Manager**: Bun (NOT npm/yarn)
- **Deployment**: Namecheap server via rsync (credentials in SSM)

Location: `frontend/` directory with own package.json and configuration

## Financial Data Handling

**CRITICAL**: This code processes real financial data for restaurant operations.

- **Always use `Decimal` type** for monetary calculations (never `float`)
- **Validate all financial data** before processing or syncing to QuickBooks
- **Implement audit trails** for financial operations
- **Test financial calculations** with edge cases (negative amounts, zero, large numbers)
- **Log financial operations** with structured JSON logging

Example pattern from codebase:
```python
from decimal import Decimal
TWO_PLACES = Decimal(10) ** -2
amount = Decimal(value).quantize(TWO_PLACES)
```

## AWS Integration Patterns

### Credentials Management
- **All secrets in SSM Parameter Store** (never hardcoded)
- **Environment-specific prefixes**: `/prod/`, `/test/`
- **Access pattern**: `ssm_parameter_store.py` provides centralized access

### WebSocket Progress Updates
```python
# Send progress updates to connected frontend clients
websocket_manager = WebSocketManager(table, connection_id)
websocket_manager.send_progress(
    operation=OperationType.DAILY_SALES,
    step="Scraping FlexePOS",
    progress=50
)
```

### Error Handling for AWS Services
- Use specific exception types from `botocore.exceptions`
- Log errors with structured JSON logging
- Implement retry logic with exponential backoff for web scraping
- Handle Lambda timeouts gracefully (functions have 5-10 minute limits)

## Web Scraping Patterns

The codebase uses Selenium WebDriver with Chrome in Lambda containers:

- **Headless mode**: Controlled via `CHROME_HEADLESS` environment variable
- **Wait for dynamic content**: Use explicit waits, not time.sleep()
- **Retry logic**: Implement exponential backoff for transient failures
- **Error screenshots**: Capture screenshot on failure for debugging
- **Resource cleanup**: Always close WebDriver instances in try/finally blocks

Common scraper modules:
- `flexepos.py`: FlexePOS data extraction
- `doordash.py`, `grubhub.py`, `ubereats.py`, `ezcater.py`: Delivery service integrations
- `crunchtime.py`: Inventory management
- `behind_the_counter.py`: Employee scheduling

## Code Quality Standards

From `.cursorrules` and `pyproject.toml`:

### Python Style
- **Line length**: 88 characters (Black standard)
- **Type hints**: Required for all function parameters and returns
- **Imports**: Follow isort with Black profile (stdlib → third-party → local)
- **Docstrings**: Google-style, required for all public functions

### Linting Configuration
The project uses strict linting with some pragmatic exceptions:
- `black` for formatting (enforced)
- `isort` for import ordering
- `flake8` with bugbear plugin
- `mypy` with strict type checking (but `ignore_missing_imports = true`)
- `pylint` for additional checks
- `bandit` for security scanning

### Testing Requirements
- **Mock external dependencies**: AWS services, web scraping, QuickBooks API
- **Use pytest fixtures** for test data (see `src/tests/conftest.py`)
- **Test markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`
- **Financial test focus**: Test edge cases for Decimal calculations

## Environment Variables

Lambda functions receive environment variables from Terraform:

- `CONNECTIONS_TABLE`: DynamoDB table for WebSocket connections
- `TASK_STATES_TABLE`: DynamoDB table for task state tracking
- `CHROME_HEADLESS`: Chrome headless mode (0 or 1)
- Plus service-specific credentials loaded from SSM

## Terraform Infrastructure

Located in `terraform/` directory with 13+ .tf files:

- `main.tf`: Provider and backend configuration (S3 state in us-east-2)
- `lambda.tf`: Lambda function definitions (containerized + zip-based)
- `ws-lambda.tf`, `ws-api-gateway.tf`: WebSocket API infrastructure
- `api_gateway.tf`: REST API Gateway configuration
- `dynamodb.tf`: State management tables
- `iam.tf`: IAM roles and policies
- `ssm.tf`: Parameter Store resources
- `monitoring.tf`: CloudWatch alarms and metrics
- `frontend.tf`: Frontend deployment configuration (Namecheap)

**Required variables**: Copy `terraform.tfvars.template` to `terraform.tfvars` and fill in values

## Common Development Tasks

### Running a Lambda Function Locally
```python
# Set up environment
export PYTHONPATH=src
python -m dotenv run python src/lambda_function.py
```

### Testing a Single Module
```bash
PYTHONPATH=src python -m pytest src/tests/unit/test_tips.py -v
```

### Updating a Scraper
1. Modify the scraper file (e.g., `src/flexepos.py`)
2. Run linting: `make lint`
3. Test locally with mock data
4. Build and deploy: `make all`

### Adding a New Lambda Function
1. Add handler to `src/lambda_function.py`
2. Define in `terraform/lambda.tf` `locals.lambda_functions`
3. Add environment variables in `terraform/lambda.tf`
4. Update `terraform/api_gateway.tf` if HTTP endpoint needed
5. Run `make all` to build and deploy

## Important Patterns & Conventions

### Request ID Tracking
All API responses include request IDs for debugging:
```python
response = create_response(
    status_code=200,
    body={"result": data},
    request_id=context.aws_request_id
)
```

### Multi-Store Configuration
The system supports multiple store locations with different opening/closing dates:
```python
store_config = StoreConfig()
for store in store_config.active_stores(target_date):
    # Process store data
```

### Progress Tracking Pattern
For long-running operations, use progress tracker:
```python
progress = ProgressTracker(
    operation_type=OperationType.DAILY_SALES,
    total_steps=10
)
progress.update(step_name="Scraping data", current_step=1)
```

## Security Considerations

- **Input validation**: Validate all API inputs before processing
- **Least privilege IAM**: Lambda roles have minimal required permissions
- **No hardcoded credentials**: All secrets in SSM Parameter Store (SecureString)
- **Data sanitization**: Sanitize data before DynamoDB operations
- **CORS configuration**: API Gateway has proper CORS headers
- **JWT authentication**: Frontend uses MSAL tokens validated by Lambda authorizer

## Debugging Tips

- **CloudWatch Logs**: Logs use JSON format for structured querying
- **WebSocket messages**: Monitor real-time progress in browser dev tools
- **DynamoDB state**: Check `task_states` table for operation history
- **Lambda errors**: Check Lambda function metrics and CloudWatch Logs
- **Chrome failures**: Check for screenshots/logs in Lambda execution logs

## Known Limitations

- **Lambda timeout**: Max 10 minutes (600 seconds) for container functions
- **Lambda memory**: Functions use 10GB memory for Chrome operations
- **Cold starts**: Container functions have ~10-15 second cold starts
- **Rate limits**: QuickBooks API has rate limits (handle 429 responses)
- **DynamoDB TTL**: Task states auto-delete after 12-48 hours

## References

- Primary entry points: `src/lambda_function.py`, `src/ws_lambda_function.py`
- Operation definitions: `src/operation_types.py`
- Infrastructure: `terraform/` directory
- Frontend: `frontend/` directory with separate README.md
