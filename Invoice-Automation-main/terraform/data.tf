# Get current AWS account ID and caller identity
# Calls AWS API: sts:GetCallerIdentity
# Returns: account_id, user_id, arn
# Used throughout the configuration for dynamic account ID in policies
# Example usage: data.aws_caller_identity.current.account_id
data "aws_caller_identity" "current" {}

# Get current AWS region
# Returns the region where Terraform is deploying resources
data "aws_region" "current" {}

# Archive Lambda function source code
data "archive_file" "email_poller" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_functions/invoice_email_poller"
  output_path = "${path.module}/builds/email_poller.zip"
  excludes    = ["__pycache__", "*.pyc", "*.md", "test_*"]
}

data "archive_file" "blueprint_manager" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_functions/bedrock_blueprint_manager"
  output_path = "${path.module}/builds/blueprint_manager.zip"
  excludes    = ["__pycache__", "*.pyc", "test_*"]
}

data "archive_file" "invoice_processor" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_functions/bedrock_invoice_processor"
  output_path = "${path.module}/builds/invoice_processor.zip"
  excludes    = ["__pycache__", "*.pyc", "test_*"]
}

data "archive_file" "gvp_publisher" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_functions/gvp_invoice_publisher"
  output_path = "${path.module}/builds/gvp_publisher.zip"
  excludes    = ["__pycache__", "*.pyc", "test_*"]
}

data "archive_file" "dlq_processor" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_functions/dlq_processor"
  output_path = "${path.module}/builds/dlq_processor.zip"
  excludes    = ["__pycache__", "*.pyc", "test_*"]
}

# Reference SSM parameters (created separately)
data "aws_ssm_parameter" "azure_client_id" {
  name            = local.ssm_parameters.azure_client_id
  with_decryption = true
  depends_on      = [aws_ssm_parameter.azure_client_id]
}

data "aws_ssm_parameter" "azure_client_secret" {
  name            = local.ssm_parameters.azure_client_secret
  with_decryption = true
  depends_on      = [aws_ssm_parameter.azure_client_secret]
}

data "aws_ssm_parameter" "azure_tenant_id" {
  name            = local.ssm_parameters.azure_tenant_id
  with_decryption = true
  depends_on      = [aws_ssm_parameter.azure_tenant_id]
}

data "aws_ssm_parameter" "gvp_password" {
  name            = local.ssm_parameters.gvp_password
  with_decryption = true
  depends_on      = [aws_ssm_parameter.gvp_password]
}
