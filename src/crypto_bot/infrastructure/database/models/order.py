"""
Order Model

Database model for trading orders.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto_bot.infrastructure.database.base import Base
from crypto_bot.infrastructure.database.models.enums import (
    OrderSide,
    OrderStatus,
    OrderType,
)

if TYPE_CHECKING:
    from crypto_bot.infrastructure.database.models.exchange import Exchange
    from crypto_bot.infrastructure.database.models.position import Position
    from crypto_bot.infrastructure.database.models.strategy import Strategy
    from crypto_bot.infrastructure.database.models.trade import Trade
    from crypto_bot.infrastructure.database.models.trading_pair import TradingPair


class Order(Base):
    """
    Order model representing trading orders.
    
    Stores all information about buy and sell orders including
    their execution status and associated trades.
    """
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # Foreign keys
    trading_pair_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_pair.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exchange_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exchange.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strategy.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Exchange order ID
    exchange_order_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    # Order details
    type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, native_enum=False, length=50),
        nullable=False,
    )
    side: Mapped[OrderSide] = mapped_column(
        Enum(OrderSide, native_enum=False, length=20),
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=50),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )
    
    # Quantities and prices
    quantity: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    price: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=True,
    )
    executed_price: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=True,
    )
    executed_quantity: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        default=0.0,
        nullable=False,
    )
    
    # Fees
    fee: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        default=0.0,
        nullable=False,
    )
    fee_currency: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Reason for the order
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    trading_pair: Mapped["TradingPair"] = relationship(
        "TradingPair",
        back_populates="orders",
    )
    exchange: Mapped["Exchange"] = relationship(
        "Exchange",
        back_populates="orders",
    )
    strategy: Mapped["Strategy | None"] = relationship(
        "Strategy",
        back_populates="orders",
    )
    trades: Mapped[list["Trade"]] = relationship(
        "Trade",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    entry_positions: Mapped[list["Position"]] = relationship(
        "Position",
        foreign_keys="Position.entry_order_id",
        back_populates="entry_order",
    )
    exit_positions: Mapped[list["Position"]] = relationship(
        "Position",
        foreign_keys="Position.exit_order_id",
        back_populates="exit_order",
    )

