"""
Database Model Enums

This module contains all enum definitions used by database models.
"""

import enum


class OrderType(str, enum.Enum):
    """Order type enumeration."""
    
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LOSS_LIMIT = "stop_loss_limit"
    TAKE_PROFIT = "take_profit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"


class OrderSide(str, enum.Enum):
    """Order side enumeration."""
    
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"
    FAILED = "failed"


class PositionSide(str, enum.Enum):
    """Position side enumeration."""
    
    LONG = "long"
    SHORT = "short"


class PositionStatus(str, enum.Enum):
    """Position status enumeration."""
    
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


class SignalType(str, enum.Enum):
    """Signal type enumeration."""
    
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class EventType(str, enum.Enum):
    """Risk event type enumeration."""
    
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    DRAWDOWN = "drawdown"
    EXPOSURE_LIMIT = "exposure_limit"
    CIRCUIT_BREAKER = "circuit_breaker"


class EventSeverity(str, enum.Enum):
    """Event severity enumeration."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

