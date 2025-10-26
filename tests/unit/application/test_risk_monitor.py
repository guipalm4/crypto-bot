"""
Unit tests for Risk Monitor Service.

Tests asynchronous monitoring, callback triggering, and risk action handling.
"""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from crypto_bot.application.dtos.order import OrderSide
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


def create_test_risk_config(check_interval: float = 0.1) -> RiskConfig:
    """Create a test risk configuration with fast check interval."""
    return RiskConfig(
        stop_loss=StopLossConfig(
            enabled=True, percentage=Decimal("2.0"), cooldown_seconds=0
        ),
        take_profit=TakeProfitConfig(
            enabled=True, percentage=Decimal("5.0"), cooldown_seconds=0
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
        risk_check_interval=check_interval,
    )


def create_test_position(
    symbol: str = "BTC/USDT",
    exchange: str = "binance",
    entry_price: float = 50000.0,
    current_price: float = 48000.0,  # Default: triggering stop loss
) -> Position:
    """Create a test position."""
    return Position(
        symbol=symbol,
        exchange=exchange,
        side=OrderSide.BUY,
        entry_price=Decimal(str(entry_price)),
        current_price=Decimal(str(current_price)),
        quantity=Decimal("0.1"),
        value=Decimal(str(current_price * 0.1)),
        unrealized_pnl=Decimal(str((current_price - entry_price) * 0.1)),
    )


class TestRiskMonitorLifecycle:
    """Tests for risk monitor lifecycle (start/stop)."""

    @pytest.mark.asyncio
    async def test_start_monitoring(self) -> None:
        """Test starting risk monitoring."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        await monitor.start()

        assert monitor.is_running() is True

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_stop_monitoring(self) -> None:
        """Test stopping risk monitoring."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        await monitor.start()
        await monitor.stop()

        assert monitor.is_running() is False

    @pytest.mark.asyncio
    async def test_double_start_warning(self) -> None:
        """Test that starting twice doesn't create multiple tasks."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        await monitor.start()
        await monitor.start()  # Should log warning

        assert monitor.is_running() is True

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_stop_without_start(self) -> None:
        """Test stopping without starting doesn't error."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        await monitor.stop()  # Should log warning but not error

        assert monitor.is_running() is False


class TestRiskMonitoringLoop:
    """Tests for monitoring loop execution."""

    @pytest.mark.asyncio
    async def test_monitoring_loop_runs_periodically(self) -> None:
        """Test that monitoring loop executes periodically."""
        risk_service = RiskService(create_test_risk_config(check_interval=0.1))
        monitor = RiskMonitor(risk_service)

        callback_called = asyncio.Event()
        call_count = 0

        async def test_callback(evaluation: RiskEvaluation) -> None:
            nonlocal call_count
            call_count += 1
            callback_called.set()

        monitor.register_action_callback(RiskAction.CLOSE_POSITION, test_callback)

        # Add position that will trigger stop loss
        position = create_test_position()
        await risk_service.update_position(position)

        await monitor.start()

        # Wait for at least one callback
        await asyncio.wait_for(callback_called.wait(), timeout=1.0)

        await monitor.stop()

        assert call_count > 0

    @pytest.mark.asyncio
    async def test_monitoring_with_position_provider(self) -> None:
        """Test monitoring with external position provider."""
        risk_service = RiskService(create_test_risk_config(check_interval=0.1))

        async def position_provider() -> list[Position]:
            return [create_test_position()]

        monitor = RiskMonitor(risk_service, position_provider=position_provider)

        callback_called = asyncio.Event()

        async def test_callback(evaluation: RiskEvaluation) -> None:
            callback_called.set()

        monitor.register_action_callback(RiskAction.CLOSE_POSITION, test_callback)

        await monitor.start()
        await asyncio.wait_for(callback_called.wait(), timeout=1.0)
        await monitor.stop()

        assert callback_called.is_set()

    @pytest.mark.asyncio
    async def test_monitoring_with_price_provider(self) -> None:
        """Test monitoring with external price provider."""
        risk_service = RiskService(create_test_risk_config(check_interval=0.1))

        position = create_test_position(current_price=50000.0)  # Initially no trigger

        async def position_provider() -> list[Position]:
            return [position]

        async def price_provider(exchange: str, symbol: str) -> float:
            return 48000.0  # Updated price triggers stop loss

        monitor = RiskMonitor(
            risk_service,
            position_provider=position_provider,
            price_provider=price_provider,
        )

        callback_called = asyncio.Event()

        async def test_callback(evaluation: RiskEvaluation) -> None:
            callback_called.set()

        monitor.register_action_callback(RiskAction.CLOSE_POSITION, test_callback)

        await monitor.start()
        await asyncio.wait_for(callback_called.wait(), timeout=1.0)
        await monitor.stop()

        assert callback_called.is_set()


class TestCallbackManagement:
    """Tests for callback registration and triggering."""

    @pytest.mark.asyncio
    async def test_register_callback(self) -> None:
        """Test registering action callback."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        async def test_callback(evaluation: RiskEvaluation) -> None:
            pass

        monitor.register_action_callback(RiskAction.CLOSE_POSITION, test_callback)

        # Callback should be registered
        assert test_callback in monitor._action_callbacks[RiskAction.CLOSE_POSITION]

    @pytest.mark.asyncio
    async def test_unregister_callback(self) -> None:
        """Test unregistering action callback."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        async def test_callback(evaluation: RiskEvaluation) -> None:
            pass

        monitor.register_action_callback(RiskAction.CLOSE_POSITION, test_callback)
        monitor.unregister_action_callback(RiskAction.CLOSE_POSITION, test_callback)

        assert test_callback not in monitor._action_callbacks[RiskAction.CLOSE_POSITION]

    @pytest.mark.asyncio
    async def test_multiple_callbacks_for_same_action(self) -> None:
        """Test multiple callbacks for the same action."""
        risk_service = RiskService(create_test_risk_config(check_interval=0.1))
        monitor = RiskMonitor(risk_service)

        callback1_called = asyncio.Event()
        callback2_called = asyncio.Event()

        async def callback1(evaluation: RiskEvaluation) -> None:
            callback1_called.set()

        async def callback2(evaluation: RiskEvaluation) -> None:
            callback2_called.set()

        monitor.register_action_callback(RiskAction.CLOSE_POSITION, callback1)
        monitor.register_action_callback(RiskAction.CLOSE_POSITION, callback2)

        # Add position that triggers stop loss
        position = create_test_position()
        await risk_service.update_position(position)

        await monitor.start()
        await asyncio.wait_for(
            asyncio.gather(
                callback1_called.wait(),
                callback2_called.wait(),
            ),
            timeout=1.0,
        )
        await monitor.stop()

        assert callback1_called.is_set()
        assert callback2_called.is_set()

    @pytest.mark.asyncio
    async def test_callback_receives_evaluation(self) -> None:
        """Test that callback receives correct evaluation."""
        risk_service = RiskService(create_test_risk_config(check_interval=0.1))
        monitor = RiskMonitor(risk_service)

        received_evaluation = None

        async def test_callback(evaluation: RiskEvaluation) -> None:
            nonlocal received_evaluation
            received_evaluation = evaluation

        monitor.register_action_callback(RiskAction.CLOSE_POSITION, test_callback)

        position = create_test_position()
        await risk_service.update_position(position)

        await monitor.start()
        await asyncio.sleep(0.3)  # Wait for monitoring loop
        await monitor.stop()

        assert received_evaluation is not None
        assert received_evaluation.action == RiskAction.CLOSE_POSITION
        assert "stop_loss" in received_evaluation.triggered_rules


class TestManualChecks:
    """Tests for manual risk checks."""

    @pytest.mark.asyncio
    async def test_check_new_trade(self) -> None:
        """Test manual new trade check."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        # Add positions to approach limits
        for i in range(5):
            position = create_test_position(
                symbol=f"COIN{i}/USDT", current_price=50000.0
            )
            await risk_service.update_position(position)

        # Check new trade that would exceed limits
        evaluations = await monitor.check_new_trade("NEW/USDT", "binance", 10000.0)

        assert len(evaluations) > 0
        assert evaluations[0].action == RiskAction.BLOCK_NEW_TRADE

    @pytest.mark.asyncio
    async def test_check_new_trade_within_limits(self) -> None:
        """Test manual check for trade within limits."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        evaluations = await monitor.check_new_trade("BTC/USDT", "binance", 5000.0)

        assert len(evaluations) == 0  # No violations


class TestHistoryAndStatistics:
    """Tests for evaluation history and statistics."""

    @pytest.mark.asyncio
    async def test_evaluation_history_recorded(self) -> None:
        """Test that evaluations are recorded in history."""
        risk_service = RiskService(create_test_risk_config(check_interval=0.1))
        monitor = RiskMonitor(risk_service)

        position = create_test_position()
        await risk_service.update_position(position)

        await monitor.start()
        await asyncio.sleep(0.3)  # Wait for monitoring
        await monitor.stop()

        history = monitor.get_evaluation_history()

        assert len(history) > 0
        assert history[0]["action"] == RiskAction.CLOSE_POSITION.value

    @pytest.mark.asyncio
    async def test_get_statistics(self) -> None:
        """Test getting monitoring statistics."""
        risk_service = RiskService(create_test_risk_config(check_interval=0.1))
        monitor = RiskMonitor(risk_service)

        position = create_test_position()
        await risk_service.update_position(position)

        await monitor.start()
        await asyncio.sleep(0.3)
        await monitor.stop()

        stats = monitor.get_statistics()

        assert "total_evaluations" in stats
        assert "action_counts" in stats
        assert stats["total_evaluations"] > 0

    @pytest.mark.asyncio
    async def test_history_limit(self) -> None:
        """Test that history respects size limit."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)
        monitor._max_history_size = 10

        # Manually record many evaluations
        for i in range(20):
            eval = RiskEvaluation(action=RiskAction.CLOSE_POSITION, reason=f"Test {i}")
            monitor._record_evaluation(eval)

        history = monitor.get_evaluation_history()

        assert len(history) <= 10


class TestConfiguration:
    """Tests for configuration updates."""

    @pytest.mark.asyncio
    async def test_update_check_interval(self) -> None:
        """Test updating check interval."""
        risk_service = RiskService(create_test_risk_config(check_interval=0.1))
        monitor = RiskMonitor(risk_service)

        await monitor.update_check_interval(0.5)

        config = monitor.get_risk_service().get_config()
        assert config.risk_check_interval == 0.5

    def test_get_risk_service(self) -> None:
        """Test getting underlying risk service."""
        risk_service = RiskService(create_test_risk_config())
        monitor = RiskMonitor(risk_service)

        retrieved_service = monitor.get_risk_service()

        assert retrieved_service is risk_service
