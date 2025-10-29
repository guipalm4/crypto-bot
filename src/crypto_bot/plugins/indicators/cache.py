"""LRU cache for computed technical indicators.

This module provides a caching mechanism that stores computed indicator results
using a hash of input parameters and data to avoid redundant calculations.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Callable, Mapping

import pandas as pd

logger = logging.getLogger(__name__)


def _hash_dataframe(data: pd.DataFrame) -> str:
    """Create a hash of a DataFrame for caching purposes.

    Uses a combination of shape, column names, and a sample of values
    to create a deterministic hash.
    """
    # Hash based on shape and column names
    shape_str = f"{data.shape[0]}_{data.shape[1]}"
    cols_str = "_".join(sorted(data.columns.astype(str)))

    # Hash a sample of the data (first, last, and middle rows)
    # to detect changes without hashing everything
    sample_rows = []
    if len(data) > 0:
        sample_rows.append(str(data.iloc[0].values))
        if len(data) > 1:
            sample_rows.append(str(data.iloc[-1].values))
        if len(data) > 2:
            sample_rows.append(str(data.iloc[len(data) // 2].values))

    data_str = "_".join([shape_str, cols_str] + sample_rows)
    return hashlib.sha256(data_str.encode()).hexdigest()


def _hash_params(params: Mapping[str, Any]) -> str:
    """Create a hash of parameters for caching purposes."""
    # Sort parameters by key for deterministic hashing
    sorted_items = sorted(params.items())
    # Convert to string representation
    params_str = "_".join(f"{k}:{v}" for k, v in sorted_items if v is not None)
    return hashlib.sha256(params_str.encode()).hexdigest()


def _create_cache_key(
    indicator_name: str,
    data: pd.DataFrame,
    params: Mapping[str, Any],
) -> str:
    """Create a cache key from indicator name, data, and parameters."""
    data_hash = _hash_dataframe(data)
    params_hash = _hash_params(params)
    return f"{indicator_name}:{data_hash}:{params_hash}"


class IndicatorCache:
    """LRU cache for computed indicators.

    This cache stores indicator calculation results keyed by a hash of:
    - Indicator name
    - Input DataFrame (shape, columns, sample values)
    - Parameters

    The cache uses an LRU eviction policy to limit memory usage.
    """

    def __init__(self, maxsize: int = 128):
        """
        Initialize the indicator cache.

        Args:
            maxsize: Maximum number of cached indicator results
        """
        self.maxsize = maxsize
        self._cache: dict[str, pd.Series | pd.DataFrame] = {}
        self._access_order: list[str] = []  # Used for LRU tracking
        self._hits = 0
        self._misses = 0

    def get(
        self,
        indicator_name: str,
        data: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series | pd.DataFrame | None:
        """
        Get a cached indicator result.

        Args:
            indicator_name: Name of the indicator
            data: Input DataFrame
            params: Indicator parameters

        Returns:
            Cached result if found, None otherwise
        """
        cache_key = _create_cache_key(indicator_name, data, params)

        if cache_key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(cache_key)
            self._access_order.append(cache_key)
            self._hits += 1
            logger.debug(f"Cache hit for {indicator_name} with key {cache_key[:16]}...")
            # Return a copy to avoid mutable issues
            result = self._cache[cache_key]
            if isinstance(result, pd.Series):
                return result.copy()
            else:
                return result.copy()
        else:
            self._misses += 1
            logger.debug(
                f"Cache miss for {indicator_name} with key {cache_key[:16]}..."
            )
            return None

    def set(
        self,
        indicator_name: str,
        data: pd.DataFrame,
        params: Mapping[str, Any],
        result: pd.Series | pd.DataFrame,
    ) -> None:
        """
        Store an indicator result in the cache.

        Args:
            indicator_name: Name of the indicator
            data: Input DataFrame
            params: Indicator parameters
            result: Computed indicator result to cache
        """
        cache_key = _create_cache_key(indicator_name, data, params)

        # Evict if cache is full (LRU policy)
        if len(self._cache) >= self.maxsize and cache_key not in self._cache:
            # Remove least recently used (first in list)
            lru_key = self._access_order.pop(0)
            del self._cache[lru_key]
            logger.debug(f"Cache evicted {lru_key[:16]}... (LRU)")

        # Store result (make a copy to avoid mutable issues)
        if isinstance(result, pd.Series):
            self._cache[cache_key] = result.copy()
        else:
            self._cache[cache_key] = result.copy()

        # Update access order
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        self._access_order.append(cache_key)

        logger.debug(f"Cached {indicator_name} with key {cache_key[:16]}...")

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        self._access_order.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Indicator cache cleared")

    def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }

    def __len__(self) -> int:
        """Return the number of cached items."""
        return len(self._cache)


# Global cache instance
_default_cache = IndicatorCache(maxsize=128)


def get_cache() -> IndicatorCache:
    """Get the global default indicator cache instance."""
    return _default_cache


def cached_indicator(
    indicator_name: str,
    cache: IndicatorCache | None = None,
) -> Callable[
    [Callable[..., pd.Series | pd.DataFrame]], Callable[..., pd.Series | pd.DataFrame]
]:
    """
    Decorator to cache indicator calculation results.

    Args:
        indicator_name: Name of the indicator (used in cache keys)
        cache: Cache instance to use (defaults to global cache)

    Returns:
        Decorator function
    """
    if cache is None:
        cache = get_cache()

    def decorator(
        func: Callable[..., pd.Series | pd.DataFrame]
    ) -> Callable[..., pd.Series | pd.DataFrame]:
        def wrapper(
            data: pd.DataFrame, params: Mapping[str, Any]
        ) -> pd.Series | pd.DataFrame:
            # Try to get from cache
            cached_result = cache.get(indicator_name, data, params)
            if cached_result is not None:
                return cached_result

            # Calculate and cache
            result = func(data, params)
            cache.set(indicator_name, data, params, result)
            return result

        return wrapper

    return decorator
