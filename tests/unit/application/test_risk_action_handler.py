"""
Unit tests for RiskActionHandler.

Tests risk action execution with mocked trading engine.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from crypto_bot.application.dtos.order import OrderSide
from crypto_bot.application.interfaces.trading_engine import TradingEngineInterface
from crypto_bot.application.services.risk_action_handler import RiskActionHandler
from crypto_bot.application.services.risk_service import (
    Position,
    RiskAction,
    RiskEvaluation,
)


@pytest.fixture
def mock_trading_engine() -> MagicMock:
    """Create a mock trading engine."""
    engine = MagicMock(spec=TradingEngineInterface)
    engine.close_position = AsyncMock()
    engine.partial_close_position = AsyncMock()
    engine.close_all_positions = AsyncMock()
    engine.block_new_trades = AsyncMock()
    return engine


@pytest.fixture
def risk_action_handler(
    mock_trading_engine: MagicMock,
) -> RiskActionHandler:
    """Create RiskActionHandler with mocked engine."""
    return RiskActionHandler(trading_engine=mock_trading_engine)


@pytest.fixture
def test_position() -> Position:
    """Create a test position."""
    return Position(
        symbol="BTC/USDT",
        exchange="binance",
        side=OrderSide.BUY,
        entry_price=Decimal("50000"),
        current_price=Decimal("51000"),
        quantity=Decimal("0.1"),
        value=Decimal("5100"),
        unrealized_pnl=Decimal("100"),
        entry_timestamp=None,
        highest_price=Decimal("51000"),
    )


@pytest.mark.asyncio
class TestRiskActionHandler:
    """Test suite for RiskActionHandler."""

    async def test_initialization(
        self, risk_action_handler: RiskActionHandler, mock_trading_engine: MagicMock
    ) -> None:
        """Test handler initialization."""
        assert risk_action_handler.trading_engine == mock_trading_engine
        assert len(risk_action_handler._action_map) == 5

    async def test_handle_risk_evaluation_none_action(
        self, risk_action_handler: RiskActionHandler, mock_trading_engine: MagicMock
    ) -> None:
        """Test handling evaluation with NONE action."""
        evaluation = RiskEvaluation(
            action=RiskAction.NONE,
            position=None,
            triggered_rules=[],
            reason="No risk detected",
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        # Should not call any engine methods
        mock_trading_engine.close_position.assert_not_called()
        mock_trading_engine.partial_close_position.assert_not_called()

    async def test_handle_close_position(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
        test_position: Position,
    ) -> None:
        """Test closing a position."""
        evaluation = RiskEvaluation(
            action=RiskAction.CLOSE_POSITION,
            position=test_position,
            triggered_rules=["stop_loss"],
            reason="Stop loss triggered",
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        mock_trading_engine.close_position.assert_called_once_with(
            symbol="BTC/USDT",
            reason="Stop loss triggered",
            evaluation_id=str(id(evaluation)),
        )

    async def test_handle_close_position_no_position(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
    ) -> None:
        """Test closing position when no position exists."""
        evaluation = RiskEvaluation(
            action=RiskAction.CLOSE_POSITION,
            position=None,
            triggered_rules=["stop_loss"],
            reason="Stop loss triggered",
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        # Should not call engine method
        mock_trading_engine.close_position.assert_not_called()

    async def test_handle_reduce_position(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
        test_position: Position,
    ) -> None:
        """Test reducing position size."""
        evaluation = RiskEvaluation(
            action=RiskAction.REDUCE_POSITION,
            position=test_position,
            triggered_rules=["exposure_limit"],
            reason="Exposure limit reached",
            metadata={"partial_close_percentage": Decimal("50")},
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        mock_trading_engine.partial_close_position.assert_called_once_with(
            symbol="BTC/USDT",
            percentage=Decimal("50"),
            reason="Exposure limit reached",
            evaluation_id=str(id(evaluation)),
        )

    async def test_handle_reduce_position_no_percentage(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
        test_position: Position,
    ) -> None:
        """Test reducing position with default percentage."""
        evaluation = RiskEvaluation(
            action=RiskAction.REDUCE_POSITION,
            position=test_position,
            triggered_rules=["exposure_limit"],
            reason="Exposure limit reached",
            metadata={},  # No percentage specified
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        # Should default to 50%
        mock_trading_engine.partial_close_position.assert_called_once_with(
            symbol="BTC/USDT",
            percentage=Decimal("50"),
            reason="Exposure limit reached",
            evaluation_id=str(id(evaluation)),
        )

    async def test_handle_reduce_position_string_percentage(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
        test_position: Position,
    ) -> None:
        """Test reducing position with string percentage."""
        evaluation = RiskEvaluation(
            action=RiskAction.REDUCE_POSITION,
            position=test_position,
            triggered_rules=["exposure_limit"],
            reason="Exposure limit reached",
            metadata={"partial_close_percentage": "30"},  # String
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        # Should convert string to Decimal
        mock_trading_engine.partial_close_position.assert_called_once_with(
            symbol="BTC/USDT",
            percentage=Decimal("30"),
            reason="Exposure limit reached",
            evaluation_id=str(id(evaluation)),
        )

    async def test_handle_emergency_exit(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
    ) -> None:
        """Test emergency exit all positions."""
        evaluation = RiskEvaluation(
            action=RiskAction.EMERGENCY_EXIT_ALL,
            position=None,
            triggered_rules=["drawdown_control"],
            reason="Emergency exit: drawdown exceeded",
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        mock_trading_engine.close_all_positions.assert_called_once_with(
            reason="Emergency exit: drawdown exceeded",
            evaluation_id=str(id(evaluation)),
        )

    async def test_handle_pause_trading(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
    ) -> None:
        """Test pausing trading."""
        evaluation = RiskEvaluation(
            action=RiskAction.PAUSE_TRADING,
            position=None,
            triggered_rules=["max_concurrent_trades"],
            reason="Too many concurrent trades",
            metadata={"pause_duration_seconds": 300},
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        mock_trading_engine.block_new_trades.assert_called_once_with(
            duration_seconds=300,
            reason="Too many concurrent trades",
            evaluation_id=str(id(evaluation)),
        )

    async def test_handle_block_trade(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
        test_position: Position,
    ) -> None:
        """Test blocking a trade."""
        evaluation = RiskEvaluation(
            action=RiskAction.BLOCK_NEW_TRADE,
            position=test_position,
            triggered_rules=["max_concurrent_trades"],
            reason="Maximum concurrent trades reached",
        )

        await risk_action_handler.handle_risk_evaluation(evaluation)

        # Block trade doesn't call engine methods
        mock_trading_engine.close_position.assert_not_called()
        mock_trading_engine.partial_close_position.assert_not_called()

    async def test_handle_unsupported_action(
        self, risk_action_handler: RiskActionHandler, mock_trading_engine: MagicMock
    ) -> None:
        """Test handling unsupported action."""
        # Create evaluation with invalid action (assuming there's a way to do this)
        evaluation = RiskEvaluation(
            action="INVALID_ACTION",  # type: ignore
            position=None,
            triggered_rules=[],
            reason="Test",
        )

        with pytest.raises(ValueError, match="Unsupported risk action"):
            await risk_action_handler.handle_risk_evaluation(evaluation)

    async def test_handle_risk_evaluation_error_handling(
        self,
        risk_action_handler: RiskActionHandler,
        mock_trading_engine: MagicMock,
        test_position: Position,
    ) -> None:
        """Test error handling during risk action execution."""
        # Make engine method raise an error
        mock_trading_engine.close_position = AsyncMock(
            side_effect=Exception("Engine error")
        )

        evaluation = RiskEvaluation(
            action=RiskAction.CLOSE_POSITION,
            position=test_position,
            triggered_rules=["stop_loss"],
            reason="Stop loss triggered",
        )

        with pytest.raises(Exception, match="Engine error"):
            await risk_action_handler.handle_risk_evaluation(evaluation)

    async def test_trading_engine_property(
        self, risk_action_handler: RiskActionHandler, mock_trading_engine: MagicMock
    ) -> None:
        """Test trading engine property access."""
        assert risk_action_handler.trading_engine == mock_trading_engine
