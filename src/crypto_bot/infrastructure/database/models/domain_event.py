"""Domain Event model for event sourcing."""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import func

from crypto_bot.infrastructure.database.base import Base


class DomainEvent(Base):
    """
    Domain event model for event sourcing.

    Stores all domain events for audit trail and event replay.
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "domain_event"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )

    event_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    event_metadata = Column(JSON, nullable=True)

    # Additional audit fields
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DomainEvent(id={self.id}, event_type={self.event_type}, "
            f"aggregate_id={self.aggregate_id}, occurred_at={self.occurred_at})>"
        )
