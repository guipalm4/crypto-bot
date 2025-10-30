from __future__ import annotations

"""MACD Crossover strategy plugin.

Gera sinais a partir de cruzamentos do MACD com a linha de sinal:
- Entrada Long: MACD cruza para cima a Signal (bullish crossover)
- Saída Long: MACD cruza para baixo a Signal (bearish crossover)
- Short opcional (espelhado) quando `allow_short=True`.

Utiliza o plugin de indicadores `MACDIndicator` com cache.
"""

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from crypto_bot.plugins.indicators.pandas_ta_indicators import MACDIndicator

from .base import Strategy, StrategySignal


@dataclass(slots=True)
class _MACDParams:
    fast: int
    slow: int
    signal: int
    allow_short: bool


class MACDCrossover(Strategy):
    """MACD Crossover strategy implementation."""

    name = "macd_crossover"

    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal = int(params.get("signal", 9))
        # allow_short validated as bool when used (no need to store here)
        if fast < 1 or slow < 1 or signal < 1:
            raise ValueError("fast/slow/signal must be >= 1")
        if fast >= slow:
            raise ValueError("fast must be < slow")
        # allow_short is boolean; no further validation

    def generate_signal(
        self, market_data: Any, params: Mapping[str, Any]
    ) -> StrategySignal:
        if not isinstance(market_data, pd.DataFrame):
            raise TypeError("market_data must be a pandas.DataFrame")
        if "close" not in market_data.columns:
            raise ValueError("market_data must include 'close' column")

        self.validate_parameters(params)
        p = _MACDParams(
            fast=int(params.get("fast", 12)),
            slow=int(params.get("slow", 26)),
            signal=int(params.get("signal", 9)),
            allow_short=bool(params.get("allow_short", False)),
        )

        macd_df = MACDIndicator().calculate(
            market_data, {"fast": p.fast, "slow": p.slow, "signal": p.signal}
        )
        if len(macd_df) < 2:
            return StrategySignal(
                action="hold", strength=0.0, metadata={"reason": "insufficient_data"}
            )

        macd_col = f"MACD_{p.fast}_{p.slow}_{p.signal}"
        sig_col = f"MACDs_{p.fast}_{p.slow}_{p.signal}"

        prev_macd, curr_macd = float(macd_df[macd_col].iloc[-2]), float(
            macd_df[macd_col].iloc[-1]
        )
        prev_sig, curr_sig = float(macd_df[sig_col].iloc[-2]), float(
            macd_df[sig_col].iloc[-1]
        )

        bullish_cross = prev_macd <= prev_sig and curr_macd > curr_sig
        bearish_cross = prev_macd >= prev_sig and curr_macd < curr_sig

        metadata = {
            "macd": curr_macd,
            "signal": curr_sig,
            "fast": p.fast,
            "slow": p.slow,
            "signal_len": p.signal,
            "allow_short": p.allow_short,
        }

        if bearish_cross:
            # Long exit / Short entry
            if p.allow_short:
                return StrategySignal(
                    action="sell",
                    strength=1.0,
                    metadata={**metadata, "reason": "bearish_cross_short_entry"},
                )
            return StrategySignal(
                action="sell",
                strength=1.0,
                metadata={**metadata, "reason": "bearish_cross_long_exit"},
            )
        if bullish_cross:
            # Long entry / Short exit
            return StrategySignal(
                action="buy",
                strength=1.0,
                metadata={**metadata, "reason": "bullish_cross_long_entry"},
            )

        return StrategySignal(
            action="hold", strength=0.0, metadata={**metadata, "reason": "no_cross"}
        )

    def reset_state(self) -> None:
        return None
