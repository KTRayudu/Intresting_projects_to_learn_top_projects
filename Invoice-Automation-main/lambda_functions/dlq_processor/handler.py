"""
DLQ Processor Lambda - Sends detailed alerts when invoices fail processing
Triggered by SQS DLQ messages
"""
import json
import os
import boto3
from datetime import datetime
from aws_lambda_powertools import Logger

logger = Logger(service="dlq_processor")
sns_client = boto3.client('sns')
s3_client = boto3.client('s3')


def extract_invoice_details_from_dlq_message(message_body):
    """
    Extract invoice details from DLQ message

    DLQ message can be in two formats:
    1. Lambda async invoke format (Lambda execution failure):
       {
         "version": "1.0",
         "timestamp": "2025-12-17T12:00:00.000Z",
         "requestContext": {
           "requestId": "...",
           "functionArn": "...",
           "condition": "RetriesExhausted",
           "approximateInvokeCount": 3
         },
         "requestPayload": { ... original EventBridge event ... },
         "responseContext": { "statusCode": 200, "functionError": "Unhandled" },
         "responsePayload": { "errorMessage": "...", "errorType": "..." }
       }

    2. EventBridge DLQ format (EventBridge delivery failure):
       { ... original EventBridge event directly ... }

    For gvp_publisher: Bedrock completion event
    For invoice_processor: S3 upload event
    """
    try:
        # Parse message body
        message = json.loads(message_body) if isinstance(message_body, str) else message_body

        # Check if this is Lambda async invoke format (has requestPayload)
        if 'requestPayload' in message:
            # Lambda async invoke DLQ - extract original EventBridge event from requestPayload
            event = message['requestPayload']
            logger.info("Processing Lambda async invoke DLQ message",
                       extra={
                           "invoke_count": message.get('requestContext', {}).get('approximateInvokeCount', 'unknown'),
                           "condition": message.get('requestContext', {}).get('condition', 'unknown'),
                           "error_type": message.get('responsePayload', {}).get('errorType', 'unknown')
                       })
        else:
            # EventBridge DLQ or direct event - original event directly
            event = message
            logger.info("Processing EventBridge DLQ message or direct event")

        details = {
            'dlq_type': 'unknown',
            'invoice_number': 'Unknown',
            'input_s3_uri': 'Unknown',
            'output_s3_uri': 'N/A',
            'bucket': 'Unknown',
            'key': 'Unknown',
            'correlation_id': 'Unknown',
            'event_time': event.get('time', 'Unknown')
        }

        # Check if this is a Bedrock completion event (gvp_publisher DLQ)
        if event.get('source') == 'aws.bedrock' and 'detail' in event:
            details['dlq_type'] = 'gvp_publisher'
            detail = event['detail']

            # Extract S3 paths
            if 'input_s3_object' in detail:
                input_obj = detail['input_s3_object']
                details['bucket'] = input_obj.get('s3_bucket', 'Unknown')
                details['key'] = input_obj.get('name', 'Unknown')
                details['input_s3_uri'] = f"s3://{details['bucket']}/{details['key']}"

            if 'output_s3_location' in detail:
                output_obj = detail['output_s3_location']
                details['output_s3_uri'] = f"s3://{output_obj.get('s3_bucket', 'Unknown')}/{output_obj.get('name', 'Unknown')}"

            # Try to get invoice metadata from S3
            try:
                s3_metadata = s3_client.head_object(
                    Bucket=details['bucket'],
                    Key=details['key']
                )
                metadata = s3_metadata.get('Metadata', {})
                details['correlation_id'] = metadata.get('correlation-id', 'Unknown')
                details['mailbox'] = metadata.get('mailbox-id', 'Unknown')
                details['recipient_address'] = metadata.get('email-recipient-address', 'Unknown')

                # Extract invoice number from filename if not in metadata
                if details['invoice_number'] == 'Unknown':
                    # Filename format: 20251203_192017_10034093.pdf
                    filename = details['key'].split('/')[-1]
                    parts = filename.replace('.pdf', '').split('_')
                    if len(parts) >= 3:
                        details['invoice_number'] = parts[2]
            except Exception as e:
                logger.warning("Could not retrieve S3 metadata", extra={"error": str(e)})

        # Check if this is an S3 upload event (invoice_processor DLQ)
        elif event.get('source') == 'aws.s3' and 'detail' in event:
            details['dlq_type'] = 'invoice_processor'
            detail = event['detail']

            if 'bucket' in detail and 'object' in detail:
                details['bucket'] = detail['bucket'].get('name', 'Unknown')
                details['key'] = detail['object'].get('key', 'Unknown')
                details['input_s3_uri'] = f"s3://{details['bucket']}/{details['key']}"

                # Extract invoice number from filename
                filename = details['key'].split('/')[-1]
                parts = filename.replace('.pdf', '').split('_')
                if len(parts) >= 3:
                    details['invoice_number'] = parts[2]

                # Try to get metadata
                try:
                    s3_metadata = s3_client.head_object(
                        Bucket=details['bucket'],
                        Key=details['key']
                    )
                    metadata = s3_metadata.get('Metadata', {})
                    details['correlation_id'] = metadata.get('correlation-id', 'Unknown')
                    details['mailbox'] = metadata.get('mailbox-id', 'Unknown')
                except Exception as e:
                    logger.warning("Could not retrieve S3 metadata", extra={"error": str(e)})

        return details

    except Exception as e:
        logger.error("Error extracting invoice details from DLQ message",
                    exc_info=True,
                    extra={"error": str(e)})
        return None


def send_dlq_alert(details, dlq_name, receive_count):
    """Send detailed alert for DLQ message"""

    sns_topic_arn = os.getenv('SNS_INVOICE_ERROR_TOPIC_ARN')
    if not sns_topic_arn:
        logger.error("SNS_INVOICE_ERROR_TOPIC_ARN not configured")
        return

    # Determine failure stage and environment-aware log paths
    # Extract environment from DLQ name (e.g., "prod-freight-audit-agent-gvp-publisher-dlq" -> "prod")
    env_prefix = dlq_name.split('-')[0] if dlq_name else 'prod'

    if details['dlq_type'] == 'gvp_publisher':
        failure_stage = "GVP API Publishing"
        issue = "Invoice was extracted by Bedrock but failed to post to GVP API"
        next_steps = f"""
1. Check if GVP API is accessible
2. Review CloudWatch logs: /aws/lambda/{env_prefix}-freight-audit-agent-gvp-publisher
3. Manual reprocessing: Retrieve event from DLQ and re-invoke Lambda
4. S3 locations are provided below for manual upload to GVP if needed
"""
    elif details['dlq_type'] == 'invoice_processor':
        failure_stage = "Bedrock Processing"
        issue = "PDF was uploaded to S3 but failed Bedrock Data Automation processing"
        next_steps = f"""
1. Check if Bedrock Data Automation is accessible
2. Review CloudWatch logs: /aws/lambda/{env_prefix}-freight-audit-agent-invoice-processor
3. Verify PDF is not corrupted: Download from S3 and open manually
4. Check Bedrock project configuration and quota limits
5. Manual reprocessing: Retrieve event from DLQ and re-invoke Lambda
"""
    else:
        failure_stage = "Unknown"
        issue = "Processing failed at unknown stage"
        next_steps = "Review DLQ message and CloudWatch logs"

    # Format email message
    message = f"""
🚨 INVOICE PROCESSING FAILED - MANUAL INTERVENTION REQUIRED
================================================================

CRITICAL: Invoice failed after 3 retry attempts and has been moved to Dead Letter Queue

INVOICE DETAILS:
  Invoice Number:     {details['invoice_number']}
  Mailbox:           {details.get('mailbox', 'Unknown')}
  Recipient Address: {details.get('recipient_address', 'Unknown')}
  Correlation ID:    {details['correlation_id']}

FAILURE DETAILS:
  Failed Stage:      {failure_stage}
  Issue:             {issue}
  Event Time:        {details['event_time']}
  Retry Attempts:    3 (all failed)
  Times Reprocessed: {receive_count - 1} (from DLQ)

FILE LOCATIONS:
  PDF Invoice:       {details['input_s3_uri']}
  Bedrock Output:    {details['output_s3_uri']}

DEAD LETTER QUEUE:
  DLQ Name:          {dlq_name}
  Message Available: Yes (can be reprocessed)

NEXT STEPS:
{next_steps}

CLOUDWATCH LOGS SEARCH:
Filter pattern: "{details['correlation_id']}"
Or use Logs Insights query:

fields @timestamp, @message, correlation_id, invoice_number, @logStream
| filter correlation_id = "{details['correlation_id']}"
| sort @timestamp asc

MANUAL REPROCESSING:
To reprocess this invoice from DLQ:
1. Go to AWS Console → SQS → {dlq_name}
2. Select the message (use correlation_id to find it)
3. Send to reprocessing queue or manually re-invoke Lambda
4. Or use AWS CLI:
   aws sqs receive-message --queue-url <DLQ_URL> --max-number-of-messages 1

PDF DOWNLOAD (if manual upload needed):
aws s3 cp {details['input_s3_uri']} ./invoice_{details['invoice_number']}.pdf

================================================================
This is an automated alert from the Freight Audit Agent system.
"""

    try:
        response = sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject=f"🚨 CRITICAL: Invoice {details['invoice_number']} Failed - In DLQ",
            Message=message
        )

        logger.info("Sent DLQ alert via SNS",
                   extra={
                       "message_id": response['MessageId'],
                       "invoice_number": details['invoice_number'],
                       "dlq_type": details['dlq_type']
                   })

    except Exception as e:
        logger.error("Failed to send SNS alert",
                    exc_info=True,
                    extra={"error": str(e)})


@logger.inject_lambda_context
def lambda_handler(event, context):
    """
    Process DLQ messages and send detailed alerts
    Triggered by SQS DLQ
    """
    logger.info("DLQ Processor triggered", extra={"record_count": len(event.get('Records', []))})

    for record in event.get('Records', []):
        try:
            # Extract DLQ information
            dlq_name = record['eventSourceARN'].split(':')[-1]
            receive_count = int(record['attributes'].get('ApproximateReceiveCount', 1))
            message_body = record['body']

            logger.info("Processing DLQ message",
                       extra={
                           "dlq_name": dlq_name,
                           "receive_count": receive_count
                       })

            # Extract invoice details
            details = extract_invoice_details_from_dlq_message(message_body)

            if details:
                # Send alert
                send_dlq_alert(details, dlq_name, receive_count)
            else:
                logger.error("Could not extract invoice details from DLQ message")

        except Exception as e:
            logger.error("Error processing DLQ record",
                        exc_info=True,
                        extra={"error": str(e)})

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(event.get("Records", []))} DLQ messages',
            'timestamp': datetime.utcnow().isoformat()
        })
    }
