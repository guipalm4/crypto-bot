"""
Position Model

Database model for trading positions.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto_bot.infrastructure.database.base import Base
from crypto_bot.infrastructure.database.models.enums import PositionSide, PositionStatus

if TYPE_CHECKING:
    from crypto_bot.infrastructure.database.models.exchange import Exchange
    from crypto_bot.infrastructure.database.models.order import Order
    from crypto_bot.infrastructure.database.models.strategy import Strategy
    from crypto_bot.infrastructure.database.models.trading_pair import TradingPair


class Position(Base):
    """
    Position model representing trading positions.
    
    A position tracks entry and exit of a trade, including P&L calculation.
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
    entry_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order.id", ondelete="SET NULL"),
        nullable=True,
    )
    exit_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Position details
    side: Mapped[PositionSide] = mapped_column(
        Enum(PositionSide, native_enum=False, length=20),
        nullable=False,
    )
    status: Mapped[PositionStatus] = mapped_column(
        Enum(PositionStatus, native_enum=False, length=20),
        nullable=False,
        default=PositionStatus.OPEN,
        index=True,
    )
    
    # Quantities and prices
    quantity: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    entry_price: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    exit_price: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=True,
    )
    
    # Risk management
    stop_loss: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=True,
    )
    take_profit: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=True,
    )
    
    # P&L
    pnl: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=True,
    )
    pnl_percentage: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=True,
    )
    
    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    trading_pair: Mapped["TradingPair"] = relationship(
        "TradingPair",
        back_populates="positions",
    )
    exchange: Mapped["Exchange"] = relationship(
        "Exchange",
        back_populates="positions",
    )
    strategy: Mapped["Strategy | None"] = relationship(
        "Strategy",
        back_populates="positions",
    )
    entry_order: Mapped["Order | None"] = relationship(
        "Order",
        foreign_keys=[entry_order_id],
        back_populates="entry_positions",
    )
    exit_order: Mapped["Order | None"] = relationship(
        "Order",
        foreign_keys=[exit_order_id],
        back_populates="exit_positions",
    )

