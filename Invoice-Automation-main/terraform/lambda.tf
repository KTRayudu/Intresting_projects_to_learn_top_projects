# =============================================================================
# Lambda Functions
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Email Poller Lambda - Polls M365 mailbox for invoice emails
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "email_poller" {
  filename         = data.archive_file.email_poller.output_path
  source_code_hash = data.archive_file.email_poller.output_base64sha256

  function_name = local.lambda_functions.email_poller
  role          = aws_iam_role.email_poller_role.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Lambda layers for dependencies
  layers = [
    local.powertools_layer_arn,
    aws_lambda_layer_version.msal_requests.arn
  ]

  environment {
    variables = {
      AZURE_CLIENT_ID     = data.aws_ssm_parameter.azure_client_id.value
      AZURE_CLIENT_SECRET = data.aws_ssm_parameter.azure_client_secret.value
      AZURE_TENANT_ID     = data.aws_ssm_parameter.azure_tenant_id.value
      MAILBOX_EMAIL       = var.mailbox_email
      S3_BUCKET           = local.s3_bucket_name
      S3_PREFIX           = var.invoice_s3_prefix
      POWERTOOLS_SERVICE_NAME   = "invoice_email_poller"
      POWERTOOLS_METRICS_NAMESPACE = "FreightAuditAgent"
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.email_poller,
    aws_iam_role_policy_attachment.email_poller_basic,
    aws_iam_role_policy_attachment.email_poller_s3,
    aws_iam_role_policy_attachment.email_poller_ssm,
  ]

  tags = merge(local.common_tags, {
    Name = local.lambda_functions.email_poller
  })
}

# -----------------------------------------------------------------------------
# 2. Blueprint Manager Lambda - Manages Bedrock blueprints/projects
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "blueprint_manager" {
  filename         = data.archive_file.blueprint_manager.output_path
  source_code_hash = data.archive_file.blueprint_manager.output_base64sha256

  function_name = local.lambda_functions.blueprint_manager
  role          = aws_iam_role.blueprint_manager_role.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Lambda layers for dependencies
  layers = [
    local.powertools_layer_arn
  ]

  environment {
    variables = {
      BLUEPRINT_NAME  = var.blueprint_name
      BLUEPRINT_FILE  = "bedrock_invoice_blueprint.json"
      PROJECT_NAME    = var.bedrock_project_name
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.blueprint_manager,
    aws_iam_role_policy_attachment.blueprint_manager_basic,
    aws_iam_role_policy_attachment.blueprint_manager_bedrock,
  ]

  tags = merge(local.common_tags, {
    Name = local.lambda_functions.blueprint_manager
  })
}

# -----------------------------------------------------------------------------
# 3. Invoice Processor Lambda - Triggers Bedrock Data Automation jobs
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "invoice_processor" {
  filename         = data.archive_file.invoice_processor.output_path
  source_code_hash = data.archive_file.invoice_processor.output_base64sha256

  function_name = local.lambda_functions.invoice_processor
  role          = aws_iam_role.invoice_processor_role.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Lambda layers for dependencies
  layers = [
    local.powertools_layer_arn
  ]

  environment {
    variables = {
      PROJECT_NAME                 = var.bedrock_project_name
      DATA_AUTOMATION_PROFILE_ARN  = local.bedrock_profile_arn
      OUTPUT_BUCKET                = local.s3_bucket_name
      OUTPUT_PREFIX                = var.output_s3_prefix
      POWERTOOLS_SERVICE_NAME      = "bedrock_invoice_processor"
      POWERTOOLS_METRICS_NAMESPACE = "FreightAuditAgent"
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.invoice_processor,
    aws_iam_role_policy_attachment.invoice_processor_basic,
    aws_iam_role_policy_attachment.invoice_processor_s3,
    aws_iam_role_policy_attachment.invoice_processor_bedrock,
  ]

  tags = merge(local.common_tags, {
    Name = local.lambda_functions.invoice_processor
  })
}

# -----------------------------------------------------------------------------
# 4. GVP Publisher Lambda - Posts extracted data to GVP/Oracle API
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "gvp_publisher" {
  filename         = data.archive_file.gvp_publisher.output_path
  source_code_hash = data.archive_file.gvp_publisher.output_base64sha256

  function_name = local.lambda_functions.gvp_publisher
  role          = aws_iam_role.gvp_publisher_role.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Lambda layers for dependencies
  layers = [
    local.powertools_layer_arn,
    aws_lambda_layer_version.msal_requests.arn
  ]

  environment {
    variables = {
      GVP_LOGIN_ID    = var.gvp_login_id
      GVP_PASSWORD    = data.aws_ssm_parameter.gvp_password.value
      GVP_AUTH_URL    = var.gvp_auth_url
      GVP_API_URL     = var.gvp_api_url
      BLUEPRINT_NAME  = var.blueprint_name
      BLUEPRINT_FILE  = "bedrock_invoice_blueprint.json"
      PROJECT_NAME    = var.bedrock_project_name
      DOC_TYPE        = "invoices"
      POWERTOOLS_SERVICE_NAME      = "gvp_invoice_publisher"
      POWERTOOLS_METRICS_NAMESPACE = "FreightAuditAgent"
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.gvp_publisher,
    aws_iam_role_policy_attachment.gvp_publisher_basic,
    aws_iam_role_policy_attachment.gvp_publisher_s3,
    aws_iam_role_policy_attachment.gvp_publisher_ssm,
  ]

  tags = merge(local.common_tags, {
    Name = local.lambda_functions.gvp_publisher
  })
}

# -----------------------------------------------------------------------------
# Lambda Permissions for EventBridge to invoke functions
# -----------------------------------------------------------------------------

# Email Poller - Invoked by EventBridge Rule (from Scheduler)
resource "aws_lambda_permission" "email_poller_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.email_poller.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduler_to_poller.arn
}

# Invoice Processor - Invoked by EventBridge Rule (from S3)
resource "aws_lambda_permission" "invoice_processor_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.invoice_processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.s3_to_processor.arn
}

# GVP Publisher - Invoked by EventBridge Rule (from Bedrock)
resource "aws_lambda_permission" "gvp_publisher_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gvp_publisher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.bedrock_to_publisher.arn
}

# -----------------------------------------------------------------------------
# Lambda Async Invoke Configuration (for DLQ on execution failures)
# -----------------------------------------------------------------------------

# GVP Publisher - Configure async invoke with DLQ for Lambda execution failures
resource "aws_lambda_function_event_invoke_config" "gvp_publisher" {
  function_name = aws_lambda_function.gvp_publisher.function_name

  # Maximum age of event before discarding (same as EventBridge)
  maximum_event_age_in_seconds = 3600

  # Retry attempts - set to 0 since EventBridge handles retries
  # EventBridge will retry (MaximumRetryAttempts=1), then send to Lambda DLQ
  maximum_retry_attempts = 0

  # Lambda DLQ - failures go here after EventBridge retries
  destination_config {
    on_failure {
      destination = aws_sqs_queue.gvp_publisher_dlq.arn
    }
  }
}

# Invoice Processor - Configure async invoke with DLQ
resource "aws_lambda_function_event_invoke_config" "invoice_processor" {
  function_name = aws_lambda_function.invoice_processor.function_name

  maximum_event_age_in_seconds = 3600
  maximum_retry_attempts       = 0

  destination_config {
    on_failure {
      destination = aws_sqs_queue.invoice_processor_dlq.arn
    }
  }
}

# Email Poller - Configure async invoke with DLQ
resource "aws_lambda_function_event_invoke_config" "email_poller" {
  function_name = aws_lambda_function.email_poller.function_name

  maximum_event_age_in_seconds = 900
  maximum_retry_attempts       = 0

  destination_config {
    on_failure {
      destination = aws_sqs_queue.email_poller_dlq.arn
    }
  }
}

# -----------------------------------------------------------------------------
# 5. DLQ Processor Lambda - Processes DLQ messages and sends detailed alerts
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "dlq_processor" {
  filename         = data.archive_file.dlq_processor.output_path
  source_code_hash = data.archive_file.dlq_processor.output_base64sha256

  function_name = local.lambda_functions.dlq_processor
  role          = aws_iam_role.dlq_processor_role.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = 60  # DLQ processing should be quick
  memory_size   = 256

  # Lambda layers for dependencies
  layers = [
    local.powertools_layer_arn
  ]

  environment {
    variables = {
      SNS_INVOICE_ERROR_TOPIC_ARN  = aws_sns_topic.invoice_errors.arn
      POWERTOOLS_SERVICE_NAME      = "dlq_processor"
      POWERTOOLS_METRICS_NAMESPACE = "FreightAuditAgent"
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.dlq_processor,
    aws_iam_role_policy_attachment.dlq_processor_basic,
    aws_iam_role_policy_attachment.dlq_processor_s3,
    aws_iam_role_policy_attachment.dlq_processor_sns,
  ]

  tags = merge(local.common_tags, {
    Name = local.lambda_functions.dlq_processor
  })
}
