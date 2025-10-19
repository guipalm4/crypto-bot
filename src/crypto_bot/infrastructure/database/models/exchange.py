"""
Exchange Model

Database model for cryptocurrency exchanges.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto_bot.infrastructure.database.base import Base
from crypto_bot.infrastructure.database.encrypted_types import EncryptedString

if TYPE_CHECKING:
    from crypto_bot.infrastructure.database.models.order import Order
    from crypto_bot.infrastructure.database.models.position import Position
    from crypto_bot.infrastructure.database.models.trading_pair import TradingPair


class Exchange(Base):
    """
    Exchange model representing cryptocurrency exchanges.
    
    Stores exchange configuration including encrypted API credentials
    and exchange-specific settings.
    """
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # Basic information
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # API credentials (automatically encrypted)
    api_key_encrypted: Mapped[str | None] = mapped_column(
        EncryptedString,
        nullable=True,
    )
    api_secret_encrypted: Mapped[str | None] = mapped_column(
        EncryptedString,
        nullable=True,
    )
    
    # Status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_testnet: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Exchange-specific configuration (rate limits, etc.)
    config_json: Mapped[dict] = mapped_column(
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    # Relationships
    trading_pairs: Mapped[list["TradingPair"]] = relationship(
        "TradingPair",
        back_populates="exchange",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="exchange",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list["Position"]] = relationship(
        "Position",
        back_populates="exchange",
        cascade="all, delete-orphan",
    )

