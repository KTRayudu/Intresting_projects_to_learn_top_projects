"""
Sample API responses for mocking external services
"""
import base64


def get_msal_token_response():
    """Microsoft Graph API token response"""
    return {
        "token_type": "Bearer",
        "expires_in": 3599,
        "access_token": "fake-access-token-abc123xyz789"
    }


def get_msal_token_error_response():
    """Microsoft Graph API token error response"""
    return {
        "error": "invalid_client",
        "error_description": "Invalid client credentials",
        "error_codes": [7000215]
    }


def get_graph_unread_emails_response():
    """Microsoft Graph API unread emails response"""
    return {
        "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('invoices@testcompany.com')/mailFolders('inbox')/messages",
        "@odata.count": 2,
        "value": [
            {
                "id": "email-id-001",
                "subject": "Invoice from ACME Shipping",
                "bodyPreview": "Please find attached invoice for shipment...",
                "from": {
                    "emailAddress": {
                        "name": "John Doe",
                        "address": "john.doe@acmeshipping.com"
                    }
                },
                "receivedDateTime": "2024-01-15T09:00:00Z",
                "hasAttachments": True
            },
            {
                "id": "email-id-002",
                "subject": "Freight Invoice #12345",
                "bodyPreview": "Attached is the freight invoice for January...",
                "from": {
                    "emailAddress": {
                        "name": "Jane Smith",
                        "address": "billing@freightco.com"
                    }
                },
                "receivedDateTime": "2024-01-15T08:30:00Z",
                "hasAttachments": True
            }
        ]
    }


def get_graph_email_attachments_response():
    """Microsoft Graph API email attachments response"""
    # Sample PDF content encoded in base64
    sample_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    encoded_content = base64.b64encode(sample_pdf_content).decode('utf-8')

    return {
        "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('invoices@testcompany.com')/messages('email-id-001')/attachments",
        "value": [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "id": "attachment-id-001",
                "name": "invoice_12345.pdf",
                "contentType": "application/pdf",
                "size": 102400,
                "isInline": False
            }
        ]
    }


def get_graph_attachment_content_response():
    """Microsoft Graph API attachment content response"""
    # Sample PDF content encoded in base64
    sample_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    encoded_content = base64.b64encode(sample_pdf_content).decode('utf-8')

    return {
        "@odata.type": "#microsoft.graph.fileAttachment",
        "id": "attachment-id-001",
        "name": "invoice_12345.pdf",
        "contentType": "application/pdf",
        "size": 102400,
        "isInline": False,
        "contentBytes": encoded_content
    }


def get_graph_inline_attachment_response():
    """Microsoft Graph API inline attachment (signature image) response"""
    return {
        "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('invoices@testcompany.com')/messages('email-id-001')/attachments",
        "value": [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "id": "attachment-id-inline-001",
                "name": "signature.png",
                "contentType": "image/png",
                "size": 5120,
                "isInline": True
            }
        ]
    }


def get_bedrock_list_blueprints_response(blueprint_name="test-freight-invoice-blueprint"):
    """AWS Bedrock list blueprints response"""
    return {
        "blueprints": [
            {
                "blueprintArn": f"arn:aws:bedrock:us-east-1:123456789012:blueprint/{blueprint_name}",
                "blueprintName": blueprint_name,
                "blueprintStage": "LIVE",
                "blueprintVersion": "1",
                "creationTime": "2024-01-15T10:00:00.000Z"
            }
        ]
    }


def get_bedrock_create_blueprint_response(blueprint_name="test-freight-invoice-blueprint"):
    """AWS Bedrock create blueprint response"""
    return {
        "blueprint": {
            "blueprintArn": f"arn:aws:bedrock:us-east-1:123456789012:blueprint/{blueprint_name}",
            "blueprintName": blueprint_name,
            "blueprintStage": "LIVE",
            "blueprintVersion": "1",
            "schema": "{}",
            "type": "DOCUMENT",
            "creationTime": "2024-01-15T10:00:00.000Z"
        }
    }


def get_bedrock_list_projects_response(project_name="test-freight-audit-project"):
    """AWS Bedrock list projects response"""
    return {
        "projects": [
            {
                "projectArn": f"arn:aws:bedrock:us-east-1:123456789012:data-automation-project/{project_name}",
                "projectName": project_name,
                "projectStage": "LIVE",
                "creationTime": "2024-01-15T10:00:00.000Z"
            }
        ]
    }


def get_bedrock_create_project_response(project_name="test-freight-audit-project"):
    """AWS Bedrock create project response"""
    return {
        "project": {
            "projectArn": f"arn:aws:bedrock:us-east-1:123456789012:data-automation-project/{project_name}",
            "projectName": project_name,
            "projectStage": "LIVE",
            "creationTime": "2024-01-15T10:00:00.000Z"
        }
    }


def get_bedrock_invoke_async_response():
    """AWS Bedrock invoke data automation async response"""
    return {
        "invocationArn": "arn:aws:bedrock:us-east-1:123456789012:invocation/test-invocation-id-12345"
    }


def get_bedrock_job_metadata():
    """Bedrock job metadata from S3"""
    return {
        "invocation_arn": "arn:aws:bedrock:us-east-1:123456789012:invocation/test-invocation-id-12345",
        "status": "SUCCEEDED",
        "output_metadata": [
            {
                "segment_metadata": [
                    {
                        "custom_output_path": "s3://test-bucket/lambda-output/test-job-id/custom-output.json"
                    }
                ]
            }
        ]
    }


def get_bedrock_inference_results():
    """Bedrock inference results (extracted invoice data)"""
    return {
        "inference_result": {
            "InvoiceDate": "2024-01-15",
            "InvoiceNumber": "INV-12345",
            "Carrier": "ACME Shipping",
            "Currency": "USD",
            "FeeAmount": "1250.00",
            "PartyName": "Test Company",
            "FleetID": "FLEET-001",
            "GLAccount": "5000",
            "CostCenter": "CC-100",
            "BOLNumber": "BOL-98765",
            "OriginCity": "Los Angeles",
            "OriginState": "CA",
            "DestinationCity": "New York",
            "DestinationState": "NY",
            "STCC": "4011",
            "LeadEquipmentID": "TRUCK-456",
            "ServiceDate": "2024-01-10",
            "Comments": "Standard freight shipment"
        }
    }


def get_gvp_auth_token_response():
    """GVP API authentication token response"""
    return "gvp-fake-auth-token-xyz789abc123"


def get_gvp_post_invoice_response():
    """GVP API post invoice success response"""
    return {
        "status": "success",
        "message": "Invoice created successfully",
        "invoiceId": "GVP-INV-12345"
    }


def get_s3_object_metadata():
    """S3 object metadata (email context)"""
    return {
        "email-id": "email-id-001",
        "email-subject": "Invoice from ACME Shipping",
        "email-sender-email": "john.doe@acmeshipping.com",
        "email-sender-name": "John Doe",
        "email-received-time": "2024-01-15T09:00:00Z",
        "original-filename": "invoice_12345.pdf",
        "attachment-size": "102400",
        "upload-timestamp": "2024-01-15T10:30:00.000000",
        "mailbox": "invoices@testcompany.com",
        "processing-status": "pending",
        "email-body-preview": "Please find attached invoice for shipment..."
    }
