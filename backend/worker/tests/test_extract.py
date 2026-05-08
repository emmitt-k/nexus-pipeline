"""
Unit tests for extract.py - S3 data extraction.

Tests the extract module that reads CSV/JSON from S3.
"""

import pytest
import sys
sys.path.insert(0, '..')

from extract import parse_csv, parse_json


class TestParseCSV:
    """Tests for CSV parsing."""

    def test_parse_simple_csv(self):
        """Test parsing a simple CSV."""

        csv_data = b"name,email,age\nJohn Doe,john@example.com,30\nJane Smith,jane@test.com,25"

        result = parse_csv(csv_data)

        assert len(result) == 2
        assert result[0]["name"] == "John Doe"
        assert result[0]["email"] == "john@example.com"
        assert result[0]["age"] == "30"

    def test_parse_csv_with_quotes(self):
        """Test parsing CSV with quoted fields."""

        csv_data = b'name,email\n"John Doe","john@example.com"'

        result = parse_csv(csv_data)

        assert result[0]["name"] == "John Doe"

    def test_parse_empty_csv(self):
        """Test parsing empty CSV returns empty list."""

        result = parse_csv(b"")

        assert result == []

    def test_parse_single_row_csv(self):
        """Test parsing CSV with only header."""

        csv_data = b"name,email"

        result = parse_csv(csv_data)

        assert result == []


class TestParseJSON:
    """Tests for JSON parsing."""

    def test_parse_list_json(self):
        """Test parsing JSON array."""

        json_data = b'[{"name": "John", "email": "john@example.com", "age": 30}]'

        result = parse_json(json_data)

        assert len(result) == 1
        assert result[0]["name"] == "John"
        assert result[0]["age"] == 30

    def test_parse_nested_data_json(self):
        """Test parsing JSON with nested data key."""

        json_data = b'{"data": [{"name": "John"}, {"name": "Jane"}]}'

        result = parse_json(json_data)

        assert len(result) == 2
        assert result[0]["name"] == "John"

    def test_parse_single_object_json(self):
        """Test parsing JSON object (not array)."""

        json_data = b'{"name": "John", "email": "john@example.com"}'

        result = parse_json(json_data)

        assert len(result) == 1
        assert result[0]["name"] == "John"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises error."""

        import json

        with pytest.raises(json.JSONDecodeError):
            parse_json(b"not valid json")

    def test_parse_empty_json_array(self):
        """Test parsing empty JSON array."""

        result = parse_json(b"[]")

        assert result == []

    def test_parse_json_with_special_chars(self):
        """Test parsing JSON with special characters."""

        json_data = b'{"name": "John Doe", "address": "123 Main St, Apt 4"}'

        result = parse_json(json_data)

        assert result[0]["address"] == "123 Main St, Apt 4"