"""
Unit tests for invoice_email_poller/auth.py
Tests GraphAuthenticator class for Microsoft Graph API authentication
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add lambda function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda_functions/invoice_email_poller'))

from auth import GraphAuthenticator
from tests.fixtures.sample_responses import get_msal_token_response, get_msal_token_error_response


class TestGraphAuthenticator:
    """Test cases for GraphAuthenticator class"""

    def test_init_sets_correct_attributes(self):
        """Test that __init__ correctly initializes authenticator attributes"""
        client_id = "test-client-id"
        client_secret = "test-client-secret"
        tenant_id = "test-tenant-id"

        authenticator = GraphAuthenticator(client_id, client_secret, tenant_id)

        assert authenticator.client_id == client_id
        assert authenticator.client_secret == client_secret
        assert authenticator.tenant_id == tenant_id
        assert authenticator.authority == f"https://login.microsoftonline.com/{tenant_id}"
        assert authenticator.scopes == ["https://graph.microsoft.com/.default"]
        assert authenticator.app is not None

    def test_get_access_token_success(self):
        """Test successful token acquisition"""
        authenticator = GraphAuthenticator("client-id", "client-secret", "tenant-id")

        # Mock the MSAL app's token acquisition
        with patch.object(authenticator.app, 'acquire_token_for_client') as mock_acquire:
            mock_acquire.return_value = get_msal_token_response()

            token = authenticator.get_access_token()

            assert token == "fake-access-token-abc123xyz789"
            mock_acquire.assert_called_once_with(scopes=["https://graph.microsoft.com/.default"])

    def test_get_access_token_failure(self):
        """Test token acquisition failure raises exception"""
        authenticator = GraphAuthenticator("client-id", "client-secret", "tenant-id")

        # Mock failed token acquisition
        with patch.object(authenticator.app, 'acquire_token_for_client') as mock_acquire:
            mock_acquire.return_value = get_msal_token_error_response()

            with pytest.raises(Exception) as exc_info:
                authenticator.get_access_token()

            assert "Failed to acquire token" in str(exc_info.value)
            assert "invalid_client" in str(exc_info.value)

    def test_get_access_token_no_token_in_response(self):
        """Test handling of response without access_token field"""
        authenticator = GraphAuthenticator("client-id", "client-secret", "tenant-id")

        # Mock response without access_token
        with patch.object(authenticator.app, 'acquire_token_for_client') as mock_acquire:
            mock_acquire.return_value = {"some_other_field": "value"}

            with pytest.raises(Exception) as exc_info:
                authenticator.get_access_token()

            assert "Failed to acquire token" in str(exc_info.value)

    def test_authority_url_constructed_correctly(self):
        """Test that authority URL is correctly constructed with tenant ID"""
        tenant_id = "my-tenant-12345"
        authenticator = GraphAuthenticator("client-id", "client-secret", tenant_id)

        expected_authority = f"https://login.microsoftonline.com/{tenant_id}"
        assert authenticator.authority == expected_authority
