"""Unit tests for indicator base interfaces."""

import dataclasses
from typing import Any, Mapping

import pandas as pd
import pytest

from crypto_bot.plugins.indicators.base import (
    BaseIndicator,
    IndicatorMetadata,
    InvalidIndicatorParameters,
)


class TestIndicator(BaseIndicator):
    """Test indicator implementation."""

    metadata = IndicatorMetadata(
        name="test",
        version="1.0",
        description="Test indicator",
    )

    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validate test parameters."""
        if "value" in params and params["value"] < 0:
            raise InvalidIndicatorParameters("value must be >= 0")

    def _calculate_impl(
        self, data: pd.DataFrame, params: Mapping[str, Any]
    ) -> pd.Series:
        """Calculate test indicator."""
        close = data.get("close", data.iloc[:, -1] if len(data.columns) > 0 else None)
        multiplier = params.get("value", 1)
        return (close * multiplier).rename("TEST")


class TestIndicatorMetadata:
    """Tests for IndicatorMetadata."""

    def test_metadata_creation(self) -> None:
        """Test creating metadata."""
        metadata = IndicatorMetadata(name="test", version="1.0", description="Test")
        assert metadata.name == "test"
        assert metadata.version == "1.0"
        assert metadata.description == "Test"

    def test_metadata_defaults(self) -> None:
        """Test metadata with default values."""
        metadata = IndicatorMetadata(name="test")
        assert metadata.name == "test"
        assert metadata.version == "1.0"
        assert metadata.description == ""

    def test_metadata_frozen(self) -> None:
        """Test that metadata is frozen."""
        metadata = IndicatorMetadata(name="test")
        with pytest.raises(dataclasses.FrozenInstanceError):
            metadata.name = "new"  # type: ignore[misc]


class TestBaseIndicator:
    """Tests for BaseIndicator."""

    def test_calculate_valid_parameters(self) -> None:
        """Test calculating with valid parameters."""
        indicator = TestIndicator()
        data = pd.DataFrame({"close": [100, 101, 102, 103, 104]})
        params = {"value": 2}

        result = indicator.calculate(data, params)

        assert isinstance(result, pd.Series)
        assert result.name == "TEST"
        assert len(result) == 5
        assert result.iloc[0] == pytest.approx(200.0)

    def test_calculate_invalid_parameters(self) -> None:
        """Test calculating with invalid parameters."""
        indicator = TestIndicator()
        data = pd.DataFrame({"close": [100, 101, 102, 103, 104]})
        params = {"value": -1}

        with pytest.raises(InvalidIndicatorParameters):
            indicator.calculate(data, params)

    def test_calculate_invalid_data_type(self) -> None:
        """Test calculating with invalid data type."""
        indicator = TestIndicator()
        params = {"value": 1}

        with pytest.raises(TypeError, match="data must be a pandas.DataFrame"):
            indicator.calculate("not a dataframe", params)  # type: ignore[arg-type]

    def test_calculate_does_not_mutate_input(self) -> None:
        """Test that calculate does not mutate input DataFrame."""
        indicator = TestIndicator()
        data = pd.DataFrame({"close": [100, 101, 102, 103, 104]})
        data_copy = data.copy()
        params = {"value": 1}

        indicator.calculate(data, params)

        pd.testing.assert_frame_equal(data, data_copy)

    def test_metadata_access(self) -> None:
        """Test accessing indicator metadata."""
        indicator = TestIndicator()
        assert indicator.metadata.name == "test"
        assert indicator.metadata.version == "1.0"


class TestInvalidIndicatorParameters:
    """Tests for InvalidIndicatorParameters exception."""

    def test_exception_creation(self) -> None:
        """Test creating the exception."""
        exc = InvalidIndicatorParameters("test message")
        assert str(exc) == "test message"
        assert isinstance(exc, ValueError)
