"""Unit tests for pandas-ta based indicators."""

import pandas as pd
import pytest

from crypto_bot.plugins.indicators.base import InvalidIndicatorParameters
from crypto_bot.plugins.indicators.cache import IndicatorCache, get_cache
from crypto_bot.plugins.indicators.pandas_ta_indicators import (
    EMAIndicator,
    MACDIndicator,
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


class TestMACDIndicator:
    """Tests for MACDIndicator."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        get_cache().clear()

    def test_metadata(self) -> None:
        """Test indicator metadata."""
        indicator = MACDIndicator()
        assert indicator.metadata.name == "macd"
        assert indicator.metadata.version == "1.0"
        assert "momentum" in indicator.metadata.description.lower()

    def test_validate_parameters_valid(self) -> None:
        """Test parameter validation with valid parameters."""
        indicator = MACDIndicator()
        indicator.validate_parameters({"fast": 12, "slow": 26, "signal": 9})
        indicator.validate_parameters({"fast": 8, "slow": 21, "signal": 5})
        # Test defaults
        indicator.validate_parameters({})

    def test_validate_parameters_invalid(self) -> None:
        """Test parameter validation with invalid parameters."""
        indicator = MACDIndicator()

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"fast": -1})

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"slow": 0})

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"signal": "9"})  # type: ignore[arg-type]

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"fast": 26, "slow": 12})  # fast >= slow

        with pytest.raises(InvalidIndicatorParameters):
            indicator.validate_parameters({"fast": 12, "slow": 12})  # fast == slow

    def test_calculate_macd_default_parameters(self) -> None:
        """Test MACD calculation with default parameters."""
        indicator = MACDIndicator()
        # Need sufficient data for MACD (at least slow period + signal period)
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
                    128,
                    127,
                    129,
                    131,
                    130,
                    132,
                    134,
                    133,
                    135,
                    137,
                    136,
                ]
            }
        )

        result = indicator.calculate(data, {})

        assert isinstance(result, pd.DataFrame)
        # Should have 3 columns: MACD line, signal line, histogram
        assert len(result.columns) == 3
        # Check column names follow standard convention
        assert any("MACD_" in col for col in result.columns)
        assert any("MACDs_" in col for col in result.columns)
        assert any("MACDh_" in col for col in result.columns)
        assert len(result) == len(data)
        # Should have some valid values after warm-up period
        assert result.notna().any().any()

    def test_calculate_macd_custom_parameters(self) -> None:
        """Test MACD calculation with custom parameters."""
        indicator = MACDIndicator()
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

        result = indicator.calculate(data, {"fast": 8, "slow": 21, "signal": 5})

        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 3
        # Check that custom parameters are reflected in column names
        assert any("8" in col and "21" in col and "5" in col for col in result.columns)

    def test_calculate_macd_missing_close(self) -> None:
        """Test MACD calculation with missing close column."""
        indicator = MACDIndicator()
        data = pd.DataFrame({"open": [100, 101, 102]})

        with pytest.raises(ValueError, match="MACD requires 'close' column"):
            indicator.calculate(data, {"fast": 12, "slow": 26, "signal": 9})

    def test_calculate_macd_caching(self) -> None:
        """Test that MACD results are cached."""
        cache = get_cache()
        indicator = MACDIndicator()
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
                    128,
                    127,
                    129,
                    131,
                    130,
                    132,
                    134,
                    133,
                    135,
                    137,
                    136,
                ]
            }
        )
        params = {"fast": 12, "slow": 26, "signal": 9}

        result1 = indicator.calculate(data, params)
        result2 = indicator.calculate(data, params)

        assert cache._hits > 0
        pd.testing.assert_frame_equal(result1, result2)

    def test_macd_components(self) -> None:
        """Test that MACD returns all three components."""
        indicator = MACDIndicator()
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
                    128,
                    127,
                    129,
                    131,
                    130,
                    132,
                    134,
                    133,
                    135,
                    137,
                    136,
                ]
            }
        )

        result = indicator.calculate(data, {})

        # Should have exactly 3 columns
        assert len(result.columns) == 3
        # All columns should have same length as input
        for col in result.columns:
            assert len(result[col]) == len(data)
