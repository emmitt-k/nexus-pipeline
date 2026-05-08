"""
Unit tests for bedrock.py - using moto to mock Bedrock.

Tests the AI mapping prompt generation and response parsing.
"""

import json
import pytest
from unittest.mock import patch

# Import the module we're testing
import sys
sys.path.insert(0, '..')

from bedrock import (
    build_mapping_prompt,
    parse_ai_response,
    call_bedrock_for_mapping
)


class TestBuildMappingPrompt:
    """Tests for prompt building."""

    def test_build_prompt_with_columns(self):
        """Test prompt is generated correctly."""

        prompt = build_mapping_prompt(
            target_table="customers",
            target_columns=["id", "full_name", "email"],
            source_columns=["cust_name", "email_addr"],
            sample_rows=[
                ["John Doe", "john@example.com"],
                ["Jane Smith", "jane@test.com"]
            ]
        )

        assert "customers" in prompt
        assert "cust_name" in prompt
        assert "email_addr" in prompt

    def test_prompt_includes_example(self):
        """Test prompt includes clear example."""

        prompt = build_mapping_prompt(
            target_table="customers",
            target_columns=["full_name", "email"],
            source_columns=["name", "email"],
            sample_rows=[["Test", "test@test.com"]]
        )

        assert "EXAMPLE" in prompt
        assert "schema_mapping" in prompt


class TestParseAIResponse:
    """Tests for AI response parsing."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""

        response = '''{
          "schema_mapping": {"cust_name": "full_name"},
          "transform_spec": {"full_name": {"transform": "titlecase"}},
          "confidence": 0.95
        }'''

        result = parse_ai_response(response)

        assert result["schema_mapping"] == {"cust_name": "full_name"}
        assert result["confidence"] == 0.95

    def test_parse_json_with_text_around(self):
        """Test parsing JSON with extra text."""

        response = '''Here is the mapping:
        {
          "schema_mapping": {"name": "full_name"},
          "confidence": 0.9
        }
        Thank you!'''

        result = parse_ai_response(response)

        assert result["schema_mapping"] == {"name": "full_name"}

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns empty."""

        result = parse_ai_response("not valid json at all")

        assert result["schema_mapping"] == {}
        assert result["confidence"] == 0


class TestCallBedrockForMapping:
    """Tests for Bedrock API call."""

    @patch('bedrock.bedrock')
    def test_call_returns_mapping(self, mock_bedrock):
        """Test API call returns parsed mapping."""

        # Mock Bedrock response
        mock_response = {
            "output": {
                "message": {
                    "content": [{
                        "text": json.dumps({
                            "schema_mapping": {"n": "full_name"},
                            "transform_spec": {},
                            "confidence": 0.95
                        })
                    }]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response

        result = call_bedrock_for_mapping(
            target_table="customers",
            target_columns=["full_name"],
            source_columns=["n"],
            sample_rows=[["John"]]
        )

        assert result["schema_mapping"] == {"n": "full_name"}
        mock_bedrock.converse.assert_called_once()


    @patch('bedrock.bedrock')
    def test_call_handles_error(self, mock_bedrock):
        """Test API error returns error dict."""

        mock_bedrock.converse.side_effect = Exception("API Error")

        result = call_bedrock_for_mapping(
            target_table="customers",
            target_columns=["name"],
            source_columns=["n"],
            sample_rows=[["John"]]
        )

        assert "error" in result