"""
Client library for GVP API integration and Bedrock output processing
Handles S3 operations, Bedrock output parsing, and GVP API calls
"""
import boto3
import json
import requests
from urllib.parse import urlparse, unquote_plus
from botocore.config import Config
from aws_lambda_powertools import Logger

# Initialize logger
logger = Logger(service="gvp_invoice_publisher", child=True)

# AWS clients with extended timeouts for Bedrock operations
boto_config = Config(
    connect_timeout=300,
    read_timeout=300,
)

s3_client = boto3.client("s3", config=boto_config)
bda_client = boto3.client('bedrock-data-automation', config=boto_config)
bda_runtime_client = boto3.client('bedrock-data-automation-runtime', config=boto_config)


def read_json_content_from_s3(s3_path):
    """
    Read JSON content from S3

    Args:
        s3_path: S3 URI (s3://bucket/key)

    Returns:
        dict: Parsed JSON content
    """
    bucket_name = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])

    logger.debug("Reading JSON from S3", extra={"bucket": bucket_name, "key": key})

    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    json_content = json.loads(response['Body'].read().decode('utf-8'))

    logger.debug("Successfully read JSON from S3", extra={"size_bytes": len(json_content)})
    return json_content


def get_custom_output_path(job_metadata_s3_uri):
    """
    Extract custom output path from Bedrock job metadata

    Args:
        job_metadata_s3_uri: S3 URI to job_metadata.json

    Returns:
        str: S3 URI to custom output JSON
    """
    logger.debug("Reading job metadata", extra={"metadata_uri": job_metadata_s3_uri})

    json_content = read_json_content_from_s3(job_metadata_s3_uri)
    custom_output_path = json_content['output_metadata'][0]['segment_metadata'][0]['custom_output_path']

    logger.debug("Extracted custom output path", extra={"output_path": custom_output_path})
    return custom_output_path


def get_s3_object_metadata(bucket, key):
    """
    Read user-defined metadata from S3 object

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        dict: User-defined metadata
    """
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        user_metadata = response.get('Metadata', {})

        logger.info("Retrieved S3 object metadata",
                   extra={
                       "bucket": bucket,
                       "key": key,
                       "metadata_keys": list(user_metadata.keys())
                   })

        return user_metadata

    except Exception as e:
        logger.error("Error reading S3 metadata",
                    exc_info=True,
                    extra={
                        "bucket": bucket,
                        "key": key,
                        "error": str(e)
                    })
        return {}


def get_gvp_auth_token(login_id, password, auth_url=None):
    """
    Get authentication token from GVP API

    Args:
        login_id: GVP login ID
        password: GVP password
        auth_url: GVP authentication URL (defaults to QA environment)

    Returns:
        str: Authentication token

    Raises:
        requests.exceptions.RequestException: If authentication fails
    """
    if auth_url is None:
        auth_url = "https://qagvp.intellitrans.com/SSO/Public/API/Auth/GetToken"

    headers = {
        "LoginID": login_id,
        "Pwd": password
    }

    logger.info("Requesting GVP authentication token", extra={"auth_url": auth_url})

    try:
        response = requests.get(auth_url, headers=headers, timeout=30)
        response.raise_for_status()

        token = response.text.strip().strip('"').strip("'")

        logger.info("Successfully obtained GVP token")
        return token

    except requests.exceptions.RequestException as e:
        logger.error("GVP authentication failed",
                    exc_info=True,
                    extra={"error": str(e)})
        raise


def post_invoice_to_gvp(inference_results, token, mailbox_name="", pdf_file_path="", api_url=None):
    """
    Post invoice data to GVP API

    Args:
        inference_results: Dictionary containing extracted invoice data from Bedrock
        token: Authentication token from get_gvp_auth_token()
        mailbox_name: Email recipient address from S3 metadata (e.g., freightaudit+arclin@intellitrans.com)
        pdf_file_path: S3 URI of the PDF file
        api_url: GVP API endpoint URL (defaults to QA environment)

    Returns:
        dict: Response from GVP API

    Raises:
        requests.exceptions.RequestException: If API call fails
    """
    if api_url is None:
        api_url = "https://qagvp.intellitrans.com/gvp/public/api/FreightRates/createmanagementinvoice"

    headers = {
        "tokenID": token,
        "Content-Type": "application/json"
    }

    # Process BOLNumber - truncate to 20 characters if exceeded
    bol_number = inference_results.get("BOLNumber", "")
    if len(bol_number) > 20:
        bol_number_truncated = bol_number[:20]
        logger.warning("BOLNumber exceeds 20 character limit - truncating",
                      extra={
                          "original": bol_number,
                          "truncated": bol_number_truncated,
                          "original_length": len(bol_number)
                      })
        bol_number = bol_number_truncated

    # Process ServiceDate - take only the first date if multiple dates are present
    service_date = inference_results.get("ServiceDate", "")
    if service_date and "," in service_date:
        # Split by comma and take the first date
        service_date_first = service_date.split(",")[0].strip()
        logger.info("Multiple ServiceDates found - using first date only",
                   extra={
                       "original": service_date,
                       "selected": service_date_first
                   })
        service_date = service_date_first

    # Map Bedrock inference results to GVP API format
    payload = {
        "InvoiceDate": inference_results.get("InvoiceDate", ""),
        "InvoiceNumber": inference_results.get("InvoiceNumber", ""),
        "Carrier": inference_results.get("Carrier", ""),
        "Currency": inference_results.get("Currency", "USD"),
        "FeeAmount": inference_results.get("FeeAmount", ""),
        "PartyName": inference_results.get("PartyName", "Novaadmin"),
        "MailboxName": mailbox_name,
        "FleetID": inference_results.get("FleetID", ""),
        "GLAccount": inference_results.get("GLAccount", ""),
        "CostCenter": inference_results.get("CostCenter", ""),
        "BOLNumber": bol_number,
        "OriginCity": inference_results.get("OriginCity", ""),
        "OriginState": inference_results.get("OriginState", ""),
        "DestinationCity": inference_results.get("DestinationCity", ""),
        "DestinationState": inference_results.get("DestinationState", ""),
        "Comments": inference_results.get("Comments", "Invoice auto-created from OCR data."),
        "STCC": inference_results.get("STCC", ""),
        "LeadEquipmentID": inference_results.get("LeadEquipmentID", ""),
        "ServiceDate": service_date,
        "PDFFilePath": pdf_file_path
    }

    # Log payload for debugging (helps diagnose 400/500 errors)
    logger.info("Posting invoice to GVP API",
               extra={
                   "api_url": api_url,
                   "invoice_number": payload.get("InvoiceNumber"),
                   "carrier": payload.get("Carrier"),
                   "mailbox": mailbox_name,
                   "payload_fields": list(payload.keys())
               })

    # Log full payload at debug level
    logger.debug("GVP API request payload", extra={"payload": payload})

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        logger.info("Successfully posted invoice to GVP",
                   extra={
                       "status_code": response.status_code,
                       "invoice_number": payload.get("InvoiceNumber")
                   })

        return response.json() if response.text else {
            "status": "success",
            "status_code": response.status_code
        }

    except requests.exceptions.RequestException as e:
        # Check if this is a duplicate invoice error (idempotent behavior)
        if hasattr(e, 'response') and e.response is not None:
            response_body = e.response.text.lower()

            # GVP API returns 500 with "Invoice Number already Exists" for duplicates
            if "invoice number already exists" in response_body or "already exists" in response_body:
                logger.warning("Duplicate invoice detected - invoice already exists in GVP",
                             extra={
                                 "invoice_number": payload.get("InvoiceNumber"),
                                 "status_code": e.response.status_code,
                                 "response_body": e.response.text,
                                 "idempotent_success": True
                             })

                # Return success response for duplicate (idempotent behavior)
                return {
                    "status": "duplicate",
                    "message": "Invoice already exists in GVP",
                    "invoice_number": payload.get("InvoiceNumber"),
                    "status_code": e.response.status_code,
                    "idempotent": True
                }

        # Log actual errors
        logger.error("GVP API request failed",
                    exc_info=True,
                    extra={
                        "error": str(e),
                        "invoice_number": payload.get("InvoiceNumber")
                    })

        # Log response details if available
        if hasattr(e, 'response') and e.response is not None:
            logger.error("GVP API error response",
                        extra={
                            "status_code": e.response.status_code,
                            "response_body": e.response.text,
                            "response_headers": dict(e.response.headers)
                        })

        # Log the payload that caused the error
        logger.error("Failed request payload", extra={"payload": payload})

        raise




"""
Common observability helper functions for Freight Audit Agent
Provides utilities for quality assessment and metric tracking
"""

def assess_extraction_quality(inference_results):
    """
    Calculate confidence score based on extracted fields from Bedrock

    Args:
        inference_results (dict): Dictionary of extracted invoice fields

    Returns:
        float: Quality score between 0.0 and 1.0

    Example:
        >>> results = {
        ...     'InvoiceNumber': {'value': '12345', 'confidence': 0.95},
        ...     'InvoiceDate': {'value': '2025-01-15', 'confidence': 0.88}
        ... }
        >>> assess_extraction_quality(results)
        0.915
    """
    if not inference_results:
        return 0.0

    total_fields = 0
    total_confidence = 0.0

    for field, value in inference_results.items():
        # Skip non-field entries
        if not isinstance(value, dict) or 'confidence' not in value:
            continue

        total_fields += 1
        confidence = value.get('confidence', 0.0)
        total_confidence += confidence

    if total_fields == 0:
        return 0.0

    return total_confidence / total_fields


def get_quality_threshold():
    """
    Get the quality threshold for automatic vs manual review

    Returns:
        float: Quality threshold (0.7 = 70% confidence)
    """
    return 0.7



def calculate_field_confidence_stats(inference_results):
    """
    Calculate detailed confidence statistics by field
    Useful for identifying which fields have low extraction quality

    Args:
        inference_results (dict): Dictionary of extracted invoice fields

    Returns:
        dict: Statistics about field confidence

    Example:
        >>> results = {
        ...     'InvoiceNumber': {'value': '12345', 'confidence': 0.95},
        ...     'InvoiceDate': {'value': '2025-01-15', 'confidence': 0.65}
        ... }
        >>> calculate_field_confidence_stats(results)
        {
            'avg_confidence': 0.80,
            'min_confidence': 0.65,
            'low_confidence_fields': ['InvoiceDate'],
            'high_confidence_fields': ['InvoiceNumber']
        }
    """
    confidences = []
    low_confidence_fields = []
    high_confidence_fields = []

    for field, value in inference_results.items():
        if not isinstance(value, dict) or 'confidence' not in value:
            continue

        confidence = value.get('confidence', 0.0)
        confidences.append(confidence)

        if confidence < 0.70:
            low_confidence_fields.append(field)
        elif confidence > 0.90:
            high_confidence_fields.append(field)

    if not confidences:
        return {
            'avg_confidence': 0.0,
            'min_confidence': 0.0,
            'low_confidence_fields': [],
            'high_confidence_fields': []
        }

    return {
        'avg_confidence': sum(confidences) / len(confidences),
        'min_confidence': min(confidences),
        'low_confidence_fields': low_confidence_fields,
        'high_confidence_fields': high_confidence_fields
    }
