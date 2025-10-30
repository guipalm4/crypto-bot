"""Unit tests for MarketDataRepository."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.infrastructure.database.engine import db_engine
from crypto_bot.infrastructure.database.models import (
    Asset,
    Exchange,
    MarketData,
    TradingPair,
)
from crypto_bot.infrastructure.database.repositories.asset_repository import (
    AssetRepository,
)
from crypto_bot.infrastructure.database.repositories.exchange_repository import (
    ExchangeRepository,
)
from crypto_bot.infrastructure.database.repositories.market_data_repository import (
    MarketDataRepository,
)
from crypto_bot.infrastructure.database.repositories.trading_pair_repository import (
    TradingPairRepository,
)


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Set up test database tables."""
    from crypto_bot.infrastructure.database.base import Base

    engine = db_engine.create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await db_engine.close()


@pytest_asyncio.fixture
async def db_session(setup_database):
    """Provide an async database session for tests."""
    session_factory = db_engine.get_session_factory()
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_create_market_data(db_session: AsyncSession) -> None:
    """Test creating market data."""
    repo = MarketDataRepository(db_session)

    # Create test data
    exchange_repo = ExchangeRepository(db_session)
    asset_repo = AssetRepository(db_session)
    trading_pair_repo = TradingPairRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    base_asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    base_asset = await asset_repo.create(base_asset)

    quote_asset = Asset(symbol="USDT", name="Tether", is_active=True)
    quote_asset = await asset_repo.create(quote_asset)

    trading_pair = TradingPair(
        base_asset_id=base_asset.id,
        quote_asset_id=quote_asset.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
        is_active=True,
    )
    trading_pair = await trading_pair_repo.create(trading_pair)

    market_data = MarketData(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        timeframe="1m",
        timestamp=datetime.now(timezone.utc),
        open=50000.0,
        high=51000.0,
        low=49000.0,
        close=50500.0,
        volume=100.0,
    )

    created = await repo.create(market_data)

    assert created.id is not None
    assert created.trading_pair_id == trading_pair.id
    assert created.close == 50500.0


@pytest.mark.asyncio
async def test_exists_at_timestamp(db_session: AsyncSession) -> None:
    """Test checking if market data exists at timestamp."""
    repo = MarketDataRepository(db_session)

    exchange_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.exchange_repository",
        fromlist=["ExchangeRepository"],
    ).ExchangeRepository(db_session)
    asset_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.asset_repository",
        fromlist=["AssetRepository"],
    ).AssetRepository(db_session)
    trading_pair_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.trading_pair_repository",
        fromlist=["TradingPairRepository"],
    ).TradingPairRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    base_asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    base_asset = await asset_repo.create(base_asset)

    quote_asset = Asset(symbol="USDT", name="Tether", is_active=True)
    quote_asset = await asset_repo.create(quote_asset)

    trading_pair = TradingPair(
        base_asset_id=base_asset.id,
        quote_asset_id=quote_asset.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
        is_active=True,
    )
    trading_pair = await trading_pair_repo.create(trading_pair)

    timestamp = datetime.now(timezone.utc)
    timeframe = "1m"

    # Should not exist initially
    exists = await repo.exists_at_timestamp(
        trading_pair.id, exchange.id, timeframe, timestamp
    )
    assert exists is False

    # Create market data
    market_data = MarketData(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        timeframe=timeframe,
        timestamp=timestamp,
        open=50000.0,
        high=51000.0,
        low=49000.0,
        close=50500.0,
        volume=100.0,
    )
    await repo.create(market_data)

    # Should exist now
    exists = await repo.exists_at_timestamp(
        trading_pair.id, exchange.id, timeframe, timestamp
    )
    assert exists is True


@pytest.mark.asyncio
async def test_create_if_not_exists_new(db_session: AsyncSession) -> None:
    """Test create_if_not_exists with new market data."""
    repo = MarketDataRepository(db_session)

    exchange_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.exchange_repository",
        fromlist=["ExchangeRepository"],
    ).ExchangeRepository(db_session)
    asset_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.asset_repository",
        fromlist=["AssetRepository"],
    ).AssetRepository(db_session)
    trading_pair_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.trading_pair_repository",
        fromlist=["TradingPairRepository"],
    ).TradingPairRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    base_asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    base_asset = await asset_repo.create(base_asset)

    quote_asset = Asset(symbol="USDT", name="Tether", is_active=True)
    quote_asset = await asset_repo.create(quote_asset)

    trading_pair = TradingPair(
        base_asset_id=base_asset.id,
        quote_asset_id=quote_asset.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
        is_active=True,
    )
    trading_pair = await trading_pair_repo.create(trading_pair)

    market_data = MarketData(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        timeframe="1m",
        timestamp=datetime.now(timezone.utc),
        open=50000.0,
        high=51000.0,
        low=49000.0,
        close=50500.0,
        volume=100.0,
    )

    created = await repo.create_if_not_exists(market_data)
    assert created is not None
    assert created.id is not None


@pytest.mark.asyncio
async def test_create_if_not_exists_duplicate(db_session: AsyncSession) -> None:
    """Test create_if_not_exists with duplicate market data."""
    repo = MarketDataRepository(db_session)

    exchange_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.exchange_repository",
        fromlist=["ExchangeRepository"],
    ).ExchangeRepository(db_session)
    asset_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.asset_repository",
        fromlist=["AssetRepository"],
    ).AssetRepository(db_session)
    trading_pair_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.trading_pair_repository",
        fromlist=["TradingPairRepository"],
    ).TradingPairRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    base_asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    base_asset = await asset_repo.create(base_asset)

    quote_asset = Asset(symbol="USDT", name="Tether", is_active=True)
    quote_asset = await asset_repo.create(quote_asset)

    trading_pair = TradingPair(
        base_asset_id=base_asset.id,
        quote_asset_id=quote_asset.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
        is_active=True,
    )
    trading_pair = await trading_pair_repo.create(trading_pair)

    timestamp = datetime.now(timezone.utc)
    timeframe = "1m"

    market_data1 = MarketData(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        timeframe=timeframe,
        timestamp=timestamp,
        open=50000.0,
        high=51000.0,
        low=49000.0,
        close=50500.0,
        volume=100.0,
    )
    await repo.create(market_data1)

    # Try to create duplicate
    market_data2 = MarketData(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        timeframe=timeframe,
        timestamp=timestamp,  # Same timestamp
        open=60000.0,  # Different price
        high=61000.0,
        low=59000.0,
        close=60500.0,
        volume=200.0,
    )

    created = await repo.create_if_not_exists(market_data2)
    assert created is None  # Should return None for duplicate


@pytest.mark.asyncio
async def test_get_by_trading_pair_and_timeframe(db_session: AsyncSession) -> None:
    """Test getting market data by trading pair and timeframe."""
    repo = MarketDataRepository(db_session)

    exchange_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.exchange_repository",
        fromlist=["ExchangeRepository"],
    ).ExchangeRepository(db_session)
    asset_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.asset_repository",
        fromlist=["AssetRepository"],
    ).AssetRepository(db_session)
    trading_pair_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.trading_pair_repository",
        fromlist=["TradingPairRepository"],
    ).TradingPairRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    base_asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    base_asset = await asset_repo.create(base_asset)

    quote_asset = Asset(symbol="USDT", name="Tether", is_active=True)
    quote_asset = await asset_repo.create(quote_asset)

    trading_pair = TradingPair(
        base_asset_id=base_asset.id,
        quote_asset_id=quote_asset.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
        is_active=True,
    )
    trading_pair = await trading_pair_repo.create(trading_pair)

    # Create multiple market data entries
    for i in range(3):
        market_data = MarketData(
            trading_pair_id=trading_pair.id,
            exchange_id=exchange.id,
            timeframe="1m",
            timestamp=datetime(2024, 1, 1, i + 1, tzinfo=timezone.utc),
            open=50000.0 + i * 100,
            high=51000.0 + i * 100,
            low=49000.0 + i * 100,
            close=50500.0 + i * 100,
            volume=100.0 + i * 10,
        )
        await repo.create(market_data)

    records = await repo.get_by_trading_pair_and_timeframe(
        trading_pair.id, exchange.id, "1m"
    )

    assert len(records) == 3
    # Should be ordered by timestamp ascending
    assert records[0].timestamp <= records[-1].timestamp


@pytest.mark.asyncio
async def test_get_latest(db_session: AsyncSession) -> None:
    """Test getting latest market data."""
    repo = MarketDataRepository(db_session)

    exchange_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.exchange_repository",
        fromlist=["ExchangeRepository"],
    ).ExchangeRepository(db_session)
    asset_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.asset_repository",
        fromlist=["AssetRepository"],
    ).AssetRepository(db_session)
    trading_pair_repo = __import__(
        "crypto_bot.infrastructure.database.repositories.trading_pair_repository",
        fromlist=["TradingPairRepository"],
    ).TradingPairRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    base_asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    base_asset = await asset_repo.create(base_asset)

    quote_asset = Asset(symbol="USDT", name="Tether", is_active=True)
    quote_asset = await asset_repo.create(quote_asset)

    trading_pair = TradingPair(
        base_asset_id=base_asset.id,
        quote_asset_id=quote_asset.id,
        exchange_id=exchange.id,
        symbol="BTC/USDT",
        min_order_size=0.001,
        tick_size=0.01,
        is_active=True,
    )
    trading_pair = await trading_pair_repo.create(trading_pair)

    # Create older market data
    market_data1 = MarketData(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        timeframe="1m",
        timestamp=datetime(2024, 1, 1, 1, tzinfo=timezone.utc),
        open=50000.0,
        high=51000.0,
        low=49000.0,
        close=50500.0,
        volume=100.0,
    )
    await repo.create(market_data1)

    # Create newer market data
    market_data2 = MarketData(
        trading_pair_id=trading_pair.id,
        exchange_id=exchange.id,
        timeframe="1m",
        timestamp=datetime(2024, 1, 1, 2, tzinfo=timezone.utc),
        open=60000.0,
        high=61000.0,
        low=59000.0,
        close=60500.0,
        volume=200.0,
    )
    await repo.create(market_data2)

    latest = await repo.get_latest(trading_pair.id, exchange.id, "1m")

    assert latest is not None
    assert latest.close == 60500.0  # Should be the newer one
