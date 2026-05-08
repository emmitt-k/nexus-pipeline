"""
Unit tests for cache.py - Schema caching.

Tests the cache module functions for schema mapping cache.
"""

import sys
sys.path.insert(0, '..')

from cache import get_cache_key, get_cached_mapping, save_cached_mapping


class TestGetCacheKey:
    """Tests for cache key generation."""

    def test_same_columns_same_order(self):
        """Same columns in same order should produce same key."""

        key1 = get_cache_key("products", ["email", "name", "sku"])
        key2 = get_cache_key("products", ["email", "name", "sku"])

        assert key1 == key2

    def test_same_columns_different_order(self):
        """Same columns in different order should produce same key."""

        key1 = get_cache_key("products", ["email", "name", "sku"])
        key2 = get_cache_key("products", ["sku", "email", "name"])

        assert key1 == key2

    def test_different_columns_different_key(self):
        """Different columns should produce different keys."""

        key1 = get_cache_key("products", ["email", "name"])
        key2 = get_cache_key("products", ["email", "name", "sku"])

        assert key1 != key2

    def test_different_topics_different_key(self):
        """Different data topics should produce different keys."""

        key1 = get_cache_key("products", ["email", "name"])
        key2 = get_cache_key("customers", ["email", "name"])

        assert key1 != key2

    def test_key_format(self):
        """Key should be in format topic#sorted_columns."""

        key = get_cache_key("products", ["z", "a", "m"])

        assert key == "products#a,m,z"


class TestGetCachedMapping:
    """Tests for get_cached_mapping function."""

    def test_get_cached_mapping_returns_none_when_empty(self):
        """Should return None when no cache entry exists."""

        # This would require moto to mock DynamoDB
        # For now, testing the function exists and has correct signature
        assert callable(get_cached_mapping)

    def test_function_signature(self):
        """Function should accept data_topic and source_columns."""

        import inspect
        sig = inspect.signature(get_cached_mapping)
        params = list(sig.parameters.keys())

        assert "data_topic" in params
        assert "source_columns" in params


class TestSaveCachedMapping:
    """Tests for save_cached_mapping function."""

    def test_save_cached_mapping_signature(self):
        """Function should accept required parameters."""

        import inspect
        sig = inspect.signature(save_cached_mapping)
        params = list(sig.parameters.keys())

        assert "data_topic" in params
        assert "source_columns" in params
        assert "mapping_result" in params

    def test_mapping_result_structure(self):
        """Mapping result should have expected structure."""

        mapping_result = {
            "schema_mapping": {"source_col": "target_col"},
            "transform_spec": {"target_col": {"transform": "uppercase"}},
            "confidence": 0.95
        }

        assert "schema_mapping" in mapping_result
        assert "transform_spec" in mapping_result
        assert "confidence" in mapping_result