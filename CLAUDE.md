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
# Backend (Python)
make test                  # Run all tests
make test-unit            # Run unit tests only
make test-integration     # Run integration tests only
make test-coverage        # Run tests with HTML coverage report
make test-parallel        # Run tests in parallel (faster)

# Frontend (React)
make frontend-test        # Run frontend unit tests (Vitest)
make frontend-e2e         # Run E2E tests (Playwright, headless)
make frontend-e2e-ui      # Run E2E tests with Playwright UI
make frontend-e2e-headed  # Run E2E tests with visible browser
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
make frontend-test       # Run frontend unit tests (Vitest)
make frontend-lint       # Lint frontend code
make frontend-deploy     # Build and deploy frontend to Namecheap (direct rsync)
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

### QuickBooks OAuth Integration

The system uses OAuth 2.0 for QuickBooks authentication. Tokens are stored in AWS Secrets Manager (`prod/qbo` in us-east-2).

**OAuth Flow:**
1. Frontend calls `/qb/auth-url` to get Intuit authorization URL
2. User authenticates in popup window on Intuit's site
3. Intuit redirects to `/qb/callback` with authorization code
4. Backend exchanges code for tokens and stores in Secrets Manager
5. Popup sends postMessage to parent window and closes

**API Endpoints:**
- `GET /qb/auth-url` - Generate OAuth authorization URL (authenticated)
- `GET /qb/callback` - Handle Intuit redirect, exchange code (unauthenticated)
- `GET /qb/connection-status` - Check current connection status (authenticated)
- `GET /unlinked_deposits` - Get sales receipts without linked bank deposits (authenticated)

**Key Functions in `src/qb.py`:**
- `get_auth_url(state)` - Generate authorization URL with state token
- `exchange_auth_code(code, realm_id)` - Exchange code for tokens
- `get_connection_status()` - Verify connection by attempting token refresh
- `get_unlinked_sales_receipts(start_date, end_date)` - Query unlinked sales receipts

**Frontend:**
- Settings page at `/settings/quickbooks` (restricted to admin user)
- Callback page at `/qb-callback` handles OAuth redirect

### Unlinked Deposits Feature

Shows QuickBooks SalesReceipts that have no linked deposit transactions (deposits that haven't hit the bank yet).

**API Endpoint:**
- `GET /unlinked_deposits` - Returns unlinked sales receipts
  - Query params: `start_date`, `end_date` (optional, defaults to 2025-01-01 through today)
  - Returns: `{ deposits: [...], summary: { count, total_amount } }`

**Backend (`src/qb.py`):**
- `get_unlinked_sales_receipts(start_date, end_date)` queries SalesReceipts where `TotalAmt > 0` and `LinkedTxn` is empty
- Returns: id, store, date, amount, doc_number, qb_url, `has_cents` (boolean)
- `has_cents=true` indicates the amount has non-zero cents, suggesting a likely missing FlexePOS entry (actionable via re-run)

**Frontend (`UnlinkedDepositsSection.tsx`):**
- Displayed on the Daily Sales page below the form
- Table columns: Date, Store, Amount, Doc#, Actions
- Warning badge for amounts with cents (these are actionable)
- "View in QB" link opens `https://app.qbo.intuit.com/app/salesreceipt?txnId={id}`
- "Re-run" button triggers daily_sales for that specific date + store

**Daily Sales Single-Store Re-run:**
The `daily_sales_handler` accepts an optional `store` parameter to process only one store:
```python
# Event format for single-store re-run
{
    "year": "2025",
    "month": "01",
    "day": "15",
    "store": "20358"  # Optional: process only this store
}
```

### State Management

- **DynamoDB Tables**:
  - `websocket_connections`: Active WebSocket connections for real-time updates
  - `task_states`: Task execution state with operation-based indexing
  - `daily_sales_progress`: Fine-grained progress tracking for daily sales operations

- **TTL Strategy**: Each operation type has custom TTL (12-48 hours) to auto-cleanup old task states

- **Stale Task Detection**: The `timeout_detector` Lambda runs every 5 minutes (via CloudWatch Events) to scan for tasks stuck in `started` or `processing` state. Tasks exceeding their operation's timeout (Lambda timeout + 60s buffer) are automatically marked as `failed` with error "Task timed out (no response received)". This handles Lambda crashes, unhandled exceptions, and other scenarios where tasks fail before sending a completion status.
  - Timeouts are defined in `terraform/lambda.tf` (`local.operation_timeouts`)
  - Uses the `operation_type-index` GSI on `task_states` table for efficient querying
  - Broadcasts failures to connected WebSocket clients

### Frontend Architecture

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4 (with PostCSS plugin)
- **UI Components**: Headless UI + Radix UI for accessibility
- **Authentication**: Azure MSAL (Microsoft Authentication Library)
- **Package Manager**: Bun (NOT npm/yarn)
- **Testing**: Vitest (unit) + Playwright (E2E)
- **Deployment**: Namecheap server via rsync (credentials in SSM)

Location: `frontend/` directory with own package.json and configuration

**E2E Test Mode**: When `VITE_E2E_MODE=true`, the app uses mock authentication (`MockMsalProvider`) and test routes (`routes.test.tsx`) to bypass real MSAL auth. Playwright config sets this automatically.

## Financial Data Handling

**CRITICAL**: This code processes real financial data for restaurant operations.

### Decimal Rules (MANDATORY)

1. **NEVER use `float` for money** - Always use `Decimal` type
2. **Import from `decimal_utils`** - Use the centralized module:
   ```python
   from decimal_utils import TWO_PLACES, ZERO, to_currency, FinancialJsonEncoder
   ```
3. **Initialize Decimal from strings** - Never from floats:
   ```python
   # CORRECT
   amount = Decimal("123.45")
   amount = ZERO

   # WRONG - float precision issues
   amount = Decimal(123.45)
   amount = Decimal(0.0)
   ```
4. **JSON serialization** - Always use `FinancialJsonEncoder`:
   ```python
   json.dumps(data, cls=FinancialJsonEncoder)
   ```
5. **Quantize after calculations**:
   ```python
   result = (subtotal * tax_rate).quantize(TWO_PLACES)
   ```

### When These Rules Apply

- QuickBooks API amounts (SalesReceipt, Bill, Deposit)
- FlexePOS scraped data (daily sales, tips)
- Delivery service amounts (DoorDash, GrubHub, UberEats)
- Any API response containing monetary values
- DynamoDB operations (returns Decimal by default)

### Additional Guidelines

- **Validate all financial data** before processing or syncing to QuickBooks
- **Implement audit trails** for financial operations
- **Log financial operations** with structured JSON logging

### Testing Financial Code

- Test negative amounts (credits, refunds)
- Test zero amounts
- Test large amounts (>$100,000)
- Verify bill splits sum exactly to original total
- Consider property-based tests with `hypothesis`

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

Located in `terraform/` directory with 12 .tf files:

- `main.tf`: Provider and backend configuration (S3 state in us-east-2)
- `lambda.tf`: Lambda function definitions (containerized + zip-based)
- `ws-lambda.tf`, `ws-api-gateway.tf`: WebSocket API infrastructure
- `api_gateway.tf`: REST API Gateway configuration
- `dynamodb.tf`: State management tables
- `iam.tf`: IAM roles and policies
- `ssm.tf`: Parameter Store resources (includes Namecheap deployment credentials)
- `monitoring.tf`: CloudWatch alarms and metrics
- `cloudwatch_event.tf`: Scheduled Lambda triggers (daily jobs, timeout detector)

**Frontend deployment**: Handled directly via `make frontend-deploy` (rsync), not Terraform. Credentials stored in SSM under `/${workspace}/frontend/namecheap/*`.

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

1. **Add handler to `src/lambda_function.py`**
   - Create handler function following existing patterns
   - Use `create_response()` for API responses (includes CORS headers)

2. **Define in `terraform/lambda.tf`**
   - Add to `locals.lambda_functions` map
   - Add environment variables if needed

3. **Add API Gateway resources in `terraform/api_gateway.tf`** (if HTTP endpoint needed)

   For a POST endpoint, add these 8 resources in order:

   ```hcl
   # 1. Resource (URL path)
   resource "aws_api_gateway_resource" "my_endpoint_resource" { ... }

   # 2. Method (POST with auth)
   resource "aws_api_gateway_method" "proxy_my_endpoint" { ... }

   # 3. Integration (Lambda proxy)
   resource "aws_api_gateway_integration" "lambda_my_endpoint" { ... }

   # 4. Method Response (200 with CORS headers)
   resource "aws_api_gateway_method_response" "my_endpoint_method_response_200" { ... }

   # 5. OPTIONS method (CORS preflight - no auth)
   resource "aws_api_gateway_method" "method_my_endpoint_options" { ... }

   # 6. OPTIONS integration (MOCK)
   resource "aws_api_gateway_integration" "integration_my_endpoint_OPTIONS" { ... }

   # 7. OPTIONS method response
   resource "aws_api_gateway_method_response" "my_endpoint_method_response_options" { ... }

   # 8. OPTIONS integration response (CORS headers)
   resource "aws_api_gateway_integration_response" "my_endpoint_options-200" { ... }
   ```

4. **Add to deployment triggers** (in `aws_api_gateway_deployment.josiah`)
   - Add integration to `depends_on` list
   - Add entries to `triggers` block

5. **Add Lambda permission** for API Gateway invocation (in `terraform/lambda.tf`)

6. **Run `make all`** to build and deploy

**IMPORTANT:** Copy an existing endpoint (like `fdms_statement_import` or `grubhub_csv_import`) as a template - don't create from scratch.

**Common Pitfalls:**
- Missing `depends_on` in integration response → "Invalid Integration identifier" error
- `deployment_id` in stage lifecycle `ignore_changes` → new endpoints don't deploy to stage
- Missing OPTIONS method → CORS errors on preflight requests
- Forgetting to add Lambda permission → 500 errors when API Gateway calls Lambda

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

## Common Gotchas & Lessons Learned

### DynamoDB

- **Composite Keys**: Tables with composite primary keys (partition + sort) require `query()` not `get_item()` to find by partition key alone. Example: `task_states` table has `task_id` + `timestamp` composite key.
- **Decimal Type**: DynamoDB returns numbers as Python `Decimal`. Use `FinancialJsonEncoder` from `decimal_utils` for JSON serialization.
- **Deduplication**: With composite keys, multiple records per partition key exist. Deduplicate results by partition key when returning lists.

### API Gateway / Terraform

- **New Endpoints**: Follow the 8-resource checklist in "Adding a New Lambda Function" section above.
- **Deployment Race Conditions**: Use explicit `depends_on` for integration responses that reference integrations.
- **Stage Updates**: Never add `deployment_id` to stage lifecycle `ignore_changes` - prevents new endpoints from deploying.

### File Uploads

- **Duplicate Field Names**: Multipart uploads with same field name (e.g., `file[]`) need deduplication in `decode_upload()`. See `src/tips_processing.py`.

### External Data Parsing

- **Data Variations**: Always handle apostrophes, casing, whitespace variations in external data.
- **Example**: Use `JERSEY MIKE'?S` regex to handle both "MIKE'S" and "MIKES" in FDMS statements.

### Python Logging

- **Reserved Attributes**: Never use `filename`, `lineno`, `funcName`, etc. in logging `extra` dicts - they're reserved by Python's LogRecord.

### Code Organization

- **QuickBooks Utilities**: All QB helpers belong in `src/qb.py` (store refs, account refs, vendor lookups). Don't duplicate patterns in feature modules.
- **Financial Calculations**: Always use `Decimal` type. Import `TWO_PLACES`, `ZERO`, `to_currency` from `decimal_utils`.

### Decimal & JSON Serialization

- **String Serialization**: Use `FinancialJsonEncoder` - Decimal becomes string to preserve precision
- **DynamoDB Returns Decimal**: Always use encoder when serializing DynamoDB query results
- **Float Contamination**: Never `Decimal(0.0)` - use `Decimal("0")` or `ZERO` from `decimal_utils`
- **reduce() Accumulator**: Initial value must be `Decimal`, not `0.0`

## References

- Primary entry points: `src/lambda_function.py`, `src/ws_lambda_function.py`
- Operation definitions: `src/operation_types.py`
- Infrastructure: `terraform/` directory
- Frontend: `frontend/` directory with separate README.md
- QuickBooks utilities: `src/qb.py` (OAuth, deposits, sales receipts, bill sync)
- Unit tests: `src/tests/unit/` (test_qb.py, test_unlinked_deposits_handler.py, etc.)
- Frontend tests: `frontend/src/**/__tests__/` (Vitest)
