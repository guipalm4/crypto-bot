"""
Integration tests for Risk Management and Trading Engine integration.

Tests the complete flow from risk detection to action execution.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from unittest.mock import AsyncMock

import pytest

from crypto_bot.application.dtos.order import (
    OrderDTO,
    OrderSide,
    OrderStatus,
    OrderType,
)
from crypto_bot.application.interfaces.trading_engine import TradingEngineInterface
from crypto_bot.application.services.risk_action_handler import RiskActionHandler
from crypto_bot.application.services.risk_monitor import RiskMonitor
from crypto_bot.application.services.risk_service import (
    Position,
    RiskAction,
    RiskEvaluation,
    RiskService,
)
from crypto_bot.infrastructure.config.risk_config import (
    DrawdownControlConfig,
    ExposureLimitConfig,
    MaxConcurrentTradesConfig,
    RiskConfig,
    StopLossConfig,
    TakeProfitConfig,
    TrailingStopConfig,
)


# Mock Trading Engine
class MockTradingEngine(TradingEngineInterface):
    """Mock trading engine for testing."""

    def __init__(self):
        self.closed_positions = []
        self.partial_closes = []
        self.all_positions_closed = False
        self.trading_blocked = False
        self.block_duration = None
        self.trading_resumed = False
        self._equity = Decimal("10000")
        self._positions = {}

    async def close_position(
        self, symbol: str, reason: str, evaluation_id: Optional[str] = None
    ) -> OrderDTO:
        self.closed_positions.append(
            {"symbol": symbol, "reason": reason, "evaluation_id": evaluation_id}
        )
        return OrderDTO(
            id="test-order-1",
            exchange_order_id="exch-order-1",
            exchange="test-exchange",
            symbol=symbol,
            type=OrderType.MARKET,
            side=OrderSide.SELL,
            price=None,
            quantity=Decimal("0.1"),
            status=OrderStatus.CLOSED,
            filled_quantity=Decimal("0.1"),
            remaining_quantity=Decimal("0"),
            average_price=Decimal("50000"),
            cost=Decimal("5000"),
            fee=Decimal("5"),
            fee_currency="USDT",
            timestamp=datetime.now(),
            last_trade_timestamp=datetime.now(),
        )

    async def partial_close_position(
        self,
        symbol: str,
        percentage: Decimal,
        reason: str,
        evaluation_id: Optional[str] = None,
    ) -> OrderDTO:
        self.partial_closes.append(
            {
                "symbol": symbol,
                "percentage": percentage,
                "reason": reason,
                "evaluation_id": evaluation_id,
            }
        )
        return OrderDTO(
            id="test-order-2",
            exchange_order_id="exch-order-2",
            exchange="test-exchange",
            symbol=symbol,
            type=OrderType.MARKET,
            side=OrderSide.SELL,
            price=None,
            quantity=Decimal("0.05"),
            status=OrderStatus.CLOSED,
            filled_quantity=Decimal("0.05"),
            remaining_quantity=Decimal("0"),
            average_price=Decimal("50000"),
            cost=Decimal("2500"),
            fee=Decimal("2.5"),
            fee_currency="USDT",
            timestamp=datetime.now(),
            last_trade_timestamp=datetime.now(),
        )

    async def close_all_positions(
        self, reason: str, evaluation_id: Optional[str] = None
    ) -> Dict[str, OrderDTO]:
        self.all_positions_closed = True
        return {}

    async def block_new_trades(
        self,
        duration_seconds: Optional[int] = None,
        reason: str = "",
        evaluation_id: Optional[str] = None,
    ) -> None:
        self.trading_blocked = True
        self.block_duration = duration_seconds

    async def is_trading_blocked(self) -> bool:
        return self.trading_blocked

    async def resume_trading(
        self, reason: str = "", evaluation_id: Optional[str] = None
    ) -> None:
        self.trading_blocked = False
        self.trading_resumed = True

    async def get_position_size(self, symbol: str) -> Decimal:
        return self._positions.get(symbol, Decimal("0"))

    async def get_account_equity(self) -> Decimal:
        return self._equity


class TestRiskIntegration:
    """Test complete risk management to trading engine integration."""

    @pytest.fixture
    def risk_config(self) -> RiskConfig:
        """Create test risk configuration."""
        return RiskConfig(
            stop_loss=StopLossConfig(percentage=Decimal("5")),
            take_profit=TakeProfitConfig(percentage=Decimal("10")),
            exposure_limit=ExposureLimitConfig(
                max_per_asset=Decimal("10000"),
                max_per_exchange=Decimal("50000"),
                max_total=Decimal("100000"),
            ),
            trailing_stop=TrailingStopConfig(
                trailing_percentage=Decimal("3"),
                activation_percentage=Decimal("6"),
            ),
            max_concurrent_trades=MaxConcurrentTradesConfig(
                max_trades=5, max_per_exchange=3
            ),
            drawdown_control=DrawdownControlConfig(
                max_drawdown_percentage=Decimal("20"),
                emergency_exit_percentage=Decimal("30"),
            ),
        )

    @pytest.fixture
    def risk_service(self, risk_config: RiskConfig) -> RiskService:
        """Create risk service instance."""
        return RiskService(risk_config)

    @pytest.fixture
    def trading_engine(self) -> MockTradingEngine:
        """Create mock trading engine."""
        return MockTradingEngine()

    @pytest.fixture
    def action_handler(self, trading_engine: MockTradingEngine) -> RiskActionHandler:
        """Create risk action handler."""
        return RiskActionHandler(trading_engine)

    @pytest.fixture
    def test_position(self) -> Position:
        """Create test position."""
        from datetime import datetime

        from crypto_bot.application.dtos.order import OrderSide

        return Position(
            symbol="BTC/USDT",
            exchange="binance",
            side=OrderSide.BUY,
            entry_price=Decimal("50000"),
            current_price=Decimal("49000"),
            quantity=Decimal("1.0"),
            value=Decimal("49000"),
            unrealized_pnl=Decimal("-1000"),
            realized_pnl=Decimal("0"),
            entry_timestamp=datetime.now(),
            highest_price=Decimal("50000"),
        )

    @pytest.mark.asyncio
    async def test_close_position_action(
        self,
        action_handler: RiskActionHandler,
        trading_engine: MockTradingEngine,
        test_position: Position,
    ):
        """Test that close position action executes correctly."""
        evaluation = RiskEvaluation(
            action=RiskAction.CLOSE_POSITION,
            reason="Stop loss triggered",
            triggered_rules=["stop_loss"],
            position=test_position,
            metadata={},
        )

        await action_handler.handle_risk_evaluation(evaluation)

        assert len(trading_engine.closed_positions) == 1
        assert trading_engine.closed_positions[0]["symbol"] == "BTC/USDT"
        assert "Stop loss" in trading_engine.closed_positions[0]["reason"]

    @pytest.mark.asyncio
    async def test_reduce_position_action(
        self,
        action_handler: RiskActionHandler,
        trading_engine: MockTradingEngine,
        test_position: Position,
    ):
        """Test that reduce position action executes correctly."""
        evaluation = RiskEvaluation(
            action=RiskAction.REDUCE_POSITION,
            reason="Partial profit taking",
            triggered_rules=["take_profit"],
            position=test_position,
            metadata={"partial_close_percentage": Decimal("50")},
        )

        await action_handler.handle_risk_evaluation(evaluation)

        assert len(trading_engine.partial_closes) == 1
        assert trading_engine.partial_closes[0]["symbol"] == "BTC/USDT"
        assert trading_engine.partial_closes[0]["percentage"] == Decimal("50")

    @pytest.mark.asyncio
    async def test_emergency_exit_action(
        self, action_handler: RiskActionHandler, trading_engine: MockTradingEngine
    ):
        """Test that emergency exit closes all positions."""
        evaluation = RiskEvaluation(
            action=RiskAction.EMERGENCY_EXIT_ALL,
            reason="Critical drawdown exceeded",
            triggered_rules=["drawdown_critical"],
            metadata={},
        )

        await action_handler.handle_risk_evaluation(evaluation)

        assert trading_engine.all_positions_closed is True

    @pytest.mark.asyncio
    async def test_pause_trading_action(
        self, action_handler: RiskActionHandler, trading_engine: MockTradingEngine
    ):
        """Test that pause trading blocks new trades."""
        evaluation = RiskEvaluation(
            action=RiskAction.PAUSE_TRADING,
            reason="Max drawdown exceeded",
            triggered_rules=["drawdown_max"],
            metadata={"pause_duration_seconds": 3600},
        )

        await action_handler.handle_risk_evaluation(evaluation)

        assert trading_engine.trading_blocked is True
        assert trading_engine.block_duration == 3600

    @pytest.mark.asyncio
    async def test_block_new_trade_action(
        self,
        action_handler: RiskActionHandler,
        trading_engine: MockTradingEngine,
        test_position: Position,
    ):
        """Test that block new trade is logged without engine action."""
        evaluation = RiskEvaluation(
            action=RiskAction.BLOCK_NEW_TRADE,
            reason="Exposure limit exceeded",
            triggered_rules=["exposure_limit"],
            position=test_position,
            metadata={},
        )

        await action_handler.handle_risk_evaluation(evaluation)

        # Block trade doesn't trigger engine actions
        assert len(trading_engine.closed_positions) == 0
        assert not trading_engine.trading_blocked

    @pytest.mark.asyncio
    async def test_none_action(
        self,
        action_handler: RiskActionHandler,
        trading_engine: MockTradingEngine,
        test_position: Position,
    ):
        """Test that NONE action doesn't trigger anything."""
        evaluation = RiskEvaluation(
            action=RiskAction.NONE,
            reason="No action needed",
            position=test_position,
            metadata={},
        )

        await action_handler.handle_risk_evaluation(evaluation)

        # No engine actions triggered
        assert len(trading_engine.closed_positions) == 0
        assert not trading_engine.trading_blocked

    @pytest.mark.asyncio
    async def test_monitor_with_handler_integration(
        self,
        risk_service: RiskService,
        trading_engine: MockTradingEngine,
        action_handler: RiskActionHandler,
        test_position: Position,
    ):
        """Test full integration: monitor -> risk service -> handler -> engine."""
        # Update position to trigger stop loss
        test_position.current_price = Decimal("47500")  # -5% loss
        test_position.unrealized_pnl = Decimal("-2500")
        await risk_service.update_position(test_position)

        # Create monitor with mock providers
        position_provider = AsyncMock(return_value=[test_position])
        price_provider = AsyncMock(return_value=float(47500))

        monitor = RiskMonitor(
            risk_service=risk_service,
            position_provider=position_provider,
            price_provider=price_provider,
        )

        # Register handler callback
        monitor.register_action_callback(
            RiskAction.CLOSE_POSITION,
            lambda eval: action_handler.handle_risk_evaluation(eval),
        )

        # Start monitor briefly and wait for first check
        await monitor.start()
        # Give it time to run at least one check cycle
        import asyncio

        await asyncio.sleep(0.5)
        await monitor.stop()

        # Verify stop loss triggered and position was closed
        assert len(trading_engine.closed_positions) >= 1
        assert trading_engine.closed_positions[0]["symbol"] == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_unsupported_action_raises_error(
        self, action_handler: RiskActionHandler
    ):
        """Test that unsupported actions raise ValueError."""
        # Create evaluation with invalid action (using string hack)
        evaluation = RiskEvaluation(
            action="INVALID_ACTION",  # type: ignore
            reason="Test",
            metadata={},
        )

        with pytest.raises(ValueError, match="Unsupported risk action"):
            await action_handler.handle_risk_evaluation(evaluation)
