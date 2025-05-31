# Testing Strategy for PyChromeless

This document outlines the testing strategy and conventions for the Jersey Mike's Data Integration Suite.

## Testing Approaches Available

### Modern Approach (Recommended)

Uses `pyproject.toml` for dependency management:

```bash
make install           # Install dev dependencies
make test             # Run tests
make test-coverage    # Run with coverage
make lint             # Code quality checks
```

### Legacy Approach (Backward Compatible)

Uses separate `requirements*.txt` files:

```bash
make install-dev      # Install dev dependencies
make test             # Run tests (same commands work)
```

## Test Organization

```
src/tests/
├── unit/              # Fast, isolated unit tests
├── integration/       # Service integration tests
├── e2e/              # End-to-end workflow tests
├── fixtures/         # Test data and fixtures
└── conftest.py       # Pytest configuration
```

## Test Categories & Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Tests external service integrations
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.slow` - Long-running tests (may be skipped in CI)

### Running Specific Test Categories

```bash
make test-unit          # Run only unit tests
make test-integration   # Run only integration tests
make test-e2e          # Run only end-to-end tests
make test-parallel     # Run all tests in parallel
```

## Current Test Coverage

### ✅ Well Tested

- **Financial Calculations** (`qb.py`): Bill splitting logic with edge cases
- **Business Logic** (`store_config.py`): Complex date calculations for inventory processing
- **Data Processing** (`tips.py`): Basic data transformation and validation

### 🚨 Needs Testing Priority

1. **Lambda Handlers** (`lambda_function.py`) - Critical entry points
2. **Authentication** (`auth_utils.py`) - Security critical
3. **Email Service** (`email_service.py`) - Business communication
4. **Web Scrapers** (`flexepos.py`, `doordash.py`, etc.) - Data accuracy critical

## Testing Best Practices

### 1. Mock External Dependencies

Always mock external services to ensure tests are:

- Fast and reliable
- Don't require API keys or network access
- Don't modify production data

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_aws_ssm():
    with patch('boto3.client') as mock_client:
        yield mock_client

def test_handler_with_mocked_aws(mock_aws_ssm):
    # Test logic here
    pass
```

### 2. Use Fixtures for Test Data

Create reusable test data using pytest fixtures:

```python
@pytest.fixture
def sample_tips_data():
    return {
        "employees": [
            {"name": "John Doe", "tips": 25.00},
            {"name": "Jane Smith", "tips": 50.00}
        ]
    }
```

### 3. Test Edge Cases

Especially important for financial calculations:

- Zero amounts
- Negative values
- Rounding precision
- Date boundaries
- Empty datasets

### 4. Test Error Handling

Verify graceful error handling:

- Network timeouts
- Invalid data formats
- Missing configuration
- Authentication failures

## Writing New Tests

### For Lambda Handlers

```python
def test_daily_sales_handler_success(mock_dependencies):
    """Test successful daily sales processing."""
    event = {"year": "2024", "month": "01", "day": "15"}

    result = daily_sales_handler(event)

    assert result["statusCode"] == 200
    assert "Success" in result["body"]

def test_daily_sales_handler_error(mock_dependencies):
    """Test error handling in daily sales processing."""
    # Mock an exception
    with patch('qb.create_daily_sales', side_effect=Exception("API Error")):
        result = daily_sales_handler({})

        assert result["statusCode"] == 500
```

### For Data Processing

```python
def test_tips_calculation_edge_cases():
    """Test tips calculations with edge cases."""
    tips = Tips()

    # Test with zero tips
    result = tips.calculate_distribution([])
    assert result == []

    # Test with negative values (should be filtered)
    data = [{"amount": -10}, {"amount": 50}]
    result = tips.calculate_distribution(data)
    assert len(result) == 1
    assert result[0]["amount"] == 50
```

## Continuous Integration

### Pre-commit Hooks

Install pre-commit hooks to run tests before commits:

```bash
make pre-commit-install
```

### CI Pipeline Tests

For CI/CD systems, use:

```bash
make ci-test  # Includes coverage reporting in XML format
```

## Lambda-Specific Testing Considerations

### 1. Size Constraints

Keep test dependencies separate from production dependencies to avoid Lambda size limits.

### 2. Cold Start Testing

Test Lambda handlers with minimal setup to simulate cold starts:

```python
def test_lambda_cold_start():
    """Test handler behavior on cold start."""
    # Clear any cached state
    importlib.reload(lambda_function)

    result = lambda_function.daily_sales_handler({})
    assert result is not None
```

### 3. Environment Variables

Test with various environment configurations:

```python
@pytest.mark.parametrize("env_vars", [
    {"AWS_LAMBDA_FUNCTION_NAME": "test-function"},
    {},  # Local development
])
def test_with_different_environments(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Run test
```

## Current Coverage Report

Run `make test-coverage` to generate:

- Terminal coverage summary
- HTML coverage report in `htmlcov/`

**Current Coverage: ~14%** (Significant improvement needed)

### Priority Areas for Coverage Improvement:

1. Lambda handlers (0% → 80% target)
2. Authentication modules (0% → 90% target)
3. Email service (0% → 70% target)
4. Web scrapers (8% → 60% target)

## Troubleshooting Tests

### Common Issues

1. **ImportError in tests**: Ensure `PYTHONPATH=src` is set
2. **AWS credential errors**: Mock AWS services properly
3. **Selenium WebDriver issues**: Use headless mode in tests
4. **Date/time inconsistencies**: Use `freezegun` for time mocking

### Debug Mode

```bash
# Run tests with more verbose output
PYTHONPATH=src python -m pytest src/tests -v -s

# Run specific test with debugging
PYTHONPATH=src python -m pytest src/tests/test_qb.py::TestQuickBooks::test_equal_bill_split -v -s
```

## Next Steps

1. **Add pytest-xdist** for parallel test execution
2. **Create integration test fixtures** for external services
3. **Add property-based testing** with Hypothesis for financial calculations
4. **Set up test database** for QuickBooks integration testing
5. **Add performance benchmarks** for critical Lambda functions

This testing strategy ensures reliable, maintainable code while respecting Lambda deployment constraints.
