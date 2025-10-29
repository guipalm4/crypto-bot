"""Unit tests for indicator cache."""

import pandas as pd
import pytest

from crypto_bot.plugins.indicators.cache import IndicatorCache, get_cache


class TestIndicatorCache:
    """Tests for IndicatorCache."""

    def test_cache_get_set(self) -> None:
        """Test basic get/set operations."""
        cache = IndicatorCache(maxsize=10)
        data = pd.DataFrame({"close": [100, 101, 102, 103, 104]})
        params = {"length": 14}
        result = pd.Series([50, 51, 52, 53, 54], name="RSI_14")

        # Should return None on miss
        assert cache.get("rsi", data, params) is None

        # Set and get
        cache.set("rsi", data, params, result)
        cached = cache.get("rsi", data, params)

        assert cached is not None
        assert isinstance(cached, pd.Series)
        pd.testing.assert_series_equal(cached, result)

    def test_cache_hit_miss(self) -> None:
        """Test cache hit and miss tracking."""
        cache = IndicatorCache(maxsize=10)
        data = pd.DataFrame({"close": [100, 101, 102]})
        params = {"length": 14}
        result = pd.Series([50, 51, 52], name="RSI_14")

        # Initial miss
        assert cache.get("rsi", data, params) is None
        assert cache._misses == 1
        assert cache._hits == 0

        # Set and get (hit)
        cache.set("rsi", data, params, result)
        cache.get("rsi", data, params)

        assert cache._hits == 1
        assert cache._misses == 1

    def test_cache_lru_eviction(self) -> None:
        """Test LRU eviction when cache is full."""
        cache = IndicatorCache(maxsize=2)
        data1 = pd.DataFrame({"close": [100]})
        data2 = pd.DataFrame({"close": [200]})
        data3 = pd.DataFrame({"close": [300]})
        params = {"length": 14}

        # Fill cache to maxsize
        cache.set("rsi", data1, params, pd.Series([1], name="RSI_14"))
        cache.set("ema", data2, params, pd.Series([2], name="EMA_14"))

        # Access data1 (make it more recently used)
        cache.get("rsi", data1, params)

        # Add new item - should evict data2 (least recently used)
        cache.set("sma", data3, params, pd.Series([3], name="SMA_14"))

        # data1 should still be cached
        assert cache.get("rsi", data1, params) is not None

        # data2 should be evicted
        assert cache.get("ema", data2, params) is None

    def test_cache_different_parameters(self) -> None:
        """Test that different parameters create different cache entries."""
        cache = IndicatorCache(maxsize=10)
        data = pd.DataFrame({"close": [100, 101, 102]})

        result1 = pd.Series([50, 51, 52], name="RSI_14")
        result2 = pd.Series([60, 61, 62], name="RSI_21")

        cache.set("rsi", data, {"length": 14}, result1)
        cache.set("rsi", data, {"length": 21}, result2)

        # Should get different results
        cached1 = cache.get("rsi", data, {"length": 14})
        cached2 = cache.get("rsi", data, {"length": 21})

        assert cached1 is not None
        assert cached2 is not None
        pd.testing.assert_series_equal(cached1, result1)
        pd.testing.assert_series_equal(cached2, result2)

    def test_cache_different_data(self) -> None:
        """Test that different data creates different cache entries."""
        cache = IndicatorCache(maxsize=10)
        data1 = pd.DataFrame({"close": [100, 101, 102]})
        data2 = pd.DataFrame({"close": [200, 201, 202]})
        params = {"length": 14}

        result1 = pd.Series([50, 51, 52], name="RSI_14")
        result2 = pd.Series([60, 61, 62], name="RSI_14")

        cache.set("rsi", data1, params, result1)
        cache.set("rsi", data2, params, result2)

        # Should get different results
        cached1 = cache.get("rsi", data1, params)
        cached2 = cache.get("rsi", data2, params)

        assert cached1 is not None
        assert cached2 is not None
        pd.testing.assert_series_equal(cached1, result1)
        pd.testing.assert_series_equal(cached2, result2)

    def test_cache_clear(self) -> None:
        """Test clearing the cache."""
        cache = IndicatorCache(maxsize=10)
        data = pd.DataFrame({"close": [100, 101, 102]})
        params = {"length": 14}

        cache.set("rsi", data, params, pd.Series([50, 51, 52], name="RSI_14"))
        assert cache.get("rsi", data, params) is not None

        cache.clear()

        assert len(cache) == 0
        assert cache.get("rsi", data, params) is None
        assert cache._hits == 0
        assert cache._misses == 1

    def test_cache_stats(self) -> None:
        """Test cache statistics."""
        cache = IndicatorCache(maxsize=10)
        data = pd.DataFrame({"close": [100, 101, 102]})
        params = {"length": 14}
        result = pd.Series([50, 51, 52], name="RSI_14")

        # Initial stats
        stats = cache.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

        # Add some activity
        cache.set("rsi", data, params, result)
        cache.get("rsi", data, params)  # hit
        cache.get("ema", data, params)  # miss

        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["maxsize"] == 10
        assert stats["hit_rate"] == "50.00%"

    def test_cache_returns_copy(self) -> None:
        """Test that cache returns copies to avoid mutable issues."""
        cache = IndicatorCache(maxsize=10)
        data = pd.DataFrame({"close": [100, 101, 102]})
        params = {"length": 14}
        result = pd.Series([50, 51, 52], name="RSI_14")

        cache.set("rsi", data, params, result)

        cached1 = cache.get("rsi", data, params)
        cached2 = cache.get("rsi", data, params)

        assert cached1 is not None
        assert cached2 is not None
        # Should be different objects (copies)
        assert cached1 is not cached2
        # But with same values
        pd.testing.assert_series_equal(cached1, cached2)

    def test_get_cache_singleton(self) -> None:
        """Test that get_cache returns a singleton instance."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2
