# =============================================================================
# SSM Parameter Store - Secrets Management
# =============================================================================

# -----------------------------------------------------------------------------
# Azure AD Credentials for Microsoft 365 Integration
# -----------------------------------------------------------------------------
resource "aws_ssm_parameter" "azure_client_id" {
  name        = local.ssm_parameters.azure_client_id
  description = "Azure AD application client ID for Microsoft 365 mailbox access"
  type        = "SecureString"
  value       = var.azure_client_id

  tags = merge(local.common_tags, {
    Name = "Azure Client ID"
  })
}

resource "aws_ssm_parameter" "azure_client_secret" {
  name        = local.ssm_parameters.azure_client_secret
  description = "Azure AD application client secret for Microsoft 365 mailbox access"
  type        = "SecureString"
  value       = var.azure_client_secret

  tags = merge(local.common_tags, {
    Name = "Azure Client Secret"
  })
}

resource "aws_ssm_parameter" "azure_tenant_id" {
  name        = local.ssm_parameters.azure_tenant_id
  description = "Azure AD tenant ID"
  type        = "SecureString"
  value       = var.azure_tenant_id

  tags = merge(local.common_tags, {
    Name = "Azure Tenant ID"
  })
}

# -----------------------------------------------------------------------------
# GVP API Credentials
# -----------------------------------------------------------------------------
resource "aws_ssm_parameter" "gvp_password" {
  name        = local.ssm_parameters.gvp_password
  description = "GVP API password for invoice publishing"
  type        = "SecureString"
  value       = var.gvp_password

  tags = merge(local.common_tags, {
    Name = "GVP Password"
  })
}
