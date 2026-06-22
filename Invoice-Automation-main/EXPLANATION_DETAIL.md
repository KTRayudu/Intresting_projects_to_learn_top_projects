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

---

# Part 2 — How to Build This From Scratch (Complete Beginner Guide)

> **Who this is for:** Someone who has never built an AWS Lambda, never used Terraform, never worked with Microsoft Graph API. We start from zero.

---

## Table of Contents (Part 2)

- [Step 0 — Understand What You Need Before Starting](#step-0-prerequisites)
- [Step 1 — Install All Required Tools](#step-1-install-tools)
- [Step 2 — Set Up Your AWS Account](#step-2-aws-account)
- [Step 3 — Set Up Azure AD for M365 Email Access](#step-3-azure-ad)
- [Step 4 — Understand the Project Folder Structure](#step-4-folder-structure)
- [Step 5 — Write the Email Poller Lambda — Every Line Explained](#step-5-email-poller-code)
- [Step 6 — Write the Auth Module — Every Line Explained](#step-6-auth-code)
- [Step 7 — Write the Mail Client — Every Line Explained](#step-7-mail-client-code)
- [Step 8 — Write the Bedrock Processor Lambda — Every Line Explained](#step-8-bedrock-processor-code)
- [Step 9 — Write the Blueprint JSON Schema](#step-9-blueprint-json)
- [Step 10 — Write the Blueprint Manager Lambda — Every Line Explained](#step-10-blueprint-manager-code)
- [Step 11 — Write the GVP Publisher Lambda — Every Line Explained](#step-11-gvp-publisher-code)
- [Step 12 — Write the GVP Client — Every Line Explained](#step-12-gvp-client-code)
- [Step 13 — Write the DLQ Processor Lambda — Every Line Explained](#step-13-dlq-processor-code)
- [Step 14 — Write Terraform Infrastructure — Every File Explained](#step-14-terraform)
- [Step 15 — Deploy Everything Step by Step](#step-15-deploy)
- [Step 16 — Test the System End to End](#step-16-test)
- [Step 17 — Monitor and Debug](#step-17-monitor)
- [Common Mistakes Beginners Make](#common-mistakes)

---

## Step 0 — Understand What You Need Before Starting

Before you write a single line of code, you need access to three different platforms:

```
PLATFORM 1: AWS Account
  What it is: Amazon Web Services — where Lambda, S3, Bedrock all live
  Why you need it: All the processing happens here
  Cost: Free tier available for testing; ~$58/month at 1,000 invoices
  Time to set up: 10 minutes

PLATFORM 2: Microsoft Azure Account + Microsoft 365 Mailbox
  What it is: Microsoft's cloud — controls access to Outlook/Exchange mailboxes
  Why you need it: Your invoice emails arrive in a Microsoft 365 mailbox
                   You need Azure AD credentials to read those emails programmatically
  Cost: Free (Azure AD is free; you need an existing M365 subscription)
  Time to set up: 30 minutes

PLATFORM 3: GVP (IntelliTrans)
  What it is: The ERP system where invoice records are stored
  Why you need it: Target destination for extracted invoice data
  Note: This is company-specific. If you're learning without GVP,
        you can mock this part with a simple HTTP server
  Time to set up: Provided by your company

TOOLS ON YOUR LAPTOP:
  Python 3.11+    → to write and test Lambda code locally
  AWS CLI         → to interact with AWS from terminal
  Terraform       → to deploy all AWS resources
  Git             → to version control your code
```

---

## Step 1 — Install All Required Tools

### 1a. Install Python 3.11

```bash
# Check if you have Python
python3 --version

# If not installed on Ubuntu/Debian:
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv

# On Mac:
brew install python@3.11

# Verify:
python3 --version   # Should show Python 3.11.x
```

### 1b. Install AWS CLI

The AWS CLI is how you talk to AWS from your terminal — checking resources, looking at logs, testing Lambdas.

```bash
# On Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# On Mac:
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify:
aws --version   # Should show aws-cli/2.x.x
```

### 1c. Install Terraform

Terraform is the tool that reads your `.tf` files and creates AWS resources.

```bash
# Download Terraform (Linux, 64-bit):
wget https://releases.hashicorp.com/terraform/1.9.0/terraform_1.9.0_linux_amd64.zip
unzip terraform_1.9.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# On Mac:
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify:
terraform --version   # Should show Terraform v1.9.x
```

### 1d. Set Up Python Virtual Environment

A virtual environment is an isolated Python installation for this project, so packages don't conflict with other projects.

```bash
# Create a folder for this project
mkdir freight-audit-agent
cd freight-audit-agent

# Create virtual environment
python3 -m venv venv

# Activate it (do this every time you open a new terminal for this project)
source venv/bin/activate    # Linux/Mac
# OR
venv\Scripts\activate       # Windows

# You'll see (venv) at the start of your terminal prompt when active

# Install all required packages
pip install boto3 botocore aws-lambda-powertools aws-xray-sdk requests msal
pip install pytest pytest-mock pytest-cov moto responses freezegun

# Verify:
pip list    # Should show all installed packages
```

---

## Step 2 — Set Up Your AWS Account

### 2a. Create AWS Account and Get Credentials

```
1. Go to aws.amazon.com → Create account
2. Complete signup (credit card required but free tier covers testing)
3. After login, go to: IAM → Users → Create User
4. Give username: freight-audit-developer
5. Attach permission: AdministratorAccess (for development — restrict later for production)
6. Create → Download credentials (Access Key ID + Secret Access Key)
   SAVE THESE — you only see the Secret once!
```

### 2b. Configure AWS CLI with Your Credentials

```bash
aws configure

# It will ask four questions:
AWS Access Key ID [None]:     AKIAIOSFODNN7EXAMPLE   ← paste your key
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG  ← paste your secret
Default region name [None]:   us-east-1              ← use this region
Default output format [None]: json                   ← type json

# Verify it works:
aws sts get-caller-identity

# Should show:
# {
#     "UserId": "AIDAIOSFODNN7EXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/freight-audit-developer"
# }
```

### 2c. Enable Bedrock Data Automation

Bedrock Data Automation is an AI service that needs to be enabled in your account:

```
1. Go to AWS Console → Amazon Bedrock
2. Click "Get started" if first time
3. Navigate to "Model access" in left sidebar
4. Request access to: Anthropic Claude models
5. Wait for approval (usually instant for individual accounts)

Also enable Bedrock Data Automation:
1. In Bedrock console → left sidebar → "Data Automation"
2. If you see "Enable" button → click it
3. Wait for activation (1-2 minutes)
```

### 2d. Create S3 Bucket for Terraform State

Terraform saves its "memory" (what it already created) to an S3 bucket. Create this first:

```bash
# Replace YOUR_ACCOUNT_ID with your actual AWS account number (12 digits)
aws s3 mb s3://freight-audit-terraform-state --region us-east-1

# Enable versioning (so you can recover if state file gets corrupted)
aws s3api put-bucket-versioning \
    --bucket freight-audit-terraform-state \
    --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
# (Prevents two people from running terraform at the same time)
aws dynamodb create-table \
    --table-name terraform-state-lock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

---

## Step 3 — Set Up Azure AD for M365 Email Access

This is the most confusing part for beginners. Let's go through it slowly.

### What Is Azure AD and Why Do You Need It?

```
Microsoft 365 mailboxes are protected by Microsoft's authentication system called Azure AD
(Azure Active Directory, now called "Entra ID").

To read emails from a mailbox PROGRAMMATICALLY (no human login), you need to:
  1. Register your application in Azure AD (like getting an ID card for your code)
  2. Grant it permission to read emails
  3. Get three credentials: client_id, client_secret, tenant_id
  4. Your Lambda uses these to get an access token → use token to call Graph API

Think of it like a hotel key card:
  - Azure AD = the hotel front desk
  - Your app registration = checking in and getting a key card
  - client_id + client_secret = your room number + personal PIN
  - access_token = the key card that opens the mailbox door
```

### 3a. Create an Azure AD App Registration

```
1. Go to portal.azure.com → sign in with your Microsoft/work account
2. Search for "Azure Active Directory" or "Microsoft Entra ID"
3. Left sidebar → "App registrations" → "New registration"
4. Fill in:
     Name: freight-audit-agent
     Supported account types: "Accounts in this organizational directory only"
     Redirect URI: Leave blank (we don't need browser login)
5. Click "Register"

SAVE THESE VALUES — you'll see them on the App Registration overview page:
  Application (client) ID:   xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  ← AZURE_CLIENT_ID
  Directory (tenant) ID:     yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy  ← AZURE_TENANT_ID
```

### 3b. Create a Client Secret

```
1. In your App Registration → left sidebar → "Certificates & secrets"
2. "Client secrets" tab → "New client secret"
3. Description: freight-audit-lambda
4. Expires: 24 months (don't use "never" — it's a security risk)
5. Click "Add"

SAVE THIS IMMEDIATELY — the secret value is shown ONCE:
  Value: AbCdEfGhIj~KLmNoPqRsTuVwXy.1234567890  ← AZURE_CLIENT_SECRET
```

### 3c. Grant Email Permissions

```
1. In your App Registration → left sidebar → "API permissions"
2. "Add a permission" → "Microsoft Graph"
3. "Application permissions" (NOT Delegated — Application runs without a user)
4. Search for "Mail" → expand → check "Mail.ReadWrite"
5. "Add permissions"
6. IMPORTANT: Click "Grant admin consent for [your org]"
   (Without this step, the permissions don't actually work)
   → A green checkmark should appear
```

### 3d. Grant Mailbox Access

Even with permissions, the app needs explicit access to specific mailboxes:

```bash
# Install Microsoft PowerShell (or use Azure Cloud Shell)
# Then run this to grant access to the specific mailbox:

# Option A: Via Exchange Admin Center (GUI):
# 1. admin.exchange.microsoft.com
# 2. Recipients → Mailboxes → select invoices@yourcompany.com
# 3. Manage mailbox delegation → Full Access → Add your app

# Option B: Via PowerShell:
Install-Module ExchangeOnlineManagement
Connect-ExchangeOnline

# Grant your app access to the mailbox
Add-MailboxPermission -Identity "invoices@yourcompany.com" \
    -User "freight-audit-agent" \
    -AccessRights FullAccess \
    -InheritanceType All
```

### 3e. Test Your Azure Credentials

Before building anything, verify your credentials work:

```python
# Save this as test_azure_auth.py and run it locally:
from msal import ConfidentialClientApplication

client_id     = "YOUR_CLIENT_ID_HERE"
client_secret = "YOUR_CLIENT_SECRET_HERE"
tenant_id     = "YOUR_TENANT_ID_HERE"
mailbox       = "invoices@yourcompany.com"

app = ConfidentialClientApplication(
    client_id=client_id,
    client_credential=client_secret,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
)

result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

if "access_token" in result:
    print("SUCCESS! Got access token.")
    print(f"Token starts with: {result['access_token'][:50]}...")
    
    # Test listing emails
    import requests
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages?$top=1",
        headers={"Authorization": f"Bearer {result['access_token']}"}
    )
    print(f"Email API response: {response.status_code}")
    if response.status_code == 200:
        emails = response.json().get("value", [])
        print(f"Found {len(emails)} emails")
    else:
        print(f"Error: {response.text}")
else:
    print(f"FAILED: {result.get('error')} - {result.get('error_description')}")
```

```bash
# Run it:
python test_azure_auth.py

# If it prints "SUCCESS! Got access token." and a status 200 → you're ready
# If not → re-check Step 3a-3d
```

---

## Step 4 — Understand the Project Folder Structure

```
freight-audit-agent/              ← root folder (your project)
│
├── requirements.txt              ← lists all Python packages needed
│
├── lambda_functions/             ← all Lambda code lives here
│   ├── invoice_email_poller/     ← Lambda 1: reads email, uploads to S3
│   │   ├── handler.py            ← main function called by AWS Lambda
│   │   ├── auth.py               ← Azure AD authentication
│   │   └── mail_client.py        ← Microsoft Graph API calls
│   │
│   ├── bedrock_blueprint_manager/  ← Lambda 2: one-time Bedrock setup
│   │   ├── handler.py
│   │   ├── bedrock_helpers.py
│   │   └── bedrock_invoice_blueprint.json  ← the AI extraction schema
│   │
│   ├── bedrock_invoice_processor/  ← Lambda 3: starts Bedrock AI job
│   │   └── handler.py
│   │
│   ├── gvp_invoice_publisher/    ← Lambda 4: posts to GVP/Oracle
│   │   ├── handler.py
│   │   └── gvp_client.py
│   │
│   └── dlq_processor/           ← Lambda 5: handles failures, sends alerts
│       └── handler.py
│
├── lambda_layers/                ← extra Python packages for Lambda
│   └── msal_requests_layer.zip  ← msal + requests bundled as a Layer
│
├── terraform/                   ← all AWS infrastructure definitions
│   ├── versions.tf              ← Terraform + AWS provider versions
│   ├── variables.tf             ← all configurable inputs
│   ├── locals.tf                ← computed naming values
│   ├── data.tf                  ← reads existing AWS resources
│   ├── lambda.tf                ← 5 Lambda function definitions
│   ├── eventbridge.tf           ← 3 EventBridge rules + scheduler
│   ├── s3.tf                    ← S3 bucket
│   ├── sqs.tf                   ← 3 Dead Letter Queues
│   ├── iam.tf                   ← IAM roles and policies
│   ├── ssm.tf                   ← secrets in SSM Parameter Store
│   ├── cloudwatch.tf            ← logs, metrics, alarms, dashboard
│   ├── bedrock.tf               ← Bedrock project (optional)
│   ├── layers.tf                ← Lambda Layer (msal + requests)
│   ├── outputs.tf               ← prints useful values after deploy
│   └── environments/
│       ├── dev.tfvars           ← dev configuration values
│       └── prod.tfvars          ← production configuration values
│
├── test_data/                   ← sample PDF invoices for testing
│   ├── invoice.pdf
│   └── BNSF switching bill.pdf
│
└── tests/                       ← automated tests
    ├── test_invoice_email_poller/
    ├── test_bedrock_invoice_processor/
    └── test_gvp_invoice_publisher/
```

### The Golden Rule of This Structure

```
Each Lambda function is its own subfolder.
Each folder has handler.py as the entry point.
AWS Lambda always calls: handler.lambda_handler(event, context)
                         ↑ filename  ↑ function name (in lambda.tf: handler = "handler.lambda_handler")
```

---

## Step 5 — Write the Email Poller Lambda — Every Line Explained

Create this file: `lambda_functions/invoice_email_poller/handler.py`

Here is the complete code with every single line explained:

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMPORTS — pulling in libraries we need
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import os          # to read environment variables (like MAILBOX_EMAIL)
import json        # to convert Python dicts to JSON strings
import boto3       # AWS SDK — to talk to S3
import base64      # to decode PDF bytes from Microsoft Graph
import uuid        # to generate unique IDs (UUIDs)
import time        # to measure how long the function takes
import re          # regular expressions — for filename sanitization
from datetime import datetime    # for timestamps
from urllib.parse import quote   # for URL-encoding filenames

# AWS Lambda Powertools — gives us structured logging + CloudWatch metrics
# "Lambda Powertools" is a library made by AWS specifically for Lambda functions
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Our custom modules (files we write ourselves):
from auth import GraphAuthenticator       # handles Azure AD login
from mail_client import GraphMailClient   # handles reading emails

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL OBJECTS — created ONCE when Lambda starts (cold start)
# Not inside the handler function — so they persist between warm invocations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Logger: every call to logger.info(), logger.error() etc. produces
# structured JSON in CloudWatch Logs automatically tagged with service name
logger = Logger(service="invoice_email_poller")

# Metrics: every call to metrics.add_metric() goes to CloudWatch Metrics
# namespace = "FreightAuditAgent" → this is like a folder name in CloudWatch
metrics = Metrics(namespace="FreightAuditAgent")

# S3 client: allows uploading files to S3
s3_client = boto3.client('s3')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sanitize_filename(filename):
    """
    Clean up a filename so it's safe to use as an S3 key.
    
    WHY: Email attachments can have names like "Invoice #12345 (BNSF).pdf"
    S3 keys can have spaces but they become %20 in URLs — messy.
    Also removes characters that can break file systems.
    """
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Keep only: letters, numbers, dots, dashes, underscores
    # Remove everything else (parentheses, #, $, etc.)
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    
    return filename


def sanitize_metadata_value(value):
    """
    Clean a string so it's safe to store as S3 metadata.
    
    WHY: S3 metadata is stored as HTTP headers.
    HTTP headers cannot contain newlines (\n), carriage returns (\r), or tabs (\t).
    Email subjects often have these characters.
    If you don't remove them, S3 will return a 400 error.
    """
    value_str = str(value)
    
    # Remove newline characters
    value_str = value_str.replace('\r\n', ' ')  # Windows-style newline
    value_str = value_str.replace('\r', ' ')     # Old Mac-style newline
    value_str = value_str.replace('\n', ' ')     # Unix newline
    value_str = value_str.replace('\t', ' ')     # Tab character
    
    # Remove any other control characters (ASCII 0-31 and 127)
    # ord(char) gets the ASCII number of a character
    # Control characters have numbers 0-31 and 127
    value_str = ''.join(
        char if ord(char) >= 32 and ord(char) != 127 else ' '
        for char in value_str
    )
    
    # Collapse multiple spaces into one
    value_str = ' '.join(value_str.split())
    
    return value_str

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN HANDLER — AWS Lambda calls this function for every invocation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# These are DECORATORS — Python's way to wrap a function with extra behavior.
# @logger.inject_lambda_context → adds Lambda request_id to every log message
# log_event=True → also logs the incoming event (the EventBridge JSON payload)
# @metrics.log_metrics → sends all metrics to CloudWatch when function finishes
# capture_cold_start_metric=True → tracks when Lambda wakes from scratch (slow start)
@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    """
    Main Lambda handler — called by EventBridge every 5 minutes.
    
    Parameters:
        event:   the JSON payload sent by EventBridge Scheduler
        context: Lambda runtime info (function name, request ID, timeout remaining)
    
    Returns:
        dict with statusCode and body (standard Lambda response format)
    """
    
    # Record start time so we can measure how long this function takes
    start_time = time.time()
    
    # ── STEP 1: Read configuration from environment variables ──
    # Environment variables are set by Terraform (from SSM Parameter Store)
    # We use os.getenv() instead of os.environ[] so we can provide defaults
    
    client_id     = os.getenv("AZURE_CLIENT_ID")      # Azure app ID
    client_secret = os.getenv("AZURE_CLIENT_SECRET")  # Azure app password
    tenant_id     = os.getenv("AZURE_TENANT_ID")      # Azure directory ID
    mailbox_email = os.getenv("MAILBOX_EMAIL")        # Which mailbox to monitor
    s3_bucket     = os.getenv("S3_BUCKET", "devgvpbucket1")    # S3 bucket name
    s3_prefix     = os.getenv("S3_PREFIX") or "Invoices/"      # Folder inside bucket
    
    # ── STEP 2: Validate required config ──
    # If any critical config is missing, fail fast with a clear error message
    # This is better than getting a confusing error deep in the code later
    required_vars = {
        "AZURE_CLIENT_ID": client_id,
        "AZURE_CLIENT_SECRET": client_secret,
        "AZURE_TENANT_ID": tenant_id,
        "MAILBOX_EMAIL": mailbox_email
    }
    
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        error_msg = f"Missing required environment variables: {missing}"
        logger.error(error_msg)
        # Count this as a configuration error in CloudWatch
        metrics.add_metric(name="ConfigurationError", unit=MetricUnit.Count, value=1)
        return {'statusCode': 500, 'body': json.dumps({'error': error_msg})}
    
    # ── STEP 3: Authenticate with Microsoft Graph API ──
    logger.info("Starting email poll", extra={"mailbox": mailbox_email})
    
    # Create the authenticator object (from our auth.py file)
    authenticator = GraphAuthenticator(client_id, client_secret, tenant_id)
    
    # Get an access token (valid for 1 hour)
    # This calls Azure AD's OAuth 2.0 token endpoint
    access_token = authenticator.get_access_token()
    
    # ── STEP 4: Fetch unread emails ──
    # Create the mail client with our token
    mail_client = GraphMailClient(access_token, mailbox_email)
    
    # Get list of unread emails (up to 50)
    unread_emails = mail_client.get_unread_emails()
    
    logger.info(f"Retrieved {len(unread_emails)} unread emails")
    metrics.add_metric(name="EmailsFound", unit=MetricUnit.Count, value=len(unread_emails))
    
    # ── STEP 5: Process each email ──
    processed_count = 0  # how many emails we successfully handled
    pdf_count = 0        # how many PDFs we uploaded to S3
    errors = []          # collect errors (don't stop on first error)
    
    for email in unread_emails:
        
        # Extract email fields from the Graph API response JSON
        email_id        = email.get("id")            # Microsoft's unique ID for this email
        subject         = email.get("subject", "(No Subject)")
        has_attachments = email.get("hasAttachments", False)
        received        = email.get("receivedDateTime", "")   # ISO 8601 timestamp
        
        # Extract sender info (nested inside "from" → "emailAddress")
        from_data    = email.get("from", {})
        sender_info  = from_data.get("emailAddress", {})
        sender_email = sender_info.get("address", "")
        sender_name  = sender_info.get("name", "")
        
        # Extract recipient address (important for "plus addressing" routing)
        # The email was sent to freightaudit+CLIENTCODE@company.com
        # We need to capture the full recipient address for GVP routing
        to_recipients    = email.get("toRecipients", [])
        recipient_address = ""
        if to_recipients:
            # Take the first "To:" recipient
            first_recipient  = to_recipients[0]
            recipient_info   = first_recipient.get("emailAddress", {})
            recipient_address = recipient_info.get("address", "")
        
        # If this email has no attachments at all, skip it
        if not has_attachments:
            logger.info(f"Skipping email with no attachments: {subject}")
            # Still mark as read so we don't check it again
            mail_client.mark_as_read(email_id)
            processed_count += 1
            continue
        
        # ── Get attachment list for this email ──
        attachments = mail_client.get_email_attachments(email_id)
        
        email_had_pdf = False  # track if this email had at least one PDF
        
        for attachment in attachments:
            
            attachment_name = attachment.get("name", "unnamed")
            attachment_size = attachment.get("size", 0)
            is_inline       = attachment.get("isInline", False)
            attachment_type = attachment.get("@odata.type", "")
            attachment_id   = attachment.get("id")
            
            # ── Filter 1: Skip inline attachments ──
            # Inline attachments are embedded images in the email body
            # (company logos, email signatures, etc.)
            # We only want actual file attachments
            if is_inline:
                logger.info(f"Skipping inline attachment: {attachment_name}")
                continue
            
            # ── Filter 2: Only file attachments ──
            # "@odata.type" tells us what kind of attachment this is
            # "#microsoft.graph.fileAttachment" = actual file (what we want)
            # "#microsoft.graph.itemAttachment" = embedded email (not what we want)
            if attachment_type != "#microsoft.graph.fileAttachment":
                logger.info(f"Skipping non-file attachment type: {attachment_type}")
                continue
            
            # ── Filter 3: Only PDFs ──
            # We're looking for invoice PDFs, not Word docs or Excel sheets
            if not attachment_name.lower().endswith('.pdf'):
                logger.info(f"Skipping non-PDF: {attachment_name}")
                continue
            
            # ── This is a PDF file attachment — process it ──
            
            try:
                # Download the attachment content (returns base64 encoded string)
                attachment_content = mail_client.get_attachment_content(email_id, attachment_id)
                
                # Decode from base64 to raw bytes
                # Microsoft Graph API always returns file content as base64
                # base64.b64decode() converts it back to the original binary data
                file_content = base64.b64decode(attachment_content)
                
                # ── Generate Correlation ID ──
                # UUID4 = random 128-bit number shown as a hex string with dashes
                # Example: "a3f8c921-4d2b-4e78-8a1c-ef90ab123456"
                # This ID is attached to EVERY log message for this invoice
                # so you can trace one invoice through all 5 Lambda functions
                correlation_id = str(uuid.uuid4())
                
                # ── Build S3 key ──
                # Format: Invoices/20251217_143022_BNSF_Invoice_12345.pdf
                timestamp    = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                safe_filename = sanitize_filename(attachment_name)
                s3_key       = f"{s3_prefix}{timestamp}_{safe_filename}"
                
                # ── Build S3 metadata ──
                # ALL context about this invoice is stored here as key-value pairs
                # Downstream Lambdas will call head_object() to read these values
                # S3 metadata keys MUST be lowercase (AWS requirement)
                metadata = {
                    'correlation-id':           sanitize_metadata_value(correlation_id),
                    'mailbox-id':               sanitize_metadata_value(mailbox_email)[:100],
                    'email-recipient-address':  sanitize_metadata_value(recipient_address)[:100],
                    'email-id':                 sanitize_metadata_value(email_id)[:100],
                    'email-subject':            sanitize_metadata_value(subject)[:200],
                    'email-sender-email':       sanitize_metadata_value(sender_email)[:100],
                    'email-sender-name':        sanitize_metadata_value(sender_name)[:100],
                    'email-received-time':      sanitize_metadata_value(received)[:50],
                    'original-filename':        sanitize_metadata_value(attachment_name)[:200],
                    'attachment-size':          str(attachment_size),
                    'upload-timestamp':         sanitize_metadata_value(datetime.utcnow().isoformat()),
                    'processing-status':        'pending',
                }
                
                # ── Upload PDF to S3 ──
                s3_client.put_object(
                    Bucket=s3_bucket,          # which bucket
                    Key=s3_key,                # path within bucket
                    Body=file_content,         # the actual PDF bytes
                    ContentType='application/pdf',
                    Metadata=metadata,          # our tracking data
                )
                
                logger.info(
                    "PDF uploaded to S3",
                    extra={
                        "correlation_id": correlation_id,
                        "s3_key": s3_key,
                        "attachment_name": attachment_name,
                        "attachment_size": attachment_size,
                        "sender": sender_email,
                    }
                )
                
                # Count this metric (CloudWatch will aggregate these)
                metrics.add_metric(name="PDFsUploaded", unit=MetricUnit.Count, value=1)
                pdf_count += 1
                email_had_pdf = True
                
            except Exception as e:
                # Log the error but continue to next attachment
                # We don't want one bad PDF to stop us processing others
                error_msg = f"Failed to process attachment {attachment_name}: {str(e)}"
                logger.error(error_msg, extra={"email_subject": subject})
                errors.append(error_msg)
        
        # ── Mark email as read ──
        # This prevents the next poll (5 minutes later) from processing same email again
        mail_client.mark_as_read(email_id)
        processed_count += 1
    
    # ── STEP 6: Log summary and return ──
    duration_ms = int((time.time() - start_time) * 1000)  # convert seconds to milliseconds
    
    logger.info(
        "Email polling completed",
        extra={
            "emails_found":     len(unread_emails),
            "emails_processed": processed_count,
            "pdfs_uploaded":    pdf_count,
            "total_errors":     len(errors),
            "duration_ms":      duration_ms,
        }
    )
    
    metrics.add_metric(name="EmailsProcessed", unit=MetricUnit.Count, value=processed_count)
    metrics.add_metric(name="EmailPollDuration", unit=MetricUnit.Milliseconds, value=duration_ms)
    
    # Return standard Lambda response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'emails_processed': processed_count,
            'pdfs_uploaded': pdf_count,
            'errors': errors,
        })
    }
```

---

## Step 6 — Write the Auth Module — Every Line Explained

Create: `lambda_functions/invoice_email_poller/auth.py`

```python
"""
Handles Azure Active Directory authentication using MSAL.

MSAL = Microsoft Authentication Library
It handles all the complexity of OAuth 2.0 token requests.
We use the "client credentials flow" — server-to-server auth with no user.
"""

from msal import ConfidentialClientApplication


class GraphAuthenticator:
    """
    Gets OAuth 2.0 access tokens from Azure AD.
    
    Think of this class as "the login helper".
    You create one, call get_access_token(), and get back a token.
    The token lets you call Microsoft Graph API endpoints.
    """
    
    def __init__(self, client_id, client_secret, tenant_id):
        """
        Set up the authenticator with your Azure app credentials.
        
        client_id:     Your Azure App Registration's "Application (client) ID"
        client_secret: The secret you created in "Certificates & secrets"
        tenant_id:     Your Azure AD "Directory (tenant) ID"
        """
        
        # Authority URL = which Azure tenant to authenticate against
        # Format: https://login.microsoftonline.com/{your-tenant-id}
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        
        # ConfidentialClientApplication = for server apps (no browser, no user)
        # vs PublicClientApplication = for desktop/mobile apps with user login
        # We're a Lambda function → we use ConfidentialClientApplication
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,   # this is the "password" for the app
            authority=self.authority,
        )
        
        # Scopes = what permissions we're requesting
        # ".default" means: grant all permissions that were configured in the Azure portal
        # (We configured Mail.ReadWrite in Step 3c above)
        self.scopes = ["https://graph.microsoft.com/.default"]
    
    def get_access_token(self) -> str:
        """
        Get an access token using client credentials flow.
        
        Flow:
        1. Send client_id + client_secret to Azure AD
        2. Azure AD verifies → returns a JWT access token (valid 1 hour)
        3. We return the token string
        
        The token is then put in HTTP headers:
        "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        """
        
        # acquire_token_for_client = client credentials grant (no user involved)
        result = self.app.acquire_token_for_client(scopes=self.scopes)
        
        # Check if we got a token
        if "access_token" in result:
            return result["access_token"]
        else:
            # If auth failed, result contains error info
            error       = result.get("error", "unknown_error")
            description = result.get("error_description", "No description")
            raise Exception(
                f"Failed to acquire Azure AD token: {error} — {description}\n"
                f"Check: client_id, client_secret, tenant_id, and admin consent for Mail.ReadWrite"
            )
```

---

## Step 7 — Write the Mail Client — Every Line Explained

Create: `lambda_functions/invoice_email_poller/mail_client.py`

```python
"""
Microsoft Graph API client for reading emails.

The Microsoft Graph API is a REST API.
Every call is just an HTTP request with the access token in the header.
"""

import requests  # Python library for making HTTP requests


class GraphMailClient:
    """Makes API calls to Microsoft Graph to read emails."""
    
    def __init__(self, access_token, mailbox_email):
        self.access_token  = access_token
        self.mailbox_email = mailbox_email
        
        # Base URL for all Microsoft Graph API calls
        self.base_url = "https://graph.microsoft.com/v1.0"
        
        # HTTP headers required for every API call:
        # Authorization: Bearer TOKEN → proves who we are
        # Content-Type: application/json → tells server we're sending JSON
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_unread_emails(self, folder="inbox", top=50):
        """
        Get list of unread emails from the inbox.
        
        Returns a list of dicts, each representing one email.
        Example: [{id:"abc", subject:"Invoice", from:{...}, hasAttachments:true}, ...]
        """
        
        # URL pattern: /users/{mailbox}/mailFolders/{folder}/messages
        url = f"{self.base_url}/users/{self.mailbox_email}/mailFolders/{folder}/messages"
        
        # Query parameters that filter the response:
        params = {
            # $filter: only get unread emails (isRead eq false)
            "$filter": "isRead eq false",
            
            # $top: max number to return (50 per API call)
            "$top": top,
            
            # $select: only return these fields (makes response smaller/faster)
            # We don't need body content — just metadata to identify attachments
            "$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,bodyPreview",
            
            # $orderby: newest emails first
            "$orderby": "receivedDateTime desc"
        }
        
        # Make the GET request
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            # Graph API wraps results in a "value" array
            data = response.json()
            return data.get("value", [])
        else:
            raise Exception(
                f"Failed to get emails: {response.status_code} — {response.text}"
            )
    
    def get_email_attachments(self, message_id):
        """Get list of attachments for a specific email (by its ID)."""
        
        url = f"{self.base_url}/users/{self.mailbox_email}/messages/{message_id}/attachments"
        params = {
            # Only get these fields — we don't need the actual content yet
            "$select": "id,name,contentType,size,isInline,@odata.type"
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json().get("value", [])
        else:
            raise Exception(
                f"Failed to get attachments: {response.status_code} — {response.text}"
            )
    
    def get_attachment_content(self, message_id, attachment_id):
        """
        Download the content of one specific attachment.
        
        Returns: base64-encoded string of the file contents.
        The handler.py then calls base64.b64decode() to get the actual bytes.
        """
        
        url = f"{self.base_url}/users/{self.mailbox_email}/messages/{message_id}/attachments/{attachment_id}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            attachment_data = response.json()
            # "contentBytes" is the base64-encoded file content
            content_bytes = attachment_data.get("contentBytes")
            
            if content_bytes:
                return content_bytes
            else:
                raise Exception("Attachment has no content (contentBytes is null)")
        else:
            raise Exception(
                f"Failed to get attachment content: {response.status_code} — {response.text}"
            )
    
    def mark_as_read(self, message_id):
        """
        Mark an email as read.
        
        Why: Without this, the email stays unread.
        Next poll (5 min later) would pick it up AGAIN and re-upload the PDF.
        Marking as read = "we processed this, don't process again"
        """
        
        url = f"{self.base_url}/users/{self.mailbox_email}/messages/{message_id}"
        
        # PATCH = update just one field of the email object
        # We're setting isRead to True
        response = requests.patch(
            url,
            headers=self.headers,
            json={"isRead": True}  # json= automatically sets Content-Type header
        )
        
        # 200 = updated with response body, 204 = updated with no body
        # Both mean success for PATCH
        if response.status_code not in [200, 204]:
            raise Exception(
                f"Failed to mark as read: {response.status_code} — {response.text}"
            )
```

---

## Step 8 — Write the Bedrock Processor Lambda — Every Line Explained

Create: `lambda_functions/bedrock_invoice_processor/handler.py`

```python
"""
Triggered by S3 EventBridge notification when a PDF is uploaded.
Starts an asynchronous Bedrock Data Automation job to extract invoice fields.
"""

import os
import json
import boto3
from urllib.parse import unquote_plus   # to decode URL-encoded S3 keys
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger  = Logger(service="bedrock_invoice_processor")
metrics = Metrics(namespace="FreightAuditAgent")

# We need TWO separate Bedrock clients:
# bedrock-data-automation = control plane (list projects, create blueprints)
# bedrock-data-automation-runtime = data plane (actually run jobs on documents)
s3_client          = boto3.client('s3')
bda_client         = boto3.client('bedrock-data-automation')
bda_runtime_client = boto3.client('bedrock-data-automation-runtime')


@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    """
    Called when a PDF lands in S3 (via EventBridge S3 notification).
    
    The event looks like:
    {
        "source": "aws.s3",
        "detail-type": "Object Created",
        "detail": {
            "bucket": {"name": "devgvpbucket1"},
            "object": {"key": "Invoices/20251217_143022_BNSF_Invoice.pdf"}
        }
    }
    """
    
    region = os.environ.get('AWS_REGION', 'us-east-1')  # where we're running
    
    # ── STEP 1: Extract which file was uploaded ──
    # The S3 key may have URL encoding: spaces become %20, # becomes %23 etc.
    # unquote_plus() decodes it back to the original string
    s3_bucket = event["detail"]["bucket"]["name"]
    s3_key    = unquote_plus(event["detail"]["object"]["key"])
    
    logger.info("Processing S3 upload event", extra={
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
    })
    
    # ── STEP 2: Read correlation_id from S3 metadata ──
    # head_object = get metadata without downloading the file
    # Cheaper than get_object when you only need metadata
    s3_response = s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
    s3_metadata  = s3_response.get('Metadata', {})
    
    # correlation_id was set by the email poller when it uploaded this PDF
    correlation_id = s3_metadata.get('correlation-id', 'unknown')
    
    # Add to logger so ALL subsequent log messages include this ID
    logger.append_keys(correlation_id=correlation_id)
    
    # ── STEP 3: Find our Bedrock project ──
    # We need the project's ARN (Amazon Resource Name) to start a job
    # The blueprint_manager Lambda created this project — we just look it up
    project_name = os.getenv("PROJECT_NAME", "Freight_Audit_Agent")
    
    # List all LIVE projects (DRAFT projects are for testing, LIVE = production)
    response = bda_client.list_data_automation_projects(projectStageFilter='LIVE')
    all_projects = response.get('projects', [])
    
    # Find our specific project by name
    project = next(
        (p for p in all_projects if p['projectName'] == project_name),
        None
    )
    
    if not project:
        error = f"Bedrock project '{project_name}' not found in LIVE stage. Run blueprint_manager first."
        logger.error(error)
        raise ValueError(error)  # Raising an exception triggers EventBridge retry → DLQ
    
    project_arn = project['projectArn']
    logger.info(f"Found Bedrock project: {project_arn}")
    
    # ── STEP 4: Configure output location ──
    # Where Bedrock will write the extracted JSON results
    output_bucket = os.getenv("OUTPUT_BUCKET", s3_bucket)
    output_prefix = os.getenv("OUTPUT_PREFIX", "freight-audit-agent-output/")
    
    # The data automation profile ARN tells Bedrock WHICH AI model to use
    # This is an AWS-managed ARN — you don't create it, just reference it
    data_automation_profile_arn = os.getenv("DATA_AUTOMATION_PROFILE_ARN",
        f"arn:aws:bedrock:{region}:{context.invoked_function_arn.split(':')[4]}:data-automation-profile/us.data-automation-v1"
    )
    
    # ── STEP 5: Start the async Bedrock job ──
    response = bda_runtime_client.invoke_data_automation_async(
        
        # Where is the PDF?
        inputConfiguration={
            's3Uri': f's3://{s3_bucket}/{s3_key}'
        },
        
        # Where to write results?
        outputConfiguration={
            's3Uri': f's3://{output_bucket}/{output_prefix}'
        },
        
        # Which AI model to use (the AWS-managed profile)
        dataAutomationProfileArn=data_automation_profile_arn,
        
        # Which blueprint (schema) to apply
        dataAutomationConfiguration={
            'dataAutomationProjectArn': project_arn
        },
        
        # Tell Bedrock: when you finish, emit a completion event to EventBridge
        # This is what triggers the GVP Publisher Lambda automatically
        notificationConfiguration={
            'eventBridgeConfiguration': {
                'eventBridgeEnabled': True
            }
        }
    )
    
    invocation_arn = response["invocationArn"]
    
    logger.info("Bedrock job started successfully", extra={
        "invocation_arn": invocation_arn,
        "project_arn": project_arn,
        "input_s3_uri": f"s3://{s3_bucket}/{s3_key}",
    })
    
    metrics.add_metric(name="BedrockJobsStarted", unit=MetricUnit.Count, value=1)
    
    # Return immediately — Bedrock runs asynchronously (we don't wait for it)
    return {
        'statusCode': 200,
        'body': json.dumps({
            'invocation_arn': invocation_arn,
            'correlation_id': correlation_id,
        })
    }
```

---

## Step 9 — Write the Blueprint JSON Schema

Create: `lambda_functions/bedrock_blueprint_manager/bedrock_invoice_blueprint.json`

This JSON file tells Bedrock's AI what to extract from the PDF. It's like writing a checklist for the AI: "look for these fields, here's how to find them."

```json
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
      "instruction": "Extract the invoice number or invoice ID from the document. This is a unique identifier for the invoice."
    },
    
    "Carrier": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the carrier name - the company billing for freight services. Common carriers: BNSF, UP (Union Pacific), CSX, NS (Norfolk Southern), KCS, CP, CN, PGTX"
    },
    
    "Currency": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the currency code (e.g., USD, CAD). Default to USD if not specified."
    },
    
    "FeeAmount": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the total invoice amount as a numeric value only, WITHOUT currency symbols or commas. Return 45335.98 not $45,335.98 or 45,335.98"
    },
    
    "PartyName": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the billing party name - the company being billed (the customer receiving this invoice)"
    },
    
    "FleetID": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the fleet identifier or fleet number associated with this invoice"
    },
    
    "GLAccount": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the General Ledger account number for accounting purposes"
    },
    
    "CostCenter": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the cost center code for internal accounting allocation"
    },
    
    "BOLNumber": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the Bill of Lading (BOL) number. This is a shipping document reference number. Keep it under 20 characters if possible."
    },
    
    "OriginCity": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the origin city where the freight shipment started"
    },
    
    "OriginState": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the origin state abbreviation (2 letters, e.g., IL, TX, CA)"
    },
    
    "DestinationCity": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the destination city where the freight was delivered"
    },
    
    "DestinationState": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the destination state abbreviation (2 letters, e.g., CO, NY, FL)"
    },
    
    "Comments": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract any additional notes, remarks, or comments from the invoice. If none, leave empty."
    },
    
    "STCC": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the Standard Transportation Commodity Code (STCC). This is a 7-digit numeric code that classifies the type of commodity being shipped."
    },
    
    "LeadEquipmentID": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the lead equipment identifier (car number, trailer number, or equipment ID)"
    },
    
    "ServiceDate": {
      "type": "string",
      "inferenceType": "explicit",
      "instruction": "Extract the service date (when freight service was provided) in mm/dd/yyyy format. If multiple dates, use the first/earliest date."
    }
  }
}
```

### How to Read This Schema

```
Each field has three things:

1. "type": "string"
   → The field value should be text (all our invoice fields are text)

2. "inferenceType": "explicit"
   → The AI looks for TEXT THAT IS LITERALLY ON THE PAGE
   → "explicit" means: find the exact label and read its value
   → vs "implicit" which would mean: infer something not directly stated

3. "instruction": "Extract the invoice date..."
   → Natural language instructions FOR THE AI MODEL
   → The more specific you are, the better the extraction
   → Bad: "Get the amount"
   → Good: "Extract only the numeric total fee amount WITHOUT currency symbols. Return 45335.98 not $45,335.98"

WHY DOES INSTRUCTION QUALITY MATTER?
  With vague instruction: AI might return "$45,335.98"
  When GVP tries to parse this as a number → FAILS ($ and , are not valid)
  
  With precise instruction: AI returns "45335.98"
  GVP parses this correctly → SUCCESS
```

---

## Step 10 — Write the Blueprint Manager Lambda — Every Line Explained

Create: `lambda_functions/bedrock_blueprint_manager/handler.py`

```python
"""
One-time setup Lambda — creates the Bedrock Data Automation project and blueprint.
Run this ONCE before the system can process any invoices.
"""

import os
import json
import boto3
from aws_lambda_powertools import Logger

logger = Logger(service="bedrock_blueprint_manager")

def lambda_handler(event, context):
    """
    Creates (or updates) the Bedrock blueprint and project.
    
    Can be run multiple times safely — it checks if blueprint already exists
    before creating a new one.
    """
    
    bda_client = boto3.client('bedrock-data-automation')
    
    blueprint_name  = os.getenv("BLUEPRINT_NAME", "freight-invoice-blueprint")
    blueprint_file  = os.getenv("BLUEPRINT_FILE", "bedrock_invoice_blueprint.json")
    project_name    = os.getenv("PROJECT_NAME", "Freight_Audit_Agent")
    
    # ── STEP 1: Load the blueprint schema from the JSON file ──
    # The JSON file is bundled with the Lambda function code
    # (Terraform packages all files in the lambda_functions/bedrock_blueprint_manager/ folder)
    with open(blueprint_file, 'r') as f:
        blueprint_schema = json.load(f)
    
    logger.info(f"Loaded blueprint schema with {len(blueprint_schema.get('properties', {}))} fields")
    
    # ── STEP 2: Check if blueprint already exists ──
    # Idempotency: don't create duplicates if this Lambda is run twice
    existing_blueprint_arn = None
    
    try:
        response = bda_client.list_blueprints(blueprintStageFilter='LIVE')
        for blueprint in response.get('blueprints', []):
            if blueprint['blueprintName'] == blueprint_name:
                existing_blueprint_arn = blueprint['blueprintArn']
                logger.info(f"Found existing blueprint: {existing_blueprint_arn}")
                break
    except Exception as e:
        logger.warning(f"Could not list blueprints: {e}")
    
    # ── STEP 3: Create or update the blueprint ──
    if existing_blueprint_arn:
        # Update existing blueprint with latest schema
        bda_client.update_blueprint(
            blueprintArn=existing_blueprint_arn,
            schema=json.dumps(blueprint_schema),  # schema must be a JSON string, not a dict
        )
        blueprint_arn = existing_blueprint_arn
        logger.info("Updated existing blueprint")
    else:
        # Create new blueprint
        response = bda_client.create_blueprint(
            blueprintName=blueprint_name,
            type='DOCUMENT',           # We're processing PDF documents
            blueprintStage='LIVE',     # DRAFT=testing, LIVE=production-ready
            schema=json.dumps(blueprint_schema),
        )
        blueprint_arn = response['blueprint']['blueprintArn']
        logger.info(f"Created new blueprint: {blueprint_arn}")
    
    # ── STEP 4: Check if project already exists ──
    existing_project_arn = None
    
    try:
        response = bda_client.list_data_automation_projects(projectStageFilter='LIVE')
        for project in response.get('projects', []):
            if project['projectName'] == project_name:
                existing_project_arn = project['projectArn']
                logger.info(f"Found existing project: {existing_project_arn}")
                break
    except Exception as e:
        logger.warning(f"Could not list projects: {e}")
    
    # ── STEP 5: Create the Data Automation project ──
    # A project is a container that links a blueprint to a deployable unit
    # The invoice_processor Lambda will look up this project by name
    if not existing_project_arn:
        response = bda_client.create_data_automation_project(
            projectName=project_name,
            projectDescription='Automated freight invoice data extraction using AI',
            projectStage='LIVE',
            customOutputConfiguration={
                'blueprints': [{
                    'blueprintArn': blueprint_arn,
                    'blueprintStage': 'LIVE',
                }]
            },
        )
        project_arn = response['project']['projectArn']
        logger.info(f"Created new project: {project_arn}")
    else:
        project_arn = existing_project_arn
    
    logger.info("Blueprint manager completed successfully", extra={
        "blueprint_arn": blueprint_arn,
        "project_arn": project_arn,
    })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'blueprint_arn': blueprint_arn,
            'project_arn': project_arn,
            'blueprint_name': blueprint_name,
            'project_name': project_name,
        })
    }
```

---

## Step 11 — Write the GVP Publisher Lambda — Every Line Explained

Create: `lambda_functions/gvp_invoice_publisher/handler.py`

```python
"""
Triggered by Bedrock completion event.
Reads extracted invoice data from S3 and posts it to GVP ERP system.
"""

import os
import json
import boto3
from datetime import datetime, timezone
from urllib.parse import unquote_plus
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

from gvp_client import get_gvp_auth_token, post_invoice_to_gvp

logger  = Logger(service="gvp_invoice_publisher")
metrics = Metrics(namespace="FreightAuditAgent")

s3_client = boto3.client('s3')


def get_s3_object_metadata(bucket, key):
    """Helper: read S3 metadata without downloading the file."""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        return response.get('Metadata', {})
    except Exception as e:
        logger.warning(f"Could not read S3 metadata: {e}")
        return {}


def read_json_from_s3(s3_uri):
    """
    Read and parse a JSON file from S3.
    s3_uri format: s3://bucket-name/path/to/file.json
    """
    # Parse the URI to get bucket and key
    # s3://devgvpbucket1/lambda-output/JOB/job_metadata.json
    # → bucket: devgvpbucket1
    # → key: lambda-output/JOB/job_metadata.json
    parts  = s3_uri.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    key    = parts[1]
    
    response = s3_client.get_object(Bucket=bucket, Key=key)
    # response['Body'] is a streaming object — read() gets all bytes
    content  = response['Body'].read().decode('utf-8')
    return json.loads(content)


def get_custom_output_path(job_metadata_uri):
    """
    Parse Bedrock's job_metadata.json to find where the custom output is.
    
    Bedrock organizes output like this:
      job_metadata.json → tells you where to find custom_output.json
      custom_output.json → has the actual extracted invoice fields
    
    job_metadata.json structure:
    {
      "output_metadata": [{
        "segment_metadata": [{
          "custom_output_path": "s3://bucket/path/custom_output/0/custom_output.json"
        }]
      }]
    }
    """
    metadata = read_json_from_s3(job_metadata_uri)
    
    # Navigate the nested JSON to find custom_output_path
    output_metadata  = metadata.get("output_metadata", [])
    if not output_metadata:
        raise ValueError("No output_metadata found in job_metadata.json")
    
    segment_metadata = output_metadata[0].get("segment_metadata", [])
    if not segment_metadata:
        raise ValueError("No segment_metadata found")
    
    custom_output_path = segment_metadata[0].get("custom_output_path")
    if not custom_output_path:
        raise ValueError("No custom_output_path found")
    
    return custom_output_path


@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    """
    Called when Bedrock finishes processing a PDF.
    
    The event from Bedrock looks like:
    {
        "source": "aws.bedrock-data-automation-runtime",
        "detail-type": "Data Automation Async Invocation Status Change",
        "detail": {
            "status": "SUCCEEDED",
            "input_s3_object": {
                "s3_bucket": "devgvpbucket1",
                "name": "Invoices/20251217_143022_invoice.pdf"
            },
            "output_s3_location": {
                "s3_bucket": "devgvpbucket1",
                "name": "freight-audit-agent-output/JOB-12345/"
            }
        }
    }
    """
    
    # ── STEP 1: Parse the Bedrock completion event ──
    detail = event.get("detail", {})
    status = detail.get("status", "UNKNOWN")
    
    # Only process SUCCEEDED jobs — FAILED jobs go to DLQ automatically
    if status != "SUCCEEDED":
        logger.warning(f"Bedrock job status is {status} — skipping")
        return {'statusCode': 200, 'body': json.dumps({'skipped': True, 'status': status})}
    
    input_obj    = detail.get("input_s3_object", {})
    output_loc   = detail.get("output_s3_location", {})
    
    input_bucket = input_obj.get("s3_bucket")
    input_key    = unquote_plus(input_obj.get("name", ""))
    
    output_bucket = output_loc.get("s3_bucket")
    output_key    = unquote_plus(output_loc.get("name", ""))
    
    logger.info("Processing Bedrock completion event", extra={
        "input": f"s3://{input_bucket}/{input_key}",
        "output": f"s3://{output_bucket}/{output_key}",
    })
    
    # ── STEP 2: Get correlation_id and email context from original PDF metadata ──
    s3_metadata      = get_s3_object_metadata(input_bucket, input_key)
    correlation_id   = s3_metadata.get('correlation-id', 'unknown')
    mailbox_id       = s3_metadata.get('mailbox-id', 'unknown')
    recipient_address = s3_metadata.get('email-recipient-address', '')
    email_received   = s3_metadata.get('email-received-time', '')
    
    # Tag all future log messages with this invoice's correlation_id
    logger.append_keys(correlation_id=correlation_id)
    
    # ── STEP 3: Find and read Bedrock's extracted data ──
    # First, find the job_metadata.json file
    # The output_key ends with "/" — job_metadata.json is right inside
    job_metadata_uri = f"s3://{output_bucket}/{output_key}job_metadata.json"
    
    # Read job_metadata.json → find path to custom_output.json
    custom_output_uri = get_custom_output_path(job_metadata_uri)
    
    # Read custom_output.json → get the extracted invoice fields
    result_json      = read_json_from_s3(custom_output_uri)
    
    # "inference_result" contains all 18 extracted fields
    inference_results = result_json.get("inference_result", {})
    
    logger.info("Read Bedrock inference results", extra={
        "fields_extracted": list(inference_results.keys()),
        "invoice_number": inference_results.get("InvoiceNumber", "unknown"),
    })
    
    # ── STEP 4: Get GVP credentials and authenticate ──
    gvp_login_id = os.getenv("GVP_LOGIN_ID", "novaadmin")
    gvp_password = os.getenv("GVP_PASSWORD")
    gvp_auth_url = os.getenv("GVP_AUTH_URL")
    gvp_api_url  = os.getenv("GVP_API_URL")
    
    if not gvp_password:
        raise ValueError("GVP_PASSWORD environment variable is not set")
    
    gvp_token = get_gvp_auth_token(gvp_login_id, gvp_password, gvp_auth_url)
    logger.info("GVP authentication successful")
    
    # ── STEP 5: Post invoice to GVP ──
    gvp_response = post_invoice_to_gvp(
        inference_results=inference_results,
        token=gvp_token,
        mailbox_name=recipient_address,    # for client routing (plus addressing)
        pdf_file_path=f"s3://{input_bucket}/{input_key}",  # S3 URI for GVP audit trail
        api_url=gvp_api_url,
    )
    
    invoice_number = inference_results.get("InvoiceNumber", "unknown")
    logger.info("Invoice posted to GVP", extra={
        "invoice_number": invoice_number,
        "gvp_response": gvp_response,
    })
    
    # ── STEP 6: Calculate and log end-to-end latency ──
    if email_received:
        try:
            # email_received is an ISO 8601 string like "2025-12-17T14:30:22Z"
            received_dt = datetime.fromisoformat(email_received.replace('Z', '+00:00'))
            now_dt      = datetime.now(timezone.utc)
            
            # Total time from email receipt to GVP posting
            end_to_end_seconds = (now_dt - received_dt).total_seconds()
            end_to_end_ms      = int(end_to_end_seconds * 1000)
            
            logger.info("Pipeline completed", extra={
                "end_to_end_duration_ms":      end_to_end_ms,
                "end_to_end_duration_minutes": round(end_to_end_seconds / 60, 1),
                "invoice_number":              invoice_number,
            })
            
            metrics.add_metric(name="EndToEndLatency", unit=MetricUnit.Milliseconds, value=end_to_end_ms)
        except Exception as e:
            logger.warning(f"Could not calculate latency: {e}")
    
    metrics.add_metric(name="GVPPostsSuccessful", unit=MetricUnit.Count, value=1)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'invoice_number':  invoice_number,
            'correlation_id':  correlation_id,
            'gvp_response':    str(gvp_response),
        })
    }
```

---

## Step 12 — Write the GVP Client — Every Line Explained

Create: `lambda_functions/gvp_invoice_publisher/gvp_client.py`

```python
"""
GVP (IntelliTrans) API client.
Handles authentication and invoice posting.
"""

import requests
import logging

logger = logging.getLogger(__name__)


def get_gvp_auth_token(login_id, password, auth_url=None):
    """
    Get a Bearer authentication token from GVP API.
    
    GVP uses a non-standard auth pattern:
    - Standard: send credentials in request BODY
    - GVP: send credentials in request HEADERS
    """
    
    if auth_url is None:
        auth_url = "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
    
    # GVP expects credentials in HTTP headers (unusual but valid)
    headers = {
        "LoginID": login_id,
        "Pwd": password,
    }
    
    response = requests.get(auth_url, headers=headers, timeout=30)
    
    # raise_for_status() = automatically raise an exception if status code is 4xx or 5xx
    # Much cleaner than if response.status_code != 200: raise Exception(...)
    response.raise_for_status()
    
    # GVP returns the token as a plain text string, possibly with surrounding quotes
    # .strip() removes whitespace, .strip('"').strip("'") removes quote characters
    token = response.text.strip().strip('"').strip("'")
    
    return token


def post_invoice_to_gvp(inference_results, token, mailbox_name, pdf_file_path, api_url=None):
    """
    Post extracted invoice data to GVP REST API.
    
    Returns the API response dict, or a dict with idempotent=True if duplicate.
    """
    
    if api_url is None:
        api_url = "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"
    
    # ── Business Rule 1: BOLNumber max 20 characters ──
    # GVP's database column for BOLNumber has a 20-char limit
    # Some carriers put long strings in the BOL field → truncate silently
    bol_number = inference_results.get("BOLNumber", "")
    if bol_number and len(bol_number) > 20:
        logger.warning(f"BOLNumber '{bol_number}' exceeds 20 chars, truncating")
        bol_number = bol_number[:20]
    
    # ── Business Rule 2: ServiceDate — take only the first date ──
    # Some invoice formats show: "11/01/2025, 11/15/2025" (multiple service dates)
    # GVP only accepts ONE date → use the first one
    service_date = inference_results.get("ServiceDate", "")
    if service_date and "," in service_date:
        service_date = service_date.split(",")[0].strip()
        logger.warning(f"Multiple service dates found, using first: {service_date}")
    
    # ── Build the GVP API payload ──
    # Map Bedrock field names → GVP API field names
    # Some names differ (e.g., Bedrock calls it "PartyName", GVP calls it "PartyName" — same here)
    payload = {
        "InvoiceDate":      inference_results.get("InvoiceDate", ""),
        "InvoiceNumber":    inference_results.get("InvoiceNumber", ""),
        "Carrier":          inference_results.get("Carrier", ""),
        "Currency":         inference_results.get("Currency", "USD"),
        "FeeAmount":        inference_results.get("FeeAmount", ""),
        "PartyName":        inference_results.get("PartyName", "Novaadmin"),
        "MailboxName":      mailbox_name,     # from S3 metadata (plus addressing)
        "FleetID":          inference_results.get("FleetID", ""),
        "GLAccount":        inference_results.get("GLAccount", ""),
        "CostCenter":       inference_results.get("CostCenter", ""),
        "BOLNumber":        bol_number,
        "OriginCity":       inference_results.get("OriginCity", ""),
        "OriginState":      inference_results.get("OriginState", ""),
        "DestinationCity":  inference_results.get("DestinationCity", ""),
        "DestinationState": inference_results.get("DestinationState", ""),
        "Comments":         inference_results.get("Comments", "Invoice auto-created from AI extraction."),
        "STCC":             inference_results.get("STCC", ""),
        "LeadEquipmentID":  inference_results.get("LeadEquipmentID", ""),
        "ServiceDate":      service_date,
        "PDFFilePath":      pdf_file_path,   # S3 URI of original PDF
    }
    
    # GVP uses tokenID header (not standard "Authorization: Bearer" header)
    headers = {
        "tokenID": token,
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        # Get the response body (what GVP said about the error)
        response_body = e.response.text.lower() if e.response else ""
        
        # ── Idempotency: Handle duplicate invoices ──
        # SCENARIO: Lambda succeeds in posting to GVP, but crashes before returning.
        # EventBridge sees Lambda failure → retries → Lambda tries to post again.
        # GVP already has the invoice → returns 500 with "Invoice Number already Exists"
        #
        # WITHOUT this check: raises exception → DLQ alarm fires → false alert
        # WITH this check: detected as duplicate → treat as success → no alarm
        if "invoice number already exists" in response_body:
            logger.warning(
                "Duplicate invoice detected — GVP already has this invoice. Treating as success.",
                extra={"invoice_number": payload.get("InvoiceNumber")}
            )
            return {
                "status": "duplicate",
                "idempotent": True,
                "invoice_number": payload.get("InvoiceNumber"),
            }
        
        # Any other HTTP error = real failure
        # Re-raise so it propagates up → Lambda fails → EventBridge retry → DLQ
        logger.error(f"GVP API error: {e.response.status_code if e.response else 'unknown'} — {response_body}")
        raise
    
    except requests.exceptions.Timeout:
        logger.error("GVP API request timed out after 30 seconds")
        raise
```

---

## Step 13 — Write the DLQ Processor Lambda — Every Line Explained

Create: `lambda_functions/dlq_processor/handler.py`

```python
"""
Processes Dead Letter Queue messages — sends alert emails when invoice processing fails.

DLQ = Dead Letter Queue. When Lambda fails after all retries, 
the failed event is put in an SQS queue (the DLQ).
This Lambda reads those failed events and sends email alerts via SNS.
"""

import os
import json
import boto3
from aws_lambda_powertools import Logger
from urllib.parse import unquote_plus

logger = Logger(service="dlq_processor")

s3_client  = boto3.client('s3')
sns_client = boto3.client('sns')


def extract_invoice_details_from_dlq_message(message_body_str):
    """
    Extract invoice details from a DLQ message.
    
    DLQ messages come in TWO different formats, and we need to handle both:
    
    FORMAT 1: Lambda async invoke failure
    When Lambda code throws an exception during async invocation:
    {
        "requestPayload": { ...original EventBridge event... },
        "requestContext": {
            "approximateInvokeCount": 3,
            "condition": "RetriesExhausted"
        },
        "responsePayload": {
            "errorType": "HTTPError",
            "errorMessage": "GVP API returned 503"
        }
    }
    → We need to unwrap requestPayload to get the original event
    
    FORMAT 2: EventBridge delivery failure
    When EventBridge itself couldn't deliver the event to Lambda
    (e.g., Lambda concurrency limit was hit):
    { ...original EventBridge event directly... }
    → The original event is the message itself (no wrapping)
    """
    
    message = json.loads(message_body_str)
    details = {}
    
    # Detect which format we have
    if 'requestPayload' in message:
        # FORMAT 1: Lambda invocation failure — unwrap the payload
        original_event = message['requestPayload']
        
        # Read failure context
        request_ctx   = message.get('requestContext', {})
        invoke_count  = request_ctx.get('approximateInvokeCount', 1)
        condition     = request_ctx.get('condition', 'unknown')
        
        response_payload = message.get('responsePayload', {})
        error_type       = response_payload.get('errorType', 'unknown')
        error_message    = response_payload.get('errorMessage', 'unknown')
        
        details['invoke_count'] = invoke_count
        details['condition']    = condition
        details['error_type']   = error_type
        details['error_message'] = error_message
    else:
        # FORMAT 2: EventBridge delivery failure — event is the message
        original_event = message
    
    # Now parse the original event to find which stage failed
    event_source = original_event.get('source', '')
    
    if 'bedrock' in event_source:
        # GVP Publisher DLQ — Bedrock completed but GVP post failed
        details['dlq_type'] = 'gvp_publisher'
        input_obj    = original_event.get('detail', {}).get('input_s3_object', {})
        details['input_bucket'] = input_obj.get('s3_bucket', '')
        details['input_key']    = unquote_plus(input_obj.get('name', ''))
        
        # Retrieve full context from S3 metadata
        if details['input_bucket'] and details['input_key']:
            try:
                s3_meta = s3_client.head_object(
                    Bucket=details['input_bucket'],
                    Key=details['input_key']
                ).get('Metadata', {})
                
                details['correlation_id']    = s3_meta.get('correlation-id', 'unknown')
                details['mailbox']           = s3_meta.get('mailbox-id', 'unknown')
                details['recipient_address'] = s3_meta.get('email-recipient-address', 'unknown')
                details['original_filename'] = s3_meta.get('original-filename', 'unknown')
                details['email_subject']     = s3_meta.get('email-subject', 'unknown')
            except Exception as e:
                logger.warning(f"Could not read S3 metadata: {e}")
    
    elif 's3' in event_source:
        # Invoice Processor DLQ — S3 upload occurred but Bedrock job failed
        details['dlq_type']   = 'invoice_processor'
        s3_detail = original_event.get('detail', {})
        details['input_bucket'] = s3_detail.get('bucket', {}).get('name', '')
        details['input_key']    = unquote_plus(s3_detail.get('object', {}).get('key', ''))
        
        if details['input_bucket'] and details['input_key']:
            try:
                s3_meta = s3_client.head_object(
                    Bucket=details['input_bucket'],
                    Key=details['input_key']
                ).get('Metadata', {})
                details['correlation_id'] = s3_meta.get('correlation-id', 'unknown')
                details['mailbox']        = s3_meta.get('mailbox-id', 'unknown')
            except Exception as e:
                logger.warning(f"Could not read S3 metadata: {e}")
    
    else:
        # Email Poller DLQ — email polling itself failed
        details['dlq_type'] = 'email_poller'
        details['correlation_id'] = 'N/A (failure before PDF upload)'
    
    return details


def send_dlq_alert(details, dlq_name, receive_count):
    """Build and send an SNS email alert with all available context."""
    
    sns_topic_arn = os.getenv("SNS_INVOICE_ERROR_TOPIC_ARN")
    
    # Determine which stage failed and what to check
    dlq_type = details.get('dlq_type', 'unknown')
    
    if dlq_type == 'gvp_publisher':
        stage   = "GVP API Publishing"
        issue   = "Invoice was extracted by Bedrock AI but FAILED to post to GVP Oracle database"
        action  = "Check GVP API status and credentials"
    elif dlq_type == 'invoice_processor':
        stage   = "Bedrock AI Extraction"
        issue   = "PDF was uploaded to S3 but FAILED to start/complete Bedrock processing"
        action  = "Check Bedrock project exists and has quota available"
    else:
        stage   = "Email Polling"
        issue   = "Failed to poll Microsoft 365 mailbox for invoice emails"
        action  = "Check Azure AD credentials and M365 mailbox access"
    
    correlation_id   = details.get('correlation_id', 'unknown')
    input_bucket     = details.get('input_bucket', '')
    input_key        = details.get('input_key', '')
    invoice_filename = details.get('original_filename', input_key.split('/')[-1] if input_key else 'unknown')
    
    # Build alert message — detailed enough that ops can act without digging through logs
    subject = f"CRITICAL: Invoice Processing Failed - {dlq_name}"
    
    message_lines = [
        f"INVOICE PROCESSING FAILURE ALERT",
        f"=" * 60,
        f"",
        f"Failed Stage:     {stage}",
        f"Problem:          {issue}",
        f"DLQ Name:         {dlq_name}",
        f"Receive Count:    {receive_count} (retried {receive_count - 1} times)",
        f"",
        f"INVOICE DETAILS",
        f"-" * 40,
        f"Invoice File:     {invoice_filename}",
        f"Correlation ID:   {correlation_id}",
        f"Mailbox:          {details.get('mailbox', 'unknown')}",
        f"Recipient:        {details.get('recipient_address', 'unknown')}",
        f"Email Subject:    {details.get('email_subject', 'unknown')}",
        f"",
    ]
    
    if input_bucket and input_key:
        message_lines.extend([
            f"PDF LOCATION",
            f"-" * 40,
            f"S3 URI:  s3://{input_bucket}/{input_key}",
            f"",
            f"# Download PDF for inspection:",
            f"aws s3 cp s3://{input_bucket}/{input_key} ./{invoice_filename}",
            f"",
        ])
    
    if correlation_id != 'unknown' and correlation_id != 'N/A (failure before PDF upload)':
        message_lines.extend([
            f"CLOUDWATCH LOGS SEARCH",
            f"-" * 40,
            f"# Find all logs for this invoice:",
            f'fields @timestamp, @log, @message',
            f'| filter correlation_id = "{correlation_id}"',
            f'| sort @timestamp asc',
            f"",
        ])
    
    message_lines.extend([
        f"NEXT STEPS",
        f"-" * 40,
        f"1. {action}",
        f"2. Review CloudWatch logs using the query above",
        f"3. Fix the root cause",
        f"4. Manually reprocess: upload the PDF to S3 to restart pipeline",
        f"",
        f"REPROCESS COMMAND (after fixing root cause):",
        f"aws s3 cp s3://{input_bucket}/{input_key} s3://{input_bucket}/{input_key}",
        f"(copying to same location triggers S3 event → restarts pipeline)",
    ])
    
    message = "\n".join(message_lines)
    
    sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject=subject[:100],    # SNS subject max 100 chars
        Message=message,
    )
    
    logger.info(f"DLQ alert sent for {dlq_type} failure", extra={
        "correlation_id": correlation_id,
        "dlq_name": dlq_name,
    })


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    """
    Triggered by SQS event source mapping — one call per batch of DLQ messages.
    event["Records"] contains a list of SQS messages.
    """
    
    # SQS delivers messages in batches (we configure batch size = 1 for DLQ)
    for record in event.get('Records', []):
        
        # Which DLQ sent this message?
        # The ARN is like: arn:aws:sqs:us-east-1:123:prod-freight-audit-gvp-publisher-dlq
        dlq_arn   = record.get('eventSourceARN', '')
        dlq_name  = dlq_arn.split(':')[-1]   # last part after colon = queue name
        
        # How many times has this message been received?
        # (counts how many times DLQ Processor tried and re-queued)
        receive_count = int(record['attributes'].get('ApproximateReceiveCount', 1))
        
        # The actual message content
        message_body = record['body']
        
        logger.info(f"Processing DLQ message from {dlq_name}", extra={
            "receive_count": receive_count,
        })
        
        try:
            details = extract_invoice_details_from_dlq_message(message_body)
            send_dlq_alert(details, dlq_name, receive_count)
        except Exception as e:
            logger.error(f"Failed to process DLQ message: {e}")
            # Don't re-raise — we want to acknowledge the SQS message
            # so it doesn't bounce back into the DLQ of the DLQ processor
```

---

## Step 14 — Write Terraform Infrastructure — Every File Explained

Now we write all the Terraform files that create AWS resources. Create a `terraform/` folder.

### 14a. versions.tf — Required Tool Versions

```hcl
# terraform/versions.tf

# This file declares what versions of tools are required.
# Terraform reads this first before doing anything else.

terraform {
  # minimum Terraform CLI version
  required_version = ">= 1.6"
  
  # Where to store Terraform "state" (its memory of what it created)
  # Without this, state is only local — dangerous for teams
  # With this, state is in S3 (shared, encrypted, versioned)
  backend "s3" {
    bucket         = "freight-audit-terraform-state"   # created in Step 2d
    key            = "infrastructure/terraform.tfstate" # path within bucket
    region         = "us-east-1"
    encrypt        = true                              # encrypt state file
    dynamodb_table = "terraform-state-lock"           # prevent concurrent runs
  }
  
  required_providers {
    # aws = the official AWS provider (what creates Lambda, S3, etc.)
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"   # use any 5.x version
    }
    
    # archive = used to zip up Lambda code for deployment
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

# Configure the AWS provider with the region from our variables
provider "aws" {
  region = var.aws_region
  
  # Apply these tags to ALL resources automatically
  # So every AWS resource shows: Project=freight-audit-agent, Environment=dev
  default_tags {
    tags = local.common_tags
  }
}
```

### 14b. variables.tf — All Configuration Inputs

```hcl
# terraform/variables.tf
# Variables are the "inputs" to Terraform — you provide values in .tfvars files

variable "environment" {
  description = "Environment name: dev, staging, or prod"
  type        = string
  # No default — you MUST specify this (prevents accidents in prod)
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# SENSITIVE = true means Terraform won't print this in logs
# Important for secrets like passwords!
variable "azure_client_id" {
  description = "Azure AD application client ID (from Step 3a)"
  type        = string
  sensitive   = true
}

variable "azure_client_secret" {
  description = "Azure AD application client secret (from Step 3b)"
  type        = string
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure AD tenant ID (from Step 3a)"
  type        = string
  sensitive   = true
}

variable "mailbox_email" {
  description = "Email address to monitor for invoices"
  type        = string
  # Example: "invoices@yourcompany.com"
}

variable "gvp_login_id" {
  description = "GVP API username"
  type        = string
  default     = "novaadmin"
}

variable "gvp_password" {
  description = "GVP API password"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email for failure alerts (your email address)"
  type        = string
  default     = ""
}

variable "bedrock_project_name" {
  description = "Name for the Bedrock Data Automation project"
  type        = string
  default     = "Freight_Audit_Agent"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds (max 900)"
  type        = number
  default     = 300  # 5 minutes
}

variable "lambda_memory_size" {
  description = "Lambda memory in MB (affects CPU speed too)"
  type        = number
  default     = 512
}

variable "email_poll_schedule" {
  description = "Cron expression for email polling"
  type        = string
  # Every 5 min, Mon-Fri, 8AM-6PM Eastern Time
  default     = "cron(*/5 8-18 ? * MON-FRI *)"
}

variable "invoice_s3_prefix" {
  type    = string
  default = "freight-audit-agent-invoices/"
}

variable "output_s3_prefix" {
  type    = string
  default = "freight-audit-agent-output/"
}

variable "log_retention_days" {
  description = "Days to keep CloudWatch logs"
  type        = number
  default     = 30
}
```

### 14c. environments/dev.tfvars — Development Values

```hcl
# terraform/environments/dev.tfvars
# This file provides VALUES for all the variables above.
# Keep this in version control — it has no secrets.

environment = "dev"
aws_region  = "us-east-1"

# Lambda config (smaller for dev = cheaper)
lambda_timeout     = 300
lambda_memory_size = 512

# Bedrock config
bedrock_project_name = "Freight_Audit_Agent"

# Schedule: every 5 minutes during business hours
email_poll_schedule = "cron(*/5 8-18 ? * MON-FRI *)"

# S3 config
invoice_s3_prefix = "freight-audit-agent-invoices/"
output_s3_prefix  = "freight-audit-agent-output/"

# GVP API — use QA environment for dev
gvp_login_id = "novaadmin"
gvp_auth_url = "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
gvp_api_url  = "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"

# Monitoring
log_retention_days = 30

# SECRETS — DO NOT put these values here!
# Set them as shell environment variables before running terraform:
# export TF_VAR_azure_client_id="your-client-id-here"
# export TF_VAR_azure_client_secret="your-secret-here"
# export TF_VAR_azure_tenant_id="your-tenant-id-here"
# export TF_VAR_mailbox_email="invoices@yourcompany.com"
# export TF_VAR_gvp_password="your-gvp-password"
# export TF_VAR_alert_email="your@email.com"
```

---

## Step 15 — Deploy Everything Step by Step

### 15a. Set Your Secrets as Environment Variables

```bash
# NEVER put secrets in .tfvars files (they go in git)
# Instead, set them as shell environment variables
# Terraform automatically reads TF_VAR_* variables

export TF_VAR_azure_client_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export TF_VAR_azure_client_secret="AbCdEfGh~IJkLmNoPqRs.1234567890"
export TF_VAR_azure_tenant_id="yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
export TF_VAR_mailbox_email="invoices@yourcompany.com"
export TF_VAR_gvp_password="your-gvp-password-here"
export TF_VAR_alert_email="your-personal-email@gmail.com"

# Verify they're set:
echo $TF_VAR_azure_client_id   # should show your client ID
```

### 15b. Initialize Terraform

```bash
cd terraform

# Download the AWS provider and configure the S3 backend
terraform init

# Expected output:
# Initializing the backend...
# Initializing provider plugins...
# - Finding hashicorp/aws versions matching "~> 5.0"...
# - Installing hashicorp/aws v5.x.x...
# Terraform has been successfully initialized!
```

### 15c. Preview What Terraform Will Create

```bash
# "plan" = show what would be created/changed WITHOUT creating anything
terraform plan -var-file="environments/dev.tfvars"

# Read the output carefully!
# Lines starting with + = will be CREATED
# Lines starting with - = will be DESTROYED (dangerous!)
# Lines starting with ~ = will be MODIFIED
# 
# For a fresh deploy, everything should be + (creates)
# Count: "Plan: 47 to add, 0 to change, 0 to destroy." → looks good!
```

### 15d. Apply — Actually Create Everything

```bash
# "apply" = actually create all resources in AWS
terraform apply -var-file="environments/dev.tfvars"

# Terraform shows the plan again and asks: "Do you want to perform these actions?"
# Type: yes

# Expected output (takes 2-5 minutes):
# aws_sqs_queue.email_poller_dlq: Creating...
# aws_s3_bucket.storage[0]: Creating...
# aws_ssm_parameter.azure_client_id: Creating...
# ...
# Apply complete! Resources: 47 added, 0 changed, 0 destroyed.
#
# Outputs:
# email_poller_function_name = "dev-freight-audit-agent-email-poller"
# s3_bucket_name = "dev-freight-audit-agent-123456789012"
```

### 15e. Run the Blueprint Manager (One-Time Setup)

```bash
# After Terraform creates everything, run the blueprint manager ONCE
# This creates the Bedrock project and blueprint

aws lambda invoke \
    --function-name dev-freight-audit-agent-blueprint-manager \
    --payload '{}' \
    /tmp/blueprint_response.json

cat /tmp/blueprint_response.json
# Expected:
# {"statusCode": 200, "body": "{\"blueprint_arn\": \"arn:aws:bedrock:...\", \"project_arn\": \"arn:aws:bedrock:...\"}"}
```

### 15f. Subscribe Your Email to Alerts

```bash
# Your email needs to confirm the SNS subscription to receive alerts
# Check your email inbox for a message from AWS
# Subject: "AWS Notification - Subscription Confirmation"
# Click the "Confirm subscription" link

# Or do it via CLI (replace with your SNS topic ARN from Terraform outputs):
aws sns list-topics --query 'Topics[].TopicArn' --output table
# Find the freight-audit-agent topic ARN, then:
aws sns subscribe \
    --topic-arn "arn:aws:sns:us-east-1:123456789012:dev-freight-audit-agent-invoice-errors" \
    --protocol email \
    --notification-endpoint "your@email.com"
```

---

## Step 16 — Test the System End to End

### 16a. Send a Test Email

```
1. Find one of the test PDFs in test_data/ folder:
   test_data/invoice.pdf
   
2. Open your email client
3. Send an email to: invoices@yourcompany.com  ← your monitored mailbox
   Subject: Test Invoice from BNSF
   Attach: invoice.pdf
   
4. Wait up to 5 minutes for the email poller to run
```

### 16b. Monitor in Real Time

Open three terminal windows:

```bash
# Terminal 1: Watch Email Poller logs
aws logs tail /aws/lambda/dev-freight-audit-agent-email-poller \
    --follow --format short

# You should see within 5 minutes:
# [INFO] Starting email poll {"mailbox": "invoices@yourcompany.com"}
# [INFO] Retrieved 1 unread emails
# [INFO] PDF uploaded to S3 {"correlation_id": "a3f8c921-..."}

# Terminal 2: Watch Bedrock Processor logs
aws logs tail /aws/lambda/dev-freight-audit-agent-invoice-processor \
    --follow --format short

# You should see after the upload:
# [INFO] Processing S3 upload event {"s3_key": "freight-audit-agent-invoices/..."}
# [INFO] Bedrock job started successfully {"invocation_arn": "arn:aws:..."}

# Terminal 3: Watch GVP Publisher logs
aws logs tail /aws/lambda/dev-freight-audit-agent-gvp-publisher \
    --follow --format short

# You should see 8-13 minutes later:
# [INFO] Invoice posted to GVP {"invoice_number": "INV-001"}
# [INFO] Pipeline completed {"end_to_end_duration_minutes": 9.2}
```

### 16c. Test Each Lambda Individually

Test Lambda 1 (email poller) without waiting for the scheduler:

```bash
aws lambda invoke \
    --function-name dev-freight-audit-agent-email-poller \
    --payload '{}' \
    /tmp/poller_response.json

cat /tmp/poller_response.json
# Expected: {"statusCode": 200, "body": "{\"emails_processed\": 1, \"pdfs_uploaded\": 1}"}
```

Test Lambda 2 (Bedrock processor) with a fake S3 event:

```bash
# First find the S3 key of an uploaded PDF
aws s3 ls s3://dev-freight-audit-agent-ACCOUNT_ID/freight-audit-agent-invoices/ --recursive

# Then invoke with a test event:
aws lambda invoke \
    --function-name dev-freight-audit-agent-invoice-processor \
    --payload '{
        "source": "aws.s3",
        "detail-type": "Object Created",
        "detail": {
            "bucket": {"name": "dev-freight-audit-agent-ACCOUNT_ID"},
            "object": {"key": "freight-audit-agent-invoices/YOUR_PDF_KEY.pdf"}
        }
    }' \
    /tmp/processor_response.json

cat /tmp/processor_response.json
```

### 16d. Check the S3 Output

After Bedrock finishes (8-13 minutes), check the output:

```bash
# List Bedrock output files
aws s3 ls s3://dev-freight-audit-agent-ACCOUNT_ID/freight-audit-agent-output/ --recursive

# Download and inspect the extracted data
aws s3 cp s3://dev-freight-audit-agent-ACCOUNT_ID/freight-audit-agent-output/JOB_ID/custom_output/0/custom_output.json /tmp/

cat /tmp/custom_output.json
# Expected:
# {
#   "inference_result": {
#     "InvoiceNumber": "INV-001",
#     "Carrier": "BNSF",
#     "FeeAmount": "45335.98",
#     ...
#   }
# }
```

### 16e. Verify GVP Received the Invoice

```bash
# Use the provided Postman collection to check GVP:
# Import: gvp_api.postman_collection.json
# Set: GVP_AUTH_URL, GVP_LOGIN_ID, GVP_PASSWORD variables
# Run: "Get Auth Token" → then "Get Invoice by Number"
# Search for the invoice number extracted by Bedrock
```

---

## Step 17 — Monitor and Debug

### See All Recent Errors

```bash
# CloudWatch Logs Insights — query across all Lambdas
aws logs start-query \
    --log-group-names \
        "/aws/lambda/dev-freight-audit-agent-email-poller" \
        "/aws/lambda/dev-freight-audit-agent-invoice-processor" \
        "/aws/lambda/dev-freight-audit-agent-gvp-publisher" \
    --start-time $(date -d '1 hour ago' +%s) \
    --end-time $(date +%s) \
    --query-string 'fields @timestamp, @log, level, message, correlation_id
                    | filter level = "ERROR"
                    | sort @timestamp desc
                    | limit 20'

# Get the query ID from output, then:
aws logs get-query-results --query-id QUERY_ID_HERE
```

### Track One Invoice by Correlation ID

```bash
# From the DLQ alert email or the logs, get the correlation_id
# Then find ALL logs for that invoice across all functions:
CORR_ID="a3f8c921-4d2b-4e78-8a1c-ef90ab123456"

aws logs filter-log-events \
    --log-group-name "/aws/lambda/dev-freight-audit-agent-gvp-publisher" \
    --filter-pattern "\"$CORR_ID\""
```

### Check DLQ Depths (Are There Stuck Invoices?)

```bash
# Check all three DLQs
for queue in email-poller invoice-processor gvp-publisher; do
    QUEUE_URL=$(aws sqs get-queue-url \
        --queue-name "dev-freight-audit-agent-${queue}-dlq" \
        --query QueueUrl --output text)
    
    DEPTH=$(aws sqs get-queue-attributes \
        --queue-url "$QUEUE_URL" \
        --attribute-names ApproximateNumberOfMessages \
        --query 'Attributes.ApproximateNumberOfMessages' --output text)
    
    echo "${queue}-dlq: ${DEPTH} messages"
done

# 0 = no failures (normal)
# > 0 = there are stuck invoices in DLQ, check your email for alerts
```

---

## Common Mistakes Beginners Make

```
MISTAKE 1: "Azure AD permissions not working"
  Symptom: auth.py fails with "AADSTS700016: Application not found"
  Cause: Wrong tenant_id (copied Application ID instead of Directory ID)
  Fix: In Azure Portal → Azure AD → Overview
       "Application (client) ID" → this is your AZURE_CLIENT_ID
       "Directory (tenant) ID"  → this is your AZURE_TENANT_ID
       They look similar but are different!

MISTAKE 2: "Mail.ReadWrite permission denied"
  Symptom: Graph API returns 403 Forbidden
  Cause: Admin consent was not granted
  Fix: Azure Portal → App Registration → API Permissions
       You MUST click "Grant admin consent for [Organization]"
       A green checkmark must appear next to Mail.ReadWrite

MISTAKE 3: "S3 upload succeeds but Bedrock Lambda never triggers"
  Symptom: PDF appears in S3, but invoice_processor Lambda never runs
  Cause: EventBridge notifications not enabled on S3 bucket
  Fix: In terraform/s3.tf, verify:
       resource "aws_s3_bucket_notification" ... {
         eventbridge = true   ← this MUST be true
       }
       Then: terraform apply -var-file="environments/dev.tfvars"

MISTAKE 4: "Bedrock project not found"
  Symptom: invoice_processor logs "Project 'Freight_Audit_Agent' not found"
  Cause: Blueprint manager Lambda was never run
  Fix: aws lambda invoke --function-name ...-blueprint-manager --payload '{}' /tmp/out.json
       cat /tmp/out.json  # should show blueprint_arn and project_arn

MISTAKE 5: "Terraform state already exists"
  Symptom: terraform init fails with "Error: failed to read state"
  Cause: Someone else (or you earlier) already ran terraform with different config
  Fix: Check if state bucket already has a state file:
       aws s3 ls s3://freight-audit-terraform-state/infrastructure/
       If so: download it and compare, then decide to use --reconfigure

MISTAKE 6: "S3 metadata values cause 400 error"
  Symptom: email_poller fails on put_object with "ValueError: Invalid header"
  Cause: Email subject contains \r\n (newline) characters
  Fix: sanitize_metadata_value() should already handle this
       Check that you're calling it for EVERY metadata value you set

MISTAKE 7: "GVP posts but DLQ alarm fires too"
  Symptom: Invoice posts successfully, but DLQ alert email arrives
  Cause: Lambda succeeded in posting but failed during the return statement
         EventBridge sees Lambda failure → retries → GVP says "already exists"
         Without idempotency handling: this raises an error → DLQ
  Fix: Ensure gvp_client.py checks "invoice number already exists" in response
       and returns idempotent=True instead of raising

MISTAKE 8: "Lambda timeout — PDF too large"
  Symptom: email_poller times out (30 seconds default is not enough)
  Cause: Very large PDF (>10MB) takes long to download from Graph API and upload to S3
  Fix: In terraform/environments/dev.tfvars:
       lambda_timeout = 300   ← 5 minutes (already set this way)
       lambda_memory_size = 1024  ← more memory = faster CPU = faster network

MISTAKE 9: "Test works but production doesn't"
  Symptom: Local test passes, but deployed Lambda fails
  Cause: Dependencies not in Lambda Layer
         Lambda runtime only has boto3 by default
         msal, requests are NOT included in the default runtime
  Fix: Check terraform/layers.tf — msal_requests_layer.zip must include both packages
       To rebuild: pip install msal requests -t /tmp/layer/python && cd /tmp/layer && zip -r layer.zip python/

MISTAKE 10: "EventBridge Rule not routing correctly"
  Symptom: S3 upload event exists, but invoice_processor is never called
  Cause: S3 prefix in EventBridge Rule doesn't match where email poller uploads
  Example: Rule filters: "freight-audit-agent-invoices/"
           Email poller uploads to: "Invoices/"
           These DON'T match → event not routed
  Fix: In dev.tfvars, ensure invoice_s3_prefix matches in BOTH:
       invoice_s3_prefix = "freight-audit-agent-invoices/"
       ↑ used by Lambda to upload PDFs
       ↑ used by EventBridge Rule to filter S3 events
```

---

### Final Deployment Checklist

```
□ AWS account created and CLI configured (aws sts get-caller-identity works)
□ Bedrock Data Automation enabled in your AWS region
□ Azure AD App Registration created with Mail.ReadWrite permission
□ Admin consent granted for Mail.ReadWrite permission
□ Azure credentials tested locally (test_azure_auth.py prints SUCCESS)
□ S3 bucket for Terraform state created: freight-audit-terraform-state
□ DynamoDB table for state lock created: terraform-state-lock
□ Secrets set as TF_VAR_* environment variables (not in .tfvars files)
□ terraform init completed successfully
□ terraform plan shows ~47 resources to create, 0 to destroy
□ terraform apply completed successfully
□ Blueprint manager Lambda invoked and returned blueprint_arn + project_arn
□ SNS email subscription confirmed (clicked link in AWS email)
□ Test email sent with PDF attachment
□ Email poller logs show "PDF uploaded to S3"
□ Bedrock processor logs show "Bedrock job started successfully"
□ GVP publisher logs show "Invoice posted to GVP" (8-13 minutes later)
□ DLQ depth = 0 (no failures)
```

---

*This implementation guide completes the end-to-end walkthrough. Combined with Part 1 (architecture and design), you now have everything needed to understand, build, deploy, and operate the Invoice Automation system from scratch.*
