# =============================================================================
# SQS Dead Letter Queues for Lambda Functions
# =============================================================================

# -----------------------------------------------------------------------------
# DLQ for Invoice Processor Lambda (Critical - captures S3 events)
# -----------------------------------------------------------------------------
resource "aws_sqs_queue" "invoice_processor_dlq" {
  name = "${local.name_prefix}-invoice-processor-dlq"

  # Retain messages for 14 days (maximum)
  message_retention_seconds = 1209600

  # Visibility timeout must be >= Lambda timeout (DLQ processor has 60s timeout)
  visibility_timeout_seconds = 120

  # Enable encryption
  sqs_managed_sse_enabled = true

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-invoice-processor-dlq"
    Description = "Dead letter queue for failed invoice processing events"
  })
}

# DLQ Policy - Allow EventBridge and Lambda to send messages
resource "aws_sqs_queue_policy" "invoice_processor_dlq_policy" {
  queue_url = aws_sqs_queue.invoice_processor_dlq.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEventBridgeSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.invoice_processor_dlq.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_cloudwatch_event_rule.s3_to_processor.arn
          }
        }
      },
      {
        Sid    = "AllowLambdaSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.invoice_processor_dlq.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_lambda_function.invoice_processor.arn
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# DLQ for GVP Publisher Lambda (Critical - captures Bedrock completion events)
# -----------------------------------------------------------------------------
resource "aws_sqs_queue" "gvp_publisher_dlq" {
  name = "${local.name_prefix}-gvp-publisher-dlq"

  # Retain messages for 14 days (maximum)
  message_retention_seconds = 1209600

  # Visibility timeout must be >= Lambda timeout (DLQ processor has 60s timeout)
  visibility_timeout_seconds = 120

  # Enable encryption
  sqs_managed_sse_enabled = true

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-gvp-publisher-dlq"
    Description = "Dead letter queue for failed GVP publishing events"
  })
}

# DLQ Policy - Allow EventBridge and Lambda to send messages
resource "aws_sqs_queue_policy" "gvp_publisher_dlq_policy" {
  queue_url = aws_sqs_queue.gvp_publisher_dlq.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEventBridgeSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.gvp_publisher_dlq.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_cloudwatch_event_rule.bedrock_to_publisher.arn
          }
        }
      },
      {
        Sid    = "AllowLambdaSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.gvp_publisher_dlq.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_lambda_function.gvp_publisher.arn
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# DLQ for Email Poller Lambda (Optional - captures scheduler events)
# -----------------------------------------------------------------------------
resource "aws_sqs_queue" "email_poller_dlq" {
  name = "${local.name_prefix}-email-poller-dlq"

  # Retain messages for 7 days
  message_retention_seconds = 604800

  # Enable encryption
  sqs_managed_sse_enabled = true

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-email-poller-dlq"
    Description = "Dead letter queue for failed email polling events"
  })
}

# DLQ Policy - Allow EventBridge and Lambda to send messages
resource "aws_sqs_queue_policy" "email_poller_dlq_policy" {
  queue_url = aws_sqs_queue.email_poller_dlq.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEventBridgeSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.email_poller_dlq.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_cloudwatch_event_rule.scheduler_to_poller.arn
          }
        }
      },
      {
        Sid    = "AllowLambdaSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.email_poller_dlq.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_lambda_function.email_poller.arn
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Reprocessing Queue (Optional - for manual reprocessing from DLQ)
# -----------------------------------------------------------------------------
resource "aws_sqs_queue" "reprocessing_queue" {
  name = "${local.name_prefix}-reprocessing-queue"

  # Standard retention
  message_retention_seconds = 345600  # 4 days

  # Visibility timeout should match Lambda timeout
  visibility_timeout_seconds = var.lambda_timeout + 30

  # Enable encryption
  sqs_managed_sse_enabled = true

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-reprocessing-queue"
    Description = "Queue for manual reprocessing of failed events"
  })
}

# -----------------------------------------------------------------------------
# SQS Event Source Mappings for DLQ Processor Lambda
# -----------------------------------------------------------------------------

# Trigger DLQ Processor from Invoice Processor DLQ
resource "aws_lambda_event_source_mapping" "invoice_processor_dlq_trigger" {
  event_source_arn = aws_sqs_queue.invoice_processor_dlq.arn
  function_name    = aws_lambda_function.dlq_processor.arn
  batch_size       = 1  # Process one DLQ message at a time for detailed alerts
  enabled          = true

  # Only process messages after they've been in DLQ for at least 1 minute
  # This prevents immediate alerting if message arrives in DLQ
  maximum_batching_window_in_seconds = 60
}

# Trigger DLQ Processor from GVP Publisher DLQ
resource "aws_lambda_event_source_mapping" "gvp_publisher_dlq_trigger" {
  event_source_arn = aws_sqs_queue.gvp_publisher_dlq.arn
  function_name    = aws_lambda_function.dlq_processor.arn
  batch_size       = 1  # Process one DLQ message at a time for detailed alerts
  enabled          = true

  # Only process messages after they've been in DLQ for at least 1 minute
  maximum_batching_window_in_seconds = 60
}

# IAM Policy for DLQ Processor to read from DLQs
resource "aws_iam_role_policy" "dlq_processor_sqs" {
  name = "SQSAccess"
  role = aws_iam_role.dlq_processor_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.invoice_processor_dlq.arn,
          aws_sqs_queue.gvp_publisher_dlq.arn
        ]
      }
    ]
  })
}
