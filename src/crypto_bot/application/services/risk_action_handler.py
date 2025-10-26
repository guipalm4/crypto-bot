"""
Risk Action Handler for Trading Engine Integration.

This module implements the connection between the risk monitoring system
and the trading engine, executing protective actions when risk rules are triggered.
"""

import logging
from decimal import Decimal
from typing import Callable, Dict

from crypto_bot.application.interfaces.trading_engine import TradingEngineInterface
from crypto_bot.application.services.risk_service import RiskAction, RiskEvaluation

logger = logging.getLogger(__name__)


class RiskActionHandler:
    """
    Handles execution of risk actions by interfacing with the trading engine.

    This handler ensures all risk-triggered actions are:
    - Atomic: Operations complete fully or fail safely
    - Logged: All actions are recorded with context
    - Traceable: Actions link back to risk evaluations
    """

    def __init__(self, trading_engine: TradingEngineInterface):
        """
        Initialize the risk action handler.

        Args:
            trading_engine: Trading engine interface for executing actions
        """
        self._engine = trading_engine
        self._action_map: Dict[RiskAction, Callable] = {
            RiskAction.CLOSE_POSITION: self._handle_close_position,
            RiskAction.REDUCE_POSITION: self._handle_reduce_position,
            RiskAction.EMERGENCY_EXIT_ALL: self._handle_emergency_exit,
            RiskAction.PAUSE_TRADING: self._handle_pause_trading,
            RiskAction.BLOCK_NEW_TRADE: self._handle_block_trade,
        }

    async def handle_risk_evaluation(self, evaluation: RiskEvaluation) -> None:
        """
        Process a risk evaluation and execute the required action.

        Args:
            evaluation: Risk evaluation containing action and context

        Raises:
            ValueError: If action is not supported
        """
        action = evaluation.action

        if action == RiskAction.NONE:
            logger.debug(f"No action required for evaluation: {evaluation}")
            return

        handler = self._action_map.get(action)
        if handler is None:
            raise ValueError(f"Unsupported risk action: {action}")

        symbol = evaluation.position.symbol if evaluation.position else "N/A"
        logger.info(
            f"Executing risk action: {action} for symbol: {symbol}, "
            f"rules: {evaluation.triggered_rules}"
        )

        try:
            await handler(evaluation)
            logger.info(f"Risk action {action} executed successfully for {symbol}")
        except Exception as e:
            logger.error(
                f"Failed to execute risk action {action} for {symbol}: {e}",
                exc_info=True,
            )
            raise

    async def _handle_close_position(self, evaluation: RiskEvaluation) -> None:
        """Close position completely."""
        if not evaluation.position:
            logger.error("Cannot close position: no position in evaluation")
            return

        await self._engine.close_position(
            symbol=evaluation.position.symbol,
            reason=evaluation.reason,
            evaluation_id=str(id(evaluation)),
        )

    async def _handle_reduce_position(self, evaluation: RiskEvaluation) -> None:
        """Reduce position size."""
        if not evaluation.position:
            logger.error("Cannot reduce position: no position in evaluation")
            return

        percentage = evaluation.metadata.get("partial_close_percentage")
        if percentage is None:
            logger.warning(
                f"Position reduction requested for {evaluation.position.symbol} "
                "but no percentage provided, defaulting to 50%"
            )
            percentage = Decimal("50")
        elif not isinstance(percentage, Decimal):
            percentage = Decimal(str(percentage))

        await self._engine.partial_close_position(
            symbol=evaluation.position.symbol,
            percentage=percentage,
            reason=evaluation.reason,
            evaluation_id=str(id(evaluation)),
        )

    async def _handle_emergency_exit(self, evaluation: RiskEvaluation) -> None:
        """Close all positions immediately."""
        await self._engine.close_all_positions(
            reason=evaluation.reason,
            evaluation_id=str(id(evaluation)),
        )

    async def _handle_pause_trading(self, evaluation: RiskEvaluation) -> None:
        """Pause trading temporarily."""
        duration = evaluation.metadata.get("pause_duration_seconds")
        await self._engine.block_new_trades(
            duration_seconds=duration,
            reason=evaluation.reason,
            evaluation_id=str(id(evaluation)),
        )

    async def _handle_block_trade(self, evaluation: RiskEvaluation) -> None:
        """Block a specific new trade."""
        # This is handled at the risk service level by returning blocking evaluation
        # No engine action needed as trade won't be executed
        symbol = evaluation.position.symbol if evaluation.position else "N/A"
        logger.info(f"Trade blocked for {symbol}: {evaluation.reason}")

    @property
    def trading_engine(self) -> TradingEngineInterface:
        """Get the underlying trading engine interface."""
        return self._engine
