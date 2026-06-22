# Freight Audit Agent - Unit Tests

Comprehensive unit tests for all Lambda functions in the Freight Audit Agent system.

## Overview

This test suite provides extensive coverage for all four Lambda functions:
- **invoice_email_poller** - Microsoft 365 email polling and PDF upload
- **bedrock_blueprint_manager** - Bedrock blueprint and project management
- **bedrock_invoice_processor** - Bedrock Data Automation job invocation
- **gvp_invoice_publisher** - GVP API invoice posting

## Test Philosophy

These are **unit tests** that mock all external dependencies:
- ✅ **No real AWS services** - Uses `moto` for mocking S3, STS, Bedrock
- ✅ **No real API calls** - Uses `responses` for mocking HTTP requests
- ✅ **No real credentials required** - Uses fake test credentials
- ✅ **Fast execution** - All tests run in seconds
- ✅ **Consistent results** - No dependency on external state

## Installation

### 1. Install Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install test dependencies
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
pytest --version
```

You should see `pytest 7.4.0` or higher.

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Tests for Specific Lambda Function

```bash
# Email poller tests
pytest tests/test_invoice_email_poller/

# Blueprint manager tests
pytest tests/test_bedrock_blueprint_manager/

# Invoice processor tests
pytest tests/test_bedrock_invoice_processor/

# GVP publisher tests
pytest tests/test_gvp_invoice_publisher/
```

### Run Specific Test File

```bash
pytest tests/test_invoice_email_poller/test_handler.py
```

### Run Specific Test Function

```bash
pytest tests/test_invoice_email_poller/test_handler.py::TestLambdaHandler::test_lambda_handler_success
```

### Run Tests by Marker

```bash
# Run only email poller tests
pytest -m email_poller

# Run only unit tests (default)
pytest -m unit

# Run slow tests
pytest -m slow
```

## Code Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=lambda_functions --cov-report=html

# Open HTML report
# Linux/Mac
open htmlcov/index.html

# Windows
start htmlcov/index.html
```

### Coverage Thresholds

The test suite enforces **80% minimum code coverage**. Tests will fail if coverage drops below this threshold.

### View Coverage in Terminal

```bash
pytest --cov=lambda_functions --cov-report=term-missing
```

This shows which lines are not covered by tests.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures (Lambda context, env vars, AWS credentials)
├── fixtures/
│   ├── sample_events.py                 # Sample event payloads (S3, EventBridge, Bedrock)
│   └── sample_responses.py              # Mock API responses (Graph, Bedrock, GVP)
├── test_invoice_email_poller/
│   ├── test_auth.py                     # GraphAuthenticator tests (36 lines)
│   ├── test_mail_client.py              # GraphMailClient tests (180+ lines)
│   └── test_handler.py                  # Lambda handler tests (270+ lines)
├── test_bedrock_blueprint_manager/
│   ├── test_bedrock_helpers.py          # Helper function tests (240+ lines)
│   └── test_handler.py                  # Lambda handler tests (170+ lines)
├── test_bedrock_invoice_processor/
│   └── test_handler.py                  # Lambda handler tests (300+ lines)
└── test_gvp_invoice_publisher/
    ├── test_gvp_client.py               # GVP client tests (280+ lines)
    └── test_handler.py                  # Lambda handler tests (270+ lines)
```

## Key Testing Patterns

### 1. Mocking AWS Services (S3, Bedrock, STS)

```python
from moto import mock_aws
import boto3

@mock_aws
def test_s3_operation(aws_credentials):
    # Create fake S3 bucket (using moto 4.x syntax)
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')

    # Your test code here - S3 operations happen in memory
```

### 2. Mocking HTTP Requests (Microsoft Graph, GVP API)

```python
import responses

@responses.activate
def test_api_call():
    # Mock the API endpoint
    responses.add(
        responses.GET,
        'https://api.example.com/endpoint',
        json={'data': 'value'},
        status=200
    )

    # Your test code here - HTTP calls are intercepted
```

### 3. Using Fixtures

```python
def test_lambda_function(lambda_context, mock_env_vars_email_poller):
    # Fixtures automatically provide:
    # - lambda_context: Mock Lambda context object
    # - mock_env_vars_email_poller: Environment variables set automatically

    response = lambda_handler({}, lambda_context)
    assert response['statusCode'] == 200
```

## Test Coverage by Component

### invoice_email_poller
- ✅ Authentication with Microsoft Graph (token acquisition, failures)
- ✅ Email retrieval (unread emails, empty inbox, API errors)
- ✅ Attachment handling (PDFs, inline images, non-PDFs)
- ✅ S3 upload with metadata (sanitization, encoding)
- ✅ Email marking as read
- ✅ Error handling (auth failures, API errors, S3 errors)

### bedrock_blueprint_manager
- ✅ Blueprint creation and retrieval
- ✅ Project creation and updates
- ✅ JSON file reading and parsing
- ✅ Environment variable handling
- ✅ Error handling (file not found, API errors)

### bedrock_invoice_processor
- ✅ EventBridge S3 event parsing
- ✅ Native S3 event parsing
- ✅ Project lookup and validation
- ✅ Bedrock job invocation
- ✅ URL-encoded key handling
- ✅ Error handling (invalid events, project not found, API errors)

### gvp_invoice_publisher
- ✅ Bedrock output retrieval and parsing
- ✅ S3 metadata extraction
- ✅ GVP authentication
- ✅ Invoice posting to GVP API
- ✅ Field mapping and defaults
- ✅ Error handling (auth failures, API errors, missing data)

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
# Make sure you're in the project root directory
cd /path/to/Freight_audit_agent

# Verify Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run tests
pytest
```

### AWS Credentials Errors

Tests should NOT require real AWS credentials. If you see credential errors:
```bash
# Verify the aws_credentials fixture is being used
# Check that test functions include 'aws_credentials' parameter
def test_something(aws_credentials):
    ...
```

### Mocking Not Working

If tests are making real network calls:
```bash
# Verify decorators are applied
@mock_aws  # For AWS services (moto 4.x syntax)
@responses.activate  # For HTTP requests
def test_something():
    ...
```

### Coverage Too Low

To find uncovered code:
```bash
pytest --cov=lambda_functions --cov-report=term-missing
```

Look for lines marked with `!` - these are not covered by tests.

## Writing New Tests

### 1. Create Test File

Follow the naming convention: `test_<module_name>.py`

### 2. Import Required Fixtures

```python
from tests.fixtures.sample_events import get_s3_eventbridge_event
from tests.fixtures.sample_responses import get_bedrock_list_projects_response
```

### 3. Use Descriptive Test Names

```python
def test_lambda_handler_success_with_valid_event():
    """Test successful processing when event is valid"""
    ...

def test_lambda_handler_error_when_missing_credentials():
    """Test error handling when credentials are missing"""
    ...
```

### 4. Follow AAA Pattern

```python
def test_something():
    # Arrange - Set up test data and mocks
    mock_data = {...}

    # Act - Execute the code being tested
    result = function_under_test(mock_data)

    # Assert - Verify the results
    assert result == expected_value
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml
```

## Best Practices

1. **Mock Everything External** - No real AWS/API calls in unit tests
2. **Test Happy Path First** - Then test error cases
3. **One Assertion Per Test** - Makes failures easier to diagnose
4. **Use Descriptive Names** - Test names should explain what they test
5. **Keep Tests Fast** - Unit tests should run in seconds
6. **Test Edge Cases** - Empty strings, None values, malformed data
7. **Clean Up After Tests** - Use fixtures for setup/teardown

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [moto Documentation](http://docs.getmoto.org/)
- [responses Documentation](https://github.com/getsentry/responses)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)

## Support

If you encounter issues with the tests:
1. Check this README for troubleshooting steps
2. Verify all dependencies are installed
3. Ensure you're running tests from the project root
4. Check that Python path is set correctly

## Test Metrics

- **Total Test Files**: 10
- **Total Test Functions**: 100+
- **Target Code Coverage**: 80%+
- **Average Execution Time**: < 30 seconds
