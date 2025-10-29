"""Unit tests for pandas-ta based indicators."""

import pandas as pd
import pytest

from crypto_bot.plugins.indicators.base import InvalidIndicatorParameters
from crypto_bot.plugins.indicators.cache import IndicatorCache, get_cache
from crypto_bot.plugins.indicators.pandas_ta_indicators import (
    EMAIndicator,
    RSIIndicator,
    SMAIndicator,
)


class TestRSIIndicator:
    """Tests for RSIIndicator."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Clear cache before each test
        get_cache().clear()

    def test_metadata(self) -> None:
        """Test indicator metadata."""
        indicator = RSIIndicator()
        assert indicator.metadata.name == "rsi"
        assert indicator.metadata.version == "1.0"
        assert "momentum" in indicator.metadata.description.lower()

    def test_validate_parameters_valid(self) -> None:
        """Test parameter validation with valid parameters."""
        indicator = RSIIndicator()
        indicator.validate_parameters({"length": 14})
        indicator.validate_parameters({"length": 21})

    def test_validate_parameters_invalid(self) -> None:
        """Test parameter validation with invalid parameters."""
        indicator = RSIIndicator()
        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"length": -1})

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"length": 0})

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"length": "14"})  # type: ignore[arg-type]

    def test_calculate_rsi_default_length(self) -> None:
        """Test RSI calculation with default length."""
        indicator = RSIIndicator()
        data = pd.DataFrame(
            {
                "close": [
                    100,
                    102,
                    101,
                    105,
                    107,
                    106,
                    108,
                    110,
                    109,
                    111,
                    112,
                    111,
                    113,
                    115,
                    114,
                ]
            }
        )

        result = indicator.calculate(data, {})

        assert isinstance(result, pd.Series)
        assert result.name == "RSI_14"
        assert len(result) == len(data)
        # RSI values should be between 0 and 100
        assert result.notna().any()  # Some values should be non-null
        if result.notna().any():
            assert (result.dropna() >= 0).all()
            assert (result.dropna() <= 100).all()

    def test_calculate_rsi_custom_length(self) -> None:
        """Test RSI calculation with custom length."""
        indicator = RSIIndicator()
        data = pd.DataFrame(
            {
                "close": [
                    100,
                    102,
                    101,
                    105,
                    107,
                    106,
                    108,
                    110,
                    109,
                    111,
                    112,
                    111,
                    113,
                    115,
                    114,
                ]
            }
        )

        result = indicator.calculate(data, {"length": 7})

        assert isinstance(result, pd.Series)
        assert result.name == "RSI_7"

    def test_calculate_rsi_missing_close(self) -> None:
        """Test RSI calculation with missing close column."""
        indicator = RSIIndicator()
        data = pd.DataFrame({"open": [100, 101, 102]})

        with pytest.raises(ValueError, match="RSI requires 'close' column"):
            indicator.calculate(data, {"length": 14})

    def test_calculate_rsi_caching(self) -> None:
        """Test that RSI results are cached."""
        cache = get_cache()
        indicator = RSIIndicator()
        data = pd.DataFrame(
            {
                "close": [
                    100,
                    102,
                    101,
                    105,
                    107,
                    106,
                    108,
                    110,
                    109,
                    111,
                    112,
                    111,
                    113,
                    115,
                    114,
                ]
            }
        )
        params = {"length": 14}

        # First call should miss cache
        result1 = indicator.calculate(data, params)
        initial_misses = cache._misses

        # Second call should hit cache
        result2 = indicator.calculate(data, params)
        assert cache._hits > 0

        pd.testing.assert_series_equal(result1, result2)


class TestEMAIndicator:
    """Tests for EMAIndicator."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        get_cache().clear()

    def test_metadata(self) -> None:
        """Test indicator metadata."""
        indicator = EMAIndicator()
        assert indicator.metadata.name == "ema"
        assert indicator.metadata.version == "1.0"

    def test_validate_parameters(self) -> None:
        """Test parameter validation."""
        indicator = EMAIndicator()
        indicator.validate_parameters({"length": 21})
        indicator.validate_parameters({"length": 50})

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"length": -1})

    def test_calculate_ema_default_length(self) -> None:
        """Test EMA calculation with default length."""
        indicator = EMAIndicator()
        data = pd.DataFrame(
            {"close": [100, 102, 101, 105, 107, 106, 108, 110, 109, 111]}
        )

        result = indicator.calculate(data, {})

        assert isinstance(result, pd.Series)
        assert result.name == "EMA_21"
        assert len(result) == len(data)
        # EMA should have some valid values
        assert result.notna().any()

    def test_calculate_ema_custom_length(self) -> None:
        """Test EMA calculation with custom length."""
        indicator = EMAIndicator()
        data = pd.DataFrame(
            {"close": [100, 102, 101, 105, 107, 106, 108, 110, 109, 111]}
        )

        result = indicator.calculate(data, {"length": 5})

        assert isinstance(result, pd.Series)
        assert result.name == "EMA_5"

    def test_calculate_ema_caching(self) -> None:
        """Test that EMA results are cached."""
        cache = get_cache()
        indicator = EMAIndicator()
        data = pd.DataFrame({"close": [100, 102, 101, 105, 107]})
        params = {"length": 5}

        result1 = indicator.calculate(data, params)
        result2 = indicator.calculate(data, params)

        assert cache._hits > 0
        pd.testing.assert_series_equal(result1, result2)


class TestSMAIndicator:
    """Tests for SMAIndicator."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        get_cache().clear()

    def test_metadata(self) -> None:
        """Test indicator metadata."""
        indicator = SMAIndicator()
        assert indicator.metadata.name == "sma"
        assert indicator.metadata.version == "1.0"

    def test_validate_parameters(self) -> None:
        """Test parameter validation."""
        indicator = SMAIndicator()
        indicator.validate_parameters({"length": 20})
        indicator.validate_parameters({"length": 50})

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"length": 0})

    def test_calculate_sma_default_length(self) -> None:
        """Test SMA calculation with default length."""
        indicator = SMAIndicator()
        # Need at least 20+ values for default length=20 SMA to produce results
        data = pd.DataFrame(
            {
                "close": [
                    100,
                    102,
                    101,
                    105,
                    107,
                    106,
                    108,
                    110,
                    109,
                    111,
                    112,
                    111,
                    113,
                    115,
                    114,
                    116,
                    118,
                    117,
                    120,
                    122,
                    121,
                    123,
                    125,
                    124,
                    126,
                ]
            }
        )

        result = indicator.calculate(data, {})

        assert isinstance(result, pd.Series)
        assert result.name == "SMA_20"
        assert len(result) == len(data)
        # SMA should have valid values after window size (first 19 NaN, then values)
        assert result.iloc[19:].notna().all()

    def test_calculate_sma_custom_length(self) -> None:
        """Test SMA calculation with custom length."""
        indicator = SMAIndicator()
        data = pd.DataFrame(
            {"close": [100, 102, 101, 105, 107, 106, 108, 110, 109, 111]}
        )

        result = indicator.calculate(data, {"length": 5})

        assert isinstance(result, pd.Series)
        assert result.name == "SMA_5"
        # With length=5, first 4 values should be NaN, 5th+ should have values
        assert result.iloc[4:].notna().all()

    def test_calculate_sma_caching(self) -> None:
        """Test that SMA results are cached."""
        cache = get_cache()
        indicator = SMAIndicator()
        data = pd.DataFrame({"close": [100, 102, 101, 105, 107]})
        params = {"length": 3}

        result1 = indicator.calculate(data, params)
        result2 = indicator.calculate(data, params)

        assert cache._hits > 0
        pd.testing.assert_series_equal(result1, result2)
