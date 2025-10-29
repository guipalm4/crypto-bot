"""
Market Data Model

Database model for OHLCV (candlestick) market data.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto_bot.infrastructure.database.base import Base

if TYPE_CHECKING:
    from crypto_bot.infrastructure.database.models.exchange import Exchange
    from crypto_bot.infrastructure.database.models.trading_pair import TradingPair


class MarketData(Base):
    """
    Market Data model representing OHLCV candlestick data.

    Stores historical price and volume data for trading pairs to support
    technical analysis, backtesting, and strategy development.
    """

    __tablename__ = "market_data"

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

    # Timeframe (e.g., "1m", "5m", "1h", "1d")
    timeframe: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    # Timestamp for this candle
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # OHLCV data
    open: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    high: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    low: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    close: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    volume: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )

    # Unique constraint for deduplication
    # Prevents duplicate market data for same pair, exchange, timeframe, and timestamp
    __table_args__ = (
        UniqueConstraint(
            "trading_pair_id",
            "exchange_id",
            "timeframe",
            "timestamp",
            name="uq_market_data_pair_exchange_timeframe_time",
        ),
    )

    # Relationships
    trading_pair: Mapped["TradingPair"] = relationship(
        "TradingPair",
        back_populates="market_data",
    )
    exchange: Mapped["Exchange"] = relationship(
        "Exchange",
        back_populates="market_data",
    )
