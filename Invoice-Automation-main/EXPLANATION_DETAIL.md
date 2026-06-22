# Invoice Automation — Complete End-to-End Explanation

> **Who this is for:** Complete beginners who want to understand how a real, production AI invoice automation system works — every component, every design decision, with code from the actual project.

---

## Table of Contents

1. [What is Invoice Automation and Why It Exists](#1-what-is-invoice-automation)
2. [The Full System Architecture](#2-full-architecture)
3. [How AWS Services Work Together](#3-aws-services)
4. [Component 1 — Email Poller Lambda](#4-email-poller)
5. [Component 2 — Microsoft Graph API Auth](#5-graph-auth)
6. [Component 3 — Bedrock Invoice Processor Lambda](#6-bedrock-processor)
7. [Component 4 — The Bedrock Blueprint (AI Extraction Schema)](#7-bedrock-blueprint)
8. [Component 5 — GVP Invoice Publisher Lambda](#8-gvp-publisher)
9. [Component 6 — DLQ Processor Lambda (Error Alerting)](#9-dlq-processor)
10. [Component 7 — Blueprint Manager Lambda (One-Time Setup)](#10-blueprint-manager)
11. [The Correlation ID — Tracking One Invoice End-to-End](#11-correlation-id)
12. [EventBridge Orchestration — The Glue](#12-eventbridge)
13. [Dead Letter Queues — Resilience and Retry](#13-dlq)
14. [Observability — CloudWatch, Metrics, and Alarms](#14-observability)
15. [Infrastructure as Code — Terraform](#15-terraform)
16. [Request Lifecycle A to Z](#16-lifecycle)
17. [Cost Breakdown](#17-cost)
18. [Security Model](#18-security)
19. [Common Failure Modes and Fixes](#19-failures)
20. [Cheatsheet](#20-cheatsheet)
21. [Summary and Conclusion](#21-summary)

---

## 1. What is Invoice Automation?

### The Problem Without Automation

Freight companies receive thousands of invoices per month from carriers (BNSF, UP, CSX, etc.) — each as a PDF attached to an email. Without automation:

```
MANUAL PROCESS (before this system):
  Step 1: Accounts payable employee opens email inbox
  Step 2: Downloads PDF attachment
  Step 3: Opens PDF, reads each field by hand
  Step 4: Types data into ERP system (GVP in this case)
  Step 5: Submits invoice record
  Step 6: Moves email to processed folder
  
  Time: 5-15 minutes per invoice
  Scale: 500+ invoices/month = 40-125 hours of manual data entry/month
  Errors: Typos, missed invoices, wrong field values
  Cost: High labor cost for pure data transcription work
```

### The Solution

```
AUTOMATED PROCESS (this system):
  Step 1: Invoice PDF arrives in email inbox
  Step 2: System AUTOMATICALLY polls mailbox every 5 minutes
  Step 3: AI (AWS Bedrock) reads the PDF and extracts 18 fields
  Step 4: System AUTOMATICALLY posts extracted data to ERP system
  
  Time: 8-13 minutes per invoice (unattended)
  Scale: 500+ invoices/month = no human hours
  Errors: AI extraction with confidence scoring
  Cost: ~$0.06 per invoice ($58/month for 1,000 invoices)
```

### What is GVP?

GVP (Global Visibility Platform by IntelliTrans) is an Oracle-based freight management ERP system. Companies use it to track freight invoices, costs, and shipment data. This system automatically posts extracted invoice data to GVP via its REST API.

---

## 2. Full System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│           FREIGHT AUDIT AGENT — COMPLETE ARCHITECTURE                    │
│                                                                          │
│  TRIGGER (every 5 min, business hours Mon-Fri 8-6 PM EST)               │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  EventBridge Scheduler  →  Event Bus  →  EventBridge Rule #1       │ │
│  └─────────────────────────────────┬───────────────────────────────────┘ │
│                                    │ triggers                            │
│  STAGE 1: EMAIL POLLING            │                                     │
│  ┌─────────────────────────────────▼───────────────────────────────────┐ │
│  │  invoice_email_poller Lambda                                        │ │
│  │  ├── Auth: Azure AD → Microsoft Graph API (MSAL library)           │ │
│  │  ├── Fetch: Unread emails from M365 mailbox                        │ │
│  │  ├── Filter: PDF attachments only (skip inline images)             │ │
│  │  ├── Generate: correlation_id (UUID4) per PDF                      │ │
│  │  ├── Upload: PDF → S3 bucket with rich metadata                    │ │
│  │  └── Mark: Email as read                                           │ │
│  └─────────────────────────────────┬───────────────────────────────────┘ │
│                                    │ S3 ObjectCreated event              │
│                            EventBridge Rule #2                           │
│                                    │ triggers                            │
│  STAGE 2: AI EXTRACTION            │                                     │
│  ┌─────────────────────────────────▼───────────────────────────────────┐ │
│  │  bedrock_invoice_processor Lambda                                   │ │
│  │  ├── Read: S3 metadata (get correlation_id)                        │ │
│  │  ├── Lookup: Bedrock project ARN                                   │ │
│  │  └── Start: Bedrock Data Automation async job                      │ │
│  └─────────────────────────────────┬───────────────────────────────────┘ │
│                                    │                                     │
│  ┌─────────────────────────────────▼───────────────────────────────────┐ │
│  │  AWS Bedrock Data Automation                                        │ │
│  │  ├── Reads: PDF from S3                                            │ │
│  │  ├── Applies: Invoice Blueprint (18 field schema)                  │ │
│  │  ├── Extracts: InvoiceNumber, Carrier, Amount, Origin, Dest...     │ │
│  │  ├── Outputs: JSON with confidence scores → S3                     │ │
│  │  └── Emits: Completion event to EventBridge                        │ │
│  └─────────────────────────────────┬───────────────────────────────────┘ │
│                                    │ Bedrock completion event             │
│                            EventBridge Rule #3                           │
│                                    │ triggers                            │
│  STAGE 3: ERP POSTING              │                                     │
│  ┌─────────────────────────────────▼───────────────────────────────────┐ │
│  │  gvp_invoice_publisher Lambda                                       │ │
│  │  ├── Read: Bedrock output JSON from S3                             │ │
│  │  ├── Retrieve: S3 metadata (correlation_id, mailbox, recipient)    │ │
│  │  ├── Auth: GVP API (Bearer token)                                  │ │
│  │  ├── Post: Invoice data to GVP REST API                           │ │
│  │  └── Handle: Duplicate invoices (idempotent)                       │ │
│  └─────────────────────────────────┬───────────────────────────────────┘ │
│                                    │                                     │
│  ┌─────────────────────────────────▼───────────────────────────────────┐ │
│  │  Oracle Database (via GVP API)                                      │ │
│  │  Invoice record stored: ready for payment approval workflow         │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ERROR HANDLING (parallel to all stages)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Lambda Async Config → 2 retries → DLQ (SQS)                      │ │
│  │  → dlq_processor Lambda → SNS Email Alert (with full details)      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  OBSERVABILITY (continuous)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  CloudWatch: Logs + Metrics + Dashboard + 5 Alarms                 │ │
│  │  AWS Lambda Powertools: Structured JSON logging + Custom metrics    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. How AWS Services Work Together

Before diving into each component, here's what every AWS service does in this project:

| AWS Service | Role | Why Used |
|-------------|------|----------|
| **Lambda** | Runs the 5 Python functions | Serverless — no servers, pay per execution |
| **S3** | Stores PDFs and Bedrock outputs | Durable, cheap object storage |
| **EventBridge Scheduler** | Fires trigger every 5 min | Built-in cron — no EC2 needed |
| **EventBridge Rules** | Routes events to the right Lambda | Decouples services — each Lambda unaware of others |
| **Bedrock Data Automation** | AI reads PDFs and extracts fields | Managed AI — no ML code to write |
| **SQS (DLQ)** | Catches Lambda failures | Ensures no invoice is silently lost |
| **SNS** | Sends failure alert emails | Simple notification to ops team |
| **SSM Parameter Store** | Stores secrets (API keys, passwords) | No hardcoded secrets in code |
| **CloudWatch** | Logs, metrics, alarms, dashboard | Full observability |
| **IAM** | Controls permissions | Each Lambda only has exactly what it needs |

### The Event-Driven Design

The key design principle is **events instead of direct calls**:

```
WRONG WAY (tight coupling):
  Email Poller → directly calls Bedrock Processor → directly calls GVP Publisher
  Problems:
    - Email poller fails if Bedrock is slow
    - No automatic retry
    - Hard to change one stage without touching others

RIGHT WAY (event-driven, this system):
  Email Poller → uploads to S3 → done (it doesn't know about Bedrock)
  S3 upload event → EventBridge → Bedrock Processor
  Bedrock completion event → EventBridge → GVP Publisher
  
  Benefits:
    ✓ Each Lambda has ONE job and is unaware of the others
    ✓ EventBridge handles retries automatically
    ✓ Failed stages go to DLQ for investigation
    ✓ Any stage can be replaced without touching others
```

---

## 4. Component 1 — Email Poller Lambda

### What It Does

`invoice_email_poller` is triggered every 5 minutes by EventBridge Scheduler. It connects to a Microsoft 365 mailbox using the Microsoft Graph API, fetches unread emails, downloads PDF attachments, and uploads them to S3.

### The Full Handler Walkthrough

```python
# lambda_functions/invoice_email_poller/handler.py

# AWS Lambda Powertools gives structured JSON logging and custom CloudWatch metrics
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger(service="invoice_email_poller")   # All logs tagged with this service name
metrics = Metrics(namespace="FreightAuditAgent")  # CloudWatch metrics namespace

s3_client = boto3.client('s3')

# These decorators do 3 things automatically:
# @logger.inject_lambda_context → adds request_id, function_name to every log
# @metrics.log_metrics          → flushes CloudWatch metrics at end of function
# capture_cold_start_metric=True → logs when Lambda wakes from cold start (performance insight)
@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    start_time = time.time()
    
    # All config comes from environment variables (set via Terraform/SSM)
    # No hardcoded values — same code works in dev and prod
    client_id     = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id     = os.getenv("AZURE_TENANT_ID")
    mailbox_email = os.getenv("MAILBOX_EMAIL")
    s3_bucket     = os.getenv("S3_BUCKET", "devgvpbucket1")
    s3_prefix     = os.getenv("S3_PREFIX") or "Invoices/"
    
    # Validate required config upfront — fail fast with clear error
    if not all([client_id, client_secret, tenant_id, mailbox_email]):
        logger.error("Missing required environment variables", extra={...})
        metrics.add_metric(name="ConfigurationError", unit=MetricUnit.Count, value=1)
        return {'statusCode': 500, 'body': json.dumps({'error': error_msg})}
    
    # STEP 1: Authenticate with Microsoft Graph API
    authenticator = GraphAuthenticator(client_id, client_secret, tenant_id)
    access_token = authenticator.get_access_token()
    
    # STEP 2: Get all unread emails from the monitored mailbox
    mail_client = GraphMailClient(access_token, mailbox_email)
    unread_emails = mail_client.get_unread_emails()
    
    metrics.add_metric(name="EmailsFound", unit=MetricUnit.Count, value=len(unread_emails))
    
    # STEP 3: For each email, process PDF attachments
    for email in unread_emails:
        email_id = email.get("id")
        subject  = email.get("subject", "(No Subject)")
        has_attachments = email.get("hasAttachments", False)
        
        # Extract the RECIPIENT address — important for "plus addressing"
        # Example: freightaudit+arclin@company.com → maps to client "arclin"
        to_recipients = email.get("toRecipients", [])
        recipient_address = to_recipients[0]["emailAddress"]["address"] if to_recipients else ""
        
        if has_attachments:
            attachments = mail_client.get_email_attachments(email_id)
            
            for attachment in attachments:
                attachment_name = attachment.get("name", "unnamed")
                is_inline = attachment.get("isInline", False)
                attachment_type = attachment.get("@odata.type", "")
                
                # FILTER 1: Skip inline attachments (email signature images)
                if is_inline:
                    continue
                
                # FILTER 2: Only process file attachments, not calendar invites, etc.
                if attachment_type != "#microsoft.graph.fileAttachment":
                    continue
                
                # FILTER 3: Only PDFs (not Word docs, Excel sheets, etc.)
                if not attachment_name.lower().endswith('.pdf'):
                    continue
                
                # Download the PDF content (base64 encoded from Graph API)
                attachment_content = mail_client.get_attachment_content(email_id, attachment.get("id"))
                file_content = base64.b64decode(attachment_content)  # Decode to bytes
                
                # CRITICAL: Generate a unique correlation ID for this invoice
                # This UUID follows the invoice through ALL stages
                correlation_id = str(uuid.uuid4())
                
                # Build S3 key with timestamp for sorting
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                safe_filename = sanitize_filename(attachment_name)  # Remove dangerous characters
                s3_key = f"{s3_prefix}{timestamp}_{safe_filename}"
                # Example: "Invoices/20251217_143022_BNSF_Invoice_12345.pdf"
                
                # CRITICAL: Store ALL context as S3 metadata
                # This metadata follows the PDF through S3 and is read by downstream Lambdas
                metadata = {
                    'correlation-id':              correlation_id,           # UUID for tracking
                    'mailbox-id':                  mailbox_email[:100],      # Which mailbox it came from
                    'email-recipient-address':     recipient_address[:100],  # For plus-addressing
                    'email-id':                    email_id[:100],            # For auditing
                    'email-subject':               subject[:200],            # Context
                    'email-sender-email':          sender_email[:100],       # Who sent it
                    'email-received-time':         received[:50],            # For end-to-end latency
                    'original-filename':           attachment_name[:200],    # Original PDF name
                    'attachment-size':             str(attachment_size),
                    'processing-status':           'pending',
                }
                
                # Upload PDF to S3 with metadata attached
                s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=s3_key,
                    Body=file_content,
                    ContentType='application/pdf',
                    Metadata=metadata,   # ← This is the magic — context travels with the file
                )
                
                metrics.add_metric(name="PDFsUploaded", unit=MetricUnit.Count, value=1)
        
        # Mark email as read so it's not processed again next 5-minute poll
        mail_client.mark_as_read(email_id)
    
    metrics.add_metric(name="EmailsProcessed", unit=MetricUnit.Count, value=processed_count)
```

### The Metadata Strategy — Why It's Clever

```
PROBLEM: Bedrock Processor and GVP Publisher don't know WHERE the PDF came from
         They just receive an S3 path — no email context

NAIVE SOLUTION: Store email context in a database, query it later
  - Extra DynamoDB table needed
  - More IAM permissions
  - Extra latency for DB lookups
  - Extra cost

ELEGANT SOLUTION: S3 object metadata
  - The PDF file itself carries all context as metadata
  - Any Lambda that reads the PDF can call head_object() to get metadata
  - No database, no extra queries, zero cost
  - Context travels with the file through every stage

METADATA KEYS SET BY EMAIL POLLER:
  correlation-id             → UUID4 to track this invoice everywhere
  mailbox-id                 → invoices@company.com (which mailbox)
  email-recipient-address    → freightaudit+arclin@company.com (client routing)
  email-id                   → Microsoft Graph message ID
  email-subject              → "BNSF Invoice #12345 for November"
  email-sender-email         → billing@bnsf.com
  email-sender-name          → BNSF Railway
  email-received-time        → 2025-12-17T14:30:22Z (for latency calculation)
  original-filename          → BNSF_Invoice_12345.pdf
  attachment-size            → 245892 (bytes)
  processing-status          → pending
```

### Metadata Sanitization — Why It Matters

```python
def sanitize_metadata_value(value):
    """S3 metadata becomes HTTP headers — headers CANNOT contain control characters."""
    
    value_str = str(value)
    
    # Email subjects often contain newlines, tabs, carriage returns
    # HTTP headers cannot have these — would cause 400 Bad Request errors
    value_str = value_str.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
    value_str = value_str.replace('\t', ' ')
    
    # Remove ASCII control characters (0-31 and 127)
    value_str = ''.join(char if ord(char) >= 32 and ord(char) != 127 else ' ' for char in value_str)
    
    # Collapse multiple spaces
    value_str = ' '.join(value_str.split())
    
    return value_str

# WITHOUT sanitization:
# Email subject: "Invoice\r\nFor November" → HTTP header breaks → S3 returns 400 error
# WITH sanitization:
# "Invoice\r\nFor November" → "Invoice For November" → safe HTTP header
```

---

## 5. Component 2 — Microsoft Graph API Auth

### How Microsoft 365 Authentication Works

```
CHALLENGE: Lambda needs to read emails from a corporate mailbox
           WITHOUT any human login (it runs unattended every 5 minutes)

SOLUTION: Azure AD App Registration with Application Permissions
  - A "service account" app is registered in Azure Active Directory
  - It gets Mail.ReadWrite permission at APPLICATION level
  - It authenticates using client credentials flow (no user required)
  - It gets an access token → uses it to call Graph API
```

### The OAuth 2.0 Client Credentials Flow

```
Lambda                Azure AD               Microsoft Graph
   │                     │                         │
   │  1. Send credentials│                         │
   │  (client_id +       │                         │
   │  client_secret)     │                         │
   │────────────────────►│                         │
   │                     │                         │
   │  2. Return access   │                         │
   │  token (JWT, 1 hour │                         │
   │  expiry)            │                         │
   │◄────────────────────│                         │
   │                     │                         │
   │  3. Call Graph API  │                         │
   │  with Bearer token  │                         │
   │─────────────────────────────────────────────►│
   │                     │                         │
   │  4. Return emails   │                         │
   │  (JSON)             │                         │
   │◄─────────────────────────────────────────────│
```

```python
# lambda_functions/invoice_email_poller/auth.py

from msal import ConfidentialClientApplication

class GraphAuthenticator:
    """Handles OAuth 2.0 client credentials flow for Microsoft Graph API."""
    
    def __init__(self, client_id, client_secret, tenant_id):
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        # MSAL = Microsoft Authentication Library
        # ConfidentialClientApplication = for server-side apps (no user interaction)
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,   # The "password" for the service app
            authority=self.authority,
        )
        self.scopes = ["https://graph.microsoft.com/.default"]
        # ".default" means: grant all permissions that were configured in Azure AD
    
    def get_access_token(self) -> str:
        """Get access token using client credentials flow."""
        result = self.app.acquire_token_for_client(scopes=self.scopes)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            # Error: e.g., wrong client_id, expired secret, wrong tenant_id
            raise Exception(f"Auth failed: {result.get('error')} - {result.get('error_description')}")
```

### Microsoft Graph API Calls

```python
# lambda_functions/invoice_email_poller/mail_client.py

class GraphMailClient:
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def get_unread_emails(self) -> list:
        """Fetch all unread emails with attachments from the mailbox."""
        url = f"{self.BASE_URL}/users/{self.mailbox}/messages"
        response = requests.get(url, 
            headers={"Authorization": f"Bearer {self.token}"},
            params={
                "$filter": "isRead eq false",         # Only unread
                "$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,bodyPreview",
                "$top": 50,                            # Max 50 per call
            }
        )
        return response.json().get("value", [])
    
    def get_email_attachments(self, email_id: str) -> list:
        """Get list of all attachments for an email."""
        url = f"{self.BASE_URL}/users/{self.mailbox}/messages/{email_id}/attachments"
        response = requests.get(url, headers={"Authorization": f"Bearer {self.token}"})
        return response.json().get("value", [])
    
    def get_attachment_content(self, email_id: str, attachment_id: str) -> str:
        """Download attachment content (returns base64 encoded string)."""
        url = f"{self.BASE_URL}/users/{self.mailbox}/messages/{email_id}/attachments/{attachment_id}"
        response = requests.get(url, headers={"Authorization": f"Bearer {self.token}"})
        return response.json().get("contentBytes")   # Base64 encoded PDF bytes
    
    def mark_as_read(self, email_id: str):
        """Mark email as read so it won't be fetched again next poll."""
        url = f"{self.BASE_URL}/users/{self.mailbox}/messages/{email_id}"
        requests.patch(url,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            json={"isRead": True},
        )
```

### Plus Addressing — Client Routing

A subtle but important design pattern used by this system:

```
PROBLEM: One company has 50 freight clients
         All freight invoices go to one mailbox: invoices@company.com
         How does GVP know which client each invoice belongs to?

SOLUTION: Email Plus Addressing (RFC 5233)
  Clients send invoices to: freightaudit+CLIENTCODE@company.com
  
  Examples:
    BNSF sends to: freightaudit+arclin@company.com  → maps to Arclin client
    UP sends to:   freightaudit+novatel@company.com → maps to Novatel client
    CSX sends to:  freightaudit+ardent@company.com  → maps to Ardent Mills client
  
  All of these land in the SAME inbox (email servers ignore the +part)
  The Lambda extracts the recipient address from the email
  and stores it as 'email-recipient-address' in S3 metadata
  
  When posting to GVP: uses recipient_address as MailboxName field
  GVP uses MailboxName to determine which client account gets the invoice
```

---

## 6. Component 3 — Bedrock Invoice Processor Lambda

### What It Does

This Lambda is triggered when a PDF is uploaded to S3. It starts an **asynchronous** Bedrock Data Automation job to extract invoice fields from the PDF.

### Why Asynchronous?

```
SYNCHRONOUS (bad for PDFs):
  Lambda starts Bedrock job → waits for result → Lambda times out after 15 min
  
  Bedrock takes 2-8 minutes per invoice
  Lambda max timeout = 15 minutes
  This works but keeps Lambda running (and billing) for 2-8 min doing nothing
  If Bedrock is slow → Lambda times out → invoice lost!

ASYNCHRONOUS (correct):
  Lambda starts Bedrock job → returns immediately (costs ~1 second of Lambda time)
  Bedrock processes in background (takes 2-8 minutes)
  Bedrock emits completion event to EventBridge when done
  EventBridge triggers GVP Publisher Lambda
  
  Total Lambda compute: ~1 second + ~3 seconds = 4 seconds billed
  vs 4-8 minutes billed with synchronous approach
```

### The Handler Code

```python
# lambda_functions/bedrock_invoice_processor/handler.py

@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Three different clients needed:
    s3_client          = boto3.client('s3')
    bda_client         = boto3.client('bedrock-data-automation')          # Control plane (list projects)
    bda_runtime_client = boto3.client('bedrock-data-automation-runtime')  # Data plane (start jobs)
    
    # STEP 1: Parse which file was uploaded (EventBridge sends S3 event details)
    # EventBridge S3 notification format:
    # { "detail": { "bucket": {"name": "..."}, "object": {"key": "..."} } }
    s3_bucket = event["detail"]["bucket"]["name"]
    s3_key    = unquote_plus(event["detail"]["object"]["key"])
    # URL-decode: spaces in filenames are encoded as %20 in S3 events
    
    # STEP 2: Retrieve the correlation_id from S3 metadata
    # (Set by email poller when PDF was uploaded)
    s3_response = s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
    s3_metadata = s3_response.get('Metadata', {})
    correlation_id = s3_metadata.get('correlation-id', 'unknown')
    
    # Add correlation_id to ALL subsequent log messages for traceability
    logger.append_keys(correlation_id=correlation_id)
    
    # STEP 3: Find the Bedrock project ARN
    project_name = os.getenv("PROJECT_NAME", "Freight_Audit_Agent")
    projects = bda_client.list_data_automation_projects(projectStageFilter='LIVE')
    project = next(
        (p for p in projects['projects'] if p['projectName'] == project_name),
        None
    )
    
    if not project:
        raise ValueError(f"Bedrock project '{project_name}' not found — run blueprint_manager first")
    
    project_arn = project['projectArn']
    
    # STEP 4: Start the async Bedrock job
    # Input:  PDF in S3
    # Output: Extracted JSON will be written to S3 output location
    response = bda_runtime_client.invoke_data_automation_async(
        inputConfiguration={
            's3Uri': f's3://{s3_bucket}/{s3_key}'   # The PDF to process
        },
        outputConfiguration={
            's3Uri': f's3://{output_bucket}/{output_prefix}'  # Where to write results
        },
        dataAutomationProfileArn=data_automation_profile_arn,  # Which AI model to use
        dataAutomationConfiguration={
            'dataAutomationProjectArn': project_arn   # Our custom invoice blueprint
        },
        notificationConfiguration={
            'eventBridgeConfiguration': {
                'eventBridgeEnabled': True  # CRITICAL: emit event when done
            }
        }
    )
    
    invocation_arn = response["invocationArn"]
    # Lambda returns immediately — job runs asynchronously in Bedrock
    
    metrics.add_metric(name="BedrockJobsStarted", unit=MetricUnit.Count, value=1)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'invocation_arn': invocation_arn, ...})
    }
```

### How EventBridge Gets Notified of S3 Uploads

```
IMPORTANT: By default, S3 events don't go to EventBridge

To enable:
  1. Enable EventBridge notifications on the S3 bucket (Terraform does this)
  2. S3 now sends ALL object events to the default EventBridge event bus
  3. EventBridge Rule #2 filters for:
     - source: "aws.s3"
     - detail-type: "Object Created"
     - bucket: "devgvpbucket1"
     - key prefix: "Invoices/"

Without step 1: uploads to S3 → nothing happens
With step 1:    uploads to S3 → EventBridge → Bedrock Processor Lambda
```

---

## 7. Component 4 — The Bedrock Blueprint (AI Extraction Schema)

### What is a Bedrock Blueprint?

A Blueprint is the **schema that tells Bedrock Data Automation what to extract from the document**. It's a JSON file that defines each field, its type, and instructions for the AI on how to find it.

### The Invoice Blueprint

```json
// lambda_functions/bedrock_blueprint_manager/bedrock_invoice_blueprint.json

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "Freight Carrier Invoice Schema",
  "class": "Freight Invoice",
  "type": "object",
  "properties": {
    
    "InvoiceDate": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the invoice date from the document in mm/dd/yyyy format (e.g., 11/05/2025)"
    },
    
    "InvoiceNumber": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the invoice number from the document"
    },
    
    "Carrier": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the carrier name - company billing for this service. Examples: BNSF, UP, CSX, NS, KCS, CP, CN, PGTX"
    },
    
    "FeeAmount": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract only the numeric total fee amount WITHOUT currency symbols. Return 45335.98 not $45,335.98"
    },
    
    "OriginCity": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the origin city of the shipment"
    },
    
    "DestinationCity": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the destination city of the shipment"
    },
    
    "BOLNumber": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the bill of lading number"
    },
    
    "STCC": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the Standard Transportation Commodity Code (STCC), a 7-digit code for commodity classification"
    },
    
    "ServiceDate": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the service date in mm/dd/yyyy format"
    }
    
    // ... 9 more fields: Currency, PartyName, FleetID, GLAccount, CostCenter,
    //     OriginState, DestinationState, LeadEquipmentID, Comments
  }
}
```

### What "inferenceType: explicit" Means

```
inferenceType: "explicit"
  → AI looks for SPECIFIC text that matches this field
  → Contrast with "implicit" where AI infers from context
  → For invoices: explicit is right — we want the exact InvoiceNumber printed on the PDF
  → "explicit" gives you: {value: "INV-12345", confidence: 0.97}

Confidence scores:
  0.97 = AI is 97% confident this is the InvoiceNumber
  0.60 = Low confidence — AI is unsure, may need manual review
  1.00 = AI found exact match with very high certainty

Why confidence matters:
  observability_helpers.py calculates average confidence across all fields
  If average < 0.70 → log warning for manual review
  If average > 0.90 → proceed automatically
```

### Bedrock Data Automation Output Structure

```
S3 Output Location: s3://devgvpbucket1/lambda-output/JOB_ID/
  ├── job_metadata.json          ← Index file (where to find results)
  └── custom_output/
      └── 0/
          └── custom_output.json ← The actual extracted fields

job_metadata.json:
{
  "output_metadata": [{
    "segment_metadata": [{
      "custom_output_path": "s3://bucket/lambda-output/JOB_ID/custom_output/0/custom_output.json"
    }]
  }]
}

custom_output.json:
{
  "inference_result": {
    "InvoiceNumber": "BNSF-2025-12345",
    "Carrier": "BNSF",
    "FeeAmount": "45335.98",
    "Currency": "USD",
    "InvoiceDate": "11/05/2025",
    "ServiceDate": "11/01/2025",
    "OriginCity": "Chicago",
    "OriginState": "IL",
    "DestinationCity": "Denver",
    "DestinationState": "CO",
    "BOLNumber": "BOL-987654",
    "STCC": "2041000",
    "PartyName": "Ardent Mills LLC",
    "GLAccount": "5100-001",
    "CostCenter": "CC-WEST",
    "FleetID": "FLT-001",
    "LeadEquipmentID": "BNSF-123456",
    "Comments": "Rush delivery, hazmat class 1"
  }
}
```

---

## 8. Component 5 — GVP Invoice Publisher Lambda

### What It Does

This Lambda is triggered when Bedrock finishes processing a PDF. It reads the extracted invoice data from S3 and posts it to the GVP ERP system via REST API.

### The Handler Walkthrough

```python
# lambda_functions/gvp_invoice_publisher/handler.py

@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    
    # STEP 1: Parse Bedrock completion event
    # EventBridge event from Bedrock Data Automation:
    # {
    #   "source": "aws.bedrock-data-automation-runtime",
    #   "detail-type": "Data Automation Async Invocation Status Change",
    #   "detail": {
    #     "status": "SUCCEEDED",
    #     "input_s3_object": {"s3_bucket": "...", "name": "Invoices/...pdf"},
    #     "output_s3_location": {"s3_bucket": "...", "name": "lambda-output/..."}
    #   }
    # }
    input_bucket  = event["detail"]["input_s3_object"]["s3_bucket"]
    input_key     = unquote_plus(event["detail"]["input_s3_object"]["name"])
    output_bucket = event["detail"]["output_s3_location"]["s3_bucket"]
    output_key    = unquote_plus(event["detail"]["output_s3_location"]["name"])
    
    input_s3_uri  = f"s3://{input_bucket}/{input_key}"
    output_s3_uri = f"s3://{output_bucket}/{output_key}"
    
    # STEP 2: Get the original email metadata from S3
    # (stored by email poller, now retrieved here)
    s3_metadata      = get_s3_object_metadata(input_bucket, input_key)
    correlation_id   = s3_metadata.get('correlation-id', 'unknown')
    mailbox_id       = s3_metadata.get('mailbox-id', 'unknown')
    recipient_address = s3_metadata.get('email-recipient-address', 'unknown')
    email_received   = s3_metadata.get('email-received-time')
    
    logger.append_keys(correlation_id=correlation_id)
    
    # STEP 3: Find the custom output file from Bedrock's job_metadata.json
    job_metadata_uri = output_s3_uri.rsplit('/', 1)[0] + "/job_metadata.json"
    custom_output_uri = get_custom_output_path(job_metadata_uri)
    
    # STEP 4: Read extracted invoice fields from Bedrock's output JSON
    result_json = read_json_content_from_s3(custom_output_uri)
    inference_results = result_json.get("inference_result", {})
    
    # STEP 5: Authenticate with GVP API (Bearer token)
    gvp_login_id = os.getenv("GVP_LOGIN_ID")
    gvp_password = os.getenv("GVP_PASSWORD")
    gvp_token = get_gvp_auth_token(gvp_login_id, gvp_password)
    
    # STEP 6: Post invoice to GVP
    gvp_response = post_invoice_to_gvp(
        inference_results,
        gvp_token,
        recipient_address,  # Client routing (plus addressing)
        pdf_file_path=input_s3_uri,
    )
    
    # STEP 7: Calculate end-to-end latency
    if email_received:
        received_dt = datetime.fromisoformat(email_received.replace('Z', '+00:00'))
        end_to_end_ms = int((datetime.utcnow() - received_dt).total_seconds() * 1000)
        metrics.add_metric(name="EndToEndLatency", unit=MetricUnit.Milliseconds, value=end_to_end_ms)
        logger.info("Pipeline completed", extra={"end_to_end_duration_ms": end_to_end_ms})
    
    metrics.add_metric(name="GVPPostsSuccessful", unit=MetricUnit.Count, value=1)
    return {'statusCode': 200, ...}
```

### The GVP API Client

```python
# lambda_functions/gvp_invoice_publisher/gvp_client.py

def get_gvp_auth_token(login_id, password, auth_url=None):
    """Get Bearer token from GVP using HTTP header-based auth."""
    
    if auth_url is None:
        auth_url = "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
    
    # GVP uses a non-standard auth pattern: credentials in request HEADERS
    # (not in body like most OAuth flows)
    headers = {
        "LoginID": login_id,
        "Pwd": password,
    }
    
    response = requests.get(auth_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    # Token is returned as a plain string (strip surrounding quotes)
    token = response.text.strip().strip('"').strip("'")
    return token


def post_invoice_to_gvp(inference_results, token, mailbox_name, pdf_file_path, api_url=None):
    """Post extracted invoice data to GVP REST API."""
    
    if api_url is None:
        api_url = "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"
    
    # Field-level business rules:
    
    # Rule 1: BOLNumber must be 20 chars max
    bol_number = inference_results.get("BOLNumber", "")
    if len(bol_number) > 20:
        bol_number = bol_number[:20]   # Truncate silently, log warning
    
    # Rule 2: ServiceDate — if Bedrock extracted multiple dates ("01/01/2025, 01/15/2025")
    # GVP only accepts one date → use the first one
    service_date = inference_results.get("ServiceDate", "")
    if service_date and "," in service_date:
        service_date = service_date.split(",")[0].strip()
    
    # Map Bedrock field names → GVP API field names
    payload = {
        "InvoiceDate":     inference_results.get("InvoiceDate", ""),
        "InvoiceNumber":   inference_results.get("InvoiceNumber", ""),
        "Carrier":         inference_results.get("Carrier", ""),
        "Currency":        inference_results.get("Currency", "USD"),
        "FeeAmount":       inference_results.get("FeeAmount", ""),
        "PartyName":       inference_results.get("PartyName", "Novaadmin"),
        "MailboxName":     mailbox_name,     # From S3 metadata (plus addressing)
        "FleetID":         inference_results.get("FleetID", ""),
        "GLAccount":       inference_results.get("GLAccount", ""),
        "CostCenter":      inference_results.get("CostCenter", ""),
        "BOLNumber":       bol_number,
        "OriginCity":      inference_results.get("OriginCity", ""),
        "OriginState":     inference_results.get("OriginState", ""),
        "DestinationCity": inference_results.get("DestinationCity", ""),
        "DestinationState":inference_results.get("DestinationState", ""),
        "Comments":        inference_results.get("Comments", "Invoice auto-created from OCR data."),
        "STCC":            inference_results.get("STCC", ""),
        "LeadEquipmentID": inference_results.get("LeadEquipmentID", ""),
        "ServiceDate":     service_date,
        "PDFFilePath":     pdf_file_path,   # S3 URI of original PDF (for GVP audit trail)
    }
    
    headers = {
        "tokenID": token,
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        response_body = e.response.text.lower() if e.response else ""
        
        # IDEMPOTENCY: GVP returns 500 for duplicate invoices
        # This is NOT a real error — invoice was already processed
        if "invoice number already exists" in response_body:
            logger.warning("Duplicate invoice detected — treating as success (idempotent)")
            return {
                "status": "duplicate",
                "idempotent": True,
                "invoice_number": payload.get("InvoiceNumber"),
            }
        
        # Real error — re-raise to trigger EventBridge retry → DLQ
        raise
```

### Idempotency — Why It Matters

```
SCENARIO: GVP post succeeds, but Lambda crashes AFTER the post but BEFORE returning
  → EventBridge sees Lambda failure → retries
  → Lambda calls GVP API again → GVP already has this invoice
  → Without idempotency: GVP returns 500 → Lambda throws error → DLQ alarm fires
  → With idempotency: GVP returns 500 with "Invoice already exists" →
    Lambda detects this pattern → treats as success → no alarm

RESULT: Duplicate detection prevents false failure alerts
        and ensures the DLQ is only used for REAL failures
```

---

## 9. Component 6 — DLQ Processor Lambda

### What It Does

The DLQ (Dead Letter Queue) Processor is triggered whenever a Lambda function exhausts all retries and its failed event lands in the Dead Letter Queue. It sends a detailed email alert via SNS.

### Why DLQs Are Critical

```
RISK WITHOUT DLQS:
  Lambda fails 3 times → error silently dropped
  Invoice never gets posted to GVP
  Nobody knows → client disputes invoice → business impact

WITH DLQS + DLQ PROCESSOR:
  Lambda fails 3 times → event goes to SQS DLQ
  DLQ Processor Lambda triggers → sends SNS email:
  
  🚨 CRITICAL: Invoice BNSF-12345 Failed - In DLQ
  
  Invoice Number:   BNSF-12345
  Mailbox:          invoices@company.com
  Recipient:        freightaudit+arclin@company.com
  Correlation ID:   a3f8c921-1234-abcd-5678-ef90ab123456
  
  Failed Stage:     GVP API Publishing
  Issue:            Invoice extracted by Bedrock but failed to post to GVP API
  Retry Attempts:   3 (all failed)
  
  PDF Invoice:      s3://devgvpbucket1/Invoices/20251217_143022_BNSF_Invoice_12345.pdf
  Bedrock Output:   s3://devgvpbucket1/lambda-output/JOB_ID/custom_output/...
  
  NEXT STEPS:
  1. Check if GVP API is accessible
  2. Review CloudWatch logs: /aws/lambda/prod-freight-audit-agent-gvp-publisher
  3. Manual reprocessing instructions...
  
  PDF DOWNLOAD:
  aws s3 cp s3://devgvpbucket1/Invoices/... ./invoice_BNSF-12345.pdf
  
  CLOUDWATCH QUERY:
  fields @timestamp, @message | filter correlation_id = "a3f8c921-..."
```

### DLQ Message Format Handling

```python
# lambda_functions/dlq_processor/handler.py

def extract_invoice_details_from_dlq_message(message_body):
    """
    DLQ messages come in two different formats depending on how the failure occurred.
    """
    message = json.loads(message_body)
    
    # FORMAT 1: Lambda async invoke failure
    # When: Lambda code throws an unhandled exception
    # Message wrapped in Lambda's invocation failure envelope
    if 'requestPayload' in message:
        # Unwrap: the actual EventBridge event is inside 'requestPayload'
        event = message['requestPayload']
        
        # Metadata about the failure:
        invoke_count = message['requestContext']['approximateInvokeCount']  # Should be 3
        condition    = message['requestContext']['condition']               # "RetriesExhausted"
        error_type   = message['responsePayload']['errorType']              # "HTTPError" etc.
    
    # FORMAT 2: EventBridge delivery failure
    # When: EventBridge can't deliver the event to Lambda (e.g., Lambda concurrency limit)
    else:
        event = message   # Original event directly in message body
    
    # Now parse the event to extract invoice details
    details = {}
    
    if event.get('source') == 'aws.bedrock':
        # GVP Publisher DLQ — Bedrock completed but GVP post failed
        details['dlq_type'] = 'gvp_publisher'
        details['bucket']   = event['detail']['input_s3_object']['s3_bucket']
        details['key']      = event['detail']['input_s3_object']['name']
        
        # Get full context from S3 metadata
        s3_metadata = s3_client.head_object(Bucket=details['bucket'], Key=details['key'])
        metadata = s3_metadata.get('Metadata', {})
        details['correlation_id']   = metadata.get('correlation-id', 'Unknown')
        details['mailbox']          = metadata.get('mailbox-id', 'Unknown')
        details['recipient_address'] = metadata.get('email-recipient-address', 'Unknown')
    
    elif event.get('source') == 'aws.s3':
        # Invoice Processor DLQ — S3 uploaded but Bedrock failed
        details['dlq_type'] = 'invoice_processor'
        details['bucket']   = event['detail']['bucket']['name']
        details['key']      = event['detail']['object']['key']
    
    return details


@logger.inject_lambda_context
def lambda_handler(event, context):
    """Process DLQ messages — one Lambda call per DLQ message."""
    
    for record in event.get('Records', []):
        dlq_name      = record['eventSourceARN'].split(':')[-1]
        receive_count = int(record['attributes'].get('ApproximateReceiveCount', 1))
        message_body  = record['body']
        
        details = extract_invoice_details_from_dlq_message(message_body)
        
        if details:
            send_dlq_alert(details, dlq_name, receive_count)
```

---

## 10. Component 7 — Blueprint Manager Lambda (One-Time Setup)

### What It Does

This Lambda is run **once** to set up the Bedrock Data Automation infrastructure. It creates:
1. A Bedrock Data Automation **project** named `Freight_Audit_Agent`
2. A **blueprint** within the project (the invoice schema JSON)

After this runs, all subsequent invoice processing uses this project and blueprint automatically.

```python
# lambda_functions/bedrock_blueprint_manager/handler.py

def lambda_handler(event, context):
    """Run once to set up Bedrock Data Automation infrastructure."""
    
    bda_client = boto3.client('bedrock-data-automation')
    
    # STEP 1: Create blueprint from schema JSON file
    with open('bedrock_invoice_blueprint.json') as f:
        blueprint_schema = json.load(f)
    
    blueprint_response = bda_client.create_blueprint(
        blueprintName='FreightInvoiceBlueprint',
        type='DOCUMENT',                 # Processing PDF documents
        blueprintStage='LIVE',           # DRAFT=testing, LIVE=production
        schema=json.dumps(blueprint_schema),
    )
    blueprint_arn = blueprint_response['blueprint']['blueprintArn']
    
    # STEP 2: Create Data Automation project (links blueprint to a deployable unit)
    project_response = bda_client.create_data_automation_project(
        projectName='Freight_Audit_Agent',
        projectDescription='Automated freight invoice extraction',
        projectStage='LIVE',
        customOutputConfiguration={
            'blueprints': [{
                'blueprintArn': blueprint_arn,
                'blueprintStage': 'LIVE',
            }]
        },
    )
    project_arn = project_response['project']['projectArn']
    
    return {'blueprint_arn': blueprint_arn, 'project_arn': project_arn}
```

---

## 11. The Correlation ID — Tracking One Invoice End-to-End

The correlation ID is the **backbone of observability** in this system. Here's how it flows:

```
STEP 1: Email Poller generates correlation_id
  correlation_id = str(uuid.uuid4())
  # Example: "a3f8c921-4d2b-4e78-8a1c-ef90ab123456"
  
  Stored in S3 metadata:
  s3://devgvpbucket1/Invoices/20251217_143022_BNSF_Invoice_12345.pdf
    metadata['correlation-id'] = 'a3f8c921-4d2b-4e78-8a1c-ef90ab123456'

STEP 2: Bedrock Processor reads it
  s3_metadata = s3_client.head_object(Bucket=bucket, Key=key)['Metadata']
  correlation_id = s3_metadata.get('correlation-id')
  logger.append_keys(correlation_id=correlation_id)
  # Now ALL logs from this Lambda include correlation_id

STEP 3: GVP Publisher reads it from same S3 file
  correlation_id = s3_metadata.get('correlation-id')
  logger.append_keys(correlation_id=correlation_id)

STEP 4: DLQ Processor reads it from S3 metadata
  correlation_id = metadata.get('correlation-id')
  # Included in SNS alert email

STEP 5: You can find ALL logs for one invoice
  CloudWatch Logs Insights query:
  fields @timestamp, function_name, message
  | filter correlation_id = "a3f8c921-4d2b-4e78-8a1c-ef90ab123456"
  | sort @timestamp asc

RESULT:
  @timestamp              function_name          message
  2025-12-17 14:30:22    email_poller           PDF uploaded to S3
  2025-12-17 14:30:24    invoice_processor      Bedrock job started
  2025-12-17 14:38:41    gvp_publisher          Invoice posted to GVP
  2025-12-17 14:38:42    gvp_publisher          Pipeline completed, 498 seconds end-to-end
```

---

## 12. EventBridge Orchestration — The Glue

### Three EventBridge Rules

```
RULE 1: Scheduler → Email Poller
  Pattern: {source: "custom.freight-audit", detail-type: "Scheduled Invoice Poll"}
  Source:  EventBridge Scheduler (every 5 min, Mon-Fri 8AM-6PM EST)
  Target:  invoice_email_poller Lambda
  DLQ:     email-poller-dlq (SQS)
  
RULE 2: S3 Upload → Bedrock Processor
  Pattern: {source: "aws.s3", detail-type: "Object Created",
            detail: {bucket: {name: ["devgvpbucket1"]}, object: {key: [{prefix: "Invoices/"}]}}}
  Source:  S3 EventBridge notification (on every object upload)
  Target:  bedrock_invoice_processor Lambda
  DLQ:     invoice-processor-dlq (SQS)
  
RULE 3: Bedrock Complete → GVP Publisher
  Pattern: {source: "aws.bedrock-data-automation-runtime",
            detail-type: "Data Automation Async Invocation Status Change",
            detail: {status: ["SUCCEEDED"]}}
  Source:  Bedrock Data Automation completion event
  Target:  gvp_invoice_publisher Lambda
  DLQ:     gvp-publisher-dlq (SQS)
```

### EventBridge Rule Terraform Code

```hcl
# terraform/eventbridge.tf

# Rule #2: S3 upload → Invoice Processor
resource "aws_cloudwatch_event_rule" "s3_to_processor" {
  name = "prod-freight-audit-agent-s3-to-processor"
  
  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = ["devgvpbucket1"] }
      object = { key = [{ prefix = "Invoices/" }] }  # Only process files in Invoices/ prefix
    }
  })
}

resource "aws_cloudwatch_event_target" "invoice_processor" {
  rule      = aws_cloudwatch_event_rule.s3_to_processor.name
  target_id = "InvoiceProcessorLambda"
  arn       = aws_lambda_function.invoice_processor.arn
  
  retry_policy {
    maximum_retry_attempts       = 2    # Try 3 times total before DLQ
    maximum_event_age_in_seconds = 900  # Give up after 15 min if still failing
  }
  
  dead_letter_config {
    arn = aws_sqs_queue.invoice_processor_dlq.arn  # Failed events land here
  }
}
```

---

## 13. Dead Letter Queues — Resilience and Retry

### The Three DLQs

```
DLQ 1: email-poller-dlq
  Receives: Failed EventBridge scheduler events
  When triggered: Email polling Lambda crashes (Azure auth failure, S3 permission error)
  
DLQ 2: invoice-processor-dlq  ← Most critical
  Receives: Failed S3 upload events (after 3 Lambda attempts)
  When triggered: Bedrock Lambda fails (project not found, Bedrock quota exceeded)
  
DLQ 3: gvp-publisher-dlq  ← Most critical
  Receives: Failed Bedrock completion events (after 3 Lambda attempts)
  When triggered: GVP API down, credentials expired, network timeout
```

### Retry Flow

```
EventBridge delivers event to Lambda (attempt 1)
  │
  ├── Lambda succeeds → done ✓
  │
  └── Lambda fails →
      EventBridge waits (backoff) → attempt 2
      │
      ├── Lambda succeeds → done ✓
      │
      └── Lambda fails →
          EventBridge waits → attempt 3
          │
          ├── Lambda succeeds → done ✓
          │
          └── Lambda fails →
              Maximum retries exhausted
              Event sent to SQS DLQ ←──────────────────┐
              DLQ Processor Lambda triggered (SQS event) │
              DLQ Processor reads S3 metadata             │
              DLQ Processor sends SNS email alert        │
              With S3 paths, CloudWatch query, CLI cmds  │
              Ops team reads email, manually reprocesses ┘

RETRY CONFIG (Terraform):
  maximum_retry_attempts:       2    (total 3 attempts)
  maximum_event_age_in_seconds: 900  (15 min - don't retry too-old events)
```

### Lambda Async Invoke Configuration

Beyond EventBridge retries, Lambda itself has an async invoke retry config:

```hcl
# terraform/lambda.tf

resource "aws_lambda_function_event_invoke_config" "gvp_publisher" {
  function_name = aws_lambda_function.gvp_publisher.function_name
  
  maximum_retry_attempts      = 2    # Lambda-level retries
  maximum_event_age_in_seconds = 3600
  
  destination_config {
    on_failure {
      destination = aws_sqs_queue.gvp_publisher_dlq.arn  # Lambda failures → DLQ
    }
  }
}
```

---

## 14. Observability — CloudWatch, Metrics, and Alarms

### AWS Lambda Powertools

This project uses AWS Lambda Powertools for structured logging and custom metrics:

```python
# Without Powertools:
print(f"Email polling started. Emails found: {count}")
# → CloudWatch log: unstructured plain text. Hard to search, filter, or alert on.

# With Powertools:
logger.info("Email polling completed", extra={
    "emails_processed":            processed_count,
    "pdfs_uploaded":               pdf_count,
    "inline_attachments_skipped":  skipped_inline_count,
    "total_errors":                len(errors),
    "correlation_id":              correlation_id,
})
# → CloudWatch log: structured JSON
# {
#   "level": "INFO",
#   "service": "invoice_email_poller",
#   "timestamp": "2025-12-17T14:30:22.123Z",
#   "function_name": "prod-freight-audit-agent-email-poller",
#   "request_id": "abc123-...",
#   "emails_processed": 3,
#   "pdfs_uploaded": 5,
#   "correlation_id": "a3f8c921-...",
#   "message": "Email polling completed"
# }

# Why JSON logs matter:
# ✓ CloudWatch Logs Insights can query any field
# ✓ Filter: filter emails_processed > 10
# ✓ Group: stats count() by service
# ✓ Alert: alarm if total_errors > 5
```

### Custom CloudWatch Metrics

```python
# Each Lambda emits metrics to CloudWatch Metrics

# Email Poller metrics:
metrics.add_metric(name="EmailsFound",     unit=MetricUnit.Count,        value=len(unread_emails))
metrics.add_metric(name="PDFsUploaded",    unit=MetricUnit.Count,        value=1)  # per PDF
metrics.add_metric(name="EmailsProcessed", unit=MetricUnit.Count,        value=processed_count)
metrics.add_metric(name="EmailPollDuration", unit=MetricUnit.Milliseconds, value=total_duration_ms)

# Bedrock Processor metrics:
metrics.add_metric(name="BedrockJobsStarted", unit=MetricUnit.Count, value=1)

# GVP Publisher metrics:
metrics.add_metric(name="GVPPostsSuccessful", unit=MetricUnit.Count, value=1)
metrics.add_metric(name="GVPPostsDuplicate",  unit=MetricUnit.Count, value=1)  # idempotent
metrics.add_metric(name="EndToEndLatency",    unit=MetricUnit.Milliseconds, value=end_to_end_ms)
metrics.add_metric(name="GVPTimeout",         unit=MetricUnit.Count, value=1)  # on timeout
```

### CloudWatch Dashboard

All metrics feed into a dashboard with these widgets:

```
DASHBOARD: FreightAuditAgent
  ┌────────────────────────┬────────────────────────┐
  │ Emails Processed Today │ GVP Posts Successful    │
  │        47              │        47               │
  └────────────────────────┴────────────────────────┘
  ┌────────────────────────┬────────────────────────┐
  │ Success Rate           │ Avg End-to-End Latency  │
  │       98.2%            │       9.4 minutes       │
  └────────────────────────┴────────────────────────┘
  ┌───────────────────────────────────────────────────┐
  │ Error Rates by Function (time series)             │
  │  email_poller: 0.0/hr                             │
  │  invoice_processor: 0.0/hr                        │
  │  gvp_publisher: 0.2/hr  ← one timeout today       │
  └───────────────────────────────────────────────────┘
  ┌───────────────────────────────────────────────────┐
  │ Throughput Over Time (PDFs processed per hour)    │
  │  9AM: ████████ 8                                  │
  │  10AM: ██████████████ 14                          │
  │  11AM: ███████████ 11                             │
  └───────────────────────────────────────────────────┘
```

### Five CloudWatch Alarms

```
ALARM 1: Email Poll Errors
  Metric: EmailPollErrors > 3 in 10 minutes
  Action: SNS email alert
  Meaning: Azure AD auth is failing or M365 mailbox unreachable

ALARM 2: GVP Post Failures
  Metric: GVPPostsFailed > 5 in 10 minutes
  Action: SNS email alert
  Meaning: GVP API is down or credentials expired

ALARM 3: No PDFs Uploaded
  Metric: PDFsUploaded == 0 for 30 minutes during business hours
  Action: SNS email alert
  Meaning: Pipeline is stuck — email poller not running or no new invoices

ALARM 4: High Latency
  Metric: EndToEndLatency p95 > 15 minutes
  Action: SNS email alert
  Meaning: Bedrock is slow (document complexity, throttling)

ALARM 5: Low Success Rate
  Metric: Success rate < 95% over 1 hour
  Action: SNS email alert
  Meaning: Systematic failures across multiple invoices
```

### CloudWatch Logs Insights Queries

```sql
-- Track one specific invoice end-to-end
fields @timestamp, function_name, message, correlation_id
| filter correlation_id = "a3f8c921-4d2b-4e78-8a1c-ef90ab123456"
| sort @timestamp asc

-- Find all recent errors
fields @timestamp, function_name, correlation_id, message
| filter level = "ERROR"
| sort @timestamp desc
| limit 50

-- Calculate average end-to-end latency
fields @timestamp, end_to_end_duration_ms
| filter function_name = "gvp_invoice_publisher"
| stats avg(end_to_end_duration_ms), p95(end_to_end_duration_ms), max(end_to_end_duration_ms) by bin(1h)

-- Count invoices by carrier
fields @timestamp, carrier
| filter function_name = "gvp_invoice_publisher" and message = "Successfully posted invoice to GVP"
| stats count() by carrier
| sort count desc

-- Find slow Bedrock jobs
fields @timestamp, correlation_id, end_to_end_duration_ms
| filter end_to_end_duration_ms > 600000  -- 10 minutes
| sort end_to_end_duration_ms desc
```

---

## 15. Infrastructure as Code — Terraform

All AWS infrastructure is defined in Terraform. This means:
- One command deploys everything
- Dev and prod are identical (same code, different variable values)
- Changes are tracked in version control

### Terraform File Structure

```
terraform/
├── variables.tf         ← Input variables (what you configure)
├── locals.tf            ← Computed values (naming conventions)
├── data.tf              ← Data sources (current AWS account, region)
├── lambda.tf            ← 5 Lambda functions + async invoke config
├── eventbridge.tf       ← Scheduler + 3 rules + retry config
├── s3.tf                ← S3 bucket + EventBridge notification config
├── sqs.tf               ← 3 DLQs (email, processor, publisher)
├── iam.tf               ← IAM roles and policies for each Lambda
├── ssm.tf               ← SSM parameters for secrets
├── cloudwatch.tf        ← Log groups, metrics, alarms, dashboard
├── bedrock.tf           ← Bedrock Data Automation project/blueprint
├── layers.tf            ← Lambda layers (MSAL, requests, etc.)
├── outputs.tf           ← Output values (ARNs, URLs, names)
└── environments/
    ├── dev.tfvars        ← Dev environment values
    └── prod.tfvars       ← Production environment values
```

### Key Terraform Resources

```hcl
# terraform/s3.tf — Enable EventBridge notifications (CRITICAL)
resource "aws_s3_bucket_notification" "invoice_bucket" {
  bucket      = aws_s3_bucket.invoices.id
  eventbridge = true   # ← This single line makes S3 → EventBridge work
}

# terraform/sqs.tf — Dead Letter Queue
resource "aws_sqs_queue" "gvp_publisher_dlq" {
  name = "${local.name_prefix}-gvp-publisher-dlq"
  
  # Keep failed messages for 14 days (time to investigate and reprocess)
  message_retention_seconds = 1209600   # 14 days
  
  # Allow EventBridge and Lambda to write messages
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = ["events.amazonaws.com", "lambda.amazonaws.com"] }
      Action    = "SQS:SendMessage"
      Resource  = "*"
    }]
  })
  
  tags = local.common_tags
}

# terraform/ssm.tf — Secrets management
resource "aws_ssm_parameter" "azure_client_secret" {
  name  = "/${var.environment}/freight-audit/azure-client-secret"
  type  = "SecureString"   # Encrypted with AWS KMS
  value = var.azure_client_secret
  # Lambda reads this at runtime — secret never in code or Lambda env vars
}

# terraform/iam.tf — Least privilege IAM for GVP Publisher
resource "aws_iam_policy" "gvp_publisher" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:HeadObject"]
        Resource = "${aws_s3_bucket.invoices.arn}/*"
        # Can ONLY read from the invoice bucket, cannot write, cannot delete
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock-data-automation-runtime:GetDataAutomationStatus"]
        Resource = "*"
        # Can check Bedrock job status but not start new jobs (not its job)
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:log-group:/aws/lambda/prod-freight-audit-agent-gvp-publisher:*"
        # Can only write to its OWN log group
      },
    ]
  })
}
```

### Environment Configuration

```hcl
# terraform/environments/prod.tfvars

environment       = "prod"
aws_region        = "us-east-1"
s3_bucket_name    = "prod-freight-audit-invoices"
invoice_s3_prefix = "Invoices/"

# Schedule: every 5 min, Mon-Fri, 8AM-6PM EST
email_poll_schedule = "cron(*/5 13-23 ? * MON-FRI *)"  # UTC (EST+5)
schedule_timezone   = "America/New_York"

# Alert email
alert_email = "ops-team@company.com"

# Lambda config
lambda_timeout     = 120   # 2 minutes (email poller — downloading large PDFs)
lambda_memory_size = 512   # 512 MB

# Bedrock project name
bedrock_project_name = "Freight_Audit_Agent"

# terraform/environments/dev.tfvars

environment   = "dev"
aws_region    = "us-east-1"
s3_bucket_name = "dev-freight-audit-invoices"
alert_email   = "developer@company.com"
lambda_memory_size = 256   # Smaller for dev (lower cost)
```

---

## 16. Request Lifecycle A to Z

Tracing one freight invoice from email receipt to Oracle database entry:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: Invoice Email Arrives (t=0)
  BNSF sends: freight_invoice_12345.pdf to freightaudit+arclin@company.com
  Subject: "BNSF Railway Invoice #BNSF-2025-12345 for November Services"
  Email sits in inbox, unread
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: EventBridge Scheduler Fires (t=0 to t=5 min)
  cron(*/5 13-23 ? * MON-FRI *) fires
  Emits custom event: {source: "custom.freight-audit", detail-type: "Scheduled Invoice Poll"}
  EventBridge Rule #1 matches → invokes invoice_email_poller Lambda
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: Email Poller Lambda Runs (t=5:00 → t=5:45)
  a. MSAL: Sends client_id + client_secret to Azure AD
  b. Azure AD: Returns JWT access token (valid 1 hour)
  c. Graph API GET /messages?$filter=isRead eq false → 1 unread email
  d. Logs: "Retrieved 1 unread emails"
  e. Graph API GET /messages/{id}/attachments → 1 PDF attachment found
  f. Filters: not inline, fileAttachment type, ends with .pdf ✓
  g. Graph API GET /attachments/{id} → base64 encoded PDF bytes
  h. Decodes base64 → 245KB PDF file bytes
  i. Generates: correlation_id = "a3f8c921-4d2b-4e78-8a1c-ef90ab123456"
  j. S3 PUT: Invoices/20251217_143022_freight_invoice_12345.pdf + metadata
  k. Graph API PATCH /messages/{id} → marks email as read
  l. Logs: "pdfs_uploaded: 1, emails_processed: 1"
  m. Metrics: EmailsFound=1, PDFsUploaded=1, EmailsProcessed=1
  n. Lambda returns: {statusCode: 200}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: S3 Emits Event (t=5:45)
  S3 upload triggers EventBridge notification:
  {
    "source": "aws.s3",
    "detail-type": "Object Created",
    "detail": {
      "bucket": {"name": "devgvpbucket1"},
      "object": {"key": "Invoices/20251217_143022_freight_invoice_12345.pdf"}
    }
  }
  EventBridge Rule #2 matches (Invoices/ prefix) → invokes bedrock_invoice_processor Lambda
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: Bedrock Processor Lambda (t=5:45 → t=5:47)
  a. Reads S3 event: bucket=devgvpbucket1, key=Invoices/...pdf
  b. S3 head_object: retrieves correlation_id from metadata
  c. logger.append_keys(correlation_id=...) → all logs now tagged
  d. Lists Bedrock projects → finds "Freight_Audit_Agent" → gets project ARN
  e. Calls invoke_data_automation_async():
     - input: s3://devgvpbucket1/Invoices/.../freight_invoice_12345.pdf
     - output: s3://devgvpbucket1/lambda-output/
     - project: Freight_Audit_Agent (uses invoice blueprint)
     - notifications: eventBridgeEnabled=True
  f. Gets back: invocation_arn = "arn:aws:bedrock-data-automation-runtime:..."
  g. Logs: "Bedrock job started successfully, invocation_arn=..."
  h. Metrics: BedrockJobsStarted=1
  i. Lambda returns in ~2 seconds (job runs async in Bedrock)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6: AWS Bedrock Processes Invoice (t=5:47 → t=13:22) [~8 minutes]
  a. Bedrock reads PDF from S3
  b. AI model reads the PDF (visual + text understanding)
  c. Applies invoice blueprint schema
  d. Extracts 18 fields:
     InvoiceNumber: "BNSF-2025-12345"        confidence: 0.98
     Carrier:       "BNSF"                    confidence: 0.99
     FeeAmount:     "45335.98"                confidence: 0.97
     Currency:      "USD"                     confidence: 0.99
     InvoiceDate:   "11/05/2025"              confidence: 0.96
     ServiceDate:   "11/01/2025"              confidence: 0.94
     OriginCity:    "Chicago"                 confidence: 0.95
     OriginState:   "IL"                      confidence: 0.98
     DestinationCity: "Denver"                confidence: 0.96
     DestinationState: "CO"                   confidence: 0.99
     BOLNumber:     "BOL-987654"              confidence: 0.91
     STCC:          "2041000"                 confidence: 0.87
     PartyName:     "Ardent Mills LLC"        confidence: 0.93
     ...
  e. Writes results to: s3://devgvpbucket1/lambda-output/JOB_ID/
  f. Emits completion event to EventBridge
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 7: EventBridge Routes Completion (t=13:22)
  Bedrock emits:
  {
    "source": "aws.bedrock-data-automation-runtime",
    "detail-type": "Data Automation Async Invocation Status Change",
    "detail": {
      "status": "SUCCEEDED",
      "input_s3_object": {"s3_bucket": "...", "name": "Invoices/...pdf"},
      "output_s3_location": {"s3_bucket": "...", "name": "lambda-output/..."}
    }
  }
  EventBridge Rule #3 matches (status=SUCCEEDED) → invokes gvp_invoice_publisher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 8: GVP Publisher Lambda (t=13:22 → t=13:27)
  a. Parses event: gets input_bucket, input_key, output_bucket, output_key
  b. S3 head_object on input PDF: retrieves correlation_id, recipient_address
     recipient_address = "freightaudit+arclin@company.com" ← client routing!
  c. Reads job_metadata.json → finds path to custom_output.json
  d. Reads custom_output.json → gets inference_results dict with 18 fields
  e. Business rule: BOLNumber "VERY-LONG-BOL-NUMBER-EXCEEDS-20-CHARS" → truncates to 20 chars
  f. Business rule: ServiceDate "11/01/2025, 11/15/2025" → takes "11/01/2025" (first)
  g. Auth: GET GVP token endpoint → Bearer token returned
  h. POST GVP API:
     {
       "InvoiceNumber": "BNSF-2025-12345",
       "Carrier": "BNSF",
       "FeeAmount": "45335.98",
       "MailboxName": "freightaudit+arclin@company.com",
       ...all 20 fields...
     }
  i. GVP returns: {"status": "success", "invoiceId": "GVP-789012"}
  j. Calculates end-to-end: now - email_received_time = 485 seconds (8.1 minutes)
  k. Logs: "Pipeline completed, end_to_end_duration_ms=485000"
  l. Metrics: GVPPostsSuccessful=1, EndToEndLatency=485000ms
  m. Lambda returns: {statusCode: 200, invoice_number: "BNSF-2025-12345", ...}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 9: Invoice Lives in GVP (t=13:27 onward)
  Invoice "BNSF-2025-12345" is now in Oracle database
  Accounts payable team can:
  ✓ See invoice in GVP dashboard
  ✓ Approve or dispute the invoice
  ✓ Trigger payment workflow
  ✓ Audit trail includes S3 PDF path for original document

TOTAL ELAPSED TIME: ~8.5 minutes from email receipt to GVP posting
HUMAN WORK REQUIRED: 0 minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 17. Cost Breakdown

### Per 1,000 Invoices Per Month

| Service | What It's Doing | Cost |
|---------|----------------|------|
| **Lambda** | 3 Lambdas × 1,000 invocations = 3,000 total, avg 30s at 512MB | $0.60 |
| **Bedrock Data Automation** | 1,000 AI extraction jobs | $50.00 |
| **S3** | 1,000 PDFs (~5MB each) + Bedrock outputs + logs | $0.12 |
| **SQS (DLQs)** | Minimal (failures only, ~0 in steady state) | $0.00 |
| **EventBridge** | ~5,000 events + scheduler invocations | $0.10 |
| **CloudWatch** | ~2 GB logs + metrics + dashboard + alarms | $7.76 |
| **SSM Parameter Store** | 4 SecureString parameters at rest | $0.00 |
| **SNS** | ~5 email alerts per month (failures) | $0.00 |
| **TOTAL** | | **~$58.58** |

**Cost per invoice: ~$0.06**

The biggest cost by far is **Bedrock Data Automation** ($50/1,000 = $0.05 per invoice). The AI extraction is where the value is delivered, so this is the justified cost.

### Cost Comparison

```
MANUAL PROCESSING (before):
  Average time per invoice: 8 minutes
  Labor cost: $25/hour
  1,000 invoices × (8/60 hours) × $25 = $3,333/month

AUTOMATED (this system):
  $58.58/month for 1,000 invoices

SAVINGS: $3,333 - $59 = $3,274/month (98.2% reduction)
ROI:     Break-even at 1 month of operation
```

---

## 18. Security Model

### Principle of Least Privilege

Each Lambda has its own IAM role with only exactly the permissions it needs:

```
Email Poller IAM Role:
  ✓ s3:PutObject on devgvpbucket1/Invoices/*  (can upload)
  ✗ s3:GetObject                               (cannot read files)
  ✗ s3:DeleteObject                            (cannot delete)
  ✗ bedrock:*                                  (no Bedrock access)
  ✓ ssm:GetParameter on azure-client-*        (can read Azure secrets)
  ✓ cloudwatch:PutMetricData                  (can write metrics)
  ✓ logs:PutLogEvents on its own log group    (can write its own logs)

Bedrock Processor IAM Role:
  ✓ s3:GetObject on devgvpbucket1/Invoices/*  (can read uploaded PDFs)
  ✓ s3:HeadObject on devgvpbucket1/Invoices/* (can read metadata)
  ✓ bedrock-data-automation:InvokeDataAutomationAsync (can start jobs)
  ✓ bedrock-data-automation:ListProjects      (can find project ARN)
  ✗ s3:PutObject                              (cannot write to S3)
  ✗ gvp:*                                     (no GVP access)

GVP Publisher IAM Role:
  ✓ s3:GetObject on devgvpbucket1/*           (can read Bedrock outputs)
  ✓ s3:HeadObject on devgvpbucket1/Invoices/* (can read metadata)
  ✗ s3:PutObject                              (cannot write)
  ✗ bedrock:*                                 (no Bedrock access)
  ✓ ssm:GetParameter on gvp-credentials-*    (can read GVP creds)
```

### Secrets Management

```
NEVER:
  azure_client_secret = "abc123def456"    ← hardcoded in code → GitHub exposure risk

ALWAYS (this system):
  # Store in SSM Parameter Store (SecureString = KMS encrypted)
  aws ssm put-parameter \
    --name "/prod/freight-audit/azure-client-secret" \
    --type "SecureString" \
    --value "abc123def456"
  
  # Lambda reads at runtime:
  azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")
  # Terraform sets this Lambda env var from SSM, never in code
```

### Network Security

```
All external API calls (Graph API, Bedrock, GVP API) use HTTPS/TLS
  ✓ Microsoft Graph: https://graph.microsoft.com
  ✓ Azure AD: https://login.microsoftonline.com
  ✓ GVP API: https://qagvp.intellitrans.com (TLS 1.2+)

S3 bucket:
  ✓ Server-side encryption at rest (AES-256)
  ✓ Bucket policy denies public access
  ✓ VPC endpoint for Lambda → S3 (no public internet traversal)

Lambda functions:
  ✓ Run in AWS-managed VPC
  ✓ No public-facing endpoints (triggered by EventBridge, not HTTP)
```

---

## 19. Common Failure Modes and Fixes

```
FAILURE 1: Azure AD Authentication Fails
  Symptom: Email poller Lambda returns 500, CloudWatch alarm fires
  Causes:
    - Client secret expired (Azure secrets expire every 1-2 years)
    - Client ID or tenant ID wrong in SSM Parameter Store
    - Application Access Policy removed from mailbox
  Fix:
    1. Check Azure AD Portal → App Registrations → Certificates & Secrets
    2. Rotate secret: aws ssm put-parameter --name /prod/.../azure-secret --value NEW_SECRET
    3. Test: python lambda_functions/invoice_email_poller/handler.py

FAILURE 2: Bedrock Project Not Found
  Symptom: invoice_processor Lambda logs "Project 'Freight_Audit_Agent' not found"
  Causes:
    - blueprint_manager Lambda was never run
    - Project is in DRAFT stage, not LIVE
    - Wrong region
  Fix:
    1. Run: aws lambda invoke --function-name bedrock_blueprint_manager --payload '{}' out.json
    2. Check: aws bedrock-data-automation list-data-automation-projects --project-stage-filter LIVE

FAILURE 3: GVP API 500 Error (Non-Duplicate)
  Symptom: gvp_publisher Lambda fails, goes to DLQ, SNS alert sent
  Causes:
    - GVP API server is down
    - GVP credentials expired
    - Missing required field (null InvoiceNumber from bad Bedrock extraction)
  Fix:
    1. Check GVP API status manually
    2. Test GVP auth: use Postman collection gvp_api.postman_collection.json
    3. Check Bedrock output: download custom_output.json from S3 and inspect fields
    4. Reprocess: move message from DLQ back to processing

FAILURE 4: Duplicate Invoices
  Symptom: gvp_publisher logs "Duplicate invoice detected"
  Cause: Lambda was retried after a success (network glitch during response)
  Status: NOT a failure — this is expected idempotency behavior
  Action: Monitor metric GVPPostsDuplicate — if consistently high, investigate why Lambdas are retrying

FAILURE 5: S3 Event Not Triggering Bedrock Lambda
  Symptom: PDF appears in S3 but invoice_processor Lambda never runs
  Causes:
    - EventBridge notifications not enabled on S3 bucket
    - EventBridge Rule #2 pattern doesn't match the S3 key prefix
    - Lambda doesn't have permission to be invoked by EventBridge
  Fix:
    1. Check S3 bucket properties → Event Bridge notifications = Enabled
    2. Test rule: aws events test-event-pattern --event-pattern FILE --event FILE
    3. Check resource-based Lambda policy allows events.amazonaws.com

FAILURE 6: Bedrock Extraction Quality Low
  Symptom: observability_helpers logs warn about low confidence (<0.70)
  Causes:
    - Scanned PDF (image-based, not text-based) → OCR quality varies
    - Unusual invoice layout not matching blueprint instructions
    - Missing field on invoice (Carrier forgot to print BOLNumber)
  Fix:
    1. Review low-confidence fields in CloudWatch logs
    2. Update blueprint instructions to be more specific
    3. Consider human review workflow for confidence < 0.70
    4. Run blueprint_manager Lambda to update blueprint and re-test
```

---

## 20. Cheatsheet

### Quick Commands

```bash
# Deploy (all infrastructure in 5 minutes)
cd terraform
terraform init
terraform apply -var-file="environments/dev.tfvars"

# One-time: create Bedrock blueprint
aws lambda invoke \
  --function-name prod-freight-audit-agent-blueprint-manager \
  --payload '{}' response.json && cat response.json

# Check all Lambda statuses
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `prod-freight-audit-agent`)].{Name:FunctionName,State:State}'

# Check DLQ depths
aws sqs get-queue-attributes \
  --queue-url "https://sqs.us-east-1.amazonaws.com/ACCOUNT/prod-freight-audit-agent-gvp-publisher-dlq" \
  --attribute-names ApproximateNumberOfMessages

# Test email poller locally
cd lambda_functions/invoice_email_poller
AZURE_CLIENT_ID=xxx AZURE_CLIENT_SECRET=yyy AZURE_TENANT_ID=zzz \
MAILBOX_EMAIL=invoices@co.com S3_BUCKET=test python handler.py

# View recent CloudWatch logs for any Lambda
aws logs tail /aws/lambda/prod-freight-audit-agent-gvp-publisher --follow

# Search logs for specific invoice by correlation_id
aws logs filter-log-events \
  --log-group-name /aws/lambda/prod-freight-audit-agent-gvp-publisher \
  --filter-pattern '"a3f8c921-4d2b-4e78-8a1c-ef90ab123456"'

# Cleanup all resources
terraform destroy -var-file="environments/dev.tfvars"
```

### Lambda Summary

| Lambda | Triggered By | Does | Critical Env Vars |
|--------|-------------|------|-------------------|
| `invoice_email_poller` | EventBridge Scheduler (5 min) | Polls M365, uploads PDFs to S3 | AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, MAILBOX_EMAIL, S3_BUCKET |
| `bedrock_invoice_processor` | S3 ObjectCreated event | Starts Bedrock async extraction job | PROJECT_NAME, AWS_REGION |
| `gvp_invoice_publisher` | Bedrock completion event | Posts invoice to GVP API | GVP_LOGIN_ID, GVP_PASSWORD |
| `bedrock_blueprint_manager` | Manual (once) | Creates Bedrock project + blueprint | — |
| `dlq_processor` | SQS DLQ message | Sends SNS email alert | SNS_INVOICE_ERROR_TOPIC_ARN |

### Invoice Fields Extracted by AI

| Field | Example | Notes |
|-------|---------|-------|
| InvoiceNumber | "BNSF-2025-12345" | Unique identifier |
| Carrier | "BNSF" | Freight carrier |
| InvoiceDate | "11/05/2025" | mm/dd/yyyy format |
| ServiceDate | "11/01/2025" | Date of service |
| FeeAmount | "45335.98" | No $ symbol, no commas |
| Currency | "USD" | Currency code |
| PartyName | "Ardent Mills LLC" | Billing party |
| OriginCity | "Chicago" | Shipment origin |
| OriginState | "IL" | 2-letter state |
| DestinationCity | "Denver" | Shipment destination |
| DestinationState | "CO" | 2-letter state |
| BOLNumber | "BOL-987654" | Max 20 chars (truncated) |
| STCC | "2041000" | 7-digit commodity code |
| FleetID | "FLT-001" | Fleet identifier |
| GLAccount | "5100-001" | General ledger account |
| CostCenter | "CC-WEST" | Cost center code |
| LeadEquipmentID | "BNSF-123456" | Equipment ID |
| Comments | "Rush delivery" | Additional notes |

### CloudWatch Metrics Reference

| Metric | Lambda | Unit | Alarm? |
|--------|--------|------|--------|
| EmailsFound | email_poller | Count | — |
| EmailsProcessed | email_poller | Count | — |
| PDFsUploaded | email_poller | Count | Yes (== 0) |
| EmailPollErrors | email_poller | Count | Yes (> 3) |
| BedrockJobsStarted | bedrock_processor | Count | — |
| GVPPostsSuccessful | gvp_publisher | Count | Yes (< 95%) |
| GVPPostsDuplicate | gvp_publisher | Count | — |
| GVPPostsFailed | gvp_publisher | Count | Yes (> 5) |
| EndToEndLatency | gvp_publisher | Milliseconds | Yes (p95 > 15 min) |
| GVPTimeout | gvp_publisher | Count | — |

---

## 21. Summary and Conclusion

### What This Project Teaches

**Event-Driven Architecture in Practice:** Three Lambda functions are completely decoupled — each knows only about its input event and output. EventBridge is the invisible orchestrator that connects them. This pattern scales to zero when no invoices arrive and handles thousands of simultaneous invoices without code changes.

**AI Extraction Without ML Code:** Bedrock Data Automation lets you extract structured data from any document type using a simple JSON schema (the blueprint). You define what fields you want and give natural-language instructions — the AI handles OCR, layout analysis, and field extraction automatically.

**Correlation IDs for Distributed Tracing:** A single UUID generated at the start of each invoice's lifecycle flows through S3 metadata into every Lambda's logs. This is the gold standard for debugging distributed systems — find any log for any invoice instantly.

**Production Error Handling:** Dead Letter Queues + DLQ Processor Lambda turns silent failures into actionable email alerts with full context (S3 paths, CloudWatch query, CLI commands, reprocessing instructions). No invoice falls through the cracks.

**Infrastructure as Code:** All 40+ AWS resources are defined in Terraform. Dev and prod are identical. New team members deploy in 5 minutes. Changes are code-reviewed in Git.

**Idempotency at Every Layer:** Lambda retries, EventBridge retries, and GVP duplicate detection work together to ensure each invoice is processed exactly once even when failures occur mid-pipeline.

### The Three Core Design Principles

```
1. DECOUPLING: No Lambda knows about other Lambdas
   → Change any stage without touching others
   → Test each stage independently

2. CONTEXT TRAVELS WITH DATA: S3 metadata carries email context
   → No database needed for correlation
   → Any Lambda can reconstruct full context from the PDF's metadata

3. FAIL LOUDLY: Every failure goes to DLQ and triggers SNS alert
   → Zero silent failures
   → Every failed invoice is recoverable manually
```

### What to Build Next

```
EXTEND THIS SYSTEM:
  1. Manual review workflow (Step Functions) for low-confidence extractions
  2. Multi-mailbox support — one system, multiple client mailboxes
  3. Cost per invoice tracking (Bedrock tokens × price per token)
  4. Invoice amount validation — cross-check FeeAmount against shipment data
  5. Dashboard: Carrier-level SLAs (avg processing time per carrier)

APPLY THESE PATTERNS TO OTHER DOCUMENT TYPES:
  - Purchase orders (PO) processing
  - Insurance claims automation
  - Medical bills processing
  - Contract data extraction
  - Expense report automation

The blueprint JSON is the only thing that changes — the entire pipeline reuses as-is.
```

### The Bottom Line

This system reduces freight invoice processing from 5-15 minutes of human data entry per invoice to **zero human time** with a cost of $0.06 per invoice. The AI extraction (Bedrock Data Automation) is the core differentiator, but the production-grade architecture around it — event-driven design, DLQs, correlation tracking, CloudWatch observability — is what makes it reliable enough to trust with real financial data.

Every pattern in this project (event-driven architecture, correlation IDs, DLQs, SSM for secrets, least-privilege IAM) applies directly to any serverless production system you build.

---

*This explanation covers every component of the `Invoice-Automation-main` project. All code examples are drawn from the actual source files. Start with deploying via Terraform, run the blueprint manager once, then test by sending a sample PDF to the monitored mailbox.*
