# =============================================================================
# Bedrock Data Automation Resources
# =============================================================================

# Note: Bedrock Data Automation blueprints and projects are managed by the
# blueprint_manager Lambda function, not directly by Terraform.
# This is because:
# 1. Terraform AWS provider doesn't yet have full Bedrock Data Automation support
# 2. The blueprint schema (bedrock_invoice_blueprint.json) is version-controlled
#    alongside Lambda code
# 3. The Lambda approach allows dynamic blueprint updates without infrastructure changes

# To create/update blueprints and projects:
# 1. Deploy infrastructure with Terraform
# 2. Invoke the blueprint_manager Lambda function manually or via EventBridge

# The Bedrock Data Automation profile ARN is constructed in locals.tf:
# arn:aws:bedrock:{region}:{account_id}:data-automation-profile/{project_name}

# Reference the profile in invoice_processor Lambda via environment variable:
# DATA_AUTOMATION_PROFILE_ARN = local.bedrock_profile_arn
