"""
Asset Model

Database model for cryptocurrency assets.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto_bot.infrastructure.database.base import Base

if TYPE_CHECKING:
    from crypto_bot.infrastructure.database.models.trading_pair import TradingPair


class Asset(Base):
    """
    Asset model representing cryptocurrency assets.
    
    Stores information about cryptocurrencies and fiat currencies
    that can be traded.
    """
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # Asset information
    symbol: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Additional metadata (decimals, contract address, etc.)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    
    # Relationships
    base_pairs: Mapped[list["TradingPair"]] = relationship(
        "TradingPair",
        foreign_keys="TradingPair.base_asset_id",
        back_populates="base_asset",
        cascade="all, delete-orphan",
    )
    quote_pairs: Mapped[list["TradingPair"]] = relationship(
        "TradingPair",
        foreign_keys="TradingPair.quote_asset_id",
        back_populates="quote_asset",
        cascade="all, delete-orphan",
    )

