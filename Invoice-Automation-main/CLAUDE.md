# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Freight Audit Agent - An AWS-based serverless system that automates freight invoice processing using AWS Bedrock Data Automation, Microsoft 365 email integration, and third-party API (GVP) integration.

### Architecture

The system follows an event-driven serverless architecture with four main Lambda functions orchestrated through AWS EventBridge:

1. **invoice_email_poller** - Polls Microsoft 365 mailbox for unread emails with PDF invoices, uploads to S3 with metadata
2. **bedrock_blueprint_manager** - Manages AWS Bedrock Data Automation blueprint and project configuration for invoice schema
3. **bedrock_invoice_processor** - Triggered by S3 uploads via EventBridge rule, starts Bedrock Data Automation async jobs
4. **gvp_invoice_publisher** - Triggered by Bedrock completion events, processes output and posts to GVP API

### Data Flow

```
                    EventBridge Scheduler (every 5 min during business hours)
                                        ↓
M365 Mailbox ← invoice_email_poller Lambda → S3 Upload (with metadata)
                                                  ↓
                                      EventBridge S3 Event Rule
                                                  ↓
                                  bedrock_invoice_processor Lambda
                                                  ↓
                              Bedrock Data Automation (async job)
                                                  ↓
                                  EventBridge Completion Event
                                                  ↓
                                    gvp_invoice_publisher Lambda
                                                  ↓
                                          GVP API
```

**Key Integration Points:**
- EventBridge Scheduler triggers `invoice_email_poller` every 5 minutes during business hours
- EventBridge rule matches S3 upload events in the `freight-audit-agent-invoices/` prefix only
- EventBridge rule matches Bedrock Data Automation completion events
- S3 object metadata carries email context through the pipeline
- Single S3 bucket with two prefixes: `freight-audit-agent-invoices/` and `freight-audit-agent-output/`

**S3 Bucket Configuration:**
- **Flexible Deployment**: Can use existing bucket (e.g., `prodgvpfilestore1`) or create new bucket
- **Policy Merging**: Terraform automatically merges Bedrock access policies with existing bucket policies
- **Account ID**: Dynamically retrieved via AWS STS - no hardcoding required
- **Permissions**: Terraform reads existing policies via `s3:GetBucketPolicy` API and merges them
- See `terraform/README.md` for detailed S3 configuration options

## Development Commands

### Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows WSL/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Testing Lambda Functions Locally

Each Lambda function can be tested locally using Python:

```bash
# Test blueprint manager
cd lambda_functions/bedrock_blueprint_manager
python handler.py

# Test GVP invoice publisher
cd lambda_functions/gvp_invoice_publisher
python handler.py

# Test invoice email poller (requires environment variables)
cd lambda_functions/invoice_email_poller
python handler.py

# Test bedrock invoice processor with test event
cd lambda_functions/bedrock_invoice_processor
# Edit test_event.json with your S3 bucket/key
python handler.py
```

### Running Jupyter Notebooks

```bash
# Launch Jupyter notebook for interactive testing
jupyter notebook invoice_processing_demo.ipynb
```

## Key Configuration

### Environment Variables Required

**invoice_email_poller Lambda:**
- `AZURE_CLIENT_ID` - Azure AD application client ID
- `AZURE_CLIENT_SECRET` - Azure AD application client secret
- `AZURE_TENANT_ID` - Azure AD tenant ID
- `MAILBOX_EMAIL` - Email address to monitor
- `S3_BUCKET` - Target S3 bucket for PDF uploads (configurable: existing or new bucket)
- `S3_PREFIX` - S3 key prefix (default: freight-audit-agent-invoices/)

**bedrock_blueprint_manager Lambda:**
- `BLUEPRINT_NAME` - Name for Bedrock blueprint (default: freight-invoice-blueprint)
- `BLUEPRINT_FILE` - JSON schema file (default: bedrock_invoice_blueprint.json)
- `PROJECT_NAME` - Bedrock project name (default: freight-audit-project)

**bedrock_invoice_processor Lambda:**
- `PROJECT_NAME` - Must match bedrock_blueprint_manager PROJECT_NAME (default: Freight_Audit_Agent)
- `DATA_AUTOMATION_PROFILE_ARN` - Bedrock Data Automation profile ARN (auto-constructed if not provided)
- `AWS_REGION` - AWS region (default: us-east-1)

**gvp_invoice_publisher Lambda:**
- `GVP_LOGIN_ID` - GVP API login ID (default: novaadmin)
- `GVP_PASSWORD` - GVP API password
- `GVP_AUTH_URL` - GVP authentication URL (optional, defaults to QA: https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken)
- `GVP_API_URL` - GVP API endpoint URL (optional, defaults to QA: https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice)
- `BLUEPRINT_NAME`, `BLUEPRINT_FILE`, `PROJECT_NAME` - Same as bedrock_blueprint_manager
- `DOC_TYPE` - Document type identifier (default: invoices)

### EventBridge Configuration

**EventBridge Scheduler Rule:**
- Trigger: `invoice_email_poller` Lambda
- Schedule: Every 5 minutes during business hours
- Purpose: Poll Microsoft 365 mailbox for new invoice emails

**S3 Upload Event Rule:**
- Event source: `aws.s3`
- Event pattern matches S3 ObjectCreated events
- Target: `bedrock_invoice_processor` Lambda
- Handles both native S3 events and EventBridge S3 notifications

**Bedrock Completion Event Rule:**
- Event source: `aws.bedrock-data-automation-runtime`
- Event pattern matches async invocation completion
- Target: `gvp_invoice_publisher` Lambda

### Invoice Schema

The freight invoice schema (`bedrock_invoice_blueprint.json`) defines extraction fields:
- InvoiceDate, InvoiceNumber, Carrier, Currency, FeeAmount
- PartyName, FleetID, GLAccount, CostCenter, BOLNumber
- OriginCity/State, DestinationCity/State
- STCC, LeadEquipmentID, ServiceDate, Comments

All fields use `inferenceType: "explicit"` for Bedrock Data Automation extraction.

## Project Structure

```
Freight_audit_agent/
├── lambda_functions/
│   ├── invoice_email_poller/         # Polls M365 mailbox, uploads PDFs to S3
│   │   ├── handler.py                # Main Lambda handler
│   │   ├── auth.py                   # Microsoft Graph authentication
│   │   ├── mail_client.py            # Mail operations (GraphMailClient)
│   │   └── README.md                 # M365 setup documentation
│   ├── bedrock_invoice_processor/    # Triggers Bedrock jobs on S3 upload
│   │   ├── handler.py                # Main Lambda handler
│   │   └── test_event.json           # Sample S3 event for testing
│   ├── gvp_invoice_publisher/        # Posts extracted data to GVP API
│   │   ├── handler.py                # Main Lambda handler
│   │   └── gvp_client.py             # GVP API client and helpers
│   └── bedrock_blueprint_manager/    # Manages Bedrock blueprints/projects
│       ├── handler.py                # Main Lambda handler
│       ├── bedrock_helpers.py        # Bedrock API helpers
│       ├── bedrock_invoice_blueprint.json  # Invoice extraction schema
│       └── test_event.json           # Sample event for testing
├── notebook_utils/                   # Jupyter notebook utilities
│   ├── helper_functions.py           # JSON display, image rendering
│   └── display_functions.py          # Additional visualization utilities
├── test_data/                        # Sample invoice PDFs for testing
├── architecture_diagrams/            # System architecture diagrams
├── invoice_processing_demo.ipynb     # Interactive testing notebook
├── gvp_api.postman_collection.json   # Postman collection for GVP API
└── requirements.txt                  # Python dependencies
```

## Key Code Patterns

### Event Format Handling

The `bedrock_invoice_processor` Lambda handles two S3 event formats:

```python
# EventBridge S3 notification format
if "detail" in event:
    s3_bucket = event["detail"]["bucket"]["name"]
    s3_key = event["detail"]["object"]["key"]

# Native S3 event notification format
elif "Records" in event:
    s3_record = event["Records"][0]["s3"]
    s3_bucket = s3_record["bucket"]["name"]
    s3_key = s3_record["object"]["key"]
```

### S3 Metadata Usage

Email metadata is preserved through S3 object metadata when PDFs are uploaded:
- `email-id` - Original email ID from Microsoft Graph
- `email-subject`, `email-sender-email`, `email-sender-name`
- `email-received-time`, `email-body-preview`
- `mailbox` - Source mailbox email address
- `processing-status` - Tracking field (initially "pending")

This metadata is retrieved by `gvp_invoice_publisher` using `get_s3_object_metadata()` to enrich GVP API calls with email context.

### Error Handling

Lambda functions return structured responses:
```python
{
    'statusCode': 200 or 500,
    'body': json.dumps({
        'message': 'Description',
        # ... additional fields
        'errors': [list_of_errors],  # if any
        'timestamp': datetime.utcnow().isoformat()
    })
}
```

### Bedrock Integration

Helper functions in `bedrock_helpers.py` and `gvp_client.py`:
- `get_or_create_blueprint()` - Idempotent blueprint creation
- `get_or_create_project()` - Idempotent project setup with blueprint
- `read_json_content_from_s3()` - Parse Bedrock output
- `get_custom_output_path()` - Navigate Bedrock output structure from job_metadata.json

### GVP API Integration

Two-step authentication pattern in `gvp_client.py`:
1. `get_gvp_auth_token(login_id, password)` - Obtain auth token
2. `post_invoice_to_gvp(inference_results, token, mailbox_name, pdf_path)` - Post invoice data

API Endpoint: `https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice`

Request format includes invoice fields plus:
- `MailboxName` - Email sender from S3 metadata
- `FilePath` - S3 URI of the PDF file

## Microsoft Graph API (invoice_email_poller)

### Authentication
Uses MSAL (Microsoft Authentication Library) with client credentials flow for application permissions (not delegated).

### Required API Permissions
- `Mail.ReadWrite` (Application permission) - Read mail, mark as read, delete emails

### Application Access Policy
The system should be restricted to specific mailboxes using Exchange Online Application Access Policies. See `lambda_functions/invoice_email_poller/README.md` for complete PowerShell setup instructions.

### Key Classes
- `GraphAuthenticator` (auth.py) - Handles MSAL token acquisition using client credentials
- `GraphMailClient` (mail_client.py) - Mail operations:
  - `get_unread_emails()` - Retrieve unread emails from inbox
  - `get_email_attachments()` - Get attachment list for an email
  - `get_attachment_content()` - Download attachment content (base64 encoded)
  - `mark_as_read()` - Mark email as read after processing

### Email Processing Flow
1. EventBridge Scheduler triggers handler every 5 minutes during business hours
2. Authenticate with Microsoft Graph API
3. Retrieve unread emails from configured mailbox
4. For each email with attachments:
   - Filter for PDF attachments only
   - Download PDF content (base64 encoded)
   - Decode and upload to S3 with metadata
   - Mark email as read
5. Return summary with processed count and uploaded file list

## Utilities

### notebook_utils/helper_functions.py
Jupyter notebook helper functions for interactive development:
- `display_json()` - Pretty HTML JSON rendering in notebooks
- `json_to_html()` - Convert JSON to styled HTML tables
- `display_image()` - Show PIL images with ipywidgets
- `pil_to_bytes()` - Convert PIL images to bytes

### notebook_utils/display_functions.py
Additional visualization utilities for Jupyter notebooks.

## Testing

The `tests/` directory is currently empty. When adding tests:
- Use `pytest` as the test framework
- Create test files matching `test_*.py` pattern
- Mock AWS services using `boto3` stubber or `moto` library
- Mock Microsoft Graph API calls in email polling tests
- Use `test_event.json` files as reference for event structures

Example test structure:
```bash
tests/
├── test_email_poller.py          # Test invoice_email_poller
├── test_bedrock_processor.py     # Test bedrock_invoice_processor
├── test_gvp_publisher.py         # Test gvp_invoice_publisher
└── fixtures/
    └── sample_events.json        # Reusable test events
```

## Important Notes

- All Lambda functions use boto3 for AWS service interaction
- EventBridge Scheduler polls email every 5 minutes during business hours
- EventBridge rules orchestrate the workflow between Lambda functions
- S3 serves as the integration point with metadata passing context between stages
- Bedrock Data Automation jobs are asynchronous - monitor via EventBridge completion events
- Never commit credentials or `settings.json` files to version control
- PDF attachments are base64-decoded before S3 upload
- Filename sanitization is applied to prevent path traversal issues
- The `bedrock_invoice_processor` Lambda accepts both EventBridge and native S3 event formats
- All Lambda handler files are named `handler.py` for consistency
- Helper modules have descriptive names (`bedrock_helpers.py`, `gvp_client.py`)
