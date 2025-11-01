"""
End-to-End tests simulating full trading flows.

These tests simulate complete trading scenarios from strategy signal generation
through order execution to position management, validating system state transitions
and data consistency across all components.
"""

import os

# Set test encryption key BEFORE importing any application modules
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_32_bytes_long!!"

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pandas as pd
import pytest
import pytest_asyncio

from crypto_bot.application.dtos.order import (
    BalanceDTO,
    CreateOrderRequest,
    OrderDTO,
    OrderSide,
    OrderStatus,
    OrderType,
    RetryPolicy,
)
from crypto_bot.application.services.risk_service import RiskService
from crypto_bot.application.services.strategy_orchestrator import (
    StrategyExecutionContext,
    StrategyOrchestrator,
)
from crypto_bot.application.services.trading_service import TradingService
from crypto_bot.domain.repositories.strategy_repository import IStrategyRepository
from crypto_bot.infrastructure.config.risk_config import (
    DrawdownControlConfig,
    ExposureLimitConfig,
    MaxConcurrentTradesConfig,
    RiskConfig,
    StopLossConfig,
    TakeProfitConfig,
    TrailingStopConfig,
)
from crypto_bot.infrastructure.database import Base, get_db_session
from crypto_bot.infrastructure.database.engine import db_engine
from crypto_bot.infrastructure.database.models import (
    Asset,
    Exchange,
    Order,
    Position,
    PositionSide,
    PositionStatus,
    TradingPair,
)
from crypto_bot.infrastructure.database.models import (
    OrderSide as OrderSideEnum,
)
from crypto_bot.infrastructure.database.models import (
    OrderStatus as OrderStatusEnum,
)
from crypto_bot.infrastructure.database.models import (
    OrderType as OrderTypeEnum,
)
from crypto_bot.infrastructure.database.models import (
    Strategy as StrategyModel,
)
from crypto_bot.infrastructure.database.repositories import (
    AssetRepository,
    ExchangeRepository,
    OrderRepository,
    PositionRepository,
    StrategyRepository,
    TradingPairRepository,
)
from crypto_bot.plugins.exchanges.base_ccxt_plugin import ExchangeBase
from crypto_bot.plugins.strategies.base import Strategy as StrategyBase
from crypto_bot.plugins.strategies.base import StrategySignal


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
async def order_repo(db_session):
    """Provide an order repository."""
    return OrderRepository(db_session)


@pytest_asyncio.fixture
async def position_repo(db_session):
    """Provide a position repository."""
    return PositionRepository(db_session)


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
async def test_trading_pair(trading_pair_repo, db_session, test_exchange, test_assets):
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


@pytest_asyncio.fixture
async def test_strategy(strategy_repo, db_session, faker):
    """Create a test strategy in the database."""
    strategy = StrategyModel(
        name=faker.word(),
        plugin_name="test_strategy",
        description="Test strategy for E2E tests",
        parameters_json={
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "quantity": "0.001",
        },
        is_active=True,
    )
    created = await strategy_repo.create(strategy)
    await db_session.commit()
    return created


@pytest_asyncio.fixture
def mock_strategy_class():
    """Create a mock strategy class for testing."""

    class TestStrategy(StrategyBase):
        name = "test_strategy"

        def validate_parameters(self, params: dict) -> None:
            """Validate parameters."""
            pass

        def generate_signal(
            self, market_data: pd.DataFrame, params: dict
        ) -> StrategySignal:
            """Generate a buy signal."""
            return StrategySignal(
                action="buy",
                strength=0.8,
                metadata={"quantity": params.get("quantity", "0.001")},
            )

        def reset_state(self) -> None:
            """Reset strategy state."""
            pass

    return TestStrategy


@pytest_asyncio.fixture
def mock_exchange_plugin():
    """Create a mock exchange plugin."""
    plugin = MagicMock(spec=ExchangeBase)
    plugin.fetch_ohlcv = AsyncMock(
        return_value=[
            [1609459200000, 50000, 51000, 49000, 50000, 1000],  # OHLCV data
            [1609462800000, 50000, 50500, 49500, 50200, 1100],
        ]
    )
    plugin.fetch_ticker = AsyncMock(
        return_value={"symbol": "BTC/USDT", "last": 50000.0}
    )
    plugin.fetch_balance = AsyncMock(
        return_value={
            "USDT": BalanceDTO(
                currency="USDT",
                free=Decimal("1000.0"),
                used=Decimal("0.0"),
                total=Decimal("1000.0"),
                exchange="binance",
                timestamp=datetime.now(UTC),
            )
        }
    )
    plugin.create_order = AsyncMock()
    plugin.cancel_order = AsyncMock()
    return plugin


@pytest_asyncio.fixture
def mock_risk_service():
    """Create a mock risk service."""
    service = MagicMock(spec=RiskService)
    service.config = RiskConfig(
        stop_loss=StopLossConfig(
            enabled=True, percentage=Decimal("2.0"), cooldown_seconds=60
        ),
        take_profit=TakeProfitConfig(
            enabled=True, percentage=Decimal("5.0"), cooldown_seconds=60
        ),
        exposure_limit=ExposureLimitConfig(
            max_per_asset=Decimal("10000.0"),
            max_per_exchange=Decimal("30000.0"),
            max_total=Decimal("50000.0"),
        ),
        trailing_stop=TrailingStopConfig(
            trailing_percentage=Decimal("3.0"), activation_percentage=Decimal("5.0")
        ),
        max_concurrent_trades=MaxConcurrentTradesConfig(
            max_trades=5, max_per_exchange=3
        ),
        drawdown_control=DrawdownControlConfig(
            max_drawdown_percentage=Decimal("15.0"),
            emergency_exit_percentage=Decimal("20.0"),
        ),
    )
    service.evaluate_risk = AsyncMock(return_value=None)  # No risk actions
    return service


@pytest_asyncio.fixture
def mock_trading_service():
    """Create a mock trading service."""
    service = MagicMock(spec=TradingService)

    async def create_order_mock(request: CreateOrderRequest) -> OrderDTO:
        """Mock order creation."""
        return OrderDTO(
            id=str(uuid4()),
            exchange_order_id=f"order_{uuid4()}",
            exchange=request.exchange,
            symbol=request.symbol,
            side=request.side,
            type=request.type,
            status=OrderStatus.OPEN,
            quantity=request.quantity,
            filled_quantity=Decimal("0"),
            remaining_quantity=request.quantity,
            price=request.price,
            average_price=None,
            cost=Decimal("0"),
            fee=Decimal("0"),
            fee_currency="USDT",
            timestamp=datetime.now(UTC),
            last_trade_timestamp=None,
        )

    service.create_order = AsyncMock(side_effect=create_order_mock)
    service.cancel_order = AsyncMock()
    service.get_order_status = AsyncMock()
    service.get_balance = AsyncMock(
        return_value={
            "USDT": BalanceDTO(
                currency="USDT",
                free=Decimal("1000.0"),
                used=Decimal("0.0"),
                total=Decimal("1000.0"),
                exchange="binance",
                timestamp=datetime.now(UTC),
            )
        }
    )
    return service


@pytest_asyncio.fixture
async def orchestrator(
    strategy_repo,
    mock_trading_service,
    mock_risk_service,
    mock_exchange_plugin,
):
    """Create a strategy orchestrator with mocked dependencies."""
    # Mock exchange registry
    exchange_registry = MagicMock()
    exchange_registry.get_plugin = MagicMock(return_value=mock_exchange_plugin)

    # Mock indicator registry (not needed for basic E2E, but required by orchestrator)
    indicator_registry = MagicMock()

    orchestrator = StrategyOrchestrator(
        strategy_repository=strategy_repo,
        trading_service=mock_trading_service,
        risk_service=mock_risk_service,
        exchange_registry=exchange_registry,
        indicator_registry=indicator_registry,
        dry_run=False,
    )

    return orchestrator


@pytest.mark.e2e
@pytest.mark.asyncio
class TestFullTradingFlow:
    """Test complete trading flows from strategy to execution."""

    async def test_buy_order_flow_e2e(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_trading_service,
        order_repo: OrderRepository,
        position_repo: PositionRepository,
        db_session,
        faker,
    ) -> None:
        """Test complete buy order flow from strategy signal to position."""
        # Set up strategy class in orchestrator
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        # Create execution context
        mock_exchange_plugin = orchestrator.exchange_registry.get_plugin("binance")
        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Step 1: Fetch market data
        await orchestrator._fetch_market_data(context)
        assert context.ohlcv_data is not None
        assert context.market_data_df is not None
        assert len(context.market_data_df) > 0

        # Step 2: Initialize strategy instance
        context.strategy_instance = context.strategy_class()
        context.strategy_instance.validate_parameters(
            context.strategy_db_model.parameters_json
        )

        # Step 3: Generate signal
        await orchestrator._generate_signal(context)
        assert context.signal is not None
        assert context.signal.action == "buy"
        assert context.signal.strength > 0

        # Step 4: Execute trade
        await orchestrator._execute_trade(context)
        assert context.order is not None
        assert context.order.side == OrderSide.BUY
        assert context.order.symbol == "BTC/USDT"

        # Verify trading service was called
        mock_trading_service.create_order.assert_called_once()
        call_args = mock_trading_service.create_order.call_args[0][0]
        assert isinstance(call_args, CreateOrderRequest)
        assert call_args.side == OrderSide.BUY
        assert call_args.symbol == "BTC/USDT"
        assert call_args.quantity == Decimal("0.001")

        # Step 4: Verify order was persisted (if trading service persisted it)
        # Note: In real scenario, TradingService would persist orders
        # For E2E, we verify the order was created via the service

        # Verify system state consistency
        assert context.order.status in [OrderStatus.OPEN, OrderStatus.CLOSED]

    async def test_dry_run_flow_e2e(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_trading_service,
        faker,
    ) -> None:
        """Test complete flow in dry-run mode (no actual orders)."""
        # Create orchestrator in dry-run mode
        orchestrator.dry_run = True

        # Set up strategy class
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        # Create execution context (dry-run)
        mock_exchange_plugin = orchestrator.exchange_registry.get_plugin("binance")
        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=True,
        )

        # Step 1-4: Execute full flow
        await orchestrator._fetch_market_data(context)
        # Initialize strategy instance
        context.strategy_instance = context.strategy_class()
        context.strategy_instance.validate_parameters(
            context.strategy_db_model.parameters_json
        )
        await orchestrator._generate_signal(context)
        await orchestrator._execute_trade(context)

        # Verify signal was generated
        assert context.signal is not None
        assert context.signal.action == "buy"

        # Verify NO order was created (dry-run)
        assert context.order is None
        mock_trading_service.create_order.assert_not_called()

    async def test_sell_signal_flow_e2e(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_trading_service,
        faker,
    ) -> None:
        """Test flow with sell signal."""

        # Create a strategy class that generates sell signals
        class SellStrategy(StrategyBase):
            name = "sell_strategy"

            def validate_parameters(self, params: dict) -> None:
                pass

            def generate_signal(
                self, market_data: pd.DataFrame, params: dict
            ) -> StrategySignal:
                return StrategySignal(
                    action="sell",
                    strength=0.7,
                    metadata={"quantity": params.get("quantity", "0.001")},
                )

            def reset_state(self) -> None:
                pass

        orchestrator._strategy_classes = {"sell_strategy": SellStrategy}

        mock_exchange_plugin = orchestrator.exchange_registry.get_plugin("binance")
        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=SellStrategy,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Execute flow
        await orchestrator._fetch_market_data(context)
        # Initialize strategy instance
        context.strategy_instance = SellStrategy()
        context.strategy_instance.validate_parameters(
            context.strategy_db_model.parameters_json
        )
        await orchestrator._generate_signal(context)
        await orchestrator._execute_trade(context)

        # Verify sell signal and order
        assert context.signal is not None
        assert context.signal.action == "sell"
        assert context.order is not None
        assert context.order.side == OrderSide.SELL

        # Verify trading service was called with sell order
        mock_trading_service.create_order.assert_called_once()
        call_args = mock_trading_service.create_order.call_args[0][0]
        assert call_args.side == OrderSide.SELL

    async def test_hold_signal_flow_e2e(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_trading_service,
        faker,
    ) -> None:
        """Test flow with hold signal (no order execution)."""

        # Create a strategy class that generates hold signals
        class HoldStrategy(StrategyBase):
            name = "hold_strategy"

            def validate_parameters(self, params: dict) -> None:
                pass

            def generate_signal(
                self, market_data: pd.DataFrame, params: dict
            ) -> StrategySignal:
                return StrategySignal(
                    action="hold",
                    strength=0.5,
                    metadata={},
                )

            def reset_state(self) -> None:
                pass

        orchestrator._strategy_classes = {"hold_strategy": HoldStrategy}

        mock_exchange_plugin = orchestrator.exchange_registry.get_plugin("binance")
        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=HoldStrategy,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Execute flow
        await orchestrator._fetch_market_data(context)
        # Initialize strategy instance
        context.strategy_instance = HoldStrategy()
        context.strategy_instance.validate_parameters(
            context.strategy_db_model.parameters_json
        )
        await orchestrator._generate_signal(context)
        assert context.signal is not None
        assert context.signal.action == "hold"

        # Execute trade (should not create order for hold)
        await orchestrator._execute_trade(context)
        assert context.order is None
        mock_trading_service.create_order.assert_not_called()

    async def test_full_strategy_execution_cycle_e2e(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_trading_service,
        faker,
    ) -> None:
        """Test complete strategy execution cycle using orchestrator's run_strategy method."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        mock_exchange_plugin = orchestrator.exchange_registry.get_plugin("binance")
        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Execute full cycle
        await orchestrator._run_strategy(context)

        # Verify all steps completed
        assert context.ohlcv_data is not None
        assert context.market_data_df is not None
        assert context.signal is not None
        # Order may or may not be created depending on signal
        assert context.error is None  # No errors

        # Verify market data was fetched
        mock_exchange_plugin.fetch_ohlcv.assert_called_once()

        # Verify trading service interaction if order was created
        if context.signal and context.signal.action != "hold":
            mock_trading_service.create_order.assert_called_once()

    async def test_data_consistency_throughout_flow_e2e(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        test_trading_pair: TradingPair,
        test_exchange: Exchange,
        faker,
    ) -> None:
        """Test that data remains consistent throughout the trading flow."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        mock_exchange_plugin = orchestrator.exchange_registry.get_plugin("binance")
        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Execute flow
        await orchestrator._fetch_market_data(context)
        initial_market_data = context.market_data_df.copy()

        await orchestrator._generate_signal(context)
        # Market data should still be available
        assert context.market_data_df is not None
        pd.testing.assert_frame_equal(context.market_data_df, initial_market_data)

        # Initialize strategy instance
        context.strategy_instance = context.strategy_class()
        context.strategy_instance.validate_parameters(
            context.strategy_db_model.parameters_json
        )
        await orchestrator._generate_signal(context)  # Generate again
        # Signal should be regenerated with same data
        assert context.signal is not None

        # Verify symbol consistency
        assert context.symbol == "BTC/USDT"
        assert test_strategy.parameters_json.get("symbol") == "BTC/USDT"
        assert context.strategy_db_model.name == test_strategy.name
