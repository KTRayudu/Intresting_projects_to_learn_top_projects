# Lambda Layers

This directory contains custom Lambda layers used by the Freight Audit Agent Lambda functions.

## Layers Overview

### 1. AWS Powertools Layer (AWS-managed)
- **Layer Name**: `AWSLambdaPowertoolsPythonV3-python311-x86_64`
- **Source**: AWS-managed (published by AWS account 017000801446)
- **Purpose**: Provides AWS Lambda Powertools for structured logging, metrics, and tracing
- **Documentation**: https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer
- **No upload required** - referenced directly by ARN in Terraform

**ARN Format**:
```
arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python311-x86_64:{version}
```

### 2. MSAL + Requests Layer (Custom)
- **Layer Name**: `{environment}-msal-requests-layer`
- **File**: `msal_requests_layer.zip` (6.6 MB)
- **Purpose**: Provides MSAL and requests libraries for Microsoft Graph API and GVP API integration
- **Runtime**: Python 3.11

**Included Packages**:
- `msal` >= 1.24.0 - Microsoft Authentication Library for OAuth authentication
- `requests` >= 2.31.0 - HTTP library for API calls
- Dependencies: `certifi`, `cffi`, `charset-normalizer`, `cryptography`, `idna`, `PyJWT`, `urllib3`

**Layer Structure**:
```
msal_requests_layer.zip
└── python/
    └── lib/
        └── python3.11/
            └── site-packages/
                ├── msal/
                ├── requests/
                └── (other dependencies)
```

## Lambda Functions and Their Layers

| Lambda Function | AWS Powertools | MSAL + Requests | Reason |
|----------------|----------------|-----------------|--------|
| `email_poller` | ✅ | ✅ | Uses Powertools for logging/metrics + MSAL for M365 authentication |
| `blueprint_manager` | ✅ | ❌ | Only needs Powertools for logging/metrics |
| `invoice_processor` | ✅ | ❌ | Only needs Powertools for logging/metrics |
| `gvp_publisher` | ✅ | ✅ | Uses Powertools for logging/metrics + requests for GVP API calls |

## Rebuilding the MSAL + Requests Layer

If you need to rebuild the layer with updated package versions:

```bash
# Create a temporary directory
mkdir -p lambda_layers/python/lib/python3.11/site-packages

# Install packages into the layer directory
pip install \
  msal>=1.24.0 \
  requests>=2.31.0 \
  -t lambda_layers/python/lib/python3.11/site-packages

# Create the zip file
cd lambda_layers
zip -r msal_requests_layer.zip python/
cd ..

# Clean up
rm -rf lambda_layers/python
```

**Note**: Build the layer on Amazon Linux 2023 or use Docker with `public.ecr.aws/lambda/python:3.11` image to ensure binary compatibility with Lambda runtime.

## Terraform Integration

The layers are configured in `terraform/layers.tf`:

```hcl
# AWS Powertools - Referenced by ARN (no upload needed)
data "aws_lambda_layer_version" "powertools" {
  layer_name = "AWSLambdaPowertoolsPythonV3-python311-x86_64"
}

# Custom MSAL + Requests Layer - Uploaded to AWS
resource "aws_lambda_layer_version" "msal_requests" {
  filename            = "${path.module}/../lambda_layers/msal_requests_layer.zip"
  layer_name          = "${var.environment}-msal-requests-layer"
  compatible_runtimes = ["python3.11"]
  source_code_hash    = filebase64sha256("${path.module}/../lambda_layers/msal_requests_layer.zip")
}
```

Lambda functions reference these layers via the `layers` attribute in `terraform/lambda.tf`.

## Important Notes

1. **AWS Powertools Updates**: AWS automatically publishes new versions. To update, either:
   - Omit the `version` parameter to always get the latest (not recommended for production)
   - Pin to a specific version number in the Terraform data source

2. **Layer Size Limits**:
   - Unzipped size limit: 250 MB (per layer)
   - Total unzipped size (all layers + deployment package): 250 MB
   - Current MSAL + Requests layer: ~6.6 MB zipped

3. **Python Version**: Ensure the layer is built for Python 3.11 to match the Lambda runtime

4. **Dependencies**: The MSAL package includes cryptography and other native extensions that must be compiled for the Lambda execution environment (Amazon Linux 2)

5. **Testing**: Always test Lambda functions with layers in a test environment before deploying to production

## Troubleshooting

### ImportError: No module named 'msal' or 'requests'
- Verify the layer is attached to the Lambda function in the AWS Console
- Check the layer structure matches the expected format: `python/lib/python3.11/site-packages/`

### Lambda function exceeds size limit
- Review the deployment package size (function code + layers)
- Consider removing unused dependencies from the layer
- Use S3 for large deployment packages instead of direct upload

### Cryptography or native library errors
- Rebuild the layer on Amazon Linux 2023 or using the Lambda Docker image
- Ensure the layer was built for x86_64 architecture (or arm64 if using ARM-based Lambda)
