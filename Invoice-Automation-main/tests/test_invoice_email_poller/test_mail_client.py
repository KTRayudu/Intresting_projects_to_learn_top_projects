"""
Unit tests for invoice_email_poller/mail_client.py
Tests GraphMailClient class for Microsoft Graph Mail API operations
"""
import pytest
import sys
import os
import responses

# Add lambda function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda_functions/invoice_email_poller'))

from mail_client import GraphMailClient
from tests.fixtures.sample_responses import (
    get_graph_unread_emails_response,
    get_graph_email_attachments_response,
    get_graph_attachment_content_response,
    get_graph_inline_attachment_response
)


class TestGraphMailClient:
    """Test cases for GraphMailClient class"""

    @pytest.fixture
    def mail_client(self):
        """Create GraphMailClient instance for testing"""
        return GraphMailClient(
            access_token="fake-access-token",
            mailbox_email="test@example.com"
        )

    def test_init_sets_correct_attributes(self, mail_client):
        """Test that __init__ correctly initializes client attributes"""
        assert mail_client.access_token == "fake-access-token"
        assert mail_client.mailbox_email == "test@example.com"
        assert mail_client.base_url == "https://graph.microsoft.com/v1.0"
        assert "Authorization" in mail_client.headers
        assert mail_client.headers["Authorization"] == "Bearer fake-access-token"

    @responses.activate
    def test_get_unread_emails_success(self, mail_client):
        """Test successful retrieval of unread emails"""
        # Mock Microsoft Graph API response
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages",
            json=get_graph_unread_emails_response(),
            status=200
        )

        emails = mail_client.get_unread_emails()

        assert len(emails) == 2
        assert emails[0]["id"] == "email-id-001"
        assert emails[0]["subject"] == "Invoice from ACME Shipping"
        assert emails[1]["id"] == "email-id-002"

    @responses.activate
    def test_get_unread_emails_empty_response(self, mail_client):
        """Test handling of empty unread emails response"""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages",
            json={"value": []},
            status=200
        )

        emails = mail_client.get_unread_emails()

        assert len(emails) == 0

    @responses.activate
    def test_get_unread_emails_api_error(self, mail_client):
        """Test handling of API error when retrieving emails"""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages",
            json={"error": {"message": "Unauthorized"}},
            status=401
        )

        with pytest.raises(Exception) as exc_info:
            mail_client.get_unread_emails()

        assert "Failed to retrieve emails" in str(exc_info.value)
        assert "401" in str(exc_info.value)

    @responses.activate
    def test_get_unread_emails_custom_parameters(self, mail_client):
        """Test get_unread_emails with custom folder and top parameters"""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/sentitems/messages",
            json={"value": []},
            status=200
        )

        emails = mail_client.get_unread_emails(folder="sentitems", top=10)

        assert len(emails) == 0
        assert len(responses.calls) == 1

    @responses.activate
    def test_get_email_attachments_success(self, mail_client):
        """Test successful retrieval of email attachments"""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001/attachments",
            json=get_graph_email_attachments_response(),
            status=200
        )

        attachments = mail_client.get_email_attachments("email-id-001")

        assert len(attachments) == 1
        assert attachments[0]["id"] == "attachment-id-001"
        assert attachments[0]["name"] == "invoice_12345.pdf"
        assert attachments[0]["@odata.type"] == "#microsoft.graph.fileAttachment"

    @responses.activate
    def test_get_email_attachments_api_error(self, mail_client):
        """Test handling of API error when retrieving attachments"""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001/attachments",
            json={"error": {"message": "Not found"}},
            status=404
        )

        with pytest.raises(Exception) as exc_info:
            mail_client.get_email_attachments("email-id-001")

        assert "Failed to retrieve attachments" in str(exc_info.value)

    @responses.activate
    def test_get_attachment_content_success(self, mail_client):
        """Test successful retrieval of attachment content"""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001/attachments/attachment-id-001",
            json=get_graph_attachment_content_response(),
            status=200
        )

        content = mail_client.get_attachment_content("email-id-001", "attachment-id-001")

        assert content is not None
        assert len(content) > 0
        # Content should be base64 encoded string
        assert isinstance(content, str)

    @responses.activate
    def test_get_attachment_content_no_content_bytes(self, mail_client):
        """Test handling of attachment response without contentBytes"""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001/attachments/attachment-id-001",
            json={"id": "attachment-id-001", "name": "test.pdf"},
            status=200
        )

        with pytest.raises(Exception) as exc_info:
            mail_client.get_attachment_content("email-id-001", "attachment-id-001")

        assert "No content bytes" in str(exc_info.value)

    @responses.activate
    def test_get_attachment_content_api_error(self, mail_client):
        """Test handling of API error when retrieving attachment content"""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001/attachments/attachment-id-001",
            json={"error": {"message": "Not found"}},
            status=404
        )

        with pytest.raises(Exception) as exc_info:
            mail_client.get_attachment_content("email-id-001", "attachment-id-001")

        assert "Failed to get attachment content" in str(exc_info.value)

    @responses.activate
    def test_mark_as_read_success(self, mail_client):
        """Test successfully marking email as read"""
        responses.add(
            responses.PATCH,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001",
            json={},
            status=200
        )

        # Should not raise exception
        mail_client.mark_as_read("email-id-001")

        assert len(responses.calls) == 1
        assert responses.calls[0].request.body == b'{"isRead": true}'

    @responses.activate
    def test_mark_as_read_status_204(self, mail_client):
        """Test marking email as read with 204 No Content response"""
        responses.add(
            responses.PATCH,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001",
            status=204
        )

        # Should not raise exception
        mail_client.mark_as_read("email-id-001")

        assert len(responses.calls) == 1

    @responses.activate
    def test_mark_as_read_api_error(self, mail_client):
        """Test handling of API error when marking email as read"""
        responses.add(
            responses.PATCH,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001",
            json={"error": {"message": "Forbidden"}},
            status=403
        )

        with pytest.raises(Exception) as exc_info:
            mail_client.mark_as_read("email-id-001")

        assert "Failed to mark email as read" in str(exc_info.value)

    @responses.activate
    def test_delete_message_success(self, mail_client):
        """Test successfully deleting an email message"""
        responses.add(
            responses.DELETE,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001",
            status=204
        )

        # Should not raise exception
        mail_client.delete_message("email-id-001")

        assert len(responses.calls) == 1

    @responses.activate
    def test_delete_message_api_error(self, mail_client):
        """Test handling of API error when deleting email"""
        responses.add(
            responses.DELETE,
            "https://graph.microsoft.com/v1.0/users/test@example.com/messages/email-id-001",
            json={"error": {"message": "Not found"}},
            status=404
        )

        with pytest.raises(Exception) as exc_info:
            mail_client.delete_message("email-id-001")

        assert "Failed to delete email" in str(exc_info.value)
