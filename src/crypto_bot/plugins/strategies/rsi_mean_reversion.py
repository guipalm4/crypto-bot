from __future__ import annotations

"""RSI Mean Reversion strategy plugin.

This strategy generates signals based on RSI mean reversion logic:
- Long entry when RSI reverts above the oversold threshold after crossing below it
- Long exit when RSI crosses above an overbought exit threshold
- Optional mirrored short logic when `allow_short=True`

It leverages the indicators plugin system (RSIIndicator) and its cache to avoid
recomputation. Only the last bar is considered for the emitted signal, keeping
the implementation stateless by default.
"""

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from crypto_bot.plugins.indicators.pandas_ta_indicators import RSIIndicator

from .base import Strategy, StrategySignal


@dataclass(slots=True)
class _ValidatedParams:
    rsi_length: int
    oversold: float
    overbought: float
    exit_oversold: float
    exit_overbought: float
    allow_short: bool
    stop_loss_pct: float
    take_profit_pct: float
    position_size_pct: float


class RSIMeanReversion(Strategy):
    """RSI Mean Reversion strategy implementation.

    Parameters (validated via `validate_parameters`):
        - rsi_length: int (default 14, >= 2)
        - oversold: float (default 30, range 5–45)
        - overbought: float (default 70, range 55–95, must be > oversold)
        - exit_oversold: float (default oversold + 5, must be >= oversold)
        - exit_overbought: float (default overbought - 5, must be <= overbought)
        - allow_short: bool (default False)
        - stop_loss_pct: float (default 2.0, > 0)
        - take_profit_pct: float (default 4.0, > 0)
        - position_size_pct: float (default 10.0, (0, 100])
    """

    name = "rsi_mean_reversion"

    def __init__(self) -> None:
        # Strategy is stateless by default; no internal state required.
        pass

    # ----------------------------- Validation ------------------------------ #
    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validate user-provided parameters.

        Raises:
            ValueError | TypeError: For missing/invalid parameters
        """
        # Defaults
        rsi_length = int(params.get("rsi_length", 14))
        oversold = float(params.get("oversold", 30.0))
        overbought = float(params.get("overbought", 70.0))
        exit_oversold = float(params.get("exit_oversold", oversold + 5.0))
        exit_overbought = float(params.get("exit_overbought", overbought - 5.0))
        # allow_short validated as bool when used (no need to store here)
        stop_loss_pct = float(params.get("stop_loss_pct", 2.0))
        take_profit_pct = float(params.get("take_profit_pct", 4.0))
        position_size_pct = float(params.get("position_size_pct", 10.0))

        # Types already coerced above; enforce bounds/invariants
        if rsi_length < 2:
            raise ValueError("rsi_length must be >= 2")
        if not (5.0 <= oversold < 50.0):
            raise ValueError("oversold must be in [5, 50)")
        if not (50.0 < overbought <= 95.0):
            raise ValueError("overbought must be in (50, 95]")
        if overbought <= oversold:
            raise ValueError("overbought must be greater than oversold")
        if exit_oversold < oversold:
            raise ValueError("exit_oversold must be >= oversold")
        if exit_overbought > overbought:
            raise ValueError("exit_overbought must be <= overbought")
        if stop_loss_pct <= 0.0:
            raise ValueError("stop_loss_pct must be > 0")
        if take_profit_pct <= 0.0:
            raise ValueError("take_profit_pct must be > 0")
        if not (0.0 < position_size_pct <= 100.0):
            raise ValueError("position_size_pct must be in (0, 100]")

    # --------------------------- Signal Generation ------------------------- #
    def generate_signal(
        self, market_data: Any, params: Mapping[str, Any]
    ) -> StrategySignal:
        """Generate a StrategySignal from the latest bar using RSI cross logic.

        Args:
            market_data: pandas.DataFrame with at least a "close" column and
                         chronological index (oldest→newest).
            params: Validated parameters per `validate_parameters`.

        Returns:
            StrategySignal with action in {"buy", "sell", "hold"} and metadata.
        """
        if not isinstance(market_data, pd.DataFrame):
            raise TypeError("market_data must be a pandas.DataFrame")
        if "close" not in market_data.columns:
            raise ValueError("market_data must include 'close' column")

        # Validate params (raises early with clear message)
        self.validate_parameters(params)

        # Coerce and compute derived validated params for internal use
        v = _ValidatedParams(
            rsi_length=int(params.get("rsi_length", 14)),
            oversold=float(params.get("oversold", 30.0)),
            overbought=float(params.get("overbought", 70.0)),
            exit_oversold=float(
                params.get("exit_oversold", float(params.get("oversold", 30.0)) + 5.0)
            ),
            exit_overbought=float(
                params.get(
                    "exit_overbought", float(params.get("overbought", 70.0)) - 5.0
                )
            ),
            allow_short=bool(params.get("allow_short", False)),
            stop_loss_pct=float(params.get("stop_loss_pct", 2.0)),
            take_profit_pct=float(params.get("take_profit_pct", 4.0)),
            position_size_pct=float(params.get("position_size_pct", 10.0)),
        )

        # Compute RSI via indicator plugin (with cache)
        rsi = RSIIndicator().calculate(market_data, {"length": v.rsi_length})
        if rsi.isna().any():
            # During warmup, we might not have enough data; hold safely
            # but still allow signal if the last two values are valid
            if rsi.tail(2).isna().any():
                return StrategySignal(
                    action="hold", strength=0.0, metadata={"reason": "warmup"}
                )

        # Use last two bars to detect cross events
        if len(rsi) < 2:
            return StrategySignal(
                action="hold", strength=0.0, metadata={"reason": "insufficient_data"}
            )

        prev_rsi = float(rsi.iloc[-2])
        curr_rsi = float(rsi.iloc[-1])

        # Long entry: revert above oversold after being below
        long_entry = prev_rsi < v.oversold and curr_rsi >= v.oversold
        # Long exit: cross above exit_overbought
        long_exit = prev_rsi <= v.exit_overbought and curr_rsi > v.exit_overbought

        # Short logic (optional)
        short_entry = v.allow_short and (
            prev_rsi > v.overbought and curr_rsi <= v.overbought
        )
        short_exit = v.allow_short and (
            prev_rsi >= v.exit_oversold and curr_rsi < v.exit_oversold
        )

        metadata = {
            "rsi": curr_rsi,
            "prev_rsi": prev_rsi,
            "params": {
                "rsi_length": v.rsi_length,
                "oversold": v.oversold,
                "overbought": v.overbought,
                "exit_oversold": v.exit_oversold,
                "exit_overbought": v.exit_overbought,
                "allow_short": v.allow_short,
                "stop_loss_pct": v.stop_loss_pct,
                "take_profit_pct": v.take_profit_pct,
                "position_size_pct": v.position_size_pct,
            },
        }

        # Priority: exits override entries when both occur (unlikely but explicit)
        if long_exit:
            return StrategySignal(
                action="sell",
                strength=1.0,
                metadata={**metadata, "reason": "long_exit"},
            )
        if long_entry:
            return StrategySignal(
                action="buy",
                strength=1.0,
                metadata={**metadata, "reason": "long_entry"},
            )

        if short_exit:
            return StrategySignal(
                action="buy",
                strength=1.0,
                metadata={**metadata, "reason": "short_exit"},
            )
        if short_entry:
            return StrategySignal(
                action="sell",
                strength=1.0,
                metadata={**metadata, "reason": "short_entry"},
            )

        return StrategySignal(
            action="hold", strength=0.0, metadata={**metadata, "reason": "no_signal"}
        )

    # ------------------------------- Lifecycle ----------------------------- #
    def reset_state(self) -> None:
        """Stateless strategy; nothing to reset."""
        return None
