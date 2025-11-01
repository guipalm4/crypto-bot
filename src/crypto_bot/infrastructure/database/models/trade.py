"""
Trade Model

Database model for executed trades.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto_bot.infrastructure.database.base import Base

if TYPE_CHECKING:
    from crypto_bot.infrastructure.database.models.order import Order


class Trade(Base):
    """
    Trade model representing executed trades.

    A trade is the execution of an order or part of an order.
    """

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Foreign keys
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Exchange trade ID
    exchange_trade_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Trade details
    price: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    fee: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        default=0.0,
        nullable=False,
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="trades",
    )
