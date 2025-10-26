"""
Domain repository interfaces.

This module defines abstract repository interfaces that follow
Domain-Driven Design principles. Concrete implementations are
provided in the infrastructure layer.
"""

from crypto_bot.domain.repositories.asset_repository import IAssetRepository
from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.domain.repositories.event_repository import IEventRepository
from crypto_bot.domain.repositories.exchange_repository import IExchangeRepository
from crypto_bot.domain.repositories.order_repository import IOrderRepository
from crypto_bot.domain.repositories.position_repository import IPositionRepository
from crypto_bot.domain.repositories.strategy_repository import IStrategyRepository
from crypto_bot.domain.repositories.trade_repository import ITradeRepository
from crypto_bot.domain.repositories.trading_pair_repository import (
    ITradingPairRepository,
)

__all__ = [
    "IRepository",
    "IOrderRepository",
    "ITradeRepository",
    "IPositionRepository",
    "IExchangeRepository",
    "IAssetRepository",
    "ITradingPairRepository",
    "IStrategyRepository",
    "IEventRepository",
]
