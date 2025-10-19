"""
Price Value Object

Immutable value object representing a monetary price.
"""

from decimal import Decimal
from typing import Any


class Price:
    """
    Price value object.
    
    Represents a monetary price with validation and precision.
    """
    
    def __init__(self, value: float | Decimal | str) -> None:
        """
        Initialize Price.
        
        Args:
            value: Price value (must be non-negative)
        
        Raises:
            ValueError: If value is negative
        """
        self._value = Decimal(str(value))
        
        if self._value < 0:
            raise ValueError("Price cannot be negative")
    
    @property
    def value(self) -> Decimal:
        """Get decimal value."""
        return self._value
    
    @property
    def float_value(self) -> float:
        """Get float value."""
        return float(self._value)
    
    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, Price):
            return False
        return self._value == other._value
    
    def __lt__(self, other: "Price") -> bool:
        """Less than comparison."""
        return self._value < other._value
    
    def __le__(self, other: "Price") -> bool:
        """Less than or equal comparison."""
        return self._value <= other._value
    
    def __gt__(self, other: "Price") -> bool:
        """Greater than comparison."""
        return self._value > other._value
    
    def __ge__(self, other: "Price") -> bool:
        """Greater than or equal comparison."""
        return self._value >= other._value
    
    def __add__(self, other: "Price") -> "Price":
        """Add two prices."""
        return Price(self._value + other._value)
    
    def __sub__(self, other: "Price") -> "Price":
        """Subtract two prices."""
        result = self._value - other._value
        return Price(result)
    
    def __mul__(self, factor: float | Decimal) -> "Price":
        """Multiply price by a factor."""
        return Price(self._value * Decimal(str(factor)))
    
    def __truediv__(self, divisor: float | Decimal) -> "Price":
        """Divide price by a divisor."""
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Price(self._value / Decimal(str(divisor)))
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Price({self._value})"
    
    def __str__(self) -> str:
        """String representation."""
        return str(self._value)
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self._value)

