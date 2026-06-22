# AWS Lambda Powertools Guide

This Lambda function uses [AWS Lambda Powertools for Python](https://docs.powertools.aws.dev/lambda/python/) for observability.

## Features Enabled

### 1. **Structured Logging** (Logger)
- JSON-formatted logs automatically sent to CloudWatch Logs
- Request context automatically injected (request_id, function_name, etc.)
- Custom keys can be appended/removed during execution
- Full exception stack traces with `exc_info=True`

### 2. **Distributed Tracing** (Tracer)
- AWS X-Ray integration for end-to-end tracing
- Subsegments for key operations (auth, email fetching, PDF processing)
- Automatic cold start annotation
- Performance bottleneck identification

### 3. **Custom Metrics** (Metrics)
- CloudWatch custom metrics automatically published
- Namespace: `FreightAuditAgent`
- Service dimension: `invoice_email_poller`
- Metrics include counts, durations, sizes, and error rates

## Environment Variables

### Required
- Standard Lambda environment variables (set automatically)

### Optional Powertools Configuration
- `POWERTOOLS_SERVICE_NAME` - Service name for logs/traces (default: "invoice_email_poller")
- `POWERTOOLS_METRICS_NAMESPACE` - CloudWatch metrics namespace (default: "FreightAuditAgent")
- `POWERTOOLS_LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `POWERTOOLS_LOGGER_LOG_EVENT` - Log incoming event (default: true)
- `POWERTOOLS_TRACER_CAPTURE_RESPONSE` - Capture Lambda response in traces (default: true)
- `POWERTOOLS_TRACER_CAPTURE_ERROR` - Capture errors in traces (default: true)

### X-Ray Tracing
To enable X-Ray tracing, configure in Lambda console:
1. Go to Lambda function → Configuration → Monitoring
2. Enable "Active tracing"

## Metrics Published

All metrics are in the `FreightAuditAgent` namespace with dimension `service=invoice_email_poller`

### Success Metrics
- `EmailsProcessed` (Count) - Total emails marked as read
- `TotalPDFsUploaded` (Count) - PDFs successfully uploaded to S3
- `PDFUploaded` (Count) - Individual PDF uploads (incremented per PDF)
- `PDFSizeBytes` (Bytes) - Size of each uploaded PDF
- `UnreadEmailsFound` (Count) - Unread emails discovered

### Performance Metrics
- `AuthenticationDuration` (Seconds) - Microsoft Graph API auth time
- `EmailFetchDuration` (Seconds) - Time to fetch unread emails
- `EmailProcessingDuration` (Seconds) - Time to process each email
- `UploadDuration` (Seconds) - S3 upload time per PDF

### Skipped Items
- `InlineAttachmentsSkipped` (Count) - Inline attachments (signatures) skipped
- `NonPDFAttachmentsSkipped` (Count) - Non-PDF attachments skipped

### Error Metrics
- `ConfigurationError` (Count) - Missing environment variables
- `PDFProcessingError` (Count) - Errors processing PDF attachments
- `AttachmentRetrievalError` (Count) - Errors fetching attachment list
- `EmailProcessingError` (Count) - Errors processing entire email
- `FatalError` (Count) - Fatal Lambda execution errors
- `TotalErrors` (Count) - Sum of all errors in execution

### Cold Start Metric
- Automatically captured by `@metrics.log_metrics(capture_cold_start_metric=True)`
- Dimension: `function_context.cold_start=true/false`

## Viewing Data

### CloudWatch Logs
Go to: CloudWatch → Log groups → `/aws/lambda/invoice_email_poller`

**Sample structured log:**
```json
{
  "level": "INFO",
  "location": "lambda_handler:264",
  "message": "Successfully uploaded PDF to S3",
  "timestamp": "2025-11-10T12:34:56.789Z",
  "service": "invoice_email_poller",
  "cold_start": false,
  "function_name": "invoice_email_poller",
  "function_memory_size": 512,
  "function_arn": "arn:aws:lambda:us-east-1:123456789012:function:invoice_email_poller",
  "function_request_id": "abc-123-def",
  "email_id": "AAMkAGI...",
  "email_subject": "Invoice for November",
  "sender_email": "vendor@example.com",
  "s3_uri": "s3://bucket/Invoices/20251110_123456_invoice.pdf",
  "file_size_bytes": 245678,
  "duration_seconds": 2.34
}
```

### CloudWatch Logs Insights Queries

**Find all errors:**
```
fields @timestamp, level, message, error
| filter level = "ERROR"
| sort @timestamp desc
```

**Track specific email:**
```
fields @timestamp, message, s3_uri
| filter email_id = "EMAIL_ID_HERE"
| sort @timestamp asc
```

**View all uploaded PDFs:**
```
fields @timestamp, email_subject, sender_email, s3_uri, file_size_bytes
| filter message = "Successfully uploaded PDF to S3"
| sort @timestamp desc
```

### CloudWatch Metrics

Go to: CloudWatch → Metrics → FreightAuditAgent

**Create dashboard with:**
- PDFs uploaded per 5 minutes (Sum of `TotalPDFsUploaded`)
- Error rate (Sum of `TotalErrors`)
- Average processing duration (`EmailProcessingDuration`)
- Cold start frequency

**Create alarms for:**
- `TotalErrors` > 5 in 15 minutes
- `FatalError` > 0
- `PDFUploaded` = 0 for 1 hour (during business hours)

### X-Ray Traces

Go to: X-Ray → Traces → Service map

**View:**
- Service dependencies (Lambda → S3, Microsoft Graph API)
- Latency distribution
- Error rates by subsegment
- Cold start impact
- Slow operations

**Subsegments created:**
- `## authenticate_graph_api` - Microsoft Graph authentication
- `## fetch_unread_emails` - Fetching unread emails
- `## process_email_{idx}` - Processing each email
- `## process_pdf_{idx}` - Processing each PDF

## Code Examples

### Adding Custom Log Fields

```python
# Temporary context for specific operations
logger.info("Processing started", extra={
    "custom_field": "value",
    "count": 42
})

# Persistent context (added to all subsequent logs)
logger.append_keys(
    email_id="AAMkAGI...",
    sender="user@example.com"
)

# Remove persistent keys when done
logger.remove_keys(["email_id", "sender"])
```

### Adding Custom Metrics

```python
from aws_lambda_powertools.metrics import MetricUnit

# Count metric
metrics.add_metric(name="CustomEvent", unit=MetricUnit.Count, value=1)

# Duration metric
metrics.add_metric(name="OperationDuration", unit=MetricUnit.Seconds, value=2.5)

# Size metric
metrics.add_metric(name="DataSize", unit=MetricUnit.Bytes, value=1024)

# Custom dimension
metrics.add_dimension(name="Environment", value="Production")
```

### Adding Trace Subsegments

```python
# Trace a specific operation
with tracer.provider.in_subsegment("## my_custom_operation"):
    result = expensive_operation()

# Add annotations (indexed, for filtering)
tracer.put_annotation(key="user_type", value="premium")

# Add metadata (not indexed, for context)
tracer.put_metadata(key="response_data", value={"key": "value"})
```

### Exception Logging

```python
try:
    risky_operation()
except Exception as e:
    # Logs full stack trace automatically
    logger.error("Operation failed", exc_info=True, extra={
        "operation": "risky_operation",
        "error": str(e)
    })
    metrics.add_metric(name="OperationFailure", unit=MetricUnit.Count, value=1)
    raise  # Re-raise if needed
```

## Best Practices

1. **Use subsegments for expensive operations** - Helps identify bottlenecks
2. **Add business metrics** - Track business-specific KPIs
3. **Log at appropriate levels:**
   - DEBUG: Detailed diagnostic info
   - INFO: Normal operations
   - WARNING: Important but non-critical issues
   - ERROR: Errors that need attention
4. **Use `extra` parameter** - Add contextual fields to logs
5. **Append/remove keys** - Maintain context without repeating
6. **Set alarms on error metrics** - Proactive monitoring
7. **Create X-Ray filter expressions** - Track specific scenarios

## Debugging Tips

1. **Find slow requests:**
   - Go to X-Ray → Traces
   - Filter by `responsetime > 30` (seconds)
   - Identify slow subsegments

2. **Correlate logs with traces:**
   - Copy `function_request_id` from log
   - Search in X-Ray by trace ID

3. **Analyze metrics trends:**
   - Use CloudWatch Metrics Math
   - Calculate error rates: `errors / total * 100`
   - Set up anomaly detection

4. **Export logs for analysis:**
   - CloudWatch Logs Insights → Export results
   - Analyze in Excel/Python
   - Identify patterns

## Cost Considerations

- **Logs:** Pay per GB ingested and stored
- **Metrics:** Custom metrics charged per metric/month
- **X-Ray:** Pay per trace recorded and retrieved
- **Optimize:** Adjust `LOG_LEVEL` to reduce log volume

**Estimated costs (us-east-1):**
- Logs: $0.50/GB ingested, $0.03/GB stored
- Metrics: $0.30/custom metric/month
- X-Ray: $5 per million traces recorded

## Resources

- [Powertools Documentation](https://docs.powertools.aws.dev/lambda/python/)
- [Logger](https://docs.powertools.aws.dev/lambda/python/latest/core/logger/)
- [Tracer](https://docs.powertools.aws.dev/lambda/python/latest/core/tracer/)
- [Metrics](https://docs.powertools.aws.dev/lambda/python/latest/core/metrics/)
- [Best Practices](https://docs.powertools.aws.dev/lambda/python/latest/core/metrics/#best-practices)
