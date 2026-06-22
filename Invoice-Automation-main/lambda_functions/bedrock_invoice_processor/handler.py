"""
Lambda handler for processing invoice documents with AWS Bedrock Data Automation
Triggered by S3 upload events via EventBridge rule
Starts async Bedrock jobs for document extraction using configured blueprints
Uses AWS Lambda Powertools for structured logging and metrics
"""
import json
import boto3
import os
import time
from datetime import datetime
from urllib.parse import unquote_plus

# AWS Lambda Powertools
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Initialize Powertools
logger = Logger(service="bedrock_invoice_processor")
metrics = Metrics(namespace="FreightAuditAgent", service="bedrock_invoice_processor")


@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    """
    Lambda handler triggered by S3 upload events
    Starts Bedrock Data Automation async job for invoice processing

    Supports two event formats:
    1. EventBridge S3 notification (event["detail"])
    2. Native S3 event notification (event["Records"])

    Environment Variables:
        PROJECT_NAME: Bedrock project name (default: Freight_Audit_Agent)
        DATA_AUTOMATION_PROFILE_ARN: Optional profile ARN (auto-constructed if not provided)
        AWS_REGION: AWS region (default: us-east-1)
    """
    start_time = time.time()
    logger.info("Bedrock invoice processor triggered")

    try:
        region = os.environ.get('AWS_REGION', 'us-east-1')

        # Initialize clients
        s3_client = boto3.client('s3')
        bda_client = boto3.client('bedrock-data-automation', region_name=region)
        bda_runtime_client = boto3.client('bedrock-data-automation-runtime', region_name=region)
        sts_client = boto3.client('sts', region_name=region)

        # Parse S3 details from event (handle both formats)
        try:
            if "detail" in event:
                # EventBridge S3 notification format
                s3_bucket = event["detail"]["bucket"]["name"]
                s3_key = unquote_plus(event["detail"]["object"]["key"])
                event_format = "EventBridge"
                logger.debug("Parsed EventBridge S3 notification")

            elif "Records" in event:
                # Native S3 event notification format
                s3_record = event["Records"][0]["s3"]
                s3_bucket = s3_record["bucket"]["name"]
                s3_key = unquote_plus(s3_record["object"]["key"])
                event_format = "S3 Native"
                logger.debug("Parsed native S3 notification")

            else:
                raise ValueError("Unsupported event format - expected EventBridge or S3 Records")

        except (KeyError, IndexError) as e:
            error_msg = f"Invalid event structure: {str(e)}"
            logger.error(error_msg, exc_info=True)
            metrics.add_metric(name="InvalidEventError", unit=MetricUnit.Count, value=1)

            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': error_msg,
                    'message': 'Missing required S3 event fields'
                })
            }

        # Get output bucket and prefix from environment variables
        # Use dedicated output bucket/prefix to separate inputs from outputs
        output_bucket = os.getenv('OUTPUT_BUCKET', event.get('output_bucket', s3_bucket))
        output_prefix = os.getenv('OUTPUT_PREFIX', 'lambda-output/')

        # Validate S3 inputs
        if not s3_bucket or not s3_key:
            error_msg = "Missing s3_bucket or s3_key"
            logger.error(error_msg,
                        extra={
                            "has_bucket": bool(s3_bucket),
                            "has_key": bool(s3_key)
                        })
            metrics.add_metric(name="MissingS3DetailsError", unit=MetricUnit.Count, value=1)

            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': error_msg,
                    'message': 'S3 bucket and key are required'
                })
            }

        # Construct S3 URIs
        document_s3_uri = f's3://{s3_bucket}/{s3_key}'
        bda_s3_output_location = f's3://{output_bucket}/{output_prefix}'

        # Get S3 object metadata to extract correlation ID and mailbox
        try:
            s3_metadata_response = s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
            s3_metadata = s3_metadata_response.get('Metadata', {})
            correlation_id = s3_metadata.get('correlation-id', 'unknown')
            mailbox_id = s3_metadata.get('mailbox-id', 'unknown')
        except Exception as e:
            logger.warning("Failed to retrieve S3 metadata", extra={"error": str(e)})
            correlation_id = 'unknown'
            mailbox_id = 'unknown'

        logger.append_keys(
            correlation_id=correlation_id,
            mailbox_id=mailbox_id,
            input_s3_uri=document_s3_uri,
            output_s3_location=bda_s3_output_location,
            event_format=event_format
        )

        logger.info("Parsed S3 event",
                   extra={
                       "input_bucket": s3_bucket,
                       "input_key": s3_key,
                       "output_bucket": output_bucket
                   })

        # Get account ID
        account_id = sts_client.get_caller_identity()["Account"]
        logger.debug("Retrieved AWS account ID", extra={"account_id": account_id})

        # Get configuration from environment variables
        project_name = os.getenv("PROJECT_NAME", "Freight_Audit_Agent")
        data_automation_profile_arn = os.getenv(
            "DATA_AUTOMATION_PROFILE_ARN",
            f'arn:aws:bedrock:{region}:{account_id}:data-automation-profile/us.data-automation-v1'
        )

        logger.append_keys(project_name=project_name)

        # Get the project ARN by listing projects
        logger.info("Looking up Bedrock project", extra={"project_name": project_name})

        projects_response = bda_client.list_data_automation_projects(projectStageFilter='LIVE')
        project = next((p for p in projects_response.get('projects', [])
                      if p['projectName'] == project_name), None)

        if not project:
            error_msg = f"Project '{project_name}' not found"
            logger.error(error_msg,
                       extra={
                           "project_name": project_name,
                           "available_projects": [p['projectName'] for p in projects_response.get('projects', [])]
                       })

            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': error_msg,
                    'message': 'Ensure bedrock_blueprint_manager Lambda has been run to create the project'
                })
            }

        data_automation_project_arn = project['projectArn']
        logger.info("Found Bedrock project",
                   extra={"project_arn": data_automation_project_arn})

        # Start Bedrock async job
        logger.info("Starting Bedrock Data Automation job",
                   extra={
                       "profile_arn": data_automation_profile_arn,
                       "project_arn": data_automation_project_arn
                   })

        response = bda_runtime_client.invoke_data_automation_async(
            inputConfiguration={'s3Uri': document_s3_uri},
            outputConfiguration={'s3Uri': bda_s3_output_location},
            dataAutomationProfileArn=data_automation_profile_arn,
            dataAutomationConfiguration={'dataAutomationProjectArn': data_automation_project_arn},
            notificationConfiguration={'eventBridgeConfiguration': {'eventBridgeEnabled': True}}
        )

        invocation_arn = response["invocationArn"]

        logger.info("Bedrock job started successfully",
                   extra={"invocation_arn": invocation_arn})

        # Phase 1 metrics
        metrics.add_metric(name="BedrockJobsStarted", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Bedrock job started successfully',
                'invocation_arn': invocation_arn,
                'input_s3_uri': document_s3_uri,
                'output_s3_location': bda_s3_output_location,
                'input_bucket': s3_bucket,
                'input_key': s3_key,
                'output_bucket': output_bucket,
                'project_name': project_name,
                'project_arn': data_automation_project_arn,
                'timestamp': datetime.utcnow().isoformat()
            })
        }

    except Exception as e:
        error_msg = "Unexpected error processing invoice"
        logger.error(error_msg,
                    exc_info=True,
                    extra={"error": str(e)})

        # Phase 1 metrics (Note: BedrockJobErrors will be tracked in gvp_invoice_publisher)
        # This tracks job start failures only
        metrics.add_metric(name="BedrockJobsStarted", unit=MetricUnit.Count, value=0)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'error_details': str(e),
                'message': 'Failed to process invoice document'
            })
        }
