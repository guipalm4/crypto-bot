"""Technical indicators implemented using pandas-ta library.

This module provides core technical indicators (RSI, EMA, SMA, MACD) using
pandas-ta's DataFrame accessor (df.ta) with fallback to pandas/numpy
when pandas-ta is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

import pandas as pd

try:
    import pandas_ta as ta

    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    ta = None  # type: ignore[assignment, unused-ignore]

from crypto_bot.plugins.indicators.base import (
    BaseIndicator,
    IndicatorMetadata,
    InvalidIndicatorParameters,
)
from crypto_bot.plugins.indicators.cache import get_cache

logger = logging.getLogger(__name__)


class RSIIndicator(BaseIndicator):
    """Relative Strength Index (RSI) indicator using pandas-ta."""

    metadata = IndicatorMetadata(
        name="rsi",
        version="1.0",
        description="Relative Strength Index - momentum oscillator measuring magnitude of price changes",
    )

    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validate RSI parameters."""
        length = params.get("length", 14)
        if not isinstance(length, int) or length < 1:
            raise InvalidIndicatorParameters(
                f"RSI 'length' must be a positive integer, got {length}"
            )

    def _calculate_impl(
        self, data: pd.DataFrame, params: Mapping[str, Any]
    ) -> pd.Series:
        """Calculate RSI using pandas-ta with fallback to pandas."""
        cache = get_cache()

        # Try cache first
        cached_result = cache.get(self.metadata.name, data, params)
        if cached_result is not None:
            return cached_result

        length = params.get("length", 14)
        if "close" not in data.columns:
            raise ValueError("RSI requires 'close' column in data")
        close = data["close"]

        if PANDAS_TA_AVAILABLE:
            try:
                # Use pandas-ta accessor
                result = ta.rsi(close, length=length)
                if result is None:
                    raise ValueError("pandas-ta RSI returned None")
                result.name = f"RSI_{length}"

                # Cache the result
                cache.set(self.metadata.name, data, params, result)
                return result
            except Exception as e:
                logger.warning(f"pandas-ta RSI calculation failed: {e}, using fallback")
                # Fall through to fallback

        # Fallback: manual RSI calculation with pandas
        result = self._rsi_fallback(close, length)

        # Cache the result
        cache.set(self.metadata.name, data, params, result)
        return result

    def _rsi_fallback(self, close: pd.Series, length: int) -> pd.Series:
        """Calculate RSI using pure pandas (fallback implementation)."""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi.name = f"RSI_{length}"
        return rsi


class EMAIndicator(BaseIndicator):
    """Exponential Moving Average (EMA) indicator using pandas-ta."""

    metadata = IndicatorMetadata(
        name="ema",
        version="1.0",
        description="Exponential Moving Average - trend-following indicator giving more weight to recent prices",
    )

    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validate EMA parameters."""
        length = params.get("length", 21)
        if not isinstance(length, int) or length < 1:
            raise InvalidIndicatorParameters(
                f"EMA 'length' must be a positive integer, got {length}"
            )

    def _calculate_impl(
        self, data: pd.DataFrame, params: Mapping[str, Any]
    ) -> pd.Series:
        """Calculate EMA using pandas-ta with fallback to pandas."""
        cache = get_cache()

        # Try cache first
        cached_result = cache.get(self.metadata.name, data, params)
        if cached_result is not None:
            return cached_result

        length = params.get("length", 21)
        if "close" not in data.columns:
            raise ValueError("EMA requires 'close' column in data")
        close = data["close"]

        if PANDAS_TA_AVAILABLE:
            try:
                result = ta.ema(close, length=length)
                if result is None:
                    raise ValueError("pandas-ta EMA returned None")
                result.name = f"EMA_{length}"

                # Cache the result
                cache.set(self.metadata.name, data, params, result)
                return result
            except Exception as e:
                logger.warning(f"pandas-ta EMA calculation failed: {e}, using fallback")
                # Fall through to fallback

        # Fallback: manual EMA calculation with pandas
        result = self._ema_fallback(close, length)

        # Cache the result
        cache.set(self.metadata.name, data, params, result)
        return result

    def _ema_fallback(self, close: pd.Series, length: int) -> pd.Series:
        """Calculate EMA using pure pandas (fallback implementation)."""
        alpha = 2.0 / (length + 1)
        ema = close.ewm(alpha=alpha, adjust=False).mean()
        ema.name = f"EMA_{length}"
        return ema


class SMAIndicator(BaseIndicator):
    """Simple Moving Average (SMA) indicator using pandas-ta."""

    metadata = IndicatorMetadata(
        name="sma",
        version="1.0",
        description="Simple Moving Average - average price over a specified period",
    )

    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validate SMA parameters."""
        length = params.get("length", 20)
        if not isinstance(length, int) or length < 1:
            raise InvalidIndicatorParameters(
                f"SMA 'length' must be a positive integer, got {length}"
            )

    def _calculate_impl(
        self, data: pd.DataFrame, params: Mapping[str, Any]
    ) -> pd.Series:
        """Calculate SMA using pandas-ta with fallback to pandas."""
        cache = get_cache()

        # Try cache first
        cached_result = cache.get(self.metadata.name, data, params)
        if cached_result is not None:
            return cached_result

        length = params.get("length", 20)
        if "close" not in data.columns:
            raise ValueError("SMA requires 'close' column in data")
        close = data["close"]

        if PANDAS_TA_AVAILABLE:
            try:
                result = ta.sma(close, length=length)
                if result is None:
                    raise ValueError("pandas-ta SMA returned None")
                result.name = f"SMA_{length}"

                # Cache the result
                cache.set(self.metadata.name, data, params, result)
                return result
            except Exception as e:
                logger.warning(f"pandas-ta SMA calculation failed: {e}, using fallback")
                # Fall through to fallback

        # Fallback: manual SMA calculation with pandas (trivial)
        result = self._sma_fallback(close, length)

        # Cache the result
        cache.set(self.metadata.name, data, params, result)
        return result

    def _sma_fallback(self, close: pd.Series, length: int) -> pd.Series:
        """Calculate SMA using pure pandas (fallback implementation)."""
        sma = close.rolling(window=length).mean()
        sma.name = f"SMA_{length}"
        return sma


class MACDIndicator(BaseIndicator):
    """Moving Average Convergence Divergence (MACD) indicator using pandas-ta.

    MACD consists of three components:
    - MACD line: Difference between fast and slow EMAs
    - Signal line: EMA of the MACD line
    - Histogram: Difference between MACD and Signal lines
    """

    metadata = IndicatorMetadata(
        name="macd",
        version="1.0",
        description="Moving Average Convergence Divergence - trend-following momentum indicator",
    )

    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validate MACD parameters."""
        fast = params.get("fast", 12)
        slow = params.get("slow", 26)
        signal = params.get("signal", 9)

        if not isinstance(fast, int) or fast < 1:
            raise InvalidIndicatorParameters(
                f"MACD 'fast' must be a positive integer, got {fast}"
            )
        if not isinstance(slow, int) or slow < 1:
            raise InvalidIndicatorParameters(
                f"MACD 'slow' must be a positive integer, got {slow}"
            )
        if not isinstance(signal, int) or signal < 1:
            raise InvalidIndicatorParameters(
                f"MACD 'signal' must be a positive integer, got {signal}"
            )
        if fast >= slow:
            raise InvalidIndicatorParameters(
                f"MACD 'fast' ({fast}) must be less than 'slow' ({slow})"
            )

    def _calculate_impl(
        self, data: pd.DataFrame, params: Mapping[str, Any]
    ) -> pd.DataFrame:
        """Calculate MACD using pandas-ta with fallback to pandas."""
        cache = get_cache()

        # Try cache first
        cached_result = cache.get(self.metadata.name, data, params)
        if cached_result is not None:
            return cached_result

        fast = params.get("fast", 12)
        slow = params.get("slow", 26)
        signal = params.get("signal", 9)

        if "close" not in data.columns:
            raise ValueError("MACD requires 'close' column in data")
        close = data["close"]

        if PANDAS_TA_AVAILABLE:
            try:
                # pandas-ta returns a DataFrame with MACD, signal, and histogram
                result = ta.macd(close, fast=fast, slow=slow, signal=signal)
                if result is None or result.empty:
                    raise ValueError("pandas-ta MACD returned None or empty")

                # Cache the result
                cache.set(self.metadata.name, data, params, result)
                return result
            except Exception as e:
                logger.warning(
                    f"pandas-ta MACD calculation failed: {e}, using fallback"
                )
                # Fall through to fallback

        # Fallback: manual MACD calculation with pandas
        result = self._macd_fallback(close, fast, slow, signal)

        # Cache the result
        cache.set(self.metadata.name, data, params, result)
        return result

    def _macd_fallback(
        self, close: pd.Series, fast: int, slow: int, signal: int
    ) -> pd.DataFrame:
        """Calculate MACD using pure pandas (fallback implementation)."""
        # Calculate fast and slow EMAs
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()

        # MACD line is the difference
        macd_line = ema_fast - ema_slow

        # Signal line is EMA of MACD line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()

        # Histogram is the difference
        histogram = macd_line - signal_line

        # Create DataFrame with standard naming convention
        result = pd.DataFrame(
            {
                f"MACD_{fast}_{slow}_{signal}": macd_line,
                f"MACDs_{fast}_{slow}_{signal}": signal_line,
                f"MACDh_{fast}_{slow}_{signal}": histogram,
            }
        )

        return result
