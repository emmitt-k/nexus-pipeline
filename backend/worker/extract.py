"""
Extract data from S3.

Reads CSV or JSON files from S3 and returns as list of dictionaries.
"""

import json

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def extract_from_s3(file_key, file_type):
    """
    Read file from S3 and return as list of dictionaries.

    Args:
        file_key: "s3://bucket/path/to/file.csv" or "bucket/path/to/file.csv"
        file_type: "csv" or "json"

    Returns:
        List of dictionaries with column names as keys
    """

    s3 = boto3.client("s3")

    # Parse s3://bucket/key format
    if file_key.startswith("s3://"):
        file_key = file_key[5:]

    bucket, key = file_key.split("/", 1)

    # Download file
    response = s3.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read()

    # Parse based on type
    if file_type == "csv":
        return parse_csv(body)
    elif file_type == "json":
        return parse_json(body)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def parse_csv(body_bytes):
    """
    Parse CSV bytes to list of dictionaries.

    Args:
        body_bytes: Raw CSV file content

    Returns:
        List of dicts like [{"column": "value"}, ...]
    """

    import csv
    import io

    text = body_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    return list(reader)


def parse_json(body_bytes):
    """
    Parse JSON bytes to list of dictionaries.

    Handles:
    - Array format: [{"a": 1}, {"a": 2}]
    - Object with data key: {"data": [{"a": 1}]}

    Args:
        body_bytes: Raw JSON file content

    Returns:
        List of dicts
    """

    data = json.loads(body_bytes.decode("utf-8"))

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "data" in data:
        return data["data"]
    else:
        return [data]