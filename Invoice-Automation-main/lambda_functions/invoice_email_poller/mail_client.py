"""
Microsoft Graph Mail Client for retrieving and managing emails
"""
import requests
import os
from pathlib import Path


class GraphMailClient:
    """Client for interacting with Microsoft Graph Mail API"""

    def __init__(self, access_token, mailbox_email):
        """
        Initialize the mail client

        Args:
            access_token: Valid access token for Microsoft Graph API
            mailbox_email: Email address of the mailbox to access
        """
        self.access_token = access_token
        self.mailbox_email = mailbox_email
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def get_unread_emails(self, folder="inbox", top=50):
        """
        Retrieve unread emails from a specific folder

        Args:
            folder: Folder name (default: inbox)
            top: Maximum number of emails to retrieve (default: 50)

        Returns:
            list: List of unread email messages

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/users/{self.mailbox_email}/mailFolders/{folder}/messages"
        params = {
            "$filter": "isRead eq false",
            "$top": top,
            "$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,bodyPreview",
            "$orderby": "receivedDateTime desc"
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            data = response.json()
            return data.get("value", [])
        else:
            raise Exception(f"Failed to retrieve emails: {response.status_code} - {response.text}")

    def get_email_attachments(self, message_id):
        """
        Retrieve attachments for a specific email message

        Args:
            message_id: The ID of the email message

        Returns:
            list: List of attachment objects

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/users/{self.mailbox_email}/messages/{message_id}/attachments"
        params = {
            "$select": "id,name,contentType,size"
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            data = response.json()
            return data.get("value", [])
        else:
            raise Exception(f"Failed to retrieve attachments: {response.status_code} - {response.text}")

    def get_attachment_content(self, message_id, attachment_id):
        """
        Get attachment content as base64 string without saving to file

        Args:
            message_id: The ID of the email message
            attachment_id: The ID of the attachment

        Returns:
            str: Base64 encoded content of the attachment

        Raises:
            Exception: If download fails
        """
        url = f"{self.base_url}/users/{self.mailbox_email}/messages/{message_id}/attachments/{attachment_id}"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            attachment_data = response.json()
            content_bytes = attachment_data.get("contentBytes")

            if content_bytes:
                return content_bytes
            else:
                raise Exception("No content bytes in attachment response")
        else:
            raise Exception(f"Failed to get attachment content: {response.status_code} - {response.text}")

    def download_attachment(self, message_id, attachment_id, attachment_name, save_dir="attachments"):
        """
        Download a specific attachment from an email

        Args:
            message_id: The ID of the email message
            attachment_id: The ID of the attachment
            attachment_name: The name of the attachment file
            save_dir: Directory to save the attachment (default: attachments)

        Returns:
            str: Path to the saved attachment file

        Raises:
            Exception: If download fails
        """
        url = f"{self.base_url}/users/{self.mailbox_email}/messages/{message_id}/attachments/{attachment_id}"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            attachment_data = response.json()
            content_bytes = attachment_data.get("contentBytes")

            if content_bytes:
                # Create save directory if it doesn't exist
                Path(save_dir).mkdir(parents=True, exist_ok=True)

                # Sanitize filename
                safe_filename = "".join(c for c in attachment_name if c.isalnum() or c in (' ', '.', '_', '-')).strip()
                file_path = os.path.join(save_dir, safe_filename)

                # Handle duplicate filenames
                counter = 1
                base_name, extension = os.path.splitext(safe_filename)
                while os.path.exists(file_path):
                    safe_filename = f"{base_name}_{counter}{extension}"
                    file_path = os.path.join(save_dir, safe_filename)
                    counter += 1

                # Decode and save the attachment
                import base64
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(content_bytes))

                return file_path
            else:
                raise Exception("No content bytes in attachment response")
        else:
            raise Exception(f"Failed to download attachment: {response.status_code} - {response.text}")

    def download_all_attachments(self, message_id, save_dir="attachments"):
        """
        Download all attachments from a specific email message

        Args:
            message_id: The ID of the email message
            save_dir: Directory to save attachments (default: attachments)

        Returns:
            list: List of paths to saved attachment files
        """
        attachments = self.get_email_attachments(message_id)
        downloaded_files = []

        for attachment in attachments:
            # Only process file attachments (not item attachments)
            if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
                attachment_id = attachment.get("id")
                attachment_name = attachment.get("name", "unnamed_attachment")

                try:
                    file_path = self.download_attachment(
                        message_id,
                        attachment_id,
                        attachment_name,
                        save_dir
                    )
                    downloaded_files.append(file_path)
                    print(f"  Downloaded: {file_path}")
                except Exception as e:
                    print(f"  Failed to download {attachment_name}: {e}")

        return downloaded_files

    def mark_as_read(self, message_id):
        """
        Mark an email message as read

        Args:
            message_id: The ID of the email message

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/users/{self.mailbox_email}/messages/{message_id}"
        data = {"isRead": True}

        response = requests.patch(url, headers=self.headers, json=data)

        if response.status_code not in [200, 204]:
            raise Exception(f"Failed to mark email as read: {response.status_code} - {response.text}")

    def delete_message(self, message_id):
        """
        Delete an email message

        Args:
            message_id: The ID of the email message

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/users/{self.mailbox_email}/messages/{message_id}"

        response = requests.delete(url, headers=self.headers)

        if response.status_code not in [200, 204]:
            raise Exception(f"Failed to delete email: {response.status_code} - {response.text}")

    def delete_old_emails(self, days_old, folder="inbox"):
        """
        Delete emails older than a specified number of days

        Args:
            days_old: Number of days - emails older than this will be deleted
            folder: Folder name (default: inbox)

        Returns:
            int: Number of emails deleted

        Raises:
            Exception: If API request fails
        """
        from datetime import datetime, timedelta, timezone

        # Calculate the cutoff date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        cutoff_date_str = cutoff_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Query for old emails
        url = f"{self.base_url}/users/{self.mailbox_email}/mailFolders/{folder}/messages"
        params = {
            "$filter": f"receivedDateTime lt {cutoff_date_str}",
            "$select": "id,subject,receivedDateTime",
            "$top": 100  # Process in batches of 100
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Failed to retrieve old emails: {response.status_code} - {response.text}")

        data = response.json()
        old_emails = data.get("value", [])
        deleted_count = 0

        for email in old_emails:
            email_id = email.get("id")
            subject = email.get("subject", "(No Subject)")
            received = email.get("receivedDateTime", "Unknown")

            try:
                self.delete_message(email_id)
                deleted_count += 1
                print(f"  Deleted old email: '{subject}' (received: {received})")
            except Exception as e:
                print(f"  Failed to delete email '{subject}': {e}")

        return deleted_count
