"""
Worker ECS Task - ETL (Extract, Transform, Load) execution.

Consumes from SQS queue when a job is approved:
1. Read file from S3
2. Apply column mapping + transformations
3. Load to PostgreSQL
"""

import json
import os
from datetime import datetime, timezone

import boto3

# AWS clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE", "nexus-jobs-dev")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")

table = dynamodb.Table(DYNAMO_TABLE)


def handler(event, context):
    """
    Main entry point - handles SQS messages.

    Args:
        event: SQS event with job messages

    Returns:
        Processed message count
    """

    processed = 0

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            job_id = body.get("jobId")

            if job_id:
                process_job(job_id)

                # Delete message on success
                sqs.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=record["receiptHandle"]
                )
                processed += 1

        except Exception as e:
            print(f"Error processing message: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({"processed": processed})
    }


def process_job(job_id):
    """Process a single ETL job."""

    print(f"Processing job: {job_id}")

    # Get job from DynamoDB
    job = get_job(job_id)

    if not job:
        print(f"Job not found: {job_id}")
        return

    # Only process approved jobs
    if job.get("status") != "approved":
        print(f"Job not approved, status: {job.get('status')}")
        return

    # Start processing
    update_status(job_id, "processing")

    try:
        # Get file info
        file_key = job["fileKey"]
        file_type = job.get("fileType", "csv")
        if not file_type:
            file_type = "csv" if file_key.endswith(".csv") else "json"

        # Step 1: Extract from S3
        from extract import extract_from_s3
        data = extract_from_s3(file_key, file_type)

        if not data:
            raise ValueError("No data extracted from file")

        # Step 2: Apply transformations
        from transform import transform_data
        schema_mapping = job.get("schemaMapping", {})
        transform_spec = job.get("transformSpec", {})
        data = transform_data(data, schema_mapping, transform_spec)

        # Step 3: Load to PostgreSQL
        target_table = job.get("targetTable", "jobs")
        from load import load_to_postgres
        rows_loaded = load_to_postgres(data, target_table)

        # Success!
        update_status(job_id, "completed")

        print(f"Job {job_id} completed: {rows_loaded} rows loaded")

    except Exception as e:
        # Failure - log error and update status
        update_status(job_id, "failed", str(e))
        print(f"Job {job_id} failed: {e}")
        raise


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------

def get_job(job_id):
    """Get job from DynamoDB."""

    response = table.get_item(Key={"jobId": job_id})
    return response.get("Item")


def update_status(job_id, status, error_message=None):
    """Update job status in DynamoDB."""

    now = datetime.now(timezone.utc).isoformat()

    expr = "SET #status = :status, updatedAt = :now"
    values = {":status": status, ":now": now}

    if error_message:
        expr += ", errorMessage = :error"
        values[":error"] = error_message

    table.update_item(
        Key={"jobId": job_id},
        UpdateExpression=expr,
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues=values
    )


def approve_job(job_id):
    """Approve job - set status to approved and send to SQS queue."""

    job = get_job(job_id)

    if not job:
        return error_response(404, "Job not found")

    if job.get("status") != "pending_approval":
        return error_response(400, f"Job not pending approval, status: {job.get('status')}")

    # Update to approved
    update_status(job_id, "approved")

    # Send to SQS queue
    sqs_client = boto3.client("sqs")
    sqs_client.send_message(
        QueueUrl=os.environ.get("SQS_QUEUE_URL", ""),
        MessageBody=json.dumps({"jobId": job_id})
    )

    return success_response({"jobId": job_id, "status": "approved"})


def reject_job(job_id):
    """Reject job - set status to rejected."""

    job = get_job(job_id)

    if not job:
        return error_response(404, "Job not found")

    if job.get("status") != "pending_approval":
        return error_response(400, f"Job not pending approval, status: {job.get('status')}")

    update_status(job_id, "rejected")

    return success_response({"jobId": job_id, "status": "rejected"})


def get_jobs(status=None, limit=50):
    """List jobs from DynamoDB with optional status filter."""

    from boto3.dynamodb.conditions import Attr

    kwargs = {"Limit": limit}

    if status:
        response = table.scan(
            FilterExpression=Attr("status").eq(status),
            **kwargs
        )
    else:
        response = table.scan(**kwargs)

    return response.get("Items", [])


def success_response(body):
    """Build success response."""

    return {
        "statusCode": 200,
        "body": json.dumps(body) if isinstance(body, dict) else body
    }


def error_response(status_code, message):
    """Build error response."""

    return {
        "statusCode": status_code,
        "body": json.dumps({"error": message})
    }