"""
Unit tests for gvp_invoice_publisher/gvp_client.py
Tests GVP API client functions and Bedrock output processing helpers
"""
import pytest
import sys
import os
import json
import responses
from unittest.mock import Mock, patch
from moto import mock_aws
import boto3

# Add lambda function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda_functions/gvp_invoice_publisher'))

from gvp_client import (
    read_json_content_from_s3,
    get_custom_output_path,
    get_s3_object_metadata,
    get_gvp_auth_token,
    post_invoice_to_gvp
)
from tests.fixtures.sample_responses import (
    get_bedrock_job_metadata,
    get_bedrock_inference_results,
    get_s3_object_metadata,
    get_gvp_auth_token_response,
    get_gvp_post_invoice_response
)


class TestReadJsonContentFromS3:
    """Test cases for read_json_content_from_s3 function"""

    @mock_aws
    def test_read_json_content_from_s3_success(self, aws_credentials):
        """Test successfully reading JSON from S3"""
        # Create S3 bucket and object
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        test_data = {"key": "value", "number": 42}
        s3_client.put_object(
            Bucket='test-bucket',
            Key='test-file.json',
            Body=json.dumps(test_data)
        )

        # Read JSON from S3
        result = read_json_content_from_s3('s3://test-bucket/test-file.json')

        assert result == test_data

    @mock_aws
    def test_read_json_content_from_s3_nested_path(self, aws_credentials):
        """Test reading JSON from S3 with nested path"""
        # Create S3 bucket and object
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        test_data = {"nested": "data"}
        s3_client.put_object(
            Bucket='test-bucket',
            Key='path/to/nested/file.json',
            Body=json.dumps(test_data)
        )

        # Read JSON from S3
        result = read_json_content_from_s3('s3://test-bucket/path/to/nested/file.json')

        assert result == test_data

    @mock_aws
    def test_read_json_content_from_s3_invalid_json(self, aws_credentials):
        """Test handling of invalid JSON content"""
        # Create S3 bucket and object with invalid JSON
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(
            Bucket='test-bucket',
            Key='invalid.json',
            Body='This is not JSON'
        )

        with pytest.raises(json.JSONDecodeError):
            read_json_content_from_s3('s3://test-bucket/invalid.json')


class TestGetCustomOutputPath:
    """Test cases for get_custom_output_path function"""

    @mock_aws
    def test_get_custom_output_path_success(self, aws_credentials):
        """Test successfully extracting custom output path from job metadata"""
        # Create S3 bucket and job metadata
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        job_metadata = get_bedrock_job_metadata()
        s3_client.put_object(
            Bucket='test-bucket',
            Key='lambda-output/job-123/job_metadata.json',
            Body=json.dumps(job_metadata)
        )

        # Get custom output path
        result = get_custom_output_path('s3://test-bucket/lambda-output/job-123/job_metadata.json')

        expected_path = "s3://test-bucket/lambda-output/test-job-id/custom-output.json"
        assert result == expected_path

    @mock_aws
    def test_get_custom_output_path_missing_field(self, aws_credentials):
        """Test handling of job metadata without custom_output_path"""
        # Create S3 bucket and incomplete job metadata
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        incomplete_metadata = {"output_metadata": [{"segment_metadata": [{}]}]}
        s3_client.put_object(
            Bucket='test-bucket',
            Key='lambda-output/job-123/job_metadata.json',
            Body=json.dumps(incomplete_metadata)
        )

        with pytest.raises(KeyError):
            get_custom_output_path('s3://test-bucket/lambda-output/job-123/job_metadata.json')


class TestGetS3ObjectMetadata:
    """Test cases for get_s3_object_metadata function"""

    @mock_aws
    def test_get_s3_object_metadata_success(self, aws_credentials):
        """Test successfully retrieving S3 object metadata"""
        # Create S3 bucket and object with metadata
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        metadata = get_s3_object_metadata()
        s3_client.put_object(
            Bucket='test-bucket',
            Key='test-file.pdf',
            Body=b'test content',
            Metadata=metadata
        )

        # Get metadata
        result = get_s3_object_metadata('test-bucket', 'test-file.pdf')

        assert result['email-id'] == 'email-id-001'
        assert result['email-sender-email'] == 'john.doe@acmeshipping.com'
        assert result['mailbox'] == 'invoices@testcompany.com'

    @mock_aws
    def test_get_s3_object_metadata_no_metadata(self, aws_credentials):
        """Test retrieving metadata from object without user metadata"""
        # Create S3 bucket and object without metadata
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(
            Bucket='test-bucket',
            Key='test-file.pdf',
            Body=b'test content'
        )

        # Get metadata (should return empty dict)
        result = get_s3_object_metadata('test-bucket', 'test-file.pdf')

        assert result == {}

    @mock_aws
    def test_get_s3_object_metadata_object_not_found(self, aws_credentials):
        """Test handling of non-existent S3 object"""
        # Create S3 bucket without object
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        # Should return empty dict on error
        result = get_s3_object_metadata('test-bucket', 'non-existent-file.pdf')

        assert result == {}


class TestGetGvpAuthToken:
    """Test cases for get_gvp_auth_token function"""

    @responses.activate
    def test_get_gvp_auth_token_success(self):
        """Test successful GVP authentication"""
        # Mock GVP auth API
        responses.add(
            responses.GET,
            "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken",
            body=f'"{get_gvp_auth_token_response()}"',
            status=200
        )

        token = get_gvp_auth_token("test-login", "test-password")

        assert token == get_gvp_auth_token_response()
        assert len(responses.calls) == 1

        # Verify headers were set correctly
        request_headers = responses.calls[0].request.headers
        assert request_headers['LoginID'] == 'test-login'
        assert request_headers['Pwd'] == 'test-password'

    @responses.activate
    def test_get_gvp_auth_token_unauthorized(self):
        """Test handling of authentication failure"""
        # Mock failed authentication
        responses.add(
            responses.GET,
            "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken",
            json={"error": "Unauthorized"},
            status=401
        )

        with pytest.raises(Exception):
            get_gvp_auth_token("invalid-login", "invalid-password")

    @responses.activate
    def test_get_gvp_auth_token_timeout(self):
        """Test handling of request timeout"""
        # Mock timeout
        import requests
        responses.add(
            responses.GET,
            "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken",
            body=requests.exceptions.Timeout()
        )

        with pytest.raises(requests.exceptions.RequestException):
            get_gvp_auth_token("test-login", "test-password")


class TestPostInvoiceToGvp:
    """Test cases for post_invoice_to_gvp function"""

    @responses.activate
    def test_post_invoice_to_gvp_success(self):
        """Test successfully posting invoice to GVP API"""
        # Mock GVP API response
        responses.add(
            responses.POST,
            "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice",
            json=get_gvp_post_invoice_response(),
            status=200
        )

        inference_results = get_bedrock_inference_results()['inference_result']
        token = "fake-token"
        mailbox_name = "test@example.com"
        pdf_path = "s3://bucket/file.pdf"

        response = post_invoice_to_gvp(inference_results, token, mailbox_name, pdf_path)

        assert response['status'] == 'success'
        assert len(responses.calls) == 1

        # Verify request headers
        request_headers = responses.calls[0].request.headers
        assert request_headers['tokenID'] == token
        assert request_headers['Content-Type'] == 'application/json'

        # Verify request body
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body['InvoiceNumber'] == 'INV-12345'
        assert request_body['Carrier'] == 'ACME Shipping'
        assert request_body['MailboxName'] == mailbox_name
        assert request_body['PDFFilePath'] == pdf_path

    @responses.activate
    def test_post_invoice_to_gvp_with_defaults(self):
        """Test posting invoice with default/missing fields"""
        # Mock GVP API response
        responses.add(
            responses.POST,
            "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice",
            json=get_gvp_post_invoice_response(),
            status=200
        )

        # Minimal inference results
        inference_results = {
            "InvoiceNumber": "INV-001",
            "Carrier": "Test Carrier"
        }
        token = "fake-token"

        response = post_invoice_to_gvp(inference_results, token)

        assert response['status'] == 'success'

        # Verify defaults were applied
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body['Currency'] == 'USD'  # Default
        assert request_body['PartyName'] == 'Novaadmin'  # Default
        assert 'auto-created from OCR data' in request_body['Comments']  # Default

    @responses.activate
    def test_post_invoice_to_gvp_api_error(self):
        """Test handling of GVP API error"""
        # Mock API error
        responses.add(
            responses.POST,
            "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice",
            json={"error": "Invalid invoice data"},
            status=400
        )

        inference_results = get_bedrock_inference_results()['inference_result']
        token = "fake-token"

        with pytest.raises(Exception):
            post_invoice_to_gvp(inference_results, token)

    @responses.activate
    def test_post_invoice_to_gvp_empty_response(self):
        """Test handling of empty response body"""
        # Mock empty response (204 No Content style)
        responses.add(
            responses.POST,
            "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice",
            body='',
            status=200
        )

        inference_results = get_bedrock_inference_results()['inference_result']
        token = "fake-token"

        response = post_invoice_to_gvp(inference_results, token)

        # Should return default success response
        assert response['status'] == 'success'
        assert response['status_code'] == 200

    @responses.activate
    def test_post_invoice_to_gvp_field_mapping(self):
        """Test that all invoice fields are correctly mapped"""
        # Mock GVP API response
        responses.add(
            responses.POST,
            "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice",
            json=get_gvp_post_invoice_response(),
            status=200
        )

        inference_results = get_bedrock_inference_results()['inference_result']
        token = "fake-token"

        post_invoice_to_gvp(inference_results, token, "mailbox@test.com", "s3://path")

        # Verify all fields were mapped correctly
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body['InvoiceDate'] == '2024-01-15'
        assert request_body['InvoiceNumber'] == 'INV-12345'
        assert request_body['Carrier'] == 'ACME Shipping'
        assert request_body['FeeAmount'] == '1250.00'
        assert request_body['BOLNumber'] == 'BOL-98765'
        assert request_body['OriginCity'] == 'Los Angeles'
        assert request_body['OriginState'] == 'CA'
        assert request_body['DestinationCity'] == 'New York'
        assert request_body['DestinationState'] == 'NY'
        assert request_body['STCC'] == '4011'
        assert request_body['LeadEquipmentID'] == 'TRUCK-456'
        assert request_body['ServiceDate'] == '2024-01-10'
