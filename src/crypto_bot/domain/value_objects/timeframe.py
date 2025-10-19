"""
Timeframe Value Object

Immutable value object representing a trading timeframe.
"""

from typing import Any


class Timeframe:
    """
    Timeframe value object.
    
    Represents a trading timeframe (e.g., 1m, 5m, 1h, 1d).
    """
    
    # Valid timeframes
    VALID_TIMEFRAMES = {
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "2h": 7200,
        "4h": 14400,
        "6h": 21600,
        "8h": 28800,
        "12h": 43200,
        "1d": 86400,
        "3d": 259200,
        "1w": 604800,
        "1M": 2592000,
    }
    
    def __init__(self, value: str) -> None:
        """
        Initialize Timeframe.
        
        Args:
            value: Timeframe string (e.g., "1m", "1h", "1d")
        
        Raises:
            ValueError: If timeframe is invalid
        """
        if value not in self.VALID_TIMEFRAMES:
            valid_options = ", ".join(self.VALID_TIMEFRAMES.keys())
            raise ValueError(
                f"Invalid timeframe: {value}. "
                f"Valid options: {valid_options}"
            )
        
        self._value = value
    
    @property
    def value(self) -> str:
        """Get timeframe string."""
        return self._value
    
    @property
    def seconds(self) -> int:
        """Get timeframe in seconds."""
        return self.VALID_TIMEFRAMES[self._value]
    
    @property
    def minutes(self) -> float:
        """Get timeframe in minutes."""
        return self.seconds / 60
    
    @property
    def hours(self) -> float:
        """Get timeframe in hours."""
        return self.seconds / 3600
    
    @property
    def days(self) -> float:
        """Get timeframe in days."""
        return self.seconds / 86400
    
    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, Timeframe):
            return False
        return self._value == other._value
    
    def __lt__(self, other: "Timeframe") -> bool:
        """Less than comparison."""
        return self.seconds < other.seconds
    
    def __le__(self, other: "Timeframe") -> bool:
        """Less than or equal comparison."""
        return self.seconds <= other.seconds
    
    def __gt__(self, other: "Timeframe") -> bool:
        """Greater than comparison."""
        return self.seconds > other.seconds
    
    def __ge__(self, other: "Timeframe") -> bool:
        """Greater than or equal comparison."""
        return self.seconds >= other.seconds
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Timeframe('{self._value}')"
    
    def __str__(self) -> str:
        """String representation."""
        return self._value
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self._value)

