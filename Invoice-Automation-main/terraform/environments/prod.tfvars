# Production Environment Variables
environment = "prod"
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
# Production: Use existing bucket
use_existing_bucket   = true
existing_bucket_name  = "prodgvpfilestore1"
invoice_s3_prefix     = "freight-audit-agent-invoices/"
output_s3_prefix      = "freight-audit-agent-output/"

# GVP API Configuration (Production Environment)
gvp_login_id = "freighagentapi"
gvp_auth_url = "http://tms.intellitrans.com/SSO/Public/API/Auth/GetToken"
gvp_api_url  = "https://gvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"

# CloudWatch Configuration
log_retention_days = 90

# Alerting Configuration
enable_alarms = true

# Secrets - These should be set via environment variables or AWS SSM
# Required secrets (set via environment variables):
# export TF_VAR_azure_client_id="4b201325-c809-4530-a3c5-34b8b9054e75"
# export TF_VAR_azure_client_secret="bud8Q~7SvzePlMj~lqbodCRl.eniZ~oQYHffwaG5"
# export TF_VAR_azure_tenant_id="66faab94-8581-4b0a-bf07-c234a00927f5"
# export TF_VAR_mailbox_email="FreightAudit@intellitrans.com"
# export TF_VAR_gvp_login_id="freighagentapi"
# export TF_VAR_gvp_password="Go9%?8Qd"
# export TF_VAR_alert_email="freightagentmonitoring@intellitrans.com"
