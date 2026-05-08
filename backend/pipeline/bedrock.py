"""
Bedrock AI client for column mapping.

Sends target schema + source columns to AI, gets back mapping.
"""

import json
import os

import boto3

bedrock = boto3.client("bedrock-runtime")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")


def call_bedrock_for_mapping(target_table, target_columns, source_columns, sample_rows):
    """
    Call Bedrock AI to map source columns to target columns.

    Args:
        target_table: Name of target table (e.g., "customers")
        target_columns: List of target column names
        source_columns: List of source column names from file
        sample_rows: List of rows with sample data

    Returns:
        {
            "schema_mapping": {"source_col": "target_col"},
            "transform_spec": {"target_col": {"transform": "..."}},
            "confidence": 0.95
        }
    """

    prompt = build_mapping_prompt(
        target_table=target_table,
        target_columns=target_columns,
        source_columns=source_columns,
        sample_rows=sample_rows
    )

    try:
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={
                "maxTokens": 2048,
                "temperature": 0.1
            }
        )

        response_text = response["output"]["message"]["content"][0]["text"]

        return parse_ai_response(response_text)

    except Exception as e:
        print(f"Bedrock error: {e}")
        return {
            "schema_mapping": {},
            "transform_spec": {},
            "confidence": 0,
            "error": str(e)
        }


def build_mapping_prompt(target_table, target_columns, source_columns, sample_rows):
    """
    Build the prompt for the AI with clear examples.
    """

    # Format sample rows as table-like display
    sample_lines = []
    for row in sample_rows[:3]:
        sample_lines.append("| " + " | ".join(str(v) for v in row) + " |")

    sample_text = "\n".join(sample_lines)

    prompt = f"""You are a data column mapping expert.

Given a source file with columns, map each source column to the target table column that best fits.

TARGET TABLE: {target_table}
TARGET COLUMNS: {target_columns}

SOURCE FILE:
Source columns: {source_columns}
Sample data (first 3 rows):
{sample_text}

YOUR JOB:
1. Match each source column to ONE target column
2. Decide if transformation is needed

MAPPING RULES:
- If column names are similar (e.g., "cust_name" and "full_name"), they match
- Use your best judgment for unclear columns

TRANSFORMATION RULES (only if needed):
- "uppercase": convert to UPPER CASE
- "lowercase": convert to lowercase
- "titlecase": Title Case
- "type: number": convert to number
- "type: boolean": convert to true/false (yes/no/1/0 → true)
- "format: YYYY-MM-DD": convert date format
- "mask: ###-####": add mask (e.g., 5551234 → 555-1234)
- "default: N/A": use default if empty

OUTPUT FORMAT (JSON only):
{{
  "schema_mapping": {{
    "source_column": "target_column"
  }},
  "transform_spec": {{
    "target_column": {{
      "transform": "uppercase",
      "type": "number",
      "format": "YYYY-MM-DD"
    }}
  }},
  "confidence": 0.95
}}

EXAMPLE - If source file has:
Source columns: ["cust_nm", "email_addr", "signup_dt"]
Target table: customers (has: full_name, email, created_at, is_active)

Then output:
{{
  "schema_mapping": {{
    "cust_nm": "full_name",
    "email_addr": "email",
    "signup_dt": "created_at"
  }},
  "transform_spec": {{
    "full_name": {{"transform": "titlecase"}},
    "email": {{"transform": "lowercase"}},
    "created_at": {{"format": "YYYY-MM-DD"}}
  }},
  "confidence": 0.9
}}

Respond ONLY with valid JSON, no text before or after."""

    return prompt


def parse_ai_response(response_text):
    """Parse AI response to extract mapping."""

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to find JSON in response
        start = response_text.find("{")
        end = response_text.rfind("}")

        if start >= 0 and end > start:
            try:
                return json.loads(response_text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return {
            "schema_mapping": {},
            "transform_spec": {},
            "confidence": 0
        }