"""
Unit tests for SnapshotService.

Tests balance snapshot and market data recording with mocked dependencies.
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from freezegun import freeze_time

from crypto_bot.application.dtos.order import BalanceDTO
from crypto_bot.application.services.snapshot_service import SnapshotService
from crypto_bot.infrastructure.database.models import Asset, BalanceSnapshot, Exchange


@pytest.fixture
def mock_exchange_plugin() -> MagicMock:
    """Create a mock exchange plugin."""
    plugin = MagicMock()
    plugin.initialize = AsyncMock()
    plugin.load_markets = AsyncMock()
    plugin.fetch_balance = AsyncMock()
    plugin.fetch_ohlcv = AsyncMock()
    return plugin


@pytest.fixture
def mock_exchange_registry(mock_exchange_plugin: MagicMock) -> MagicMock:
    """Create a mock exchange registry."""
    registry = MagicMock()
    registry.get_exchange = MagicMock(return_value=mock_exchange_plugin)
    return registry


@pytest.fixture
def mock_exchange_repo() -> MagicMock:
    """Create a mock exchange repository."""
    repo = MagicMock()
    repo.get_active_exchanges = AsyncMock()
    return repo


@pytest.fixture
def mock_asset_repo() -> MagicMock:
    """Create a mock asset repository."""
    repo = MagicMock()
    repo.get_by_symbol = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_snapshot_repo() -> MagicMock:
    """Create a mock balance snapshot repository."""
    repo = MagicMock()
    repo.create_if_not_exists = AsyncMock()
    return repo


@pytest.fixture
def mock_market_data_repo() -> MagicMock:
    """Create a mock market data repository."""
    repo = MagicMock()
    repo.create_if_not_exists = AsyncMock()
    return repo


@pytest.fixture
def mock_trading_pair_repo() -> MagicMock:
    """Create a mock trading pair repository."""
    repo = MagicMock()
    repo.get_by_exchange = AsyncMock()
    return repo


@pytest.fixture
def snapshot_service() -> SnapshotService:
    """Create a SnapshotService instance for testing."""
    return SnapshotService(
        balance_snapshot_interval=60.0,
        market_data_interval=30.0,
        enabled_exchanges=["binance"],
        enabled_symbols=["BTC/USDT"],
        default_timeframe="1m",
    )


@pytest.mark.asyncio
class TestSnapshotService:
    """Test suite for SnapshotService."""

    async def test_initialization(self, snapshot_service: SnapshotService) -> None:
        """Test service initialization."""
        assert snapshot_service._balance_snapshot_interval == 60.0
        assert snapshot_service._market_data_interval == 30.0
        assert snapshot_service._enabled_exchanges == ["binance"]
        assert snapshot_service._enabled_symbols == ["BTC/USDT"]
        assert snapshot_service._default_timeframe == "1m"
        assert snapshot_service.is_running() is False

    async def test_start_stop_service(self, snapshot_service: SnapshotService) -> None:
        """Test starting and stopping the service."""
        # Start service
        await snapshot_service.start()
        assert snapshot_service.is_running() is True
        assert snapshot_service._balance_task is not None
        assert snapshot_service._market_data_task is not None

        # Stop service
        await snapshot_service.stop()
        assert snapshot_service.is_running() is False

    async def test_start_already_running(
        self, snapshot_service: SnapshotService
    ) -> None:
        """Test starting service when already running."""
        await snapshot_service.start()
        assert snapshot_service.is_running() is True

        # Try to start again
        await snapshot_service.start()  # Should not raise error
        assert snapshot_service.is_running() is True

        await snapshot_service.stop()

    async def test_stop_not_running(self, snapshot_service: SnapshotService) -> None:
        """Test stopping service when not running."""
        assert snapshot_service.is_running() is False
        await snapshot_service.stop()  # Should not raise error
        assert snapshot_service.is_running() is False

    @patch("crypto_bot.application.services.snapshot_service.db_engine")
    @patch("crypto_bot.application.services.snapshot_service.exchange_registry")
    async def test_record_balance_snapshots_success(
        self,
        mock_registry: MagicMock,
        mock_db_engine: MagicMock,
        snapshot_service: SnapshotService,
        mock_exchange_plugin: MagicMock,
        mock_exchange_repo: MagicMock,
        mock_asset_repo: MagicMock,
        mock_snapshot_repo: MagicMock,
    ) -> None:
        """Test successful balance snapshot recording."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        # Create async context manager for session factory
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_engine.get_session_factory = MagicMock(
            return_value=mock_session_factory
        )

        mock_registry.get_exchange = MagicMock(return_value=mock_exchange_plugin)

        # Create test exchange
        test_exchange = Exchange(
            id=uuid4(), name="binance", is_active=True, is_testnet=False
        )
        mock_exchange_repo.get_active_exchanges = AsyncMock(
            return_value=[test_exchange]
        )

        # Mock balance data
        balance_dto = BalanceDTO(
            exchange="binance",
            currency="BTC",
            free=Decimal("1.0"),
            used=Decimal("0.1"),
            total=Decimal("1.1"),
            timestamp=datetime.now(UTC),
        )
        mock_exchange_plugin.fetch_balance = AsyncMock(
            return_value={"BTC": balance_dto}
        )

        # Mock asset repository
        test_asset = Asset(id=uuid4(), symbol="BTC", name="Bitcoin", is_active=True)
        mock_asset_repo.get_by_symbol = AsyncMock(return_value=None)
        mock_asset_repo.create = AsyncMock(return_value=test_asset)

        # Mock snapshot repository
        created_snapshot = BalanceSnapshot(
            id=uuid4(),
            exchange_id=test_exchange.id,
            asset_id=test_asset.id,
            free_balance=1.0,
            locked_balance=0.1,
            total_balance=1.1,
            snapshot_at=datetime.now(UTC),
        )
        mock_snapshot_repo.create_if_not_exists = AsyncMock(
            return_value=created_snapshot
        )

        # Inject repositories into session
        with (
            patch(
                "crypto_bot.application.services.snapshot_service.ExchangeRepository",
                return_value=mock_exchange_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.AssetRepository",
                return_value=mock_asset_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.BalanceSnapshotRepository",
                return_value=mock_snapshot_repo,
            ),
        ):
            await snapshot_service._record_balance_snapshots()

        # Verify
        mock_exchange_plugin.initialize.assert_called_once()
        mock_exchange_plugin.fetch_balance.assert_called_once()
        mock_asset_repo.get_by_symbol.assert_called_once_with("BTC")
        mock_snapshot_repo.create_if_not_exists.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("crypto_bot.application.services.snapshot_service.db_engine")
    @patch("crypto_bot.application.services.snapshot_service.exchange_registry")
    async def test_record_balance_snapshots_skip_zero_balance(
        self,
        mock_registry: MagicMock,
        mock_db_engine: MagicMock,
        snapshot_service: SnapshotService,
        mock_exchange_plugin: MagicMock,
        mock_exchange_repo: MagicMock,
    ) -> None:
        """Test that zero balances are skipped."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()

        # Create async context manager for session factory
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_engine.get_session_factory = MagicMock(
            return_value=mock_session_factory
        )

        mock_registry.get_exchange = MagicMock(return_value=mock_exchange_plugin)

        test_exchange = Exchange(
            id=uuid4(), name="binance", is_active=True, is_testnet=False
        )
        mock_exchange_repo.get_active_exchanges = AsyncMock(
            return_value=[test_exchange]
        )

        # Mock zero balance
        zero_balance = BalanceDTO(
            exchange="binance",
            currency="BTC",
            free=Decimal("0"),
            used=Decimal("0"),
            total=Decimal("0"),
            timestamp=datetime.now(UTC),
        )
        mock_exchange_plugin.fetch_balance = AsyncMock(
            return_value={"BTC": zero_balance}
        )

        mock_snapshot_repo = MagicMock()
        mock_snapshot_repo.create_if_not_exists = AsyncMock()

        with (
            patch(
                "crypto_bot.application.services.snapshot_service.ExchangeRepository",
                return_value=mock_exchange_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.BalanceSnapshotRepository",
                return_value=mock_snapshot_repo,
            ),
        ):
            await snapshot_service._record_balance_snapshots()

        # Verify snapshot was not created for zero balance
        mock_snapshot_repo.create_if_not_exists.assert_not_called()

    @patch("crypto_bot.application.services.snapshot_service.db_engine")
    @patch("crypto_bot.application.services.snapshot_service.exchange_registry")
    async def test_record_balance_snapshots_duplicate_handling(
        self,
        mock_registry: MagicMock,
        mock_db_engine: MagicMock,
        snapshot_service: SnapshotService,
        mock_exchange_plugin: MagicMock,
        mock_exchange_repo: MagicMock,
        mock_asset_repo: MagicMock,
        mock_snapshot_repo: MagicMock,
    ) -> None:
        """Test duplicate snapshot handling."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()

        # Create async context manager for session factory
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_engine.get_session_factory = MagicMock(
            return_value=mock_session_factory
        )

        mock_registry.get_exchange = MagicMock(return_value=mock_exchange_plugin)

        test_exchange = Exchange(
            id=uuid4(), name="binance", is_active=True, is_testnet=False
        )
        mock_exchange_repo.get_active_exchanges = AsyncMock(
            return_value=[test_exchange]
        )

        balance_dto = BalanceDTO(
            exchange="binance",
            currency="BTC",
            free=Decimal("1.0"),
            used=Decimal("0.1"),
            total=Decimal("1.1"),
            timestamp=datetime.now(UTC),
        )
        mock_exchange_plugin.fetch_balance = AsyncMock(
            return_value={"BTC": balance_dto}
        )

        test_asset = Asset(id=uuid4(), symbol="BTC", name="Bitcoin", is_active=True)
        mock_asset_repo.get_by_symbol = AsyncMock(return_value=test_asset)

        # Mock duplicate (returns None)
        mock_snapshot_repo.create_if_not_exists = AsyncMock(return_value=None)

        with (
            patch(
                "crypto_bot.application.services.snapshot_service.ExchangeRepository",
                return_value=mock_exchange_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.AssetRepository",
                return_value=mock_asset_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.BalanceSnapshotRepository",
                return_value=mock_snapshot_repo,
            ),
        ):
            await snapshot_service._record_balance_snapshots()

        # Verify duplicate was handled (returns None)
        mock_snapshot_repo.create_if_not_exists.assert_called_once()

    @patch("crypto_bot.application.services.snapshot_service.db_engine")
    @patch("crypto_bot.application.services.snapshot_service.exchange_registry")
    async def test_record_market_data_success(
        self,
        mock_registry: MagicMock,
        mock_db_engine: MagicMock,
        snapshot_service: SnapshotService,
        mock_exchange_plugin: MagicMock,
        mock_exchange_repo: MagicMock,
        mock_trading_pair_repo: MagicMock,
        mock_market_data_repo: MagicMock,
    ) -> None:
        """Test successful market data recording."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()

        # Create async context manager for session factory
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_engine.get_session_factory = MagicMock(
            return_value=mock_session_factory
        )

        mock_registry.get_exchange = MagicMock(return_value=mock_exchange_plugin)

        test_exchange = Exchange(
            id=uuid4(), name="binance", is_active=True, is_testnet=False
        )
        mock_exchange_repo.get_active_exchanges = AsyncMock(
            return_value=[test_exchange]
        )

        from crypto_bot.infrastructure.database.models import TradingPair

        test_pair = TradingPair(
            id=uuid4(),
            symbol="BTC/USDT",
            exchange_id=test_exchange.id,
            is_active=True,
        )
        mock_trading_pair_repo.get_by_exchange = AsyncMock(return_value=[test_pair])

        # Mock OHLCV data: [timestamp_ms, open, high, low, close, volume]
        timestamp_ms = int(datetime.now(UTC).timestamp() * 1000)
        ohlcv_data = [[timestamp_ms, 50000.0, 51000.0, 49000.0, 50500.0, 100.5]]
        mock_exchange_plugin.fetch_ohlcv = AsyncMock(return_value=ohlcv_data)

        created_market_data = MagicMock()
        mock_market_data_repo.create_if_not_exists = AsyncMock(
            return_value=created_market_data
        )

        with (
            patch(
                "crypto_bot.application.services.snapshot_service.ExchangeRepository",
                return_value=mock_exchange_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.TradingPairRepository",
                return_value=mock_trading_pair_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.MarketDataRepository",
                return_value=mock_market_data_repo,
            ),
        ):
            await snapshot_service._record_market_data()

        # Verify
        mock_exchange_plugin.initialize.assert_called_once()
        mock_exchange_plugin.load_markets.assert_called_once()
        mock_exchange_plugin.fetch_ohlcv.assert_called_once_with(
            "BTC/USDT", timeframe="1m", limit=1
        )
        mock_market_data_repo.create_if_not_exists.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("crypto_bot.application.services.snapshot_service.db_engine")
    @patch("crypto_bot.application.services.snapshot_service.exchange_registry")
    async def test_get_enabled_exchanges_all(
        self,
        mock_registry: MagicMock,
        mock_db_engine: MagicMock,
        snapshot_service: SnapshotService,
        mock_exchange_repo: MagicMock,
    ) -> None:
        """Test getting all enabled exchanges when no filter."""
        # Create service without exchange filter
        service = SnapshotService(enabled_exchanges=None)

        test_exchanges = [
            Exchange(id=uuid4(), name="binance", is_active=True, is_testnet=False),
            Exchange(id=uuid4(), name="coinbase", is_active=True, is_testnet=False),
        ]
        mock_exchange_repo.get_active_exchanges = AsyncMock(return_value=test_exchanges)

        result = await service._get_enabled_exchanges(mock_exchange_repo)

        assert len(result) == 2
        assert result == test_exchanges

    @patch("crypto_bot.application.services.snapshot_service.db_engine")
    @patch("crypto_bot.application.services.snapshot_service.exchange_registry")
    async def test_get_enabled_exchanges_filtered(
        self,
        mock_registry: MagicMock,
        mock_db_engine: MagicMock,
        snapshot_service: SnapshotService,
        mock_exchange_repo: MagicMock,
    ) -> None:
        """Test filtering enabled exchanges."""
        test_exchanges = [
            Exchange(id=uuid4(), name="binance", is_active=True, is_testnet=False),
            Exchange(id=uuid4(), name="coinbase", is_active=True, is_testnet=False),
            Exchange(id=uuid4(), name="kraken", is_active=True, is_testnet=False),
        ]
        mock_exchange_repo.get_active_exchanges = AsyncMock(return_value=test_exchanges)

        result = await snapshot_service._get_enabled_exchanges(mock_exchange_repo)

        # Should only return binance (enabled in fixture)
        assert len(result) == 1
        assert result[0].name == "binance"

    @patch("crypto_bot.application.services.snapshot_service.db_engine")
    @patch("crypto_bot.application.services.snapshot_service.exchange_registry")
    async def test_record_balance_snapshot_now(
        self,
        mock_registry: MagicMock,
        mock_db_engine: MagicMock,
        snapshot_service: SnapshotService,
        mock_exchange_plugin: MagicMock,
        mock_exchange_repo: MagicMock,
        mock_asset_repo: MagicMock,
        mock_snapshot_repo: MagicMock,
    ) -> None:
        """Test manual balance snapshot triggering."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()

        # Create async context manager for session factory
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_engine.get_session_factory = MagicMock(
            return_value=mock_session_factory
        )

        mock_registry.get_exchange = MagicMock(return_value=mock_exchange_plugin)

        test_exchange = Exchange(
            id=uuid4(), name="binance", is_active=True, is_testnet=False
        )
        mock_exchange_repo.get_active_exchanges = AsyncMock(
            return_value=[test_exchange]
        )

        balance_dto = BalanceDTO(
            exchange="binance",
            currency="BTC",
            free=Decimal("1.0"),
            used=Decimal("0.1"),
            total=Decimal("1.1"),
            timestamp=datetime.now(UTC),
        )
        mock_exchange_plugin.fetch_balance = AsyncMock(
            return_value={"BTC": balance_dto}
        )

        test_asset = Asset(id=uuid4(), symbol="BTC", name="Bitcoin", is_active=True)
        mock_asset_repo.get_by_symbol = AsyncMock(return_value=None)
        mock_asset_repo.create = AsyncMock(return_value=test_asset)

        created_snapshot = BalanceSnapshot(
            id=uuid4(),
            exchange_id=test_exchange.id,
            asset_id=test_asset.id,
            free_balance=1.0,
            locked_balance=0.1,
            total_balance=1.1,
            snapshot_at=datetime.now(UTC),
        )
        mock_snapshot_repo.create_if_not_exists = AsyncMock(
            return_value=created_snapshot
        )

        with (
            patch(
                "crypto_bot.application.services.snapshot_service.ExchangeRepository",
                return_value=mock_exchange_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.AssetRepository",
                return_value=mock_asset_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.BalanceSnapshotRepository",
                return_value=mock_snapshot_repo,
            ),
        ):
            count = await snapshot_service.record_balance_snapshot_now()

        assert count == 1
        mock_snapshot_repo.create_if_not_exists.assert_called_once()

    @patch("crypto_bot.application.services.snapshot_service.db_engine")
    @patch("crypto_bot.application.services.snapshot_service.exchange_registry")
    async def test_record_market_data_now(
        self,
        mock_registry: MagicMock,
        mock_db_engine: MagicMock,
        snapshot_service: SnapshotService,
        mock_exchange_plugin: MagicMock,
        mock_exchange_repo: MagicMock,
        mock_trading_pair_repo: MagicMock,
        mock_market_data_repo: MagicMock,
    ) -> None:
        """Test manual market data recording."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()

        # Create async context manager for session factory
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_engine.get_session_factory = MagicMock(
            return_value=mock_session_factory
        )

        mock_registry.get_exchange = MagicMock(return_value=mock_exchange_plugin)

        test_exchange = Exchange(
            id=uuid4(), name="binance", is_active=True, is_testnet=False
        )
        mock_exchange_repo.get_active_exchanges = AsyncMock(
            return_value=[test_exchange]
        )

        from crypto_bot.infrastructure.database.models import TradingPair

        test_pair = TradingPair(
            id=uuid4(),
            symbol="BTC/USDT",
            exchange_id=test_exchange.id,
            is_active=True,
        )
        mock_trading_pair_repo.get_by_exchange = AsyncMock(return_value=[test_pair])

        timestamp_ms = int(datetime.now(UTC).timestamp() * 1000)
        ohlcv_data = [[timestamp_ms, 50000.0, 51000.0, 49000.0, 50500.0, 100.5]]
        mock_exchange_plugin.fetch_ohlcv = AsyncMock(return_value=ohlcv_data)

        created_market_data = MagicMock()
        mock_market_data_repo.create_if_not_exists = AsyncMock(
            return_value=created_market_data
        )

        with (
            patch(
                "crypto_bot.application.services.snapshot_service.ExchangeRepository",
                return_value=mock_exchange_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.TradingPairRepository",
                return_value=mock_trading_pair_repo,
            ),
            patch(
                "crypto_bot.application.services.snapshot_service.MarketDataRepository",
                return_value=mock_market_data_repo,
            ),
        ):
            count = await snapshot_service.record_market_data_now()

        assert count == 1
        mock_market_data_repo.create_if_not_exists.assert_called_once()

    async def test_balance_snapshot_loop_error_handling(
        self, snapshot_service: SnapshotService
    ) -> None:
        """Test error handling in balance snapshot loop."""
        with patch.object(
            snapshot_service,
            "_record_balance_snapshots",
            side_effect=Exception("Test error"),
        ):
            snapshot_service._running = True

            # Run loop for a short time
            task = asyncio.create_task(snapshot_service._balance_snapshot_loop())
            await asyncio.sleep(0.1)
            snapshot_service._running = False
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Loop should have handled the error and continued

    async def test_market_data_loop_error_handling(
        self, snapshot_service: SnapshotService
    ) -> None:
        """Test error handling in market data loop."""
        with patch.object(
            snapshot_service, "_record_market_data", side_effect=Exception("Test error")
        ):
            snapshot_service._running = True

            # Run loop for a short time
            task = asyncio.create_task(snapshot_service._market_data_loop())
            await asyncio.sleep(0.1)
            snapshot_service._running = False
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Loop should have handled the error and continued
