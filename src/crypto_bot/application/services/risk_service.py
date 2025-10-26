"""
Risk Management Service.

This module implements core risk management logic for the trading bot,
including stop loss, take profit, exposure limits, trailing stops,
max concurrent trades, and drawdown control.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from crypto_bot.application.dtos.order import OrderSide
from crypto_bot.infrastructure.config.risk_config import RiskConfig
from crypto_bot.utils.logger import get_logger

logger = get_logger(__name__)


class RiskAction(str, Enum):
    """Actions that can be triggered by risk rules."""

    NONE = "none"
    CLOSE_POSITION = "close_position"
    REDUCE_POSITION = "reduce_position"
    BLOCK_NEW_TRADE = "block_new_trade"
    EMERGENCY_EXIT_ALL = "emergency_exit_all"
    PAUSE_TRADING = "pause_trading"


@dataclass
class Position:
    """
    Simplified position representation for risk calculations.

    Attributes:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        exchange: Exchange name
        side: Position side (buy or sell)
        entry_price: Average entry price
        current_price: Current market price
        quantity: Position size in base currency
        value: Position value in quote currency
        unrealized_pnl: Unrealized profit/loss
        realized_pnl: Realized profit/loss
        entry_timestamp: Position entry timestamp
        highest_price: Highest price since entry (for trailing stop)
    """

    symbol: str
    exchange: str
    side: OrderSide
    entry_price: Decimal
    current_price: Decimal
    quantity: Decimal
    value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal = Decimal("0")
    entry_timestamp: datetime = field(default_factory=datetime.now)
    highest_price: Optional[Decimal] = None


@dataclass
class RiskEvaluation:
    """
    Result of risk evaluation for a position or portfolio.

    Attributes:
        action: Recommended action based on risk rules
        reason: Human-readable explanation for the action
        triggered_rules: List of rule names that were triggered
        position: Position that triggered the evaluation (if applicable)
        metadata: Additional context data
    """

    action: RiskAction
    reason: str
    triggered_rules: List[str] = field(default_factory=list)
    position: Optional[Position] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RiskService:
    """
    Risk management service for trading operations.

    This service implements all risk management rules and provides
    methods to evaluate positions, portfolios, and trading decisions.
    """

    def __init__(self, config: RiskConfig) -> None:
        """
        Initialize risk service with configuration.

        Args:
            config: Risk management configuration.
        """
        self._config = config
        self._positions: Dict[str, Position] = {}
        self._positions_lock = asyncio.Lock()
        self._last_action_time: Dict[str, datetime] = {}
        self._trading_paused = False
        self._peak_equity: Decimal = Decimal("0")
        self._current_equity: Decimal = Decimal("0")

    # --- Position Management ---

    async def update_position(self, position: Position) -> None:
        """
        Update position data for risk monitoring.

        Args:
            position: Position to update or add.
        """
        async with self._positions_lock:
            key = f"{position.exchange}:{position.symbol}"

            # Update highest price for trailing stop
            if (
                position.highest_price is None
                or position.current_price > position.highest_price
            ):
                position.highest_price = position.current_price

            self._positions[key] = position

        logger.debug(f"Updated position: {key}")

    async def remove_position(self, exchange: str, symbol: str) -> None:
        """
        Remove a closed position from monitoring.

        Args:
            exchange: Exchange name.
            symbol: Trading pair symbol.
        """
        async with self._positions_lock:
            key = f"{exchange}:{symbol}"
            if key in self._positions:
                del self._positions[key]
                logger.debug(f"Removed position: {key}")

    async def get_positions(self) -> Dict[str, Position]:
        """
        Get current monitored positions.

        Returns:
            Dictionary of positions keyed by "exchange:symbol".
        """
        async with self._positions_lock:
            return self._positions.copy()

    # --- Risk Rule: Stop Loss ---

    async def check_stop_loss(self, position: Position) -> RiskEvaluation:
        """
        Check if stop loss should be triggered for a position.

        Args:
            position: Position to evaluate.

        Returns:
            Risk evaluation result.
        """
        if not self._config.stop_loss.enabled:
            return RiskEvaluation(action=RiskAction.NONE, reason="Stop loss disabled")

        # Calculate loss percentage
        if position.side == OrderSide.BUY:
            loss_pct = (
                (position.entry_price - position.current_price) / position.entry_price
            ) * 100
        else:  # SELL
            loss_pct = (
                (position.current_price - position.entry_price) / position.entry_price
            ) * 100

        loss_pct = Decimal(str(loss_pct))

        if loss_pct >= self._config.stop_loss.percentage:
            # Check cooldown
            if await self._check_cooldown(
                f"stop_loss_{position.symbol}", self._config.stop_loss.cooldown_seconds
            ):
                logger.warning(
                    f"Stop loss triggered for {position.symbol} on {position.exchange}: "
                    f"Loss {loss_pct:.2f}% >= {self._config.stop_loss.percentage}%"
                )
                return RiskEvaluation(
                    action=RiskAction.CLOSE_POSITION,
                    reason=f"Stop loss triggered: {loss_pct:.2f}% loss",
                    triggered_rules=["stop_loss"],
                    position=position,
                    metadata={"loss_pct": float(loss_pct)},
                )

        return RiskEvaluation(action=RiskAction.NONE, reason="Stop loss not triggered")

    # --- Risk Rule: Take Profit ---

    async def check_take_profit(self, position: Position) -> RiskEvaluation:
        """
        Check if take profit should be triggered for a position.

        Args:
            position: Position to evaluate.

        Returns:
            Risk evaluation result.
        """
        if not self._config.take_profit.enabled:
            return RiskEvaluation(action=RiskAction.NONE, reason="Take profit disabled")

        # Calculate profit percentage
        if position.side == OrderSide.BUY:
            profit_pct = (
                (position.current_price - position.entry_price) / position.entry_price
            ) * 100
        else:  # SELL
            profit_pct = (
                (position.entry_price - position.current_price) / position.entry_price
            ) * 100

        profit_pct = Decimal(str(profit_pct))

        if profit_pct >= self._config.take_profit.percentage:
            # Check cooldown
            if await self._check_cooldown(
                f"take_profit_{position.symbol}",
                self._config.take_profit.cooldown_seconds,
            ):
                action = RiskAction.CLOSE_POSITION
                reason = f"Take profit triggered: {profit_pct:.2f}% profit"

                if self._config.take_profit.partial_close:
                    action = RiskAction.REDUCE_POSITION
                    reason = f"Partial take profit triggered: {profit_pct:.2f}% profit"

                logger.info(
                    f"Take profit triggered for {position.symbol} on {position.exchange}: "
                    f"Profit {profit_pct:.2f}% >= {self._config.take_profit.percentage}%"
                )

                return RiskEvaluation(
                    action=action,
                    reason=reason,
                    triggered_rules=["take_profit"],
                    position=position,
                    metadata={
                        "profit_pct": float(profit_pct),
                        "partial": self._config.take_profit.partial_close,
                        "partial_pct": float(
                            self._config.take_profit.partial_close_percentage or 0
                        ),
                    },
                )

        return RiskEvaluation(
            action=RiskAction.NONE, reason="Take profit not triggered"
        )

    # --- Risk Rule: Trailing Stop ---

    async def check_trailing_stop(self, position: Position) -> RiskEvaluation:
        """
        Check if trailing stop should be triggered for a position.

        Args:
            position: Position to evaluate.

        Returns:
            Risk evaluation result.
        """
        if not self._config.trailing_stop.enabled:
            return RiskEvaluation(
                action=RiskAction.NONE, reason="Trailing stop disabled"
            )

        if position.highest_price is None:
            return RiskEvaluation(
                action=RiskAction.NONE, reason="Highest price not set"
            )

        # Calculate current profit
        if position.side == OrderSide.BUY:
            profit_pct = (
                (position.current_price - position.entry_price) / position.entry_price
            ) * 100
            drop_from_peak_pct = (
                (position.highest_price - position.current_price)
                / position.highest_price
            ) * 100
        else:  # SELL
            profit_pct = (
                (position.entry_price - position.current_price) / position.entry_price
            ) * 100
            drop_from_peak_pct = (
                (position.current_price - position.highest_price)
                / position.highest_price
            ) * 100

        profit_pct = Decimal(str(profit_pct))
        drop_from_peak_pct = Decimal(str(drop_from_peak_pct))

        # Check if trailing stop is activated (profit >= activation percentage)
        if profit_pct < self._config.trailing_stop.activation_percentage:
            return RiskEvaluation(
                action=RiskAction.NONE, reason="Trailing stop not yet activated"
            )

        # Check if price dropped enough from peak to trigger trailing stop
        if drop_from_peak_pct >= self._config.trailing_stop.trailing_percentage:
            logger.info(
                f"Trailing stop triggered for {position.symbol} on {position.exchange}: "
                f"Drop from peak {drop_from_peak_pct:.2f}% >= {self._config.trailing_stop.trailing_percentage}%"
            )
            return RiskEvaluation(
                action=RiskAction.CLOSE_POSITION,
                reason=f"Trailing stop triggered: {drop_from_peak_pct:.2f}% drop from peak",
                triggered_rules=["trailing_stop"],
                position=position,
                metadata={
                    "profit_pct": float(profit_pct),
                    "drop_from_peak_pct": float(drop_from_peak_pct),
                    "highest_price": float(position.highest_price),
                },
            )

        return RiskEvaluation(
            action=RiskAction.NONE, reason="Trailing stop not triggered"
        )

    # --- Risk Rule: Exposure Limits ---

    async def check_exposure_limits(
        self, symbol: str, exchange: str, proposed_value: Decimal
    ) -> RiskEvaluation:
        """
        Check if opening a new position would exceed exposure limits.

        Args:
            symbol: Trading pair symbol.
            exchange: Exchange name.
            proposed_value: Value of the proposed position.

        Returns:
            Risk evaluation result.
        """
        positions = await self.get_positions()

        # Calculate current exposures
        asset_exposure = Decimal("0")
        exchange_exposure = Decimal("0")
        total_exposure = Decimal("0")

        for pos in positions.values():
            total_exposure += pos.value

            if pos.exchange == exchange:
                exchange_exposure += pos.value

            if pos.symbol == symbol:
                asset_exposure += pos.value

        # Check proposed limits
        new_asset_exposure = asset_exposure + proposed_value
        new_exchange_exposure = exchange_exposure + proposed_value
        new_total_exposure = total_exposure + proposed_value

        triggered = []
        reason_parts = []

        if new_asset_exposure > self._config.exposure_limit.max_per_asset:
            triggered.append("exposure_per_asset")
            reason_parts.append(
                f"Asset exposure would be {new_asset_exposure} > {self._config.exposure_limit.max_per_asset}"
            )

        if new_exchange_exposure > self._config.exposure_limit.max_per_exchange:
            triggered.append("exposure_per_exchange")
            reason_parts.append(
                f"Exchange exposure would be {new_exchange_exposure} > {self._config.exposure_limit.max_per_exchange}"
            )

        if new_total_exposure > self._config.exposure_limit.max_total:
            triggered.append("exposure_total")
            reason_parts.append(
                f"Total exposure would be {new_total_exposure} > {self._config.exposure_limit.max_total}"
            )

        if triggered:
            logger.warning(
                f"Exposure limit would be exceeded: {'; '.join(reason_parts)}"
            )
            return RiskEvaluation(
                action=RiskAction.BLOCK_NEW_TRADE,
                reason=f"Exposure limits: {'; '.join(reason_parts)}",
                triggered_rules=triggered,
                metadata={
                    "current_asset_exposure": float(asset_exposure),
                    "current_exchange_exposure": float(exchange_exposure),
                    "current_total_exposure": float(total_exposure),
                    "proposed_value": float(proposed_value),
                },
            )

        return RiskEvaluation(action=RiskAction.NONE, reason="Exposure limits OK")

    # --- Risk Rule: Max Concurrent Trades ---

    async def check_max_concurrent_trades(
        self, symbol: str, exchange: str
    ) -> RiskEvaluation:
        """
        Check if opening a new position would exceed concurrent trade limits.

        Args:
            symbol: Trading pair symbol.
            exchange: Exchange name.

        Returns:
            Risk evaluation result.
        """
        positions = await self.get_positions()

        # Count current trades
        total_trades = len(positions)
        exchange_trades = sum(1 for p in positions.values() if p.exchange == exchange)
        asset_trades = sum(1 for p in positions.values() if p.symbol == symbol)

        triggered = []
        reason_parts = []

        if asset_trades >= self._config.max_concurrent_trades.max_per_asset:
            triggered.append("max_per_asset")
            reason_parts.append(
                f"{asset_trades} trade(s) already open for {symbol} (max: {self._config.max_concurrent_trades.max_per_asset})"
            )

        if exchange_trades >= self._config.max_concurrent_trades.max_per_exchange:
            triggered.append("max_per_exchange")
            reason_parts.append(
                f"{exchange_trades} trade(s) already open on {exchange} (max: {self._config.max_concurrent_trades.max_per_exchange})"
            )

        if total_trades >= self._config.max_concurrent_trades.max_trades:
            triggered.append("max_total_trades")
            reason_parts.append(
                f"{total_trades} trade(s) already open (max: {self._config.max_concurrent_trades.max_trades})"
            )

        if triggered:
            logger.warning(
                f"Max concurrent trades would be exceeded: {'; '.join(reason_parts)}"
            )
            return RiskEvaluation(
                action=RiskAction.BLOCK_NEW_TRADE,
                reason=f"Concurrent trade limits: {'; '.join(reason_parts)}",
                triggered_rules=triggered,
                metadata={
                    "total_trades": total_trades,
                    "exchange_trades": exchange_trades,
                    "asset_trades": asset_trades,
                },
            )

        return RiskEvaluation(
            action=RiskAction.NONE, reason="Concurrent trade limits OK"
        )

    # --- Risk Rule: Drawdown Control ---

    async def check_drawdown(self) -> RiskEvaluation:
        """
        Check if current drawdown exceeds limits.

        Returns:
            Risk evaluation result.
        """
        # Update equity tracking
        if self._current_equity > self._peak_equity:
            self._peak_equity = self._current_equity

        if self._peak_equity == 0:
            return RiskEvaluation(action=RiskAction.NONE, reason="Peak equity not set")

        # Calculate drawdown
        drawdown = (
            (self._peak_equity - self._current_equity) / self._peak_equity
        ) * 100
        drawdown = Decimal(str(drawdown))

        # Check emergency exit threshold
        if (
            self._config.drawdown_control.enable_emergency_exit
            and drawdown >= self._config.drawdown_control.emergency_exit_percentage
        ):
            logger.critical(
                f"EMERGENCY DRAWDOWN THRESHOLD BREACHED: {drawdown:.2f}% >= {self._config.drawdown_control.emergency_exit_percentage}%"
            )
            return RiskEvaluation(
                action=RiskAction.EMERGENCY_EXIT_ALL,
                reason=f"Emergency drawdown: {drawdown:.2f}% (emergency threshold: {self._config.drawdown_control.emergency_exit_percentage}%)",
                triggered_rules=["drawdown_emergency"],
                metadata={
                    "drawdown_pct": float(drawdown),
                    "peak_equity": float(self._peak_equity),
                    "current_equity": float(self._current_equity),
                },
            )

        # Check max drawdown threshold
        if drawdown >= self._config.drawdown_control.max_drawdown_percentage:
            if self._config.drawdown_control.pause_trading_on_breach:
                self._trading_paused = True
                logger.error(
                    f"Max drawdown breached: {drawdown:.2f}% >= {self._config.drawdown_control.max_drawdown_percentage}%. Trading paused."
                )
                return RiskEvaluation(
                    action=RiskAction.PAUSE_TRADING,
                    reason=f"Max drawdown breached: {drawdown:.2f}%",
                    triggered_rules=["drawdown_max"],
                    metadata={
                        "drawdown_pct": float(drawdown),
                        "peak_equity": float(self._peak_equity),
                        "current_equity": float(self._current_equity),
                    },
                )

        return RiskEvaluation(action=RiskAction.NONE, reason="Drawdown within limits")

    # --- Combined Risk Evaluation ---

    async def evaluate_position_risk(self, position: Position) -> List[RiskEvaluation]:
        """
        Evaluate all risk rules for a position.

        Args:
            position: Position to evaluate.

        Returns:
            List of risk evaluations (empty if all checks pass).
        """
        evaluations = []

        # Check stop loss
        stop_loss_eval = await self.check_stop_loss(position)
        if stop_loss_eval.action != RiskAction.NONE:
            evaluations.append(stop_loss_eval)

        # Check take profit
        take_profit_eval = await self.check_take_profit(position)
        if take_profit_eval.action != RiskAction.NONE:
            evaluations.append(take_profit_eval)

        # Check trailing stop
        trailing_stop_eval = await self.check_trailing_stop(position)
        if trailing_stop_eval.action != RiskAction.NONE:
            evaluations.append(trailing_stop_eval)

        return evaluations

    async def evaluate_new_trade_risk(
        self, symbol: str, exchange: str, proposed_value: Decimal
    ) -> List[RiskEvaluation]:
        """
        Evaluate risk for a proposed new trade.

        Args:
            symbol: Trading pair symbol.
            exchange: Exchange name.
            proposed_value: Value of the proposed position.

        Returns:
            List of risk evaluations (empty if all checks pass).
        """
        if self._trading_paused:
            return [
                RiskEvaluation(
                    action=RiskAction.BLOCK_NEW_TRADE,
                    reason="Trading is paused due to risk limits",
                    triggered_rules=["trading_paused"],
                )
            ]

        evaluations = []

        # Check exposure limits
        exposure_eval = await self.check_exposure_limits(
            symbol, exchange, proposed_value
        )
        if exposure_eval.action != RiskAction.NONE:
            evaluations.append(exposure_eval)

        # Check max concurrent trades
        concurrent_eval = await self.check_max_concurrent_trades(symbol, exchange)
        if concurrent_eval.action != RiskAction.NONE:
            evaluations.append(concurrent_eval)

        # Check drawdown
        drawdown_eval = await self.check_drawdown()
        if drawdown_eval.action != RiskAction.NONE:
            evaluations.append(drawdown_eval)

        return evaluations

    # --- Utility Methods ---

    async def _check_cooldown(self, action_key: str, cooldown_seconds: int) -> bool:
        """
        Check if cooldown period has passed for an action.

        Args:
            action_key: Unique key for the action.
            cooldown_seconds: Cooldown period in seconds.

        Returns:
            True if action is allowed, False if still in cooldown.
        """
        now = datetime.now()
        last_time = self._last_action_time.get(action_key)

        if last_time is None or (now - last_time) >= timedelta(
            seconds=cooldown_seconds
        ):
            self._last_action_time[action_key] = now
            return True

        return False

    async def update_equity(self, current_equity: Decimal) -> None:
        """
        Update current equity for drawdown calculations.

        Args:
            current_equity: Current total equity value.
        """
        self._current_equity = current_equity
        if self._current_equity > self._peak_equity:
            self._peak_equity = self._current_equity

    def is_trading_paused(self) -> bool:
        """
        Check if trading is paused due to risk limits.

        Returns:
            True if trading is paused, False otherwise.
        """
        return self._trading_paused

    async def resume_trading(self) -> None:
        """Resume trading after it was paused."""
        self._trading_paused = False
        logger.info("Trading resumed")

    def get_config(self) -> RiskConfig:
        """
        Get current risk configuration.

        Returns:
            Risk configuration.
        """
        return self._config
