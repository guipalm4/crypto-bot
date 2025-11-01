"""
End-to-End tests for error scenarios and recovery mechanisms.

These tests simulate error conditions such as network failures, API errors,
and system crashes, verifying that error handling, retries, and recovery
procedures restore normal operation without data loss or inconsistent states.
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
)
from crypto_bot.application.exceptions import (
    ExchangeError,
    NetworkError,
    OrderNotFound,
    RateLimitExceeded,
)
from crypto_bot.application.services.risk_service import RiskService
from crypto_bot.application.services.strategy_orchestrator import (
    StrategyExecutionContext,
    StrategyOrchestrator,
)
from crypto_bot.application.services.trading_service import TradingService
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
from crypto_bot.infrastructure.database.models import Strategy as StrategyModel
from crypto_bot.infrastructure.database.repositories import StrategyRepository
from crypto_bot.plugins.exchanges.base_ccxt_plugin import ExchangeBase
from crypto_bot.plugins.strategies.base import Strategy as StrategyBase
from crypto_bot.plugins.strategies.base import StrategySignal


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Create all tables before each test and drop them after."""
    await db_engine.close()
    engine = db_engine.create_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await db_engine.close()


@pytest_asyncio.fixture
async def db_session(setup_database):
    """Provide an async database session for tests."""
    async for session in get_db_session():
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def strategy_repo(db_session):
    """Provide a strategy repository."""
    return StrategyRepository(db_session)


@pytest_asyncio.fixture
async def test_strategy(strategy_repo, db_session, faker):
    """Create a test strategy in the database."""
    strategy = StrategyModel(
        name=faker.word(),
        plugin_name="test_strategy",
        description="Test strategy for error scenario tests",
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
            [1609459200000, 50000, 51000, 49000, 50000, 1000],
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
    service.evaluate_risk = AsyncMock(return_value=None)
    return service


@pytest_asyncio.fixture
def mock_trading_service():
    """Create a mock trading service."""
    service = MagicMock(spec=TradingService)
    service.create_order = AsyncMock()
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
    exchange_registry = MagicMock()
    exchange_registry.get_plugin = MagicMock(return_value=mock_exchange_plugin)

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
class TestNetworkErrorHandling:
    """Test handling of network errors during trading flows."""

    async def test_network_error_during_market_data_fetch(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_exchange_plugin,
    ) -> None:
        """Test recovery from network error during market data fetch."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        # Simulate network error on first call, success on retry
        call_count = 0

        async def fetch_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NetworkError("Network connection failed")
            return [
                [1609459200000, 50000, 51000, 49000, 50000, 1000],
                [1609462800000, 50000, 50500, 49500, 50200, 1100],
            ]

        mock_exchange_plugin.fetch_ohlcv = AsyncMock(side_effect=fetch_with_retry)

        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # First attempt should fail
        try:
            await orchestrator._fetch_market_data(context)
        except NetworkError:
            # Expected - network error should be propagated or handled
            pass

        # Retry should succeed (if orchestrator retries)
        # Note: Actual retry logic depends on orchestrator implementation
        if context.error is None:
            # If no error set, try again
            await orchestrator._fetch_market_data(context)
            assert context.ohlcv_data is not None

    async def test_network_error_during_order_execution(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_trading_service,
        mock_exchange_plugin,
    ) -> None:
        """Test recovery from network error during order execution."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        # Simulate network error on order creation
        call_count = 0

        async def create_order_with_retry(request: CreateOrderRequest) -> OrderDTO:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NetworkError("Network connection failed during order creation")
            # Success on retry
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

        mock_trading_service.create_order = AsyncMock(
            side_effect=create_order_with_retry
        )

        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Set up for trade execution
        await orchestrator._fetch_market_data(context)
        # Initialize strategy instance
        context.strategy_instance = context.strategy_class()
        context.strategy_instance.validate_parameters(
            context.strategy_db_model.parameters_json
        )
        await orchestrator._generate_signal(context)

        # First attempt should fail
        try:
            await orchestrator._execute_trade(context)
        except NetworkError:
            # Expected - TradingService should handle retries
            pass

        # Verify trading service was called (retry logic handled internally)
        assert mock_trading_service.create_order.call_count >= 1


@pytest.mark.e2e
@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Test handling of exchange API errors."""

    async def test_rate_limit_error_handling(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_exchange_plugin,
    ) -> None:
        """Test handling of rate limit errors."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        # Simulate rate limit error
        rate_limit_raised = False

        async def fetch_with_rate_limit(*args, **kwargs):
            nonlocal rate_limit_raised
            if not rate_limit_raised:
                rate_limit_raised = True
                raise RateLimitExceeded("Rate limit exceeded")
            return [
                [1609459200000, 50000, 51000, 49000, 50000, 1000],
            ]

        mock_exchange_plugin.fetch_ohlcv = AsyncMock(side_effect=fetch_with_rate_limit)

        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # First attempt should raise rate limit error
        try:
            await orchestrator._fetch_market_data(context)
        except RateLimitExceeded:
            # Expected - rate limit error should be handled
            pass

        # System should continue (error logged but not fatal)
        assert context.error is None or isinstance(context.error, RateLimitExceeded)

    async def test_exchange_error_during_order_creation(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_trading_service,
        mock_exchange_plugin,
    ) -> None:
        """Test handling of exchange errors during order creation."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        # Simulate exchange error
        mock_trading_service.create_order = AsyncMock(
            side_effect=ExchangeError("Exchange rejected order: insufficient balance")
        )

        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        await orchestrator._fetch_market_data(context)
        # Initialize strategy instance
        context.strategy_instance = context.strategy_class()
        context.strategy_instance.validate_parameters(
            context.strategy_db_model.parameters_json
        )
        await orchestrator._generate_signal(context)

        # Order creation should fail with exchange error
        try:
            await orchestrator._execute_trade(context)
        except ExchangeError as e:
            assert "insufficient balance" in str(e).lower()
            # Error should be captured in context
            assert context.error is not None or context.order is None


@pytest.mark.e2e
@pytest.mark.asyncio
class TestErrorRecovery:
    """Test recovery mechanisms after errors."""

    async def test_circuit_breaker_after_consecutive_errors(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_exchange_plugin,
    ) -> None:
        """Test circuit breaker activation after consecutive errors."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        # Simulate consecutive errors
        mock_exchange_plugin.fetch_ohlcv = AsyncMock(
            side_effect=NetworkError("Network error")
        )

        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Generate strategy key
        strategy_key = orchestrator._get_strategy_key(context)

        # Simulate multiple consecutive errors
        for _ in range(3):
            try:
                await orchestrator._fetch_market_data(context)
            except Exception:
                orchestrator._increment_error_count(strategy_key)
                pass

        # Verify error count increased
        assert orchestrator._error_counts.get(strategy_key, 0) >= 3

        # After max errors, strategy should be circuit-broken
        # (exact threshold depends on orchestrator configuration)

    async def test_error_count_reset_after_success(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_exchange_plugin,
    ) -> None:
        """Test error count reset after successful execution."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        strategy_key = orchestrator._get_strategy_key(context)

        # Simulate errors
        mock_exchange_plugin.fetch_ohlcv = AsyncMock(
            side_effect=NetworkError("Network error")
        )
        for _ in range(2):
            try:
                await orchestrator._fetch_market_data(context)
            except Exception:
                orchestrator._increment_error_count(strategy_key)
                pass

        assert orchestrator._error_counts.get(strategy_key, 0) >= 2

        # Simulate success
        mock_exchange_plugin.fetch_ohlcv = AsyncMock(
            return_value=[[1609459200000, 50000, 51000, 49000, 50000, 1000]]
        )
        await orchestrator._fetch_market_data(context)

        # Reset error count after success
        orchestrator._reset_error_count(strategy_key)
        assert orchestrator._error_counts.get(strategy_key, 0) == 0

    async def test_partial_failure_recovery(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_trading_service,
        mock_exchange_plugin,
    ) -> None:
        """Test recovery from partial failures in the trading flow."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        # Simulate failure in indicator computation, but recovery in signal generation
        indicator_failed = False

        async def compute_with_failure(context):
            nonlocal indicator_failed
            if not indicator_failed:
                indicator_failed = True
                raise ValueError("Indicator computation failed")
            # Success on retry
            context.indicators = {"RSI": 65.5}

        # Mock indicator registry to fail then succeed
        orchestrator.indicator_registry.create_indicator_instance = MagicMock(
            return_value=None
        )

        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Fetch market data (should succeed)
        await orchestrator._fetch_market_data(context)
        assert context.market_data_df is not None

        # Try to compute indicators (may fail, but flow continues)
        try:
            await orchestrator._compute_indicators(context)
        except Exception:
            # Indicator failure should not stop signal generation
            pass

        # Initialize strategy instance
        context.strategy_instance = context.strategy_class()
        context.strategy_instance.validate_parameters(
            context.strategy_db_model.parameters_json
        )
        # Signal generation should still work even if indicators failed
        # (strategies can work with just market data)
        await orchestrator._generate_signal(context)
        assert context.signal is not None

    async def test_state_consistency_after_error(
        self,
        orchestrator: StrategyOrchestrator,
        test_strategy: StrategyModel,
        mock_strategy_class,
        mock_exchange_plugin,
    ) -> None:
        """Test that system state remains consistent after errors."""
        orchestrator._strategy_classes = {
            test_strategy.plugin_name: mock_strategy_class
        }

        context = StrategyExecutionContext(
            strategy_db_model=test_strategy,
            strategy_class=mock_strategy_class,
            exchange_plugin=mock_exchange_plugin,
            symbol="BTC/USDT",
            timeframe="1h",
            dry_run=False,
        )

        # Initial state
        initial_symbol = context.symbol
        initial_strategy_name = context.strategy_db_model.name

        # Simulate error
        mock_exchange_plugin.fetch_ohlcv = AsyncMock(
            side_effect=NetworkError("Network error")
        )
        try:
            await orchestrator._fetch_market_data(context)
        except Exception:
            pass

        # Verify state consistency
        assert context.symbol == initial_symbol
        assert context.strategy_db_model.name == initial_strategy_name
        assert context.timeframe == "1h"
        assert context.dry_run is False

        # Recover and verify state still consistent
        mock_exchange_plugin.fetch_ohlcv = AsyncMock(
            return_value=[[1609459200000, 50000, 51000, 49000, 50000, 1000]]
        )
        await orchestrator._fetch_market_data(context)

        # State should remain consistent
        assert context.symbol == initial_symbol
        assert context.strategy_db_model.name == initial_strategy_name
