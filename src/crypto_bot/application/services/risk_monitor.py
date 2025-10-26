"""
Risk Monitoring Service.

This module provides asynchronous monitoring of positions and triggers
risk actions based on the RiskService evaluations.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from crypto_bot.application.services.risk_service import (
    Position,
    RiskAction,
    RiskEvaluation,
    RiskService,
)
from crypto_bot.utils.logger import get_logger

logger = get_logger(__name__)


class RiskMonitor:
    """
    Asynchronous risk monitoring service.

    Continuously monitors positions and triggers risk actions when thresholds are breached.
    Uses asyncio tasks for concurrent monitoring without blocking.
    """

    def __init__(
        self,
        risk_service: RiskService,
        position_provider: Optional[
            Callable[[], asyncio.Future[List[Position]]]
        ] = None,
        price_provider: Optional[
            Callable[[str, str], asyncio.Future[float]]
        ] = None,  # (exchange, symbol) -> price
    ) -> None:
        """
        Initialize risk monitor.

        Args:
            risk_service: RiskService instance for evaluating risks.
            position_provider: Async callable that returns list of current positions.
            price_provider: Async callable that returns current price for a symbol.
        """
        self._risk_service = risk_service
        self._position_provider = position_provider
        self._price_provider = price_provider
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        self._action_callbacks: Dict[RiskAction, List[Callable]] = {
            action: [] for action in RiskAction
        }
        self._evaluation_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000

    # --- Monitoring Control ---

    async def start(self) -> None:
        """
        Start asynchronous risk monitoring.

        Creates background task that continuously monitors positions.
        """
        if self._running:
            logger.warning("Risk monitor is already running")
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Risk monitor started")

    async def stop(self) -> None:
        """
        Stop risk monitoring and cleanup.

        Cancels monitoring task and waits for graceful shutdown.
        """
        if not self._running:
            logger.warning("Risk monitor is not running")
            return

        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                logger.info("Monitoring task cancelled successfully")

        logger.info("Risk monitor stopped")

    def is_running(self) -> bool:
        """
        Check if monitor is currently running.

        Returns:
            True if monitoring is active, False otherwise.
        """
        return self._running

    # --- Monitoring Loop ---

    async def _monitoring_loop(self) -> None:
        """
        Main monitoring loop that runs continuously.

        Monitors positions at the configured interval and triggers risk checks.
        """
        config = self._risk_service.get_config()
        interval = config.risk_check_interval

        logger.info(f"Starting monitoring loop with {interval}s interval")

        try:
            while self._running:
                try:
                    # Emergency-only mode check
                    if config.emergency_only_mode:
                        await self._check_emergency_risks_only()
                    else:
                        await self._check_all_risks()

                    # Sleep for configured interval
                    await asyncio.sleep(interval)

                except asyncio.CancelledError:
                    logger.info("Monitoring loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                    # Continue monitoring despite errors
                    await asyncio.sleep(interval)

        except Exception as e:
            logger.critical(f"Fatal error in monitoring loop: {e}", exc_info=True)
            self._running = False

    async def _check_all_risks(self) -> None:
        """
        Check all risk rules for current positions.

        Fetches current positions and evaluates all risk rules.
        """
        # Update positions from provider
        if self._position_provider:
            try:
                positions = await self._position_provider()
                for position in positions:
                    # Update position prices if price provider is available
                    if self._price_provider:
                        try:
                            current_price = await self._price_provider(
                                position.exchange, position.symbol
                            )
                            from decimal import Decimal

                            position.current_price = Decimal(str(current_price))
                        except Exception as e:
                            logger.error(
                                f"Failed to get price for {position.symbol}: {e}"
                            )

                    await self._risk_service.update_position(position)
            except Exception as e:
                logger.error(f"Failed to fetch positions: {e}")
                return

        # Get all positions being monitored
        positions_dict: Dict[str, Position] = await self._risk_service.get_positions()

        # Check each position
        for _key, position in positions_dict.items():
            await self._check_position_risks(position)

        # Check portfolio-level risks
        await self._check_portfolio_risks()

    async def _check_emergency_risks_only(self) -> None:
        """
        Check only emergency-level risks (drawdown).

        Used when system is in degraded state.
        """
        logger.debug("Running emergency-only risk checks")
        await self._check_portfolio_risks()

    async def _check_position_risks(self, position: Position) -> None:
        """
        Check all risk rules for a single position.

        Args:
            position: Position to evaluate.
        """
        try:
            evaluations = await self._risk_service.evaluate_position_risk(position)

            for evaluation in evaluations:
                if evaluation.action != RiskAction.NONE:
                    logger.warning(
                        f"Risk action triggered for {position.symbol} on {position.exchange}: "
                        f"{evaluation.action.value} - {evaluation.reason}"
                    )

                    # Record evaluation
                    self._record_evaluation(evaluation)

                    # Trigger callbacks
                    await self._trigger_action_callbacks(evaluation)

        except Exception as e:
            logger.error(
                f"Error checking risks for {position.symbol}: {e}", exc_info=True
            )

    async def _check_portfolio_risks(self) -> None:
        """
        Check portfolio-level risk rules (drawdown).

        These risks apply to the entire portfolio rather than individual positions.
        """
        try:
            evaluation = await self._risk_service.check_drawdown()

            if evaluation.action != RiskAction.NONE:
                logger.warning(
                    f"Portfolio risk action triggered: {evaluation.action.value} - {evaluation.reason}"
                )

                # Record evaluation
                self._record_evaluation(evaluation)

                # Trigger callbacks
                await self._trigger_action_callbacks(evaluation)

        except Exception as e:
            logger.error(f"Error checking portfolio risks: {e}", exc_info=True)

    # --- Action Callbacks ---

    def register_action_callback(
        self, action: RiskAction, callback: Callable[[RiskEvaluation], asyncio.Future]
    ) -> None:
        """
        Register a callback for a specific risk action.

        Args:
            action: Risk action to trigger callback for.
            callback: Async callable to execute when action is triggered.
        """
        self._action_callbacks[action].append(callback)
        logger.info(f"Registered callback for action: {action.value}")

    def unregister_action_callback(
        self, action: RiskAction, callback: Callable
    ) -> None:
        """
        Unregister a callback for a risk action.

        Args:
            action: Risk action to remove callback from.
            callback: Callback to remove.
        """
        if callback in self._action_callbacks[action]:
            self._action_callbacks[action].remove(callback)
            logger.info(f"Unregistered callback for action: {action.value}")

    async def _trigger_action_callbacks(self, evaluation: RiskEvaluation) -> None:
        """
        Trigger all registered callbacks for an action.

        Args:
            evaluation: Risk evaluation containing the action to trigger.
        """
        callbacks = self._action_callbacks.get(evaluation.action, [])

        if not callbacks:
            logger.debug(
                f"No callbacks registered for action: {evaluation.action.value}"
            )
            return

        # Execute all callbacks concurrently
        tasks = [callback(evaluation) for callback in callbacks]

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(
                f"Error executing callbacks for {evaluation.action.value}: {e}"
            )

    # --- Manual Checks ---

    async def check_new_trade(
        self, symbol: str, exchange: str, value: float
    ) -> List[RiskEvaluation]:
        """
        Manually check if a new trade would violate risk limits.

        Args:
            symbol: Trading pair symbol.
            exchange: Exchange name.
            value: Value of the proposed position.

        Returns:
            List of risk evaluations (empty if all checks pass).
        """
        from decimal import Decimal

        evaluations = await self._risk_service.evaluate_new_trade_risk(
            symbol, exchange, Decimal(str(value))
        )

        # Record evaluations
        for evaluation in evaluations:
            self._record_evaluation(evaluation)

        return evaluations

    # --- History & Statistics ---

    def _record_evaluation(self, evaluation: RiskEvaluation) -> None:
        """
        Record a risk evaluation in history.

        Args:
            evaluation: Evaluation to record.
        """
        record = {
            "timestamp": datetime.now(),
            "action": evaluation.action.value,
            "reason": evaluation.reason,
            "triggered_rules": evaluation.triggered_rules,
            "position": (
                {
                    "symbol": evaluation.position.symbol,
                    "exchange": evaluation.position.exchange,
                }
                if evaluation.position
                else None
            ),
            "metadata": evaluation.metadata,
        }

        self._evaluation_history.append(record)

        # Maintain history size limit
        if len(self._evaluation_history) > self._max_history_size:
            self._evaluation_history = self._evaluation_history[
                -self._max_history_size :
            ]

    def get_evaluation_history(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get risk evaluation history.

        Args:
            limit: Maximum number of records to return (most recent first).

        Returns:
            List of evaluation records.
        """
        if limit:
            return list(reversed(self._evaluation_history[-limit:]))
        return list(reversed(self._evaluation_history))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get monitoring statistics.

        Returns:
            Dictionary of statistics.
        """
        total_evaluations = len(self._evaluation_history)
        action_counts: Dict[str, int] = {}

        for record in self._evaluation_history:
            action = record["action"]
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "total_evaluations": total_evaluations,
            "action_counts": action_counts,
            "is_running": self._running,
            "positions_monitored": len(
                asyncio.run(self._risk_service.get_positions()) if self._running else {}
            ),
        }

    # --- Configuration Updates ---

    async def update_check_interval(self, interval: float) -> None:
        """
        Update risk check interval dynamically.

        Args:
            interval: New check interval in seconds.
        """
        config = self._risk_service.get_config()
        config.risk_check_interval = interval
        logger.info(f"Updated risk check interval to {interval}s")

    def get_risk_service(self) -> RiskService:
        """
        Get the underlying risk service.

        Returns:
            RiskService instance.
        """
        return self._risk_service
