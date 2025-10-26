"""
Unit tests for value objects.
"""

from decimal import Decimal

import pytest

from crypto_bot.domain.value_objects import Percentage, Price, Quantity, Timeframe


class TestPrice:
    """Tests for Price value object."""

    def test_create_price_from_float(self) -> None:
        """Test creating price from float."""
        price = Price(50000.0)
        assert price.float_value == 50000.0

    def test_create_price_from_decimal(self) -> None:
        """Test creating price from Decimal."""
        price = Price(Decimal("50000.00"))
        assert price.value == Decimal("50000.00")

    def test_create_price_from_string(self) -> None:
        """Test creating price from string."""
        price = Price("50000.00")
        assert price.value == Decimal("50000.00")

    def test_price_cannot_be_negative(self) -> None:
        """Test that price cannot be negative."""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            Price(-100.0)

    def test_price_equality(self) -> None:
        """Test price equality."""
        price1 = Price(50000.0)
        price2 = Price(50000.0)
        price3 = Price(60000.0)

        assert price1 == price2
        assert price1 != price3

    def test_price_comparison(self) -> None:
        """Test price comparison operators."""
        price1 = Price(50000.0)
        price2 = Price(60000.0)

        assert price1 < price2
        assert price1 <= price2
        assert price2 > price1
        assert price2 >= price1

    def test_price_arithmetic(self) -> None:
        """Test price arithmetic operations."""
        price1 = Price(50000.0)
        price2 = Price(10000.0)

        # Addition
        result = price1 + price2
        assert result.float_value == 60000.0

        # Subtraction
        result = price1 - price2
        assert result.float_value == 40000.0

        # Multiplication
        result = price1 * 2
        assert result.float_value == 100000.0

        # Division
        result = price1 / 2
        assert result.float_value == 25000.0


class TestQuantity:
    """Tests for Quantity value object."""

    def test_create_quantity(self) -> None:
        """Test creating quantity."""
        quantity = Quantity(0.5)
        assert quantity.float_value == 0.5

    def test_quantity_cannot_be_negative(self) -> None:
        """Test that quantity cannot be negative."""
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            Quantity(-0.5)

    def test_quantity_is_zero(self) -> None:
        """Test checking if quantity is zero."""
        quantity = Quantity(0)
        assert quantity.is_zero()

        quantity = Quantity(0.5)
        assert not quantity.is_zero()

    def test_quantity_arithmetic(self) -> None:
        """Test quantity arithmetic operations."""
        q1 = Quantity(0.5)
        q2 = Quantity(0.3)

        result = q1 + q2
        assert float(result.value) == pytest.approx(0.8)

        result = q1 - q2
        assert float(result.value) == pytest.approx(0.2)


class TestPercentage:
    """Tests for Percentage value object."""

    def test_create_percentage(self) -> None:
        """Test creating percentage."""
        pct = Percentage(50.0)
        assert pct.float_value == 50.0

    def test_percentage_must_be_in_range(self) -> None:
        """Test that percentage must be between 0 and 100."""
        with pytest.raises(ValueError, match="Percentage must be between 0 and 100"):
            Percentage(-1.0)

        with pytest.raises(ValueError, match="Percentage must be between 0 and 100"):
            Percentage(101.0)

    def test_percentage_fraction(self) -> None:
        """Test percentage as fraction."""
        pct = Percentage(50.0)
        assert float(pct.fraction) == 0.5
        assert pct.fraction_float == 0.5

    def test_percentage_apply_to(self) -> None:
        """Test applying percentage to amount."""
        pct = Percentage(10.0)
        result = pct.apply_to(1000.0)
        assert float(result) == 100.0


class TestTimeframe:
    """Tests for Timeframe value object."""

    def test_create_timeframe(self) -> None:
        """Test creating timeframe."""
        tf = Timeframe("1h")
        assert tf.value == "1h"
        assert tf.seconds == 3600

    def test_invalid_timeframe(self) -> None:
        """Test creating invalid timeframe."""
        with pytest.raises(ValueError, match="Invalid timeframe"):
            Timeframe("invalid")

    def test_timeframe_conversions(self) -> None:
        """Test timeframe unit conversions."""
        tf = Timeframe("1h")

        assert tf.seconds == 3600
        assert tf.minutes == 60
        assert tf.hours == 1
        assert tf.days == 1 / 24

    def test_timeframe_comparison(self) -> None:
        """Test timeframe comparison."""
        tf1 = Timeframe("1m")
        tf2 = Timeframe("1h")

        assert tf1 < tf2
        assert tf2 > tf1

    def test_all_valid_timeframes(self) -> None:
        """Test that all defined timeframes are valid."""
        valid_timeframes = [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "8h",
            "12h",
            "1d",
            "3d",
            "1w",
            "1M",
        ]

        for tf_str in valid_timeframes:
            tf = Timeframe(tf_str)
            assert tf.value == tf_str
            assert tf.seconds > 0
