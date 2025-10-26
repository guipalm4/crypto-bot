"""Event repository implementation for event sourcing."""

from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.domain.repositories.event_repository import (
    DomainEvent as DomainEventInterface,
)
from crypto_bot.domain.repositories.event_repository import (
    IEventRepository,
)
from crypto_bot.infrastructure.database.models.domain_event import DomainEvent
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class EventRepository(BaseRepository[DomainEvent], IEventRepository):
    """Repository for Domain Events (event sourcing)."""

    def __init__(self, session: AsyncSession):
        """
        Initialize event repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, DomainEvent)

    def _to_interface(self, model: DomainEvent) -> DomainEventInterface:
        """
        Convert DB model to domain interface.

        Args:
            model: The database model.

        Returns:
            Domain event interface instance.
        """
        return DomainEventInterface(
            event_id=cast(UUID, model.id),
            event_type=cast(str, model.event_type),
            aggregate_id=cast(UUID, model.aggregate_id),
            aggregate_type=cast(str, model.aggregate_type),
            occurred_at=cast(datetime, model.occurred_at),
            payload=cast(dict, model.payload),
            metadata=cast(dict | None, model.event_metadata),
        )

    async def create(  # type: ignore[override]
        self, entity: DomainEventInterface
    ) -> DomainEventInterface:
        """Create a new domain event from interface and return the interface."""
        try:
            # Convert domain interface to database model
            model = DomainEvent(
                id=entity.event_id,
                event_type=entity.event_type,
                aggregate_id=entity.aggregate_id,
                aggregate_type=entity.aggregate_type,
                occurred_at=entity.occurred_at,
                payload=entity.payload,
                event_metadata=entity.metadata,
            )
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            # Convert back to interface for return
            return self._to_interface(model)
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to create domain event: {str(e)}") from e

    async def get_by_aggregate(
        self, aggregate_id: UUID, aggregate_type: str, skip: int = 0, limit: int = 1000
    ) -> list[DomainEventInterface]:
        """Get all events for a specific aggregate."""
        try:
            stmt = (
                select(DomainEvent)
                .where(
                    DomainEvent.aggregate_id == aggregate_id,
                    DomainEvent.aggregate_type == aggregate_type,
                )
                .offset(skip)
                .limit(limit)
                .order_by(DomainEvent.occurred_at.asc())
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            return [self._to_interface(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get events for aggregate {aggregate_id}: {str(e)}"
            ) from e

    async def get_by_event_type(
        self,
        event_type: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DomainEventInterface]:
        """Get events by type within an optional date range."""
        try:
            stmt = select(DomainEvent).where(DomainEvent.event_type == event_type)

            if start_date:
                stmt = stmt.where(DomainEvent.occurred_at >= start_date)
            if end_date:
                stmt = stmt.where(DomainEvent.occurred_at <= end_date)

            stmt = (
                stmt.offset(skip).limit(limit).order_by(DomainEvent.occurred_at.desc())
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            return [self._to_interface(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get events by type {event_type}: {str(e)}"
            ) from e

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        aggregate_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DomainEventInterface]:
        """Get events within a date range."""
        try:
            stmt = select(DomainEvent).where(
                DomainEvent.occurred_at >= start_date,
                DomainEvent.occurred_at <= end_date,
            )

            if aggregate_type:
                stmt = stmt.where(DomainEvent.aggregate_type == aggregate_type)

            stmt = (
                stmt.offset(skip).limit(limit).order_by(DomainEvent.occurred_at.desc())
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            return [self._to_interface(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get events by date range: {str(e)}"
            ) from e

    async def get_latest_events(
        self, limit: int = 100, aggregate_type: str | None = None
    ) -> list[DomainEventInterface]:
        """Get the latest events."""
        try:
            stmt = select(DomainEvent)

            if aggregate_type:
                stmt = stmt.where(DomainEvent.aggregate_type == aggregate_type)

            stmt = stmt.limit(limit).order_by(DomainEvent.occurred_at.desc())
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            return [self._to_interface(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get latest events: {str(e)}") from e
