# Freight Audit Agent

Automated freight invoice processing system using AWS Bedrock Data Automation, Microsoft 365 email integration, and GVP API integration. Built with serverless architecture for scalable, cost-effective invoice extraction and posting.

## Overview

The Freight Audit Agent automates the end-to-end processing of freight invoices:
1. **Polls** Microsoft 365 mailbox for PDF invoice attachments
2. **Uploads** PDFs to S3 with metadata
3. **Processes** invoices with AWS Bedrock Data Automation (AI extraction)
4. **Posts** extracted data to GVP API

**Average Processing Time:** 8-13 minutes per invoice (email receipt → GVP post)

---

## Architecture

![Freight Audit Agent Architecture](architecture_diagrams/Freight%20audit%20architecture.jpg)

### Workflow Steps

1. **EventBridge Scheduler** emits events every 5 minutes during business hours
2. **EventBridge Rule** matches scheduler events and triggers email poller Lambda
3. **Email Poller Lambda** polls Microsoft 365 mailbox using Graph API with Azure credentials
4. **PDF Invoices** uploaded to S3 bucket with metadata (correlation ID, email context)
5. **S3 Event Notifications** sent to EventBridge
6. **EventBridge Rule** matches S3 ObjectCreated events and triggers invoice processor Lambda
7. **Invoice Processor Lambda** reads invoice from S3 and starts Bedrock Data Automation async job
8. **Bedrock Data Automation** performs AI extraction and stores structured output in S3
9. **Bedrock Completion Event** emitted to EventBridge when job completes
10. **EventBridge Rule** matches Bedrock completion events and triggers GVP publisher Lambda
11. **GVP Publisher Lambda** retrieves extracted data and posts to Oracle database via GVP API
12. **Oracle Database** stores processed invoice data

### Key Features

- **Event-Driven Architecture**: EventBridge orchestrates the entire workflow
- **Correlation ID Tracking**: UUID generated at step 4, tracked through all stages via S3 metadata
- **Dead Letter Queues**: Failed Lambda executions captured in DLQs with automatic alerting
- **DLQ Processor**: Automatically triggered Lambda that parses DLQ messages and sends detailed SNS alerts
- **CloudWatch Observability**: Structured logging, custom metrics, and dashboards
- **Automatic Retries**: Lambda async invoke config retries failed executions (2 attempts, 3 total attempts)
- **SNS Email Alerts**: Detailed failure notifications with invoice context, S3 paths, and reprocessing steps

---

## Features

✅ **Automated Email Processing**
- Polls Microsoft 365 mailbox via Microsoft Graph API
- Filters for PDF attachments only
- Marks emails as read after processing
- Application-level permissions (no user delegation required)

✅ **Serverless & Event-Driven**
- AWS Lambda for compute (pay per execution)
- EventBridge for orchestration
- S3 for storage
- No servers to manage

✅ **AI-Powered Extraction**
- AWS Bedrock Data Automation with custom blueprints
- Extracts 15+ invoice fields (InvoiceNumber, Carrier, Amount, etc.)
- Confidence scoring for data quality
- Handles scanned and digital invoices

✅ **Full Observability**
- Structured JSON logging with AWS Lambda Powertools
- Correlation ID tracking across pipeline
- CloudWatch metrics & dashboard
- Automated alarms for failures
- End-to-end latency tracking
- See [terraform/README.md - Monitoring](terraform/README.md#monitoring--observability)

✅ **Error Handling & Resilience**
- **Lambda Async Invoke Config**: Automatic retries (2 attempts) before DLQ
- **Dead Letter Queues (DLQs)**: Capture failed Lambda executions for all critical functions
- **DLQ Processor Lambda**: Automatically triggered when messages arrive in DLQ
  - Parses Lambda async invoke and EventBridge DLQ message formats
  - Extracts invoice details from S3 metadata (correlation ID, invoice number, mailbox)
  - Sends detailed SNS email alerts with failure stage, S3 paths, and reprocessing instructions
- **SNS Alerts**: Email notifications with full invoice context (no generic "Unknown" alerts)
- **Manual Reprocessing**: Instructions included in alert emails for failed invoice recovery
- **Quality-Based Warnings**: Low confidence scores logged for manual review
- **Comprehensive Error Logging**: Structured logs with correlation ID tracking across pipeline

---

## Project Structure

```
Freight_audit_agent/
├── lambda_functions/
│   ├── invoice_email_poller/         # Polls M365 mailbox
│   │   ├── handler.py                # Main Lambda handler
│   │   ├── auth.py                   # Microsoft Graph authentication
│   │   ├── mail_client.py            # Mail operations (GraphMailClient)
│   │   └── README.md                 # M365 setup documentation
│   ├── bedrock_invoice_processor/    # Triggers Bedrock jobs
│   │   ├── handler.py                # Main Lambda handler
│   │   └── test_event.json           # Sample S3 event for testing
│   ├── gvp_invoice_publisher/        # Posts to GVP API
│   │   ├── handler.py                # Main Lambda handler
│   │   └── gvp_client.py             # GVP API client
│   ├── bedrock_blueprint_manager/    # Manages Bedrock config
│   │   ├── handler.py                # Main Lambda handler
│   │   ├── bedrock_helpers.py        # Bedrock API helpers
│   │   └── bedrock_invoice_blueprint.json  # Invoice schema
│   ├── dlq_processor/                # Processes DLQ messages & sends alerts
│   │   └── handler.py                # DLQ processor Lambda handler
│   └── common/                       # Shared utilities
│       └── observability_helpers.py  # Quality assessment
├── terraform/                        # Infrastructure as Code (IaC)
│   ├── README.md                     # Terraform deployment guide
│   ├── lambda.tf                     # Lambda functions
│   ├── eventbridge.tf                # EventBridge scheduler & rules
│   ├── s3.tf                         # S3 buckets
│   ├── sqs.tf                        # Dead Letter Queues
│   ├── iam.tf                        # IAM roles & policies
│   ├── ssm.tf                        # SSM Parameter Store (secrets)
│   ├── cloudwatch.tf                 # Logs, alarms, dashboard
│   └── environments/                 # Environment configs (dev/prod)
├── notebook_utils/                   # Jupyter notebook utilities
├── test_data/                        # Sample invoices for testing
├── architecture_diagrams/            # System diagrams
├── tests/                            # Unit tests
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## Quick Start

### Deployment Options

**Option 1: Terraform (Recommended)** - Complete infrastructure deployment
- See [terraform/README.md](terraform/README.md) for automated deployment
- Deploys all Lambda functions, EventBridge rules, S3 buckets, DLQs, IAM roles, and monitoring
- Supports multiple environments (dev/prod)
- Estimated deployment time: 5 minutes

**Option 2: Manual Deployment** - Step-by-step setup (documented below)

### Prerequisites

- **AWS Account** with access to:
  - Lambda, S3, EventBridge, Bedrock Data Automation, SQS, SSM, SNS
- **Microsoft 365** with:
  - Azure AD app registration (client credentials flow)
  - Application permissions: `Mail.ReadWrite`
- **GVP API** credentials (login ID and password)
- **Python 3.11+** for local development
- **Terraform 1.6+** (if using Terraform deployment)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Microsoft 365 Access

See [lambda_functions/invoice_email_poller/README.md](lambda_functions/invoice_email_poller/README.md) for detailed Microsoft 365 setup.

**Quick summary:**
1. Create Azure AD app registration
2. Grant `Mail.ReadWrite` application permission
3. Create Application Access Policy to restrict to specific mailbox
4. Get client ID, client secret, tenant ID

### 3. Deploy Infrastructure

#### Option A: Terraform Deployment (Recommended)

```bash
cd terraform

# Initialize Terraform
terraform init

# Set required variables
export TF_VAR_azure_client_id="your-client-id"
export TF_VAR_azure_client_secret="your-secret"
export TF_VAR_azure_tenant_id="your-tenant-id"
export TF_VAR_mailbox_email="invoices@company.com"
export TF_VAR_gvp_login_id="novaadmin"
export TF_VAR_gvp_password="your-password"
export TF_VAR_alert_email="ops@company.com"

# Deploy
terraform apply -var-file="environments/dev.tfvars"

# Initialize Bedrock blueprint
BLUEPRINT_MANAGER=$(terraform output -raw lambda_function_names | jq -r '.blueprint_manager')
aws lambda invoke --function-name ${BLUEPRINT_MANAGER} --payload '{}' response.json
```

See [terraform/README.md](terraform/README.md) for complete instructions.

#### Option B: Manual Lambda Deployment

Set environment variables for each Lambda:

**invoice_email_poller:**
```bash
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
AZURE_TENANT_ID=<your-tenant-id>
MAILBOX_EMAIL=invoices@company.com
S3_BUCKET=devgvpbucket1
S3_PREFIX=Invoices/

# Observability
POWERTOOLS_SERVICE_NAME=invoice_email_poller
POWERTOOLS_METRICS_NAMESPACE=FreightAuditAgent
POWERTOOLS_LOGGER_LOG_EVENT=true
LOG_LEVEL=INFO
```

**bedrock_invoice_processor:**
```bash
PROJECT_NAME=Freight_Audit_Agent
AWS_REGION=us-east-1

# Observability
POWERTOOLS_SERVICE_NAME=bedrock_invoice_processor
POWERTOOLS_METRICS_NAMESPACE=FreightAuditAgent
POWERTOOLS_LOGGER_LOG_EVENT=true
LOG_LEVEL=INFO
```

**gvp_invoice_publisher:**
```bash
GVP_LOGIN_ID=novaadmin
GVP_PASSWORD=<your-gvp-password>

# Observability
POWERTOOLS_SERVICE_NAME=gvp_invoice_publisher
POWERTOOLS_METRICS_NAMESPACE=FreightAuditAgent
POWERTOOLS_LOGGER_LOG_EVENT=true
LOG_LEVEL=INFO
```

### 4. Setup Bedrock Blueprint

Run once to create Bedrock Data Automation project and blueprint:

```bash
cd lambda_functions/bedrock_blueprint_manager
python handler.py
```

This creates:
- Blueprint from `bedrock_invoice_blueprint.json` (15+ invoice fields)
- Data Automation project named `Freight_Audit_Agent`

### 5. Configure EventBridge Rules (Manual Deployment Only)

> **Note:** If using Terraform, EventBridge resources are created automatically. Skip to step 6.

**Scheduler:** EventBridge Scheduler
- Schedule: `cron(*/5 8-18 ? * MON-FRI *)` (every 5 min, business hours EST)
- Target: Default event bus with custom event
  ```json
  {
    "source": "custom.freight-audit",
    "detail-type": "Scheduled Invoice Poll"
  }
  ```

**Rule 1: Scheduler → Email Poller**
- Event pattern:
  ```json
  {
    "source": ["custom.freight-audit"],
    "detail-type": ["Scheduled Invoice Poll"]
  }
  ```
- Target: `invoice_email_poller` Lambda
- Dead Letter Queue: `email-poller-dlq` (SQS)

**Rule 2: S3 Upload → Bedrock**
- Enable EventBridge notifications on S3 bucket first
- Event pattern:
  ```json
  {
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {"name": ["devgvpbucket1"]},
      "object": {"key": [{"prefix": "Invoices/"}]}
    }
  }
  ```
- Target: `bedrock_invoice_processor` Lambda
- Dead Letter Queue: `invoice-processor-dlq` (SQS) ⚠️ Critical

**Rule 3: Bedrock Completion → GVP**
- Event pattern:
  ```json
  {
    "source": ["aws.bedrock-data-automation-runtime"],
    "detail-type": ["Data Automation Async Invocation Status Change"],
    "detail": {
      "status": ["SUCCEEDED"]
    }
  }
  ```
- Target: `gvp_invoice_publisher` Lambda
- Dead Letter Queue: `gvp-publisher-dlq` (SQS) ⚠️ Critical

> **Note:** If using Terraform, all monitoring resources (alarms, dashboard, log groups) are created automatically.

---

## Testing Locally

### Test Individual Lambda Functions

```bash
# Test blueprint manager
cd lambda_functions/bedrock_blueprint_manager
python handler.py

# Test GVP publisher (with test data)
cd lambda_functions/gvp_invoice_publisher
python handler.py

# Test bedrock processor (requires test_event.json)
cd lambda_functions/bedrock_invoice_processor
python handler.py
```

### Test with Jupyter Notebook

```bash
jupyter notebook invoice_processing_demo.ipynb
```

Interactive notebook for testing:
- Bedrock API calls
- Blueprint creation
- Invoice processing
- Output parsing

---

## DLQ Processor Lambda

The DLQ Processor Lambda is a critical component for error handling and alerting. It automatically processes failed Lambda executions and sends detailed email notifications.

### How It Works

1. **Trigger**: SQS event source mapping triggers DLQ Processor when messages arrive in DLQ
2. **Message Parsing**:
   - Detects Lambda async invoke format (has `requestPayload` field)
   - Extracts original EventBridge event from `requestPayload`
   - Falls back to EventBridge DLQ format for backwards compatibility
3. **Invoice Context Extraction**:
   - Parses Bedrock completion events (gvp_publisher DLQ)
   - Parses S3 upload events (invoice_processor DLQ)
   - Retrieves S3 metadata (correlation ID, invoice number, mailbox, recipient)
4. **Alert Generation**:
   - Determines failure stage (Bedrock Processing vs GVP API Publishing)
   - Formats detailed email with actionable troubleshooting steps
   - Publishes to SNS topic (`invoice_errors`)

### Supported DLQ Message Formats

**Lambda Async Invoke Format** (current):
```json
{
  "version": "1.0",
  "timestamp": "2025-12-17T12:00:00.000Z",
  "requestContext": {
    "requestId": "abc123",
    "functionArn": "arn:aws:lambda:...",
    "condition": "RetriesExhausted",
    "approximateInvokeCount": 3
  },
  "requestPayload": {
    "source": "aws.bedrock",
    "detail-type": "Bedrock Data Automation Job Succeeded",
    "detail": { ... }
  },
  "responseContext": {
    "statusCode": 200,
    "functionError": "Unhandled"
  },
  "responsePayload": {
    "errorType": "HTTPError",
    "errorMessage": "503 Server Error"
  }
}
```

**EventBridge DLQ Format** (legacy):
```json
{
  "source": "aws.bedrock",
  "detail-type": "Bedrock Data Automation Job Succeeded",
  "detail": { ... }
}
```

### Email Alert Contents

Each DLQ alert email includes:
- **Invoice Details**: Number, mailbox, recipient address, correlation ID
- **Failure Context**: Stage (Bedrock/GVP), issue description, event time
- **File Locations**: S3 paths for PDF invoice and Bedrock output
- **CloudWatch Logs**: Direct links and Logs Insights queries
- **Reprocessing Steps**: Manual recovery instructions
- **AWS CLI Commands**: Ready-to-use commands for downloading PDFs

### Environment Configuration

```bash
SNS_INVOICE_ERROR_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:prod-freight-audit-agent-invoice-errors
POWERTOOLS_SERVICE_NAME=dlq_processor
POWERTOOLS_METRICS_NAMESPACE=FreightAuditAgent
LOG_LEVEL=INFO
```

### Monitoring

- CloudWatch Logs: `/aws/lambda/prod-freight-audit-agent-dlq-processor`
- Metrics: DLQ messages processed, SNS publish success/failure
- No CloudWatch alarms on DLQs (alerts handled by DLQ Processor Lambda)

---

## Invoice Schema

The system extracts the following fields from freight invoices:

| Field | Type | Description |
|-------|------|-------------|
| `InvoiceDate` | Date | Invoice issue date |
| `InvoiceNumber` | String | Unique invoice identifier |
| `Carrier` | String | Freight carrier name |
| `Currency` | String | Currency code (USD, CAD, etc.) |
| `FeeAmount` | Number | Total invoice amount |
| `PartyName` | String | Billing party name |
| `FleetID` | String | Fleet identifier |
| `GLAccount` | String | General ledger account |
| `CostCenter` | String | Cost center code |
| `BOLNumber` | String | Bill of lading number |
| `OriginCity` | String | Shipment origin city |
| `OriginState` | String | Shipment origin state |
| `DestinationCity` | String | Shipment destination city |
| `DestinationState` | String | Shipment destination state |
| `STCC` | String | Standard Transportation Commodity Code |
| `LeadEquipmentID` | String | Equipment identifier |
| `ServiceDate` | Date | Service date |
| `Comments` | String | Additional comments |

Schema defined in: `lambda_functions/bedrock_blueprint_manager/bedrock_invoice_blueprint.json`

---

## Observability & Monitoring

### CloudWatch Dashboard

View real-time metrics:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=FreightAuditAgent
```

**Widgets:**
- Emails processed today
- GVP posts successful
- Success rate percentage
- Average end-to-end latency
- Error rates by function
- Throughput over time

### CloudWatch Logs Insights

**Track specific invoice:**
```sql
fields @timestamp, function_name, message
| filter correlation_id = "EMAIL123_1699564800"
| sort @timestamp asc
```

**Recent errors:**
```sql
fields @timestamp, function_name, correlation_id, message
| filter level = "ERROR"
| sort @timestamp desc
| limit 50
```

More queries in [terraform/README.md - Monitoring Section](terraform/README.md#monitoring--observability)

### CloudWatch Alarms

5 critical alarms configured:
1. **Email poll errors** (> 3 in 10 min)
2. **GVP post failures** (> 5 in 10 min)
3. **No PDFs uploaded** (stuck pipeline)
4. **High latency** (p95 > 15 min)
5. **Low success rate** (< 95%)

---

## API Documentation

### GVP API

**Endpoint:** `https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice`

**Authentication:** Bearer token (obtained via login)

**Postman Collection:** [gvp_api.postman_collection.json](gvp_api.postman_collection.json)

### Microsoft Graph API

**Base URL:** `https://graph.microsoft.com/v1.0`

**Endpoints Used:**
- `GET /users/{mailbox}/messages?$filter=isRead eq false`
- `GET /users/{mailbox}/messages/{id}/attachments`
- `GET /users/{mailbox}/messages/{id}/attachments/{attachmentId}/$value`
- `PATCH /users/{mailbox}/messages/{id}` (mark as read)

**Documentation:** [lambda_functions/invoice_email_poller/README.md](lambda_functions/invoice_email_poller/README.md)

---

## Cost Estimate

### AWS Services (per 1,000 invoices/month)

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| **Lambda** | 3,000 invocations @ 1GB, 30s avg | $0.60 |
| **Bedrock Data Automation** | 1,000 jobs | $50.00 |
| **S3** | 1,000 PDFs (5 MB avg) + outputs | $0.12 |
| **SQS** | DLQs (minimal, failures only) | $0.00 |
| **EventBridge** | Events + scheduler | $0.10 |
| **CloudWatch** | Logs (2 GB) + Metrics + Dashboard | $7.76 |
| **SSM Parameter Store** | 4 SecureString parameters | $0.00 |
| **Total** | | **~$58.58** |

**Cost per invoice:** $0.06

**Scales linearly** with invoice volume.

---

## Troubleshooting

### Email Polling Issues

**Problem:** No emails being fetched

**Solutions:**
1. Verify Azure AD credentials are correct
2. Check Application Access Policy is configured
3. Verify mailbox email address is correct
4. Check CloudWatch logs for authentication errors
5. Test Microsoft Graph API access manually

### Bedrock Job Failures

**Problem:** Bedrock jobs failing or timing out

**Solutions:**
1. Check PDF is valid and not corrupted
2. Verify Bedrock project exists: `aws bedrock-data-automation list-data-automation-projects`
3. Check Bedrock quotas and throttling
4. Review Bedrock job logs in CloudWatch

### GVP API Failures

**Problem:** GVP posts failing

**Solutions:**
1. Verify GVP credentials are correct
2. Check GVP API status (https://qagvp.intellitrans.com)
3. Review required fields in GVP API documentation
4. Check CloudWatch logs for specific error messages
5. Test GVP API manually with Postman collection

### Pipeline Stuck

**Problem:** Invoices not completing end-to-end

**Solutions:**
1. Check CloudWatch dashboard for stuck stage
2. **Check Dead Letter Queues** for failed events:
   ```bash
   # Via Terraform outputs
   aws sqs get-queue-attributes \
     --queue-url $(terraform output -raw dlq_urls | jq -r '.invoice_processor') \
     --attribute-names ApproximateNumberOfMessages
   ```
3. Use Logs Insights query: "Invoices stuck in pipeline"
4. Verify EventBridge rules are active
5. Check Lambda execution role permissions
6. Review correlation ID tracking through logs

### Dead Letter Queue Issues

**Problem:** Messages appearing in DLQs

**Automatic Response:**
- DLQ Processor Lambda automatically triggers when messages arrive in DLQ
- Sends detailed SNS email alert with:
  - Invoice number, correlation ID, mailbox, recipient address
  - Failure stage (Bedrock Processing vs GVP API Publishing)
  - S3 paths (PDF invoice location and Bedrock output)
  - CloudWatch log search queries
  - Manual reprocessing instructions

**Manual Investigation:**
1. Check email alerts for detailed failure information
2. Use correlation ID from alert to search CloudWatch Logs
3. Review Lambda logs at time of failure (log path included in alert)
4. Examine DLQ message structure if needed
5. Reprocess failed invoices using instructions in alert email
6. See [terraform/README.md - DLQ Operations](terraform/README.md#dead-letter-queue-dlq-operations) for reprocessing scripts

**Common Failure Scenarios:**
- **GVP API Publishing Failure**: Bedrock extraction succeeded but GVP API is down/unreachable
- **Bedrock Processing Failure**: PDF uploaded but Bedrock Data Automation job failed
- **Lambda Execution Failure**: Unhandled exceptions in Lambda code

**DLQ Message Formats Supported:**
- Lambda async invoke format (wrapped in `requestPayload`)
- EventBridge DLQ format (original event directly)

See [terraform/README.md](terraform/README.md) for detailed troubleshooting and monitoring guides.

---

## Development

### Code Style

- **Python:** PEP 8 compliant
- **Logging:** Structured JSON via AWS Lambda Powertools
- **Error Handling:** Try-except with specific error logging
- **Documentation:** Docstrings for all functions

### Adding New Fields to Invoice Schema

1. Edit `bedrock_invoice_blueprint.json`
2. Add field definition with `inferenceType: "explicit"`
3. Run `bedrock_blueprint_manager` Lambda to update
4. Update `gvp_client.py` to include new field in API payload
5. Test with sample invoice


## Security Considerations

1. **Credentials Management**
   - Never commit `.env` or `settings.json` files
   - Use AWS Secrets Manager for production credentials
   - Rotate credentials regularly

2. **IAM Permissions**
   - Follow principle of least privilege
   - Lambda execution roles should only have required permissions
   - Use separate roles for each Lambda function

3. **Input Validation**
   - Filename sanitization in email poller
   - S3 metadata sanitization (remove control characters)
   - PDF validation before processing

4. **Network Security**
   - Use VPC for Lambda functions if accessing private resources
   - Enable S3 bucket encryption at rest

5. **Data Privacy**
   - Invoice PDFs contain PII - configure appropriate retention policies

---

## Performance

### Benchmarks (Approximate)

| Stage | Duration | Bottleneck |
|-------|----------|------------|
| Email poll | 5-60 seconds | Microsoft Graph API response time |
| S3 upload | 1-5 seconds | PDF size |
| Bedrock processing | 2-8 minutes | Document complexity, field count |
| GVP post | 1-3 seconds | GVP API response time |
| **Total** | **8-13 minutes** | Bedrock processing |



## Roadmap

### Phase 1 (Completed)
- ✅ Microsoft 365 email integration
- ✅ AWS Bedrock Data Automation integration
- ✅ GVP API integration
- ✅ Full observability (metrics, logs, dashboard, alarms)
- ✅ Correlation ID tracking across entire pipeline
- ✅ Quality assessment logging
- ✅ DLQ handling with automatic SNS email alerts
- ✅ DLQ Processor Lambda with Lambda async invoke format support
- ✅ Terraform infrastructure as code
- ✅ EventBridge Scheduler → Rule → Lambda pattern
- ✅ SSM Parameter Store for secrets management
- ✅ Lambda async invoke configuration for execution failure handling

### Phase 2 (To be done)
- [ ] Manual review workflow for low-quality extractions
- [ ] Multi-mailbox support with per-mailbox metrics
- [ ] Cost per invoice tracking


---




## Acknowledgments

Built with:
- [AWS Lambda Powertools](https://awslabs.github.io/aws-lambda-powertools-python/) for observability
- [AWS Bedrock Data Automation](https://aws.amazon.com/bedrock/data-automation/) for AI extraction
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/overview) for email integration
- [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python) for Azure AD authentication
- [Terraform](https://www.terraform.io/) for infrastructure as code

---

**Last Updated:** 17 Dec 2025
**Version:** 1.1.0
**Status:** Production
