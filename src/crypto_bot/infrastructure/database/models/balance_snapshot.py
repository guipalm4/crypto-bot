"""
Balance Snapshot Model

Database model for portfolio balance snapshots.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto_bot.infrastructure.database.base import Base

if TYPE_CHECKING:
    from crypto_bot.infrastructure.database.models.asset import Asset
    from crypto_bot.infrastructure.database.models.exchange import Exchange


class BalanceSnapshot(Base):
    """
    Balance Snapshot model representing portfolio balance snapshots.

    Stores periodic snapshots of account balances for tracking portfolio
    value over time and calculating performance metrics.
    """

    __tablename__ = "balance_snapshots"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Foreign keys
    exchange_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exchange.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Balance values
    free_balance: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    locked_balance: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
        default=0.0,
    )
    total_balance: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=False,
    )
    value_in_usd: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=8),
        nullable=True,
    )

    # Timestamp
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Unique constraint for deduplication
    # Prevents duplicate snapshots for same exchange, asset, and timestamp
    __table_args__ = (
        UniqueConstraint(
            "exchange_id",
            "asset_id",
            "snapshot_at",
            name="uq_balance_snapshot_exchange_asset_time",
        ),
    )

    # Relationships
    exchange: Mapped["Exchange"] = relationship(
        "Exchange",
        back_populates="balance_snapshots",
    )
    asset: Mapped["Asset"] = relationship(
        "Asset",
        back_populates="balance_snapshots",
    )
