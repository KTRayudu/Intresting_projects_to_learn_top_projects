output "lambda_function_arns" {
  description = "ARNs of Lambda functions"
  value = {
    email_poller      = aws_lambda_function.email_poller.arn
    blueprint_manager = aws_lambda_function.blueprint_manager.arn
    invoice_processor = aws_lambda_function.invoice_processor.arn
    gvp_publisher     = aws_lambda_function.gvp_publisher.arn
  }
}

output "lambda_function_names" {
  description = "Names of Lambda functions"
  value = {
    email_poller      = aws_lambda_function.email_poller.function_name
    blueprint_manager = aws_lambda_function.blueprint_manager.function_name
    invoice_processor = aws_lambda_function.invoice_processor.function_name
    gvp_publisher     = aws_lambda_function.gvp_publisher.function_name
  }
}

output "s3_bucket_name" {
  description = "S3 bucket name for invoices and output"
  value       = local.s3_bucket_name
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = var.use_existing_bucket ? data.aws_s3_bucket.existing[0].arn : aws_s3_bucket.storage[0].arn
}

output "invoice_s3_prefix" {
  description = "S3 prefix for invoice PDFs"
  value       = var.invoice_s3_prefix
}

output "output_s3_prefix" {
  description = "S3 prefix for Bedrock output"
  value       = var.output_s3_prefix
}

output "eventbridge_scheduler_arn" {
  description = "EventBridge Scheduler ARN"
  value       = aws_scheduler_schedule.email_poller.arn
}

output "eventbridge_rule_arns" {
  description = "EventBridge Rule ARNs"
  value = {
    scheduler_to_poller   = aws_cloudwatch_event_rule.scheduler_to_poller.arn
    s3_to_processor       = aws_cloudwatch_event_rule.s3_to_processor.arn
    bedrock_to_publisher  = aws_cloudwatch_event_rule.bedrock_to_publisher.arn
  }
}

output "ssm_parameter_names" {
  description = "SSM parameter names (secrets)"
  value = {
    azure_client_id     = aws_ssm_parameter.azure_client_id.name
    azure_client_secret = aws_ssm_parameter.azure_client_secret.name
    azure_tenant_id     = aws_ssm_parameter.azure_tenant_id.name
    gvp_password        = aws_ssm_parameter.gvp_password.name
  }
}

output "cloudwatch_log_groups" {
  description = "CloudWatch Log Group names"
  value = {
    email_poller      = aws_cloudwatch_log_group.email_poller.name
    blueprint_manager = aws_cloudwatch_log_group.blueprint_manager.name
    invoice_processor = aws_cloudwatch_log_group.invoice_processor.name
    gvp_publisher     = aws_cloudwatch_log_group.gvp_publisher.name
  }
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = var.enable_alarms ? aws_sns_topic.alerts[0].arn : null
}

output "bedrock_project_name" {
  description = "Bedrock Data Automation project name"
  value       = var.bedrock_project_name
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "region" {
  description = "AWS region"
  value       = var.aws_region
}

output "dlq_urls" {
  description = "Dead Letter Queue URLs"
  value = {
    email_poller      = aws_sqs_queue.email_poller_dlq.url
    invoice_processor = aws_sqs_queue.invoice_processor_dlq.url
    gvp_publisher     = aws_sqs_queue.gvp_publisher_dlq.url
  }
}

output "dlq_arns" {
  description = "Dead Letter Queue ARNs"
  value = {
    email_poller      = aws_sqs_queue.email_poller_dlq.arn
    invoice_processor = aws_sqs_queue.invoice_processor_dlq.arn
    gvp_publisher     = aws_sqs_queue.gvp_publisher_dlq.arn
  }
}

output "reprocessing_queue_url" {
  description = "Reprocessing queue URL for manual retries"
  value       = aws_sqs_queue.reprocessing_queue.url
}
