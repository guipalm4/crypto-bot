"""
Unit tests for StrategyOrchestrator.

Tests strategy orchestration logic with fully mocked dependencies.
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pandas as pd
import pytest
import pytest_asyncio
from freezegun import freeze_time

from crypto_bot.application.dtos.order import (
    CreateOrderRequest,
    OrderDTO,
    OrderSide,
    OrderStatus,
    OrderType,
)
from crypto_bot.application.interfaces.trading_service import ITradingService
from crypto_bot.application.services.risk_service import RiskService
from crypto_bot.application.services.strategy_orchestrator import (
    StrategyExecutionContext,
    StrategyOrchestrator,
)
from crypto_bot.domain.repositories.strategy_repository import IStrategyRepository
from crypto_bot.infrastructure.exchanges.base import ExchangeBase
from crypto_bot.plugins.indicators.loader import IndicatorPluginRegistry
from crypto_bot.plugins.registry import ExchangePluginRegistry
from crypto_bot.plugins.strategies.base import Strategy, StrategySignal


# Mock Strategy class
class MockStrategy(Strategy):
    """Mock strategy for testing."""

    name = "mock_strategy"

    def validate_parameters(self, params: dict) -> None:
        """Validate parameters."""
        pass

    def generate_signal(
        self, market_data: pd.DataFrame, params: dict
    ) -> StrategySignal:
        """Generate mock signal."""
        action = params.get("signal_action", "hold")
        strength = params.get("signal_strength", 0.5)
        return StrategySignal(action=action, strength=strength, metadata=params)

    def reset_state(self) -> None:
        """Reset state."""
        pass


def create_mock_exchange_plugin() -> MagicMock:
    """Create a mock exchange plugin."""
    plugin = MagicMock(spec=ExchangeBase)
    plugin.name = "Mock Exchange"
    plugin.id = "mock_exchange"
    plugin.initialize = AsyncMock()
    plugin.fetch_ohlcv = AsyncMock()
    plugin.load_markets = AsyncMock(return_value={})
    return plugin


@pytest.fixture
def mock_strategy_repo() -> MagicMock:
    """Create a mock strategy repository."""
    repo = MagicMock(spec=IStrategyRepository)
    repo.get_active_strategies = AsyncMock()
    return repo


@pytest.fixture
def mock_trading_service() -> MagicMock:
    """Create a mock trading service."""
    service = MagicMock(spec=ITradingService)
    service.create_order = AsyncMock()
    return service


@pytest.fixture
def mock_risk_service() -> MagicMock:
    """Create a mock risk service."""
    from crypto_bot.infrastructure.config.risk_config import (
        DrawdownControlConfig,
        ExposureLimitConfig,
        MaxConcurrentTradesConfig,
        RiskConfig,
        StopLossConfig,
        TakeProfitConfig,
        TrailingStopConfig,
    )

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
    return service


@pytest.fixture
def mock_exchange_registry() -> MagicMock:
    """Create a mock exchange registry."""
    registry = MagicMock(spec=ExchangePluginRegistry)
    return registry


@pytest.fixture
def mock_indicator_registry() -> MagicMock:
    """Create a mock indicator registry."""
    registry = MagicMock(spec=IndicatorPluginRegistry)
    return registry


@pytest.fixture
def orchestrator(
    mock_strategy_repo: MagicMock,
    mock_trading_service: MagicMock,
    mock_risk_service: MagicMock,
    mock_exchange_registry: MagicMock,
    mock_indicator_registry: MagicMock,
) -> StrategyOrchestrator:
    """Create StrategyOrchestrator with mocked dependencies."""
    return StrategyOrchestrator(
        strategy_repository=mock_strategy_repo,
        trading_service=mock_trading_service,
        risk_service=mock_risk_service,
        exchange_registry=mock_exchange_registry,
        indicator_registry=mock_indicator_registry,
        dry_run=True,
        max_concurrent_strategies=5,
    )


@pytest.fixture
def mock_strategy_db_model() -> MagicMock:
    """Create a mock strategy database model."""
    model = MagicMock()
    model.id = uuid4()
    model.name = "Test Strategy"
    model.plugin_name = "mock_strategy"
    model.parameters_json = {
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "signal_action": "buy",
        "signal_strength": 0.8,
    }
    model.is_active = True
    return model


@pytest.fixture
def execution_context(
    mock_strategy_db_model: MagicMock,
) -> StrategyExecutionContext:
    """Create a strategy execution context."""
    exchange_plugin = create_mock_exchange_plugin()
    return StrategyExecutionContext(
        strategy_db_model=mock_strategy_db_model,
        strategy_class=MockStrategy,
        exchange_plugin=exchange_plugin,
        symbol="BTC/USDT",
        timeframe="1h",
        dry_run=True,
    )


@pytest.mark.asyncio
class TestStrategyOrchestrator:
    """Test suite for StrategyOrchestrator."""

    async def test_initialization(self, orchestrator: StrategyOrchestrator) -> None:
        """Test orchestrator initialization."""
        assert orchestrator.dry_run is True
        assert orchestrator.max_concurrent_strategies == 5
        assert orchestrator._running is False
        assert orchestrator._semaphore._value == 5

    async def test_start_success(self, orchestrator: StrategyOrchestrator) -> None:
        """Test starting the orchestrator."""
        with patch.object(orchestrator, "_scheduler_loop", new_callable=AsyncMock):
            await orchestrator.start()
            assert orchestrator._running is True
            assert orchestrator._scheduler_task is not None

            await orchestrator.stop()

    async def test_start_already_running(
        self, orchestrator: StrategyOrchestrator
    ) -> None:
        """Test starting orchestrator when already running."""
        with patch.object(orchestrator, "_scheduler_loop", new_callable=AsyncMock):
            await orchestrator.start()
            assert orchestrator._running is True

            with pytest.raises(RuntimeError, match="already running"):
                await orchestrator.start()

            await orchestrator.stop()

    async def test_stop_not_running(self, orchestrator: StrategyOrchestrator) -> None:
        """Test stopping orchestrator when not running."""
        assert orchestrator._running is False
        await orchestrator.stop()  # Should not raise error
        assert orchestrator._running is False

    async def test_stop_with_running_tasks(
        self, orchestrator: StrategyOrchestrator
    ) -> None:
        """Test stopping orchestrator with running tasks."""

        # Create real tasks that can be awaited
        async def dummy_task() -> None:
            await asyncio.sleep(0.1)

        task1 = asyncio.create_task(dummy_task())
        task2 = asyncio.create_task(dummy_task())
        orchestrator._tasks.add(task1)
        orchestrator._tasks.add(task2)

        with patch.object(orchestrator, "_scheduler_loop", new_callable=AsyncMock):
            orchestrator._running = True
            orchestrator._scheduler_task = asyncio.create_task(asyncio.sleep(0.01))

            await asyncio.sleep(0.05)  # Let tasks start
            await orchestrator.stop()

            assert orchestrator._running is False
            assert len(orchestrator._tasks) == 0

    async def test_fetch_market_data_success(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test successful market data fetching."""
        # Mock OHLCV data: [timestamp_ms, open, high, low, close, volume]
        timestamp_ms = 1609459200000  # 2021-01-01 00:00:00
        ohlcv_data = [
            [timestamp_ms - 3600000, 48000.0, 49000.0, 47000.0, 48500.0, 100.0],
            [timestamp_ms, 48500.0, 51000.0, 48000.0, 50500.0, 150.0],
        ]

        execution_context.exchange_plugin.fetch_ohlcv = AsyncMock(
            return_value=ohlcv_data
        )

        await orchestrator._fetch_market_data(execution_context)

        assert execution_context.ohlcv_data == ohlcv_data
        assert execution_context.market_data_df is not None
        assert len(execution_context.market_data_df) == 2

    async def test_fetch_market_data_retry_on_failure(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test market data fetching with retry on failure."""
        # First call fails, second succeeds
        execution_context.exchange_plugin.fetch_ohlcv = AsyncMock(
            side_effect=[
                Exception("Network error"),
                [[1609459200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0]],
            ]
        )

        await orchestrator._fetch_market_data(execution_context, max_retries=3)

        assert execution_context.ohlcv_data is not None
        assert execution_context.exchange_plugin.fetch_ohlcv.call_count == 2

    async def test_compute_indicators_success(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test successful indicator computation."""
        # Setup market data
        execution_context.market_data_df = pd.DataFrame(
            {
                "open": [48000.0, 48500.0],
                "high": [49000.0, 51000.0],
                "low": [47000.0, 48000.0],
                "close": [48500.0, 50500.0],
                "volume": [100.0, 150.0],
            }
        )

        # Add indicators config to strategy parameters
        execution_context.strategy_db_model.parameters_json["indicators"] = {
            "RSI": {"length": 14}
        }

        # Mock indicator instance
        mock_indicator = MagicMock()
        mock_indicator.validate_parameters = MagicMock()
        mock_indicator_result = pd.Series([0.5, 0.7], name="RSI")
        mock_indicator.calculate = MagicMock(return_value=mock_indicator_result)

        orchestrator.indicator_registry.create_indicator_instance = MagicMock(
            return_value=mock_indicator
        )

        # Mock cache
        with patch(
            "crypto_bot.application.services.strategy_orchestrator.get_cache"
        ) as mock_cache:
            cache_mock = MagicMock()
            cache_mock.get = MagicMock(return_value=None)  # Cache miss
            cache_mock.set = MagicMock()
            mock_cache.return_value = cache_mock

            await orchestrator._compute_indicators(execution_context)

        assert "RSI" in execution_context.indicators
        assert len(execution_context.indicators) > 0

    async def test_generate_signal_success(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test successful signal generation."""
        # Setup required context data
        execution_context.market_data_df = pd.DataFrame(
            {
                "close": [48000.0, 48500.0, 50500.0],
            }
        )
        execution_context.indicators = {"RSI": pd.Series([30.0, 35.0, 40.0])}

        # Initialize strategy instance
        execution_context.strategy_instance = MockStrategy()

        await orchestrator._generate_signal(execution_context)

        assert execution_context.signal is not None
        assert execution_context.signal.action in ("buy", "sell", "hold")

    async def test_generate_signal_hold_when_no_data(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test signal generation raises error when no market data."""
        execution_context.market_data_df = None
        execution_context.strategy_instance = MockStrategy()

        with pytest.raises(ValueError, match="Market data must be available"):
            await orchestrator._generate_signal(execution_context)

    async def test_execute_trade_dry_run(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test trade execution in dry-run mode."""
        execution_context.dry_run = True
        execution_context.signal = StrategySignal(
            action="buy", strength=0.8, metadata={"quantity": "0.001"}
        )

        await orchestrator._execute_trade(execution_context)

        # In dry-run, should not call trading service
        orchestrator.trading_service.create_order.assert_not_called()
        assert execution_context.order is None

    async def test_execute_trade_live_mode(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test trade execution in live mode."""
        orchestrator.dry_run = False
        execution_context.dry_run = False
        execution_context.signal = StrategySignal(
            action="buy", strength=0.8, metadata={"quantity": "0.001"}
        )

        # Ensure exchange is in parameters
        execution_context.strategy_db_model.parameters_json["exchange"] = "binance"

        # Mock order creation

        mock_order = OrderDTO(
            id=str(uuid4()),
            exchange_order_id="order_123",
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            status=OrderStatus.OPEN,
            quantity=Decimal("0.001"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("0.001"),
            price=None,
            average_price=None,
            cost=Decimal("50"),
            fee=Decimal("0.05"),
            fee_currency="USDT",
            timestamp=datetime.now(UTC),
            last_trade_timestamp=None,
        )
        orchestrator.trading_service.create_order = AsyncMock(return_value=mock_order)

        await orchestrator._execute_trade(execution_context)

        orchestrator.trading_service.create_order.assert_called_once()
        assert execution_context.order is not None
        assert execution_context.order.exchange_order_id == "order_123"

    async def test_execute_trade_no_signal(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test trade execution when no signal."""
        execution_context.signal = None

        await orchestrator._execute_trade(execution_context)

        orchestrator.trading_service.create_order.assert_not_called()

    async def test_execute_trade_hold_signal(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test trade execution with hold signal."""
        execution_context.signal = StrategySignal(action="hold", strength=0.5)

        await orchestrator._execute_trade(execution_context)

        orchestrator.trading_service.create_order.assert_not_called()

    async def test_run_strategy_full_cycle(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test full strategy execution cycle."""
        # Setup mocks
        ohlcv_data = [[1609459200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0]]
        execution_context.exchange_plugin.fetch_ohlcv = AsyncMock(
            return_value=ohlcv_data
        )

        orchestrator.indicator_registry.compute = MagicMock(
            return_value=pd.Series([0.7])
        )

        await orchestrator._run_strategy(execution_context)

        # Verify all steps were executed
        execution_context.exchange_plugin.fetch_ohlcv.assert_called_once()
        assert execution_context.market_data_df is not None

    async def test_run_strategy_with_error(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test strategy execution with error."""
        # Cause an error in fetching market data
        execution_context.exchange_plugin.fetch_ohlcv = AsyncMock(
            side_effect=Exception("Network error")
        )

        await orchestrator._run_strategy(execution_context)

        assert execution_context.error is not None
        assert "Network error" in str(execution_context.error)

    async def test_create_execution_contexts_success(
        self,
        orchestrator: StrategyOrchestrator,
        mock_strategy_db_model: MagicMock,
    ) -> None:
        """Test successful execution context creation."""
        # Setup mocks
        orchestrator._strategy_classes = {"mock_strategy": MockStrategy}

        mock_exchange = create_mock_exchange_plugin()
        orchestrator.exchange_registry.get_exchange = MagicMock(
            return_value=mock_exchange
        )

        contexts = await orchestrator._create_execution_contexts(
            [mock_strategy_db_model]
        )

        assert len(contexts) == 1
        assert contexts[0].strategy_db_model == mock_strategy_db_model
        assert contexts[0].symbol == "BTC/USDT"
        assert contexts[0].timeframe == "1h"

    async def test_create_execution_contexts_missing_strategy_class(
        self,
        orchestrator: StrategyOrchestrator,
        mock_strategy_db_model: MagicMock,
    ) -> None:
        """Test context creation when strategy class not found."""
        orchestrator._strategy_classes = {}  # No strategies available

        contexts = await orchestrator._create_execution_contexts(
            [mock_strategy_db_model]
        )

        assert len(contexts) == 0

    async def test_create_execution_contexts_missing_config(
        self,
        orchestrator: StrategyOrchestrator,
        mock_strategy_db_model: MagicMock,
    ) -> None:
        """Test context creation with missing configuration."""
        orchestrator._strategy_classes = {"mock_strategy": MockStrategy}

        # Remove required config
        mock_strategy_db_model.parameters_json = {}

        contexts = await orchestrator._create_execution_contexts(
            [mock_strategy_db_model]
        )

        assert len(contexts) == 0

    async def test_circuit_breaker_on_consecutive_errors(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test circuit breaker activation after consecutive errors."""
        orchestrator._max_consecutive_errors = 3

        # Cause errors multiple times
        execution_context.exchange_plugin.fetch_ohlcv = AsyncMock(
            side_effect=Exception("Error")
        )

        strategy_key = orchestrator._get_strategy_key(execution_context)

        # Run strategy multiple times to trigger circuit breaker
        for _ in range(3):
            await orchestrator._run_strategy(execution_context)
            orchestrator._increment_error_count(strategy_key)

        # Check error count
        assert orchestrator._error_counts[strategy_key] >= 3

    async def test_reset_error_count_on_success(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test error count reset after successful execution."""
        strategy_key = orchestrator._get_strategy_key(execution_context)

        # Set error count
        orchestrator._error_counts[strategy_key] = 2

        # Successful execution
        ohlcv_data = [[1609459200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0]]
        execution_context.exchange_plugin.fetch_ohlcv = AsyncMock(
            return_value=ohlcv_data
        )
        orchestrator.indicator_registry.compute = MagicMock(
            return_value=pd.Series([0.7])
        )

        await orchestrator._run_strategy_with_tracking(execution_context, 1000.0)

        # Error count should be reset
        assert orchestrator._error_counts.get(strategy_key, 0) == 0

    async def test_get_strategy_key(
        self,
        orchestrator: StrategyOrchestrator,
        execution_context: StrategyExecutionContext,
    ) -> None:
        """Test strategy key generation."""
        key = orchestrator._get_strategy_key(execution_context)

        assert key == f"{execution_context.strategy_db_model.id}:BTC/USDT:1h"
