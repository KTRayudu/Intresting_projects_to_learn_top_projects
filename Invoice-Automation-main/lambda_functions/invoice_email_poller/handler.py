"""
Lambda handler for polling Microsoft 365 mailbox and uploading PDFs to S3 with metadata
Triggered by EventBridge Scheduler every 5 minutes
Uses AWS Lambda Powertools for structured logging and metrics
"""
import json
import os
import base64
import time
import uuid
import boto3
from datetime import datetime
from auth import GraphAuthenticator
from mail_client import GraphMailClient

# AWS Lambda Powertools
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Initialize Powertools
logger = Logger(service="invoice_email_poller")
metrics = Metrics(namespace="FreightAuditAgent", service="invoice_email_poller")

# Initialize S3 client
s3_client = boto3.client('s3')


def sanitize_metadata_value(value):
    """
    Sanitize metadata values for S3 object metadata (HTTP headers)
    Removes newlines, carriage returns, and other control characters
    """
    if not value:
        return ""

    # Convert to string if not already
    value_str = str(value)

    # Replace newlines and carriage returns with spaces
    value_str = value_str.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')

    # Replace tabs with spaces
    value_str = value_str.replace('\t', ' ')

    # Remove other control characters (ASCII 0-31 and 127)
    value_str = ''.join(char if ord(char) >= 32 and ord(char) != 127 else ' ' for char in value_str)

    # Collapse multiple spaces into single space
    value_str = ' '.join(value_str.split())

    return value_str


@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    """
    Lambda handler triggered by EventBridge Scheduler
    Polls mailbox and uploads PDF attachments directly to S3 with email metadata
    """
    start_time = time.time()
    logger.info("Email polling lambda triggered")

    # Get configuration from environment variables
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    mailbox_email = os.getenv("MAILBOX_EMAIL")
    s3_bucket = os.getenv("S3_BUCKET", "devgvpbucket1")
    s3_prefix = os.getenv("S3_PREFIX") or "Invoices/"

    # Ensure prefix ends with / if not empty
    if s3_prefix and not s3_prefix.endswith('/'):
        s3_prefix += '/'

    logger.info("Configuration loaded",
                extra={
                    "mailbox": mailbox_email,
                    "s3_bucket": s3_bucket,
                    "s3_prefix": s3_prefix
                })

    # Validate required configuration
    if not all([client_id, client_secret, tenant_id, mailbox_email]):
        error_msg = "Missing required environment variables"
        logger.error(error_msg,
                    extra={
                        "has_client_id": bool(client_id),
                        "has_client_secret": bool(client_secret),
                        "has_tenant_id": bool(tenant_id),
                        "has_mailbox_email": bool(mailbox_email)
                    })
        metrics.add_metric(name="ConfigurationError", unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }

    try:
        # Authenticate with Microsoft Graph API
        logger.info("Authenticating with Microsoft Graph API")
        authenticator = GraphAuthenticator(client_id, client_secret, tenant_id)
        access_token = authenticator.get_access_token()
        logger.info("Authentication successful")

        # Initialize mail client
        mail_client = GraphMailClient(access_token, mailbox_email)

        # Get unread emails
        logger.info("Checking mailbox for unread emails")
        unread_emails = mail_client.get_unread_emails()

        logger.info("Retrieved unread emails", extra={"count": len(unread_emails)})
        metrics.add_metric(name="EmailsFound", unit=MetricUnit.Count, value=len(unread_emails))

        # Processing metrics
        processed_count = 0
        pdf_count = 0
        skipped_inline_count = 0
        skipped_non_pdf_count = 0
        uploaded_files = []
        errors = []

        # Process each email
        for idx, email in enumerate(unread_emails, 1):
            email_pdf_count = 0
            email_start_time = datetime.utcnow()

            try:
                email_id = email.get("id", f"unknown_{idx}")
                subject = email.get("subject", "(No Subject)")
                sender_info = email.get("from", {}).get("emailAddress", {})
                sender_email = sender_info.get("address", "Unknown")
                sender_name = sender_info.get("name", "Unknown")
                received = email.get("receivedDateTime", "Unknown")
                has_attachments = email.get("hasAttachments", False)
                body_preview = email.get("bodyPreview", "")

                # Extract recipient address (for plus addressing like freightaudit+arclin@intellitrans.com)
                to_recipients = email.get("toRecipients", [])
                recipient_address = ""
                if to_recipients and len(to_recipients) > 0:
                    recipient_address = to_recipients[0].get("emailAddress", {}).get("address", "")

                # Add email context to logger
                logger.append_keys(
                    email_id=email_id[:50],
                    email_subject=subject[:100],
                    sender_email=sender_email
                )

                logger.info("Processing email",
                           extra={
                               "email_number": f"{idx}/{len(unread_emails)}",
                               "sender_name": sender_name,
                               "recipient_address": recipient_address,
                               "received_time": received,
                               "has_attachments": has_attachments
                           })

                if has_attachments:
                    try:
                        # Get all attachments
                        attachments = mail_client.get_email_attachments(email_id)
                        logger.info("Retrieved attachments",
                                  extra={"attachment_count": len(attachments)})

                        for att_idx, attachment in enumerate(attachments, 1):
                            try:
                                # Get attachment properties
                                attachment_type = attachment.get("@odata.type", "")
                                attachment_name = attachment.get("name", "unnamed_attachment")
                                attachment_size = attachment.get("size", 0)
                                attachment_id = attachment.get("id")
                                is_inline = attachment.get("isInline", False)

                                logger.debug("Examining attachment",
                                           extra={
                                               "attachment_number": f"{att_idx}/{len(attachments)}",
                                               "name": attachment_name,
                                               "size_bytes": attachment_size,
                                               "type": attachment_type,
                                               "is_inline": is_inline
                                           })

                                # Skip inline attachments (signature images)
                                if is_inline:
                                    logger.info("Skipping inline attachment (signature image)",
                                              extra={"attachment_name": attachment_name})
                                    skipped_inline_count += 1
                                    continue

                                # Only process file attachments
                                if attachment_type != "#microsoft.graph.fileAttachment":
                                    logger.info("Skipping non-file attachment",
                                              extra={
                                                  "attachment_name": attachment_name,
                                                  "attachment_type": attachment_type
                                              })
                                    continue

                                # Validate required fields
                                if not attachment_name or not attachment_id:
                                    logger.warning("Skipping attachment with missing fields",
                                                 extra={
                                                     "has_name": bool(attachment_name),
                                                     "has_id": bool(attachment_id)
                                                 })
                                    continue

                                # Check if it's a PDF
                                if attachment_name.lower().endswith('.pdf'):
                                    logger.info("Processing PDF attachment",
                                              extra={
                                                  "attachment_name": attachment_name,
                                                  "size_bytes": attachment_size
                                              })
                                    pdf_start = time.time()

                                    try:
                                        # Download attachment content
                                        attachment_content = mail_client.get_attachment_content(
                                            email_id, attachment_id
                                        )

                                        if attachment_content:
                                            # Create S3 key with timestamp
                                            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

                                            # Generate unique correlation ID (UUID4 - globally unique, 36 chars)
                                            correlation_id = str(uuid.uuid4())

                                            # Sanitize filename
                                            safe_filename = "".join(
                                                c for c in attachment_name
                                                if c.isalnum() or c in (' ', '.', '_', '-')
                                            ).strip()

                                            if not safe_filename:
                                                safe_filename = f"invoice_{timestamp}.pdf"
                                                logger.warning(
                                                    "Filename sanitization resulted in empty string",
                                                    extra={
                                                        "original_name": attachment_name,
                                                        "safe_name": safe_filename
                                                    }
                                                )

                                            s3_key = f"{s3_prefix}{timestamp}_{safe_filename}"

                                            # Decode base64 content
                                            file_content = base64.b64decode(attachment_content)
                                            file_size = len(file_content)

                                            # Prepare S3 metadata - sanitize all values to remove newlines
                                            # S3 metadata becomes HTTP headers which cannot contain control characters
                                            metadata = {
                                                'correlation-id': correlation_id,
                                                'mailbox-id': sanitize_metadata_value(mailbox_email[:100]),
                                                'email-recipient-address': sanitize_metadata_value(recipient_address[:100]),
                                                'email-id': sanitize_metadata_value(email_id[:100]),
                                                'email-subject': sanitize_metadata_value((subject[:200] if subject else 'No Subject')),
                                                'email-sender-email': sanitize_metadata_value(sender_email[:100]),
                                                'email-sender-name': sanitize_metadata_value(sender_name[:100]),
                                                'email-received-time': sanitize_metadata_value(received[:50]),
                                                'original-filename': sanitize_metadata_value(attachment_name[:200]),
                                                'attachment-size': str(attachment_size),
                                                'upload-timestamp': datetime.utcnow().isoformat(),
                                                'processing-status': 'pending'
                                            }

                                            if body_preview:
                                                metadata['email-body-preview'] = sanitize_metadata_value(body_preview[:500])

                                            # Upload to S3
                                            s3_client.put_object(
                                                Bucket=s3_bucket,
                                                Key=s3_key,
                                                Body=file_content,
                                                ContentType='application/pdf',
                                                Metadata=metadata
                                            )

                                            upload_duration_ms = int((time.time() - pdf_start) * 1000)
                                            s3_uri = f"s3://{s3_bucket}/{s3_key}"

                                            logger.info("Successfully uploaded PDF to S3",
                                                      extra={
                                                          "correlation_id": correlation_id,
                                                          "s3_uri": s3_uri,
                                                          "file_size_bytes": file_size,
                                                          "duration_ms": upload_duration_ms
                                                      })

                                            # Add metrics (Phase 1)
                                            metrics.add_metric(name="PDFsUploaded", unit=MetricUnit.Count, value=1)

                                            pdf_count += 1
                                            email_pdf_count += 1
                                            uploaded_files.append({
                                                'correlation_id': correlation_id,
                                                's3_uri': s3_uri,
                                                'filename': attachment_name,
                                                'sender': sender_email,
                                                'subject': subject,
                                                'size_bytes': file_size
                                            })

                                        else:
                                            logger.warning("No content returned for attachment",
                                                         extra={
                                                             "attachment_name": attachment_name,
                                                             "attachment_id": attachment_id
                                                         })

                                    except Exception as e:
                                        error_msg = f"Error processing PDF attachment {attachment_name}"
                                        logger.error(error_msg,
                                                   exc_info=True,
                                                   extra={
                                                       "attachment_name": attachment_name,
                                                       "attachment_id": attachment_id,
                                                       "error": str(e)
                                                   })
                                        errors.append(f"{error_msg}: {str(e)}")

                                else:
                                    logger.debug("Skipping non-PDF attachment",
                                               extra={"attachment_name": attachment_name})
                                    skipped_non_pdf_count += 1

                            except Exception as e:
                                error_msg = "Error processing attachment"
                                logger.error(error_msg,
                                           exc_info=True,
                                           extra={
                                               "attachment_number": att_idx,
                                               "error": str(e)
                                           })
                                errors.append(f"{error_msg} #{att_idx}: {str(e)}")

                    except Exception as e:
                        error_msg = "Error retrieving attachments list"
                        logger.error(error_msg, exc_info=True, extra={"error": str(e)})
                        errors.append(f"{error_msg} for email '{subject}': {str(e)}")

                # Mark email as read
                try:
                    mail_client.mark_as_read(email_id)

                    logger.info("Email processing completed",
                              extra={
                                  "pdfs_extracted": email_pdf_count,
                                  "marked_as_read": True
                              })
                    processed_count += 1

                except Exception as e:
                    error_msg = "Error marking email as read"
                    logger.error(error_msg, exc_info=True, extra={"error": str(e)})
                    errors.append(f"{error_msg} '{subject}': {str(e)}")

            except Exception as e:
                error_msg = f"Error processing email"
                logger.error(error_msg,
                           exc_info=True,
                           extra={
                               "email_number": idx,
                               "error": str(e)
                           })
                errors.append(f"{error_msg} #{idx}: {str(e)}")
            finally:
                # Remove email-specific keys
                logger.remove_keys(["email_id", "email_subject", "sender_email"])

        # Calculate total duration
        total_duration_ms = int((time.time() - start_time) * 1000)

        # Record final metrics (Phase 1)
        metrics.add_metric(name="EmailsProcessed", unit=MetricUnit.Count, value=processed_count)
        metrics.add_metric(name="EmailPollDuration", unit=MetricUnit.Milliseconds, value=total_duration_ms)

        # Final summary
        logger.info("Email polling completed",
                   extra={
                       "emails_processed": processed_count,
                       "pdfs_uploaded": pdf_count,
                       "inline_attachments_skipped": skipped_inline_count,
                       "non_pdf_attachments_skipped": skipped_non_pdf_count,
                       "total_errors": len(errors),
                       "s3_location": f"s3://{s3_bucket}/{s3_prefix}"
                   })

        result = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Email polling completed successfully',
                'emails_processed': processed_count,
                'pdfs_uploaded_to_s3': pdf_count,
                'unread_emails_found': len(unread_emails),
                'inline_attachments_skipped': skipped_inline_count,
                'non_pdf_attachments_skipped': skipped_non_pdf_count,
                'uploaded_files': uploaded_files,
                's3_bucket': s3_bucket,
                's3_prefix': s3_prefix,
                'errors': errors,
                'timestamp': datetime.utcnow().isoformat()
            })
        }

        return result

    except Exception as e:
        error_msg = "Fatal error during email polling"
        logger.exception(error_msg)
        metrics.add_metric(name="EmailPollErrors", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'error_details': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
