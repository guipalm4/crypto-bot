"""
Integration tests for repository implementations.

Tests all repository CRUD operations, relationships, and event sourcing.
"""

import os

# Set test encryption key BEFORE importing any application modules
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_32_bytes_long!!"

from datetime import UTC, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from crypto_bot.application.services.event_service import EventService
from crypto_bot.infrastructure.database import Base, get_db_session
from crypto_bot.infrastructure.database.engine import db_engine
from crypto_bot.infrastructure.database.models import (
    Asset,
    Exchange,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    PositionSide,
    PositionStatus,
    Strategy,
    Trade,
    TradingPair,
)
from crypto_bot.infrastructure.database.repositories import (
    AssetRepository,
    EventRepository,
    ExchangeRepository,
    OrderRepository,
    PositionRepository,
    StrategyRepository,
    TradeRepository,
    TradingPairRepository,
)


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Create all tables before each test and drop them after."""
    # Reset engine to avoid event loop issues
    await db_engine.close()
    engine = db_engine.create_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Clean up engine
    await db_engine.close()


@pytest_asyncio.fixture
async def db_session(setup_database):
    """Provide an async database session for tests."""
    async for session in get_db_session():
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def exchange_repo(db_session):
    """Provide an exchange repository."""
    return ExchangeRepository(db_session)


@pytest_asyncio.fixture
async def asset_repo(db_session):
    """Provide an asset repository."""
    return AssetRepository(db_session)


@pytest_asyncio.fixture
async def trading_pair_repo(db_session):
    """Provide a trading pair repository."""
    return TradingPairRepository(db_session)


@pytest_asyncio.fixture
async def order_repo(db_session):
    """Provide an order repository."""
    return OrderRepository(db_session)


@pytest_asyncio.fixture
async def trade_repo(db_session):
    """Provide a trade repository."""
    return TradeRepository(db_session)


@pytest_asyncio.fixture
async def position_repo(db_session):
    """Provide a position repository."""
    return PositionRepository(db_session)


@pytest_asyncio.fixture
async def strategy_repo(db_session):
    """Provide a strategy repository."""
    return StrategyRepository(db_session)


@pytest_asyncio.fixture
async def event_repo(db_session):
    """Provide an event repository."""
    return EventRepository(db_session)


@pytest_asyncio.fixture
async def event_service(event_repo):
    """Provide an event service."""
    return EventService(event_repo)


class TestExchangeRepository:
    """Tests for ExchangeRepository."""

    @pytest.mark.asyncio
    async def test_create_exchange(self, exchange_repo, db_session):
        """Test creating an exchange."""
        exchange = Exchange(
            name="binance",
            api_key_encrypted="test_api_key",
            api_secret_encrypted="test_api_secret",
            is_active=True,
            is_testnet=False,
            config_json={"timeout": 30000},
        )

        created = await exchange_repo.create(exchange)
        await db_session.commit()

        assert created.id is not None
        assert created.name == "binance"
        assert created.created_at is not None
        assert created.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_by_name(self, exchange_repo, db_session):
        """Test getting exchange by name."""
        exchange = Exchange(
            name="coinbase",
            api_key_encrypted="test_key",
            api_secret_encrypted="test_secret",
        )
        await exchange_repo.create(exchange)
        await db_session.commit()

        found = await exchange_repo.get_by_name("coinbase")
        assert found is not None
        assert found.name == "coinbase"

    @pytest.mark.asyncio
    async def test_get_active_exchanges(self, exchange_repo, db_session):
        """Test getting active exchanges."""
        active_exchange = Exchange(
            name="binance",
            api_key_encrypted="key1",
            api_secret_encrypted="secret1",
            is_active=True,
        )
        inactive_exchange = Exchange(
            name="kraken",
            api_key_encrypted="key2",
            api_secret_encrypted="secret2",
            is_active=False,
        )

        await exchange_repo.create(active_exchange)
        await exchange_repo.create(inactive_exchange)
        await db_session.commit()

        active_exchanges = await exchange_repo.get_active_exchanges()
        assert len(active_exchanges) == 1
        assert active_exchanges[0].name == "binance"


class TestAssetRepository:
    """Tests for AssetRepository."""

    @pytest.mark.asyncio
    async def test_create_asset(self, asset_repo, db_session):
        """Test creating an asset."""
        asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)

        created = await asset_repo.create(asset)
        await db_session.commit()

        assert created.id is not None
        assert created.symbol == "BTC"
        assert created.name == "Bitcoin"

    @pytest.mark.asyncio
    async def test_get_by_symbol(self, asset_repo, db_session):
        """Test getting asset by symbol."""
        asset = Asset(symbol="ETH", name="Ethereum")
        await asset_repo.create(asset)
        await db_session.commit()

        found = await asset_repo.get_by_symbol("ETH")
        assert found is not None
        assert found.name == "Ethereum"

    @pytest.mark.asyncio
    async def test_search_by_name(self, asset_repo, db_session):
        """Test searching assets by name."""
        btc = Asset(symbol="BTC", name="Bitcoin")
        eth = Asset(symbol="ETH", name="Ethereum")
        usdt = Asset(symbol="USDT", name="Tether USD")

        await asset_repo.create(btc)
        await asset_repo.create(eth)
        await asset_repo.create(usdt)
        await db_session.commit()

        results = await asset_repo.search_by_name("ethereum")
        assert len(results) == 1
        assert results[0].symbol == "ETH"


class TestOrderRepository:
    """Tests for OrderRepository."""

    @pytest.mark.asyncio
    async def test_create_order_and_get_by_status(
        self, order_repo, exchange_repo, trading_pair_repo, asset_repo, db_session
    ):
        """Test creating an order and querying by status."""
        # Create dependencies
        exchange = Exchange(
            name="binance", api_key_encrypted="key", api_secret_encrypted="secret"
        )
        await exchange_repo.create(exchange)

        btc = Asset(symbol="BTC", name="Bitcoin")
        usdt = Asset(symbol="USDT", name="Tether")
        await asset_repo.create(btc)
        await asset_repo.create(usdt)

        pair = TradingPair(
            exchange_id=exchange.id,
            base_asset_id=btc.id,
            quote_asset_id=usdt.id,
            symbol="BTC/USDT",
            min_order_size=Decimal("0.001"),
            max_order_size=Decimal("1000.0"),
            tick_size=Decimal("0.01"),
        )
        await trading_pair_repo.create(pair)

        # Create order
        order = Order(
            exchange_order_id="12345",
            exchange_id=exchange.id,
            trading_pair_id=pair.id,
            type=OrderType.LIMIT,
            side=OrderSide.BUY,
            status=OrderStatus.PENDING,
            quantity=Decimal("1.5"),
            price=Decimal("50000.00"),
        )
        created = await order_repo.create(order)
        await db_session.commit()

        # Query by status
        pending_orders = await order_repo.get_by_status(OrderStatus.PENDING)
        assert len(pending_orders) == 1
        assert pending_orders[0].id == created.id


class TestEventSourcing:
    """Tests for event sourcing and EventService."""

    @pytest.mark.asyncio
    async def test_emit_order_created_event(self, event_service, db_session):
        """Test emitting OrderCreated event."""
        order_id = uuid4()
        order_data = {
            "type": "LIMIT",
            "side": "BUY",
            "quantity": "1.5",
            "price": "50000.00",
        }

        event = await event_service.emit_order_created(
            order_id=order_id,
            order_data=order_data,
            metadata={"user": "test_user"},
        )
        await db_session.commit()

        assert event.event_id is not None
        assert event.event_type == "OrderCreated"
        assert event.aggregate_id == order_id
        assert event.payload == order_data

    @pytest.mark.asyncio
    async def test_replay_aggregate_events(self, event_service, db_session):
        """Test replaying events to reconstruct aggregate state."""
        order_id = uuid4()

        # Emit series of events
        await event_service.emit_order_created(
            order_id=order_id,
            order_data={"type": "LIMIT", "side": "BUY", "quantity": "1.0"},
        )
        await event_service.emit_order_updated(
            order_id=order_id, update_data={"status": "partially_filled"}
        )
        await event_service.emit_order_filled(
            order_id=order_id, fill_data={"filled_quantity": "1.0"}
        )
        await db_session.commit()

        # Replay events
        state = await event_service.replay_aggregate(
            aggregate_id=order_id, aggregate_type="Order"
        )

        assert state["events_count"] == 3
        assert state["status"] == "filled"
        assert len(state["history"]) == 3


class TestFullTradingFlow:
    """Integration tests for complete trading flows."""

    @pytest.mark.asyncio
    async def test_complete_order_lifecycle(
        self,
        exchange_repo,
        asset_repo,
        trading_pair_repo,
        order_repo,
        trade_repo,
        event_service,
        db_session,
    ):
        """Test complete order lifecycle with event sourcing."""
        # Setup
        exchange = Exchange(
            name="test_exchange", api_key_encrypted="k", api_secret_encrypted="s"
        )
        await exchange_repo.create(exchange)

        btc = Asset(symbol="BTC", name="Bitcoin")
        usdt = Asset(symbol="USDT", name="Tether")
        await asset_repo.create(btc)
        await asset_repo.create(usdt)

        pair = TradingPair(
            exchange_id=exchange.id,
            base_asset_id=btc.id,
            quote_asset_id=usdt.id,
            symbol="BTC/USDT",
            min_order_size=Decimal("0.001"),
            max_order_size=Decimal("1000.0"),
            tick_size=Decimal("0.01"),
        )
        await trading_pair_repo.create(pair)

        # Create order
        order = Order(
            exchange_order_id="ord_123",
            exchange_id=exchange.id,
            trading_pair_id=pair.id,
            type=OrderType.LIMIT,
            side=OrderSide.BUY,
            status=OrderStatus.PENDING,
            quantity=Decimal("1.0"),
            price=Decimal("50000.00"),
        )
        created_order = await order_repo.create(order)

        # Emit event
        await event_service.emit_order_created(
            order_id=created_order.id,
            order_data={
                "exchange_order_id": "ord_123",
                "type": "LIMIT",
                "side": "BUY",
                "quantity": "1.0",
                "price": "50000.00",
            },
        )

        # Create trade
        trade = Trade(
            exchange_trade_id="trade_123",
            order_id=created_order.id,
            quantity=Decimal("1.0"),
            price=Decimal("50000.00"),
            fee=Decimal("50.00"),
            timestamp=datetime.now(UTC),
        )
        await trade_repo.create(trade)

        # Update order status
        created_order.status = OrderStatus.FILLED
        updated_order = await order_repo.update(created_order)

        # Emit filled event
        await event_service.emit_order_filled(
            order_id=updated_order.id, fill_data={"filled_quantity": "1.0"}
        )

        await db_session.commit()

        # Verify
        order_events = await event_service.get_aggregate_events(
            aggregate_id=created_order.id, aggregate_type="Order"
        )
        assert len(order_events) == 2
        assert order_events[0].event_type == "OrderCreated"
        assert order_events[1].event_type == "OrderFilled"

        # Replay
        state = await event_service.replay_aggregate(
            aggregate_id=created_order.id, aggregate_type="Order"
        )
        assert state["status"] == "filled"
        assert state["events_count"] == 2
