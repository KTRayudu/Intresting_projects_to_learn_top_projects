# GetMails - Microsoft 365 Mailbox Monitor

A Python application that polls a Microsoft 365 mailbox using the Microsoft Graph API to monitor unread emails and download attachments.

## Features

- Authenticate with Microsoft Graph API using Azure AD application credentials
- Poll mailbox at configurable intervals
- Retrieve unread emails from inbox
- Download email attachments automatically
- Sanitize filenames and handle duplicates
- Display email metadata (subject, sender, received date)

## Prerequisites

- Python 3.7 or higher
- Microsoft 365 account
- Azure AD application registration with appropriate permissions

## Azure AD Application Setup

Before using this application, you need to register an application in Azure AD:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Enter a name (e.g., "GetMails App")
5. Select **Accounts in this organizational directory only**
6. Click **Register**

### Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Select **Application permissions** (not Delegated)
5. Add the following permissions:
   - `Mail.ReadWrite` - Required for reading mail, marking as read, and deleting emails
6. Click **Grant admin consent** for your organization

### Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and select expiration
4. Click **Add**
5. **Copy the secret value immediately** (it won't be shown again)

### Get Application Details

Note down the following from the **Overview** page:
- **Application (client) ID**
- **Directory (tenant) ID**

### Restrict Access to a Single Mailbox (Application Access Policy)

By default, application permissions grant access to all mailboxes in your organization. To restrict the application to access only a specific mailbox, you need to configure an Application Access Policy using Exchange Online PowerShell.

**Prerequisites:**
- Exchange Online PowerShell module installed
- Global Administrator or Exchange Administrator role

**Steps:**

1. Install Exchange Online PowerShell module (if not already installed):
```powershell
Install-Module -Name ExchangeOnlineManagement
```

2. Connect to Exchange Online:
```powershell
Connect-ExchangeOnline
```

3. Create a mail-enabled security group (or use an existing one):
```powershell
# Create a new mail-enabled security group
New-DistributionGroup -Name "GetMails Access Group" -Type "Security"

# Add the target mailbox to the group
Add-DistributionGroupMember -Identity "GetMails Access Group" -Member "user@yourdomain.com"
```

4. Create an Application Access Policy to restrict the app to this group:
```powershell
New-ApplicationAccessPolicy -AppId "your_client_id_here" -PolicyScopeGroupId "GetMails Access Group" -AccessRight RestrictAccess -Description "Restrict GetMails app to specific mailbox"
```

5. Test the policy (may take a few minutes to propagate):
```powershell
Test-ApplicationAccessPolicy -Identity "user@yourdomain.com" -AppId "your_client_id_here"
```

The output should show `AccessCheckResult : Granted` for the allowed mailbox.

6. Verify the policy blocks access to other mailboxes:
```powershell
Test-ApplicationAccessPolicy -Identity "otheruser@yourdomain.com" -AppId "your_client_id_here"
```

The output should show `AccessCheckResult : Denied` for mailboxes not in the group.

**Important Notes:**
- The AppId in the policy must match your Azure AD application's Client ID
- Policy changes may take 15-60 minutes to fully propagate
- Only mailboxes that are members of the specified group will be accessible
- The application will receive permission errors when attempting to access mailboxes outside the policy scope

## Installation

1. Clone or download this repository

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Create a `settings.json` file by copying the example:
```bash
cp settings.json.example settings.json
```

4. Edit `settings.json` and fill in your credentials:
```json
{
  "azure_ad": {
    "client_id": "your_client_id_here",
    "client_secret": "your_client_secret_here",
    "tenant_id": "your_tenant_id_here"
  },
  "mailbox": {
    "email": "user@yourdomain.com"
  },
  "polling": {
    "interval_seconds": 60
  },
  "attachments": {
    "save_directory": "attachments"
  }
}
```

## Configuration

The application uses a `settings.json` file for configuration. Copy `settings.json.example` to `settings.json` and modify the values:

### Configuration Options

**azure_ad**:
- `client_id`: Azure AD application client ID
- `client_secret`: Azure AD application client secret
- `tenant_id`: Azure AD tenant ID

**mailbox**:
- `email`: Email address of the mailbox to monitor

**polling**:
- `interval_seconds`: Polling interval in seconds (default: 60)

**attachments**:
- `save_directory`: Directory to save attachments (default: attachments)

**email_retention**:
- `enabled`: Enable automatic deletion of old emails (true/false, default: false)
- `delete_older_than_days`: Delete emails older than this many days (default: 30)

## Usage

Run the application:

```bash
python src/index.py
```

The application will:
1. Authenticate with Microsoft Graph API
2. Start polling the mailbox at the configured interval
3. Display information about unread emails
4. Download any attachments to the specified directory
5. Mark processed emails as read
6. Delete emails older than the configured retention period (if enabled)
7. Continue running until you press Ctrl+C

### Example Output

```
============================================================
Microsoft 365 Mailbox Monitor
============================================================
Mailbox: user@yourdomain.com
Poll Interval: 60 seconds
Attachments Directory: attachments
Email Retention: Delete emails older than 30 days
============================================================

Authenticating with Microsoft Graph API...
Authentication successful!

Starting mail polling (checking every 60 seconds)...
Press Ctrl+C to stop.

[2025-11-03 10:15:00] Checking for unread emails...
Found 2 unread email(s)

  Subject: Monthly Report
  From: sender@example.com
  Received: 2025-11-03T09:30:00Z
  Has Attachments: True
  Downloading attachments...
  Downloaded: attachments/report.pdf
  Successfully downloaded 1 attachment(s)
  Marked as read

  Subject: Meeting Notes
  From: colleague@example.com
  Received: 2025-11-03T10:00:00Z
  Has Attachments: False
  Marked as read

Checking for emails older than 30 days...
  Deleted old email: 'October Report' (received: 2025-10-01T09:00:00Z)
  Deleted old email: 'Old Meeting Notes' (received: 2025-09-28T14:30:00Z)
Deleted 2 old email(s)

[2025-11-03 10:16:00] Checking for unread emails...
No unread emails found

Checking for emails older than 30 days...
No old emails to delete
```

## Project Structure

```
getmails/
├── src/
│   ├── index.py          # Main application with polling loop
│   ├── auth.py           # Microsoft Graph API authentication
│   └── mail_client.py    # Mail retrieval and attachment download
├── settings.json.example # Example configuration file
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## API Reference

### GraphAuthenticator

Handles authentication with Microsoft Graph API using MSAL.

**Methods:**
- `get_access_token()`: Acquires an access token for API calls

### GraphMailClient

Client for interacting with Microsoft Graph Mail API.

**Methods:**
- `get_unread_emails(folder="inbox", top=50)`: Retrieve unread emails
- `get_email_attachments(message_id)`: Get attachments for a specific email
- `download_attachment(message_id, attachment_id, attachment_name, save_dir)`: Download a single attachment
- `download_all_attachments(message_id, save_dir)`: Download all attachments from an email
- `mark_as_read(message_id)`: Mark an email as read
- `delete_message(message_id)`: Delete a specific email message
- `delete_old_emails(days_old, folder="inbox")`: Delete emails older than specified days

## Security Considerations

- Never commit your `settings.json` file to version control
- Store credentials securely
- Use Azure Key Vault for production environments
- Rotate client secrets regularly
- Follow principle of least privilege for API permissions
- **Always configure Application Access Policy** to restrict access to only the required mailbox(es)
- Validate and sanitize attachment filenames
- Regularly audit which mailboxes the application can access
- Monitor application access logs in Azure AD

## Troubleshooting

### Authentication Errors

- Verify your CLIENT_ID, CLIENT_SECRET, and TENANT_ID are correct
- Ensure admin consent has been granted for API permissions
- Check that the client secret hasn't expired

### Permission Errors

- Verify the application has `Mail.ReadWrite` permission
- Ensure admin consent was granted
- Check that application permissions (not delegated) were used
- If emails cannot be deleted, verify `Mail.ReadWrite` permission is granted (not just `Mail.Read`)

### Mailbox Access Errors

- Verify the MAILBOX_EMAIL is correct
- Ensure the mailbox exists in your organization
- Check that application permissions allow access to all mailboxes
- **Verify Application Access Policy is configured correctly** if you're restricting access to specific mailboxes
- Test the policy using `Test-ApplicationAccessPolicy` PowerShell command
- Wait 15-60 minutes after creating the policy for changes to propagate
- Ensure the mailbox is a member of the policy scope group

## License

MIT License
