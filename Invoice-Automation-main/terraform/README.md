# Freight Audit Agent - Terraform Deployment

This directory contains Terraform infrastructure-as-code for deploying the Freight Audit Agent to AWS.

## Architecture Overview

The Terraform deployment creates:

1. **5 Lambda Functions**
   - `email_poller` - Polls Microsoft 365 mailbox
   - `blueprint_manager` - Manages Bedrock blueprints
   - `invoice_processor` - Processes invoices with Bedrock
   - `gvp_publisher` - Publishes to GVP/Oracle API
   - `dlq_processor` - Processes DLQ messages and sends detailed alerts

2. **EventBridge Resources**
   - EventBridge Scheduler → EventBridge Rule → Email Poller Lambda
   - S3 Upload Event Rule → Invoice Processor Lambda
   - Bedrock Completion Event Rule → GVP Publisher Lambda

3. **1 S3 Bucket** (or use existing)
   - Single bucket with two prefixes:
     - `freight-audit-agent-invoices/` for raw PDF invoices
     - `freight-audit-agent-output/` for Bedrock structured output
   - Can use existing bucket (e.g., `prodgvpfilestore1`) or create new one

4. **Dead Letter Queues (DLQs) + Automated Alerting**
   - Email poller DLQ (scheduler event failures)
   - Invoice processor DLQ (S3 event failures) ⚠️ Critical
   - GVP publisher DLQ (Bedrock event failures) ⚠️ Critical
   - Reprocessing queue (manual retry workflows)
   - DLQ Processor Lambda automatically sends detailed alerts via SNS

5. **SNS Topics for Alerts**
   - `invoice-errors` - Detailed invoice failure alerts (sent by DLQ Processor)
   - `alerts` - General CloudWatch alarms (optional)

6. **IAM Roles & Policies**
   - Per-function Lambda execution roles
   - EventBridge Scheduler role
   - SSM Parameter Store access
   - CloudWatch Logs & Metrics permissions

7. **SSM Parameter Store** (SecureString)
   - Azure AD credentials
   - GVP API password

8. **CloudWatch Resources**
   - Log groups with retention
   - Metric alarms
   - Dashboard

## Recent Changes & Enhancements

### ✅ Lambda Async Invoke Configuration (NEW)
- **Automatic retries at Lambda level** using `aws_lambda_function_event_invoke_config`
- 2 retry attempts (3 total invocations) before sending to DLQ
- Properly handles Lambda execution failures (not just delivery failures)
- IAM permissions added for Lambda roles to send messages to SQS DLQ
- Configured for all critical Lambda functions: `gvp_publisher`, `invoice_processor`, `email_poller`

### ✅ Automated DLQ Alerting with Smart Message Parsing (UPDATED)
- **DLQ Processor Lambda** automatically sends detailed email alerts when invoices fail
- Supports **Lambda async invoke message format** (extracts event from `requestPayload` wrapper)
- Backwards compatible with EventBridge DLQ format
- ONE email per failed invoice (after all 3 retry attempts) with full invoice context
- Includes invoice number, correlation ID, mailbox, S3 paths, CloudWatch logs queries, and reprocessing steps
- Separate SNS topic `invoice-errors` for invoice-specific alerts

### ✅ CloudWatch DLQ Alarms Disabled
- **No duplicate alerts** - CloudWatch DLQ alarms (monitoring queue depth) have been disabled
- DLQ alerting is now exclusively handled by DLQ Processor Lambda
- Prevents generic "DLQ has messages" emails that lack invoice context
- All alerts now include detailed failure information for actionable troubleshooting

### ✅ Improved Error Handling
- **All exceptions are re-raised** to enable Lambda async invoke config to detect failures
- Lambda re-raises exceptions → Lambda async invoke retries 2x → DLQ after 3 failures → Detailed alert sent
- AWS Lambda Powertools `@metrics.log_metrics()` decorator re-enabled for automatic metric flushing
- Error metrics now captured even when exceptions are raised

### ✅ S3 Bucket Flexibility
- **Use existing bucket** (e.g., `prodgvpfilestore1`) or create new one
- Terraform automatically merges bucket policies (preserves existing policies)
- Configurable S3 prefixes with descriptive names:
  - `freight-audit-agent-invoices/` for raw PDFs
  - `freight-audit-agent-output/` for Bedrock output

### ✅ Data Sanitization for GVP API
- **BOLNumber truncation**: Automatically truncates BOLNumber to 20 characters if exceeded
  - Example: `"106386, 106383, 106380, 106384..."` (200+ chars) → `"106386, 106383, 1063"` (20 chars)
  - Logs warning with original and truncated values
- **ServiceDate selection**: Takes first date when multiple dates are present
  - Example: `"11/15/2025, 11/16/2025, 11/17/2025"` → `"11/15/2025"`
  - Logs info with original and selected values

### ✅ Parameterized GVP API URLs
- **Configurable endpoints** for different environments (QA vs Production)
- Environment variables:
  - `GVP_AUTH_URL` - Authentication endpoint (defaults to QA: `https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken`)
  - `GVP_API_URL` - API endpoint (defaults to QA: `https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice`)
- Configure in `terraform.tfvars` or use defaults for QA environment
- Easy switching between QA and Production without code changes

## Prerequisites

### 1. Install Required Tools

```bash
# Terraform >= 1.6
terraform --version

# AWS CLI v2
aws --version

# Configure AWS credentials
aws configure
```

**IAM Permissions for Terraform User/Role:**

The AWS credentials you configure must have sufficient permissions to create and manage resources. Required permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "iam:*",
        "s3:*",
        "events:*",
        "scheduler:*",
        "logs:*",
        "ssm:*",
        "sqs:*",
        "sns:*",
        "cloudwatch:*",
        "bedrock:*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

**For production, use least-privilege policies.** The above is for development/testing.

**Verify your permissions:**
```bash
# Check your AWS identity
aws sts get-caller-identity

# Check if you can create Lambda functions
aws lambda list-functions

# Check if you can read/write S3 buckets
aws s3 ls
```

### 2. Prepare Backend (S3 + DynamoDB)

**IMPORTANT**: Before running Terraform, create the S3 bucket and DynamoDB table for state management:

```bash
# Set your variables
BUCKET_NAME="freight-audit-terraform-state"
TABLE_NAME="terraform-state-lock"
REGION="us-east-1"

# Create S3 bucket for Terraform state
aws s3 mb s3://${BUCKET_NAME} --region ${REGION}

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ${BUCKET_NAME} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ${BUCKET_NAME} \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Block public access
aws s3api put-public-access-block \
  --bucket ${BUCKET_NAME} \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name ${TABLE_NAME} \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${REGION}
```

If you want to use a different backend configuration, edit `versions.tf`.

### 3. Configure Azure AD Application

Follow the instructions in `lambda_functions/invoice_email_poller/README.md` to:
- Create an Azure AD application
- Configure Microsoft Graph API permissions (`Mail.ReadWrite`)
- Set up Application Access Policy for the mailbox

### 4. Prepare Secrets and Configuration

Set sensitive variables as environment variables:

```bash
export TF_VAR_azure_client_id="your-azure-client-id"
export TF_VAR_azure_client_secret="your-azure-client-secret"
export TF_VAR_azure_tenant_id="your-azure-tenant-id"
export TF_VAR_mailbox_email="invoices@yourcompany.com"
export TF_VAR_gvp_login_id="novaadmin"
export TF_VAR_gvp_password="your-gvp-password"
export TF_VAR_alert_email="ops-team@yourcompany.com"

# Optional: Configure GVP API URLs (defaults to QA environment)
export TF_VAR_gvp_auth_url="https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
export TF_VAR_gvp_api_url="https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"

# For Production environment:
# export TF_VAR_gvp_auth_url="https://gvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
# export TF_VAR_gvp_api_url="https://gvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"
```

**Alternative**: Create a `terraform.tfvars` file (NOT committed to Git):

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

**Example terraform.tfvars for QA environment:**
```hcl
# Azure AD Configuration
azure_client_id     = "your-azure-client-id"
azure_client_secret = "your-azure-client-secret"
azure_tenant_id     = "your-azure-tenant-id"
mailbox_email       = "invoices@yourcompany.com"

# GVP API Configuration (QA)
gvp_login_id  = "novaadmin"
gvp_password  = "your-gvp-password"
gvp_auth_url  = "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
gvp_api_url   = "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"

# Alerts
alert_email = "ops-team@yourcompany.com"

# S3 Configuration
use_existing_bucket  = false
invoice_s3_prefix    = "freight-audit-agent-invoices/"
output_s3_prefix     = "freight-audit-agent-output/"
```

**Example terraform.tfvars for Production environment:**
```hcl
# Same as QA, but with production GVP URLs:
gvp_auth_url  = "https://gvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
gvp_api_url   = "https://gvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"

# And use existing production bucket:
use_existing_bucket   = true
existing_bucket_name  = "prodgvpfilestore1"
```

### 5. Configure S3 Bucket Options

You have two options for S3 bucket configuration:

**Option A: Use an Existing Bucket** (e.g., `prodgvpfilestore1`)

Set these variables in your `.tfvars` file:
```hcl
use_existing_bucket   = true
existing_bucket_name  = "prodgvpfilestore1"
invoice_s3_prefix     = "freight-audit-agent-invoices/"
output_s3_prefix      = "freight-audit-agent-output/"
```

What Terraform will configure automatically:
- ✅ EventBridge notifications (enables S3 events)
- ✅ Bucket policy for Bedrock Data Automation access (MERGED with existing policies)
- ✅ IAM roles and policies for Lambda functions

What Terraform will NOT modify:
- ❌ Versioning settings
- ❌ Encryption configuration
- ❌ Lifecycle policies
- ❌ Existing bucket policy statements (preserved and merged)

**How Policy Merging Works:**
1. Terraform calls AWS API `s3:GetBucketPolicy` to read existing policies
2. Parses existing policy statements (if any)
3. Adds new Bedrock Data Automation access statements
4. Merges them into a single policy document
5. Applies the merged policy back to the bucket
6. **Your existing policies are preserved!**

**IAM Permissions Required:**

Your AWS credentials (used by Terraform) must have these permissions on the existing bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucket",
        "s3:GetBucketPolicy",
        "s3:PutBucketPolicy",
        "s3:GetBucketNotification",
        "s3:PutBucketNotification"
      ],
      "Resource": "arn:aws:s3:::prodgvpfilestore1"
    }
  ]
}
```

**Check your permissions:**
```bash
# Test if you can read the bucket policy
aws s3api get-bucket-policy --bucket prodgvpfilestore1

# Test if you can read bucket notifications
aws s3api get-bucket-notification-configuration --bucket prodgvpfilestore1
```

**Important Notes:**
- Terraform dynamically retrieves your AWS Account ID using `aws sts get-caller-identity`
- Account IDs in policy conditions are automatically populated (no hardcoding needed)
- If the bucket has policies with the same Sid (Statement ID) as our Bedrock statements, they will be overridden
- Our Bedrock statements use Sids: `AllowBedrockDataAutomationRead` and `AllowBedrockDataAutomationWrite`
- The bucket must exist in the same AWS account and region

**Verify Policy Merging:**
```bash
# Check your AWS Account ID (used in policy conditions)
aws sts get-caller-identity --query Account --output text

# Check existing policies before Terraform apply
aws s3api get-bucket-policy --bucket prodgvpfilestore1 | jq -r '.Policy' | jq

# After terraform apply, verify merged policy
aws s3api get-bucket-policy --bucket prodgvpfilestore1 | jq -r '.Policy' | jq '.Statement'
# Should show: existing statements + new Bedrock statements
```

**Option B: Create a New Bucket** (default)

Set these variables in your `.tfvars` file:
```hcl
use_existing_bucket   = false
invoice_s3_prefix     = "freight-audit-agent-invoices/"
output_s3_prefix      = "freight-audit-agent-output/"
```

Terraform will create a new bucket with:
- Versioning enabled
- AES256 encryption
- Public access blocked
- Lifecycle policies (90-day transition for invoices, 90-day expiration for outputs)
- EventBridge notifications enabled
- Bedrock Data Automation access policy

**Prefix Customization:**
The S3 prefixes are configurable and default to descriptive names:
- `invoice_s3_prefix` defaults to `"freight-audit-agent-invoices/"`
- `output_s3_prefix` defaults to `"freight-audit-agent-output/"`

## Deployment Steps

### Step 1: Initialize Terraform

```bash
cd terraform
terraform init
```

This will:
- Download required provider plugins (AWS, Archive)
- Initialize the S3 backend for state storage
- Prepare the working directory

### Step 2: Review the Plan

```bash
# For dev environment
terraform plan -var-file="environments/dev.tfvars"

# For prod environment
terraform plan -var-file="environments/prod.tfvars"
```

Review the output to ensure all resources are correct.

### Step 3: Apply the Configuration

```bash
# For dev environment
terraform apply -var-file="environments/dev.tfvars"

# For prod environment
terraform apply -var-file="environments/prod.tfvars"

# Type 'yes' when prompted to confirm
```

This will create:
- ~35 resources total
- 5 Lambda functions with deployment packages
- 3 EventBridge rules + 1 Scheduler
- 1 S3 bucket (or use existing if configured)
- 5 IAM roles + policies
- 4 SSM parameters
- 5 CloudWatch log groups
- 2 SNS topics (invoice errors + general alerts)
- 3 SQS Dead Letter Queues
- 2 SQS event source mappings (DLQ → DLQ Processor Lambda)
- CloudWatch alarms + dashboard

**Deployment time**: ~3-5 minutes

### Step 4: Initialize Bedrock Blueprints

After Terraform completes, manually invoke the `blueprint_manager` Lambda to create Bedrock blueprints and projects:

```bash
# Get the function name from Terraform output
BLUEPRINT_MANAGER=$(terraform output -raw lambda_function_names | jq -r '.blueprint_manager')

# Invoke the function
aws lambda invoke \
  --function-name ${BLUEPRINT_MANAGER} \
  --payload '{}' \
  response.json

# Check the response
cat response.json | jq
```

Expected output:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Blueprint and project configured successfully",
    "blueprint_arn": "arn:aws:bedrock:...",
    "project_arn": "arn:aws:bedrock:..."
  }
}
```

### Step 5: Verify Deployment

1. **Check Lambda functions**:
   ```bash
   aws lambda list-functions --query 'Functions[?contains(FunctionName, `freight-audit`)].FunctionName'
   ```

2. **Check EventBridge rules**:
   ```bash
   aws events list-rules --name-prefix "dev-freight-audit"
   ```

3. **Check S3 bucket**:
   ```bash
   terraform output -raw s3_bucket_name
   aws s3 ls $(terraform output -raw s3_bucket_name)
   ```

4. **View CloudWatch Dashboard**:
   - Go to AWS Console → CloudWatch → Dashboards
   - Open `dev-freight-audit-agent-dashboard`

5. **Test email polling manually**:
   ```bash
   EMAIL_POLLER=$(terraform output -raw lambda_function_names | jq -r '.email_poller')

   aws lambda invoke \
     --function-name ${EMAIL_POLLER} \
     --payload '{}' \
     response.json

   cat response.json | jq
   ```

## Monitoring & Observability

### CloudWatch Logs with Correlation ID

All Lambda functions use AWS Lambda Powertools for structured logging. To trace an invoice end-to-end:

1. Find the correlation ID in the email_poller logs:
   ```bash
   aws logs tail /aws/lambda/dev-freight-audit-agent-email-poller --follow
   ```
   Look for: `"correlation_id": "123e4567-e89b-12d3-a456-426614174000"`

2. Search across all functions using CloudWatch Logs Insights:
   ```sql
   fields @timestamp, @message, correlation_id, service, @logStream
   | filter correlation_id = "123e4567-e89b-12d3-a456-426614174000"
   | sort @timestamp asc
   ```

### CloudWatch Metrics

Custom metrics in the `FreightAuditAgent` namespace:

**Success Metrics:**
- `PDFsUploaded` - Count of PDFs uploaded to S3
- `BedrockJobsStarted` - Count of Bedrock jobs initiated
- `GVPPostsSuccessful` - Count of successful GVP API posts (includes new + duplicates)
- `GVPPostsDuplicate` - Count of duplicate invoices detected (idempotent handling)
- `EndToEndLatency` - Time from email received to GVP posted (milliseconds)

**Error Metrics (NEW):**
- `GVPPostsFailed` - Count of failed GVP API posts (general failures)
- `GVPTimeout` - Count of GVP API timeout errors
- `GVPConnectionError` - Count of GVP API connection errors
- `GVPHTTPError` - Count of GVP API HTTP errors (4xx/5xx)
- `GVPUnknownError` - Count of unknown errors during GVP publishing

**Data Quality Metrics (NEW):**
- Logged in CloudWatch Logs (not as metrics):
  - BOLNumber truncation warnings (when >20 characters)
  - ServiceDate selection info (when multiple dates found)

View metrics:
```bash
# View successful posts
aws cloudwatch get-metric-statistics \
  --namespace FreightAuditAgent \
  --metric-name GVPPostsSuccessful \
  --dimensions Name=service,Value=gvp_invoice_publisher \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum

# View timeout errors
aws cloudwatch get-metric-statistics \
  --namespace FreightAuditAgent \
  --metric-name GVPTimeout \
  --dimensions Name=service,Value=gvp_invoice_publisher \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### CloudWatch Alarms

If `enable_alarms = true` and `alert_email` is set, you'll receive email notifications for:
- **Lambda function errors** (>3 errors in 10 minutes) - General Lambda health
- **Lambda throttles** (>5 throttles in 5 minutes) - Concurrency issues
- **GVP publishing failures** (>5 failures in 5 minutes) - Custom metric from Lambda Powertools

**Note on DLQ Alarms:**
- CloudWatch DLQ alarms (monitoring `ApproximateNumberOfMessagesVisible`) are **DISABLED** to prevent duplicate alerts
- DLQ alerting is handled exclusively by the **DLQ Processor Lambda**, which sends detailed invoice-specific alerts
- This approach provides ONE detailed email per failed invoice (instead of generic "DLQ has messages" alerts)

Check alarm status:
```bash
aws cloudwatch describe-alarms --alarm-name-prefix "dev-freight-audit"
```

## Dead Letter Queue (DLQ) Operations & Automated Alerting

### Overview

The system uses Dead Letter Queues (DLQs) to capture failed events at critical points in the processing pipeline, ensuring no invoice data is lost due to transient failures. When invoices fail after all retry attempts, the **DLQ Processor Lambda** automatically sends detailed alerts to the ops team.

### DLQ Architecture with Automated Alerts

```
EventBridge → Lambda Execution (with async invoke config)
                 ↓
            Exception raised?
                 ↓
            Lambda retries 2x (async invoke config)
                 ↓
            Still fails after 3 total attempts?
                 ↓
            Send to DLQ (Lambda async invoke destination)
                 ↓
            DLQ Processor Lambda (triggered by SQS event source mapping)
                 ↓
            SNS Alert Email (detailed invoice context)
```

**How It Works:**
1. EventBridge successfully delivers event to Lambda (no retry needed at this level)
2. Lambda function execution encounters an error (timeout, API error, etc.)
3. Lambda **re-raises the exception** (critical for async invoke config to detect failure)
4. **Lambda async invoke config** retries the execution 2 more times (3 total attempts)
5. If all 3 attempts fail → **Lambda async invoke config** sends message to DLQ
6. SQS event source mapping triggers **DLQ Processor Lambda**
7. DLQ Processor parses message, extracts invoice details, and sends **ONE detailed alert email**

**Key Distinction:**
- **EventBridge DLQ**: Only triggers when EventBridge cannot DELIVER event to Lambda (permissions, throttling)
- **Lambda Async Invoke DLQ**: Triggers when Lambda EXECUTION fails (exceptions raised)
- We use **Lambda async invoke DLQ** because we need to handle execution failures, not delivery failures

**Dead Letter Queues:**
1. **email-poller-dlq** - Scheduler events that failed to poll emails (7-day retention)
2. **invoice-processor-dlq** ⚠️ **CRITICAL** - S3 upload events that failed Bedrock processing (14-day retention)
3. **gvp-publisher-dlq** ⚠️ **CRITICAL** - Bedrock completion events that failed GVP posting (14-day retention)

### Error Handling & Retry Strategy

**GVP Publisher Lambda** uses intelligent exception handling:
- **Timeout errors** → Re-raise (network might recover)
- **Connection errors** → Re-raise (server might come back)
- **HTTP 5xx errors** → Re-raise (server error, might be transient)
- **HTTP 4xx errors** → Re-raise (triggers DLQ alert for manual review)
- **Unknown errors** → Re-raise (safer to retry)

**Why re-raise ALL errors?**
- ✅ Ensures NO invoices are lost (every failure → DLQ → alert)
- ✅ Consistent behavior (all failures trigger same alert mechanism)
- ✅ Safer approach (even "permanent" errors might be transient)
- ⚠️ Trade-off: Wastes 2 retries on permanent errors (delays alert by ~6 minutes)

### Lambda Async Invoke Configuration

**What It Does:**
All critical Lambda functions are configured with Lambda async invoke configuration to automatically retry failed executions and send failures to DLQ. This is separate from EventBridge retry configuration.

**Configuration Details:**
- **Retry Attempts**: 2 retries (3 total attempts including initial invocation)
- **Event Age**: Discards events older than 1 hour
- **DLQ Destination**: Sends failed events to SQS DLQ after all retries exhausted

**Applied To:**
- `gvp_publisher` - Bedrock completion → GVP API posting
- `invoice_processor` - S3 upload → Bedrock job initiation
- `email_poller` - Scheduler → M365 email polling

**DLQ Message Format:**

When Lambda async invoke config sends messages to DLQ, they are wrapped with metadata about the failure:
- **Request Context**: Function ARN, request ID, condition (RetriesExhausted), invoke count (3)
- **Request Payload**: Original EventBridge event (Bedrock completion or S3 upload event)
- **Response Context**: Function error type (Unhandled, TimeoutError, etc.)
- **Response Payload**: Error message and error type from Lambda execution

**DLQ Processor Compatibility:**

The DLQ Processor Lambda automatically detects and handles both message formats:
1. **Lambda async invoke format**: Extracts original EventBridge event from `requestPayload` field
2. **EventBridge DLQ format**: Processes original event directly (backwards compatible)

This ensures alerts always include invoice details (correlation ID, invoice number, S3 paths) regardless of how the message reached the DLQ.

**IAM Permissions:**

Lambda execution roles have been granted `sqs:SendMessage` permission to their respective DLQ queues. Without this permission, Lambda async invoke config cannot send messages to DLQ.

### When Messages Land in DLQ

| DLQ | Common Causes | Impact |
|-----|---------------|--------|
| invoice-processor-dlq | Lambda errors, Bedrock throttling, IAM issues | PDF uploaded but not processed |
| gvp-publisher-dlq | GVP API timeout, HTTP errors, auth failures | Invoice extracted but not posted |
| email-poller-dlq | Graph API auth failures, S3 permission issues | Emails not processed (low risk) |

### Automated Alert Emails

**What You'll Receive:**

When an invoice fails after all retries, you'll receive **ONE detailed email** with:
- 📋 **Invoice Details**: Invoice number, carrier, recipient address, correlation ID
- 🚨 **Failure Stage**: Where it failed (Bedrock processing vs GVP publishing)
- 📁 **File Locations**: S3 URIs for PDF invoice and Bedrock output
- 🔍 **CloudWatch Logs**: Pre-formatted search queries with correlation ID
- 📖 **Manual Steps**: Instructions for reprocessing from DLQ
- 🛠️ **AWS CLI Commands**: Ready-to-run commands for downloading PDF

**Email Subject:**
```
🚨 CRITICAL: Invoice 12345678 Failed - In DLQ
```

**Alert Timing:**
- After 3 failed attempts (initial + 2 retries via Lambda async invoke config)
- Delay depends on error type: immediate for quick failures, up to ~6 minutes for timeouts
- ONE email per failed invoice (not 3 separate emails per retry)
- DLQ Processor typically triggers within 1-2 minutes after message arrives in DLQ

### Monitoring DLQs

**Automated Monitoring:**
- DLQ Processor Lambda automatically sends email alerts when messages arrive
- No need for manual monitoring - you'll be notified immediately
- CloudWatch DLQ alarms are disabled to prevent duplicate notifications

**Manual DLQ Inspection (if needed):**

Check DLQ depth manually:
```bash
# Invoice Processor DLQ
aws sqs get-queue-attributes \
  --queue-url $(terraform output -raw dlq_urls | jq -r '.invoice_processor') \
  --attribute-names ApproximateNumberOfMessages

# GVP Publisher DLQ
aws sqs get-queue-attributes \
  --queue-url $(terraform output -raw dlq_urls | jq -r '.gvp_publisher') \
  --attribute-names ApproximateNumberOfMessages
```

**View messages without removing:**
```bash
QUEUE_URL=$(terraform output -raw dlq_urls | jq -r '.invoice_processor')

aws sqs receive-message \
  --queue-url ${QUEUE_URL} \
  --max-number-of-messages 10 \
  --visibility-timeout 0
```

**Check DLQ Processor Lambda logs:**
```bash
aws logs tail /aws/lambda/dev-freight-audit-agent-dlq-processor --follow
```

### Reprocessing Failed Events

#### Invoice Processor DLQ (S3 Events)

1. **Read the DLQ message:**
```bash
QUEUE_URL=$(terraform output -raw dlq_urls | jq -r '.invoice_processor')

aws sqs receive-message \
  --queue-url ${QUEUE_URL} \
  --max-number-of-messages 1 \
  --visibility-timeout 300 > message.json
```

2. **Manually invoke the Lambda:**
```bash
INVOICE_PROCESSOR=$(terraform output -raw lambda_function_names | jq -r '.invoice_processor')

# Use the event from DLQ
cat message.json | jq -r '.Messages[0].Body' > event.json

aws lambda invoke \
  --function-name ${INVOICE_PROCESSOR} \
  --payload file://event.json \
  response.json

cat response.json | jq
```

3. **Delete the message if successful:**
```bash
RECEIPT_HANDLE=$(cat message.json | jq -r '.Messages[0].ReceiptHandle')

aws sqs delete-message \
  --queue-url ${QUEUE_URL} \
  --receipt-handle "${RECEIPT_HANDLE}"
```

#### GVP Publisher DLQ (Bedrock Completion Events)

Follow the same pattern, using the gvp-publisher-dlq and gvp_publisher Lambda function.

#### Bulk Reprocessing Script

```bash
#!/bin/bash
# reprocess_dlq.sh

set -e

DLQ_URL=$1
LAMBDA_FUNCTION=$2
MAX_MESSAGES=${3:-10}

if [ -z "$DLQ_URL" ] || [ -z "$LAMBDA_FUNCTION" ]; then
  echo "Usage: ./reprocess_dlq.sh <DLQ_URL> <LAMBDA_FUNCTION_NAME> [MAX_MESSAGES]"
  exit 1
fi

echo "Reprocessing up to ${MAX_MESSAGES} messages from DLQ..."

SUCCESS=0
FAILED=0

for i in $(seq 1 ${MAX_MESSAGES}); do
  MESSAGE=$(aws sqs receive-message \
    --queue-url ${DLQ_URL} \
    --max-number-of-messages 1 \
    --visibility-timeout 300 \
    --output json)

  if [ "$(echo ${MESSAGE} | jq '.Messages | length')" -eq "0" ]; then
    echo "No more messages in DLQ"
    break
  fi

  BODY=$(echo ${MESSAGE} | jq -r '.Messages[0].Body')
  RECEIPT_HANDLE=$(echo ${MESSAGE} | jq -r '.Messages[0].ReceiptHandle')

  echo "Processing message $i..."

  RESPONSE=$(aws lambda invoke \
    --function-name ${LAMBDA_FUNCTION} \
    --payload "${BODY}" \
    --output json \
    /dev/stdout 2>&1)

  if echo ${RESPONSE} | jq -e '.StatusCode == 200' > /dev/null; then
    aws sqs delete-message \
      --queue-url ${DLQ_URL} \
      --receipt-handle "${RECEIPT_HANDLE}"

    echo "✓ Message $i processed successfully"
    ((SUCCESS++))
  else
    echo "✗ Message $i failed to process"
    ((FAILED++))
  fi

  sleep 1
done

echo ""
echo "Reprocessing complete: Success: ${SUCCESS}, Failed: ${FAILED}"
```

**Usage:**
```bash
chmod +x reprocess_dlq.sh

# Reprocess invoice processor DLQ
./reprocess_dlq.sh \
  $(terraform output -raw dlq_urls | jq -r '.invoice_processor') \
  $(terraform output -raw lambda_function_names | jq -r '.invoice_processor') \
  10
```

### Root Cause Analysis

When messages appear in DLQ:

1. **Check Lambda logs:**
```bash
aws logs tail /aws/lambda/dev-freight-audit-agent-invoice-processor \
  --since 1h \
  --filter-pattern "ERROR"
```

2. **Check for throttling:**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value=dev-freight-audit-agent-invoice-processor \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Common Issues and Solutions

| Issue | Solution | Status |
|-------|----------|--------|
| Bedrock API throttling | Implement exponential backoff, request quota increase | Manual |
| GVP API timeout | Increase Lambda timeout, check GVP API status | Auto-retry |
| Memory errors | Increase Lambda memory size in variables.tf | Manual |
| IAM permission denied | Review and update IAM policies in iam.tf | Manual |
| Malformed data | Fix blueprint schema, redeploy blueprint_manager | Manual |
| BOLNumber exceeds 20 chars | ✅ **Fixed**: Automatically truncated to 20 characters | Auto-handled |
| Multiple ServiceDates | ✅ **Fixed**: First date automatically selected | Auto-handled |
| Lambda returns statusCode 500 | ✅ **Fixed**: Now re-raises exceptions for retries | Auto-retry |

### Best Practices

1. **Monitor DLQ depth daily** - Check CloudWatch Dashboard
2. **Investigate root cause first** - Fix underlying issues before reprocessing
3. **Process messages promptly** - Messages expire after retention period (7-14 days)
4. **Archive critical messages** - Save before deleting for audit trail
5. **Document recurring issues** - Create runbooks for common scenarios

## Configuration Updates

### Update Lambda Code

After modifying Lambda function code:

```bash
cd terraform
terraform apply -var-file="environments/dev.tfvars"
```

Terraform will detect the code changes (via `source_code_hash`) and update the Lambda functions automatically.

### Update Environment Variables

Modify `variables.tf` or your `.tfvars` file, then:

```bash
terraform apply -var-file="environments/dev.tfvars"
```

### Update Secrets in SSM Parameter Store

To rotate secrets without running Terraform:

```bash
# Update Azure client secret
aws ssm put-parameter \
  --name "/dev/freight-audit-agent/azure-client-secret" \
  --value "new-secret-value" \
  --type SecureString \
  --overwrite

# Lambda functions will pick up the new value on next invocation
```

### Update EventBridge Scheduler Schedule

Edit `email_poll_schedule` in your `.tfvars` file:

```hcl
# Every 10 minutes instead of 5
email_poll_schedule = "cron(*/10 8-18 ? * MON-FRI *)"
```

Then apply:
```bash
terraform apply -var-file="environments/dev.tfvars"
```

## Troubleshooting

### Lambda Function Errors

1. **Check logs**:
   ```bash
   aws logs tail /aws/lambda/dev-freight-audit-agent-email-poller --follow
   ```

2. **Test manually**:
   ```bash
   aws lambda invoke \
     --function-name dev-freight-audit-agent-email-poller \
     --log-type Tail \
     --payload '{}' \
     response.json
   ```

3. **Check IAM permissions**:
   ```bash
   aws lambda get-function --function-name dev-freight-audit-agent-email-poller
   ```

### EventBridge Not Triggering Lambda

1. **Check EventBridge rule is enabled**:
   ```bash
   aws events describe-rule --name dev-freight-audit-agent-scheduler-to-poller
   ```

2. **Check Lambda permissions**:
   ```bash
   aws lambda get-policy --function-name dev-freight-audit-agent-email-poller
   ```

3. **Monitor EventBridge invocations**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Events \
     --metric-name TriggeredRules \
     --dimensions Name=RuleName,Value=dev-freight-audit-agent-scheduler-to-poller \
     --start-time 2025-01-01T00:00:00Z \
     --end-time 2025-01-02T00:00:00Z \
     --period 300 \
     --statistics Sum
   ```

### S3 Events Not Triggering Bedrock Processor

1. **Check S3 EventBridge is enabled**:
   ```bash
   BUCKET_NAME=$(terraform output -raw s3_bucket_name)
   aws s3api get-bucket-notification-configuration --bucket ${BUCKET_NAME}
   ```
   Should show: `"EventBridgeConfiguration": {}`

2. **Test S3 upload manually**:
   ```bash
   BUCKET_NAME=$(terraform output -raw s3_bucket_name)
   INVOICE_PREFIX=$(terraform output -raw invoice_s3_prefix)

   echo "test" > test.pdf
   aws s3 cp test.pdf s3://${BUCKET_NAME}/${INVOICE_PREFIX}test.pdf
   ```

3. **Check EventBridge rule pattern**:
   ```bash
   aws events describe-rule --name dev-freight-audit-agent-s3-to-processor
   ```

### Terraform State Issues

If you encounter state lock issues:

```bash
# List locks
aws dynamodb scan --table-name terraform-state-lock

# Force unlock (use with caution!)
terraform force-unlock <LOCK_ID>
```

## Cost Estimation

Approximate monthly costs (dev environment, 10 invoices/day):

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Lambda | ~4,500 invocations, 512MB, 30s avg | $0.50 |
| S3 | 300 objects, 100MB storage | $0.02 |
| SQS (DLQs) | Minimal usage (only failures) | $0.00 |
| EventBridge | 4,500 events | $0.05 |
| Bedrock Data Automation | 300 pages processed | $30.00 |
| CloudWatch Logs | 1GB ingestion, 30-day retention | $1.50 |
| CloudWatch Metrics | Custom metrics | $0.30 |
| **Total** | | **~$32.40/month** |

Production costs will scale with invoice volume.

## Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy -var-file="environments/dev.tfvars"
```

**WARNING**: This will:
- Delete all Lambda functions
- Delete S3 bucket (if created by Terraform, must be empty first)
- Delete SQS Dead Letter Queues (must be empty first)
- Delete CloudWatch logs
- Remove SSM parameters (secrets)
- Remove all IAM roles

**Note**: If you used an existing bucket (`use_existing_bucket = true`), the bucket will NOT be deleted.

To empty S3 bucket and DLQs before destroying:
```bash
# Get bucket name from Terraform output
BUCKET_NAME=$(terraform output -raw s3_bucket_name)

# Empty S3 bucket (both prefixes)
aws s3 rm s3://${BUCKET_NAME}/freight-audit-agent-invoices/ --recursive
aws s3 rm s3://${BUCKET_NAME}/freight-audit-agent-output/ --recursive

# Empty DLQs (purge all messages)
aws sqs purge-queue --queue-url $(terraform output -raw dlq_urls | jq -r '.email_poller')
aws sqs purge-queue --queue-url $(terraform output -raw dlq_urls | jq -r '.invoice_processor')
aws sqs purge-queue --queue-url $(terraform output -raw dlq_urls | jq -r '.gvp_publisher')
aws sqs purge-queue --queue-url $(terraform output -raw reprocessing_queue_url)
```

## File Structure

```
terraform/
├── README.md                    # This file
├── versions.tf                  # Terraform and provider versions
├── variables.tf                 # Input variable definitions
├── locals.tf                    # Local values and computed names
├── data.tf                      # Data sources
├── outputs.tf                   # Output values
├── lambda.tf                    # Lambda function resources
├── eventbridge.tf               # EventBridge scheduler and rules
├── s3.tf                        # S3 bucket resources
├── sqs.tf                       # SQS Dead Letter Queues
├── iam.tf                       # IAM roles and policies
├── ssm.tf                       # SSM Parameter Store secrets
├── cloudwatch.tf                # CloudWatch logs, alarms, dashboard
├── bedrock.tf                   # Bedrock configuration notes
├── terraform.tfvars.example     # Example variables file
├── .gitignore                   # Git ignore patterns
├── builds/                      # Lambda ZIP files (generated)
└── environments/
    ├── dev.tfvars               # Dev environment variables
    └── prod.tfvars              # Prod environment variables
```

## Additional Resources

- [CLAUDE.md](../CLAUDE.md) - Project overview and development guide
- [Lambda Functions README](../lambda_functions/invoice_email_poller/README.md) - Microsoft 365 setup
- [Postman Collection](../gvp_api.postman_collection.json) - GVP API testing

## Support

For issues or questions:
1. Check CloudWatch Logs with correlation ID
2. Check Dead Letter Queues for failed events
3. Review Terraform plan output
4. Verify IAM permissions
5. Check EventBridge rule patterns
6. Test Lambda functions manually
