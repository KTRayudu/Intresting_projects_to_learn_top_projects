"""
Shared pytest fixtures and configuration for all Lambda function tests
"""
import pytest
import os
from unittest.mock import Mock
from datetime import datetime


@pytest.fixture
def lambda_context():
    """
    Create mock AWS Lambda context object

    Returns:
        Mock: Lambda context with common attributes
    """
    context = Mock()
    context.function_name = 'test-function'
    context.function_version = '$LATEST'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
    context.memory_limit_in_mb = 128
    context.aws_request_id = 'test-request-id-12345'
    context.log_group_name = '/aws/lambda/test-function'
    context.log_stream_name = '2024/01/01/[$LATEST]test'

    # Mock remaining time method
    context.get_remaining_time_in_millis = Mock(return_value=30000)

    return context


@pytest.fixture
def mock_env_vars_email_poller(monkeypatch):
    """
    Set environment variables for invoice_email_poller Lambda

    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    monkeypatch.setenv('AZURE_CLIENT_ID', 'test-client-id-12345')
    monkeypatch.setenv('AZURE_CLIENT_SECRET', 'test-client-secret-67890')
    monkeypatch.setenv('AZURE_TENANT_ID', 'test-tenant-id-abcde')
    monkeypatch.setenv('MAILBOX_EMAIL', 'invoices@testcompany.com')
    monkeypatch.setenv('S3_BUCKET', 'test-bucket')
    monkeypatch.setenv('S3_PREFIX', 'Invoices/')


@pytest.fixture
def mock_env_vars_blueprint_manager(monkeypatch):
    """
    Set environment variables for bedrock_blueprint_manager Lambda

    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    monkeypatch.setenv('BLUEPRINT_NAME', 'test-freight-invoice-blueprint')
    monkeypatch.setenv('BLUEPRINT_FILE', 'bedrock_invoice_blueprint.json')
    monkeypatch.setenv('PROJECT_NAME', 'test-freight-audit-project')


@pytest.fixture
def mock_env_vars_invoice_processor(monkeypatch):
    """
    Set environment variables for bedrock_invoice_processor Lambda

    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    monkeypatch.setenv('PROJECT_NAME', 'Freight_Audit_Agent')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    monkeypatch.setenv('DATA_AUTOMATION_PROFILE_ARN',
                      'arn:aws:bedrock:us-east-1:123456789012:data-automation-profile/test-profile')


@pytest.fixture
def mock_env_vars_gvp_publisher(monkeypatch):
    """
    Set environment variables for gvp_invoice_publisher Lambda

    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    monkeypatch.setenv('GVP_LOGIN_ID', 'test-login-id')
    monkeypatch.setenv('GVP_PASSWORD', 'test-password')
    monkeypatch.setenv('BLUEPRINT_NAME', 'test-freight-invoice-blueprint')
    monkeypatch.setenv('BLUEPRINT_FILE', 'bedrock_invoice_blueprint.json')
    monkeypatch.setenv('PROJECT_NAME', 'test-freight-audit-project')
    monkeypatch.setenv('DOC_TYPE', 'invoices')


@pytest.fixture
def sample_timestamp():
    """
    Return consistent timestamp for testing

    Returns:
        datetime: Fixed datetime for reproducible tests
    """
    return datetime(2024, 1, 15, 10, 30, 0)


@pytest.fixture
def aws_credentials(monkeypatch):
    """
    Mock AWS credentials to prevent boto3 from looking for real credentials

    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
