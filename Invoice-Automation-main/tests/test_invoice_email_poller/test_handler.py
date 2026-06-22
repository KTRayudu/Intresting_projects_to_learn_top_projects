"""
Unit tests for invoice_email_poller/handler.py
Tests Lambda handler for email polling and PDF upload to S3
"""
import pytest
import sys
import os
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3
import responses
import importlib.util

# Load the specific handler module to avoid import conflicts
handler_path = os.path.join(os.path.dirname(__file__), '../../lambda_functions/invoice_email_poller/handler.py')
spec = importlib.util.spec_from_file_location("email_poller_handler", handler_path)
email_poller_handler = importlib.util.module_from_spec(spec)
sys.modules['email_poller_handler'] = email_poller_handler
spec.loader.exec_module(email_poller_handler)

lambda_handler = email_poller_handler.lambda_handler
sanitize_metadata_value = email_poller_handler.sanitize_metadata_value
from tests.fixtures.sample_responses import (
    get_graph_unread_emails_response,
    get_graph_email_attachments_response,
    get_graph_attachment_content_response,
    get_graph_inline_attachment_response
)


class TestSanitizeMetadataValue:
    """Test cases for sanitize_metadata_value helper function"""

    def test_sanitize_removes_newlines(self):
        """Test that newlines are removed"""
        input_value = "Line 1\nLine 2\r\nLine 3"
        result = sanitize_metadata_value(input_value)
        assert "\n" not in result
        assert "\r" not in result
        assert result == "Line 1 Line 2 Line 3"

    def test_sanitize_removes_tabs(self):
        """Test that tabs are removed"""
        input_value = "Column1\tColumn2\tColumn3"
        result = sanitize_metadata_value(input_value)
        assert "\t" not in result
        assert result == "Column1 Column2 Column3"

    def test_sanitize_removes_control_characters(self):
        """Test that control characters are removed"""
        input_value = "Text\x00with\x01control\x1fchars"
        result = sanitize_metadata_value(input_value)
        # Control characters should be replaced with spaces
        assert "\x00" not in result
        assert "\x01" not in result

    def test_sanitize_collapses_multiple_spaces(self):
        """Test that multiple spaces are collapsed to single space"""
        input_value = "Text    with     many      spaces"
        result = sanitize_metadata_value(input_value)
        assert result == "Text with many spaces"

    def test_sanitize_empty_string(self):
        """Test handling of empty string"""
        result = sanitize_metadata_value("")
        assert result == ""

    def test_sanitize_none_value(self):
        """Test handling of None value"""
        result = sanitize_metadata_value(None)
        assert result == ""

    def test_sanitize_preserves_normal_text(self):
        """Test that normal text is preserved"""
        input_value = "This is normal text with punctuation!"
        result = sanitize_metadata_value(input_value)
        assert result == input_value


class TestLambdaHandler:
    """Test cases for lambda_handler function"""

    @mock_aws
    @responses.activate
    def test_lambda_handler_success(
        self,
        lambda_context,
        mock_env_vars_email_poller,
        aws_credentials
    ):
        """Test successful email processing and S3 upload"""
        # Create S3 bucket and patch the handler's s3_client
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        # Patch the s3_client in the handler module
        email_poller_handler.s3_client = s3_client

        # Mock Microsoft Graph API responses
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/mailFolders/inbox/messages",
            json=get_graph_unread_emails_response(),
            status=200
        )

        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-001/attachments",
            json=get_graph_email_attachments_response(),
            status=200
        )

        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-001/attachments/attachment-id-001",
            json=get_graph_attachment_content_response(),
            status=200
        )

        responses.add(
            responses.PATCH,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-001",
            json={},
            status=200
        )

        # Repeat for second email
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-002/attachments",
            json=get_graph_email_attachments_response(),
            status=200
        )

        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-002/attachments/attachment-id-001",
            json=get_graph_attachment_content_response(),
            status=200
        )

        responses.add(
            responses.PATCH,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-002",
            json={},
            status=200
        )

        # Mock MSAL token acquisition
        with patch('email_poller_handler.GraphAuthenticator') as mock_auth_class:
            mock_auth_instance = Mock()
            mock_auth_instance.get_access_token.return_value = "fake-token"
            mock_auth_class.return_value = mock_auth_instance

            # Execute handler
            response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['emails_processed'] == 2
        assert body['pdfs_uploaded_to_s3'] == 2
        assert len(body['uploaded_files']) == 2

        # Verify S3 objects were created
        objects = s3_client.list_objects_v2(Bucket='test-bucket', Prefix='Invoices/')
        assert objects['KeyCount'] == 2

    def test_lambda_handler_missing_env_vars(self, lambda_context, aws_credentials):
        """Test handler fails gracefully when environment variables are missing"""
        # Don't set any environment variables
        response = lambda_handler({}, lambda_context)

        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Missing required environment variables' in body['error']

    @mock_aws
    @responses.activate
    def test_lambda_handler_skips_inline_attachments(
        self,
        lambda_context,
        mock_env_vars_email_poller,
        aws_credentials
    ):
        """Test that inline attachments (signature images) are skipped"""
        # Create S3 bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        # Mock email with inline attachment
        email_response = {
            "value": [
                {
                    "id": "email-id-001",
                    "subject": "Test Email",
                    "bodyPreview": "Test body",
                    "from": {
                        "emailAddress": {
                            "name": "John Doe",
                            "address": "john@example.com"
                        }
                    },
                    "receivedDateTime": "2024-01-15T09:00:00Z",
                    "hasAttachments": True
                }
            ]
        }

        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/mailFolders/inbox/messages",
            json=email_response,
            status=200
        )

        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-001/attachments",
            json=get_graph_inline_attachment_response(),
            status=200
        )

        responses.add(
            responses.PATCH,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-001",
            json={},
            status=200
        )

        # Mock MSAL token acquisition
        with patch('email_poller_handler.GraphAuthenticator') as mock_auth_class:
            mock_auth_instance = Mock()
            mock_auth_instance.get_access_token.return_value = "fake-token"
            mock_auth_class.return_value = mock_auth_instance

            # Execute handler
            response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['inline_attachments_skipped'] == 1
        assert body['pdfs_uploaded_to_s3'] == 0

    @mock_aws
    @responses.activate
    def test_lambda_handler_no_unread_emails(
        self,
        lambda_context,
        mock_env_vars_email_poller,
        aws_credentials
    ):
        """Test handler when there are no unread emails"""
        # Create S3 bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        # Mock empty response
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/mailFolders/inbox/messages",
            json={"value": []},
            status=200
        )

        # Mock MSAL token acquisition
        with patch('email_poller_handler.GraphAuthenticator') as mock_auth_class:
            mock_auth_instance = Mock()
            mock_auth_instance.get_access_token.return_value = "fake-token"
            mock_auth_class.return_value = mock_auth_instance

            # Execute handler
            response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['emails_processed'] == 0
        assert body['pdfs_uploaded_to_s3'] == 0
        assert body['unread_emails_found'] == 0

    @responses.activate
    def test_lambda_handler_authentication_failure(
        self,
        lambda_context,
        mock_env_vars_email_poller,
        aws_credentials
    ):
        """Test handler when authentication fails"""
        # Mock MSAL token acquisition failure
        with patch('email_poller_handler.GraphAuthenticator') as mock_auth_class:
            mock_auth_instance = Mock()
            mock_auth_instance.get_access_token.side_effect = Exception("Authentication failed")
            mock_auth_class.return_value = mock_auth_instance

            # Execute handler
            response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body

    @mock_aws
    @responses.activate
    def test_lambda_handler_s3_metadata_sanitization(
        self,
        lambda_context,
        mock_env_vars_email_poller,
        aws_credentials
    ):
        """Test that S3 metadata values are sanitized"""
        # Create S3 bucket and patch handler's s3_client
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        email_poller_handler.s3_client = s3_client

        # Mock email with problematic metadata (newlines, etc.)
        email_response = {
            "value": [
                {
                    "id": "email-id-001",
                    "subject": "Subject\nwith\nnewlines",
                    "bodyPreview": "Body\r\nwith\r\ncarriage\r\nreturns",
                    "from": {
                        "emailAddress": {
                            "name": "John\tDoe",
                            "address": "john@example.com"
                        }
                    },
                    "receivedDateTime": "2024-01-15T09:00:00Z",
                    "hasAttachments": True
                }
            ]
        }

        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/mailFolders/inbox/messages",
            json=email_response,
            status=200
        )

        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-001/attachments",
            json=get_graph_email_attachments_response(),
            status=200
        )

        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-001/attachments/attachment-id-001",
            json=get_graph_attachment_content_response(),
            status=200
        )

        responses.add(
            responses.PATCH,
            "https://graph.microsoft.com/v1.0/users/invoices@testcompany.com/messages/email-id-001",
            json={},
            status=200
        )

        # Mock MSAL token acquisition
        with patch('email_poller_handler.GraphAuthenticator') as mock_auth_class:
            mock_auth_instance = Mock()
            mock_auth_instance.get_access_token.return_value = "fake-token"
            mock_auth_class.return_value = mock_auth_instance

            # Execute handler
            response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 200

        # Verify S3 metadata is sanitized
        objects = s3_client.list_objects_v2(Bucket='test-bucket', Prefix='Invoices/')
        s3_key = objects['Contents'][0]['Key']
        head_response = s3_client.head_object(Bucket='test-bucket', Key=s3_key)
        metadata = head_response['Metadata']

        # Check that problematic characters are removed/replaced
        assert '\n' not in metadata.get('email-subject', '')
        assert '\r' not in metadata.get('email-body-preview', '')
        assert '\t' not in metadata.get('email-sender-name', '')
