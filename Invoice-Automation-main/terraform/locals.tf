locals {
  # Common tags applied to all resources
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    CostCenter  = var.cost_center
  }

  # Naming prefix for resources
  name_prefix = "${var.environment}-${var.project_name}"

  # Lambda function names
  lambda_functions = {
    email_poller         = "${local.name_prefix}-email-poller"
    blueprint_manager    = "${local.name_prefix}-blueprint-manager"
    invoice_processor    = "${local.name_prefix}-invoice-processor"
    gvp_publisher        = "${local.name_prefix}-gvp-publisher"
    dlq_processor        = "${local.name_prefix}-dlq-processor"
  }

  # S3 bucket name - use existing bucket or create new one
  # If use_existing_bucket is true, use the provided bucket name
  # Otherwise, create a new bucket with a unique name
  s3_bucket_name = var.use_existing_bucket ? var.existing_bucket_name : "${local.name_prefix}-${data.aws_caller_identity.current.account_id}"

  # S3 bucket ARN - dynamically determined based on whether using existing or new bucket
  s3_bucket_arn = var.use_existing_bucket ? data.aws_s3_bucket.existing[0].arn : aws_s3_bucket.storage[0].arn

  # EventBridge rule names
  eventbridge_rules = {
    scheduler_to_poller = "${local.name_prefix}-scheduler-to-poller"
    s3_to_processor     = "${local.name_prefix}-s3-to-processor"
    bedrock_to_publisher = "${local.name_prefix}-bedrock-to-publisher"
  }

  # EventBridge scheduler name
  scheduler_name = "${local.name_prefix}-email-poller-schedule"

  # SSM parameter paths
  ssm_prefix = "/${var.environment}/${var.project_name}"
  ssm_parameters = {
    azure_client_id     = "${local.ssm_prefix}/azure-client-id"
    azure_client_secret = "${local.ssm_prefix}/azure-client-secret"
    azure_tenant_id     = "${local.ssm_prefix}/azure-tenant-id"
    gvp_password        = "${local.ssm_prefix}/gvp-password"
  }

  # Bedrock Data Automation Profile ARN
  # Uses AWS-managed standard profile identifier, not project name
  bedrock_profile_arn = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:data-automation-profile/us.data-automation-v1"
}
