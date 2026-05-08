"""
Dashboard API Lambda.

Provides REST API for dashboard to:
- List jobs
- Get job details
- Approve/reject jobs
"""

import json
import os

import boto3

# Dashboard-specific imports from worker handler
sys_path = os.path.join(os.path.dirname(__file__), "..", "worker")
import sys
sys.path.insert(0, sys_path)

from worker.handler import get_job, get_jobs, approve_job, reject_job, error_response


# Initialize clients
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DYNAMO_TABLE"])


def handler(event, context):
    """
    API Gateway Lambda handler.

    Routes based on HTTP method and path:
    - GET /jobs -> list_jobs
    - GET /jobs/{jobId} -> get_job_details
    - POST /jobs/{jobId}/approve -> approve_job_handler
    - POST /jobs/{jobId}/reject -> reject_job_handler
    """

    # Get request details
    http_method = event.get("httpMethod")
    path = event.get("path", "")
    query_params = event.get("queryStringParameters") or {}

    # Route to handler
    try:
        # GET /jobs
        if http_method == "GET" and path == "/jobs":
            return list_jobs(event, context)

        # GET /jobs/{jobId}
        if http_method == "GET" and path.startswith("/jobs/"):
            job_id = path.split("/")[2]
            return get_job_details(event, context, job_id)

        # POST /jobs/{jobId}/approve
        if http_method == "POST" and path.endswith("/approve"):
            job_id = path.split("/")[2]
            return handle_approve(event, context, job_id)

        # POST /jobs/{jobId}/reject
        if http_method == "POST" and path.endswith("/reject"):
            job_id = path.split("/")[2]
            return handle_reject(event, context, job_id)

        # No match
        return error_response(404, "Not found")

    except Exception as e:
        print(f"API Error: {e}")
        return error_response(500, str(e))


def list_jobs(event, context):
    """GET /jobs - List all jobs with optional status filter."""

    query_params = event.get("queryStringParameters") or {}
    status = query_params.get("status")
    limit = int(query_params.get("limit", 50))

    jobs = get_jobs(status=status, limit=limit)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(jobs)
    }


def get_job_details(event, context, job_id):
    """GET /jobs/{jobId} - Get job details."""

    job = get_job(job_id)

    if not job:
        return error_response(404, "Job not found")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(job)
    }


def handle_approve(event, context, job_id):
    """POST /jobs/{jobId}/approve - Approve job."""

    # Get job details before approval
    job = get_job(job_id)

    result = approve_job(job_id)

    # Save to cache after successful approval
    if result.get("statusCode") == 200 and job:
        try:
            # Import from backend path
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
            from cache import save_cached_mapping

            save_cached_mapping(
                data_topic=job.get("dataTopic", ""),
                source_columns=job.get("sourceColumns", []),
                mapping_result={
                    "schema_mapping": job.get("schemaMapping", {}),
                    "transform_spec": job.get("transformSpec", {}),
                    "confidence": job.get("confidence", 0)
                }
            )
        except Exception as e:
            print(f"Cache save error: {e}")

    return {
        "statusCode": result.get("statusCode", 200),
        "headers": {"Content-Type": "application/json"},
        "body": result.get("body", "{}")
    }


def handle_reject(event, context, job_id):
    """POST /jobs/{jobId}/reject - Reject job."""

    result = reject_job(job_id)

    return {
        "statusCode": result.get("statusCode", 200),
        "headers": {"Content-Type": "application/json"},
        "body": result.get("body", "{}")
    }