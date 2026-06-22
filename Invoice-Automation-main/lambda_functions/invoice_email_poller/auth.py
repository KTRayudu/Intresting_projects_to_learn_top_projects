"""
Authentication module for Microsoft Graph API using MSAL
"""
import os
from msal import ConfidentialClientApplication


class GraphAuthenticator:
    """Handles authentication with Microsoft Graph API"""

    def __init__(self, client_id, client_secret, tenant_id):
        """
        Initialize the authenticator

        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]

        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )

    def get_access_token(self):
        """
        Acquire an access token for Microsoft Graph API

        Returns:
            str: Access token

        Raises:
            Exception: If token acquisition fails
        """
        result = self.app.acquire_token_for_client(scopes=self.scopes)

        if "access_token" in result:
            return result["access_token"]
        else:
            error = result.get("error", "Unknown error")
            error_description = result.get("error_description", "No description")
            raise Exception(f"Failed to acquire token: {error} - {error_description}")
