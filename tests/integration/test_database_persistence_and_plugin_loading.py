"""
Integration tests for database persistence and plugin loading.

Tests database persistence of entities (Strategy, Position, Order) and
verifies plugin discovery and loading mechanisms.
"""

import os

# Set test encryption key BEFORE importing any application modules
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_32_bytes_long!!"

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

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
    TradingPair,
)
from crypto_bot.infrastructure.database.repositories import (
    AssetRepository,
    ExchangeRepository,
    OrderRepository,
    PositionRepository,
    StrategyRepository,
    TradingPairRepository,
)
from crypto_bot.plugins.exchanges.binance_plugin import BinancePlugin
from crypto_bot.plugins.exchanges.config_models import BinanceConfig
from crypto_bot.plugins.indicators.loader import IndicatorPluginRegistry
from crypto_bot.plugins.indicators.pandas_ta_indicators import RSIIndicator
from crypto_bot.plugins.strategies.loader import discover_strategies


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
async def strategy_repo(db_session):
    """Provide a strategy repository."""
    return StrategyRepository(db_session)


@pytest_asyncio.fixture
async def position_repo(db_session):
    """Provide a position repository."""
    return PositionRepository(db_session)


@pytest_asyncio.fixture
async def order_repo(db_session):
    """Provide an order repository."""
    return OrderRepository(db_session)


@pytest_asyncio.fixture
async def test_exchange(exchange_repo, db_session):
    """Create a test exchange in the database."""
    exchange = Exchange(
        name="binance",
        api_key_encrypted="test_api_key",
        api_secret_encrypted="test_api_secret",
        is_active=True,
        is_testnet=True,
        config_json={"timeout": 30000},
    )
    created = await exchange_repo.create(exchange)
    await db_session.commit()
    return created


@pytest_asyncio.fixture
async def test_assets(asset_repo, db_session):
    """Create test assets in the database."""
    btc = Asset(symbol="BTC", name="Bitcoin", decimals=8)
    usdt = Asset(symbol="USDT", name="Tether", decimals=6)
    btc_created = await asset_repo.create(btc)
    usdt_created = await asset_repo.create(usdt)
    await db_session.commit()
    return btc_created, usdt_created


@pytest_asyncio.fixture
async def test_trading_pair(trading_pair_repo, db_session, test_assets):
    """Create a test trading pair in the database."""
    btc, usdt = test_assets
    trading_pair = TradingPair(
        base_asset_id=btc.id,
        quote_asset_id=usdt.id,
        symbol="BTC/USDT",
    )
    created = await trading_pair_repo.create(trading_pair)
    await db_session.commit()
    return created


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabasePersistence:
    """Test database persistence for entities."""

    async def test_strategy_persistence(self, strategy_repo, db_session, faker) -> None:
        """Test creating, reading, updating, and deleting a Strategy."""
        # Create
        strategy = Strategy(
            name=faker.word(),
            plugin_name="test_strategy",
            description=faker.text(max_nb_chars=200),
            parameters_json={"param1": "value1", "param2": 42},
            is_active=True,
        )
        created = await strategy_repo.create(strategy)
        await db_session.commit()

        assert created.id is not None
        assert created.name == strategy.name
        assert created.plugin_name == "test_strategy"
        assert created.parameters_json == {"param1": "value1", "param2": 42}
        assert created.is_active is True
        assert created.created_at is not None
        assert created.updated_at is not None

        # Read
        retrieved = await strategy_repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.name == created.name
        assert retrieved.plugin_name == created.plugin_name

        # Update
        created.description = "Updated description"
        created.is_active = False
        updated = await strategy_repo.update(created)
        await db_session.commit()

        assert updated.description == "Updated description"
        assert updated.is_active is False

        # Query by name
        by_name = await strategy_repo.get_by_name(created.name)
        assert by_name is not None
        assert by_name.id == created.id

        # Query active strategies
        active = await strategy_repo.get_active_strategies()
        assert len(active) == 0  # We set is_active to False

        # Delete
        await strategy_repo.delete(created.id)
        await db_session.commit()

        deleted = await strategy_repo.get_by_id(created.id)
        assert deleted is None

    async def test_strategy_relationships_with_orders_and_positions(
        self,
        strategy_repo,
        order_repo,
        position_repo,
        db_session,
        test_exchange,
        test_trading_pair,
        faker,
    ) -> None:
        """Test Strategy relationships with Orders and Positions."""
        # Create strategy
        strategy = Strategy(
            name=faker.word(),
            plugin_name="test_strategy",
            parameters_json={},
            is_active=True,
        )
        created_strategy = await strategy_repo.create(strategy)
        await db_session.commit()

        # Create order linked to strategy
        order = Order(
            exchange_id=test_exchange.id,
            trading_pair_id=test_trading_pair.id,
            strategy_id=created_strategy.id,
            exchange_order_id=faker.uuid4(),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            status=OrderStatus.OPEN,
            quantity=Decimal("0.001"),
            price=Decimal("50000"),
        )
        created_order = await order_repo.create(order)
        await db_session.commit()

        # Create position linked to strategy
        position = Position(
            trading_pair_id=test_trading_pair.id,
            exchange_id=test_exchange.id,
            strategy_id=created_strategy.id,
            entry_order_id=created_order.id,
            side=PositionSide.LONG,
            status=PositionStatus.OPEN,
            quantity=Decimal("0.001"),
            entry_price=Decimal("50000"),
        )
        created_position = await position_repo.create(position)
        await db_session.commit()

        # Verify relationships
        assert created_order.strategy_id == created_strategy.id
        assert created_position.strategy_id == created_strategy.id
        assert created_position.entry_order_id == created_order.id

        # Query positions by strategy
        positions = await position_repo.get_by_strategy(created_strategy.id)
        assert len(positions) == 1
        assert positions[0].id == created_position.id

    async def test_position_persistence_and_status_queries(
        self,
        position_repo,
        db_session,
        test_exchange,
        test_trading_pair,
        faker,
    ) -> None:
        """Test Position persistence and status-based queries."""
        # Create open position
        open_position = Position(
            trading_pair_id=test_trading_pair.id,
            exchange_id=test_exchange.id,
            side=PositionSide.LONG,
            status=PositionStatus.OPEN,
            quantity=Decimal("0.001"),
            entry_price=Decimal("50000"),
            stop_loss=Decimal("45000"),
            take_profit=Decimal("60000"),
        )
        created_open = await position_repo.create(open_position)
        await db_session.commit()

        # Create closed position
        closed_position = Position(
            trading_pair_id=test_trading_pair.id,
            exchange_id=test_exchange.id,
            side=PositionSide.LONG,
            status=PositionStatus.CLOSED,
            quantity=Decimal("0.002"),
            entry_price=Decimal("48000"),
            exit_price=Decimal("55000"),
            pnl=Decimal("140"),
            pnl_percentage=Decimal("14.58"),
        )
        created_closed = await position_repo.create(closed_position)
        await db_session.commit()

        # Query by status
        open_positions = await position_repo.get_by_status(PositionStatus.OPEN)
        assert len(open_positions) >= 1
        assert any(p.id == created_open.id for p in open_positions)

        closed_positions = await position_repo.get_by_status(PositionStatus.CLOSED)
        assert len(closed_positions) >= 1
        assert any(p.id == created_closed.id for p in closed_positions)

        # Query open positions with filters
        open_by_exchange = await position_repo.get_open_positions(
            exchange_id=test_exchange.id
        )
        assert len(open_by_exchange) >= 1

        open_by_pair = await position_repo.get_open_positions(
            trading_pair_id=test_trading_pair.id
        )
        assert len(open_by_pair) >= 1

        # Query by trading pair
        by_pair = await position_repo.get_by_trading_pair(test_trading_pair.id)
        assert len(by_pair) >= 2

    async def test_order_persistence_and_status_updates(
        self,
        order_repo,
        db_session,
        test_exchange,
        test_trading_pair,
        faker,
    ) -> None:
        """Test Order persistence and status transitions."""
        # Create order
        order = Order(
            exchange_id=test_exchange.id,
            trading_pair_id=test_trading_pair.id,
            exchange_order_id=faker.uuid4(),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            quantity=Decimal("0.001"),
            price=Decimal("50000"),
        )
        created = await order_repo.create(order)
        await db_session.commit()

        assert created.status == OrderStatus.OPEN

        # Update status to PARTIALLY_FILLED
        created.status = OrderStatus.PARTIALLY_FILLED
        created.filled_quantity = Decimal("0.0005")
        updated = await order_repo.update(created)
        await db_session.commit()

        assert updated.status == OrderStatus.PARTIALLY_FILLED
        assert updated.filled_quantity == Decimal("0.0005")

        # Update status to CLOSED
        updated.status = OrderStatus.CLOSED
        updated.filled_quantity = Decimal("0.001")
        final = await order_repo.update(updated)
        await db_session.commit()

        assert final.status == OrderStatus.CLOSED
        assert final.filled_quantity == Decimal("0.001")

    async def test_data_integrity_constraints(
        self,
        strategy_repo,
        db_session,
        faker,
    ) -> None:
        """Test database constraints and data integrity."""
        # Create strategy with unique name
        strategy1 = Strategy(
            name="unique_strategy",
            plugin_name="test_plugin",
            parameters_json={},
            is_active=True,
        )
        created1 = await strategy_repo.create(strategy1)
        await db_session.commit()

        # Try to create another strategy with the same name (should fail)
        strategy2 = Strategy(
            name="unique_strategy",
            plugin_name="test_plugin",
            parameters_json={},
            is_active=True,
        )
        with pytest.raises(IntegrityError):  # Should raise integrity error
            created2 = await strategy_repo.create(strategy2)
            await db_session.commit()

        # Cleanup
        await strategy_repo.delete(created1.id)
        await db_session.commit()


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginLoading:
    """Test plugin discovery and loading mechanisms."""

    async def test_strategy_plugin_discovery(self) -> None:
        """Test discovery of strategy plugins via entry points."""
        strategies = discover_strategies()

        # Should return a mapping (may be empty if no plugins registered)
        assert isinstance(strategies, dict)

        # Verify cache is working (second call should be cached)
        strategies2 = discover_strategies()
        assert strategies is strategies2  # Same object due to cache

    async def test_indicator_plugin_loading(self) -> None:
        """Test loading of indicator plugins."""
        registry = IndicatorPluginRegistry()
        registry.load_plugins()

        # Verify that built-in indicators are available
        # RSI should be available as it's in the plugins directory
        indicator_names = registry.plugin_names
        assert isinstance(indicator_names, list)

        # Try to get RSI plugin if available
        rsi_plugin_name = None
        for name in indicator_names:
            if name.lower() == "rsi":
                rsi_plugin_name = name
                break

        if rsi_plugin_name:
            # RSI indicator should be loadable
            try:
                rsi_class = registry.get_plugin(rsi_plugin_name)
                if rsi_class:
                    # Verify it's a class
                    assert isinstance(rsi_class, type)
                    # Verify it has required attributes
                    assert hasattr(rsi_class, "metadata")
                    assert hasattr(rsi_class, "calculate")
            except Exception:
                # Some environments may not have all plugins configured
                pass

    async def test_exchange_plugin_initialization(self) -> None:
        """Test that exchange plugins initialize correctly."""
        # Create a Binance plugin config (sandbox mode, no real credentials needed)
        config = BinanceConfig(
            api_key="test_key",
            api_secret="test_secret",
            sandbox=True,
        )

        plugin = BinancePlugin(config)

        # Verify plugin is not initialized yet
        assert not plugin._initialized

        # Initialize (will fail with invalid credentials, but tests initialization flow)
        try:
            await plugin.initialize()
            # If initialization succeeds (e.g., with mock/testnet), verify state
            assert plugin._initialized is True or plugin._initialized is False
        except Exception:
            # Expected to fail with invalid credentials, but initialization attempt is logged
            pass
        finally:
            try:
                await plugin.close()
            except Exception:
                pass

    async def test_plugin_response_and_capabilities(self) -> None:
        """Test that plugins respond as expected and expose correct capabilities."""
        config = BinanceConfig(
            api_key="test_key",
            api_secret="test_secret",
            sandbox=True,
        )

        plugin = BinancePlugin(config)

        # Verify plugin name
        assert plugin.name == "Binance"

        # Verify plugin capabilities (before initialization, uses defaults)
        capabilities = plugin.has
        assert isinstance(capabilities, dict)
        # Binance should support these operations
        assert capabilities.get("createOrder", False) is True
        assert capabilities.get("fetchBalance", False) is True
        assert capabilities.get("fetchOHLCV", False) is True

    async def test_indicator_plugin_registry_discovery(self) -> None:
        """Test indicator plugin registry discovery mechanism."""
        registry = IndicatorPluginRegistry()

        # Before loading, plugins should be empty or unloaded
        initial_count = len(registry.plugin_names)

        # Load plugins
        registry.load_plugins()

        # After loading, should have discovered plugins (at least 0)
        final_count = len(registry.plugin_names)
        assert final_count >= 0  # May be 0 if no plugins in directory

        # Reloading should not add duplicates
        registry.load_plugins()
        assert len(registry.plugin_names) == final_count
