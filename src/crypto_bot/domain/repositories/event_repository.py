"""Event repository interface for event sourcing."""

from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from crypto_bot.domain.repositories.base import IRepository


class DomainEvent:
    """
    Base class for domain events.

    Domain events represent facts that occurred in the domain
    and are used for event sourcing and audit trail.
    """

    def __init__(
        self,
        event_id: UUID,
        event_type: str,
        aggregate_id: UUID,
        aggregate_type: str,
        occurred_at: datetime,
        payload: dict,
        metadata: dict | None = None,
    ):
        """
        Initialize domain event.

        Args:
            event_id: Unique event identifier.
            event_type: Type of the event (e.g., 'OrderCreated').
            aggregate_id: ID of the aggregate root this event relates to.
            aggregate_type: Type of the aggregate (e.g., 'Order').
            occurred_at: Timestamp when the event occurred.
            payload: Event data as dictionary.
            metadata: Optional metadata (user, correlation ID, etc.).
        """
        self.event_id = event_id
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.occurred_at = occurred_at
        self.payload = payload
        self.metadata = metadata or {}


class IEventRepository(IRepository[DomainEvent]):
    """Repository interface for Domain Events (event sourcing)."""

    @abstractmethod
    async def get_by_aggregate(
        self, aggregate_id: UUID, aggregate_type: str, skip: int = 0, limit: int = 1000
    ) -> list[DomainEvent]:
        """
        Get all events for a specific aggregate.

        Args:
            aggregate_id: The aggregate root ID.
            aggregate_type: The type of the aggregate (e.g., 'Order').
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of events for the specified aggregate, ordered by occurrence.
        """
        pass

    @abstractmethod
    async def get_by_event_type(
        self,
        event_type: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DomainEvent]:
        """
        Get events by type within an optional date range.

        Args:
            event_type: The event type to filter by.
            start_date: Optional start of the date range.
            end_date: Optional end of the date range.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of events matching the criteria.
        """
        pass

    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        aggregate_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DomainEvent]:
        """
        Get events within a date range.

        Args:
            start_date: Start of the date range.
            end_date: End of the date range.
            aggregate_type: Optional aggregate type to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of events within the specified date range.
        """
        pass

    @abstractmethod
    async def get_latest_events(
        self, limit: int = 100, aggregate_type: str | None = None
    ) -> list[DomainEvent]:
        """
        Get the latest events.

        Args:
            limit: Maximum number of events to return.
            aggregate_type: Optional aggregate type to filter by.

        Returns:
            List of latest events, ordered by occurrence (descending).
        """
        pass
