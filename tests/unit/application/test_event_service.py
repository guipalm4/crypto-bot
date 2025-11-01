"""
Unit tests for EventService.

Tests event creation and persistence with mocked repository.
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from freezegun import freeze_time

from crypto_bot.application.services.event_service import EventService
from crypto_bot.domain.repositories.event_repository import (
    DomainEvent as DomainEventInterface,
)
from crypto_bot.domain.repositories.event_repository import IEventRepository


@pytest.fixture
def mock_event_repository() -> MagicMock:
    """Create a mock event repository."""
    repo = MagicMock(spec=IEventRepository)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def event_service(mock_event_repository: MagicMock) -> EventService:
    """Create EventService with mocked repository."""
    return EventService(event_repository=mock_event_repository)


@pytest.mark.asyncio
class TestEventService:
    """Test suite for EventService."""

    async def test_emit_order_created_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful order created event emission."""
        order_id = uuid4()
        order_data = {
            "symbol": "BTC/USDT",
            "side": "buy",
            "type": "market",
            "amount": 0.1,
            "price": 50000.0,
        }
        metadata = {"user_id": "123", "correlation_id": "abc"}

        # Mock repository response
        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderCreated",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(UTC),
            payload=order_data,
            metadata=metadata,
        )
        mock_event_repository.create.return_value = created_event

        # Execute
        with freeze_time("2024-01-01 12:00:00"):
            result = await event_service.emit_order_created(
                order_id=order_id, order_data=order_data, metadata=metadata
            )

        # Verify
        assert result.event_type == "OrderCreated"
        assert result.aggregate_id == order_id
        assert result.aggregate_type == "Order"
        assert result.payload == order_data
        assert result.metadata == metadata
        mock_event_repository.create.assert_called_once()

    async def test_emit_order_created_without_metadata(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test order created event emission without metadata."""
        order_id = uuid4()
        order_data = {"symbol": "ETH/USDT", "side": "sell", "amount": 1.0}

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderCreated",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(UTC),
            payload=order_data,
            metadata={},
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_order_created(
            order_id=order_id, order_data=order_data
        )

        assert result.event_type == "OrderCreated"
        assert result.metadata == {}
        mock_event_repository.create.assert_called_once()

    async def test_emit_order_cancelled_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful order cancelled event emission."""
        order_id = uuid4()
        reason = "User requested cancellation"
        metadata = {"user_id": "123"}

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderCancelled",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(UTC),
            payload={"reason": reason},
            metadata=metadata,
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_order_cancelled(
            order_id=order_id, reason=reason, metadata=metadata
        )

        assert result.event_type == "OrderCancelled"
        assert result.aggregate_id == order_id
        assert "reason" in result.payload
        assert result.payload["reason"] == reason
        mock_event_repository.create.assert_called_once()

    async def test_emit_order_filled_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful order filled event emission."""
        order_id = uuid4()
        fill_data = {
            "filled_amount": 0.1,
            "filled_price": 50000.0,
            "fee": 5.0,
        }
        metadata = {"trade_id": "trade_123"}

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderFilled",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(UTC),
            payload=fill_data,
            metadata=metadata,
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_order_filled(
            order_id=order_id, fill_data=fill_data, metadata=metadata
        )

        assert result.event_type == "OrderFilled"
        assert result.payload == fill_data
        assert result.metadata == metadata
        mock_event_repository.create.assert_called_once()

    async def test_emit_position_opened_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful position opened event emission."""
        position_id = uuid4()
        position_data = {
            "symbol": "BTC/USDT",
            "side": "long",
            "entry_price": 50000.0,
            "quantity": 0.1,
        }

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="PositionOpened",
            aggregate_id=position_id,
            aggregate_type="Position",
            occurred_at=datetime.now(UTC),
            payload=position_data,
            metadata={},
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_position_opened(
            position_id=position_id, position_data=position_data
        )

        assert result.event_type == "PositionOpened"
        assert result.aggregate_type == "Position"
        assert result.payload == position_data
        mock_event_repository.create.assert_called_once()

    async def test_emit_position_closed_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful position closed event emission."""
        position_id = uuid4()
        close_data = {
            "exit_price": 51000.0,
            "pnl": 100.0,
            "pnl_percentage": 2.0,
            "exit_order_id": str(uuid4()),
        }

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="PositionClosed",
            aggregate_id=position_id,
            aggregate_type="Position",
            occurred_at=datetime.now(UTC),
            payload=close_data,
            metadata={},
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_position_closed(
            position_id=position_id, close_data=close_data
        )

        assert result.event_type == "PositionClosed"
        assert result.payload["pnl"] == 100.0
        assert result.payload["exit_price"] == 51000.0
        mock_event_repository.create.assert_called_once()

    async def test_emit_order_updated_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful order updated event emission."""
        order_id = uuid4()
        update_data = {"status": "partially_filled", "filled": 0.05, "remaining": 0.05}

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="OrderUpdated",
            aggregate_id=order_id,
            aggregate_type="Order",
            occurred_at=datetime.now(UTC),
            payload=update_data,
            metadata={},
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_order_updated(
            order_id=order_id, update_data=update_data
        )

        assert result.event_type == "OrderUpdated"
        assert result.payload == update_data
        mock_event_repository.create.assert_called_once()

    async def test_emit_trade_executed_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful trade executed event emission."""
        trade_id = uuid4()
        trade_data = {
            "order_id": str(uuid4()),
            "quantity": 0.1,
            "price": 50000.0,
            "fee": 5.0,
            "exchange": "binance",
        }

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="TradeExecuted",
            aggregate_id=trade_id,
            aggregate_type="Trade",
            occurred_at=datetime.now(UTC),
            payload=trade_data,
            metadata={},
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_trade_executed(
            trade_id=trade_id, trade_data=trade_data
        )

        assert result.event_type == "TradeExecuted"
        assert result.aggregate_type == "Trade"
        assert result.payload == trade_data
        mock_event_repository.create.assert_called_once()

    async def test_emit_position_updated_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful position updated event emission."""
        position_id = uuid4()
        update_data = {"stop_loss": 48000.0, "take_profit": 52000.0}

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="PositionUpdated",
            aggregate_id=position_id,
            aggregate_type="Position",
            occurred_at=datetime.now(UTC),
            payload=update_data,
            metadata={},
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_position_updated(
            position_id=position_id, update_data=update_data
        )

        assert result.event_type == "PositionUpdated"
        assert result.payload == update_data
        mock_event_repository.create.assert_called_once()

    async def test_emit_generic_event_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful generic event emission."""
        aggregate_id = uuid4()
        payload = {"message": "Custom event data", "value": 123}

        created_event = DomainEventInterface(
            event_id=uuid4(),
            event_type="CustomEvent",
            aggregate_id=aggregate_id,
            aggregate_type="CustomAggregate",
            occurred_at=datetime.now(UTC),
            payload=payload,
            metadata={},
        )
        mock_event_repository.create.return_value = created_event

        result = await event_service.emit_generic_event(
            event_type="CustomEvent",
            aggregate_id=aggregate_id,
            aggregate_type="CustomAggregate",
            payload=payload,
        )

        assert result.event_type == "CustomEvent"
        assert result.aggregate_type == "CustomAggregate"
        assert result.payload == payload
        mock_event_repository.create.assert_called_once()

    async def test_get_aggregate_events_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful retrieval of aggregate events."""
        aggregate_id = uuid4()
        aggregate_type = "Order"

        mock_events = [
            DomainEventInterface(
                event_id=uuid4(),
                event_type="OrderCreated",
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                occurred_at=datetime.now(UTC),
                payload={"symbol": "BTC/USDT"},
                metadata={},
            ),
            DomainEventInterface(
                event_id=uuid4(),
                event_type="OrderFilled",
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                occurred_at=datetime.now(UTC),
                payload={"filled": 0.1},
                metadata={},
            ),
        ]
        mock_event_repository.get_by_aggregate.return_value = mock_events

        result = await event_service.get_aggregate_events(
            aggregate_id=aggregate_id, aggregate_type=aggregate_type
        )

        assert len(result) == 2
        assert result[0].event_type == "OrderCreated"
        assert result[1].event_type == "OrderFilled"
        mock_event_repository.get_by_aggregate.assert_called_once_with(
            aggregate_id=aggregate_id, aggregate_type=aggregate_type
        )

    async def test_replay_aggregate_success(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test successful aggregate replay."""
        aggregate_id = uuid4()
        aggregate_type = "Order"

        mock_events = [
            DomainEventInterface(
                event_id=uuid4(),
                event_type="OrderCreated",
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                occurred_at=datetime.now(UTC),
                payload={"symbol": "BTC/USDT", "side": "buy", "amount": 0.1},
                metadata={},
            ),
            DomainEventInterface(
                event_id=uuid4(),
                event_type="OrderUpdated",
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                occurred_at=datetime.now(UTC),
                payload={"status": "partially_filled"},
                metadata={},
            ),
            DomainEventInterface(
                event_id=uuid4(),
                event_type="OrderFilled",
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                occurred_at=datetime.now(UTC),
                payload={"filled_amount": 0.1},
                metadata={},
            ),
        ]
        mock_event_repository.get_by_aggregate.return_value = mock_events

        result = await event_service.replay_aggregate(
            aggregate_id=aggregate_id, aggregate_type=aggregate_type
        )

        assert result["id"] == aggregate_id
        assert result["type"] == aggregate_type
        assert result["events_count"] == 3
        assert len(result["history"]) == 3
        assert result["status"] == "filled"
        assert result["symbol"] == "BTC/USDT"
        assert result["side"] == "buy"

    async def test_event_persistence_failure(
        self, event_service: EventService, mock_event_repository: MagicMock
    ) -> None:
        """Test handling of event persistence failures."""
        order_id = uuid4()
        order_data = {"symbol": "BTC/USDT", "side": "buy"}

        # Simulate repository failure
        mock_event_repository.create.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await event_service.emit_order_created(
                order_id=order_id, order_data=order_data
            )

        mock_event_repository.create.assert_called_once()
