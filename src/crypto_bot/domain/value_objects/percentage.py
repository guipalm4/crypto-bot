"""
Percentage Value Object

Immutable value object representing a percentage.
"""

from decimal import Decimal
from typing import Any


class Percentage:
    """
    Percentage value object.

    Represents a percentage value with validation (0-100 range).
    """

    def __init__(self, value: float | Decimal | str) -> None:
        """
        Initialize Percentage.

        Args:
            value: Percentage value (0-100)

        Raises:
            ValueError: If value is outside 0-100 range
        """
        self._value = Decimal(str(value))

        if not (0 <= self._value <= 100):
            raise ValueError("Percentage must be between 0 and 100")

    @property
    def value(self) -> Decimal:
        """Get decimal value (0-100)."""
        return self._value

    @property
    def float_value(self) -> float:
        """Get float value (0-100)."""
        return float(self._value)

    @property
    def fraction(self) -> Decimal:
        """Get fractional value (0-1)."""
        return self._value / 100

    @property
    def fraction_float(self) -> float:
        """Get fractional float value (0-1)."""
        return float(self._value) / 100

    def apply_to(self, amount: float | Decimal) -> Decimal:
        """
        Apply percentage to an amount.

        Args:
            amount: Amount to apply percentage to

        Returns:
            Result of applying percentage
        """
        return Decimal(str(amount)) * self.fraction

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, Percentage):
            return False
        return self._value == other._value

    def __lt__(self, other: "Percentage") -> bool:
        """Less than comparison."""
        return self._value < other._value

    def __le__(self, other: "Percentage") -> bool:
        """Less than or equal comparison."""
        return self._value <= other._value

    def __gt__(self, other: "Percentage") -> bool:
        """Greater than comparison."""
        return self._value > other._value

    def __ge__(self, other: "Percentage") -> bool:
        """Greater than or equal comparison."""
        return self._value >= other._value

    def __repr__(self) -> str:
        """String representation."""
        return f"Percentage({self._value}%)"

    def __str__(self) -> str:
        """String representation."""
        return f"{self._value}%"

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self._value)
