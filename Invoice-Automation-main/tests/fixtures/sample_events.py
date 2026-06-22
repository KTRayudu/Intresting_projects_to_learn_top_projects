"""
Sample event payloads for testing Lambda functions
"""


def get_s3_eventbridge_event(bucket="test-bucket", key="Invoices/test-invoice.pdf"):
    """
    EventBridge S3 notification event format

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        dict: EventBridge S3 event
    """
    return {
        "version": "0",
        "id": "test-event-id-12345",
        "detail-type": "Object Created",
        "source": "aws.s3",
        "account": "123456789012",
        "time": "2024-01-15T10:30:00Z",
        "region": "us-east-1",
        "resources": [f"arn:aws:s3:::{bucket}"],
        "detail": {
            "version": "0",
            "bucket": {
                "name": bucket
            },
            "object": {
                "key": key,
                "size": 102400,
                "etag": "test-etag-abc123",
                "sequencer": "test-sequencer-xyz789"
            },
            "request-id": "test-request-id",
            "requester": "123456789012",
            "source-ip-address": "10.0.0.1",
            "reason": "PutObject"
        }
    }


def get_s3_native_event(bucket="test-bucket", key="Invoices/test-invoice.pdf"):
    """
    Native S3 event notification format

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        dict: Native S3 event
    """
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "2024-01-15T10:30:00.000Z",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "test-config-id",
                    "bucket": {
                        "name": bucket,
                        "arn": f"arn:aws:s3:::{bucket}"
                    },
                    "object": {
                        "key": key,
                        "size": 102400,
                        "eTag": "test-etag-abc123",
                        "sequencer": "test-sequencer-xyz789"
                    }
                }
            }
        ]
    }


def get_bedrock_completion_event(
    input_bucket="test-bucket",
    input_key="Invoices/test-invoice.pdf",
    output_bucket="test-bucket",
    output_key="lambda-output/test-job-id"
):
    """
    Bedrock Data Automation completion event

    Args:
        input_bucket: Input S3 bucket
        input_key: Input S3 key
        output_bucket: Output S3 bucket
        output_key: Output S3 key prefix

    Returns:
        dict: Bedrock completion event
    """
    return {
        "version": "0",
        "id": "bedrock-event-id-12345",
        "detail-type": "Bedrock Data Automation Job State Change",
        "source": "aws.bedrock-data-automation-runtime",
        "account": "123456789012",
        "time": "2024-01-15T10:35:00Z",
        "region": "us-east-1",
        "resources": [
            "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/test-project"
        ],
        "detail": {
            "invocation_arn": "arn:aws:bedrock:us-east-1:123456789012:invocation/test-invocation-id",
            "status": "SUCCEEDED",
            "input_s3_object": {
                "s3_bucket": input_bucket,
                "name": input_key
            },
            "output_s3_location": {
                "s3_bucket": output_bucket,
                "name": output_key
            },
            "data_automation_project_arn": "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/test-project",
            "timestamp": "2024-01-15T10:35:00.000Z"
        }
    }


def get_eventbridge_scheduler_event():
    """
    EventBridge Scheduler event (triggers email poller)

    Returns:
        dict: EventBridge Scheduler event
    """
    return {
        "version": "0",
        "id": "scheduler-event-id-12345",
        "detail-type": "Scheduled Event",
        "source": "aws.scheduler",
        "account": "123456789012",
        "time": "2024-01-15T10:30:00Z",
        "region": "us-east-1",
        "resources": [
            "arn:aws:scheduler:us-east-1:123456789012:schedule/default/invoice-email-poller-schedule"
        ],
        "detail": {}
    }
