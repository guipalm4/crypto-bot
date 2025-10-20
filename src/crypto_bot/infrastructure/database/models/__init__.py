"""
Database Models Module

This module contains all SQLAlchemy models for the crypto trading bot.
"""

from crypto_bot.infrastructure.database.models.asset import Asset
from crypto_bot.infrastructure.database.models.enums import (
    EventSeverity,
    EventType,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
    PositionStatus,
    SignalType,
)
from crypto_bot.infrastructure.database.models.exchange import Exchange
from crypto_bot.infrastructure.database.models.order import Order
from crypto_bot.infrastructure.database.models.position import Position
from crypto_bot.infrastructure.database.models.strategy import Strategy
from crypto_bot.infrastructure.database.models.trade import Trade
from crypto_bot.infrastructure.database.models.trading_pair import TradingPair
from crypto_bot.infrastructure.database.models.domain_event import DomainEvent

__all__ = [
    # Enums
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "PositionSide",
    "PositionStatus",
    "SignalType",
    "EventType",
    "EventSeverity",
    # Models
    "Asset",
    "Exchange",
    "TradingPair",
    "Order",
    "Trade",
    "Position",
    "Strategy",
    "DomainEvent",
]

