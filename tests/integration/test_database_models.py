"""
Integration tests for database models.
"""

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.infrastructure.database import Base, db_engine
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


@pytest_asyncio.fixture
async def setup_database() -> None:
    """Set up test database schema."""
    engine = db_engine.create_engine()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await db_engine.close()


@pytest_asyncio.fixture
async def db_session(setup_database: None) -> AsyncSession:
    """Get database session for tests."""
    session_factory = db_engine.get_session_factory()
    async with session_factory() as session:
        yield session


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_tables(setup_database: None) -> None:
    """Test that all tables are created correctly."""
    engine = db_engine.create_engine()

    async with engine.connect() as conn:
        # Check that tables exist
        def get_table_names(connection):  # type: ignore
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_table_names)

        expected_tables = [
            "asset",
            "exchange",
            "strategy",
            "trading_pair",
            "order",
            "trade",
            "position",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_exchange(db_session: AsyncSession) -> None:
    """Test creating an exchange record."""
    exchange = Exchange(
        name="binance",
        is_active=True,
        is_testnet=False,
        config_json={"rate_limit": 1200},
    )

    db_session.add(exchange)
    await db_session.commit()
    await db_session.refresh(exchange)

    assert exchange.id is not None
    assert exchange.name == "binance"
    assert exchange.is_active is True
    assert exchange.created_at is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_asset(db_session: AsyncSession) -> None:
    """Test creating an asset record."""
    asset = Asset(
        symbol="BTC",
        name="Bitcoin",
        is_active=True,
        metadata_json={"decimals": 8},
    )

    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)

    assert asset.id is not None
    assert asset.symbol == "BTC"
    assert asset.name == "Bitcoin"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_trading_pair_with_relationships(
    db_session: AsyncSession,
) -> None:
    """Test creating a trading pair with asset and exchange relationships."""
    # Create exchange
    exchange = Exchange(name="binance", is_active=True)
    db_session.add(exchange)

    # Create assets
    btc = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    usdt = Asset(symbol="USDT", name="Tether", is_active=True)
    db_session.add_all([btc, usdt])

    await db_session.commit()
    await db_session.refresh(exchange)
    await db_session.refresh(btc)
    await db_session.refresh(usdt)

    # Create trading pair
    trading_pair = TradingPair(
        base_asset_id=btc.id,
        quote_asset_id=usdt.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
        is_active=True,
    )

    db_session.add(trading_pair)
    await db_session.commit()
    await db_session.refresh(trading_pair)

    assert trading_pair.id is not None
    assert trading_pair.symbol == "BTC/USDT"
    assert trading_pair.base_asset.symbol == "BTC"
    assert trading_pair.quote_asset.symbol == "USDT"
    assert trading_pair.exchange.name == "binance"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_order_with_trades(db_session: AsyncSession) -> None:
    """Test creating an order with associated trades."""
    # Setup: Create necessary relationships
    exchange = Exchange(name="binance", is_active=True)
    btc = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    usdt = Asset(symbol="USDT", name="Tether", is_active=True)
    db_session.add_all([exchange, btc, usdt])
    await db_session.commit()

    trading_pair = TradingPair(
        base_asset_id=btc.id,
        quote_asset_id=usdt.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
    )
    db_session.add(trading_pair)
    await db_session.commit()

    # Create order
    order = Order(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        exchange_order_id="EX123456",
        type=OrderType.LIMIT,
        side=OrderSide.BUY,
        status=OrderStatus.FILLED,
        quantity=0.1,
        price=50000.0,
        executed_price=50000.0,
        executed_quantity=0.1,
        fee=5.0,
        fee_currency="USDT",
    )

    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create trade
    trade = Trade(
        order_id=order.id,
        exchange_trade_id="TR123456",
        price=50000.0,
        quantity=0.1,
        fee=5.0,
    )

    db_session.add(trade)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.id is not None
    assert order.exchange_order_id == "EX123456"
    assert order.type == OrderType.LIMIT
    assert order.side == OrderSide.BUY

    # Avoid async lazy-loading: query trades explicitly
    trades_stmt = select(Trade).where(Trade.order_id == order.id)
    trades_result = await db_session.execute(trades_stmt)
    trades = trades_result.scalars().all()
    assert len(trades) == 1
    assert trades[0].exchange_trade_id == "TR123456"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_position(db_session: AsyncSession) -> None:
    """Test creating a position."""
    # Setup
    exchange = Exchange(name="binance", is_active=True)
    btc = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    usdt = Asset(symbol="USDT", name="Tether", is_active=True)
    strategy = Strategy(name="RSI Strategy", plugin_name="rsi_strategy")
    db_session.add_all([exchange, btc, usdt, strategy])
    await db_session.commit()

    trading_pair = TradingPair(
        base_asset_id=btc.id,
        quote_asset_id=usdt.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
    )
    db_session.add(trading_pair)
    await db_session.commit()

    # Create position
    position = Position(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        strategy_id=strategy.id,
        side=PositionSide.LONG,
        status=PositionStatus.OPEN,
        quantity=0.1,
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0,
    )

    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)

    assert position.id is not None
    assert position.side == PositionSide.LONG
    assert position.status == PositionStatus.OPEN
    assert position.entry_price == 50000.0
    assert position.strategy.name == "RSI Strategy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cascade_delete(db_session: AsyncSession) -> None:
    """Test that cascade delete works correctly."""
    # Create exchange with trading pairs and orders
    exchange = Exchange(name="binance", is_active=True)
    btc = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    usdt = Asset(symbol="USDT", name="Tether", is_active=True)
    db_session.add_all([exchange, btc, usdt])
    await db_session.commit()

    trading_pair = TradingPair(
        base_asset_id=btc.id,
        quote_asset_id=usdt.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
    )
    db_session.add(trading_pair)
    await db_session.commit()

    order = Order(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        type=OrderType.MARKET,
        side=OrderSide.BUY,
        status=OrderStatus.PENDING,
        quantity=0.1,
    )
    db_session.add(order)
    await db_session.commit()

    exchange_id = exchange.id
    order_id = order.id

    # Delete exchange (should cascade to orders)
    await db_session.delete(exchange)
    await db_session.commit()

    # Verify order was deleted
    result = await db_session.execute(select(Order).where(Order.id == order_id))
    assert result.scalar_one_or_none() is None
