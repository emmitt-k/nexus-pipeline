"""
Pipeline Lambda - S3 trigger + AI Column Mapping

Handle S3 upload events:
1. Determine data topic from S3 folder (products/, customers/, etc.)
2. Read sample data from file
3. Call Bedrock AI for column mapping
4. Save job to DynamoDB (status: pending_approval)
"""

import json
import os

import boto3

from bedrock import call_bedrock_for_mapping

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DYNAMO_TABLE"])


def handler(event, context):
    """
    Lambda entry point - handles S3 object created events.
    """

    # Handle S3 event
    for record in event.get("Records", []):
        if "s3" in record:
            result = handle_s3_event(record["s3"])
            if result:
                return result

    return {"statusCode": 200, "body": json.dumps({"message": "No files processed"})}


def handle_s3_event(s3_event):
    """
    Process a single S3 event.
    """

    bucket = s3_event["bucket"]["name"]
    key = s3_event["object"]["key"]

    # Determine data topic from S3 folder
    data_topic = get_data_topic(key)

    if not data_topic:
        return {"statusCode": 400, "body": json.dumps({"error": "Unknown data topic"})}

    # Read sample data from S3
    sample_data = read_sample_from_s3(bucket, key)

    if not sample_data:
        return {"statusCode": 400, "body": json.dumps({"error": "Could not read file"})}

    # Get target table config
    target_config = get_target_config(data_topic)

    # Check schema cache first
    from cache import get_cached_mapping
    cached = get_cached_mapping(data_topic, sample_data["columns"])

    if cached:
        # Use cached mapping
        mapping_result = cached
    else:
        # Call AI for column mapping
        mapping_result = call_bedrock_for_mapping(
            target_table=target_config["table"],
            target_columns=target_config["columns"],
            source_columns=sample_data["columns"],
            sample_rows=sample_data["rows"]
        )

    # Save job to DynamoDB
    job_id = save_job(
        data_topic=data_topic,
        target_table=target_config["table"],
        file_key=f"s3://{bucket}/{key}",
        source_columns=sample_data["columns"],
        mapping_result=mapping_result
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "jobId": job_id,
            "dataTopic": data_topic,
            "targetTable": target_config["table"],
            "status": "pending_approval"
        })
    }


def get_data_topic(key):
    """
    Determine data topic from S3 key.

    Example: customers/partner-a/file.csv -> customers
    """

    parts = key.strip("/").split("/")

    if len(parts) >= 1:
        topic = parts[0]

        valid_topics = ["products", "customers", "orders", "inventory"]

        if topic in valid_topics:
            return topic

    return None


def read_sample_from_s3(bucket, key):
    """
    Read first 5 rows from S3 file.
    Returns: {"columns": [...], "rows": [...]}
    """

    s3 = boto3.client("s3")

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        body = response["Body"].read()

        # Determine file type
        if key.endswith(".csv"):
            return parse_csv(body)
        elif key.endswith(".json"):
            return parse_json(body)
        else:
            return None

    except Exception as e:
        print(f"Error reading S3: {e}")
        return None


def parse_csv(body):
    """Parse CSV and return columns + sample rows."""

    import csv
    import io

    # Handle empty body
    if not body or not body.strip():
        return None

    text = body.decode("utf-8")
    reader = csv.reader(io.StringIO(text))

    # First row is header
    try:
        columns = next(reader)
    except StopIteration:
        return None

    # Next 5 rows are sample
    rows = []
    for i, row in enumerate(reader):
        if i >= 5:
            break
        rows.append(row)

    return {"columns": columns, "rows": rows}


def parse_json(body):
    """Parse JSON and return columns + sample rows."""

    import json

    # Handle empty body
    if not body or not body.strip():
        return None

    try:
        data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return None

    if isinstance(data, list) and len(data) > 0:
        columns = list(data[0].keys())
        rows = [list(row.values()) for row in data[:5]]
        return {"columns": columns, "rows": rows}

    return None


def get_target_config(data_topic):
    """
    Get target table configuration.
    """

    configs = {
        "products": {
            "table": "products",
            "columns": ["id", "sku", "name", "description", "category", "price", "cost", "quantity", "is_active", "created_at", "updated_at"]
        },
        "customers": {
            "table": "customers",
            "columns": ["id", "customer_code", "full_name", "email", "phone", "company", "address", "city", "country", "is_active", "created_at", "updated_at"]
        },
        "orders": {
            "table": "orders",
            "columns": ["id", "order_id", "customer_id", "product_id", "quantity", "unit_price", "total_price", "status", "order_date", "shipped_date", "created_at", "updated_at"]
        },
        "inventory": {
            "table": "inventory",
            "columns": ["id", "sku", "location", "quantity", "reserved_quantity", "available_quantity", "last_restocked", "created_at", "updated_at"]
        }
    }

    return configs.get(data_topic, {"table": data_topic, "columns": []})


def save_job(data_topic, target_table, file_key, source_columns, mapping_result):
    """
    Save job to DynamoDB.
    """

    import uuid
    from datetime import datetime, timezone

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    table.put_item(Item={
        "jobId": job_id,
        "dataTopic": data_topic,
        "targetTable": target_table,
        "fileKey": file_key,
        "sourceColumns": source_columns,
        "schemaMapping": mapping_result.get("schema_mapping", {}),
        "transformSpec": mapping_result.get("transform_spec", {}),
        "confidence": mapping_result.get("confidence", 0),
        "status": "pending_approval",
        "createdAt": now,
        "updatedAt": now,
        "ttl": int(datetime.now(timezone.utc).timestamp()) + 86400
    })

    return job_id