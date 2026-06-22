# =============================================================================
# IAM Roles and Policies
# =============================================================================

# -----------------------------------------------------------------------------
# EventBridge Scheduler Role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "scheduler_role" {
  name = "${local.name_prefix}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "scheduler_invoke_eventbridge" {
  name = "InvokeEventBridge"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "events:PutEvents"
      ]
      Resource = "arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:event-bus/default"
    }]
  })
}

# -----------------------------------------------------------------------------
# Email Poller Lambda Role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "email_poller_role" {
  name = "${local.name_prefix}-email-poller-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

# Basic Lambda execution (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "email_poller_basic" {
  role       = aws_iam_role.email_poller_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 access for email poller
resource "aws_iam_role_policy" "email_poller_s3" {
  name = "S3Access"
  role = aws_iam_role.email_poller_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectMetadata",
          "s3:PutObjectTagging"
        ]
        Resource = "${local.s3_bucket_arn}/${var.invoice_s3_prefix}*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = local.s3_bucket_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "email_poller_s3" {
  role       = aws_iam_role.email_poller_role.name
  policy_arn = aws_iam_policy.email_poller_s3_policy.arn
}

resource "aws_iam_policy" "email_poller_s3_policy" {
  name        = "${local.name_prefix}-email-poller-s3-policy"
  description = "S3 write access for email poller Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectMetadata",
          "s3:PutObjectTagging"
        ]
        Resource = "${local.s3_bucket_arn}/${var.invoice_s3_prefix}*"
      }
    ]
  })

  tags = local.common_tags
}

# SSM Parameter Store access for email poller
resource "aws_iam_role_policy_attachment" "email_poller_ssm" {
  role       = aws_iam_role.email_poller_role.name
  policy_arn = aws_iam_policy.ssm_read_policy.arn
}

# CloudWatch Metrics for Lambda Powertools
resource "aws_iam_role_policy" "email_poller_metrics" {
  name = "CloudWatchMetrics"
  role = aws_iam_role.email_poller_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cloudwatch:PutMetricData"
      ]
      Resource = "*"
      Condition = {
        StringEquals = {
          "cloudwatch:namespace" = "FreightAuditAgent"
        }
      }
    }]
  })
}

# SQS DLQ access for Lambda async invoke config
resource "aws_iam_role_policy" "email_poller_dlq" {
  name = "SQSDLQAccess"
  role = aws_iam_role.email_poller_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage"
      ]
      Resource = aws_sqs_queue.email_poller_dlq.arn
    }]
  })
}

# -----------------------------------------------------------------------------
# Blueprint Manager Lambda Role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "blueprint_manager_role" {
  name = "${local.name_prefix}-blueprint-manager-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "blueprint_manager_basic" {
  role       = aws_iam_role.blueprint_manager_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Bedrock access for blueprint manager
resource "aws_iam_role_policy_attachment" "blueprint_manager_bedrock" {
  role       = aws_iam_role.blueprint_manager_role.name
  policy_arn = aws_iam_policy.bedrock_blueprint_policy.arn
}

resource "aws_iam_policy" "bedrock_blueprint_policy" {
  name        = "${local.name_prefix}-bedrock-blueprint-policy"
  description = "Bedrock Data Automation blueprint and project management"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:CreateBlueprint",
          "bedrock:GetBlueprint",
          "bedrock:UpdateBlueprint",
          "bedrock:ListBlueprints",
          "bedrock:DeleteBlueprint",
          "bedrock:CreateDataAutomationProject",
          "bedrock:GetDataAutomationProject",
          "bedrock:UpdateDataAutomationProject",
          "bedrock:ListDataAutomationProjects",
          "bedrock:DeleteDataAutomationProject"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Invoice Processor Lambda Role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "invoice_processor_role" {
  name = "${local.name_prefix}-invoice-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "invoice_processor_basic" {
  role       = aws_iam_role.invoice_processor_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 access for invoice processor
resource "aws_iam_role_policy_attachment" "invoice_processor_s3" {
  role       = aws_iam_role.invoice_processor_role.name
  policy_arn = aws_iam_policy.invoice_processor_s3_policy.arn
}

resource "aws_iam_policy" "invoice_processor_s3_policy" {
  name        = "${local.name_prefix}-invoice-processor-s3-policy"
  description = "S3 read/write access for invoice processor Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectMetadata",
          "s3:HeadObject"
        ]
        Resource = "${local.s3_bucket_arn}/${var.invoice_s3_prefix}*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${local.s3_bucket_arn}/${var.output_s3_prefix}*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = local.s3_bucket_arn
      }
    ]
  })

  tags = local.common_tags
}

# Bedrock access for invoice processor
resource "aws_iam_role_policy_attachment" "invoice_processor_bedrock" {
  role       = aws_iam_role.invoice_processor_role.name
  policy_arn = aws_iam_policy.bedrock_runtime_policy.arn
}

resource "aws_iam_policy" "bedrock_runtime_policy" {
  name        = "${local.name_prefix}-bedrock-runtime-policy"
  description = "Bedrock Data Automation runtime invocation"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeDataAutomationAsync",
          "bedrock:GetDataAutomationStatus",
          "bedrock:GetAsyncInvocation",
          "bedrock:ListDataAutomationProjects"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

# CloudWatch Metrics for Lambda Powertools
resource "aws_iam_role_policy" "invoice_processor_metrics" {
  name = "CloudWatchMetrics"
  role = aws_iam_role.invoice_processor_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cloudwatch:PutMetricData"
      ]
      Resource = "*"
      Condition = {
        StringEquals = {
          "cloudwatch:namespace" = "FreightAuditAgent"
        }
      }
    }]
  })
}

# SQS DLQ access for Lambda async invoke config
resource "aws_iam_role_policy" "invoice_processor_dlq" {
  name = "SQSDLQAccess"
  role = aws_iam_role.invoice_processor_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage"
      ]
      Resource = aws_sqs_queue.invoice_processor_dlq.arn
    }]
  })
}

# -----------------------------------------------------------------------------
# GVP Publisher Lambda Role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "gvp_publisher_role" {
  name = "${local.name_prefix}-gvp-publisher-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "gvp_publisher_basic" {
  role       = aws_iam_role.gvp_publisher_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 access for GVP publisher
resource "aws_iam_role_policy_attachment" "gvp_publisher_s3" {
  role       = aws_iam_role.gvp_publisher_role.name
  policy_arn = aws_iam_policy.gvp_publisher_s3_policy.arn
}

resource "aws_iam_policy" "gvp_publisher_s3_policy" {
  name        = "${local.name_prefix}-gvp-publisher-s3-policy"
  description = "S3 read access for GVP publisher Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectMetadata",
          "s3:HeadObject"
        ]
        Resource = "${local.s3_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = local.s3_bucket_arn
      }
    ]
  })

  tags = local.common_tags
}

# SSM Parameter Store access for GVP publisher
resource "aws_iam_role_policy_attachment" "gvp_publisher_ssm" {
  role       = aws_iam_role.gvp_publisher_role.name
  policy_arn = aws_iam_policy.ssm_read_policy.arn
}

# CloudWatch Metrics for Lambda Powertools
resource "aws_iam_role_policy" "gvp_publisher_metrics" {
  name = "CloudWatchMetrics"
  role = aws_iam_role.gvp_publisher_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cloudwatch:PutMetricData"
      ]
      Resource = "*"
      Condition = {
        StringEquals = {
          "cloudwatch:namespace" = "FreightAuditAgent"
        }
      }
    }]
  })
}

# SQS DLQ access for Lambda async invoke config
resource "aws_iam_role_policy" "gvp_publisher_dlq" {
  name = "SQSDLQAccess"
  role = aws_iam_role.gvp_publisher_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage"
      ]
      Resource = aws_sqs_queue.gvp_publisher_dlq.arn
    }]
  })
}

# -----------------------------------------------------------------------------
# DLQ Processor Lambda Role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "dlq_processor_role" {
  name = "${local.name_prefix}-dlq-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "dlq_processor_basic" {
  role       = aws_iam_role.dlq_processor_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 access for DLQ processor (read object metadata)
resource "aws_iam_role_policy_attachment" "dlq_processor_s3" {
  role       = aws_iam_role.dlq_processor_role.name
  policy_arn = aws_iam_policy.dlq_processor_s3_policy.arn
}

resource "aws_iam_policy" "dlq_processor_s3_policy" {
  name        = "${local.name_prefix}-dlq-processor-s3-policy"
  description = "S3 read access for DLQ processor Lambda to read object metadata"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectMetadata",
          "s3:HeadObject"
        ]
        Resource = "${local.s3_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = local.s3_bucket_arn
      }
    ]
  })

  tags = local.common_tags
}

# SNS publish access for DLQ processor
resource "aws_iam_role_policy_attachment" "dlq_processor_sns" {
  role       = aws_iam_role.dlq_processor_role.name
  policy_arn = aws_iam_policy.dlq_processor_sns_policy.arn
}

resource "aws_iam_policy" "dlq_processor_sns_policy" {
  name        = "${local.name_prefix}-dlq-processor-sns-policy"
  description = "SNS publish access for DLQ processor Lambda to send invoice error alerts"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sns:Publish"
      ]
      Resource = aws_sns_topic.invoice_errors.arn
    }]
  })

  tags = local.common_tags
}

# CloudWatch Metrics for Lambda Powertools
resource "aws_iam_role_policy" "dlq_processor_metrics" {
  name = "CloudWatchMetrics"
  role = aws_iam_role.dlq_processor_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cloudwatch:PutMetricData"
      ]
      Resource = "*"
      Condition = {
        StringEquals = {
          "cloudwatch:namespace" = "FreightAuditAgent"
        }
      }
    }]
  })
}

# -----------------------------------------------------------------------------
# Shared SSM Parameter Store Read Policy
# -----------------------------------------------------------------------------
resource "aws_iam_policy" "ssm_read_policy" {
  name        = "${local.name_prefix}-ssm-read-policy"
  description = "Read access to SSM Parameter Store secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ]
      Resource = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}/*"
    }]
  })

  tags = local.common_tags
}
