# =============================================================================
# Lambda Layers
# =============================================================================

# -----------------------------------------------------------------------------
# AWS Powertools Layer (AWS-managed)
# -----------------------------------------------------------------------------
# Reference the AWS-managed Lambda Powertools layer using ARN
# Published by AWS account 017000801446 for all regions
# https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer
#
# ARN Format: arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python311-x86_64:{version}
# Latest version as of 2025-12: version 16
# Check latest: https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer

locals {
  # AWS Powertools Layer ARN - update version as needed
  powertools_layer_arn = "arn:aws:lambda:${var.aws_region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python311-x86_64:16"
}

# -----------------------------------------------------------------------------
# Custom MSAL + Requests Layer
# -----------------------------------------------------------------------------
# This layer provides msal and requests libraries for Microsoft Graph API integration
resource "aws_lambda_layer_version" "msal_requests" {
  filename            = "${path.module}/../lambda_layers/msal_requests_layer.zip"
  layer_name          = "${var.environment}-msal-requests-layer"
  description         = "MSAL and requests libraries for Microsoft Graph API integration"
  compatible_runtimes = ["python3.11"]

  # This will force recreation when the zip file changes
  source_code_hash = filebase64sha256("${path.module}/../lambda_layers/msal_requests_layer.zip")
}
