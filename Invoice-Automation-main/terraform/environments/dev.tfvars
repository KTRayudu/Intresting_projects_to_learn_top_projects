# Development Environment Variables
environment = "dev"
aws_region  = "us-east-1"
cost_center = "freight-operations"

# Lambda Configuration
lambda_runtime     = "python3.11"
lambda_timeout     = 300
lambda_memory_size = 512

# Bedrock Configuration
blueprint_name       = "freight-invoice-blueprint"
bedrock_project_name = "Freight_Audit_Agent"

# Scheduler Configuration - Every 5 minutes during business hours
email_poll_schedule = "cron(*/5 8-18 ? * MON-FRI *)"
schedule_timezone   = "America/New_York"

# S3 Configuration
# Option 1: Create new bucket (default)
use_existing_bucket  = false
invoice_s3_prefix    = "freight-audit-agent-invoices/"
output_s3_prefix     = "freight-audit-agent-output/"

# Option 2: Use existing bucket (uncomment to use)
# use_existing_bucket   = true
# existing_bucket_name  = "devgvpbucket1"
# invoice_s3_prefix     = "freight-audit-agent-invoices/"
# output_s3_prefix      = "freight-audit-agent-output/"

# GVP API Configuration (QA Environment)
gvp_login_id = "novaadmin"
gvp_auth_url = "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
gvp_api_url  = "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"

# CloudWatch Configuration
log_retention_days = 30

# Alerting Configuration
enable_alarms = true

# Secrets - These should be set via environment variables or AWS SSM
# Required secrets (set via environment variables):
# export TF_VAR_azure_client_id="your-azure-client-id"
# export TF_VAR_azure_client_secret="your-azure-client-secret"
# export TF_VAR_azure_tenant_id="your-azure-tenant-id"
# export TF_VAR_mailbox_email="invoices@yourcompany.com"
# export TF_VAR_gvp_password="your-gvp-password"
# export TF_VAR_alert_email="ops-team@yourcompany.com"
