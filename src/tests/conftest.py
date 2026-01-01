"""
Pytest configuration and shared fixtures for PyChromeless test suite.

This file contains common fixtures and test configuration that can be used
across all test modules in the project.
"""

import os
import sys
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_aws_credentials() -> Generator[None, None, None]:
    """Mock AWS credentials to avoid actual AWS calls during testing."""
    with patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_SECURITY_TOKEN": "testing",
            "AWS_SESSION_TOKEN": "testing",
            "AWS_DEFAULT_REGION": "us-east-2",
        },
    ):
        yield


@pytest.fixture
def mock_ssm_parameter_store() -> Generator[MagicMock, None, None]:
    """Mock SSM Parameter Store to avoid AWS dependencies."""
    with patch("ssm_parameter_store.SSMParameterStore") as mock_ssm_class:
        mock_ssm_instance = MagicMock()
        mock_ssm_class.return_value = mock_ssm_instance

        # Default mock values for common parameters
        mock_ssm_instance.__getitem__.side_effect = lambda key: {
            "wheniwork": {
                "user": "test_user",
                "password": "test_password",
                "key": "test_key",
            },
            "email": {
                "from_email": "test@example.com",
                "receiver_email": "recipient@example.com",
            },
        }.get(key, {})

        yield mock_ssm_instance


@pytest.fixture
def mock_boto3_clients() -> Generator[Dict[str, Any], None, None]:
    """Mock all boto3 clients used in the application."""
    with patch("boto3.client") as mock_client, patch("boto3.resource") as mock_resource:
        # Mock SES client
        mock_ses = Mock()
        mock_ses.send_email.return_value = {"MessageId": "test-message-id"}

        # Mock DynamoDB resource
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        def client_side_effect(service_name: str, **kwargs: Any) -> Mock:
            if service_name == "ses":
                return mock_ses
            return Mock()

        def resource_side_effect(service_name: str, **kwargs: Any) -> Mock:
            if service_name == "dynamodb":
                return mock_dynamodb
            return Mock()

        mock_client.side_effect = client_side_effect
        mock_resource.side_effect = resource_side_effect

        yield {"ses": mock_ses, "dynamodb": mock_dynamodb, "table": mock_table}


@pytest.fixture
def sample_lambda_event() -> Dict[str, str]:
    """Sample Lambda event for testing handlers."""
    return {"year": "2024", "month": "01", "day": "15"}


@pytest.fixture
def sample_store_data() -> Dict[str, Dict[str, Any]]:
    """Sample store configuration data."""
    return {
        "20400": {"name": "Store 20400", "open_date": date(2024, 1, 31)},
        "20407": {"name": "Store 20407", "open_date": date(2024, 3, 6)},
    }


@pytest.fixture
def sample_tips_data() -> List[Dict[str, Any]]:
    """Sample tips data for testing."""
    return [
        {
            "last_name": "Doe",
            "first_name": "John",
            "title": "Crew (Primary)",
            "paycheck_tips": Decimal("25.00"),
        },
        {
            "last_name": "Smith",
            "first_name": "Jane",
            "title": "Crew (Primary)",
            "paycheck_tips": Decimal("50.00"),
        },
        {
            "last_name": "Brown",
            "first_name": "Bob",
            "title": "Manager",
            "paycheck_tips": Decimal("30.00"),
        },
    ]


@pytest.fixture
def sample_bill_data() -> Dict[str, Any]:
    """Sample QuickBooks bill data for testing."""
    return {
        "total_amount": Decimal("256.36"),
        "line_amounts": [Decimal("100.00"), Decimal("156.36")],
        "locations": ["20400", "20407", "20366", "20367", "20368"],
        "vendor": "Test Vendor",
        "doc_number": "TEST-001",
    }


@pytest.fixture
def mock_webdriver() -> Generator[Mock, None, None]:
    """Mock Selenium WebDriver to avoid actual browser automation."""
    with patch("selenium.webdriver.Chrome") as mock_chrome:
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Common WebDriver methods
        mock_driver.get.return_value = None
        mock_driver.quit.return_value = None
        mock_driver.find_element.return_value = Mock()
        mock_driver.find_elements.return_value = []

        yield mock_driver


@pytest.fixture
def mock_external_apis() -> Generator[Dict[str, Any], None, None]:
    """Mock external API calls (requests, etc.)."""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        # Default successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response

        yield {"get": mock_get, "post": mock_post, "response": mock_response}


@pytest.fixture
def freeze_time() -> Generator[datetime, None, None]:
    """Fixture to freeze time for testing date/time dependent code."""
    from freezegun import freeze_time as _freeze_time

    with _freeze_time("2024-01-15 10:00:00"):
        yield datetime(2024, 1, 15, 10, 0, 0)


@pytest.fixture(autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """Auto-use fixture to set up test environment variables."""
    test_env_vars = {
        "CONNECTIONS_TABLE": "test-connections-table",
        "CHROME_HEADLESS": "1",
        "PYTHONPATH": "src",
    }

    with patch.dict(os.environ, test_env_vars):
        yield


# Pytest markers for different test categories
pytest_plugins: List[str] = []


def pytest_configure(config: Any) -> None:
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Fast unit tests with no external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with external services"
    )
    config.addinivalue_line("markers", "e2e: End-to-end workflow tests")
    config.addinivalue_line("markers", "slow: Slow tests that may be skipped in CI")
    config.addinivalue_line(
        "markers", "financial: Tests involving financial calculations"
    )
    config.addinivalue_line("markers", "auth: Authentication and authorization tests")


def pytest_collection_modifyitems(config: Any, items: List[Any]) -> None:
    """Automatically mark tests based on their location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Add markers based on test name patterns
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        if "financial" in item.name.lower() or "bill" in item.name.lower():
            item.add_marker(pytest.mark.financial)
        if "auth" in item.name.lower() or "token" in item.name.lower():
            item.add_marker(pytest.mark.auth)
