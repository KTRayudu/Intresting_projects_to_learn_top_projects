"""
Unit tests for bedrock_invoice_processor/handler.py
Tests Lambda handler for processing invoice documents with AWS Bedrock Data Automation
"""
import pytest
import sys
import os
import json
from unittest.mock import Mock, patch
from moto import mock_aws
import importlib.util

# Load the specific handler module to avoid import conflicts
handler_path = os.path.join(os.path.dirname(__file__), '../../lambda_functions/bedrock_invoice_processor/handler.py')
spec = importlib.util.spec_from_file_location("invoice_processor_handler", handler_path)
invoice_processor_handler = importlib.util.module_from_spec(spec)
sys.modules['invoice_processor_handler'] = invoice_processor_handler
spec.loader.exec_module(invoice_processor_handler)

lambda_handler = invoice_processor_handler.lambda_handler
from tests.fixtures.sample_events import get_s3_eventbridge_event, get_s3_native_event
from tests.fixtures.sample_responses import (
    get_bedrock_list_projects_response,
    get_bedrock_invoke_async_response
)


class TestLambdaHandler:
    """Test cases for lambda_handler function"""

    @mock_aws
    @patch('invoice_processor_handler.boto3.client')
    def test_lambda_handler_eventbridge_format_success(
        self,
        mock_boto_client,
        lambda_context,
        mock_env_vars_invoice_processor,
        aws_credentials
    ):
        """Test successful processing of EventBridge S3 event"""
        # Mock AWS clients
        mock_bda_client = Mock()
        mock_bda_runtime_client = Mock()
        mock_sts_client = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'bedrock-data-automation':
                return mock_bda_client
            elif service_name == 'bedrock-data-automation-runtime':
                return mock_bda_runtime_client
            elif service_name == 'sts':
                return mock_sts_client

        mock_boto_client.side_effect = client_factory

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock Bedrock responses
        mock_bda_client.list_data_automation_projects.return_value = get_bedrock_list_projects_response("Freight_Audit_Agent")
        mock_bda_runtime_client.invoke_data_automation_async.return_value = get_bedrock_invoke_async_response()

        # Create EventBridge S3 event
        event = get_s3_eventbridge_event(
            bucket="test-bucket",
            key="Invoices/test-invoice.pdf"
        )

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Bedrock job started successfully'
        assert 'invocation_arn' in body
        assert body['input_bucket'] == 'test-bucket'
        assert body['input_key'] == 'Invoices/test-invoice.pdf'
        assert body['project_name'] == 'Freight_Audit_Agent'

        # Verify Bedrock was called correctly
        mock_bda_runtime_client.invoke_data_automation_async.assert_called_once()
        call_kwargs = mock_bda_runtime_client.invoke_data_automation_async.call_args[1]
        assert call_kwargs['inputConfiguration']['s3Uri'] == 's3://test-bucket/Invoices/test-invoice.pdf'
        assert call_kwargs['outputConfiguration']['s3Uri'] == 's3://test-bucket/lambda-output'
        assert 'dataAutomationProjectArn' in call_kwargs['dataAutomationConfiguration']

    @mock_aws
    @patch('invoice_processor_handler.boto3.client')
    def test_lambda_handler_native_s3_format_success(
        self,
        mock_boto_client,
        lambda_context,
        mock_env_vars_invoice_processor,
        aws_credentials
    ):
        """Test successful processing of native S3 event"""
        # Mock AWS clients
        mock_bda_client = Mock()
        mock_bda_runtime_client = Mock()
        mock_sts_client = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'bedrock-data-automation':
                return mock_bda_client
            elif service_name == 'bedrock-data-automation-runtime':
                return mock_bda_runtime_client
            elif service_name == 'sts':
                return mock_sts_client

        mock_boto_client.side_effect = client_factory

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock Bedrock responses
        mock_bda_client.list_data_automation_projects.return_value = get_bedrock_list_projects_response("Freight_Audit_Agent")
        mock_bda_runtime_client.invoke_data_automation_async.return_value = get_bedrock_invoke_async_response()

        # Create native S3 event
        event = get_s3_native_event(
            bucket="test-bucket",
            key="Invoices/test-invoice.pdf"
        )

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Bedrock job started successfully'
        assert body['input_bucket'] == 'test-bucket'
        assert body['input_key'] == 'Invoices/test-invoice.pdf'

    def test_lambda_handler_invalid_event_format(
        self,
        lambda_context,
        mock_env_vars_invoice_processor,
        aws_credentials
    ):
        """Test handling of invalid event format"""
        # Event without 'detail' or 'Records'
        event = {"invalid": "structure"}

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Unsupported event format' in body['error']

    def test_lambda_handler_missing_s3_details(
        self,
        lambda_context,
        mock_env_vars_invoice_processor,
        aws_credentials
    ):
        """Test handling of event with missing S3 bucket/key"""
        # Event with incomplete S3 details
        event = {
            "detail": {
                "bucket": {},  # Missing 'name'
                "object": {}   # Missing 'key'
            }
        }

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    @mock_aws
    @patch('invoice_processor_handler.boto3.client')
    def test_lambda_handler_project_not_found(
        self,
        mock_boto_client,
        lambda_context,
        mock_env_vars_invoice_processor,
        aws_credentials
    ):
        """Test handling of project not found error"""
        # Mock AWS clients
        mock_bda_client = Mock()
        mock_sts_client = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'bedrock-data-automation':
                return mock_bda_client
            elif service_name == 'sts':
                return mock_sts_client
            elif service_name == 'bedrock-data-automation-runtime':
                return Mock()

        mock_boto_client.side_effect = client_factory

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock empty projects list
        mock_bda_client.list_data_automation_projects.return_value = {"projects": []}

        # Create event
        event = get_s3_eventbridge_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'not found' in body['error'].lower()

    @mock_aws
    @patch('invoice_processor_handler.boto3.client')
    def test_lambda_handler_bedrock_invocation_error(
        self,
        mock_boto_client,
        lambda_context,
        mock_env_vars_invoice_processor,
        aws_credentials
    ):
        """Test handling of Bedrock invocation error"""
        # Mock AWS clients
        mock_bda_client = Mock()
        mock_bda_runtime_client = Mock()
        mock_sts_client = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'bedrock-data-automation':
                return mock_bda_client
            elif service_name == 'bedrock-data-automation-runtime':
                return mock_bda_runtime_client
            elif service_name == 'sts':
                return mock_sts_client

        mock_boto_client.side_effect = client_factory

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock Bedrock responses
        mock_bda_client.list_data_automation_projects.return_value = get_bedrock_list_projects_response("Freight_Audit_Agent")
        mock_bda_runtime_client.invoke_data_automation_async.side_effect = Exception("Bedrock API error")

        # Create event
        event = get_s3_eventbridge_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Unexpected error' in body['error']

    @mock_aws
    @patch('invoice_processor_handler.boto3.client')
    def test_lambda_handler_custom_output_bucket(
        self,
        mock_boto_client,
        lambda_context,
        mock_env_vars_invoice_processor,
        aws_credentials
    ):
        """Test handler with custom output bucket specified in event"""
        # Mock AWS clients
        mock_bda_client = Mock()
        mock_bda_runtime_client = Mock()
        mock_sts_client = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'bedrock-data-automation':
                return mock_bda_client
            elif service_name == 'bedrock-data-automation-runtime':
                return mock_bda_runtime_client
            elif service_name == 'sts':
                return mock_sts_client

        mock_boto_client.side_effect = client_factory

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock Bedrock responses
        mock_bda_client.list_data_automation_projects.return_value = get_bedrock_list_projects_response("Freight_Audit_Agent")
        mock_bda_runtime_client.invoke_data_automation_async.return_value = get_bedrock_invoke_async_response()

        # Create event with custom output bucket
        event = get_s3_eventbridge_event()
        event['output_bucket'] = 'custom-output-bucket'

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['output_bucket'] == 'custom-output-bucket'

        # Verify Bedrock was called with custom output bucket
        call_kwargs = mock_bda_runtime_client.invoke_data_automation_async.call_args[1]
        assert 's3://custom-output-bucket/lambda-output' in call_kwargs['outputConfiguration']['s3Uri']

    @mock_aws
    @patch('invoice_processor_handler.boto3.client')
    def test_lambda_handler_url_encoded_s3_key(
        self,
        mock_boto_client,
        lambda_context,
        mock_env_vars_invoice_processor,
        aws_credentials
    ):
        """Test handler correctly decodes URL-encoded S3 keys"""
        # Mock AWS clients
        mock_bda_client = Mock()
        mock_bda_runtime_client = Mock()
        mock_sts_client = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'bedrock-data-automation':
                return mock_bda_client
            elif service_name == 'bedrock-data-automation-runtime':
                return mock_bda_runtime_client
            elif service_name == 'sts':
                return mock_sts_client

        mock_boto_client.side_effect = client_factory

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock Bedrock responses
        mock_bda_client.list_data_automation_projects.return_value = get_bedrock_list_projects_response("Freight_Audit_Agent")
        mock_bda_runtime_client.invoke_data_automation_async.return_value = get_bedrock_invoke_async_response()

        # Create event with URL-encoded key (spaces encoded as +)
        event = get_s3_eventbridge_event(
            bucket="test-bucket",
            key="Invoices/invoice+with+spaces.pdf"
        )

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        # Key should be decoded
        assert body['input_key'] == 'Invoices/invoice with spaces.pdf'

    @mock_aws
    @patch('invoice_processor_handler.boto3.client')
    def test_lambda_handler_default_profile_arn_construction(
        self,
        mock_boto_client,
        lambda_context,
        monkeypatch,
        aws_credentials
    ):
        """Test that profile ARN is auto-constructed when not provided"""
        # Set environment variables without DATA_AUTOMATION_PROFILE_ARN
        monkeypatch.setenv('PROJECT_NAME', 'Freight_Audit_Agent')
        monkeypatch.setenv('AWS_REGION', 'us-west-2')

        # Mock AWS clients
        mock_bda_client = Mock()
        mock_bda_runtime_client = Mock()
        mock_sts_client = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'bedrock-data-automation':
                return mock_bda_client
            elif service_name == 'bedrock-data-automation-runtime':
                return mock_bda_runtime_client
            elif service_name == 'sts':
                return mock_sts_client

        mock_boto_client.side_effect = client_factory

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {"Account": "987654321098"}

        # Mock Bedrock responses
        mock_bda_client.list_data_automation_projects.return_value = get_bedrock_list_projects_response("Freight_Audit_Agent")
        mock_bda_runtime_client.invoke_data_automation_async.return_value = get_bedrock_invoke_async_response()

        # Create event
        event = get_s3_eventbridge_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 200

        # Verify profile ARN was auto-constructed with correct region and account
        call_kwargs = mock_bda_runtime_client.invoke_data_automation_async.call_args[1]
        profile_arn = call_kwargs['dataAutomationProfileArn']
        assert 'us-west-2' in profile_arn
        assert '987654321098' in profile_arn
        assert 'data-automation-profile' in profile_arn
