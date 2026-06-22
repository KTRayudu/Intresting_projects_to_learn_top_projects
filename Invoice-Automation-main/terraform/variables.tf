variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "freight-audit-agent"
}

variable "cost_center" {
  description = "Cost center tag for billing"
  type        = string
  default     = "freight-operations"
}

# Microsoft 365 Configuration
variable "azure_client_id" {
  description = "Azure AD application client ID"
  type        = string
  sensitive   = true
}

variable "azure_client_secret" {
  description = "Azure AD application client secret"
  type        = string
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
  sensitive   = true
}

variable "mailbox_email" {
  description = "Email address to monitor for invoices"
  type        = string
}

# GVP API Configuration
variable "gvp_login_id" {
  description = "GVP API login ID"
  type        = string
  default     = "novaadmin"
}

variable "gvp_password" {
  description = "GVP API password"
  type        = string
  sensitive   = true
}

variable "gvp_auth_url" {
  description = "GVP authentication URL (defaults to QA environment)"
  type        = string
  default     = "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken"
}

variable "gvp_api_url" {
  description = "GVP API endpoint URL (defaults to QA environment)"
  type        = string
  default     = "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"
}

# Bedrock Configuration
variable "blueprint_name" {
  description = "Bedrock blueprint name"
  type        = string
  default     = "freight-invoice-blueprint"
}

variable "bedrock_project_name" {
  description = "Bedrock project name"
  type        = string
  default     = "Freight_Audit_Agent"
}

# Lambda Configuration
variable "lambda_runtime" {
  description = "Lambda runtime version"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

# Scheduler Configuration
variable "email_poll_schedule" {
  description = "Cron expression for email polling (every 5 min, business hours)"
  type        = string
  default     = "cron(*/5 8-18 ? * MON-FRI *)"
}

variable "schedule_timezone" {
  description = "Timezone for scheduler"
  type        = string
  default     = "America/New_York"
}

# S3 Configuration
variable "use_existing_bucket" {
  description = "Whether to use an existing S3 bucket instead of creating a new one"
  type        = bool
  default     = false
}

variable "existing_bucket_name" {
  description = "Name of existing S3 bucket (e.g., prodgvpfilestore1). Only used if use_existing_bucket is true"
  type        = string
  default     = ""
}

variable "invoice_s3_prefix" {
  description = "S3 prefix for invoice PDFs within the bucket"
  type        = string
  default     = "freight-audit-agent-invoices/"
}

variable "output_s3_prefix" {
  description = "S3 prefix for Bedrock structured output within the bucket"
  type        = string
  default     = "freight-audit-agent-output/"
}

# CloudWatch Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing for Lambda functions"
  type        = bool
  default     = true
}

# Alerting Configuration
variable "alert_email" {
  description = "Email address for CloudWatch alarms"
  type        = string
  default     = ""
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}
