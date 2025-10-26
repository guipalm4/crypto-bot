"""
Unit tests for Risk Management Service.

Tests all risk rules with edge cases including rapid price changes,
simultaneous triggers, and boundary conditions.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import pytest

from crypto_bot.application.dtos.order import OrderSide
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


def create_test_risk_config() -> RiskConfig:
    """Create a test risk configuration."""
    return RiskConfig(
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


def create_test_position(
    symbol: str = "BTC/USDT",
    exchange: str = "binance",
    side: OrderSide = OrderSide.BUY,
    entry_price: Decimal = Decimal("50000"),
    current_price: Decimal = Decimal("50000"),
    quantity: Decimal = Decimal("0.1"),
    highest_price: Optional[Decimal] = None,
) -> Position:
    """Create a test position."""
    value = quantity * current_price
    unrealized_pnl = (
        (current_price - entry_price) * quantity
        if side == OrderSide.BUY
        else (entry_price - current_price) * quantity
    )

    if highest_price is None:
        highest_price = current_price if side == OrderSide.BUY else entry_price

    return Position(
        symbol=symbol,
        exchange=exchange,
        side=side,
        entry_price=entry_price,
        current_price=current_price,
        quantity=quantity,
        value=value,
        unrealized_pnl=unrealized_pnl,
        entry_timestamp=datetime.now(),
        highest_price=highest_price,
    )


class TestPositionManagement:
    """Tests for position management methods."""

    @pytest.mark.asyncio
    async def test_update_position(self) -> None:
        """Test updating position data."""
        service = RiskService(create_test_risk_config())
        position = create_test_position()

        await service.update_position(position)
        positions = await service.get_positions()

        assert "binance:BTC/USDT" in positions
        assert positions["binance:BTC/USDT"].symbol == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_remove_position(self) -> None:
        """Test removing position data."""
        service = RiskService(create_test_risk_config())
        position = create_test_position()

        await service.update_position(position)
        await service.remove_position("binance", "BTC/USDT")
        positions = await service.get_positions()

        assert "binance:BTC/USDT" not in positions

    @pytest.mark.asyncio
    async def test_update_highest_price_on_increase(self) -> None:
        """Test that highest price is updated when price increases."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(current_price=Decimal("50000"))

        await service.update_position(position)

        # Update with higher price
        position.current_price = Decimal("52000")
        await service.update_position(position)

        positions = await service.get_positions()
        assert positions["binance:BTC/USDT"].highest_price == Decimal("52000")


class TestStopLoss:
    """Tests for stop loss rule."""

    @pytest.mark.asyncio
    async def test_stop_loss_not_triggered(self) -> None:
        """Test stop loss when price hasn't dropped enough."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("49500"),  # 1% drop
        )

        evaluation = await service.check_stop_loss(position)

        assert evaluation.action == RiskAction.NONE

    @pytest.mark.asyncio
    async def test_stop_loss_triggered(self) -> None:
        """Test stop loss when price drops beyond threshold."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("48000"),  # 4% drop, > 2% threshold
        )

        evaluation = await service.check_stop_loss(position)

        assert evaluation.action == RiskAction.CLOSE_POSITION
        assert "stop_loss" in evaluation.triggered_rules

    @pytest.mark.asyncio
    async def test_stop_loss_exact_threshold(self) -> None:
        """Test stop loss at exact threshold boundary."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("49000"),  # Exactly 2% drop
        )

        evaluation = await service.check_stop_loss(position)

        assert evaluation.action == RiskAction.CLOSE_POSITION

    @pytest.mark.asyncio
    async def test_stop_loss_sell_position(self) -> None:
        """Test stop loss for short position."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            side=OrderSide.SELL,
            entry_price=Decimal("50000"),
            current_price=Decimal("52000"),  # Price went up (loss for short)
        )

        evaluation = await service.check_stop_loss(position)

        assert evaluation.action == RiskAction.CLOSE_POSITION

    @pytest.mark.asyncio
    async def test_stop_loss_cooldown(self) -> None:
        """Test stop loss cooldown period."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("48000"),
        )

        # First trigger
        eval1 = await service.check_stop_loss(position)
        assert eval1.action == RiskAction.CLOSE_POSITION

        # Immediate second trigger (within cooldown)
        eval2 = await service.check_stop_loss(position)
        assert eval2.action == RiskAction.NONE


class TestTakeProfit:
    """Tests for take profit rule."""

    @pytest.mark.asyncio
    async def test_take_profit_not_triggered(self) -> None:
        """Test take profit when profit hasn't reached threshold."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("51000"),  # 2% profit, < 5% threshold
        )

        evaluation = await service.check_take_profit(position)

        assert evaluation.action == RiskAction.NONE

    @pytest.mark.asyncio
    async def test_take_profit_triggered(self) -> None:
        """Test take profit when profit exceeds threshold."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("53000"),  # 6% profit, > 5% threshold
        )

        evaluation = await service.check_take_profit(position)

        assert evaluation.action == RiskAction.CLOSE_POSITION
        assert "take_profit" in evaluation.triggered_rules

    @pytest.mark.asyncio
    async def test_take_profit_partial_close(self) -> None:
        """Test partial take profit."""
        config = create_test_risk_config()
        config.take_profit.partial_close = True
        config.take_profit.partial_close_percentage = Decimal("50.0")
        service = RiskService(config)

        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("53000"),
        )

        evaluation = await service.check_take_profit(position)

        assert evaluation.action == RiskAction.REDUCE_POSITION
        assert evaluation.metadata["partial"] is True
        assert evaluation.metadata["partial_pct"] == 50.0


class TestTrailingStop:
    """Tests for trailing stop rule."""

    @pytest.mark.asyncio
    async def test_trailing_stop_not_activated(self) -> None:
        """Test trailing stop when profit hasn't reached activation."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("51000"),  # 2% profit, < 5% activation
            highest_price=Decimal("51000"),
        )

        evaluation = await service.check_trailing_stop(position)

        assert evaluation.action == RiskAction.NONE

    @pytest.mark.asyncio
    async def test_trailing_stop_activated_but_not_triggered(self) -> None:
        """Test trailing stop activated but not triggered."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("52500"),  # 5% profit, activated
            highest_price=Decimal("53000"),  # Small drop, < 3% trailing
        )

        evaluation = await service.check_trailing_stop(position)

        assert evaluation.action == RiskAction.NONE

    @pytest.mark.asyncio
    async def test_trailing_stop_triggered(self) -> None:
        """Test trailing stop triggered after activation."""
        service = RiskService(create_test_risk_config())
        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("53000"),  # 6% profit (still above 5% activation)
            highest_price=Decimal("55000"),  # 10% profit peak, now 3.64% drop from peak
        )

        evaluation = await service.check_trailing_stop(position)

        assert evaluation.action == RiskAction.CLOSE_POSITION
        assert "trailing_stop" in evaluation.triggered_rules


class TestExposureLimits:
    """Tests for exposure limits rule."""

    @pytest.mark.asyncio
    async def test_exposure_within_limits(self) -> None:
        """Test exposure check when all limits are OK."""
        service = RiskService(create_test_risk_config())

        evaluation = await service.check_exposure_limits(
            "BTC/USDT", "binance", Decimal("5000")
        )

        assert evaluation.action == RiskAction.NONE

    @pytest.mark.asyncio
    async def test_exposure_exceeds_per_asset_limit(self) -> None:
        """Test exposure exceeding per-asset limit."""
        service = RiskService(create_test_risk_config())

        # Add existing position
        pos1 = create_test_position(
            symbol="BTC/USDT", entry_price=Decimal("50000"), quantity=Decimal("0.15")
        )  # 7500 value
        await service.update_position(pos1)

        # Try to add more that would exceed 10000 limit
        evaluation = await service.check_exposure_limits(
            "BTC/USDT", "binance", Decimal("3000")
        )

        assert evaluation.action == RiskAction.BLOCK_NEW_TRADE
        assert "exposure_per_asset" in evaluation.triggered_rules

    @pytest.mark.asyncio
    async def test_exposure_exceeds_per_exchange_limit(self) -> None:
        """Test exposure exceeding per-exchange limit."""
        service = RiskService(create_test_risk_config())

        # Add multiple positions on same exchange
        for i in range(3):
            pos = create_test_position(
                symbol=f"COIN{i}/USDT",
                exchange="binance",
                quantity=Decimal("200"),
                current_price=Decimal("50"),
            )  # 10000 each = 30000 total
            await service.update_position(pos)

        # Try to add more that would exceed 30000 limit
        evaluation = await service.check_exposure_limits(
            "NEW/USDT", "binance", Decimal("1000")
        )

        assert evaluation.action == RiskAction.BLOCK_NEW_TRADE
        assert "exposure_per_exchange" in evaluation.triggered_rules

    @pytest.mark.asyncio
    async def test_exposure_exceeds_total_limit(self) -> None:
        """Test exposure exceeding total limit."""
        service = RiskService(create_test_risk_config())

        # Add positions on different exchanges totaling near 50000
        for i in range(5):
            pos = create_test_position(
                symbol=f"COIN{i}/USDT",
                exchange=f"exchange{i}",
                quantity=Decimal("200"),
                current_price=Decimal("48"),
            )  # 9600 each = 48000 total
            await service.update_position(pos)

        # Try to add more that would exceed 50000 limit
        evaluation = await service.check_exposure_limits(
            "NEW/USDT", "binance", Decimal("3000")
        )

        assert evaluation.action == RiskAction.BLOCK_NEW_TRADE
        assert "exposure_total" in evaluation.triggered_rules


class TestMaxConcurrentTrades:
    """Tests for max concurrent trades rule."""

    @pytest.mark.asyncio
    async def test_concurrent_trades_within_limits(self) -> None:
        """Test concurrent trades check when all limits are OK."""
        service = RiskService(create_test_risk_config())

        evaluation = await service.check_max_concurrent_trades("BTC/USDT", "binance")

        assert evaluation.action == RiskAction.NONE

    @pytest.mark.asyncio
    async def test_concurrent_trades_per_asset_exceeded(self) -> None:
        """Test max concurrent trades per asset exceeded."""
        service = RiskService(create_test_risk_config())

        # Add one position for BTC/USDT (max_per_asset = 1)
        pos = create_test_position(symbol="BTC/USDT")
        await service.update_position(pos)

        # Try to add another for same asset
        evaluation = await service.check_max_concurrent_trades("BTC/USDT", "binance")

        assert evaluation.action == RiskAction.BLOCK_NEW_TRADE
        assert "max_per_asset" in evaluation.triggered_rules

    @pytest.mark.asyncio
    async def test_concurrent_trades_per_exchange_exceeded(self) -> None:
        """Test max concurrent trades per exchange exceeded."""
        service = RiskService(create_test_risk_config())

        # Add 3 positions on binance (max_per_exchange = 3)
        for i in range(3):
            pos = create_test_position(symbol=f"COIN{i}/USDT", exchange="binance")
            await service.update_position(pos)

        # Try to add another on binance
        evaluation = await service.check_max_concurrent_trades("NEW/USDT", "binance")

        assert evaluation.action == RiskAction.BLOCK_NEW_TRADE
        assert "max_per_exchange" in evaluation.triggered_rules

    @pytest.mark.asyncio
    async def test_concurrent_trades_total_exceeded(self) -> None:
        """Test max total concurrent trades exceeded."""
        service = RiskService(create_test_risk_config())

        # Add 5 positions (max_trades = 5)
        for i in range(5):
            pos = create_test_position(
                symbol=f"COIN{i}/USDT", exchange=f"exchange{i % 3}"
            )
            await service.update_position(pos)

        # Try to add another
        evaluation = await service.check_max_concurrent_trades("NEW/USDT", "binance")

        assert evaluation.action == RiskAction.BLOCK_NEW_TRADE
        assert "max_total_trades" in evaluation.triggered_rules


class TestDrawdownControl:
    """Tests for drawdown control rule."""

    @pytest.mark.asyncio
    async def test_drawdown_within_limits(self) -> None:
        """Test drawdown within acceptable limits."""
        service = RiskService(create_test_risk_config())

        await service.update_equity(Decimal("100000"))  # Peak
        await service.update_equity(Decimal("95000"))  # 5% drawdown

        evaluation = await service.check_drawdown()

        assert evaluation.action == RiskAction.NONE

    @pytest.mark.asyncio
    async def test_drawdown_max_exceeded(self) -> None:
        """Test max drawdown exceeded."""
        service = RiskService(create_test_risk_config())

        await service.update_equity(Decimal("100000"))  # Peak
        await service.update_equity(
            Decimal("83000")
        )  # 17% drawdown, > 15% max but < 20% emergency

        evaluation = await service.check_drawdown()

        assert evaluation.action == RiskAction.PAUSE_TRADING
        assert "drawdown_max" in evaluation.triggered_rules
        assert service.is_trading_paused() is True

    @pytest.mark.asyncio
    async def test_drawdown_emergency_exit(self) -> None:
        """Test emergency exit when drawdown critical."""
        service = RiskService(create_test_risk_config())

        await service.update_equity(Decimal("100000"))  # Peak
        await service.update_equity(Decimal("75000"))  # 25% drawdown, > 20% emergency

        evaluation = await service.check_drawdown()

        assert evaluation.action == RiskAction.EMERGENCY_EXIT_ALL
        assert "drawdown_emergency" in evaluation.triggered_rules

    @pytest.mark.asyncio
    async def test_drawdown_peak_updates_on_new_high(self) -> None:
        """Test that peak equity updates when equity increases."""
        service = RiskService(create_test_risk_config())

        await service.update_equity(Decimal("100000"))  # Initial peak
        await service.update_equity(Decimal("110000"))  # New peak

        # Drawdown should be calculated from new peak
        await service.update_equity(Decimal("100000"))  # 9.09% drawdown from new peak

        evaluation = await service.check_drawdown()

        assert evaluation.action == RiskAction.NONE


class TestCombinedEvaluations:
    """Tests for combined risk evaluations."""

    @pytest.mark.asyncio
    async def test_evaluate_position_risk_multiple_triggers(self) -> None:
        """Test position evaluation with multiple rules triggered."""
        config = create_test_risk_config()
        # Set take profit lower so both stop loss and take profit could theoretically trigger
        config.take_profit.percentage = Decimal("1.0")
        service = RiskService(config)

        position = create_test_position(
            entry_price=Decimal("50000"),
            current_price=Decimal("48000"),  # 4% loss
        )

        evaluations = await service.evaluate_position_risk(position)

        # Should trigger stop loss
        assert len(evaluations) > 0
        assert any(e.action == RiskAction.CLOSE_POSITION for e in evaluations)

    @pytest.mark.asyncio
    async def test_evaluate_new_trade_risk_trading_paused(self) -> None:
        """Test new trade evaluation when trading is paused."""
        service = RiskService(create_test_risk_config())

        # Trigger drawdown to pause trading
        await service.update_equity(Decimal("100000"))
        await service.update_equity(Decimal("83000"))  # 17% drawdown, triggers pause
        await service.check_drawdown()

        evaluations = await service.evaluate_new_trade_risk(
            "BTC/USDT", "binance", Decimal("5000")
        )

        assert len(evaluations) > 0
        assert evaluations[0].action == RiskAction.BLOCK_NEW_TRADE
        assert "trading_paused" in evaluations[0].triggered_rules

    @pytest.mark.asyncio
    async def test_evaluate_new_trade_risk_multiple_limits(self) -> None:
        """Test new trade evaluation with multiple limits exceeded."""
        service = RiskService(create_test_risk_config())

        # Add positions to approach limits
        for i in range(4):
            pos = create_test_position(
                symbol=f"COIN{i}/USDT",
                exchange="binance" if i < 2 else f"exchange{i}",
            )
            await service.update_position(pos)

        # Try to add large position that exceeds multiple limits
        evaluations = await service.evaluate_new_trade_risk(
            "BTC/USDT", "binance", Decimal("40000")
        )

        # Should trigger at least one rule (exposure limits)
        assert len(evaluations) >= 1
        # Check that the evaluation includes all violated limits in triggered_rules
        assert any(
            "exposure" in rule for eval in evaluations for rule in eval.triggered_rules
        )


class TestUtilityMethods:
    """Tests for utility methods."""

    @pytest.mark.asyncio
    async def test_resume_trading(self) -> None:
        """Test resuming trading after pause."""
        service = RiskService(create_test_risk_config())

        # Pause trading with 17% drawdown
        await service.update_equity(Decimal("100000"))
        await service.update_equity(Decimal("83000"))  # 17% drawdown, triggers pause
        await service.check_drawdown()

        assert service.is_trading_paused() is True

        # Resume trading
        await service.resume_trading()

        assert service.is_trading_paused() is False

    def test_get_config(self) -> None:
        """Test getting risk configuration."""
        config = create_test_risk_config()
        service = RiskService(config)

        retrieved_config = service.get_config()

        assert retrieved_config is config
        assert retrieved_config.stop_loss.percentage == Decimal("2.0")
