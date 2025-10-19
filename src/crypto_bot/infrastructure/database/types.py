"""
Custom SQLAlchemy Types

Custom column types for value objects.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import Numeric, String
from sqlalchemy.types import TypeDecorator

from crypto_bot.domain.value_objects import Percentage, Price, Quantity, Timeframe


class PriceType(TypeDecorator[Price]):
    """SQLAlchemy type for Price value object."""
    
    impl = Numeric(precision=20, scale=8)
    cache_ok = True
    
    def process_bind_param(self, value: Price | None, dialect: Any) -> Decimal | None:
        """Convert Price to Decimal for database storage."""
        if value is None:
            return None
        if isinstance(value, Price):
            return value.value
        return Decimal(str(value))
    
    def process_result_value(self, value: Decimal | None, dialect: Any) -> Price | None:
        """Convert Decimal from database to Price."""
        if value is None:
            return None
        return Price(value)


class QuantityType(TypeDecorator[Quantity]):
    """SQLAlchemy type for Quantity value object."""
    
    impl = Numeric(precision=20, scale=8)
    cache_ok = True
    
    def process_bind_param(
        self, value: Quantity | None, dialect: Any
    ) -> Decimal | None:
        """Convert Quantity to Decimal for database storage."""
        if value is None:
            return None
        if isinstance(value, Quantity):
            return value.value
        return Decimal(str(value))
    
    def process_result_value(
        self, value: Decimal | None, dialect: Any
    ) -> Quantity | None:
        """Convert Decimal from database to Quantity."""
        if value is None:
            return None
        return Quantity(value)


class PercentageType(TypeDecorator[Percentage]):
    """SQLAlchemy type for Percentage value object."""
    
    impl = Numeric(precision=10, scale=4)
    cache_ok = True
    
    def process_bind_param(
        self, value: Percentage | None, dialect: Any
    ) -> Decimal | None:
        """Convert Percentage to Decimal for database storage."""
        if value is None:
            return None
        if isinstance(value, Percentage):
            return value.value
        return Decimal(str(value))
    
    def process_result_value(
        self, value: Decimal | None, dialect: Any
    ) -> Percentage | None:
        """Convert Decimal from database to Percentage."""
        if value is None:
            return None
        return Percentage(value)


class TimeframeType(TypeDecorator[Timeframe]):
    """SQLAlchemy type for Timeframe value object."""
    
    impl = String(10)
    cache_ok = True
    
    def process_bind_param(self, value: Timeframe | None, dialect: Any) -> str | None:
        """Convert Timeframe to string for database storage."""
        if value is None:
            return None
        if isinstance(value, Timeframe):
            return value.value
        return str(value)
    
    def process_result_value(
        self, value: str | None, dialect: Any
    ) -> Timeframe | None:
        """Convert string from database to Timeframe."""
        if value is None:
            return None
        return Timeframe(value)

