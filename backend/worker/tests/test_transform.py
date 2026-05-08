"""
Unit tests for transform.py - data transformation and column mapping.

Tests the transformation engine that applies column mapping and value transforms.
"""

import sys
sys.path.insert(0, '..')

from transform import (
    transform_data,
    apply_transforms,
    parse_boolean,
    parse_date,
    apply_mask,
)


class TestTransformData:
    """Tests for the main transform_data function."""

    def test_transform_with_schema_mapping(self):
        """Test basic column mapping."""

        data = [
            {"cust_name": "John Doe", "cust_email": "john@example.com"},
            {"cust_name": "Jane Smith", "cust_email": "jane@test.com"}
        ]

        schema_mapping = {
            "cust_name": "full_name",
            "cust_email": "email"
        }

        result = transform_data(data, schema_mapping, {})

        assert result[0]["full_name"] == "John Doe"
        assert result[0]["email"] == "john@example.com"
        assert "cust_name" not in result[0]

    def test_transform_with_transform_spec(self):
        """Test value transformations."""

        data = [{"name": "john doe", "email": "JOHN@EXAMPLE.COM"}]

        schema_mapping = {"name": "full_name", "email": "email"}
        transform_spec = {
            "full_name": {"transform": "titlecase"},
            "email": {"transform": "lowercase"}
        }

        result = transform_data(data, schema_mapping, transform_spec)

        assert result[0]["full_name"] == "John Doe"
        assert result[0]["email"] == "john@example.com"

    def test_transform_empty_data(self):
        """Test empty list returns empty."""

        result = transform_data([], {}, {})

        assert result == []

    def test_transform_unmapped_columns_pass_through(self):
        """Test columns not in mapping are passed through."""

        data = [{"col_a": "value_a", "col_b": "value_b"}]

        result = transform_data(data, {"col_a": "new_a"}, {})

        assert result[0]["new_a"] == "value_a"
        assert result[0]["col_b"] == "value_b"


class TestApplyTransforms:
    """Tests for apply_transforms function."""

    def test_uppercase_transform(self):
        """Test uppercase transformation."""

        result = apply_transforms("hello", {"transform": "uppercase"})

        assert result == "HELLO"

    def test_lowercase_transform(self):
        """Test lowercase transformation."""

        result = apply_transforms("HELLO", {"transform": "lowercase"})

        assert result == "hello"

    def test_titlecase_transform(self):
        """Test titlecase transformation."""

        result = apply_transforms("john doe", {"transform": "titlecase"})

        assert result == "John Doe"

    def test_type_number(self):
        """Test number conversion."""

        result = apply_transforms("123.45", {"type": "number"})

        assert result == 123.45

    def test_type_number_integer(self):
        """Test number conversion to integer."""

        result = apply_transforms("123.45", {"type": "number", "integer": True})

        assert result == 123

    def test_type_boolean_true_values(self):
        """Test boolean parsing for truthy values."""

        for value in ["true", "yes", "1", "on", "enabled"]:
            assert apply_transforms(value, {"type": "boolean"}) is True

    def test_type_boolean_false_values(self):
        """Test boolean parsing for falsy values."""

        for value in ["false", "no", "0", "off", "disabled", ""]:
            assert apply_transforms(value, {"type": "boolean"}) is False

    def test_mask_pattern(self):
        """Test masking."""

        result = apply_transforms("5551234", {"mask": "###-####"})

        assert result == "555-1234"

    def test_default_value_for_empty(self):
        """Test default value when input is empty."""

        result = apply_transforms("", {"default": "N/A"})

        assert result == "N/A"

    def test_null_returns_default(self):
        """Test null value returns default."""

        result = apply_transforms(None, {"default": "DEFAULT"})

        assert result == "DEFAULT"


class TestParseBoolean:
    """Tests for parse_boolean function."""

    def test_parse_true_strings(self):
        """Test parsing various true strings."""

        assert parse_boolean("true") is True
        assert parse_boolean("yes") is True
        assert parse_boolean("1") is True
        assert parse_boolean("on") is True

    def test_parse_false_strings(self):
        """Test parsing various false strings."""

        assert parse_boolean("false") is False
        assert parse_boolean("no") is False
        assert parse_boolean("0") is False

    def test_parse_strips_whitespace(self):
        """Test whitespace is stripped."""

        assert parse_boolean("  true  ") is True

    def test_parse_invalid_returns_none(self):
        """Test invalid string returns None."""

        assert parse_boolean("maybe") is None


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_iso_format(self):
        """Test ISO date format."""

        result = parse_date("2024-01-15")

        assert result == "2024-01-15"

    def test_parse_us_format(self):
        """Test US date format."""

        result = parse_date("01/15/2024")

        assert result == "2024-01-15"

    def test_parse_eu_format(self):
        """Test EU date format."""

        result = parse_date("15/01/2024")

        assert result == "2024-01-15"

    def test_parse_custom_format(self):
        """Test custom format parsing."""

        result = parse_date("15-Jan-2024", "DD-MMM-YYYY")

        assert result == "2024-01-15"

    def test_parse_invalid_returns_original(self):
        """Test invalid date returns original."""

        result = parse_date("not-a-date")

        assert result == "not-a-date"


class TestApplyMask:
    """Tests for apply_mask function."""

    def test_phone_mask(self):
        """Test phone number masking."""

        result = apply_mask("5551234", "###-####")

        assert result == "555-1234"

    def test_mask_with_extra_chars(self):
        """Test mask with extra characters."""

        result = apply_mask("5551234567", "(###) ###-####")

        assert result == "(555) 123-4567"

    def test_mask_short_value(self):
        """Test mask with shorter value than pattern."""

        result = apply_mask("123", "###-####")

        assert result == "123-####"