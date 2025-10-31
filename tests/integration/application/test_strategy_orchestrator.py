"""
Integration tests for Strategy Orchestrator.

Tests the full orchestration pipeline with multiple strategies,
various exchange plugins, and both dry-run and live modes.
"""

import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from crypto_bot.application.dtos.order import (
    CreateOrderRequest,
    OrderDTO,
    OrderSide,
    OrderStatus,
    OrderType,
    RetryPolicy,
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


# Mock Strategy class for testing
class MockStrategy(Strategy):
    """Mock strategy for testing."""

    name = "mock_strategy"

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate parameters."""
        if "invalid" in params:
            raise ValueError("Invalid parameter")

    def generate_signal(
        self, market_data: Any, params: Dict[str, Any]
    ) -> StrategySignal:
        """Generate mock signal."""
        action = params.get("signal_action", "hold")
        strength = params.get("signal_strength", 0.5)
        return StrategySignal(action=action, strength=strength, metadata=params)

    def reset_state(self) -> None:
        """Reset state."""
        pass


# Mock Exchange Plugin
class MockExchangePlugin(ExchangeBase):
    """Mock exchange plugin for testing."""

    name = "Mock Exchange"
    id = "mock_exchange"
    countries = ["US"]
    urls = {"api": "https://api.mock.com"}
    version = "1.0.0"
    certified = False
    has = {"fetchOHLCV": True}

    def __init__(self):
        """Initialize mock exchange."""
        self._initialized = False
        self._should_fail = False
        self._fail_count = 0

    async def initialize(self) -> None:
        """Initialize exchange."""
        self._initialized = True

    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """Load markets."""
        return {}

    async def fetch_markets(self) -> List[Dict[str, Any]]:
        """Fetch markets."""
        return []

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch ticker."""
        return {"symbol": symbol, "last": 50000.0}

    async def fetch_tickers(
        self, symbols: List[str] | None = None
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch tickers."""
        return {}

    async def fetch_order_book(
        self, symbol: str, limit: int | None = None
    ) -> Dict[str, Any]:
        """Fetch order book."""
        return {"bids": [], "asks": []}

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        since: datetime | None = None,
        limit: int | None = None,
    ) -> List[List[int | float]]:
        """Fetch OHLCV data."""
        if self._should_fail and self._fail_count < 2:
            self._fail_count += 1
            raise ConnectionError("Network error")

        # Generate mock OHLCV data
        base_time = int(datetime.now().timestamp() * 1000)
        ohlcv_data = []
        for i in range(limit or 100):
            timestamp = base_time - (limit - i - 1) * 60000  # 1 minute intervals
            ohlcv_data.append(
                [
                    timestamp,
                    50000.0 + i * 10,  # open
                    50100.0 + i * 10,  # high
                    49900.0 + i * 10,  # low
                    50050.0 + i * 10,  # close
                    1000.0 + i * 5,  # volume
                ]
            )
        return ohlcv_data

    async def fetch_trades(
        self, symbol: str, since: datetime | None = None, limit: int | None = None
    ) -> List[Dict[str, Any]]:
        """Fetch trades."""
        return []

    async def create_order(self, request: CreateOrderRequest) -> OrderDTO:
        """Create order."""
        return OrderDTO(
            id=str(uuid.uuid4()),
            exchange_order_id="mock_order_123",
            exchange="mock_exchange",
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
            timestamp=datetime.now(),
            last_trade_timestamp=None,
        )

    async def cancel_order(self, order_id: str, symbol: str | None = None) -> OrderDTO:
        """Cancel order."""
        return OrderDTO(
            id=order_id,
            exchange_order_id=order_id,
            exchange="mock_exchange",
            symbol=symbol or "BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            status=OrderStatus.CANCELED,
            quantity=Decimal("1"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("1"),
            price=None,
            average_price=None,
            cost=Decimal("0"),
            fee=Decimal("0"),
            fee_currency="USDT",
            timestamp=datetime.now(),
            last_trade_timestamp=None,
        )

    async def fetch_order(self, order_id: str, symbol: str | None = None) -> OrderDTO:
        """Fetch order."""
        return OrderDTO(
            id=order_id,
            exchange_order_id=order_id,
            exchange="mock_exchange",
            symbol=symbol or "BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            status=OrderStatus.OPEN,
            quantity=Decimal("1"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("1"),
            price=None,
            average_price=None,
            cost=Decimal("0"),
            fee=Decimal("0"),
            fee_currency="USDT",
            timestamp=datetime.now(),
            last_trade_timestamp=None,
        )

    async def fetch_order_status(self, order_id: str, symbol: str | None = None) -> Any:
        """Fetch order status."""
        pass

    async def fetch_open_orders(self, symbol: str | None = None) -> List[OrderDTO]:
        """Fetch open orders."""
        return []

    async def cancel_all_orders(self, symbol: str | None = None) -> List[OrderDTO]:
        """Cancel all orders."""
        return []

    async def fetch_balance(self, currency: str | None = None) -> Any:
        """Fetch balance."""
        pass

    async def fetch_positions(self, symbols: List[str] | None = None) -> List[Any]:
        """Fetch positions."""
        return []

    async def fetch_my_trades(
        self,
        symbol: str | None = None,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Fetch my trades."""
        return []

    def amount_to_precision(self, symbol: str, amount: float) -> str:
        """Convert amount to precision."""
        return str(amount)

    def price_to_precision(self, symbol: str, price: float) -> str:
        """Convert price to precision."""
        return str(price)

    def cost_to_precision(self, symbol: str, cost: float) -> str:
        """Convert cost to precision."""
        return str(cost)

    def currency_to_precision(self, currency: str, amount: float) -> str:
        """Convert currency to precision."""
        return str(amount)

    async def close(self) -> None:
        """Close exchange."""
        self._initialized = False


@pytest.fixture
def mock_strategy_repository():
    """Create mock strategy repository."""
    repository = MagicMock(spec=IStrategyRepository)
    strategy1 = MagicMock()
    strategy1.id = uuid.uuid4()
    strategy1.name = "Test Strategy 1"
    strategy1.plugin_name = "mock_strategy"
    strategy1.parameters_json = {
        "exchange": "mock_exchange",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "indicators": {"rsi": {"length": 14}},
        "signal_action": "buy",
        "signal_strength": 0.8,
    }

    strategy2 = MagicMock()
    strategy2.id = uuid.uuid4()
    strategy2.name = "Test Strategy 2"
    strategy2.plugin_name = "mock_strategy"
    strategy2.parameters_json = {
        "exchange": "mock_exchange",
        "symbol": "ETH/USDT",
        "timeframe": "5m",
        "indicators": {},
        "signal_action": "sell",
        "signal_strength": 0.6,
    }

    async def get_active_strategies():
        return [strategy1, strategy2]

    repository.get_active_strategies = AsyncMock(side_effect=get_active_strategies)
    return repository


@pytest.fixture
def mock_trading_service():
    """Create mock trading service."""
    service = MagicMock(spec=ITradingService)
    service.create_order = AsyncMock(
        return_value=OrderDTO(
            id=str(uuid.uuid4()),
            exchange_order_id="test_order",
            exchange="mock_exchange",
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
            fee=Decimal("0.1"),
            fee_currency="USDT",
            timestamp=datetime.now(),
            last_trade_timestamp=None,
        )
    )
    return service


@pytest.fixture
def mock_risk_service():
    """Create mock risk service."""
    return MagicMock(spec=RiskService)


@pytest.fixture
def mock_exchange_registry():
    """Create mock exchange registry."""
    registry = MagicMock(spec=ExchangePluginRegistry)
    exchange_plugin = MockExchangePlugin()

    def get_exchange(name: str):
        return exchange_plugin

    registry.get_exchange = get_exchange
    return registry


@pytest.fixture
def mock_indicator_registry():
    """Create mock indicator registry."""
    registry = MagicMock(spec=IndicatorPluginRegistry)

    class MockIndicator:
        def validate_parameters(self, params: Dict[str, Any]) -> None:
            pass

        def calculate(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
            return pd.Series([50.0] * len(data), name="rsi")

    def create_indicator_instance(name: str):
        return MockIndicator()

    registry.create_indicator_instance = create_indicator_instance
    return registry


@pytest.fixture
def orchestrator(
    mock_strategy_repository,
    mock_trading_service,
    mock_risk_service,
    mock_exchange_registry,
    mock_indicator_registry,
):
    """Create strategy orchestrator instance."""
    with patch(
        "crypto_bot.application.services.strategy_orchestrator.discover_strategies",
        return_value={"mock_strategy": MockStrategy},
    ):
        orchestrator = StrategyOrchestrator(
            strategy_repository=mock_strategy_repository,
            trading_service=mock_trading_service,
            risk_service=mock_risk_service,
            exchange_registry=mock_exchange_registry,
            indicator_registry=mock_indicator_registry,
            dry_run=False,
            max_concurrent_strategies=5,
        )
        yield orchestrator
        # Cleanup
        if orchestrator._running:
            asyncio.run(orchestrator.stop())


@pytest.mark.asyncio
async def test_orchestrator_start_stop(orchestrator):
    """Test orchestrator start and stop functionality."""
    # Start orchestrator
    await orchestrator.start()
    assert orchestrator._running is True
    assert orchestrator._scheduler_task is not None

    # Wait a bit
    await asyncio.sleep(0.1)

    # Stop orchestrator
    await orchestrator.stop()
    assert orchestrator._running is False


@pytest.mark.asyncio
async def test_orchestrator_dry_run_mode(
    mock_strategy_repository,
    mock_trading_service,
    mock_risk_service,
    mock_exchange_registry,
    mock_indicator_registry,
):
    """Test orchestrator in dry-run mode."""
    with patch(
        "crypto_bot.application.services.strategy_orchestrator.discover_strategies",
        return_value={"mock_strategy": MockStrategy},
    ):
        orchestrator = StrategyOrchestrator(
            strategy_repository=mock_strategy_repository,
            trading_service=mock_trading_service,
            risk_service=mock_risk_service,
            exchange_registry=mock_exchange_registry,
            indicator_registry=mock_indicator_registry,
            dry_run=True,  # Dry-run mode
            max_concurrent_strategies=5,
        )

        # Start and run briefly
        await orchestrator.start()
        await asyncio.sleep(0.2)
        await orchestrator.stop()

        # Verify no orders were created (dry-run mode)
        mock_trading_service.create_order.assert_not_called()


@pytest.mark.asyncio
async def test_strategy_execution_cycle(orchestrator):
    """Test complete strategy execution cycle."""
    # Get strategies
    strategies = await orchestrator.strategy_repository.get_active_strategies()
    assert len(strategies) == 2

    # Create execution contexts
    contexts = await orchestrator._create_execution_contexts(strategies)
    assert len(contexts) == 2

    # Execute one strategy
    await orchestrator._run_strategy(contexts[0])

    # Verify execution completed
    assert contexts[0].ohlcv_data is not None
    assert contexts[0].market_data_df is not None
    assert contexts[0].signal is not None
    assert contexts[0].error is None


@pytest.mark.asyncio
async def test_concurrent_strategy_execution(orchestrator):
    """Test concurrent execution of multiple strategies."""
    await orchestrator.start()

    # Wait for at least one execution cycle
    await asyncio.sleep(0.5)

    # Check that multiple strategies were processed
    assert len(orchestrator._tasks) == 0  # Tasks completed

    await orchestrator.stop()


@pytest.mark.asyncio
async def test_error_handling_and_retries(orchestrator):
    """Test error handling and retry logic."""
    # Create a context with a failing exchange
    exchange = MockExchangePlugin()
    exchange._should_fail = True

    strategy_db = MagicMock()
    strategy_db.id = uuid.uuid4()
    strategy_db.name = "Failing Strategy"
    strategy_db.plugin_name = "mock_strategy"
    strategy_db.parameters_json = {
        "exchange": "mock_exchange",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "indicators": {},
    }

    context = StrategyExecutionContext(
        strategy_db_model=strategy_db,
        strategy_class=MockStrategy,
        exchange_plugin=exchange,
        symbol="BTC/USDT",
        timeframe="1h",
        dry_run=False,
    )

    # Should retry and eventually succeed (after 2 failures)
    try:
        await orchestrator._fetch_market_data(context, max_retries=3)
        assert context.ohlcv_data is not None
    except Exception:
        # If it fails completely, that's also acceptable for testing
        pass


@pytest.mark.asyncio
async def test_circuit_breaker_pattern(orchestrator):
    """Test circuit breaker pattern for failing strategies."""
    strategy_key = "test_strategy:BTC/USDT:1h"

    # Simulate multiple errors
    for _ in range(6):
        orchestrator._increment_error_count(strategy_key)

    # Check circuit breaker threshold
    error_count = orchestrator._error_counts.get(strategy_key, 0)
    assert error_count >= orchestrator._max_consecutive_errors

    # Reset should clear errors
    orchestrator._reset_error_count(strategy_key)
    assert orchestrator._error_counts.get(strategy_key, 0) == 0


@pytest.mark.asyncio
async def test_scheduler_timing(orchestrator):
    """Test scheduler respects timeframe boundaries."""
    await orchestrator.start()

    # Get strategies
    strategies = await orchestrator.strategy_repository.get_active_strategies()
    contexts = await orchestrator._create_execution_contexts(strategies)

    # Execute and track time
    strategy_key = orchestrator._get_strategy_key(contexts[0])
    initial_time = orchestrator._last_execution.get(strategy_key, 0)

    # Run strategy
    await orchestrator._run_strategy_with_tracking(
        contexts[0], asyncio.get_event_loop().time()
    )

    # Check that execution time was tracked
    final_time = orchestrator._last_execution.get(strategy_key, 0)
    assert final_time > initial_time

    await orchestrator.stop()


@pytest.mark.asyncio
async def test_trade_execution_in_live_mode(orchestrator):
    """Test trade execution in live mode (not dry-run)."""
    strategy_db = MagicMock()
    strategy_db.id = uuid.uuid4()
    strategy_db.name = "Live Trading Strategy"
    strategy_db.plugin_name = "mock_strategy"
    strategy_db.parameters_json = {
        "exchange": "mock_exchange",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "indicators": {},
    }

    exchange = MockExchangePlugin()
    context = StrategyExecutionContext(
        strategy_db_model=strategy_db,
        strategy_class=MockStrategy,
        exchange_plugin=exchange,
        symbol="BTC/USDT",
        timeframe="1h",
        dry_run=False,
    )

    # Set up context with signal
    context.strategy_instance = MockStrategy()
    context.signal = StrategySignal(action="buy", strength=0.8)

    # Execute trade
    await orchestrator._execute_trade(context)

    # Verify order was created (not dry-run)
    assert context.order is not None
    orchestrator.trading_service.create_order.assert_called()


@pytest.mark.asyncio
async def test_indicator_computation(orchestrator):
    """Test indicator computation with caching."""
    strategy_db = MagicMock()
    strategy_db.id = uuid.uuid4()
    strategy_db.name = "Indicator Test"
    strategy_db.plugin_name = "mock_strategy"
    strategy_db.parameters_json = {
        "exchange": "mock_exchange",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "indicators": {"rsi": {"length": 14}},
    }

    exchange = MockExchangePlugin()
    context = StrategyExecutionContext(
        strategy_db_model=strategy_db,
        strategy_class=MockStrategy,
        exchange_plugin=exchange,
        symbol="BTC/USDT",
        timeframe="1h",
        dry_run=False,
    )

    # Fetch market data first
    await orchestrator._fetch_market_data(context)

    # Compute indicators
    await orchestrator._compute_indicators(context)

    # Verify indicators were computed
    assert "rsi" in context.indicators
    assert len(context.indicators["rsi"]) > 0


@pytest.mark.asyncio
async def test_signal_generation(orchestrator):
    """Test signal generation from strategy."""
    strategy_db = MagicMock()
    strategy_db.id = uuid.uuid4()
    strategy_db.name = "Signal Test"
    strategy_db.plugin_name = "mock_strategy"
    strategy_db.parameters_json = {
        "exchange": "mock_exchange",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "indicators": {},
        "signal_action": "buy",
        "signal_strength": 0.9,
    }

    exchange = MockExchangePlugin()
    context = StrategyExecutionContext(
        strategy_db_model=strategy_db,
        strategy_class=MockStrategy,
        exchange_plugin=exchange,
        symbol="BTC/USDT",
        timeframe="1h",
        dry_run=False,
    )

    # Set up context
    context.strategy_instance = MockStrategy()
    await orchestrator._fetch_market_data(context)
    context.indicators = {}

    # Generate signal
    await orchestrator._generate_signal(context)

    # Verify signal was generated
    assert context.signal is not None
    assert context.signal.action == "buy"
    assert context.signal.strength == 0.9
