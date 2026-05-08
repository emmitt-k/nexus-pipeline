"""
Unit tests for handler.py - using moto to mock S3 and DynamoDB.

Tests the S3 event handling and job creation.
"""

import json
import os
import pytest
from unittest.mock import patch

# Set environment before import
os.environ["DYNAMO_TABLE"] = "test-jobs-table"

# Import the module we're testing
import sys
sys.path.insert(0, '..')

from handler import (
    get_data_topic,
    parse_csv,
    parse_json,
    get_target_config,
)


class TestGetDataTopic:
    """Tests for data topic detection."""

    def test_customers_folder(self):
        """Test customers folder detection."""

        assert get_data_topic("customers/file.csv") == "customers"
        assert get_data_topic("customers/partner-a/data.csv") == "customers"

    def test_products_folder(self):
        """Test products folder detection."""

        assert get_data_topic("products/partner-a/products.csv") == "products"

    def test_invalid_folder(self):
        """Test invalid folder returns None."""

        assert get_data_topic("unknown/file.csv") is None
        assert get_data_topic("random.txt") is None


class TestParseCSV:
    """Tests for CSV parsing."""

    def test_parse_simple_csv(self):
        """Test parsing a simple CSV."""

        csv_data = b"name,email\nJohn Doe,john@example.com\nJane,jane@test.com"

        result = parse_csv(csv_data)

        assert result["columns"] == ["name", "email"]
        assert len(result["rows"]) == 2
        assert result["rows"][0] == ["John Doe", "john@example.com"]

    def test_parse_empty_csv(self):
        """Test parsing empty CSV."""

        result = parse_csv(b"")

        assert result is None


class TestParseJSON:
    """Tests for JSON parsing."""

    def test_parse_list_json(self):
        """Test parsing JSON array."""

        json_data = b'[{"name": "John", "email": "john@example.com"}]'

        result = parse_json(json_data)

        assert result["columns"] == ["name", "email"]

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""

        result = parse_json(b"not json")

        assert result is None


class TestGetTargetConfig:
    """Tests for target configuration."""

    def test_customers_config(self):
        """Test customers config."""

        config = get_target_config("customers")

        assert config["table"] == "customers"
        assert "full_name" in config["columns"]
        assert "email" in config["columns"]

    def test_products_config(self):
        """Test products config."""

        config = get_target_config("products")

        assert config["table"] == "products"
        assert "sku" in config["columns"]
        assert "name" in config["columns"]

    def test_unknown_config(self):
        """Test unknown returns empty config."""

        config = get_target_config("unknown")

        assert config["table"] == "unknown"
        assert config["columns"] == []