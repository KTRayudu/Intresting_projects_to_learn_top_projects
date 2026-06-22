# =============================================================================
# EventBridge Scheduler and Rules
# =============================================================================

# -----------------------------------------------------------------------------
# EventBridge Scheduler - Triggers email poller every 5 minutes
# -----------------------------------------------------------------------------
resource "aws_scheduler_schedule" "email_poller" {
  name = local.scheduler_name

  description = "Triggers invoice email poller Lambda every 5 minutes during business hours"

  schedule_expression          = var.email_poll_schedule
  schedule_expression_timezone = var.schedule_timezone

  flexible_time_window {
    mode                      = "FLEXIBLE"
    maximum_window_in_minutes = 2
  }

  target {
    arn      = "arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:event-bus/default"
    role_arn = aws_iam_role.scheduler_role.arn

    eventbridge_parameters {
      detail_type = "Scheduled Invoice Poll"
      source      = "custom.freight-audit"
    }

    retry_policy {
      maximum_retry_attempts       = 2
      maximum_event_age_in_seconds = 900
    }
  }

  state = "ENABLED"
}

# -----------------------------------------------------------------------------
# EventBridge Rule #1: Scheduler → Email Poller Lambda
# Matches events from EventBridge Scheduler
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "scheduler_to_poller" {
  name        = local.eventbridge_rules.scheduler_to_poller
  description = "Trigger email poller Lambda from EventBridge Scheduler"

  event_pattern = jsonencode({
    source      = ["custom.freight-audit"]
    detail-type = ["Scheduled Invoice Poll"]
  })

  state = "ENABLED"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "email_poller" {
  rule      = aws_cloudwatch_event_rule.scheduler_to_poller.name
  target_id = "EmailPollerLambda"
  arn       = aws_lambda_function.email_poller.arn

  retry_policy {
    maximum_retry_attempts       = 2
    maximum_event_age_in_seconds = 900
  }

  dead_letter_config {
    arn = aws_sqs_queue.email_poller_dlq.arn
  }
}

# -----------------------------------------------------------------------------
# EventBridge Rule #2: S3 Upload → Invoice Processor Lambda
# Matches S3 ObjectCreated events from EventBridge S3 notifications
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "s3_to_processor" {
  name        = local.eventbridge_rules.s3_to_processor
  description = "Trigger invoice processor Lambda on S3 invoice upload"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [local.s3_bucket_name]
      }
      object = {
        key = [{
          prefix = var.invoice_s3_prefix
        }]
      }
    }
  })

  state = "ENABLED"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "invoice_processor" {
  rule      = aws_cloudwatch_event_rule.s3_to_processor.name
  target_id = "InvoiceProcessorLambda"
  arn       = aws_lambda_function.invoice_processor.arn

  retry_policy {
    maximum_retry_attempts       = 2
    maximum_event_age_in_seconds = 3600
  }

  dead_letter_config {
    arn = aws_sqs_queue.invoice_processor_dlq.arn
  }
}

# -----------------------------------------------------------------------------
# EventBridge Rule #3: Bedrock Completion → GVP Publisher Lambda
# Matches Bedrock Data Automation async job completion events
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "bedrock_to_publisher" {
  name        = local.eventbridge_rules.bedrock_to_publisher
  description = "Trigger GVP publisher Lambda on Bedrock job completion"

  event_pattern = jsonencode({
    source      = ["aws.bedrock"]
    detail-type = ["Bedrock Data Automation Job Succeeded"]
  })

  state = "ENABLED"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "gvp_publisher" {
  rule      = aws_cloudwatch_event_rule.bedrock_to_publisher.name
  target_id = "GVPPublisherLambda"
  arn       = aws_lambda_function.gvp_publisher.arn

  retry_policy {
    maximum_retry_attempts       = 2
    maximum_event_age_in_seconds = 3600
  }

  dead_letter_config {
    arn = aws_sqs_queue.gvp_publisher_dlq.arn
  }
}
