"""
Unit tests for gvp_invoice_publisher/handler.py
Tests Lambda handler for publishing invoice data to GVP API
"""
import pytest
import sys
import os
import json
from unittest.mock import Mock, patch
from moto import mock_aws
import boto3
import importlib.util

# Load the specific handler module to avoid import conflicts
handler_path = os.path.join(os.path.dirname(__file__), '../../lambda_functions/gvp_invoice_publisher/handler.py')
spec = importlib.util.spec_from_file_location("gvp_publisher_handler", handler_path)
gvp_publisher_handler = importlib.util.module_from_spec(spec)
sys.modules['gvp_publisher_handler'] = gvp_publisher_handler
spec.loader.exec_module(gvp_publisher_handler)

lambda_handler = gvp_publisher_handler.lambda_handler
from tests.fixtures.sample_events import get_bedrock_completion_event
from tests.fixtures.sample_responses import (
    get_bedrock_job_metadata,
    get_bedrock_inference_results,
    get_s3_object_metadata,
    get_gvp_auth_token_response,
    get_gvp_post_invoice_response
)


class TestLambdaHandler:
    """Test cases for lambda_handler function"""

    @mock_aws
    @patch('gvp_publisher_handler.post_invoice_to_gvp')
    @patch('gvp_publisher_handler.get_gvp_auth_token')
    @patch('gvp_publisher_handler.get_s3_object_metadata')
    @patch('gvp_publisher_handler.read_json_content_from_s3')
    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_success(
        self,
        mock_get_custom_path,
        mock_read_s3_json,
        mock_get_metadata,
        mock_get_token,
        mock_post_invoice,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test successful end-to-end invoice processing and GVP posting"""
        # Mock helper function responses
        mock_get_custom_path.return_value = "s3://test-bucket/lambda-output/custom-output.json"
        mock_read_s3_json.return_value = get_bedrock_inference_results()
        mock_get_metadata.return_value = get_s3_object_metadata()
        mock_get_token.return_value = get_gvp_auth_token_response()
        mock_post_invoice.return_value = get_gvp_post_invoice_response()

        # Create Bedrock completion event
        event = get_bedrock_completion_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Successfully posted invoice to GVP'
        assert body['invoice_number'] == 'INV-12345'
        assert body['carrier'] == 'ACME Shipping'
        assert 'gvp_response' in body

        # Verify GVP token was obtained
        mock_get_token.assert_called_once_with('test-login-id', 'test-password')

        # Verify invoice was posted to GVP
        mock_post_invoice.assert_called_once()
        call_args = mock_post_invoice.call_args[0]
        assert call_args[0]['InvoiceNumber'] == 'INV-12345'  # inference_results
        assert call_args[1] == get_gvp_auth_token_response()  # token
        assert call_args[2] == 'john.doe@acmeshipping.com'  # mailbox_name

    def test_lambda_handler_invalid_event_structure(
        self,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test handling of invalid event structure"""
        # Event missing required fields
        event = {"invalid": "structure"}

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Invalid event structure' in body['error']

    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_missing_gvp_credentials(
        self,
        mock_get_custom_path,
        lambda_context,
        monkeypatch,
        aws_credentials
    ):
        """Test handling of missing GVP credentials"""
        # Don't set GVP credentials
        monkeypatch.delenv('GVP_LOGIN_ID', raising=False)
        monkeypatch.delenv('GVP_PASSWORD', raising=False)

        # Mock successful Bedrock output retrieval
        mock_get_custom_path.return_value = "s3://test-bucket/output.json"

        with patch('handler.read_json_content_from_s3') as mock_read:
            mock_read.return_value = get_bedrock_inference_results()

            event = get_bedrock_completion_event()

            # Execute handler
            response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Missing GVP credentials' in body['error']

    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_bedrock_output_error(
        self,
        mock_get_custom_path,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test handling of error retrieving Bedrock output"""
        # Mock error in getting custom output path
        mock_get_custom_path.side_effect = Exception("S3 access error")

        event = get_bedrock_completion_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Error retrieving Bedrock inference results' in body['error']

    @patch('gvp_publisher_handler.read_json_content_from_s3')
    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_no_inference_results(
        self,
        mock_get_custom_path,
        mock_read_s3_json,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test handling of empty inference results"""
        mock_get_custom_path.return_value = "s3://test-bucket/output.json"
        # Mock empty inference results
        mock_read_s3_json.return_value = {"inference_result": {}}

        event = get_bedrock_completion_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'No inference results found' in body['error_details']

    @patch('gvp_publisher_handler.post_invoice_to_gvp')
    @patch('gvp_publisher_handler.get_gvp_auth_token')
    @patch('gvp_publisher_handler.get_s3_object_metadata')
    @patch('gvp_publisher_handler.read_json_content_from_s3')
    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_gvp_auth_failure(
        self,
        mock_get_custom_path,
        mock_read_s3_json,
        mock_get_metadata,
        mock_get_token,
        mock_post_invoice,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test handling of GVP authentication failure"""
        mock_get_custom_path.return_value = "s3://test-bucket/output.json"
        mock_read_s3_json.return_value = get_bedrock_inference_results()
        mock_get_metadata.return_value = get_s3_object_metadata()
        # Mock authentication failure
        mock_get_token.side_effect = Exception("Authentication failed")

        event = get_bedrock_completion_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Error posting invoice to GVP' in body['error']

    @patch('gvp_publisher_handler.post_invoice_to_gvp')
    @patch('gvp_publisher_handler.get_gvp_auth_token')
    @patch('gvp_publisher_handler.get_s3_object_metadata')
    @patch('gvp_publisher_handler.read_json_content_from_s3')
    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_gvp_post_failure(
        self,
        mock_get_custom_path,
        mock_read_s3_json,
        mock_get_metadata,
        mock_get_token,
        mock_post_invoice,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test handling of GVP API post error"""
        mock_get_custom_path.return_value = "s3://test-bucket/output.json"
        mock_read_s3_json.return_value = get_bedrock_inference_results()
        mock_get_metadata.return_value = get_s3_object_metadata()
        mock_get_token.return_value = get_gvp_auth_token_response()
        # Mock post failure
        mock_post_invoice.side_effect = Exception("GVP API error: Invalid invoice")

        event = get_bedrock_completion_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Error posting invoice to GVP' in body['error']
        assert 'GVP API error' in body['error_details']

    @patch('gvp_publisher_handler.post_invoice_to_gvp')
    @patch('gvp_publisher_handler.get_gvp_auth_token')
    @patch('gvp_publisher_handler.get_s3_object_metadata')
    @patch('gvp_publisher_handler.read_json_content_from_s3')
    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_metadata_retrieval_failure_continues(
        self,
        mock_get_custom_path,
        mock_read_s3_json,
        mock_get_metadata,
        mock_get_token,
        mock_post_invoice,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test that handler continues even if S3 metadata retrieval fails"""
        mock_get_custom_path.return_value = "s3://test-bucket/output.json"
        mock_read_s3_json.return_value = get_bedrock_inference_results()
        # Mock metadata retrieval failure
        mock_get_metadata.side_effect = Exception("Metadata error")
        mock_get_token.return_value = get_gvp_auth_token_response()
        mock_post_invoice.return_value = get_gvp_post_invoice_response()

        event = get_bedrock_completion_event()

        # Execute handler - should succeed despite metadata error
        response = lambda_handler(event, lambda_context)

        # Assertions - should still succeed
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Successfully posted invoice to GVP'

        # Verify invoice was posted with empty mailbox
        mock_post_invoice.assert_called_once()
        call_args = mock_post_invoice.call_args[0]
        assert call_args[2] == ''  # empty mailbox_name

    @patch('gvp_publisher_handler.post_invoice_to_gvp')
    @patch('gvp_publisher_handler.get_gvp_auth_token')
    @patch('gvp_publisher_handler.get_s3_object_metadata')
    @patch('gvp_publisher_handler.read_json_content_from_s3')
    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_url_encoded_keys(
        self,
        mock_get_custom_path,
        mock_read_s3_json,
        mock_get_metadata,
        mock_get_token,
        mock_post_invoice,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test that URL-encoded S3 keys are properly decoded"""
        mock_get_custom_path.return_value = "s3://test-bucket/output.json"
        mock_read_s3_json.return_value = get_bedrock_inference_results()
        mock_get_metadata.return_value = get_s3_object_metadata()
        mock_get_token.return_value = get_gvp_auth_token_response()
        mock_post_invoice.return_value = get_gvp_post_invoice_response()

        # Create event with URL-encoded keys
        event = get_bedrock_completion_event(
            input_bucket="test-bucket",
            input_key="Invoices/invoice+with+spaces.pdf",
            output_bucket="test-bucket",
            output_key="lambda-output/job+123"
        )

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Should succeed and properly decode keys
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'invoice with spaces' in body['input_s3_uri']

    @patch('gvp_publisher_handler.post_invoice_to_gvp')
    @patch('gvp_publisher_handler.get_gvp_auth_token')
    @patch('gvp_publisher_handler.get_s3_object_metadata')
    @patch('gvp_publisher_handler.read_json_content_from_s3')
    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_response_includes_input_uri(
        self,
        mock_get_custom_path,
        mock_read_s3_json,
        mock_get_metadata,
        mock_get_token,
        mock_post_invoice,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test that response includes input S3 URI for traceability"""
        mock_get_custom_path.return_value = "s3://test-bucket/output.json"
        mock_read_s3_json.return_value = get_bedrock_inference_results()
        mock_get_metadata.return_value = get_s3_object_metadata()
        mock_get_token.return_value = get_gvp_auth_token_response()
        mock_post_invoice.return_value = get_gvp_post_invoice_response()

        event = get_bedrock_completion_event(
            input_bucket="my-bucket",
            input_key="Invoices/invoice-123.pdf"
        )

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Verify input URI is in response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['input_s3_uri'] == 's3://my-bucket/Invoices/invoice-123.pdf'

    @patch('gvp_publisher_handler.post_invoice_to_gvp')
    @patch('gvp_publisher_handler.get_gvp_auth_token')
    @patch('gvp_publisher_handler.get_s3_object_metadata')
    @patch('gvp_publisher_handler.read_json_content_from_s3')
    @patch('gvp_publisher_handler.get_custom_output_path')
    def test_lambda_handler_extracts_mailbox_from_metadata(
        self,
        mock_get_custom_path,
        mock_read_s3_json,
        mock_get_metadata,
        mock_get_token,
        mock_post_invoice,
        lambda_context,
        mock_env_vars_gvp_publisher,
        aws_credentials
    ):
        """Test that mailbox name is extracted from S3 metadata"""
        mock_get_custom_path.return_value = "s3://test-bucket/output.json"
        mock_read_s3_json.return_value = get_bedrock_inference_results()

        # Custom metadata with specific sender
        custom_metadata = get_s3_object_metadata()
        custom_metadata['email-sender-email'] = 'specific-sender@example.com'
        mock_get_metadata.return_value = custom_metadata

        mock_get_token.return_value = get_gvp_auth_token_response()
        mock_post_invoice.return_value = get_gvp_post_invoice_response()

        event = get_bedrock_completion_event()

        # Execute handler
        response = lambda_handler(event, lambda_context)

        # Verify correct mailbox was passed to GVP
        assert response['statusCode'] == 200
        mock_post_invoice.assert_called_once()
        call_args = mock_post_invoice.call_args[0]
        assert call_args[2] == 'specific-sender@example.com'  # mailbox_name
