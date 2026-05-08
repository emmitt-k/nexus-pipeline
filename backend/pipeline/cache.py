"""
Schema cache for column mappings.

Caches approved schema mappings to avoid repeated Bedrock AI calls
for the same source columns.
"""

import os
import json
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr


def get_cache_key(data_topic, source_columns):
    """
    Generate cache key from data topic and source columns.

    Uses sorted columns to handle different column orderings.
    """
    sorted_cols = ",".join(sorted(source_columns))
    return f"{data_topic}#{sorted_cols}"


def get_cached_mapping(data_topic, source_columns):
    """
    Look up cached mapping for source columns.

    Args:
        data_topic: Target data topic (products, customers, etc.)
        source_columns: List of source column names

    Returns:
        Cached mapping dict or None if not found
    """
    cache_key = get_cache_key(data_topic, source_columns)

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ.get("SCHEMA_CACHE_TABLE", "nexus-schema-cache-dev"))

    try:
        response = table.get_item(Key={"cacheKey": cache_key})
        item = response.get("Item")

        if item:
            print(f"Cache hit for: {cache_key}")
            return {
                "schema_mapping": item.get("schemaMapping", {}),
                "transform_spec": item.get("transformSpec", {}),
                "confidence": item.get("confidence", 0),
                "mapping_source": "cache"
            }

        print(f"Cache miss for: {cache_key}")
        return None

    except Exception as e:
        print(f"Cache lookup error: {e}")
        return None


def save_cached_mapping(data_topic, source_columns, mapping_result):
    """
    Save approved mapping to cache.

    Args:
        data_topic: Target data topic
        source_columns: List of source column names
        mapping_result: Dict with schema_mapping, transform_spec, confidence
    """
    cache_key = get_cache_key(data_topic, source_columns)

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ.get("SCHEMA_CACHE_TABLE", "nexus-schema-cache-dev"))

    now = datetime.now(timezone.utc)

    try:
        table.put_item(Item={
            "cacheKey": cache_key,
            "dataTopic": data_topic,
            "sourceColumns": source_columns,
            "schemaMapping": mapping_result.get("schema_mapping", {}),
            "transformSpec": mapping_result.get("transform_spec", {}),
            "confidence": mapping_result.get("confidence", 0),
            "cachedAt": now.isoformat(),
            "ttl": int(now.timestamp()) + (90 * 24 * 60 * 60)  # 90 days TTL
        })
        print(f"Cached mapping for: {cache_key}")

    except Exception as e:
        print(f"Cache save error: {e}")


def clear_cache_for_topic(data_topic):
    """Clear all cached mappings for a data topic."""

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ.get("SCHEMA_CACHE_TABLE", "nexus-schema-cache-dev"))

    try:
        # Scan for items with this data topic
        response = table.scan(
            FilterExpression=Attr("dataTopic").eq(data_topic)
        )

        for item in response.get("Items", []):
            table.delete_item(Key={"cacheKey": item["cacheKey"]})

        print(f"Cleared cache for topic: {data_topic}")

    except Exception as e:
        print(f"Cache clear error: {e}")