"""
Event sourcing service for domain events.

Provides methods to create and persist domain events for all trading operations.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Any, Dict, Optional

from crypto_bot.domain.repositories.event_repository import (
    DomainEvent as DomainEventInterface,
    IEventRepository,
)


class EventService:
    """
    Service for creating and persisting domain events.

    This service provides methods to create domain events for all
    important trading operations, maintaining a complete audit trail.
    """

    def __init__(self, event_repository: IEventRepository):
        """
        Initialize event service.

        Args:
            event_repository: The event repository for persisting events.
        """
        self._event_repo = event_repository

    async def emit_order_created(
        self,
        order_id: UUID,
        order_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit OrderCreated event.

        Args:
            order_id: The order ID.
            order_data: Order details (type, side, quantity, price, etc.).
            metadata: Optional metadata (user, correlation ID, etc.).

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderCreated",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(timezone.utc),
            payload=order_data,
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def emit_order_cancelled(
        self,
        order_id: UUID,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit OrderCancelled event.

        Args:
            order_id: The order ID.
            reason: Cancellation reason.
            metadata: Optional metadata.

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderCancelled",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(timezone.utc),
            payload={"reason": reason},
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def emit_order_filled(
        self,
        order_id: UUID,
        fill_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit OrderFilled event.

        Args:
            order_id: The order ID.
            fill_data: Fill details (quantity, price, fee, etc.).
            metadata: Optional metadata.

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderFilled",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(timezone.utc),
            payload=fill_data,
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def emit_order_updated(
        self,
        order_id: UUID,
        update_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit OrderUpdated event.

        Args:
            order_id: The order ID.
            update_data: Updated fields.
            metadata: Optional metadata.

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderUpdated",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(timezone.utc),
            payload=update_data,
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def emit_trade_executed(
        self,
        trade_id: UUID,
        trade_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit TradeExecuted event.

        Args:
            trade_id: The trade ID.
            trade_data: Trade details (order_id, quantity, price, fee, etc.).
            metadata: Optional metadata.

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type="TradeExecuted",
            aggregate_id=trade_id,
            aggregate_type="Trade",
            occurred_at=datetime.now(timezone.utc),
            payload=trade_data,
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def emit_position_opened(
        self,
        position_id: UUID,
        position_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit PositionOpened event.

        Args:
            position_id: The position ID.
            position_data: Position details (entry_order_id, side, quantity, etc.).
            metadata: Optional metadata.

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type="PositionOpened",
            aggregate_id=position_id,
            aggregate_type="Position",
            occurred_at=datetime.now(timezone.utc),
            payload=position_data,
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def emit_position_closed(
        self,
        position_id: UUID,
        close_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit PositionClosed event.

        Args:
            position_id: The position ID.
            close_data: Close details (exit_order_id, realized_pnl, etc.).
            metadata: Optional metadata.

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type="PositionClosed",
            aggregate_id=position_id,
            aggregate_type="Position",
            occurred_at=datetime.now(timezone.utc),
            payload=close_data,
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def emit_position_updated(
        self,
        position_id: UUID,
        update_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit PositionUpdated event.

        Args:
            position_id: The position ID.
            update_data: Updated fields (stop_loss, take_profit, etc.).
            metadata: Optional metadata.

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type="PositionUpdated",
            aggregate_id=position_id,
            aggregate_type="Position",
            occurred_at=datetime.now(timezone.utc),
            payload=update_data,
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def emit_generic_event(
        self,
        event_type: str,
        aggregate_id: UUID,
        aggregate_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainEventInterface:
        """
        Emit a generic domain event.

        Args:
            event_type: Type of the event.
            aggregate_id: ID of the aggregate root.
            aggregate_type: Type of the aggregate.
            payload: Event data.
            metadata: Optional metadata.

        Returns:
            The created domain event.
        """
        event = DomainEventInterface(
            event_id=uuid4(),
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            occurred_at=datetime.now(timezone.utc),
            payload=payload,
            metadata=metadata or {},
        )
        return await self._event_repo.create(entity=event)

    async def get_aggregate_events(
        self, aggregate_id: UUID, aggregate_type: str
    ) -> list[DomainEventInterface]:
        """
        Get all events for a specific aggregate.

        Args:
            aggregate_id: The aggregate root ID.
            aggregate_type: The type of the aggregate.

        Returns:
            List of events ordered by occurrence time.
        """
        return await self._event_repo.get_by_aggregate(
            aggregate_id=aggregate_id, aggregate_type=aggregate_type
        )

    async def replay_aggregate(
        self, aggregate_id: UUID, aggregate_type: str
    ) -> Dict[str, Any]:
        """
        Replay all events for an aggregate to reconstruct its state.

        Args:
            aggregate_id: The aggregate root ID.
            aggregate_type: The type of the aggregate.

        Returns:
            Dictionary representing the reconstructed state.
        """
        events = await self.get_aggregate_events(aggregate_id, aggregate_type)

        # Build state from events
        state: Dict[str, Any] = {
            "id": aggregate_id,
            "type": aggregate_type,
            "events_count": len(events),
            "history": [],
        }

        for event in events:
            state["history"].append(
                {
                    "event_id": str(event.event_id),
                    "event_type": event.event_type,
                    "occurred_at": event.occurred_at.isoformat(),
                    "payload": event.payload,
                    "metadata": event.metadata,
                }
            )

            # Update state based on event type
            if event.event_type == "OrderCreated":
                state.update(event.payload)
            elif event.event_type == "OrderUpdated":
                state.update(event.payload)
            elif event.event_type == "OrderCancelled":
                state["status"] = "cancelled"
                state["cancellation_reason"] = event.payload.get("reason")
            elif event.event_type == "OrderFilled":
                state["status"] = "filled"
                state.update(event.payload)
            elif event.event_type == "PositionOpened":
                state.update(event.payload)
            elif event.event_type == "PositionUpdated":
                state.update(event.payload)
            elif event.event_type == "PositionClosed":
                state["status"] = "closed"
                state.update(event.payload)

        return state

