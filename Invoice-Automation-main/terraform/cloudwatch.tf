# =============================================================================
# CloudWatch Log Groups and Alarms
# =============================================================================

# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "email_poller" {
  name              = "/aws/lambda/${local.lambda_functions.email_poller}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Lambda = local.lambda_functions.email_poller
  })
}

resource "aws_cloudwatch_log_group" "blueprint_manager" {
  name              = "/aws/lambda/${local.lambda_functions.blueprint_manager}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Lambda = local.lambda_functions.blueprint_manager
  })
}

resource "aws_cloudwatch_log_group" "invoice_processor" {
  name              = "/aws/lambda/${local.lambda_functions.invoice_processor}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Lambda = local.lambda_functions.invoice_processor
  })
}

resource "aws_cloudwatch_log_group" "gvp_publisher" {
  name              = "/aws/lambda/${local.lambda_functions.gvp_publisher}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Lambda = local.lambda_functions.gvp_publisher
  })
}

resource "aws_cloudwatch_log_group" "dlq_processor" {
  name              = "/aws/lambda/${local.lambda_functions.dlq_processor}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Lambda = local.lambda_functions.dlq_processor
  })
}

# -----------------------------------------------------------------------------
# SNS Topics
# -----------------------------------------------------------------------------

# SNS topic for invoice-level error alerts (sent by DLQ Processor Lambda)
# This topic receives detailed alerts when invoices fail after all retries
resource "aws_sns_topic" "invoice_errors" {
  name = "${local.name_prefix}-invoice-errors"

  tags = merge(local.common_tags, {
    AlertType = "InvoiceError"
  })
}

# Subscribe email to invoice error alerts
resource "aws_sns_topic_subscription" "invoice_errors_email" {
  count = var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.invoice_errors.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# -----------------------------------------------------------------------------
# SNS Topic for General CloudWatch Alarms (optional)
# -----------------------------------------------------------------------------
resource "aws_sns_topic" "alerts" {
  count = var.enable_alarms ? 1 : 0

  name = "${local.name_prefix}-alerts"

  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count = var.enable_alarms && var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms
# -----------------------------------------------------------------------------

# Email Poller Errors
resource "aws_cloudwatch_metric_alarm" "email_poller_errors" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-email-poller-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "Email poller Lambda function errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.email_poller.function_name
  }

  alarm_actions = [aws_sns_topic.alerts[0].arn]

  tags = local.common_tags
}

# Email Poller Throttles
resource "aws_cloudwatch_metric_alarm" "email_poller_throttles" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-email-poller-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Email poller Lambda function throttles"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.email_poller.function_name
  }

  alarm_actions = [aws_sns_topic.alerts[0].arn]

  tags = local.common_tags
}

# Invoice Processor Errors
resource "aws_cloudwatch_metric_alarm" "invoice_processor_errors" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-invoice-processor-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "Invoice processor Lambda function errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.invoice_processor.function_name
  }

  alarm_actions = [aws_sns_topic.alerts[0].arn]

  tags = local.common_tags
}

# GVP Publisher Errors
resource "aws_cloudwatch_metric_alarm" "gvp_publisher_errors" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-gvp-publisher-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "GVP publisher Lambda function errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.gvp_publisher.function_name
  }

  alarm_actions = [aws_sns_topic.alerts[0].arn]

  tags = local.common_tags
}

# Custom Metric: GVP Posts Failed (from Lambda Powertools)
resource "aws_cloudwatch_metric_alarm" "gvp_posts_failed" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-gvp-posts-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "GVPPostsFailed"
  namespace           = "FreightAuditAgent"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "GVP invoice publishing failures"
  treat_missing_data  = "notBreaching"

  dimensions = {
    service = "gvp_invoice_publisher"
  }

  alarm_actions = [aws_sns_topic.alerts[0].arn]

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Dead Letter Queue Alarms
# -----------------------------------------------------------------------------
# NOTE: DLQ alarms are DISABLED to prevent duplicate alerts
# The DLQ Processor Lambda already sends detailed email alerts via SNS when
# messages arrive in DLQ (via SQS event source mapping). These CloudWatch
# alarms would create generic duplicate alerts without invoice details.
# Keep DLQ alerting centralized in the DLQ Processor Lambda.

# Invoice Processor DLQ Alarm (DISABLED - DLQ Processor Lambda handles alerts)
# resource "aws_cloudwatch_metric_alarm" "invoice_processor_dlq" {
#   count = var.enable_alarms ? 1 : 0
#
#   alarm_name          = "${local.name_prefix}-invoice-processor-dlq"
#   comparison_operator = "GreaterThanThreshold"
#   evaluation_periods  = 1
#   metric_name         = "ApproximateNumberOfMessagesVisible"
#   namespace           = "AWS/SQS"
#   period              = 60
#   statistic           = "Average"
#   threshold           = 0
#   alarm_description   = "Invoice processor DLQ has messages - S3 events failed processing"
#   treat_missing_data  = "notBreaching"
#
#   dimensions = {
#     QueueName = aws_sqs_queue.invoice_processor_dlq.name
#   }
#
#   alarm_actions = [aws_sns_topic.alerts[0].arn]
#
#   tags = local.common_tags
# }

# GVP Publisher DLQ Alarm (DISABLED - DLQ Processor Lambda handles alerts)
# resource "aws_cloudwatch_metric_alarm" "gvp_publisher_dlq" {
#   count = var.enable_alarms ? 1 : 0
#
#   alarm_name          = "${local.name_prefix}-gvp-publisher-dlq"
#   comparison_operator = "GreaterThanThreshold"
#   evaluation_periods  = 1
#   metric_name         = "ApproximateNumberOfMessagesVisible"
#   namespace           = "AWS/SQS"
#   period              = 60
#   statistic           = "Average"
#   threshold           = 0
#   alarm_description   = "GVP publisher DLQ has messages - Bedrock events failed publishing"
#   treat_missing_data  = "notBreaching"
#
#   dimensions = {
#     QueueName = aws_sqs_queue.gvp_publisher_dlq.name
#   }
#
#   alarm_actions = [aws_sns_topic.alerts[0].arn]
#
#   tags = local.common_tags
# }

# Email Poller DLQ Alarm (DISABLED - DLQ Processor Lambda handles alerts)
# resource "aws_cloudwatch_metric_alarm" "email_poller_dlq" {
#   count = var.enable_alarms ? 1 : 0
#
#   alarm_name          = "${local.name_prefix}-email-poller-dlq"
#   comparison_operator = "GreaterThanThreshold"
#   evaluation_periods  = 2
#   metric_name         = "ApproximateNumberOfMessagesVisible"
#   namespace           = "AWS/SQS"
#   period              = 300
#   statistic           = "Average"
#   threshold           = 3
#   alarm_description   = "Email poller DLQ has messages - Scheduler events failing"
#   treat_missing_data  = "notBreaching"
#
#   dimensions = {
#     QueueName = aws_sqs_queue.email_poller_dlq.name
#   }
#
#   alarm_actions = [aws_sns_topic.alerts[0].arn]
#
#   tags = local.common_tags
# }

# -----------------------------------------------------------------------------
# CloudWatch Dashboard (optional)
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "freight_audit" {
  dashboard_name = "${local.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", { stat = "Sum", label = "Email Poller Invocations" }],
            ["...", { stat = "Sum", label = "Invoice Processor Invocations" }],
            ["...", { stat = "Sum", label = "GVP Publisher Invocations" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Invocations"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", { stat = "Sum", label = "Email Poller Errors" }],
            ["...", { stat = "Sum", label = "Invoice Processor Errors" }],
            ["...", { stat = "Sum", label = "GVP Publisher Errors" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Errors"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["FreightAuditAgent", "PDFsUploaded", "service", "invoice_email_poller", { stat = "Sum", label = "PDFs Uploaded" }],
            ["...", "BedrockJobsStarted", ".", "bedrock_invoice_processor", { stat = "Sum", label = "Bedrock Jobs Started" }],
            ["...", "GVPPostsSuccessful", ".", "gvp_invoice_publisher", { stat = "Sum", label = "GVP Posts Successful" }],
            ["...", "GVPPostsFailed", ".", ".", { stat = "Sum", label = "GVP Posts Failed" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Pipeline Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["FreightAuditAgent", "EndToEndLatency", "service", "gvp_invoice_publisher", { stat = "Average", label = "Avg E2E Latency (ms)" }],
            [".", ".", ".", ".", { stat = "Maximum", label = "Max E2E Latency (ms)" }]
          ]
          period = 300
          region = var.aws_region
          title  = "End-to-End Latency"
        }
      }
    ]
  })
}
