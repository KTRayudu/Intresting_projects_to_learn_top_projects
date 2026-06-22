"""
Lambda handler for publishing invoice data to GVP API
Triggered by Bedrock Data Automation completion events via EventBridge
Uses AWS Lambda Powertools for structured logging and metrics
"""
import json
import os
import time
import requests
from datetime import datetime
from urllib.parse import unquote_plus
from gvp_client import (
    get_custom_output_path,
    read_json_content_from_s3,
    get_s3_object_metadata,
    get_gvp_auth_token,
    post_invoice_to_gvp
)

# AWS Lambda Powertools
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Initialize Powertools
logger = Logger(service="gvp_invoice_publisher")
metrics = Metrics(namespace="FreightAuditAgent", service="gvp_invoice_publisher")


@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    """
    Lambda handler triggered by Bedrock completion event
    Retrieves inference results and posts to GVP API
    """
    start_time = time.time()
    logger.info("GVP invoice publisher triggered")

    try:
        # Parse event from Bedrock completion
        input_bucket = event["detail"]["input_s3_object"]["s3_bucket"]
        input_key = unquote_plus(event["detail"]["input_s3_object"]["name"])
        output_bucket = event["detail"]["output_s3_location"]["s3_bucket"]
        output_key = unquote_plus(event["detail"]["output_s3_location"]["name"])

        logger.info("Parsed Bedrock completion event",
                   extra={
                       "input_bucket": input_bucket,
                       "input_key": input_key,
                       "output_bucket": output_bucket
                   })

    except KeyError as e:
        error_msg = f"Invalid event structure: missing key {str(e)}"
        logger.error(error_msg, exc_info=True)
        metrics.add_metric(name="InvalidEventError", unit=MetricUnit.Count, value=1)
        # Raise exception to trigger EventBridge retry and DLQ
        raise ValueError(error_msg) from e

    # Construct S3 URIs
    input_s3_uri = f"s3://{input_bucket}/{input_key}"
    output_s3_uri = f"s3://{output_bucket}/{output_key}"

    # Build job metadata path
    job_metadata_s3_uri = "/".join(output_s3_uri.split("/")[:-1]) + "/job_metadata.json"

    # Get S3 object metadata to extract correlation ID, mailbox, and recipient address
    try:
        s3_metadata = get_s3_object_metadata(input_bucket, input_key)
        correlation_id = s3_metadata.get('correlation-id', 'unknown')
        mailbox_id = s3_metadata.get('mailbox-id', 'unknown')
        recipient_address = s3_metadata.get('email-recipient-address', 'unknown')
        email_received_time = s3_metadata.get('email-received-time')
    except Exception as e:
        logger.warning("Failed to retrieve S3 metadata", extra={"error": str(e)})
        correlation_id = 'unknown'
        mailbox_id = 'unknown'
        recipient_address = 'unknown'
        email_received_time = None

    logger.append_keys(
        correlation_id=correlation_id,
        mailbox_id=mailbox_id,
        recipient_address=recipient_address,
        input_s3_uri=input_s3_uri,
        job_metadata_uri=job_metadata_s3_uri
    )

    try:
        # Get custom output path from job metadata
        logger.info("Retrieving Bedrock output path")
        custom_output_s3_uri = get_custom_output_path(job_metadata_s3_uri)

        logger.info("Reading inference results", extra={"output_uri": custom_output_s3_uri})
        custom_op_json = read_json_content_from_s3(custom_output_s3_uri)
        inference_results = custom_op_json.get("inference_result", {})

        if not inference_results:
            raise ValueError("No inference results found in Bedrock output")

        logger.info("Successfully retrieved inference results",
                   extra={"field_count": len(inference_results)})

    except Exception as e:
        error_msg = "Error retrieving Bedrock inference results"
        logger.error(error_msg, exc_info=True, extra={"error": str(e)})
        metrics.add_metric(name="GVPPostsFailed", unit=MetricUnit.Count, value=1)
        # Raise exception to trigger EventBridge retry and DLQ
        raise RuntimeError(f"{error_msg}: {str(e)}") from e

    # Get invoice number for logging
    invoice_number = inference_results.get('InvoiceNumber', 'N/A')

    logger.info("Processing invoice", extra={
        "invoice_number": invoice_number,
        "carrier": inference_results.get("Carrier", "N/A"),
        "recipient_address": recipient_address
    })

    # Use recipient_address from metadata (contains plus addressing like freightaudit+arclin@intellitrans.com)
    pdf_file_path = input_s3_uri

    # Get GVP credentials and configuration
    gvp_login_id = os.getenv("GVP_LOGIN_ID")
    gvp_password = os.getenv("GVP_PASSWORD")
    gvp_auth_url = os.getenv("GVP_AUTH_URL")  # Optional - defaults to QA in gvp_client
    gvp_api_url = os.getenv("GVP_API_URL")    # Optional - defaults to QA in gvp_client

    if not gvp_login_id or not gvp_password:
        error_msg = "Missing GVP credentials in environment variables"
        logger.error(error_msg,
                    extra={
                        "has_login_id": bool(gvp_login_id),
                        "has_password": bool(gvp_password)
                    })
        metrics.add_metric(name="ConfigurationError", unit=MetricUnit.Count, value=1)
        # Raise exception to trigger EventBridge retry and DLQ
        raise RuntimeError(error_msg)

    try:
        # Authenticate with GVP API
        logger.info("Authenticating with GVP API")
        gvp_token = get_gvp_auth_token(gvp_login_id, gvp_password, gvp_auth_url)
        logger.info("GVP authentication successful")

        # Post invoice to GVP API
        logger.info("Posting invoice to GVP API",
                   extra={
                       "invoice_number": invoice_number,
                       "carrier": inference_results.get("Carrier", "N/A"),
                       "recipient_address": recipient_address
                   })

        gvp_response = post_invoice_to_gvp(
            inference_results,
            gvp_token,
            recipient_address,  # Use recipient address (e.g., freightaudit+arclin@intellitrans.com)
            pdf_file_path,
            gvp_api_url
        )

        # Check if this was a duplicate invoice
        is_duplicate = gvp_response.get("idempotent", False)

        if is_duplicate:
            logger.info("Invoice already exists in GVP (duplicate)",
                       extra={
                           "gvp_response": gvp_response,
                           "invoice_number": invoice_number,
                           "duplicate": True
                       })
            # Add duplicate metric
            metrics.add_metric(name="GVPPostsDuplicate", unit=MetricUnit.Count, value=1)
        else:
            logger.info("Successfully posted invoice to GVP",
                       extra={
                           "gvp_response": gvp_response,
                           "invoice_number": invoice_number
                       })

        # Phase 1 metrics (count both new and duplicate as successful)
        metrics.add_metric(name="GVPPostsSuccessful", unit=MetricUnit.Count, value=1)

        # Calculate end-to-end latency if we have email received time
        if email_received_time:
            try:
                received_dt = datetime.fromisoformat(email_received_time.replace('Z', '+00:00'))
                end_to_end_ms = int((datetime.utcnow() - received_dt).total_seconds() * 1000)

                logger.info("Pipeline completed", extra={
                    "end_to_end_duration_ms": end_to_end_ms,
                    "invoice_number": invoice_number
                })

                # Phase 1 metrics
                metrics.add_metric(name="EndToEndLatency", unit=MetricUnit.Milliseconds, value=end_to_end_ms)
            except Exception as e:
                logger.warning("Could not calculate end-to-end latency", extra={"error": str(e)})

        total_duration_ms = int((time.time() - start_time) * 1000)

        # Build success message based on duplicate status
        success_message = 'Invoice already exists in GVP (duplicate)' if is_duplicate else 'Successfully posted invoice to GVP'

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': success_message,
                'correlation_id': correlation_id,
                'invoice_number': invoice_number,
                'carrier': inference_results.get("Carrier", "N/A"),
                'duplicate': is_duplicate,
                'gvp_response': gvp_response,
                'input_s3_uri': input_s3_uri,
                'duration_ms': total_duration_ms,
                'timestamp': datetime.utcnow().isoformat()
            })
        }

    except requests.exceptions.Timeout as e:
        # Transient error - re-raise to trigger EventBridge retry and eventual DLQ
        logger.error("GVP API timeout - will retry",
                    exc_info=True,
                    extra={
                        "error": str(e),
                        "invoice_number": invoice_number,
                        "correlation_id": correlation_id
                    })
        metrics.add_metric(name="GVPTimeout", unit=MetricUnit.Count, value=1)
        raise  # EventBridge will retry, then send to DLQ after 3 attempts

    except requests.exceptions.ConnectionError as e:
        # Transient error - re-raise to trigger EventBridge retry and eventual DLQ
        logger.error("GVP API connection error - will retry",
                    exc_info=True,
                    extra={
                        "error": str(e),
                        "invoice_number": invoice_number,
                        "correlation_id": correlation_id
                    })
        metrics.add_metric(name="GVPConnectionError", unit=MetricUnit.Count, value=1)
        raise  # EventBridge will retry, then send to DLQ after 3 attempts

    except requests.exceptions.HTTPError as e:
        # HTTP error (both 4xx and 5xx) - re-raise to trigger retry and eventual DLQ
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'unknown'
        logger.error("GVP API HTTP error - will retry",
                    exc_info=True,
                    extra={
                        "error": str(e),
                        "status_code": status_code,
                        "invoice_number": invoice_number,
                        "correlation_id": correlation_id
                    })
        metrics.add_metric(name="GVPHTTPError", unit=MetricUnit.Count, value=1)
        raise  # EventBridge will retry, then send to DLQ after 3 attempts

    except Exception as e:
        # Unknown error - re-raise to trigger retry and eventual DLQ
        logger.error("Error posting invoice to GVP - will retry",
                    exc_info=True,
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "invoice_number": invoice_number,
                        "correlation_id": correlation_id
                    })
        metrics.add_metric(name="GVPPostsFailed", unit=MetricUnit.Count, value=1)
        raise  # EventBridge will retry, then send to DLQ after 3 attempts
