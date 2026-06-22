# =============================================================================
# S3 Bucket for Freight Audit Agent
# =============================================================================
# Single bucket stores both invoice PDFs and Bedrock output using prefixes:
# - freight-audit-agent-invoices/ for raw PDF invoices
# - freight-audit-agent-output/ for structured Bedrock output
#
# Can either create a new bucket or use an existing one (e.g., prodgvpfilestore1)
# Set use_existing_bucket=true and existing_bucket_name="your-bucket" to use existing

# -----------------------------------------------------------------------------
# Data source for existing bucket (when use_existing_bucket is true)
# -----------------------------------------------------------------------------
data "aws_s3_bucket" "existing" {
  count  = var.use_existing_bucket ? 1 : 0
  bucket = var.existing_bucket_name
}

# -----------------------------------------------------------------------------
# Storage Bucket - Conditionally created only if not using existing bucket
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "storage" {
  count  = var.use_existing_bucket ? 0 : 1
  bucket = local.s3_bucket_name

  tags = merge(local.common_tags, {
    Name        = local.s3_bucket_name
    Description = "Storage for freight invoice PDFs and Bedrock output"
  })
}

# Enable versioning for storage bucket
resource "aws_s3_bucket_versioning" "storage" {
  count  = var.use_existing_bucket ? 0 : 1
  bucket = aws_s3_bucket.storage[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption for storage bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "storage" {
  count  = var.use_existing_bucket ? 0 : 1
  bucket = aws_s3_bucket.storage[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Block public access for storage bucket
resource "aws_s3_bucket_public_access_block" "storage" {
  count  = var.use_existing_bucket ? 0 : 1
  bucket = aws_s3_bucket.storage[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for storage bucket
resource "aws_s3_bucket_lifecycle_configuration" "storage" {
  count  = var.use_existing_bucket ? 0 : 1
  bucket = aws_s3_bucket.storage[0].id

  # Rule for invoice PDFs - transition to cheaper storage over time
  rule {
    id     = "transition-invoices-to-ia"
    status = "Enabled"

    filter {
      prefix = var.invoice_s3_prefix
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER_IR"
    }
  }

  # Rule for Bedrock output - clean up after 90 days
  rule {
    id     = "cleanup-old-outputs"
    status = "Enabled"

    filter {
      prefix = var.output_s3_prefix
    }

    expiration {
      days = 90
    }
  }
}

# Enable EventBridge notifications for storage bucket
resource "aws_s3_bucket_notification" "storage" {
  count       = var.use_existing_bucket ? 0 : 1
  bucket      = aws_s3_bucket.storage[0].id
  eventbridge = true
}

# S3 bucket policy to allow Bedrock Data Automation access (new bucket)
resource "aws_s3_bucket_policy" "storage_bedrock_access" {
  count  = var.use_existing_bucket ? 0 : 1
  bucket = aws_s3_bucket.storage[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowBedrockDataAutomationRead"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.storage[0].arn,
          "${aws_s3_bucket.storage[0].arn}/*"
        ]
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "AllowBedrockDataAutomationWrite"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${aws_s3_bucket.storage[0].arn}/*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Configuration for EXISTING bucket (when use_existing_bucket = true)
# -----------------------------------------------------------------------------
# IMPORTANT: These resources will modify the existing bucket configuration:
# - EventBridge notifications will be enabled (required for S3 event processing)
# - Bucket policy will be MERGED with existing statements (preserves existing policies)
# - Other bucket settings (versioning, encryption, lifecycle) are NOT modified

# Enable EventBridge notifications for existing bucket
resource "aws_s3_bucket_notification" "existing" {
  count       = var.use_existing_bucket ? 1 : 0
  bucket      = data.aws_s3_bucket.existing[0].id
  eventbridge = true
}

# Read existing bucket policy (if any)
# This data source calls AWS API: s3:GetBucketPolicy
# Requires IAM permission: s3:GetBucketPolicy on the bucket
# Returns the current bucket policy JSON, or empty if no policy exists
# If the bucket has no policy, this will fail gracefully (handled by try() below)
data "aws_s3_bucket_policy" "existing" {
  count  = var.use_existing_bucket ? 1 : 0
  bucket = data.aws_s3_bucket.existing[0].id
}

# Define Bedrock access policy statements
# Account IDs are dynamically retrieved from data.aws_caller_identity.current
# No hardcoding needed - Terraform automatically uses YOUR AWS account ID
data "aws_iam_policy_document" "bedrock_access_existing" {
  count = var.use_existing_bucket ? 1 : 0

  statement {
    sid    = "AllowBedrockDataAutomationRead"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      data.aws_s3_bucket.existing[0].arn,
      "${data.aws_s3_bucket.existing[0].arn}/*"
    ]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      # Dynamically populated with your AWS account ID (from aws sts get-caller-identity)
      values   = [data.aws_caller_identity.current.account_id]
    }
  }

  statement {
    sid    = "AllowBedrockDataAutomationWrite"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl"
    ]
    resources = [
      "${data.aws_s3_bucket.existing[0].arn}/*"
    ]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

# Merge existing policy with Bedrock access policy
# This combines existing statements with new Bedrock statements
# - source_policy_documents: Preserves all existing policy statements (if policy exists)
# - override_policy_documents: Adds our Bedrock statements (overrides if Sid matches)
# - try() with jsondecode/jsonencode handles two cases:
#   1. Bucket has existing policy → merge it
#   2. Bucket has no policy → data source returns null → try() returns empty policy → only Bedrock statements applied
locals {
  # Get existing policy, or use empty policy if none exists
  # This handles the "no policy" case gracefully without errors
  existing_policy_json = var.use_existing_bucket ? try(
    data.aws_s3_bucket_policy.existing[0].policy,
    jsonencode({
      Version   = "2012-10-17"
      Statement = []
    })
  ) : ""
}

data "aws_iam_policy_document" "existing_merged" {
  count = var.use_existing_bucket ? 1 : 0

  # Include existing policy statements (if policy exists)
  # If bucket has no policy, locals.existing_policy_json contains empty Statement array
  source_policy_documents = [
    local.existing_policy_json
  ]

  # Add Bedrock access statements
  # If existing policy has same Sids, these will override them
  override_policy_documents = [
    data.aws_iam_policy_document.bedrock_access_existing[0].json
  ]
}

# Apply merged bucket policy to existing bucket
# This MERGES with existing policies instead of replacing them
# Existing policy statements are preserved, Bedrock statements are added
resource "aws_s3_bucket_policy" "existing_bedrock_access" {
  count  = var.use_existing_bucket ? 1 : 0
  bucket = data.aws_s3_bucket.existing[0].id

  policy = data.aws_iam_policy_document.existing_merged[0].json
}
