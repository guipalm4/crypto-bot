"""Unit tests for BalanceSnapshotRepository."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.infrastructure.database.engine import db_engine
from crypto_bot.infrastructure.database.models import Asset, BalanceSnapshot, Exchange
from crypto_bot.infrastructure.database.repositories.asset_repository import (
    AssetRepository,
)
from crypto_bot.infrastructure.database.repositories.balance_snapshot_repository import (
    BalanceSnapshotRepository,
)
from crypto_bot.infrastructure.database.repositories.exchange_repository import (
    ExchangeRepository,
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
async def test_create_balance_snapshot(db_session: AsyncSession) -> None:
    """Test creating a balance snapshot."""
    repo = BalanceSnapshotRepository(db_session)

    # Create test exchange and asset
    exchange_repo = ExchangeRepository(db_session)
    asset_repo = AssetRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    asset = await asset_repo.create(asset)

    snapshot = BalanceSnapshot(
        exchange_id=exchange.id,
        asset_id=asset.id,
        free_balance=1.5,
        locked_balance=0.5,
        total_balance=2.0,
        value_in_usd=100000.0,
        snapshot_at=datetime.now(timezone.utc),
    )

    created = await repo.create(snapshot)

    assert created.id is not None
    assert created.exchange_id == exchange.id
    assert created.asset_id == asset.id
    assert created.total_balance == 2.0


@pytest.mark.asyncio
async def test_exists_at_timestamp(db_session: AsyncSession) -> None:
    """Test checking if snapshot exists at timestamp."""
    repo = BalanceSnapshotRepository(db_session)

    exchange_repo = ExchangeRepository(db_session)
    asset_repo = AssetRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    asset = await asset_repo.create(asset)

    snapshot_at = datetime.now(timezone.utc)

    # Should not exist initially
    exists = await repo.exists_at_timestamp(exchange.id, asset.id, snapshot_at)
    assert exists is False

    # Create snapshot
    snapshot = BalanceSnapshot(
        exchange_id=exchange.id,
        asset_id=asset.id,
        free_balance=1.0,
        locked_balance=0.0,
        total_balance=1.0,
        snapshot_at=snapshot_at,
    )
    await repo.create(snapshot)

    # Should exist now
    exists = await repo.exists_at_timestamp(exchange.id, asset.id, snapshot_at)
    assert exists is True


@pytest.mark.asyncio
async def test_create_if_not_exists_new(db_session: AsyncSession) -> None:
    """Test create_if_not_exists with new snapshot."""
    repo = BalanceSnapshotRepository(db_session)

    exchange_repo = ExchangeRepository(db_session)
    asset_repo = AssetRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    asset = await asset_repo.create(asset)

    snapshot = BalanceSnapshot(
        exchange_id=exchange.id,
        asset_id=asset.id,
        free_balance=1.0,
        locked_balance=0.0,
        total_balance=1.0,
        snapshot_at=datetime.now(timezone.utc),
    )

    created = await repo.create_if_not_exists(snapshot)
    assert created is not None
    assert created.id is not None


@pytest.mark.asyncio
async def test_create_if_not_exists_duplicate(db_session: AsyncSession) -> None:
    """Test create_if_not_exists with duplicate snapshot."""
    repo = BalanceSnapshotRepository(db_session)

    exchange_repo = ExchangeRepository(db_session)
    asset_repo = AssetRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    asset = await asset_repo.create(asset)

    snapshot_at = datetime.now(timezone.utc)

    snapshot1 = BalanceSnapshot(
        exchange_id=exchange.id,
        asset_id=asset.id,
        free_balance=1.0,
        locked_balance=0.0,
        total_balance=1.0,
        snapshot_at=snapshot_at,
    )
    await repo.create(snapshot1)

    # Try to create duplicate
    snapshot2 = BalanceSnapshot(
        exchange_id=exchange.id,
        asset_id=asset.id,
        free_balance=2.0,  # Different balance
        locked_balance=0.0,
        total_balance=2.0,
        snapshot_at=snapshot_at,  # Same timestamp
    )

    created = await repo.create_if_not_exists(snapshot2)
    assert created is None  # Should return None for duplicate


@pytest.mark.asyncio
async def test_get_by_exchange_and_asset(db_session: AsyncSession) -> None:
    """Test getting snapshots by exchange and asset."""
    repo = BalanceSnapshotRepository(db_session)

    exchange_repo = ExchangeRepository(db_session)
    asset_repo = AssetRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    asset = await asset_repo.create(asset)

    # Create multiple snapshots
    for i in range(3):
        snapshot = BalanceSnapshot(
            exchange_id=exchange.id,
            asset_id=asset.id,
            free_balance=float(i),
            locked_balance=0.0,
            total_balance=float(i),
            snapshot_at=datetime.now(timezone.utc),
        )
        await repo.create(snapshot)

    snapshots = await repo.get_by_exchange_and_asset(exchange.id, asset.id, limit=10)

    assert len(snapshots) == 3
    # Should be ordered by snapshot_at descending
    assert snapshots[0].snapshot_at >= snapshots[-1].snapshot_at


@pytest.mark.asyncio
async def test_get_latest(db_session: AsyncSession) -> None:
    """Test getting latest snapshot."""
    repo = BalanceSnapshotRepository(db_session)

    exchange_repo = ExchangeRepository(db_session)
    asset_repo = AssetRepository(db_session)

    exchange = Exchange(name="test_exchange", is_active=True, is_testnet=False)
    exchange = await exchange_repo.create(exchange)

    asset = Asset(symbol="BTC", name="Bitcoin", is_active=True)
    asset = await asset_repo.create(asset)

    # Create older snapshot
    snapshot1 = BalanceSnapshot(
        exchange_id=exchange.id,
        asset_id=asset.id,
        free_balance=1.0,
        locked_balance=0.0,
        total_balance=1.0,
        snapshot_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    await repo.create(snapshot1)

    # Create newer snapshot
    snapshot2 = BalanceSnapshot(
        exchange_id=exchange.id,
        asset_id=asset.id,
        free_balance=2.0,
        locked_balance=0.0,
        total_balance=2.0,
        snapshot_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    await repo.create(snapshot2)

    latest = await repo.get_latest(exchange.id, asset.id)

    assert latest is not None
    assert latest.total_balance == 2.0  # Should be the newer one
