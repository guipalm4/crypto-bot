"""
Trading Pair Model

Database model for trading pairs.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto_bot.infrastructure.database.base import Base

if TYPE_CHECKING:
    from crypto_bot.infrastructure.database.models.asset import Asset
    from crypto_bot.infrastructure.database.models.exchange import Exchange
    from crypto_bot.infrastructure.database.models.order import Order
    from crypto_bot.infrastructure.database.models.position import Position


class TradingPair(Base):
    """
    Trading Pair model representing tradable pairs on exchanges.
    
    A trading pair consists of a base asset and a quote asset
    (e.g., BTC/USDT where BTC is base and USDT is quote).
    """
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # Foreign keys
    base_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quote_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exchange_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exchange.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Pair information
    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    # Trading constraints
    min_order_size: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    max_order_size: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=True,
    )
    tick_size: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Relationships
    base_asset: Mapped["Asset"] = relationship(
        "Asset",
        foreign_keys=[base_asset_id],
        back_populates="base_pairs",
    )
    quote_asset: Mapped["Asset"] = relationship(
        "Asset",
        foreign_keys=[quote_asset_id],
        back_populates="quote_pairs",
    )
    exchange: Mapped["Exchange"] = relationship(
        "Exchange",
        back_populates="trading_pairs",
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="trading_pair",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list["Position"]] = relationship(
        "Position",
        back_populates="trading_pair",
        cascade="all, delete-orphan",
    )

