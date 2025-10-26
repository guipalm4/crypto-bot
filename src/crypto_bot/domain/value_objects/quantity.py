"""
Quantity Value Object

Immutable value object representing an asset quantity.
"""

from decimal import Decimal
from typing import Any


class Quantity:
    """
    Quantity value object.

    Represents an asset quantity with validation and precision.
    """

    def __init__(self, value: float | Decimal | str) -> None:
        """
        Initialize Quantity.

        Args:
            value: Quantity value (must be non-negative)

        Raises:
            ValueError: If value is negative
        """
        self._value = Decimal(str(value))

        if self._value < 0:
            raise ValueError("Quantity cannot be negative")

    @property
    def value(self) -> Decimal:
        """Get decimal value."""
        return self._value

    @property
    def float_value(self) -> float:
        """Get float value."""
        return float(self._value)

    def is_zero(self) -> bool:
        """Check if quantity is zero."""
        return self._value == 0

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, Quantity):
            return False
        return self._value == other._value

    def __lt__(self, other: "Quantity") -> bool:
        """Less than comparison."""
        return self._value < other._value

    def __le__(self, other: "Quantity") -> bool:
        """Less than or equal comparison."""
        return self._value <= other._value

    def __gt__(self, other: "Quantity") -> bool:
        """Greater than comparison."""
        return self._value > other._value

    def __ge__(self, other: "Quantity") -> bool:
        """Greater than or equal comparison."""
        return self._value >= other._value

    def __add__(self, other: "Quantity") -> "Quantity":
        """Add two quantities."""
        return Quantity(self._value + other._value)

    def __sub__(self, other: "Quantity") -> "Quantity":
        """Subtract two quantities."""
        result = self._value - other._value
        return Quantity(result)

    def __mul__(self, factor: float | Decimal) -> "Quantity":
        """Multiply quantity by a factor."""
        return Quantity(self._value * Decimal(str(factor)))

    def __truediv__(self, divisor: float | Decimal) -> "Quantity":
        """Divide quantity by a divisor."""
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Quantity(self._value / Decimal(str(divisor)))

    def __repr__(self) -> str:
        """String representation."""
        return f"Quantity({self._value})"

    def __str__(self) -> str:
        """String representation."""
        return str(self._value)

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self._value)
